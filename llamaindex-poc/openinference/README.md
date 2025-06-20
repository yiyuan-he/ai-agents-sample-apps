# LlamaIndex Chat Agent with OpenInference

A FastAPI-based chat application using LlamaIndex framework with AWS Bedrock Claude-3 Sonnet model, instrumented with OpenInference for observability through OpenTelemetry.

## Features

- Chat API endpoint powered by LlamaIndex and AWS Bedrock
- Memory-based conversation history
- OpenTelemetry instrumentation for distributed tracing
- FastAPI web framework for RESTful API
- Health check endpoint

## Prerequisites

- Python 3.8 or higher
- AWS account with Bedrock access
- AWS credentials configured (via AWS CLI, environment variables, or IAM role)
- OpenTelemetry Collector running (optional, for trace collection)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd llamaindex-poc/openinference
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root (optional):

```bash
# AWS Configuration
AWS_REGION=us-west-2  # Default region for Bedrock

# OpenTelemetry Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317  # OTLP collector endpoint
```

### 4. Ensure AWS Credentials

Make sure your AWS credentials are configured. You can use any of these methods:

- AWS CLI: `aws configure`
- Environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- IAM role (if running on EC2/ECS/Lambda)

### 5. Run the Application

```bash
python server.py
```

The application will start on `http://0.0.0.0:8000`

## API Endpoints

### Root Endpoint
- **GET** `/`
- Returns a welcome message

### Chat Endpoint
- **POST** `/chat`
- Request body:
  ```json
  {
    "prompt": "Your message here"
  }
  ```
- Response:
  ```json
  {
    "response": "AI assistant response"
  }
  ```

### Health Check
- **GET** `/health`
- Returns:
  ```json
  {
    "status": "healthy"
  }
  ```

## Usage Example

### Using curl:

```bash
# Send a chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'

# Check health
curl http://localhost:8000/health
```

### Using Python:

```python
import requests

# Send a chat message
response = requests.post(
    "http://localhost:8000/chat",
    json={"prompt": "What is LlamaIndex?"}
)
print(response.json())
```

## OpenTelemetry Integration

This application is instrumented with OpenInference for LlamaIndex, which automatically traces:
- LLM calls to AWS Bedrock
- Chat engine operations
- Memory buffer interactions

Traces are exported to an OpenTelemetry Collector at the configured endpoint (default: `localhost:4317`).

### Setting up OpenTelemetry Collector

1. Download and configure the OpenTelemetry Collector
2. Configure it to receive OTLP data on port 4317
3. Set up exporters to your preferred backend (Jaeger, Zipkin, Datadog, etc.)

## Architecture

- **FastAPI**: Web framework for the REST API
- **LlamaIndex**: Orchestration framework for LLM interactions
- **AWS Bedrock**: Managed LLM service (Claude-3 Sonnet model)
- **OpenInference**: Instrumentation library for LlamaIndex observability
- **OpenTelemetry**: Distributed tracing framework

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   - Ensure AWS credentials are properly configured
   - Check if your account has access to Bedrock in the specified region

2. **Model Access Error**
   - Verify you have access to `anthropic.claude-3-sonnet-20240229-v1:0` in your AWS region
   - Some regions may not have all Bedrock models available

3. **Connection to OTLP Endpoint Failed**
   - This is non-fatal; the app will continue to work
   - To fix: ensure OpenTelemetry Collector is running on the configured endpoint

4. **Port Already in Use**
   - Change the port in `server.py` or kill the process using port 8000

## Development

### Running with Different Models

To use a different Bedrock model, modify the `model` parameter in `server.py`:

```python
llm = Bedrock(
    model="your-preferred-model-id",
    aws_region=os.getenv("AWS_REGION", "us-west-2"),
    max_tokens=1024,
    temperature=0.7
)
```

### Customizing the System Prompt

Modify the `system_prompt` in the chat engine initialization to change the AI's behavior:

```python
chat_engine = SimpleChatEngine.from_defaults(
    llm=llm,
    memory=memory,
    system_prompt="Your custom system prompt here"
)
```

## License

[Your License Here]