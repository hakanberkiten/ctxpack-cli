from pathlib import Path
import pytest
from ctxpack.formatter import (
    LANGUAGE_MAP,
    build_directory_tree,
    detect_language,
    format_to_markdown,
    format_to_xml,
)
from ctxpack.tokenizer import FileContext


def test_detect_language_common_types():
    assert detect_language(Path("main.py")) == "python"
    assert detect_language(Path("app.ts")) == "typescript"
    assert detect_language(Path("app.tsx")) == "tsx"
    assert detect_language(Path("index.js")) == "javascript"
    assert detect_language(Path("lib.rs")) == "rust"
    assert detect_language(Path("main.go")) == "go"
    assert detect_language(Path("style.css")) == "css"
    assert detect_language(Path("config.json")) == "json"
    assert detect_language(Path("config.yaml")) == "yaml"
    assert detect_language(Path("config.yml")) == "yaml"
    assert detect_language(Path("config.toml")) == "toml"
    assert detect_language(Path("script.sh")) == "bash"
    assert detect_language(Path("unknown.xyz")) == "text"


def test_detect_language_dockerfiles():
    assert detect_language(Path("Dockerfile")) == "dockerfile"
    assert detect_language(Path("dockerfile")) == "dockerfile"
    assert detect_language(Path("Containerfile")) == "dockerfile"


def test_build_directory_tree():
    files = [
        FileContext(
            path=Path("ctxpack/cli.py"),
            relative_path="ctxpack/cli.py",
            content="",
            token_count=100,
        ),
        FileContext(
            path=Path("ctxpack/scanner.py"),
            relative_path="ctxpack/scanner.py",
            content="",
            token_count=50,
        ),
        FileContext(
            path=Path("pyproject.toml"),
            relative_path="pyproject.toml",
            content="",
            token_count=30,
        ),
    ]

    tree = build_directory_tree(files)
    assert "ctxpack" in tree
    assert "cli.py" in tree
    assert "scanner.py" in tree
    assert "pyproject.toml" in tree
    assert "├── " in tree or "└── " in tree


def test_format_to_xml_with_tree():
    files = [
        FileContext(
            path=Path("src/main.py"),
            relative_path="src/main.py",
            content="print('hello')",
            token_count=5,
        )
    ]

    xml_output = format_to_xml(files, include_tree=True)
    assert "<project_context>" in xml_output
    assert "<directory_structure>" in xml_output
    assert "src" in xml_output
    assert 'path="src/main.py"' in xml_output
    assert 'language="python"' in xml_output
    assert 'tokens="5"' in xml_output
    assert "print('hello')" in xml_output
    assert "</file>" in xml_output
    assert "</project_context>" in xml_output


def test_format_to_xml_without_tree():
    files = [
        FileContext(
            path=Path("src/main.py"),
            relative_path="src/main.py",
            content="x = 1",
            token_count=3,
        )
    ]

    xml_output = format_to_xml(files, include_tree=False)
    assert "<project_context>" in xml_output
    assert "<directory_structure>" not in xml_output
    assert 'path="src/main.py"' in xml_output


def test_format_to_markdown_with_tree():
    files = [
        FileContext(
            path=Path("src/main.py"),
            relative_path="src/main.py",
            content="print('hi')",
            token_count=4,
        )
    ]

    md_output = format_to_markdown(files, include_tree=True)
    assert "# Project Context" in md_output
    assert "## Directory Structure" in md_output
    assert "```text" in md_output
    assert "## Files" in md_output
    assert "### `src/main.py` (4 tokens)" in md_output
    assert "```python" in md_output
    assert "print('hi')" in md_output


def test_format_to_markdown_without_tree():
    files = [
        FileContext(
            path=Path("src/main.py"),
            relative_path="src/main.py",
            content="print('hi')",
            token_count=4,
        )
    ]

    md_output = format_to_markdown(files, include_tree=False)
    assert "# Project Context" in md_output
    assert "## Directory Structure" not in md_output
    assert "## Files" in md_output
    assert "### `src/main.py` (4 tokens)" in md_output
