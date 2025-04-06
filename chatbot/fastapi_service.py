from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from model_manager import ModelManager
from pydantic import BaseModel
import os
from langchain.schema import HumanMessage, AIMessage

app = FastAPI()

# Allow CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_manager = ModelManager()

class ChatRequest(BaseModel):
    message: str

class SwitchModelRequest(BaseModel):
    model_name: str

@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        print(f"Initializing model... Current model: {os.getenv('CURRENT_MODEL', 'deepseek')}")
        model = model_manager.get_model()
        if not model:
            print("Failed to initialize model - check config.yaml and API keys")
            raise HTTPException(status_code=500, detail="Failed to initialize model - check config.yaml and API keys")
        print(f"Model initialized successfully: {type(model).__name__}")
    except Exception as e:
        import traceback
        print(f"Model initialization error: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Model initialization error: {str(e)}")
    
    try:
        print(f"Processing message: {request.message[:100]}...")
        # Add user message to history
        model_manager.add_to_history(request.message, "user")
        
        # Get conversation history for context
        history = model_manager.get_history()
        print(f"History length: {len(history)}")
        messages = [
            HumanMessage(content=msg['text']) if msg['sender'] == 'user' 
            else AIMessage(content=msg['text']) 
            for msg in history
        ]
        
        print(f"Invoking model with {len(messages)} messages")
        response = await model.ainvoke(messages)
        
        # Add AI response to history
        model_manager.add_to_history(response.content, "ai")
        
        return {"response": response.content}
    except Exception as e:
        import traceback
        print(f"Error during chat processing: {str(e)}")
        print(f"Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/switch_model")
async def switch_model(request: SwitchModelRequest):
    success = model_manager.switch_model(request.model_name)
    if not success:
        raise HTTPException(status_code=400, detail="Invalid model name")
    return {"status": "success", "model": request.model_name}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)