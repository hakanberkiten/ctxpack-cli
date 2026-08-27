from pathlib import Path
from typing import Optional
import pyperclip


def copy_to_clipboard(content: str) -> bool:
    try:
        pyperclip.copy(content)
        return True
    except Exception:
        return False


def write_to_file(content: str, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
    return output_path