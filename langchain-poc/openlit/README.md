# OpenLit LangChain Sample Application

This sample application demonstrates how to use LangChain with Ollama (a free, local LLM) and OpenLit for observability. It includes both a CLI application and a FastAPI server with traffic generation capabilities.

## Features

- **Local LLM**: Uses Ollama for completely free, offline language model inference
- **OpenTelemetry Integration**: Sends traces to both console and OTLP endpoints
- **OpenLit Instrumentation**: Automatic tracing of LangChain operations
- **FastAPI Server**: RESTful API with multiple endpoints
- **Traffic Generation**: Automated script for continuous load testing

## Prerequisites

- Python 3.8+
- Ollama (for local LLM inference)
- curl and jq (for traffic generation script)

## Setup Instructions

### 1. Install Ollama

Ollama is a free tool that lets you run large language models locally on your machine.

#### Linux/macOS:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Windows:
Download the installer from [https://ollama.ai](https://ollama.ai)

### 2. Pull a Language Model

After installing Ollama, pull the llama3.2 model (or any other supported model):

```bash
# Pull the default model used by this app
ollama pull llama3.2

# Alternative models you can try:
# ollama pull mistral
# ollama pull phi
# ollama pull llama2
```

### 3. Install Python Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Verify Ollama is Running

Ollama runs as a service. You can verify it's running:

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not running, start it manually:
ollama serve
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

To use a different OTLP endpoint, modify the endpoint URL in `app.py` or `server.py`:

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

### Ollama Connection Issues

If you get connection errors:

1. Ensure Ollama is installed and running:
   ```bash
   ollama --version
   curl http://localhost:11434/api/tags
   ```

2. If Ollama is running on a different port or host, update the base_url in the code:
   ```python
   llm = ChatOllama(
       model="llama3.2",
       temperature=0.7,
       base_url="http://your-host:your-port"
   )
   ```

### Model Not Found

If you get a model not found error:

1. List available models:
   ```bash
   ollama list
   ```

2. Pull the required model:
   ```bash
   ollama pull llama3.2
   ```

3. Or update the code to use an available model:
   ```python
   llm = ChatOllama(
       model="your-available-model",
       temperature=0.7,
       base_url="http://localhost:11434"
   )
   ```

### Performance Issues

For better performance:

1. Use smaller models (e.g., `phi` or `mistral`)
2. Reduce the temperature parameter for faster, more deterministic responses
3. Consider using GPU acceleration if available

## Environment Variables

No API keys are required! Ollama runs completely locally without any authentication.

If you need to set custom configurations, you can create a `.env` file:

```bash
# Optional: Custom Ollama endpoint
OLLAMA_BASE_URL=http://localhost:11434

# Optional: Custom OTLP endpoint
OTLP_ENDPOINT=http://localhost:4318/v1/traces
```

## Viewing Spans in CloudWatch

If using AWS X-Ray, after the application is finished running, you can view the generated spans in CloudWatch by following these steps:
1. Open the AWS CloudWatch console
2. Navigate to the "Logs groups" section in the left sidebar
3. Select the `aws/spans` log group to view your trace data

## License

This is a sample application for demonstration purposes.