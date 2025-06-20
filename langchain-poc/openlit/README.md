# OpenLit AWS Bedrock Sample Application

This sample application demonstrates how to use AWS Bedrock Converse API with OpenLit for observability. It includes a FastAPI server with traffic generation capabilities.

## Features

- **AWS Bedrock Integration**: Uses AWS Bedrock Converse API with Claude 3 Haiku model
- **OpenTelemetry Integration**: Sends traces to both console and OTLP endpoints
- **OpenLit Instrumentation**: Automatic tracing of Bedrock API operations
- **FastAPI Server**: RESTful API with multiple endpoints
- **Traffic Generation**: Automated script for continuous load testing

## Prerequisites

- Python 3.8+
- AWS Account with Bedrock access
- AWS credentials configured (via AWS CLI, environment variables, or IAM role)
- curl and jq (for traffic generation script)

## Setup Instructions

### 1. Configure AWS Credentials

Ensure you have AWS credentials configured with access to AWS Bedrock. You can configure credentials using:

```bash
# Using AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-west-2
```

### 2. Enable Bedrock Model Access

In the AWS Console:
1. Navigate to the Amazon Bedrock service
2. Go to "Model access" in the left sidebar
3. Request access to `Claude 3 Haiku` model (or modify the code to use another available model)
4. Wait for approval (usually instant for Claude models)

### 3. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Verify AWS Bedrock Access

You can verify your Bedrock access by listing available models:

```bash
# List available foundation models
aws bedrock list-foundation-models --region us-west-2

# Test the specific model we're using
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --region us-west-2 \
  --body '{"messages":[{"role":"user","content":"Hello"}],"max_tokens":10}' \
  --cli-binary-format raw-in-base64-out \
  /tmp/bedrock-test.json
```

## Running the Application

### FastAPI Server

The server provides a RESTful API with automatic documentation:

```bash
python server.py
```

The server will start on `http://localhost:8000`

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
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?"}'

# Batch messages
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"messages": ["Hello", "How are you?", "Tell me a joke"]}'

# Run samples
curl http://localhost:8000/sample
```

### Traffic Generation

Generate continuous traffic to test the application:

```bash
./generate_traffic.sh
```

The script will:
- Send random messages from a predefined list
- Display colored output for success/failure
- Show response times and previews
- Track statistics (total, success, failed)
- Support graceful shutdown with Ctrl+C

#### Configuration Options

Edit the script to customize:
- `DELAY_SECONDS=2` - Delay between requests (in seconds)
- `NUM_REQUESTS=0` - Number of requests (0 for infinite)
- `TIMEOUT=30` - Request timeout in seconds

## OpenTelemetry Configuration

The application sends traces to two destinations:

1. **Console**: Prints traces to stdout for debugging
2. **OTLP**: Sends to `http://localhost:4318/v1/traces`

To use a different OTLP endpoint, modify the endpoint URL in `server.py`:

```python
otlp_exporter = OTLPSpanExporter(endpoint="http://your-collector:4318/v1/traces")
```

### Running with AWS X-Ray

To send traces directly to AWS X-Ray:

```bash
env OTEL_METRICS_EXPORTER=none \
    OTEL_LOGS_EXPORTER=none \
    OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
    OTEL_RESOURCE_ATTRIBUTES="service.name=openlit-langchain-app" \
    OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,botocore,boto3,urllib3,requests" \
    opentelemetry-instrument python server.py
```

## Troubleshooting

### AWS Authentication Issues

If you get authentication errors:

1. Verify your AWS credentials are configured:
   ```bash
   aws sts get-caller-identity
   ```

2. Ensure your credentials have the necessary Bedrock permissions:
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "bedrock:InvokeModel",
                   "bedrock:InvokeModelWithResponseStream"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

### Model Access Issues

If you get model access errors:

1. Verify you have access to the model in the AWS Console
2. Check the correct region (default is `us-west-2`)
3. Try a different model by updating `MODEL_ID` in `server.py`:
   ```python
   # Available models (check your access):
   MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'
   # MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'
   # MODEL_ID = 'amazon.titan-text-express-v1'
   ```

### Performance Optimization

1. Adjust `MAX_TOKENS` and `TEMPERATURE` in `server.py` for your use case
2. Use concurrent requests with the `/batch` endpoint
3. Consider using a larger instance type if running on EC2

## Environment Variables

The application uses AWS credentials from your environment. You can also create a `.env` file for custom configurations:

```bash
# AWS Configuration (if not using AWS CLI or IAM roles)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2

# Optional: Custom OTLP endpoint
OTLP_ENDPOINT=http://localhost:4318/v1/traces

# Optional: Override model settings
BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
BEDROCK_MAX_TOKENS=300
BEDROCK_TEMPERATURE=0.7
```

## Viewing Spans in CloudWatch

If using AWS X-Ray, after the application is finished running, you can view the generated spans in CloudWatch by following these steps:
1. Open the AWS CloudWatch console
2. Navigate to the "Logs groups" section in the left sidebar
3. Select the `aws/spans` log group to view your trace data

## License

This is a sample application for demonstration purposes.