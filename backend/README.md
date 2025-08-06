# Chatmux Backend

FastAPI backend with WebSocket support for the Chatmux multi-LLM chat interface.

## Setup

1. Create a virtual environment:
```bash
uv venv
```

2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

## Running the Backend

Run the FastAPI server:
```bash
uv run python run.py
```

The API will be available at:
- HTTP: http://localhost:8000
- WebSocket: ws://localhost:8000/ws
- API Docs: http://localhost:8000/docs

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `WebSocket /ws` - WebSocket connection for real-time chat

## WebSocket Message Format

### Client to Server:
```json
{
  "content": "Your message here",
  "targets": [1, 2],  // Optional: array of model IDs, empty for all
  "user_id": "user123"  // Optional: user identifier
}
```

### Server to Client:

**Stream Start:**
```json
{
  "type": "stream_start",
  "model_id": 1,
  "model_name": "GPT-4",
  "provider": "OpenAI",
  "timestamp": "2024-01-15T..."
}
```

**Stream Chunk:**
```json
{
  "type": "stream_chunk",
  "data": {
    "model_id": 1,
    "model_name": "GPT-4",
    "provider": "OpenAI",
    "content": "chunk of text",
    "is_complete": false,
    "timestamp": "2024-01-15T..."
  }
}
```

**Stream End:**
```json
{
  "type": "stream_end",
  "model_id": 1,
  "model_name": "GPT-4",
  "provider": "OpenAI",
  "timestamp": "2024-01-15T..."
}
```

**Error:**
```json
{
  "type": "error",
  "model_id": 1,
  "error": "Error message"
}
```

## Development

The current implementation uses mock LLM providers. To integrate real LLM APIs:

1. Update the provider classes in `app/services/llm_providers/`
2. Add API keys to environment variables
3. Implement proper streaming with the actual SDKs
