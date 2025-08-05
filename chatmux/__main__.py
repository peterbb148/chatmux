"""CLI entry point for Chatmux."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from . import __version__
from .app import main as app_main
from .textual_app import main as textual_main
from .config import config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="chatmux",
        description="Terminal-based multi-LLM chat interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chatmux                    # Start interactive chat
  chatmux --version          # Show version
  chatmux --config ~/.config/chatmux/config.toml  # Use custom config
  chatmux --show-config      # Display current configuration
        """.strip(),
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="show program's version number and exit",
    )

    parser.add_argument(
        "--config",
        type=Path,
        metavar="PATH",
        help="path to configuration file",
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="display current configuration and exit",
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default=config.log_level.lower(),
        help="set logging level (default: %(default)s)",
    )

    parser.add_argument(
        "--textual",
        action="store_true",
        help="use Textual-based UI (recommended for better terminal compatibility)",
    )

    parser.add_argument(
        "--legacy",
        action="store_true",
        help="use legacy Rich-based UI (deprecated, has terminal issues)",
    )

    return parser.parse_args()


def show_config() -> None:
    """Display current configuration."""
    print("Chatmux Configuration")
    print("=" * 50)
    print(f"Version: {__version__}")
    print(f"Log level: {config.log_level}")
    print(f"Grid layout: {config.grid_rows}x{config.grid_cols}")
    print(f"Default temperature: {config.default_temperature}")
    print(f"Default max tokens: {config.default_max_tokens}")
    print()

    print("Model Configuration:")
    print("-" * 30)

    # OpenAI
    if config.openai_api_key:
        print("OpenAI:")
        print(f"  API Key: {'*' * 10}...{config.openai_api_key[-4:]}")
        print(f"  Model 1: {config.openai_model_1}")
        print(f"  Model 2: {config.openai_model_2}")
    else:
        print("OpenAI: Not configured")

    # Anthropic
    if config.anthropic_api_key:
        print("Anthropic:")
        print(f"  API Key: {'*' * 10}...{config.anthropic_api_key[-4:]}")
        print(f"  Model 1: {config.anthropic_model_1}")
        print(f"  Model 2: {config.anthropic_model_2}")
    else:
        print("Anthropic: Not configured")

    # Other providers
    if config.gemini_api_key:
        print(f"Gemini: {config.gemini_model}")
    if config.mistral_api_key:
        print(f"Mistral: {config.mistral_model}")
    if config.ollama_host:
        print(f"Ollama: {config.ollama_model} @ {config.ollama_host}")


def main() -> None:
    """Main CLI entry point."""
    args = parse_args()

    # Handle show-config
    if args.show_config:
        show_config()
        sys.exit(0)

    # TODO: Handle custom config file
    if args.config:
        print(f"Custom config not yet implemented: {args.config}")
        sys.exit(1)

    # TODO: Set up logging based on log level
    # For now, we'll just use the config's log level

    # Check if at least one model is configured
    has_models = any(
        [
            config.openai_api_key,
            config.anthropic_api_key,
            config.gemini_api_key,
            config.mistral_api_key,
            config.ollama_host,
        ]
    )

    if not has_models:
        print("Error: No model API keys configured!")
        print("\nPlease set at least one of the following environment variables:")
        print("  OPENAI_API_KEY")
        print("  ANTHROPIC_API_KEY")
        print("  GEMINI_API_KEY")
        print("  MISTRAL_API_KEY")
        print("\nOr configure Ollama with OLLAMA_HOST")
        print("\nSee --help for more information.")
        sys.exit(1)

    # Run the application
    try:
        # Determine which UI to use
        # Default to Textual unless --legacy is specified
        use_textual = not args.legacy
        
        # Override with --textual if specified
        if args.textual:
            use_textual = True
            
        # Environment variable can also control this
        if os.environ.get("CHATMUX_USE_LEGACY", "").lower() == "true":
            use_textual = False
            
        if use_textual:
            # Run Textual version (synchronous)
            textual_main()
        else:
            # Run legacy Rich version (async)
            print("Warning: Using legacy UI which has known terminal compatibility issues.")
            print("Consider using the default Textual UI for better experience.\n")
            asyncio.run(app_main())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
