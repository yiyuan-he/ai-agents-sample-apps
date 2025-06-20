import os
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.bedrock import Bedrock

# OpenInference instrumentation
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from openinference.instrumentation.llama_index import LlamaIndexInstrumentor

# Set up OpenTelemetry
resource = Resource.create({"service.name": "llamaindex-chat-agent"})
trace.set_tracer_provider(TracerProvider(resource=resource))
tracer_provider = trace.get_tracer_provider()

# Configure OTLP exporter (defaults to localhost:4317)
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317"),
    insecure=True
)
span_processor = BatchSpanProcessor(otlp_exporter)
tracer_provider.add_span_processor(span_processor)

# Instrument LlamaIndex
LlamaIndexInstrumentor().instrument()

# Initialize FastAPI app
app = FastAPI(title="LlamaIndex Chat Agent")

# Initialize Bedrock LLM
llm = Bedrock(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    aws_region=os.getenv("AWS_REGION", "us-west-2"),
    max_tokens=1024,
    temperature=0.7
)

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
    return {"message": "Welcome to LlamaIndex Chat Agent with OpenInference!"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        # Chat with the engine
        response = chat_engine.chat(request.prompt)
        return ChatResponse(response=str(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check() -> Dict[str, str]:
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)