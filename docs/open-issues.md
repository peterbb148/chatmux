# Open Issues

## 1. CLI lacks custom config file support
The main entry point accepts `--config` but exits with a placeholder message instead of loading the provided file.

:::task-stub{title="Add custom config file loading to CLI"}
- Update `chatmux/__main__.py` to parse and apply a user-specified config path when `--config` is provided.
- Expand `Config` in `chatmux/config.py` to merge settings from the supplied file with environment variables.
- Add unit tests in `tests/` verifying that CLI flags override `.env` defaults and that missing files raise clear errors.
:::

## 2. Logging configuration is unimplemented
The CLI parses `--log-level` but does not initialize Python’s logging module accordingly.

:::task-stub{title="Initialize logging based on CLI log level"}
- In `chatmux/__main__.py`, configure the `logging` module using `args.log_level` or the config default before running the app.
- Ensure logs respect the chosen level across all modules.
- Add tests confirming that different `--log-level` settings affect emitted log records.
:::

## 3. Only OpenAI model provider is supported
Other providers (Anthropic, Gemini, Mistral, etc.) are stubbed out with a TODO marker in the coordinator.

:::task-stub{title="Implement additional model providers in ResponseCoordinator"}
- Extend `_get_or_create_client` in `chatmux/coordinator.py` to instantiate clients for Anthropic, Gemini, Mistral, and Ollama.
- Create corresponding client classes under `chatmux/models/` or integrate existing ones.
- Write tests verifying response streaming and error handling for each new provider.
:::

## 4. Initial streaming updates use an incorrect pane ID
`send_to_models` references `config.pane_id`, which does not exist, instead of `model_config.pane_id`.

:::task-stub{title="Fix pane ID in initial stream update"}
- Replace `config.pane_id` with `model_config.pane_id` inside `send_to_models` in `chatmux/coordinator.py`.
- Add tests ensuring the correct pane receives initial updates and that no AttributeError occurs.
:::

## 5. Rate-limit backoff jitter is broken and spawns orphan tasks
Jitter is computed via an `asyncio.create_task` trick that always returns the same value and leaves tasks unawaited.

:::task-stub{title="Use proper random jitter for rate-limit backoff"}
- Import `random` and compute jitter with `random.uniform(-0.1, 0.1) * backoff` (or similar) in `_handle_rate_limit_error`.
- Remove the unnecessary `asyncio.create_task`.
- Write tests validating exponential backoff with randomized jitter and no task leaks.
:::

## 6. Token usage for streaming responses is not tracked
The coordinator sets `token_usage = None` with a TODO placeholder.

:::task-stub{title="Track token usage during streaming responses"}
- Enhance `ModelClient.stream_response` implementations to yield token usage metadata.
- Update `_handle_model_response` in `chatmux/coordinator.py` to accumulate token counts during streaming.
- Expose the token usage in `StreamUpdate` and add tests asserting accurate counts.
:::

## 7. Token usage summary is unimplemented
`get_token_usage_summary` currently returns an empty dict with a TODO marker.

:::task-stub{title="Implement token usage summary aggregation"}
- Maintain token usage per pane in `ResponseTask` or a dedicated structure.
- Populate and return aggregated totals in `get_token_usage_summary` in `chatmux/coordinator.py`.
- Add tests verifying that completed tasks contribute correct totals to the summary.
:::

## 8. Retry count is dynamically added instead of declared
`ResponseTask` lacks a `retry_count` field, yet `_handle_rate_limit_error` attaches it dynamically and suppresses type checking.

:::task-stub{title="Add retry_count to ResponseTask dataclass"}
- Introduce `retry_count: int = 0` in the `ResponseTask` dataclass in `chatmux/coordinator.py`.
- Remove the `# type: ignore` and adjust `_handle_rate_limit_error` to update this field directly.
- Provide tests ensuring retry counts increment correctly and reset when tasks succeed.
:::

