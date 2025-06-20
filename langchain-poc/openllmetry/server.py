import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
import boto3

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

# Instrument LangChain
LangchainInstrumentor().instrument(tracer_provider=tracer_provider)

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="OpenLLMetry LangChain Sample API",
    description="A sample API using LangChain with OpenLLMetry instrumentation and AWS Bedrock",
    version="1.0.0"
)

# Initialize the LLM with AWS Bedrock
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs={"temperature": 0.7},
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-west-2")
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
    "What is machine learning?",
    "Explain quantum computing in simple terms",
    "What are the benefits of cloud computing?",
    "How does blockchain technology work?",
    "What is the difference between AI and ML?"
]

@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "service": "OpenLLMetry LangChain Sample API",
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
    return {"status": "healthy", "service": "openllmetry-langchain-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a single chat message"""
    try:
        # Process the message through the chain asynchronously
        response = await asyncio.to_thread(chain.invoke, {"input": request.message})
        return ChatResponse(response=response["text"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/batch", response_model=BatchChatResponse)
async def batch_chat(request: BatchChatRequest):
    """Process multiple messages in batch"""
    try:
        # Process all messages concurrently
        tasks = [asyncio.to_thread(chain.invoke, {"input": message}) for message in request.messages]
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
        tasks = [asyncio.to_thread(chain.invoke, {"input": message}) for message in SAMPLE_MESSAGES]
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
    
    # Check if AWS credentials are available
    try:
        # Try to create a bedrock client to verify credentials
        bedrock = boto3.client('bedrock-runtime', region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
        print("AWS credentials configured successfully.")
    except Exception as e:
        print("Error: AWS credentials not properly configured.")
        print("Please configure AWS credentials using:")
        print("  - AWS CLI: aws configure")
        print("  - Environment variables: AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        print("  - IAM role (if running on EC2/Lambda)")
        print(f"\nError details: {e}")
        exit(1)
    
    print("Starting OpenLLMetry LangChain FastAPI server with AWS Bedrock...")
    print("API documentation available at: http://localhost:8002/docs")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8002)
