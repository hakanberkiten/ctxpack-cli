from pathlib import Path
import pytest
from ctxpack.tokenizer import (
    FileContext,
    get_tokenizer,
    parse_budget,
    process_files,
)


def test_file_context_dataclass():
    path = Path("src/main.py")
    ctx = FileContext(
        path=path,
        relative_path="src/main.py",
        content="print(1)",
        token_count=3,
    )
    assert ctx.path == path
    assert ctx.relative_path == "src/main.py"
    assert ctx.content == "print(1)"
    assert ctx.token_count == 3


def test_get_tokenizer_default():
    tokenizer = get_tokenizer()
    assert tokenizer.name == "cl100k_base"


def test_get_tokenizer_fallback():
    tokenizer = get_tokenizer("non_existent_encoding_123")
    assert tokenizer.name == "cl100k_base"


@pytest.mark.parametrize(
    "budget_str, expected",
    [
        (None, None),
        ("", None),
        ("   ", None),
        ("8000", 8000),
        ("12345", 12345),
        ("32k", 32000),
        ("32K", 32000),
        ("1.5k", 1500),
        ("128k", 128000),
        ("1m", 1000000),
        ("1M", 1000000),
        ("2.5m", 2500000),
    ],
)
def test_parse_budget_valid(budget_str, expected):
    assert parse_budget(budget_str) == expected


@pytest.mark.parametrize(
    "invalid_str",
    [
        "abc",
        "32kb",
        "10mb",
        "k",
        "m",
        "32-k",
        "$$$",
    ],
)
def test_parse_budget_invalid(invalid_str):
    with pytest.raises(ValueError, match="Invalid budget format"):
        parse_budget(invalid_str)


def test_process_files_no_budget(tmp_path: Path):
    f1 = tmp_path / "a.py"
    f1.write_text("def a(): return 1", encoding="utf-8")
    f2 = tmp_path / "b.py"
    f2.write_text("def b(): return 2", encoding="utf-8")

    included, excluded, total_tokens = process_files([f1, f2], tmp_path, budget=None)

    assert len(included) == 2
    assert len(excluded) == 0
    assert total_tokens == included[0].token_count + included[1].token_count
    assert included[0].relative_path == "a.py"
    assert included[1].relative_path == "b.py"


def test_process_files_with_budget(tmp_path: Path):
    f1 = tmp_path / "small.py"
    f1.write_text("x = 1", encoding="utf-8")
    f2 = tmp_path / "large.py"
    f2.write_text("print('large file')\n" * 50, encoding="utf-8")

    # Measure raw tokens first
    all_ctx, _, _ = process_files([f1, f2], tmp_path, budget=None)
    small_tokens = all_ctx[0].token_count

    # Set budget to fit only small.py
    included, excluded, total_tokens = process_files(
        [f1, f2], tmp_path, budget=small_tokens + 5
    )

    assert len(included) == 1
    assert included[0].relative_path == "small.py"
    assert len(excluded) == 1
    assert excluded[0].relative_path == "large.py"
    assert total_tokens == small_tokens


def test_process_files_missing_file(tmp_path: Path):
    existing = tmp_path / "exist.py"
    existing.write_text("print('ok')", encoding="utf-8")
    missing = tmp_path / "missing.py"

    included, excluded, total_tokens = process_files([existing, missing], tmp_path)
    assert len(included) == 1
    assert included[0].relative_path == "exist.py"
