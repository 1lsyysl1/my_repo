import os
import tree_sitter_languages
from blar_graph.graph_construction.languages.base_parser import BaseParser
from blar_graph.graph_construction.utils.interfaces.GlobalGraphInfo import GlobalGraphInfo


class JavaParser(BaseParser):
    def __init__(self, global_graph_info: GlobalGraphInfo):
        super().__init__("java", "*", ".java", ".", global_graph_info)

    @property
    def self_syntax(self):
        return "this."

    @property
    def decompose_call_query(self):
        return """
            (method_invocation
                object: (identifier) @_
            )
            (field_access
                object: (identifier) @_
            )
            """

    @property
    def assignment_query(self):
        return """(variable_declarator name: _ @variable value: _ @expression)"""

    @property
    def function_call_query(self):
        return """
            (method_invocation
                name: (identifier) @method_call
            )
            """

    @property
    def inheritances_query(self):
        return """
            (class_declaration
                (super_interfaces
                    (type_identifier) @interface
                )
            )
            """

    @property
    def controller_path_query(self):
        return """
            (class_declaration
                (modifiers
                    (annotation
                        name: (identifier) @annotation
                        (#match? @annotation "Controller|RestController")
                    )
                )
                name: (identifier) @class_name
            )
            """

    @property
    def scopes_names(self):
        return {
            "function": ["method_declaration"],
            "class": ["class_declaration"],
            "plain_code_block": ["block"],
        }

    @property
    def relation_types_map(self):
        return {
            "method_declaration": "METHOD_DEFINITION",
            "class_declaration": "CLASS_DEFINITION",
        }

    def _get_imports(self, path: str, file_node_id: str, root_path: str) -> dict:
        parser = tree_sitter_languages.get_parser(self.language)
        with open(path, "r") as file:
            code = file.read()
        tree = parser.parse(bytes(code, "utf-8"))

        imports = {"_*wildcard*_": {"path": [], "alias": "", "type": "wildcard"}}
        import_query = """
            (import_declaration
                (scoped_identifier) @import_path
                (.*)? @alias
            )
            """
        query = tree_sitter_languages.get_language(self.language).query(import_query)
        captures = query.captures(tree.root_node)

        for node, _ in captures:
            import_text = node.text.decode()
            if " as " in import_text:
                import_path, alias = import_text.split(" as ")
                imports[alias.strip()] = {
                    "path": self.resolve_import_path(import_path.strip(), path, root_path),
                    "alias": alias.strip(),
                    "type": "aliased_import",
                }
            else:
                imports[import_text] = {
                    "path": self.resolve_import_path(import_text, path, root_path),
                    "alias": "",
                    "type": "import_statement",
                }

        return {file_node_id: imports}

    def _parse_controller_paths(self, tree):
        query = tree_sitter_languages.get_language(self.language).query(self.controller_path_query)
        captures = query.captures(tree.root_node)
        
        controllers = []
        for node, _ in captures:
            class_name = node.text.decode()
            controllers.append({
                "class_name": class_name,
                "path": self._get_controller_path(node)
            })
        return controllers

    def _get_controller_path(self, node):
        # 获取类级别的RequestMapping路径
        class_path = ""
        class_query = """
            (class_declaration
                (modifiers
                    (annotation
                        name: (identifier) @annotation
                        arguments: (annotation_argument_list)? @args
                        (#match? @annotation "RestController|Controller|RequestMapping")
                    )
                )
            )
        """
        query = tree_sitter_languages.get_language(self.language).query(class_query)
        captures = query.captures(node)
        
        for capture_node, _ in captures:
            if capture_node.text.decode() == "RequestMapping":
                # 解析RequestMapping的value参数
                args = capture_node.next_sibling.text.decode()
                if "value=" in args:
                    class_path = args.split("value=")[1].split(",")[0].strip('"\'')
            elif capture_node.text.decode() in ["RestController", "Controller"]:
                class_path = ""

    @property
    def method_call_query(self):
        return """
            (method_invocation
                object: (identifier)? @object
                name: (identifier) @method_name
            )
        """

    def _parse_method_calls(self, tree, file_path, root_path):
        query = tree_sitter_languages.get_language(self.language).query(self.method_call_query)
        captures = query.captures(tree.root_node)
        
        method_calls = []
        for node, _ in captures:
            method_name = node.text.decode()
            object_node = node.prev_sibling
            class_name = object_node.text.decode() if object_node and object_node.type == 'identifier' else None
            method_calls.append({
                'method': method_name,
                'class': class_name
            })
        return method_calls

    def parse_file(self, file_path: str, root_path: str, global_graph_info: GlobalGraphInfo, level: int):
        parser = tree_sitter_languages.get_parser(self.language)
        with open(file_path, "r") as file:
            code = file.read()
        tree = parser.parse(bytes(code, "utf-8"))

        # 解析Controller路径
        controllers = self._parse_controller_paths(tree)
        for controller in controllers:
            global_graph_info.add_controller(controller)

        # 解析方法调用并添加到METHOD类型的attributes中
        method_calls = self._parse_method_calls(tree, file_path, root_path)
        for method in global_graph_info.get_methods():
            method['attributes']['method_calls'] = method_calls

        return self.parse(file_path, root_path, global_graph_info, level)