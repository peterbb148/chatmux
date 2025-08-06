import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from fastapi import WebSocket

from app.models.message import Message, StreamingResponse
from app.services.llm_providers import (
    AnthropicProvider,
    GoogleProvider,
    MistralProvider,
    OpenAIProvider,
)

# Load environment variables from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../../.env"))

logger = logging.getLogger(__name__)


class LLMCoordinator:
    def __init__(self):
        # Parse models from environment variable
        models_str = os.getenv(
            "MODELS",
            "openai:gpt-4o,anthropic:claude-3-5-sonnet,google:gemini-1.5-pro,mistral:mistral-large-latest",
        )
        models_list = [m.strip() for m in models_str.split(",")]

        # Initialize providers and model info based on the list
        self.providers = {}
        self.model_info = {}

        provider_map = {
            "openai": (OpenAIProvider, "OpenAI"),
            "anthropic": (AnthropicProvider, "Anthropic"),
            "google": (GoogleProvider, "Google"),
            "mistral": (MistralProvider, "Mistral"),
        }

        for idx, model_spec in enumerate(models_list[:4], 1):  # Limit to 4 models
            if ":" in model_spec:
                provider_key, model_name = model_spec.split(":", 1)
                provider_key = provider_key.lower()

                if provider_key in provider_map:
                    provider_class, provider_name = provider_map[provider_key]
                    self.providers[idx] = provider_class()
                    self.model_info[idx] = {"name": model_name, "provider": provider_name}
                    logger.info(f"Loaded model {idx}: {model_name} ({provider_name})")
                else:
                    logger.warning(f"Unknown provider: {provider_key}")
            else:
                logger.warning(f"Invalid model specification: {model_spec}")

        # Ensure we have at least some models
        if not self.providers:
            logger.error("No models loaded, using defaults")
            self.providers = {
                1: OpenAIProvider(),
                2: AnthropicProvider(),
                3: GoogleProvider(),
                4: MistralProvider(),
            }
            self.model_info = {
                1: {"name": "gpt-4o", "provider": "OpenAI"},
                2: {"name": "claude-3-5-sonnet", "provider": "Anthropic"},
                3: {"name": "gemini-1.5-pro", "provider": "Google"},
                4: {"name": "mistral-large-latest", "provider": "Mistral"},
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

        # Start all tasks concurrently but don't wait for completion
        # Each model will stream independently
        if tasks:
            logger.info(
                f"Started {len(tasks)} concurrent streaming tasks for models: {target_models}"
            )
            # Fire and forget - let each model stream independently
            for task in tasks:
                task.add_done_callback(lambda t: self._log_task_completion(t))

    async def _stream_from_model(self, model_id: int, message: Message, websocket: WebSocket):
        try:
            provider = self.providers[model_id]
            model_info = self.model_info[model_id]

            # Check if websocket is still connected before sending
            if websocket.client_state.value != 1:  # 1 = CONNECTED
                logger.warning(f"WebSocket disconnected before streaming model {model_id}")
                return

            # Send initial response to indicate streaming started
            try:
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
            except Exception:
                logger.warning(f"Failed to send stream_start for model {model_id}")
                return

            # Stream responses from the provider
            logger.info(f"Starting to stream from {model_info['name']} (model_id: {model_id})")
            chunk_count = 0
            async for chunk in provider.stream_completion(message.content):
                chunk_count += 1
                logger.debug(
                    f"Received chunk {chunk_count} from {model_info['name']}: {chunk[:50]}..."
                )
                response = StreamingResponse(
                    model_id=model_id,
                    model_name=model_info["name"],
                    provider=model_info["provider"],
                    content=chunk,
                    is_complete=False,
                )

                # Check connection before each send
                if websocket.client_state.value != 1:
                    logger.warning(f"WebSocket disconnected during streaming for model {model_id}")
                    break

                try:
                    await websocket.send_text(
                        json.dumps(
                            {"type": "stream_chunk", "data": response.model_dump(mode="json")}
                        )
                    )
                except Exception:
                    logger.warning(f"Failed to send chunk for model {model_id}")
                    break

            logger.info(f"Finished streaming from {model_info['name']}, sent {chunk_count} chunks")

            # Send completion signal
            if websocket.client_state.value == 1:
                try:
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
                except Exception:
                    logger.warning(f"Failed to send stream_end for model {model_id}")

        except Exception as e:
            logger.error(f"Error streaming from model {model_id}: {e}")
            # Only try to send error if websocket is still connected
            if websocket.client_state.value == 1:
                try:
                    await websocket.send_text(
                        json.dumps({"type": "error", "model_id": model_id, "error": str(e)})
                    )
                except Exception:
                    pass

    def _log_task_completion(self, task):
        """Log when a streaming task completes"""
        if task.exception():
            logger.error(f"Streaming task failed: {task.exception()}")
        else:
            logger.info("Streaming task completed successfully")
