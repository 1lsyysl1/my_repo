from model_manager import ModelManager
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import os

class ChatBot:
    def __init__(self):
        self.model_manager = ModelManager()
        self.conversation = ConversationChain(
            llm=self.model_manager.get_model(),
            memory=ConversationBufferMemory()
        )

    def switch_model(self, model_name: str):
        success = self.model_manager.switch_model(model_name)
        if success:
            self.conversation.llm = self.model_manager.get_model()
            return model_name
        return False

    def chat(self):
        print("ChatBot initialized. Type '/switch [azure|deepseek]' to change model")
        while True:
            user_input = input("You: ")
            
            if user_input.startswith('/switch'):
                _, model = user_input.split()
                if self.switch_model(model.strip()):
                    print(f"Switched to {model} model")
                else:
                    print("Invalid model name")
                continue
            
            response = self.conversation.predict(input=user_input)
            print(f"Bot: {response}")

if __name__ == "__main__":
    bot = ChatBot()
    bot.chat()