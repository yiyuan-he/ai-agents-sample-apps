from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
import os
from customer_support_assistant import CustomerSupportAssistant
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import json

app = FastAPI(title="Customer Support Chat API", version="1.0.0")

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thread_id: str

# Global assistant instance
assistant = None

@app.on_event("startup")
async def startup_event():
    global assistant
    assistant = CustomerSupportAssistant()

@app.get("/")
async def root():
    return {"message": "Customer Support Chat API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not assistant:
            raise HTTPException(status_code=500, detail="Assistant not initialized")
        
        # Generate thread_id if not provided
        thread_id = request.thread_id or str(uuid.uuid4())
        
        # Submit the query to the assistant
        result, returned_thread_id = assistant.submit(
            query=request.message,
            thread_id=thread_id if request.thread_id else None
        )
        
        # Extract the last AI message from the result
        messages = result.get('messages', [])
        if not messages:
            raise HTTPException(status_code=500, detail="No response generated")
        
        last_message = messages[-1]
        response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        return ChatResponse(
            response=response_content,
            thread_id=returned_thread_id or thread_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)