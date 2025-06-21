# Traceloop LangChain Sample Application

## Prerequisites

- AWS credentials configured
- Transaction Search enabled on your AWS Account: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html
- `TRACELOOP_API_KEY` environment variable (get from Traceloop dashboard)

## Setup

1. **Set up virtual environment:**
   ```bash
   uv venv
   ```

2. **Install dependencies:**
   ```bash
   uv pip install -r requirements.txt
   ```

3. **Set Traceloop API key:**
   ```bash
   export TRACELOOP_API_KEY=<your_api_key>
   ```

4. **Run the application:**
   ```bash
   env OTEL_PYTHON_DISTRO=aws_distro \
       OTEL_PYTHON_CONFIGURATOR=aws_configurator \
       OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
       OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
       OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-traceloop-app" \
       AGENT_OBSERVABILITY_ENABLED="true" \
       opentelemetry-instrument python server.py
   ```

The server will start on `http://localhost:8000`

## Testing the API

Once the server is running, you can test it with curl:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

Other available endpoints:
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Viewing Spans in CloudWatch

After the application is finished running, you can view the generated spans in CloudWatch by following these steps:
1. Open the AWS CloudWatch console
2. Navigate to the "Logs groups" section in the left sidebar.
3. Select the `aws/spans` log group to view your trace data.

![Screenshot 2025-04-18 at 4 36 13 PM](https://github.com/user-attachments/assets/c78a484e-1d10-42c9-8fde-bd34513fe2e3)