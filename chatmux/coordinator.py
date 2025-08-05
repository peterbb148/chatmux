"""Response coordinator for managing multiple model responses."""

import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from .config import config
from .core.models import Message, MessageRole, ModelConfig, ModelProvider, TokenUsage
from .models import ModelClient, RateLimitError
from .models.openai_client import OpenAIClient
from .ui.pane import ModelPane, PaneStatus


@dataclass
class StreamUpdate:
    """Update event for streaming responses."""

    pane_id: str
    content: str
    is_complete: bool = False
    error: str | None = None
    token_usage: TokenUsage | None = None


@dataclass
class ResponseTask:
    """Tracks a response task for a specific model."""

    pane: ModelPane
    client: ModelClient
    task_id: UUID = field(default_factory=uuid4)
    task: asyncio.Task[None] | None = None
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime | None = None
    error: Exception | None = None


class ResponseCoordinator:
    """Coordinates sending prompts to multiple models and aggregating responses."""

    def __init__(
        self,
        on_stream_update: Callable[[StreamUpdate], None] | None = None,
    ):
        """Initialize the response coordinator.

        Args:
            on_stream_update: Callback for streaming updates
        """
        self.on_stream_update = on_stream_update
        self.active_tasks: dict[UUID, ResponseTask] = {}
        self._client_cache: dict[tuple[ModelProvider, str], ModelClient] = {}

    def _get_or_create_client(
        self, provider: ModelProvider, model_name: str
    ) -> ModelClient:
        """Get or create a model client.

        Args:
            provider: The model provider
            model_name: The model name

        Returns:
            Model client instance

        Raises:
            ValueError: If provider is not supported
        """
        cache_key = (provider, model_name)
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]

        # Get configuration for this model
        if provider == ModelProvider.OPENAI:
            pane_num = "1" if model_name == config.openai_model_1 else "2"
        elif provider == ModelProvider.ANTHROPIC:
            pane_num = "1" if model_name == config.anthropic_model_1 else "2"
        else:
            pane_num = ""

        model_config_dict = config.get_model_config(provider.value, pane_num)
        model_config = ModelConfig(**model_config_dict)

        # Create client based on provider
        if provider == ModelProvider.OPENAI:
            client = OpenAIClient(model_config)
        # TODO: Add other providers as they're implemented
        # elif provider == ModelProvider.ANTHROPIC:
        #     client = AnthropicClient(model_config)
        else:
            raise ValueError(f"Provider {provider} not yet implemented")

        self._client_cache[cache_key] = client
        return client

    async def send_to_models(
        self,
        message: str,
        target_panes: list[ModelPane],
        conversation_history: list[Message] | None = None,
    ) -> dict[str, ResponseTask]:
        """Send a message to multiple models concurrently.

        Args:
            message: The user message to send
            target_panes: List of model panes to send to
            conversation_history: Optional conversation history

        Returns:
            Dictionary mapping pane IDs to response tasks
        """
        # Create user message
        user_message = Message(role=MessageRole.USER, content=message)

        # Build full message list
        messages = (conversation_history or []) + [user_message]

        # Create tasks for each pane
        tasks: dict[str, ResponseTask] = {}

        for pane in target_panes:
            # Skip if pane has no model configured
            if not pane.model_name:
                continue

            # Create client
            try:
                client = self._get_or_create_client(pane.provider, pane.model_name)
            except ValueError as e:
                # Send error update
                if self.on_stream_update:
                    self.on_stream_update(
                        StreamUpdate(
                            pane_id=pane.pane_id,
                            content="",
                            is_complete=True,
                            error=str(e),
                        )
                    )
                continue

            # Create response task
            response_task = ResponseTask(pane=pane, client=client)

            # Update pane status
            pane.set_status(PaneStatus.STREAMING)
            pane.clear_content()

            # Create async task
            response_task.task = asyncio.create_task(
                self._handle_model_response(response_task, messages)
            )

            tasks[pane.pane_id] = response_task
            self.active_tasks[response_task.task_id] = response_task

        return tasks

    async def _handle_model_response(
        self, task: ResponseTask, messages: list[Message]
    ) -> None:
        """Handle response from a single model.

        Args:
            task: The response task
            messages: Messages to send
        """
        try:
            # Try streaming first
            full_response = ""
            async for chunk in task.client.stream_response(messages):
                full_response += chunk
                task.pane.append_content(chunk)

                # Send stream update
                if self.on_stream_update:
                    self.on_stream_update(
                        StreamUpdate(
                            pane_id=task.pane.pane_id,
                            content=chunk,
                            is_complete=False,
                        )
                    )

            # Get token usage if available
            # For streaming, we might need to estimate or call a separate method
            token_usage = None
            # TODO: Implement token usage tracking for streaming responses

            # Mark as complete
            task.pane.set_status(PaneStatus.COMPLETE)
            task.end_time = datetime.utcnow()

            # Send completion update
            if self.on_stream_update:
                self.on_stream_update(
                    StreamUpdate(
                        pane_id=task.pane.pane_id,
                        content="",
                        is_complete=True,
                        token_usage=token_usage,
                    )
                )

        except RateLimitError as e:
            await self._handle_rate_limit_error(task, messages, e)
        except Exception as e:
            await self._handle_error(task, e)
        finally:
            # Remove from active tasks
            self.active_tasks.pop(task.task_id, None)

    async def _handle_rate_limit_error(
        self, task: ResponseTask, messages: list[Message], error: RateLimitError
    ) -> None:
        """Handle rate limit errors with exponential backoff.

        Args:
            task: The response task
            messages: Messages to retry
            error: The rate limit error
        """
        task.pane.set_status(PaneStatus.RATE_LIMITED)
        task.error = error

        # Send error update
        if self.on_stream_update:
            self.on_stream_update(
                StreamUpdate(
                    pane_id=task.pane.pane_id,
                    content="",
                    is_complete=True,
                    error=f"Rate limited: {error}",
                )
            )

        # Implement exponential backoff with jitter
        retry_count = getattr(task, "retry_count", 0)
        if retry_count < config.retry_attempts:
            task.retry_count = retry_count + 1  # type: ignore
            backoff = config.retry_delay * (2**retry_count)
            jitter = backoff * 0.1 * (0.5 - asyncio.create_task(asyncio.sleep(0)).done())
            await asyncio.sleep(backoff + jitter)

            # Retry
            task.pane.set_status(PaneStatus.STREAMING)
            await self._handle_model_response(task, messages)
        else:
            task.pane.set_status(PaneStatus.ERROR)

    async def _handle_error(self, task: ResponseTask, error: Exception) -> None:
        """Handle general errors.

        Args:
            task: The response task
            error: The error that occurred
        """
        task.pane.set_status(PaneStatus.ERROR)
        task.error = error
        task.end_time = datetime.utcnow()

        error_message = str(error)
        task.pane.append_content(f"\n\n[Error: {error_message}]")

        # Send error update
        if self.on_stream_update:
            self.on_stream_update(
                StreamUpdate(
                    pane_id=task.pane.pane_id,
                    content="",
                    is_complete=True,
                    error=error_message,
                )
            )

    async def cancel_all(self) -> None:
        """Cancel all active response tasks."""
        tasks = list(self.active_tasks.values())
        for response_task in tasks:
            if response_task.task and not response_task.task.done():
                response_task.task.cancel()
                response_task.pane.set_status(PaneStatus.CANCELLED)

        # Wait for all tasks to complete
        await asyncio.gather(
            *[t.task for t in tasks if t.task], return_exceptions=True
        )

        self.active_tasks.clear()

    def get_active_count(self) -> int:
        """Get count of active response tasks."""
        return len(self.active_tasks)

    def get_token_usage_summary(self) -> dict[str, TokenUsage]:
        """Get token usage summary for completed tasks.

        Returns:
            Dictionary mapping pane IDs to token usage
        """
        # TODO: Implement token usage tracking
        return {}
