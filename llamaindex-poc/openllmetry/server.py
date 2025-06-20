import os
from typing import Dict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.llms.bedrock_converse import BedrockConverse

# OpenTelemetry and OpenLLMetry setup
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# OpenLLMetry instrumentation
from opentelemetry.instrumentation.llamaindex import LlamaIndexInstrumentor

# Set up OpenTelemetry
resource = Resource.create({
    "service.name": "llamaindex-chat-agent-openllmetry",
    "service.version": "1.0.0"
})

# Configure tracer provider
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# Configure OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317"),
    insecure=True
)

# Add span processor
span_processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(span_processor)

# Instrument LlamaIndex with OpenLLMetry
LlamaIndexInstrumentor().instrument(
    tracer_provider=provider
)

# Initialize FastAPI app
app = FastAPI(title="LlamaIndex Chat Agent with OpenLLMetry")

# Initialize Bedrock Converse LLM
llm = BedrockConverse(
    model="anthropic.claude-3-sonnet-20240229-v1:0",
    region_name=os.getenv("AWS_REGION", "us-west-2"),
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
    return {"message": "Welcome to LlamaIndex Chat Agent with OpenLLMetry!"}

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