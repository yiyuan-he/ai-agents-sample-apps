# OpenInference LangChain Sample Application

## Prerequisites

- AWS credentials configured
- Transaction Search enabled on your AWS Account: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

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
   ```bash
   env OTEL_PYTHON_DISTRO=aws_distro \
       OTEL_PYTHON_CONFIGURATOR=aws_configurator \
       OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
       OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
       OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-openinference-app" \
       AGENT_OBSERVABILITY_ENABLED="true" \
       opentelemetry-instrument python server.py
   ```

The server will start on `http://localhost:8000`

## API Endpoints

- `GET /` - Root endpoint with API information
- `GET /health` - Health check
- `POST /chat` - Single message chat endpoint
- `POST /batch` - Batch message processing
- `GET /sample` - Run predefined sample prompts
- `GET /docs` - Interactive API documentation

## Testing the API

**Single message:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'
```

**Batch messages:**
```bash
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"messages": ["Tell me a joke", "What is 2+2?", "How do I make coffee?"]}'
```

**Run sample prompts:**
```bash
curl http://localhost:8000/sample
```

## Traffic Generation

Use the included `generate_traffic.sh` script to generate consistent traffic:
```bash
# Default settings (5s delay between requests)
./generate_traffic.sh

# Custom settings
DELAY_SECONDS=3 NUM_REQUESTS=100 ./generate_traffic.sh
```

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:
1. Open the AWS CloudWatch console
2. Navigate to the "Logs groups" section in the left sidebar.
3. Select the `aws/spans` log group to view your trace data.
    
![Screenshot 2025-04-18 at 4 36 13 PM](https://github.com/user-attachments/assets/98e98faf-c8bf-415c-9e0c-87baa86216f1)