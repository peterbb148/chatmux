"""Tests for clipboard functionality."""

import subprocess
from unittest.mock import Mock, patch

from chatmux.ui.clipboard import copy_to_clipboard, get_clipboard_command


class TestClipboard:
    """Test clipboard functionality."""

    def test_copy_empty_text(self):
        """Test copying empty text returns False."""
        assert not copy_to_clipboard("")

    @patch("platform.system")
    @patch("subprocess.run")
    def test_copy_macos(self, mock_run, mock_system):
        """Test copying on macOS."""
        mock_system.return_value = "Darwin"
        mock_run.return_value = Mock(returncode=0)

        assert copy_to_clipboard("Hello world")
        mock_run.assert_called_once_with(
            ["pbcopy"],
            input=b"Hello world",
            check=True,
        )

    @patch("platform.system")
    @patch("subprocess.run")
    def test_copy_linux_xclip(self, mock_run, mock_system):
        """Test copying on Linux with xclip."""
        mock_system.return_value = "Linux"
        mock_run.return_value = Mock(returncode=0)

        assert copy_to_clipboard("Hello world")
        mock_run.assert_called_with(
            ["xclip", "-selection", "clipboard"],
            input=b"Hello world",
            check=True,
        )

    @patch("platform.system")
    @patch("subprocess.run")
    def test_copy_linux_xsel(self, mock_run, mock_system):
        """Test copying on Linux with xsel (fallback)."""
        mock_system.return_value = "Linux"

        # First call to xclip fails
        mock_run.side_effect = [
            subprocess.CalledProcessError(1, ["xclip"]),
            Mock(returncode=0),  # xsel succeeds
        ]

        assert copy_to_clipboard("Hello world")
        assert mock_run.call_count == 2

        # Check xsel was called
        mock_run.assert_called_with(
            ["xsel", "--clipboard", "--input"],
            input=b"Hello world",
            check=True,
        )

    @patch("platform.system")
    @patch("subprocess.run")
    def test_copy_windows(self, mock_run, mock_system):
        """Test copying on Windows."""
        mock_system.return_value = "Windows"
        mock_run.return_value = Mock(returncode=0)

        assert copy_to_clipboard("Hello world")
        mock_run.assert_called_once_with(
            ["clip"],
            input="Hello world".encode("utf-16le"),
            check=True,
            shell=True,
        )

    @patch("platform.system")
    def test_copy_unsupported_platform(self, mock_system):
        """Test copying on unsupported platform."""
        mock_system.return_value = "Unknown"
        assert not copy_to_clipboard("Hello world")

    @patch("platform.system")
    @patch("subprocess.run")
    def test_copy_subprocess_error(self, mock_run, mock_system):
        """Test handling subprocess errors."""
        mock_system.return_value = "Darwin"
        mock_run.side_effect = subprocess.CalledProcessError(1, ["pbcopy"])

        assert not copy_to_clipboard("Hello world")

    @patch("platform.system")
    def test_get_clipboard_command_macos(self, mock_system):
        """Test getting clipboard command on macOS."""
        mock_system.return_value = "Darwin"
        assert get_clipboard_command() == "pbcopy"

    @patch("platform.system")
    def test_get_clipboard_command_windows(self, mock_system):
        """Test getting clipboard command on Windows."""
        mock_system.return_value = "Windows"
        assert get_clipboard_command() == "clip"

    @patch("platform.system")
    @patch("subprocess.run")
    def test_get_clipboard_command_linux(self, mock_run, mock_system):
        """Test getting clipboard command on Linux."""
        mock_system.return_value = "Linux"
        mock_run.return_value = Mock(returncode=0)

        cmd = get_clipboard_command()
        assert cmd in ["xclip", "xsel"]

    @patch("platform.system")
    @patch("subprocess.run")
    def test_get_clipboard_command_linux_none_available(self, mock_run, mock_system):
        """Test getting clipboard command on Linux with no tools available."""
        mock_system.return_value = "Linux"
        mock_run.side_effect = FileNotFoundError

        assert get_clipboard_command() is None

    @patch("platform.system")
    def test_get_clipboard_command_unsupported(self, mock_system):
        """Test getting clipboard command on unsupported platform."""
        mock_system.return_value = "Unknown"
        assert get_clipboard_command() is None
