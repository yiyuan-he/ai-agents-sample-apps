import os
import asyncio
import boto3
import json
from datetime import datetime, timezone
from typing import Dict, List, Any
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import openlit
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

# Initialize OpenLit
openlit.init()

# FastAPI app
app = FastAPI(title="CrewAI OpenLit Demo with Bedrock Converse")

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

# Initialize Bedrock client
def get_bedrock_client():
    region = os.getenv("AWS_DEFAULT_REGION", "us-west-2")
    return boto3.client('bedrock-runtime', region_name=region)

# Custom wrapper for Bedrock Converse API
class BedrockConverseWrapper:
    def __init__(self):
        self.client = get_bedrock_client()
        self.model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
    
    def converse(self, message: str, max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Use Bedrock Converse API to get response"""
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=[
                    {
                        "role": "user",
                        "content": [{"text": message}]
                    }
                ],
                inferenceConfig={
                    "maxTokens": max_tokens,
                    "temperature": temperature
                }
            )
            
            # Extract the assistant's response
            return response['output']['message']['content'][0]['text']
        except Exception as e:
            logger.error(f"Error calling Bedrock Converse API: {str(e)}")
            raise

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

# Create CrewAI agents with custom tasks
def create_support_crew(query: str) -> Crew:
    """Create a support crew for processing queries"""
    llm = get_llm()
    
    # Technical Support Agent
    tech_support = Agent(
        role="Technical Support Specialist",
        goal="Provide expert technical assistance and troubleshooting guidance",
        backstory="You are an experienced technical support specialist with deep knowledge of software systems, debugging techniques, and best practices for resolving technical issues.",
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3
    )
    
    # Documentation Expert
    doc_expert = Agent(
        role="Documentation Expert",
        goal="Create clear and comprehensive documentation and guides",
        backstory="You are a documentation specialist who excels at creating user-friendly guides, tutorials, and explanations that help users understand complex technical concepts.",
        verbose=True,
        llm=llm,
        allow_delegation=False,
        max_iter=3
    )
    
    # Troubleshooting Task
    troubleshoot_task = Task(
        description=f"Analyze and provide solutions for the following issue: {query}",
        expected_output="A detailed troubleshooting guide with step-by-step solutions and potential root causes",
        agent=tech_support
    )
    
    # Documentation Task
    doc_task = Task(
        description="Create a user-friendly guide based on the troubleshooting analysis",
        expected_output="A clear, well-structured guide that users can follow to resolve their issue",
        agent=doc_expert,
        context=[troubleshoot_task]
    )
    
    # Create and return crew
    return Crew(
        agents=[tech_support, doc_expert],
        tasks=[troubleshoot_task, doc_task],
        verbose=True,
        process=Process.sequential
    )

# Direct Bedrock Converse endpoint for comparison
@app.post("/converse")
async def converse_direct(request: ChatRequest):
    """Direct Bedrock Converse API call (bypassing CrewAI)"""
    try:
        logger.info(f"Processing direct converse request: {request.message}")
        
        bedrock_wrapper = BedrockConverseWrapper()
        response_text = bedrock_wrapper.converse(request.message)
        
        response = ChatResponse(
            response=response_text,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "model": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                "api": "bedrock-converse",
                "direct_call": True
            }
        )
        
        logger.info(f"Direct converse response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error processing converse request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "CrewAI OpenLit Demo with Bedrock Converse",
        "version": "1.0.0",
        "endpoints": ["/chat", "/converse", "/batch", "/sample", "/health"]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a single chat message using CrewAI"""
    try:
        logger.info(f"Processing chat request: {request.message}")
        
        # Create and run crew
        crew = create_support_crew(request.message)
        result = crew.kickoff()
        
        response = ChatResponse(
            response=str(result),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={
                "model": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                "agents_used": ["tech_support", "doc_expert"],
                "process": "sequential",
                "api": "bedrock-via-crewai"
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
            crew = create_support_crew(message)
            result = crew.kickoff()
            
            responses.append(ChatResponse(
                response=str(result),
                timestamp=datetime.now(timezone.utc).isoformat(),
                metadata={
                    "model": os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                    "agents_used": ["tech_support", "doc_expert"],
                    "api": "bedrock-via-crewai"
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
        sample_query = "How do I troubleshoot high memory usage in a Python application?"
        logger.info(f"Running sample query: {sample_query}")
        
        crew = create_support_crew(sample_query)
        result = crew.kickoff()
        
        return {
            "query": sample_query,
            "response": str(result),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error running sample: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "crewai-openlit"
    }

if __name__ == "__main__":
    # Run the FastAPI app
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)