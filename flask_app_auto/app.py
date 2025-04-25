import json
import boto3
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(title="Bedrock API Server", description="Server for interacting with AWS Bedrock models")

class BedrockRequest(BaseModel):
    input: str
    model: Optional[str] = "us.anthropic.claude-3-5-sonnet-20241022-v2:0"

@app.post("/invoke")
async def invoke_bedrock(request: BedrockRequest = Body(...)):
    """
    Invoke an AWS Bedrock model with the provided input text.
    """
    try:
        # Initialize the Bedrock Runtime client
        bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
        
        # Prepare the request body
        request_body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": request.input
                        }
                    ]
                }
            ],
            "temperature": 0.5,
            "top_p": 1
        })
        
        # Invoke the Bedrock model
        response = bedrock_runtime.invoke_model(
            modelId=request.model,
            contentType='application/json',
            accept='application/json',
            body=request_body
        )
        
        # Parse and return the response
        response_body = json.loads(response['body'].read())
        
        return {
            'statusCode': 200,
            'response': response_body['content'][0]['text']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error invoking Bedrock model: {str(e)}")

@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the server is running.
    """
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
