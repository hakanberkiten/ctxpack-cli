from pathlib import Path
from unittest.mock import patch
from ctxpack.writer import copy_to_clipboard, write_to_file


def test_write_to_file_creates_file_and_parents(tmp_path: Path):
    target = tmp_path / "deep" / "nested" / "output.xml"
    content = "<project_context></project_context>"

    saved_path = write_to_file(content, target)
    assert saved_path == target
    assert target.is_file()
    assert target.read_text(encoding="utf-8") == content


def test_copy_to_clipboard_success():
    with patch("pyperclip.copy") as mock_copy:
        success = copy_to_clipboard("test content")
        assert success is True
        mock_copy.assert_called_once_with("test content")


def test_copy_to_clipboard_failure():
    with patch("pyperclip.copy", side_effect=Exception("Clipboard unavailable")):
        success = copy_to_clipboard("test content")
        assert success is False
