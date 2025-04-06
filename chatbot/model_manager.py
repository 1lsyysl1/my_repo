from typing import Optional, List, Dict
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
import yaml
import os
import datetime

class ModelManager:
    def __init__(self, config_path: str = os.path.join(os.path.dirname(__file__), 'config.yaml')):
        self.config_path = config_path
        self.models = {
            'azure': self._init_azure,
            'deepseek': self._init_deepseek
        }
        self.current_model = None
        self.conversation_history: List[Dict] = []
        self._load_config()

    def _load_config(self):
        with open(self.config_path) as f:
            self.config = yaml.safe_load(f)

    def _init_azure(self):
        return AzureChatOpenAI(
            openai_api_key=self.config['azure']['api_key'],
            api_version=self.config['azure']['api_version'],
            azure_endpoint=self.config['azure']['azure_endpoint'],
            temperature=0.7
        )

    def _init_deepseek(self):
        return ChatOpenAI(
            api_key=self.config['deepseek']['api_key'],
            base_url=self.config['deepseek']['base_url'],
            temperature=0.5,
            model_name='deepseek-chat'
        )

    def switch_model(self, model_name: str):
        if model_name in self.models:
            self.current_model = self.models[model_name]()
            os.environ['CURRENT_MODEL'] = model_name
            return True
        return False

    def get_model(self) -> Optional[ChatOpenAI]:
        try:
            if self.current_model:
                return self.current_model
            
            model_name = os.getenv('CURRENT_MODEL', 'deepseek')
            if model_name in self.models:
                model = self.models[model_name]()
                self.current_model = model
                return model
            return None
        except Exception as e:
            print(f"Error initializing model: {str(e)}")
            return None
            
    def add_to_history(self, message: str, sender: str):
        self.conversation_history.append({
            'text': message,
            'sender': sender,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
    def get_history(self) -> List[Dict]:
        return self.conversation_history
        
    def clear_history(self):
        self.conversation_history = []