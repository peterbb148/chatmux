# Chatmux

A terminal-based multi-LLM chat interface that allows you to send prompts to multiple AI models simultaneously and compare their responses side-by-side in a tmux-inspired grid layout.

## Overview

Chatmux is designed for developers and researchers who want to efficiently compare outputs from different language models without switching between multiple browser tabs or applications. It provides a clean, keyboard-driven terminal interface with real-time streaming responses.

## Key Features

- **Multi-Model Chat**: Send one prompt to multiple AI models simultaneously
- **Grid Layout**: 2x3 terminal grid showing responses from up to 5 models plus input pane
- **Model Targeting**: Use `@model_name` syntax to send followup prompts to specific models
- **Real-time Streaming**: Async streaming responses with independent error handling
- **Local Storage**: Conversation history and prompt library stored locally
- **Keyboard Navigation**: Direct shortcuts (Ctrl+1-5) for model pane focus
- **Configuration**: Simple .env file for API keys and model settings

## Supported Models

- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3)
- Google Gemini
- Mistral AI
- Ollama (local models)

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Chatmux                              │
├─────────────────────────────────────────────────────────────┤
│  Terminal UI Layer (Rich/Textual)                          │
│  ├── Grid Layout Manager (2x3)                             │
│  ├── Model Response Panes                                  │
│  ├── Input Handler                                         │
│  └── Keyboard Shortcuts                                    │
├─────────────────────────────────────────────────────────────┤
│  Core Application Layer                                     │
│  ├── Chat Session Manager                                  │
│  ├── Async Response Coordinator                            │
│  ├── Message Parser (@model targeting)                     │
│  └── Configuration Manager                                 │
├─────────────────────────────────────────────────────────────┤
│  Model Integration Layer                                    │
│  ├── Abstract Model Interface                              │
│  ├── OpenAI Client                                         │
│  ├── Anthropic Client                                      │
│  ├── Gemini Client                                         │
│  ├── Mistral Client                                        │
│  └── Ollama Client                                         │
├─────────────────────────────────────────────────────────────┤
│  Data Layer                                                │
│  ├── Local Configuration (.env)                            │
│  ├── Conversation History (SQLite)                         │
│  └── Prompt Library                                        │
└─────────────────────────────────────────────────────────────┘
```

## Installation

```bash
git clone https://github.com/peterbb148/chatmux
cd chatmux
uv install
cp .env.example .env
# Edit .env with your API keys
chatmux
```

## Usage

```bash
# Start chatmux
chatmux

# In the interface:
# - Type prompts in bottom-right pane
# - Responses appear in model panes
# - Use @claude to target specific model
# - Ctrl+1-5 to focus model panes
# - Ctrl+Q to quit
```

## Configuration

Create a `.env` file with your API keys:

```env
# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL_1=gpt-4
OPENAI_MODEL_2=gpt-3.5-turbo

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL_1=claude-3-5-sonnet-20241022
ANTHROPIC_MODEL_2=claude-3-haiku-20240307

# Google Gemini
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-1.5-pro

# Mistral
MISTRAL_API_KEY=your-mistral-api-key
MISTRAL_MODEL=mistral-large-latest

# Ollama (local)
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

## Development

```bash
# Clone the repository
git clone https://github.com/peterbb148/chatmux
cd chatmux

# Install dependencies
uv venv
uv pip install -e .

# Run tests
uv run pytest

# Run with development mode
uv run python -m chatmux
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

- Inspired by tmux's efficient terminal multiplexing
- Built with Rich for beautiful terminal UIs
- Powered by various AI model providers