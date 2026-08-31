from pathlib import Path
import pytest
from ctxpack.scanner import (
    DEFAULT_IGNORES,
    is_binary_file,
    load_gitignore_spec,
    scan_directory,
)


def test_default_ignores_contains_standard_entries():
    assert ".git" in DEFAULT_IGNORES
    assert ".venv" in DEFAULT_IGNORES
    assert ".env" in DEFAULT_IGNORES
    assert "node_modules" in DEFAULT_IGNORES
    assert "__pycache__" in DEFAULT_IGNORES
    assert "dist" in DEFAULT_IGNORES
    assert "build" in DEFAULT_IGNORES
    assert ".pytest_cache" in DEFAULT_IGNORES


def test_is_binary_file_with_text(tmp_path: Path):
    text_file = tmp_path / "hello.py"
    text_file.write_text("print('Hello World')", encoding="utf-8")
    assert is_binary_file(text_file) is False


def test_is_binary_file_with_null_bytes(tmp_path: Path):
    bin_file = tmp_path / "data.bin"
    bin_file.write_bytes(b"\x00\x01\x02\x03\xff")
    assert is_binary_file(bin_file) is True


def test_is_binary_file_non_existent(tmp_path: Path):
    missing_file = tmp_path / "missing.txt"
    assert is_binary_file(missing_file) is True


def test_is_binary_file_invalid_utf8(tmp_path: Path):
    invalid_file = tmp_path / "invalid.dat"
    invalid_file.write_bytes(b"\x80\x81\x82\x83")
    assert is_binary_file(invalid_file) is True


def test_load_gitignore_spec_without_gitignore(tmp_path: Path):
    spec = load_gitignore_spec(tmp_path)
    assert spec.match_file(".git")
    assert spec.match_file("node_modules")
    assert spec.match_file(".env")
    assert not spec.match_file("src/main.py")


def test_load_gitignore_spec_with_gitignore(tmp_path: Path):
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.log\ntmp/\n", encoding="utf-8")

    spec = load_gitignore_spec(tmp_path)
    assert spec.match_file("app.log")
    assert spec.match_file("tmp/test.txt")
    assert not spec.match_file("app.py")


def test_load_gitignore_spec_with_extra_excludes(tmp_path: Path):
    spec = load_gitignore_spec(tmp_path, extra_excludes=["*.test.js", "docs/"])
    assert spec.match_file("src/index.test.js")
    assert spec.match_file("docs/index.md")
    assert not spec.match_file("src/index.js")


def test_scan_directory_comprehensive(tmp_path: Path):
    # Valid source files
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    main_py = src_dir / "main.py"
    main_py.write_text("print('main')", encoding="utf-8")
    utils_py = src_dir / "utils.py"
    utils_py.write_text("def util(): pass", encoding="utf-8")

    # Root files
    readme = tmp_path / "README.md"
    readme.write_text("# Project", encoding="utf-8")

    # Ignored directories
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config", encoding="utf-8")

    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "package.json").write_text("{}", encoding="utf-8")

    # Ignored files
    env_file = tmp_path / ".env"
    env_file.write_text("SECRET=123", encoding="utf-8")

    # Binary file
    image_file = src_dir / "logo.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    # Gitignore rule
    gitignore = tmp_path / ".gitignore"
    gitignore.write_text("*.tmp\n", encoding="utf-8")
    (src_dir / "temp.tmp").write_text("temporary", encoding="utf-8")

    scanned = scan_directory(tmp_path)
    scanned_rel = [str(f.relative_to(tmp_path)) for f in scanned]

    assert scanned_rel == [".gitignore", "README.md", "src/main.py", "src/utils.py"]


def test_scan_directory_with_extra_excludes(tmp_path: Path):
    (tmp_path / "app.py").write_text("print('app')", encoding="utf-8")
    (tmp_path / "app.test.py").write_text("print('test')", encoding="utf-8")

    scanned = scan_directory(tmp_path, extra_excludes=["*.test.py"])
    scanned_rel = [str(f.relative_to(tmp_path)) for f in scanned]

    assert scanned_rel == ["app.py"]


def test_scan_directory_empty(tmp_path: Path):
    scanned = scan_directory(tmp_path)
    assert scanned == []
