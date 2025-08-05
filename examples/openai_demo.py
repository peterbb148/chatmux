"""Demo of the OpenAI client."""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatmux.core.models import Message, MessageRole, ModelConfig, ModelProvider
from chatmux.models import OpenAIClient


async def main():
    """Run OpenAI client demo."""
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it with: export OPENAI_API_KEY='your-api-key'")
        return

    # Create configuration
    config = ModelConfig(
        provider=ModelProvider.OPENAI,
        model_name="gpt-3.5-turbo",
        api_key=api_key,
        temperature=0.7,
        max_tokens=100,
    )

    # Create client
    client = OpenAIClient(config)

    # Create conversation
    messages = [
        Message(role=MessageRole.USER, content="Tell me a short joke about programming"),
    ]

    print("Streaming response from OpenAI...")
    print("-" * 50)

    try:
        # Stream the response
        response = ""
        async for chunk in client.stream_response(messages):
            print(chunk, end="", flush=True)
            response += chunk
        print("\n" + "-" * 50)

        # Add assistant response to conversation
        messages.append(Message(role=MessageRole.ASSISTANT, content=response))

        # Follow-up question
        messages.append(Message(role=MessageRole.USER, content="Can you explain why it's funny?"))

        print("\nSending follow-up question...")
        print("-" * 50)

        # Get complete response with token usage
        response_text, token_usage = await client.send_message(messages)
        print(response_text)
        print("-" * 50)

        if token_usage:
            print("\nToken usage:")
            print(f"  Prompt tokens: {token_usage.prompt_tokens}")
            print(f"  Completion tokens: {token_usage.completion_tokens}")
            print(f"  Total tokens: {token_usage.total_tokens}")
            print(f"  Estimated cost: ${token_usage.estimated_cost:.4f}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
