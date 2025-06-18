from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import asyncio
from strands import Agent, tool
from strands_tools import calculator, current_time, python_repl
from strands.telemetry.tracer import get_tracer

# Configure the tracer
tracer = get_tracer(
    service_name="strands-agent-api",
    otlp_endpoint="http://localhost:4318",
    otlp_headers={"Authorization": "Bearer TOKEN"},
    enable_console_export=True  # Helpful for development
)

# Initialize FastAPI app
app = FastAPI(
    title="Strands Agent Sample API",
    description="A sample API using Strands agents with tool capabilities",
    version="1.0.0"
)

# Define a custom tool as a Python function using the @tool decorator
@tool
def letter_counter(word: str, letter: str) -> int:
    """
    Count occurrences of a specific letter in a word.

    Args:
        word (str): The input word to search in
        letter (str): The specific letter to count

    Returns:
        int: The number of occurrences of the letter in the word
    """
    if not isinstance(word, str) or not isinstance(letter, str):
        return 0

    if len(letter) != 1:
        raise ValueError("The 'letter' parameter must be a single character")

    return word.lower().count(letter.lower())

# Create an agent with tools
agent = Agent(
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    system_prompt="You are a helpful AI assistant",
    tools=[calculator, current_time, python_repl, letter_counter]
)

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
    "What is the current time?",
    "Calculate 1234 * 5678",
    "How many letter 'e's are in the word 'elephant'?",
    "What is 15% of 200?",
    "Write a Python function to calculate factorial and test it with 5",
    "What is the square root of 144?",
    "Count the vowels in 'artificial intelligence'",
    "Calculate the compound interest on $1000 at 5% for 3 years",
    "What day of the week is it?",
    "Solve the equation: 2x + 5 = 13"
]

@app.get("/")
async def root():
    """Root endpoint providing API information"""
    return {
        "service": "Strands Agent Sample API",
        "version": "1.0.0",
        "endpoints": {
            "/": "This information",
            "/health": "Health check endpoint",
            "/chat": "Chat with the AI agent",
            "/batch": "Process multiple messages in batch",
            "/sample": "Run sample prompts",
            "/tools": "List available tools",
            "/docs": "Interactive API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "strands-agent-api"}

@app.get("/tools")
async def list_tools():
    """List all available tools"""
    return {
        "tools": [
            {
                "name": "calculator",
                "description": "Perform mathematical calculations"
            },
            {
                "name": "current_time",
                "description": "Get the current date and time"
            },
            {
                "name": "python_repl",
                "description": "Execute Python code"
            },
            {
                "name": "letter_counter",
                "description": "Count occurrences of a specific letter in a word"
            }
        ]
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process a single chat message"""
    try:
        # Run the agent synchronously (since strands doesn't provide async interface)
        def run_agent():
            result = agent(request.message)
            # Extract the response text from the agent's response
            if hasattr(result, 'content'):
                return result.content
            elif isinstance(result, str):
                return result
            else:
                return str(result)
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, run_agent)
        
        return ChatResponse(response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

@app.post("/batch", response_model=BatchChatResponse)
async def batch_chat(request: BatchChatRequest):
    """Process multiple messages in batch"""
    try:
        # Process messages concurrently using thread pool
        async def process_message(message):
            def run_agent():
                result = agent(message)
                if hasattr(result, 'content'):
                    return result.content
                elif isinstance(result, str):
                    return result
                else:
                    return str(result)
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, run_agent)
        
        # Process all messages concurrently
        responses = await asyncio.gather(*[process_message(msg) for msg in request.messages])
        
        return BatchChatResponse(responses=responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch request: {str(e)}")

@app.get("/sample")
async def run_samples():
    """Run sample prompts to demonstrate the API"""
    try:
        # Process sample messages
        async def process_sample(message):
            def run_agent():
                result = agent(message)
                if hasattr(result, 'content'):
                    return result.content
                elif isinstance(result, str):
                    return result
                else:
                    return str(result)
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, run_agent)
        
        # Process first 5 samples to avoid long wait times
        sample_subset = SAMPLE_MESSAGES[:5]
        results = await asyncio.gather(*[process_sample(msg) for msg in sample_subset])
        
        # Format the response
        samples = []
        for i, (message, result) in enumerate(zip(sample_subset, results)):
            samples.append({
                "index": i + 1,
                "prompt": message,
                "response": result
            })
        
        return {
            "message": "Sample prompts processed successfully",
            "note": f"Showing first {len(sample_subset)} of {len(SAMPLE_MESSAGES)} available samples",
            "samples": samples
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running samples: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    print("Starting Strands Agent FastAPI server...")
    print("API documentation available at: http://localhost:8000/docs")
    print("\nAvailable tools:")
    print("- calculator: Perform mathematical calculations")
    print("- current_time: Get the current date and time")
    print("- python_repl: Execute Python code")
    print("- letter_counter: Count occurrences of a letter in a word")
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=8000)