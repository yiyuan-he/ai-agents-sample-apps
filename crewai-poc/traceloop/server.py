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
from traceloop.sdk import Traceloop
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

# Initialize Traceloop
Traceloop.init()

# FastAPI app
app = FastAPI(title="CrewAI Traceloop Demo")

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
    
    # Analyst Agent
    analyst = Agent(
        role="Data Analyst",
        goal="Analyze queries and provide data-driven insights",
        backstory="You are an experienced data analyst who excels at breaking down complex questions and providing clear, actionable insights based on available information.",
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3  # Limit iterations to prevent excessive API calls
    )
    
    # Strategist Agent
    strategist = Agent(
        role="Strategic Advisor",
        goal="Provide strategic recommendations based on analysis",
        backstory="You are a strategic advisor who takes analytical insights and transforms them into actionable recommendations and strategic guidance.",
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3  # Limit iterations to prevent excessive API calls
    )
    
    # Analysis Task
    analysis_task = Task(
        description=f"Analyze the following query and provide detailed insights: {query}",
        expected_output="A comprehensive analysis with key findings and data points",
        agent=analyst
    )
    
    # Strategy Task
    strategy_task = Task(
        description="Based on the analysis, provide strategic recommendations and actionable next steps",
        expected_output="Clear strategic recommendations with actionable steps the user can take",
        agent=strategist,
        context=[analysis_task]
    )
    
    # Create and return crew
    return Crew(
        agents=[analyst, strategist],
        tasks=[analysis_task, strategy_task],
        verbose=True,
        process=Process.sequential
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CrewAI Traceloop Demo",
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
                "agents_used": ["analyst", "strategist"],
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
                    "agents_used": ["analyst", "strategist"]
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
        sample_query = "What are the key trends in artificial intelligence and how can businesses leverage them?"
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
        "service": "crewai-traceloop"
    }

if __name__ == "__main__":
    # Run the FastAPI app
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)