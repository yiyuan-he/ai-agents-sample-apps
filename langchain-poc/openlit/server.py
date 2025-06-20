import os
import asyncio
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

import openlit

# Set up OpenTelemetry with BOTH exporters
tracer_provider = TracerProvider()

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
    title="OpenLit Bedrock Converse API",
    description="A sample API using AWS Bedrock Converse API with OpenLit instrumentation",
    version="1.0.0"
)

# Initialize Bedrock client
bedrock_runtime = boto3.client(
    'bedrock-runtime',
    region_name='us-west-2'
)

# Model configuration
MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'
MAX_TOKENS = 300
TEMPERATURE = 0.7

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
        "service": "OpenLit Bedrock Converse API",
        "version": "1.0.0",
        "model": MODEL_ID,
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
    return {"status": "healthy", "service": "openlit-bedrock-api"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a single chat message using Bedrock Converse API"""
    try:
        # Prepare messages for converse API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "text": f"You are a helpful assistant. The user says: {request.message}. Provide a helpful response."
                    }
                ]
            }
        ]
        
        # Inference configuration
        inference_config = {
            "maxTokens": MAX_TOKENS,
            "temperature": TEMPERATURE,
            "topP": 1
        }
        
        # Call Bedrock converse API
        response = bedrock_runtime.converse(
            modelId=MODEL_ID,
            messages=messages,
            inferenceConfig=inference_config
        )
        
        # Extract response text
        output_message = response['output']['message']
        text_content = output_message['content'][0]['text']
        
        return ChatResponse(response=text_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/batch", response_model=BatchChatResponse)
async def batch_chat(request: BatchChatRequest):
    """Process multiple messages in batch"""
    try:
        async def process_message(message: str) -> str:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"You are a helpful assistant. The user says: {message}. Provide a helpful response."
                        }
                    ]
                }
            ]
            
            inference_config = {
                "maxTokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "topP": 1
            }
            
            response = bedrock_runtime.converse(
                modelId=MODEL_ID,
                messages=messages,
                inferenceConfig=inference_config
            )
            
            return response['output']['message']['content'][0]['text']
        
        # Process all messages concurrently
        tasks = [process_message(message) for message in request.messages]
        responses = await asyncio.gather(*tasks)
        
        return BatchChatResponse(responses=responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch request: {str(e)}")

@app.get("/sample")
async def run_samples():
    """Run sample prompts to demonstrate the API"""
    try:
        async def process_sample(message: str) -> str:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": f"You are a helpful assistant. The user says: {message}. Provide a helpful response."
                        }
                    ]
                }
            ]
            
            inference_config = {
                "maxTokens": MAX_TOKENS,
                "temperature": TEMPERATURE,
                "topP": 1
            }
            
            response = bedrock_runtime.converse(
                modelId=MODEL_ID,
                messages=messages,
                inferenceConfig=inference_config
            )
            
            return response['output']['message']['content'][0]['text']
        
        # Process sample messages
        tasks = [process_sample(message) for message in SAMPLE_MESSAGES]
        results = await asyncio.gather(*tasks)
        
        # Format the response
        samples = []
        for i, (message, result) in enumerate(zip(SAMPLE_MESSAGES, results)):
            samples.append({
                "index": i + 1,
                "prompt": message,
                "response": result
            })
        
        return {
            "message": "Sample prompts processed successfully",
            "samples": samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running samples: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Check AWS credentials
    print("Make sure AWS credentials are configured.")
    print("Using AWS Region: us-west-2")
    print(f"Using Model: {MODEL_ID}")
    print("")
    print("Starting FastAPI server...")
    print("API documentation available at: http://localhost:8003/docs")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8003)
