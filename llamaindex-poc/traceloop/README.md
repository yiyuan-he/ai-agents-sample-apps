# LlamaIndex Chat Server with Traceloop

A FastAPI server that provides a chat API using LlamaIndex and Ollama, instrumented with Traceloop for observability.

## Prerequisites

1. Install Ollama: https://ollama.com/download
2. Pull a model: `ollama pull llama3.2`
3. Start Ollama: `ollama serve`

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python server.py
```

The server will start on http://localhost:8000

## Usage

Send a chat request with curl:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, how are you?"}'
```

Check health:
```bash
curl http://localhost:8000/health
```

## API Endpoints

- `GET /` - Welcome message
- `POST /chat` - Send a chat prompt
- `GET /health` - Health check

## Traceloop Integration

The application is automatically instrumented with Traceloop. Traces will be sent to your configured Traceloop backend for monitoring and observability.