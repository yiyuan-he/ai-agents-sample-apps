# Strands Agent Sample Application

This sample application demonstrates the Strands agent framework with tool capabilities and OpenTelemetry instrumentation. It includes both a standalone agent script and a FastAPI server with traffic generation.

## Features

- **AI Agent with Tools**: Uses Strands agents with built-in and custom tools
- **Tool Capabilities**: Calculator, current time, Python REPL, and custom letter counter
- **OpenTelemetry Integration**: Full tracing support with console and OTLP exporters
- **FastAPI Server**: RESTful API with multiple endpoints
- **Traffic Generation**: Automated script for continuous load testing

## Prerequisites

- Python 3.8+
- AWS Bedrock access (for Claude model)
- curl and jq (for traffic generation script)

## Setup Instructions

### 1. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

The Strands agent uses AWS Bedrock for the Claude model. Ensure you have AWS credentials configured:

```bash
# Option 1: AWS CLI
aws configure

# Option 2: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Configure OTLP Endpoint (Optional)

The application sends traces to `http://localhost:4318` by default. To use a different endpoint, modify the `otlp_endpoint` in `agent.py` or `server.py`.

## Running the Application

### Standalone Agent Mode

Run the agent directly with the sample tasks:

```bash
python agent.py
```

This will execute a series of tasks demonstrating all available tools.

### FastAPI Server Mode

The server provides a RESTful API with automatic documentation:

```bash
python server.py
```

The server will start on `http://localhost:8000`

#### Available Endpoints

- `GET /` - API information and available endpoints
- `GET /health` - Health check endpoint
- `GET /tools` - List all available tools
- `POST /chat` - Process a single message
- `POST /batch` - Process multiple messages in batch
- `GET /sample` - Run predefined sample prompts
- `GET /docs` - Interactive API documentation (Swagger UI)

#### Available Tools

1. **calculator** - Perform mathematical calculations
2. **current_time** - Get the current date and time
3. **python_repl** - Execute Python code
4. **letter_counter** - Count occurrences of a specific letter in a word

#### Example API Usage

```bash
# Single message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 25 * 40?"}'

# Batch messages
curl -X POST http://localhost:8000/batch \
  -H "Content-Type: application/json" \
  -d '{"messages": ["What time is it?", "Calculate 100 / 25", "Count letter e in elephant"]}'

# List available tools
curl http://localhost:8000/tools

# Run samples
curl http://localhost:8000/sample
```

### Traffic Generation

Generate continuous traffic to test the application:

```bash
./generate_traffic.sh
```

The script will:
- Send random tool-focused messages
- Display colored output for success/failure
- Show response times and previews
- Track statistics (total, success, failed)
- Support graceful shutdown with Ctrl+C

#### Configuration Options

Edit the script to customize:
- `DELAY_SECONDS=10` - Delay between requests (in seconds) - increase if you see throttling
- `NUM_REQUESTS=0` - Number of requests (0 for infinite)
- `TIMEOUT=60` - Request timeout in seconds (higher for complex agent tasks)

**Important Note on AWS Bedrock Rate Limits**: AWS Bedrock has rate limits on requests and tokens per minute. If you encounter throttling errors, increase the `DELAY_SECONDS` to 20-30 seconds in the script.

## OpenTelemetry Configuration

The application sends traces to:

1. **Console**: Prints traces to stdout for debugging
2. **OTLP**: Sends to `http://localhost:4318` (can be customized)

### Viewing Traces

1. **Console Output**: Traces are printed directly to the terminal
2. **OTLP Collector**: Configure your collector to receive traces at the OTLP endpoint
3. **AWS X-Ray**: Can be configured to send traces to X-Ray

### Running with AWS X-Ray

To send traces directly to AWS X-Ray:

```bash
env OTEL_METRICS_EXPORTER=none \
    OTEL_LOGS_EXPORTER=none \
    OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf \
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://xray.us-east-1.amazonaws.com/v1/traces \
    OTEL_RESOURCE_ATTRIBUTES="service.name=strands-agent-app" \
    opentelemetry-instrument python server.py
```

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
2. You may need to request access through the AWS Console
3. Try a different model if needed by updating the model ID in the code

### Throttling Issues

AWS Bedrock has rate limits. If you see throttling errors:

1. Increase the delay between requests in `generate_traffic.sh`:
   ```bash
   DELAY_SECONDS=20  # or even 30
   ```

2. Use simpler prompts to reduce token usage

3. Check your AWS Bedrock quotas:
   ```bash
   aws service-quotas list-service-quotas --service-code bedrock
   ```

### Performance Considerations

- Agent responses can take time due to tool execution
- The timeout in the traffic script is set to 60 seconds to accommodate complex tasks
- Consider reducing the complexity of prompts for faster responses

## Environment Variables

Configure the following environment variables as needed:

```bash
# AWS Configuration (if not using AWS CLI)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1

# Optional: Custom OTLP endpoint
export OTLP_ENDPOINT=http://your-collector:4318

# Optional: OTLP Authorization header
export OTLP_AUTH_HEADER="Bearer your-token"
```

## License

This is a sample application for demonstration purposes.