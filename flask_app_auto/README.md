# Bedrock API Server

A FastAPI server that provides an API for interacting with AWS Bedrock models.

# Setup

## Prerequisites

Before you begin, ensure that Transaction Search is enabled on your AWS Account.

https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/Enable-Lambda-TransactionSearch.html

## Environment Setup

1. Create a Python virtual environment:
```
$ python -m venv venv
```

2. Activate the virtual environment:
```
$ source venv/bin/activate
```

3. Install dependencies:
```
$ pip install -r requirements.txt
```

**Note**: The AWS Distro for OpenTelemetry (ADOT) Python SDK is already included in the `requirements.txt` file.

## Running the Application

Launch the application with the ADOT Python SDK using the following command:
```
$ env OTEL_METRICS_EXPORTER=none \
          OTEL_LOGS_EXPORTER=none \
          OTEL_PYTHON_DISTRO=aws_distro \
          OTEL_TRACES_EXPORTER=console \
          OTEL_PYTHON_CONFIGURATOR=aws_configurator \
          OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
          OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
          OTEL_RESOURCE_ATTRIBUTES="service.name=langchain-app" \
          OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="http,sqlalchemy,psycopg2,pymysql,sqlite3,aiopg,asyncpg,mysql_connector,urllib3,requests" \
          PYTHONPATH="./../autoinstrumentation/opentelemetry/instrumentation/auto_instrumentation:$PYTHONPATH:./../autoinstrumentation" \
          python app.py
```

The server will start on http://0.0.0.0:8000

## API Endpoints

### POST /invoke
Invokes a Bedrock model with the provided input.

**Request Body:**
```json
{
  "input": "Your prompt text here",
  "model": "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
}
```

The `model` field is optional and defaults to Claude 3.5 Sonnet.

**Response:**
```json
{
  "statusCode": 200,
  "response": "Model response text"
}
```

### GET /health
Health check endpoint to verify the server is running.

**Response:**
```json
{
  "status": "healthy"
}
```

## Example Usage

Using curl:
```bash
curl -X POST http://localhost:8000/invoke \
  -H "Content-Type: application/json" \
  -d '{"input": "Please explain the concept of cloud computing."}'
```
