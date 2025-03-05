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
        # 解析Controller的路径信息
        # 这里可以根据具体项目结构实现路径解析逻辑
        return "/api/" + node.text.decode().lower()

    def parse_file(self, file_path: str, root_path: str, global_graph_info: GlobalGraphInfo, level: int):
        parser = tree_sitter_languages.get_parser(self.language)
        with open(file_path, "r") as file:
            code = file.read()
        tree = parser.parse(bytes(code, "utf-8"))

        # 解析Controller路径
        controllers = self._parse_controller_paths(tree)
        for controller in controllers:
            global_graph_info.add_controller(controller)

        return self.parse(file_path, root_path, global_graph_info, level)