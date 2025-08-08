# Chatmux

[![CI](https://github.com/peterbb148/chatmux/actions/workflows/ci.yml/badge.svg)](https://github.com/peterbb148/chatmux/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/peterbb148/chatmux/branch/main/graph/badge.svg)](https://codecov.io/gh/peterbb148/chatmux)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A web-based multi-LLM chat interface that allows you to send prompts to multiple AI models simultaneously and compare their responses side-by-side in a clean, modern UI.

## Overview

Chatmux is designed for developers and researchers who want to efficiently compare outputs from different language models without switching between multiple browser tabs or applications. It provides a responsive web interface with real-time streaming responses and intuitive keyboard shortcuts.

## Key Features

- **Multi-Model Chat**: Send one prompt to multiple AI models simultaneously
- **Web-Based UI**: Modern, responsive interface accessible from any browser
- **Model Targeting**: Use `@1-4` syntax to send prompts to specific models
- **Real-time Streaming**: WebSocket-based streaming responses with independent error handling
- **Clean Layout**: Two-row design with chat windows above and full-width input below
- **Keyboard Shortcuts**: Press Enter to send to all models, use @n for targeted sending
- **Configuration**: Simple .env file for API keys and model settings

## Supported Models

Currently configured for frontier models:
- OpenAI (GPT-4)
- Anthropic (Claude 3)
- Google (Gemini Pro/Ultra)
- Mistral (Mistral Large)

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Chatmux Web UI                          │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + TypeScript)                              │
│  ├── Layout Components                                      │
│  │   ├── Two-row CSS Grid Layout                          │
│  │   ├── ChatWindow Components (1-4)                      │
│  │   └── InputBox Component (full width)                  │
│  ├── State Management                                       │
│  │   ├── Chat History per Window                          │
│  │   └── Active Connections Status                        │
│  ├── WebSocket Client                                       │
│  │   ├── Real-time Message Streaming                      │
│  │   └── Connection Management                            │
│  └── Input Parser (@n targeting)                           │
├─────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + WebSockets)                            │
│  ├── WebSocket Server                                       │
│  │   ├── Connection Handler                               │
│  │   ├── Message Router                                    │
│  │   └── Stream Aggregator                                │
│  ├── API Endpoints                                          │
│  │   ├── /ws - WebSocket endpoint                         │
│  │   ├── /health - Health check                           │
│  │   └── /config - Model configuration                    │
│  └── Response Coordinator (adapted from CLI)               │
├─────────────────────────────────────────────────────────────┤
│  Model Integration Layer                                    │
│  ├── Abstract Model Interface                              │
│  ├── OpenAI Client (GPT-4)                                │
│  ├── Anthropic Client (Claude 3)                          │
│  ├── Google Client (Gemini)                               │
│  └── Mistral Client (Mistral Large)                       │
├─────────────────────────────────────────────────────────────┤
│  Configuration & Storage                                    │
│  ├── Environment Variables (.env)                          │
│  ├── API Key Management                                    │
│  └── Session Storage (optional)                            │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
git clone https://github.com/peterbb148/chatmux
cd chatmux

# Backend setup
uv install
cp .env.example .env
# Edit .env with your API keys

# Frontend setup
cd web
npm install

# Start the application
npm run dev  # Starts both backend and frontend
```

## Usage

1. Open http://localhost:3000 in your browser
2. Type your prompt in the input box at the bottom
3. Press Enter to send to all models, or use @1-4 to target specific models
4. Watch responses stream in real-time in the chat windows above

Examples:
- "Tell me a joke" - sends to all 4 models
- "@1 Tell me a joke" - sends only to model 1 (OpenAI)
- "@2 @4 Explain quantum computing" - sends to models 2 and 4

## Configuration

Create a `.env` file with your API keys:

```env
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL_1=gpt-4o

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-opus-20240229

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-pro

# Mistral
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_MODEL=mistral-large-latest
```

## Development

```bash
# Clone the repository
git clone https://github.com/peterbb148/chatmux
cd chatmux

# Backend development
uv venv
uv pip install -e .
uv run pytest

# Frontend development
cd web
npm install
npm run dev

# Run backend and frontend separately for development
# Terminal 1: Backend
uv run python -m chatmux.api

# Terminal 2: Frontend
cd web && npm start
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the need to compare AI model responses efficiently
- Built with FastAPI and React for a modern web experience
- Powered by various AI model providers
