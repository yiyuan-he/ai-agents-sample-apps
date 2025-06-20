import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.crewai import CrewAIInstrumentor
import uvicorn
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Initialize CrewAI instrumentation
CrewAIInstrumentor().instrument(tracer_provider=tracer_provider)

# FastAPI app
app = FastAPI(title="CrewAI OpenLLMetry Demo")

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    context: Dict[str, Any] = {}

class ChatResponse(BaseModel):
    response: str
    timestamp: str
    metadata: Dict[str, Any] = {}

class BatchRequest(BaseModel):
    messages: List[str]

class BatchResponse(BaseModel):
    responses: List[ChatResponse]

# Initialize LLM with AWS Bedrock
def get_llm():
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    
    try:
        # Use CrewAI's LLM class with Bedrock
        llm = LLM(
            model=f"bedrock/{model_id}",
            temperature=0.7,
            max_tokens=512,
            aws_region_name=region
        )
        logger.info(f"Successfully initialized Bedrock LLM with model: {model_id} in region: {region}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock LLM: {str(e)}")
        logger.error("Please ensure you have proper AWS credentials configured and access to the Bedrock model")
        raise

# Create CrewAI agents
def create_analysis_crew(query: str) -> Crew:
    """Create an analysis crew for processing queries"""
    llm = get_llm()
    
    # Research Agent
    researcher = Agent(
        role="Research Analyst",
        goal="Research and gather comprehensive information on topics",
        backstory="You are a meticulous researcher who excels at finding relevant information and presenting it in a clear, organized manner.",
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3  # Limit iterations to prevent excessive API calls
    )
    
    # Writer Agent
    writer = Agent(
        role="Content Writer",
        goal="Transform research into engaging and informative content",
        backstory="You are a skilled writer who takes complex information and transforms it into clear, engaging content that is easy to understand.",
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3  # Limit iterations to prevent excessive API calls
    )
    
    # Research Task
    research_task = Task(
        description=f"Research the following topic thoroughly: {query}",
        expected_output="A comprehensive research summary with key findings and relevant information",
        agent=researcher
    )
    
    # Writing Task
    writing_task = Task(
        description="Based on the research, create a well-structured and engaging response",
        expected_output="A clear, informative, and engaging response that addresses the query comprehensively",
        agent=writer,
        context=[research_task]
    )
    
    # Create and return crew
    return Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        verbose=True,
        process=Process.sequential
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CrewAI OpenLLMetry Demo",
        "version": "1.0.0",
        "endpoints": ["/chat", "/batch", "/sample", "/health"]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a single chat message using CrewAI"""
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        # Create and run crew
        crew = create_analysis_crew(request.message)
        result = crew.kickoff()
        
        response = ChatResponse(
            response=str(result),
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                "model": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                "agents_used": ["researcher", "writer"],
                "process": "sequential"
            }
        )
        
        logger.info(f"Chat response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch", response_model=BatchResponse)
async def batch_chat(request: BatchRequest):
    """Process multiple messages in batch"""
    try:
        logger.info(f"Processing batch request with {len(request.messages)} messages")
        
        responses = []
        for message in request.messages:
            crew = create_analysis_crew(message)
            result = crew.kickoff()
            
            responses.append(ChatResponse(
                response=str(result),
                timestamp=datetime.utcnow().isoformat(),
                metadata={
                    "model": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                    "agents_used": ["researcher", "writer"]
                }
            ))
        
        logger.info(f"Batch processing completed successfully")
        return BatchResponse(responses=responses)
        
    except Exception as e:
        logger.error(f"Error processing batch request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sample")
async def sample():
    """Run a sample query for testing"""
    try:
        sample_query = "What are the best practices for implementing observability in microservices architectures?"
        logger.info(f"Running sample query: {sample_query}")
        
        crew = create_analysis_crew(sample_query)
        result = crew.kickoff()
        
        return {
            "query": sample_query,
            "response": str(result),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running sample: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "crewai-openllmetry"
    }

if __name__ == "__main__":
    # Run the FastAPI app
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)