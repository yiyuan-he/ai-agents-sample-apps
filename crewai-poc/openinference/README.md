# CrewAI OpenInference Sample Application

This sample demonstrates how to integrate CrewAI with OpenInference instrumentation and AWS OpenTelemetry distribution for observability.

## Prerequisites

Before you begin, ensure that:
1. Transaction Search is enabled on your AWS Account
   - Follow the guide: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html
2. You have AWS credentials configured (IAM role, environment variables, or AWS CLI)
3. You have access to AWS Bedrock Claude models in your configured region

## Environment Setup

### 1. Create Python Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured using one of these methods:
- AWS IAM role (recommended for EC2/ECS)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS CLI configuration (`aws configure`)

### 3. Set Environment Variables (Optional)

Create a `.env` file for optional configuration:
```bash
# Optional: Override default Bedrock model
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0

# Optional: Override AWS region
AWS_DEFAULT_REGION=us-west-2

# Optional: Override server port
PORT=8000
```

## Running the Application

### Local Development with Console Output

For local development with console trace output:
```bash
env OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_EXPORTER_OTLP_LOGS_HEADERS="x-aws-log-group=test/genesis,x-aws-log-stream=default,x-aws-metric-namespace=genesis" \
    OTEL_RESOURCE_ATTRIBUTES="service.name=crewai-openinference-app" \
    AGENT_OBSERVABILITY_ENABLED="true" \
    opentelemetry-instrument python server.py
```

## API Endpoints

The application exposes the following RESTful endpoints:

### 1. Chat Endpoint
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the benefits of using AI agents?"}'
```

### 2. Batch Processing
```bash
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"messages": ["Explain quantum computing", "What is machine learning?"]}'
```

### 3. Sample Query
```bash
curl http://localhost:8000/sample
```

### 4. Health Check
```bash
curl http://localhost:8000/health
```

## Viewing Traces

### Local Development
When running with `STRANDS_OTEL_ENABLE_CONSOLE_EXPORT="true"`, traces will be printed to the console.

### AWS CloudWatch
After running the application with AWS deployment configuration:
1. Open the AWS CloudWatch console
2. Navigate to "Logs groups" in the left sidebar
3. Select the `aws/spans` log group to view your trace data
4. Use Transaction Search to analyze traces

## Architecture

This application demonstrates:
- **CrewAI Multi-Agent System**: Uses a research agent and writer agent working together
- **OpenInference Instrumentation**: Automatic tracing of CrewAI operations
- **AWS Bedrock Integration**: Uses Claude 3 Haiku model for LLM operations
- **FastAPI REST API**: Modern async web framework for API endpoints
- **AWS OpenTelemetry**: Enterprise-grade observability with AWS integration

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   - Ensure AWS credentials are properly configured
   - Check IAM permissions for Bedrock access

2. **Model Access Error**
   - Verify you have access to the Bedrock model in your region
   - Check the model ID is correct

3. **No Traces in CloudWatch**
   - Ensure Transaction Search is enabled
   - Verify the X-Ray endpoint URL matches your region
   - Check IAM permissions for X-Ray trace submission

### Debug Mode

To enable debug logging, add:
```bash
OTEL_LOG_LEVEL=debug
```

## License

This sample application is provided as-is for demonstration purposes.
