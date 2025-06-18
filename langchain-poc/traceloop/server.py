import os
from typing import Dict
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_aws import ChatBedrock
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from traceloop.sdk import Traceloop

# Load environment variables
load_dotenv()

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

Traceloop.init()

# Initialize FastAPI app
app = FastAPI(title="LangChain Bedrock API", version="1.0.0")

# Initialize the LLM with AWS Bedrock
llm = ChatBedrock(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    model_kwargs={
        "temperature": 0.7,
        "max_tokens": 500
    },
    region_name=os.getenv("AWS_DEFAULT_REGION", "us-west-2")
)

# Create a prompt template
prompt = ChatPromptTemplate.from_template(
    "You are a helpful assistant. The user says: {input}. Provide a helpful response."
)

# Create a chain
chain = LLMChain(llm=llm, prompt=prompt)

# Request model
class ChatRequest(BaseModel):
    message: str

# Response model
class ChatResponse(BaseModel):
    response: str

@app.get("/")
async def root():
    return {"message": "LangChain Bedrock API is running!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes user messages through AWS Bedrock
    """
    try:
        # Process the input through the chain
        result = await chain.ainvoke({"input": request.message})
        return ChatResponse(response=result["text"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server with AWS Bedrock...")
    print("Make sure AWS credentials are configured")
    print("Server will run on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)