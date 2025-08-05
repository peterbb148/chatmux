"""Demo script to test the main Chatmux application."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatmux.app import main

if __name__ == "__main__":
    print("Starting Chatmux demo...")
    print("Make sure you have OPENAI_API_KEY set in your environment or .env file")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDemo interrupted")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
