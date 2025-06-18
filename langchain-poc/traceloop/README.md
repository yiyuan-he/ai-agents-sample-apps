# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

## Environment Setup

This application uses AWS Bedrock instead of OpenAI. Ensure you have AWS credentials configured via one of these methods:
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS CLI configuration (`~/.aws/credentials`)
- IAM instance profile (if running on EC2)

Set your `TRACELOOP_API_KEY` in the your shell environment:
```
export TRACELOOP_API_KEY=<your_api_key>
```

Create a python virtual env with all the necessary dependencies:
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the Application

The application now runs as a FastAPI server. Run it with the ADOT Python SDK:
```
env OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
    OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-app" \
    OTEL_AWS_APPLICATION_SIGNALS_ENABLED="false" \
    AGENT_OBSERVABILITY_ENABLED="true" \
    STRANDS_OTEL_ENABLE_CONSOLE_EXPORT="true" \
    OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true" \
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

![Screenshot 2025-04-18 at 4 36 13 PM](https://github.com/user-attachments/assets/c78a484e-1d10-42c9-8fde-bd34513fe2e3)
