from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from ctxpack.cli import main
from ctxpack.tokenizer import FileContext


def create_sample_repo(base_dir: Path):
    src = base_dir / "src"
    src.mkdir()
    (src / "app.py").write_text("def app(): return 'OK'", encoding="utf-8")
    (src / "utils.py").write_text("def util(): pass", encoding="utf-8")
    (base_dir / "README.md").write_text("# Test Repo", encoding="utf-8")


def test_cli_default_run(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    with patch("ctxpack.cli.copy_to_clipboard", return_value=True) as mock_copy:
        result = runner.invoke(main, [str(tmp_path)])
        assert result.exit_code == 0
        assert "Context Analysis" in result.output
        assert "app.py" in result.output
        assert "Total Tokens:" in result.output
        assert "Context copied to clipboard." in result.output
        mock_copy.assert_called_once()


def test_cli_output_file(tmp_path: Path):
    create_sample_repo(tmp_path)
    output_file = tmp_path / "context.xml"
    runner = CliRunner()

    with patch("ctxpack.cli.copy_to_clipboard", return_value=True):
        result = runner.invoke(main, [str(tmp_path), "-o", str(output_file)])
        assert result.exit_code == 0
        assert output_file.is_file()
        content = output_file.read_text(encoding="utf-8")
        assert "<project_context>" in content
        assert "app.py" in content


def test_cli_markdown_format(tmp_path: Path):
    create_sample_repo(tmp_path)
    output_file = tmp_path / "context.md"
    runner = CliRunner()

    result = runner.invoke(
        main, [str(tmp_path), "-f", "markdown", "-o", str(output_file)]
    )
    assert result.exit_code == 0
    assert output_file.is_file()
    content = output_file.read_text(encoding="utf-8")
    assert "# Project Context" in content
    assert "```python" in content


def test_cli_dry_run(tmp_path: Path):
    create_sample_repo(tmp_path)
    output_file = tmp_path / "context.xml"
    runner = CliRunner()

    with patch("ctxpack.cli.copy_to_clipboard") as mock_copy:
        result = runner.invoke(
            main, [str(tmp_path), "-d", "-o", str(output_file)]
        )
        assert result.exit_code == 0
        assert "Context Analysis" in result.output
        assert not output_file.exists()
        mock_copy.assert_not_called()


def test_cli_invalid_budget(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    result = runner.invoke(main, [str(tmp_path), "-b", "invalid_budget"])
    assert result.exit_code == 0
    assert "Error:" in result.output
    assert "Invalid budget format" in result.output


def test_cli_budget_enforcement(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    with patch("ctxpack.cli.copy_to_clipboard", return_value=True):
        result = runner.invoke(main, [str(tmp_path), "-b", "5"])
        assert result.exit_code == 0
        assert "Number of files excluded due to budget" in result.output


def test_cli_no_files_found(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    runner = CliRunner()

    result = runner.invoke(main, [str(empty_dir)])
    assert result.exit_code == 0
    assert "No suitable source code files found" in result.output


def test_cli_extra_excludes(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    with patch("ctxpack.cli.copy_to_clipboard", return_value=True):
        result = runner.invoke(main, [str(tmp_path), "-e", "*.md"])
        assert result.exit_code == 0
        assert "app.py" in result.output
        assert "README.md" not in result.output


def test_cli_no_tree(tmp_path: Path):
    create_sample_repo(tmp_path)
    output_file = tmp_path / "no_tree.xml"
    runner = CliRunner()

    result = runner.invoke(
        main, [str(tmp_path), "--no-tree", "-o", str(output_file)]
    )
    assert result.exit_code == 0
    content = output_file.read_text(encoding="utf-8")
    assert "<directory_structure>" not in content
    assert "<file path=" in content


def test_cli_interactive_cancelled(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    with patch("ctxpack.cli.prompt_file_selection", return_value=None):
        result = runner.invoke(main, [str(tmp_path), "-i"])
        assert result.exit_code == 0
        assert "Operation cancelled." in result.output


def test_cli_interactive_empty_selection(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    with patch("ctxpack.cli.prompt_file_selection", return_value=[]):
        result = runner.invoke(main, [str(tmp_path), "-i"])
        assert result.exit_code == 0
        assert "No files selected. Exiting." in result.output


def test_cli_interactive_selection_success(tmp_path: Path):
    create_sample_repo(tmp_path)
    runner = CliRunner()

    app_file = tmp_path / "src" / "app.py"
    selected_ctx = FileContext(
        path=app_file,
        relative_path="src/app.py",
        content="def app(): return 'OK'",
        token_count=10,
    )

    with patch(
        "ctxpack.cli.prompt_file_selection", return_value=[selected_ctx]
    ), patch("ctxpack.cli.copy_to_clipboard", return_value=True):
        result = runner.invoke(main, [str(tmp_path), "-i"])
        assert result.exit_code == 0
        assert "src/app.py" in result.output
        assert "Included Files: 1" in result.output
