# OpenLLMetry LangChain Sample Application

This sample application demonstrates how to use LangChain with OpenLLMetry instrumentation for OpenTelemetry tracing, using AWS Bedrock for language models. It includes both a CLI application and a FastAPI server with traffic generation capabilities.

## Features

- **LangChain Integration**: Uses AWS Bedrock Claude models through LangChain
- **OpenLLMetry Instrumentation**: Automatic tracing of LangChain operations
- **OpenTelemetry Integration**: Sends traces to both console and OTLP endpoints
- **FastAPI Server**: RESTful API with multiple endpoints
- **Traffic Generation**: Automated script for continuous load testing

## Prerequisites

- Python 3.8+
- AWS account with Bedrock access
- AWS credentials configured
- curl and jq (for traffic generation script)

## Setup Instructions

### 1. Configure AWS Credentials

The application uses AWS Bedrock for language models. Ensure you have AWS credentials configured:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Option 3: IAM role (if running on EC2/Lambda)
```

**Note**: Make sure you have access to Claude models in AWS Bedrock. You may need to request access through the AWS Console.

### 2. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

### CLI Mode

The CLI application provides an interactive chat interface:

```bash
python app.py
```

Type your messages and press Enter. Type 'exit' to quit.

### FastAPI Server Mode

The server provides a RESTful API with automatic documentation:

```bash
python server.py
```

The server will start on `http://localhost:8002`

#### Available Endpoints

- `GET /` - API information and available endpoints
- `GET /health` - Health check endpoint
- `POST /chat` - Process a single message
- `POST /batch` - Process multiple messages in batch
- `GET /sample` - Run predefined sample prompts
- `GET /docs` - Interactive API documentation (Swagger UI)

#### Example API Usage

```bash
# Single message
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is artificial intelligence?"}'

# Batch messages
curl -X POST http://localhost:8002/batch \
  -H "Content-Type: application/json" \
  -d '{"messages": ["What is ML?", "What is NLP?", "What is computer vision?"]}'

# Run samples
curl http://localhost:8002/sample
```

### Traffic Generation

Generate continuous traffic to test the application:

```bash
./generate_traffic.sh
```

The script will:
- Send random AI/ML-related messages
- Display colored output for success/failure
- Show response times and previews
- Track statistics (total, success, failed)
- Support graceful shutdown with Ctrl+C

#### Configuration Options

Edit the script to customize:
- `DELAY_SECONDS=2` - Delay between requests (in seconds) - increase if you see AWS throttling
- `NUM_REQUESTS=0` - Number of requests (0 for infinite)
- `TIMEOUT=30` - Request timeout in seconds

## OpenTelemetry Configuration

The application sends traces to two destinations:

1. **Console**: Prints traces to stdout for debugging
2. **OTLP**: Sends to `http://localhost:4318/v1/traces`

To use a different OTLP endpoint, modify the endpoint URL in `app.py` or `server.py`:

```python
otlp_exporter = OTLPSpanExporter(endpoint="http://your-collector:4318/v1/traces")
```

### Running with AWS X-Ray

To send traces directly to AWS X-Ray:

```bash
export PYTHONPATH="./otel-init:$PYTHONPATH"
env OTEL_METRICS_EXPORTER=none \
    OTEL_LOGS_EXPORTER=none \
    OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
    OTEL_RESOURCE_ATTRIBUTES="service.name=openllmetry-langchain-app" \
    opentelemetry-instrument python server.py
```

### Viewing Spans in CloudWatch

If using AWS X-Ray, after the application is running, you can view the generated spans in CloudWatch:
1. Open the AWS CloudWatch console
2. Navigate to the "Logs groups" section in the left sidebar
3. Select the `aws/spans` log group to view your trace data

## Troubleshooting

### AWS Credentials Issues

If you get authentication errors:

1. Verify AWS credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Ensure you have access to Bedrock in your region:
   ```bash
   aws bedrock list-foundation-models --region us-east-1
   ```

### Model Access Issues

If you get model access errors:

1. Check that you have access to Claude models in Bedrock
2. Request access through the AWS Console if needed
3. The app uses `anthropic.claude-3-haiku-20240307-v1:0` by default

### Rate Limiting

AWS Bedrock has rate limits. If you see throttling errors:

1. Increase the delay in `generate_traffic.sh`:
   ```bash
   DELAY_SECONDS=10  # or even 20-30
   ```

2. Use simpler prompts to reduce token usage

### Connection Issues

If the OTLP exporter fails to connect:

1. Ensure your OTLP collector is running
2. Check the endpoint URL is correct
3. For local testing, you can comment out the OTLP exporter and use only console output

## Environment Variables

Configure the following environment variables as needed:

```bash
# AWS Configuration (if not using AWS CLI)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Optional: Custom OTLP endpoint
export OTLP_ENDPOINT=http://your-collector:4318/v1/traces

# Optional: Use a different Bedrock model
export BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

## License

This is a sample application for demonstration purposes.