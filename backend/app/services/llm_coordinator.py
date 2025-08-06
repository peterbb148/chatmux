import asyncio
import json
import logging
from datetime import datetime

from fastapi import WebSocket

from app.models.message import Message, StreamingResponse
from app.services.llm_providers import (
    AnthropicProvider,
    GoogleProvider,
    MistralProvider,
    OpenAIProvider,
)

logger = logging.getLogger(__name__)


class LLMCoordinator:
    def __init__(self):
        # Initialize LLM providers
        self.providers = {
            1: OpenAIProvider(),  # GPT-4
            2: AnthropicProvider(),  # Claude 3
            3: GoogleProvider(),  # Gemini Pro
            4: MistralProvider(),  # Mistral Large
        }

        self.model_info = {
            1: {"name": "GPT-4", "provider": "OpenAI"},
            2: {"name": "Claude 3", "provider": "Anthropic"},
            3: {"name": "Gemini Pro", "provider": "Google"},
            4: {"name": "Mistral Large", "provider": "Mistral"},
        }

    async def process_message(self, message: Message, websocket: WebSocket):
        # Determine which models to send to
        target_models = message.targets if message.targets else list(self.providers.keys())

        # Create tasks for each target model
        tasks = []
        for model_id in target_models:
            if model_id in self.providers:
                task = asyncio.create_task(self._stream_from_model(model_id, message, websocket))
                tasks.append(task)
            else:
                logger.warning(f"Unknown model ID: {model_id}")

        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _stream_from_model(self, model_id: int, message: Message, websocket: WebSocket):
        try:
            provider = self.providers[model_id]
            model_info = self.model_info[model_id]

            # Send initial response to indicate streaming started
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "stream_start",
                        "model_id": model_id,
                        "model_name": model_info["name"],
                        "provider": model_info["provider"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

            # Stream responses from the provider
            async for chunk in provider.stream_completion(message.content):
                response = StreamingResponse(
                    model_id=model_id,
                    model_name=model_info["name"],
                    provider=model_info["provider"],
                    content=chunk,
                    is_complete=False,
                )

                await websocket.send_text(
                    json.dumps({"type": "stream_chunk", "data": response.dict()})
                )

            # Send completion signal
            await websocket.send_text(
                json.dumps(
                    {
                        "type": "stream_end",
                        "model_id": model_id,
                        "model_name": model_info["name"],
                        "provider": model_info["provider"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            )

        except Exception as e:
            logger.error(f"Error streaming from model {model_id}: {e}")
            await websocket.send_text(
                json.dumps({"type": "error", "model_id": model_id, "error": str(e)})
            )
