# OpenLLMetry LangChain Sample Application

This sample application demonstrates how to use LangChain with OpenLLMetry instrumentation for OpenTelemetry tracing, using AWS Bedrock for language models.

## Prerequisites

- AWS credentials configured
- Transaction Search enabled on your AWS Account: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html
- Access to Claude models in AWS Bedrock

## Setup

1. **Set up virtual environment:**
   ```bash
   uv venv
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Run the application:**

   **CLI Mode:**
   ```bash
   python app.py
   ```
   Type your messages and press Enter. Type 'exit' to quit.

   **Server Mode:**
   ```bash
   python server.py
   ```
   The server will start on `http://localhost:8002`

### Running with AWS X-Ray

To send traces directly to AWS X-Ray:
```bash
env OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
    OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-openllmetry-app" \
    AGENT_OBSERVABILITY_ENABLED="true" \
    opentelemetry-instrument python server.py
```

## API Endpoints

- `GET /` - API information and available endpoints
- `GET /health` - Health check endpoint
- `POST /chat` - Process a single message
- `POST /batch` - Process multiple messages in batch
- `GET /sample` - Run predefined sample prompts
- `GET /docs` - Interactive API documentation (Swagger UI)

## Example API Usage

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

## Traffic Generation

Generate continuous traffic to test the application:
```bash
./generate_traffic.sh
```

Configuration options:
- `DELAY_SECONDS=2` - Delay between requests (increase if you see AWS throttling)
- `NUM_REQUESTS=0` - Number of requests (0 for infinite)
- `TIMEOUT=30` - Request timeout in seconds

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:
1. Open the AWS CloudWatch console
2. Navigate to the "Logs groups" section in the left sidebar
3. Select the `aws/spans` log group to view your trace data