import os
from pathlib import Path
from typing import List, Set
import pathspec

DEFAULT_IGNORES = {
    ".git",
    ".venv",
    "venv",
    "env",
    ".env",
    "__pycache__",
    "node_modules",
    "bin",
    "obj",
    "target",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".DS_Store",
    "*.pyc",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    ".pytest_cache",
}


def is_binary_file(file_path: Path) -> bool:
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
            chunk.decode("utf-8")
            return False
    except (UnicodeDecodeError, PermissionError, OSError):
        return True


def load_gitignore_spec(root_path: Path, extra_excludes: List[str] = None) -> pathspec.PathSpec:
    patterns: Set[str] = set(DEFAULT_IGNORES)

    if extra_excludes:
        patterns.update(extra_excludes)

    gitignore_file = root_path / ".gitignore"
    if gitignore_file.is_file():
        try:
            with open(gitignore_file, "r", encoding="utf-8", errors="ignore") as f:
                patterns.update(f.read().splitlines())
        except OSError:
            pass

    return pathspec.PathSpec.from_lines("gitignore", patterns)


def scan_directory(root_path: Path, extra_excludes: List[str] = None) -> List[Path]:
    spec = load_gitignore_spec(root_path, extra_excludes)
    valid_files: List[Path] = []

    for root, dirs, files in os.walk(root_path):
        current_dir = Path(root)
        
        rel_dir = current_dir.relative_to(root_path)
        dirs[:] = [
            d for d in dirs 
            if not spec.match_file(str(rel_dir / d) if str(rel_dir) != "." else d)
            and not spec.match_file(f"{str(rel_dir / d)}/" if str(rel_dir) != "." else f"{d}/")
        ]

        for file_name in files:
            file_path = current_dir / file_name
            rel_file_path = file_path.relative_to(root_path)

            if spec.match_file(str(rel_file_path)):
                continue

            if not is_binary_file(file_path):
                valid_files.append(file_path)

    return sorted(valid_files)