import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

import openlit

# Set up OpenTelemetry with BOTH exporters
tracer_provider = TracerProvider()

# Add Console exporter
console_exporter = ConsoleSpanExporter()
console_processor = BatchSpanProcessor(console_exporter)
tracer_provider.add_span_processor(console_processor)

# Add OTLP exporter
otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
otlp_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(otlp_processor)

# Set as global provider
trace.set_tracer_provider(tracer_provider)

# Initialize OpenLit
openlit.init()

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="OpenLit LangChain Sample API",
    description="A sample API using LangChain with Ollama and OpenLit instrumentation",
    version="1.0.0"
)

# Initialize the LLM with Ollama
llm = ChatOllama(
    model="llama3.2",
    temperature=0.7,
    base_url="http://localhost:11434"
)

# Create a prompt template
prompt = ChatPromptTemplate.from_template(
    "You are a helpful assistant. The user says: {input}. Provide a helpful response."
)

# Create a chain
chain = LLMChain(llm=llm, prompt=prompt)

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class BatchChatRequest(BaseModel):
    messages: List[str]

class BatchChatResponse(BaseModel):
    responses: List[str]

# Sample messages for the /sample endpoint
SAMPLE_MESSAGES = [
    "What is the capital of France?",
    "How do I make a perfect cup of coffee?",
    "Explain quantum computing in simple terms",
    "What are the benefits of exercise?",
    "How can I improve my productivity?"
]

@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "service": "OpenLit LangChain Sample API",
        "version": "1.0.0",
        "endpoints": {
            "/": "This information",
            "/health": "Health check endpoint",
            "/chat": "Chat with the AI assistant",
            "/batch": "Process multiple messages in batch",
            "/sample": "Run sample prompts",
            "/docs": "Interactive API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "openlit-langchain-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a single chat message"""
    try:
        # Process the message through the chain
        response = await chain.ainvoke({"input": request.message})
        return ChatResponse(response=response["text"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/batch", response_model=BatchChatResponse)
async def batch_chat(request: BatchChatRequest):
    """Process multiple messages in batch"""
    try:
        # Process all messages concurrently
        tasks = [chain.ainvoke({"input": message}) for message in request.messages]
        results = await asyncio.gather(*tasks)
        
        # Extract responses
        responses = [result["text"] for result in results]
        return BatchChatResponse(responses=responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch request: {str(e)}")

@app.get("/sample")
async def run_samples():
    """Run sample prompts to demonstrate the API"""
    try:
        # Process sample messages
        tasks = [chain.ainvoke({"input": message}) for message in SAMPLE_MESSAGES]
        results = await asyncio.gather(*tasks)
        
        # Format the response
        samples = []
        for i, (message, result) in enumerate(zip(SAMPLE_MESSAGES, results)):
            samples.append({
                "index": i + 1,
                "prompt": message,
                "response": result["text"]
            })
        
        return {
            "message": "Sample prompts processed successfully",
            "samples": samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running samples: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Check if Ollama is accessible
    print("Make sure Ollama is running locally.")
    print("If not installed, visit: https://ollama.ai")
    print("Then run: ollama pull llama3.2")
    print("")
    print("Starting FastAPI server...")
    print("API documentation available at: http://localhost:8000/docs")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)