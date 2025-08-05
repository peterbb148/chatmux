"""Clipboard functionality for copying model responses."""

import platform
import subprocess


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard.

    Args:
        text: Text to copy

    Returns:
        True if successful, False otherwise
    """
    if not text:
        return False

    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(
                ["pbcopy"],
                input=text.encode("utf-8"),
                check=True,
            )
        elif system == "Linux":
            # Try xclip first, then xsel
            for cmd in [["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
                try:
                    subprocess.run(
                        cmd,
                        input=text.encode("utf-8"),
                        check=True,
                    )
                    break
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            else:
                return False
        elif system == "Windows":
            subprocess.run(
                ["clip"],
                input=text.encode("utf-16le"),
                check=True,
                shell=True,
            )
        else:
            return False

        return True
    except Exception:
        return False


def get_clipboard_command() -> str | None:
    """Get the clipboard command for the current platform.

    Returns:
        Command name or None if not supported
    """
    system = platform.system()

    if system == "Darwin":
        return "pbcopy"
    elif system == "Linux":
        # Check for available commands
        for cmd in ["xclip", "xsel"]:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, check=False)
                return cmd
            except FileNotFoundError:
                continue
        return None
    elif system == "Windows":
        return "clip"
    else:
        return None
