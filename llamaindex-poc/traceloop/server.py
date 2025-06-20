from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.ollama import Ollama
from llama_index.core.chat_engine import SimpleChatEngine
from traceloop.sdk import Traceloop
import uvicorn

# Initialize Traceloop
Traceloop.init(app_name="llamaindex-fastapi-server")

# Initialize FastAPI
app = FastAPI(title="LlamaIndex Chat API")

# Configure Ollama
llm = Ollama(model="llama3.2", request_timeout=60.0)

# Create chat engine with memory
memory = ChatMemoryBuffer.from_defaults(token_limit=1500)
chat_engine = SimpleChatEngine.from_defaults(
    llm=llm,
    memory=memory,
    system_prompt=(
        "You are a helpful AI assistant. "
        "Answer questions and maintain conversation history."
    )
)

# Request/Response models
class ChatRequest(BaseModel):
    prompt: str

class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "LlamaIndex Chat API is running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        response = chat_engine.chat(request.prompt)
        return ChatResponse(response=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)