from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import questionary.prompts.common as common
from questionary import Choice, Separator
from ctxpack.tokenizer import FileContext
from ctxpack.tui import (
    fuzzy_score,
    prompt_file_selection,
)


def test_fuzzy_score_empty_pattern():
    assert fuzzy_score("", "ctxpack/cli.py") == 0.0
    assert fuzzy_score("   ", "ctxpack/cli.py") == 0.0


def test_fuzzy_score_exact_filename_match():
    score = fuzzy_score("cli.py", "ctxpack/cli.py")
    assert score > 1000.0


def test_fuzzy_score_filename_prefix():
    score_prefix = fuzzy_score("cli", "ctxpack/cli.py")
    score_no_prefix = fuzzy_score("li", "ctxpack/cli.py")
    assert score_prefix > score_no_prefix


def test_fuzzy_score_substring_in_path():
    score = fuzzy_score("ctxpack", "ctxpack/cli.py")
    assert score > 0.0


def test_fuzzy_score_subsequence_fuzzy_match():
    # 'tk' matches 'tokenizer.py' and 'ccli' matches 'ctxpack/cli.py'
    score_tk = fuzzy_score("tk", "ctxpack/tokenizer.py")
    score_ccli = fuzzy_score("ccli", "ctxpack/cli.py")
    assert score_tk > 0.0
    assert score_ccli > 0.0


def test_fuzzy_score_no_match():
    assert fuzzy_score("xyz123", "ctxpack/cli.py") == -1.0


def test_prompt_file_selection_empty():
    assert prompt_file_selection([]) == []


def test_prompt_file_selection_cancelled():
    ctxs = [
        FileContext(
            path=Path("main.py"),
            relative_path="main.py",
            content="x=1",
            token_count=3,
        )
    ]
    with patch("questionary.checkbox") as mock_checkbox:
        mock_question = MagicMock()
        mock_question.ask.return_value = None
        mock_checkbox.return_value = mock_question

        result = prompt_file_selection(ctxs)
        assert result is None


def test_prompt_file_selection_preserves_file_order():
    ctx1 = FileContext(
        path=Path("a.py"), relative_path="a.py", content="1", token_count=1
    )
    ctx2 = FileContext(
        path=Path("b.py"), relative_path="b.py", content="2", token_count=2
    )
    ctx3 = FileContext(
        path=Path("c.py"), relative_path="c.py", content="3", token_count=3
    )

    # User selected in reverse order: c.py, a.py
    with patch("questionary.checkbox") as mock_checkbox:
        mock_question = MagicMock()
        mock_question.ask.return_value = [ctx3, ctx1]
        mock_checkbox.return_value = mock_question

        result = prompt_file_selection([ctx1, ctx2, ctx3])
        assert result == [ctx1, ctx3]


def test_inquirer_control_search_bar_tokens():
    ctx1 = FileContext(
        path=Path("ctxpack/cli.py"),
        relative_path="ctxpack/cli.py",
        content="",
        token_count=800,
    )
    ctx2 = FileContext(
        path=Path("ctxpack/formatter.py"),
        relative_path="ctxpack/formatter.py",
        content="",
        token_count=500,
    )

    choices = [
        Choice(title=f"{ctx1.relative_path} (800 tokens)", value=ctx1),
        Choice(title=f"{ctx2.relative_path} (500 tokens)", value=ctx2),
    ]

    ic = common.InquirerControl(choices)

    # Initial state (no search string)
    initial_tokens = ic.get_search_string_tokens()
    raw_initial = "".join(t[1] for t in initial_tokens)
    assert "Search:" in raw_initial
    assert "Type to fuzzy search" in raw_initial
    assert "Found: 2/2" in raw_initial
    assert "Selected: 0 files (0 tokens)" in raw_initial

    # Add search character 'c' -> 'l' -> 'i'
    ic.add_search_character("c")
    ic.add_search_character("l")
    ic.add_search_character("i")

    query_tokens = ic.get_search_string_tokens()
    raw_query = "".join(t[1] for t in query_tokens)
    assert "cli" in raw_query
    assert "Found: 1/2" in raw_query


def test_inquirer_control_filtered_choices_ranking():
    ctx_cli = FileContext(
        path=Path("ctxpack/cli.py"),
        relative_path="ctxpack/cli.py",
        content="",
        token_count=800,
    )
    ctx_tok = FileContext(
        path=Path("ctxpack/tokenizer.py"),
        relative_path="ctxpack/tokenizer.py",
        content="",
        token_count=500,
    )

    choices = [
        Choice(title=f"{ctx_cli.relative_path} (800 tokens)", value=ctx_cli),
        Choice(title=f"{ctx_tok.relative_path} (500 tokens)", value=ctx_tok),
    ]

    ic = common.InquirerControl(choices)

    # Search for 'tk' -> tokenizer.py should rank highest
    ic.add_search_character("t")
    ic.add_search_character("k")

    filtered = ic.filtered_choices
    assert len(filtered) > 0
    assert filtered[0].value == ctx_tok

    # Clear and search for non-matching query
    ic.search_filter = "nonexistent999"
    no_match_filtered = ic.filtered_choices
    assert len(no_match_filtered) == 1
    assert isinstance(no_match_filtered[0], Separator)
    assert "no files matching" in str(no_match_filtered[0].title)
