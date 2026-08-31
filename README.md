# ctxpack

`ctxpack` is a fast, offline command-line interface (CLI) tool designed to scan, analyze, and package codebases into optimized context prompts for Large Language Models (LLMs). It calculates token counts using `tiktoken`, enforces strict token budgets, generates visual directory trees, provides interactive file selection, and exports structured context directly to the system clipboard or a specified output file.

---

## Key Features

- **Automated Repository Scanning**: Discovers source code files while honoring `.gitignore` rules and built-in ignore patterns (including `.env` protection).
- **Interactive File Selection & Live Search**: Select or deselect discovered files interactively using an in-terminal prompt (`-i`, `--interactive`) with an always-visible top search bar, live fuzzy filtering, and real-time per-file token metrics.
- **Binary File Exclusion**: Automatically detects and excludes binary, compiled, and non-text files.
- **Accurate Token Estimation**: Measures token consumption using OpenAI's `cl100k_base` encoding via `tiktoken`.
- **Token Budget Management**: Supports budget limits (e.g., `8000`, `32k`, `128k`) and prioritizes files within the designated capacity.
- **Built-in Line Numbering**: Automatically formats all output files with aligned 1-based line numbers (`1 | ...`) for precise LLM code references and citations.
- **Multiple Output Formats**: Generates prompt-ready output in either structured XML or standard Markdown.
- **Directory Tree Generation**: Builds a hierarchical ASCII directory tree of included files for structural awareness.
- **Seamless Integration**: Automatically copies output to the clipboard when no destination file is specified.
- **Inspection & Dry-Run Mode**: Inspects token distribution per file without generating or saving output payloads.

---

## Requirements

- Python 3.9 or higher
- Supported Platforms: macOS, Linux, Windows

---

## Installation

### Install from Source

Clone the repository and install the package in editable mode:

```bash
git clone https://github.com/hakanberkiten/ctxpack-cli.git
cd ctxpack-cli
pip install -e .
```

Verify the installation:

```bash
ctxpack --help
```

---

## Command-Line Interface Reference

### Syntax

```bash
ctxpack [TARGET_PATH] [OPTIONS]
```

### Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `TARGET_PATH` | Directory Path | `.` (Current Directory) | Path to the directory to scan and package. |

### Options

| Flag | Option | Value | Description |
| :--- | :--- | :--- | :--- |
| `-i` | `--interactive` | None | Launches an interactive terminal prompt to manually select files. |
| `-b` | `--budget` | `TEXT` | Maximum token budget limit (e.g., `8000`, `32k`, `128k`, `1m`). |
| `-o` | `--output` | `PATH` | Path to the destination file where output will be saved. |
| `-c` | `--copy` | None | Explicitly copies the generated context to the system clipboard. |
| `-f` | `--format` | `xml` \| `markdown` | Context format style (Default: `xml`). |
| `-e` | `--exclude` | `TEXT` | Additional glob pattern(s) to exclude (can be specified multiple times). |
| | `--no-tree` | None | Disables the ASCII directory structure in the output payload. |
| `-d` | `--dry-run` | None | Displays the file token analysis table only; skips payload generation. |
| | `--help` | None | Shows help message and exits. |

---

## Usage Examples

### 1. Basic Codebase Packaging

Scan the current directory, display token metrics, and copy the XML prompt to the clipboard:

```bash
ctxpack
```

### 2. Interactive File Selection

Launch an interactive checklist to cherry-pick files for inclusion:

```bash
ctxpack -i
```

Interactive controls:
- **Type text**: Live search & fuzzy filter files (e.g. type `cli`, `fmt`, or `py` to instantly filter).
- **Arrow Keys (Up / Down)**: Navigate through candidate files.
- **Space**: Toggle file selection state (`[x]` / `[ ]`).
- **Ctrl+A**: Select / Deselect all visible files.
- **Ctrl+I**: Invert current selection.
- **Enter**: Finalize selection and generate the packaged context.
- **Ctrl+C**: Cancel the operation safely.

### 3. Scanning a Specific Subdirectory

Target a specific module or folder rather than the repository root:

```bash
ctxpack ./src/services
```

### 4. Enforcing a Token Budget

Enforce a token threshold suitable for standard LLM context windows (e.g., 32,000 tokens):

```bash
ctxpack -b 32k
```

Files exceeding the budget limit are skipped, and a summary of excluded files is reported in the terminal.

### 5. Combining Interactive Selection with Budget Limits

Interactively select candidate files while enforcing a maximum budget ceiling:

```bash
ctxpack -i -b 64k
```

### 6. Exporting to a File

Write the generated context payload directly to a file:

```bash
ctxpack -o prompt_context.xml
```

Generate a Markdown-formatted context file:

```bash
ctxpack -f markdown -o context.md
```

### 7. Writing to File and Copying to Clipboard Simultaneously

Save output to disk while simultaneously copying it to the clipboard:

```bash
ctxpack -o context.xml -c
```

### 8. Excluding Custom Patterns

Exclude specific files or patterns (e.g., tests, documentation, lockfiles) in addition to `.gitignore`:

```bash
ctxpack -e "*.test.py" -e "*.spec.ts" -e "docs/*"
```

### 9. Omitting Directory Tree

Generate context without the embedded directory structure overview:

```bash
ctxpack --no-tree -o context.xml
```

### 10. Performing a Dry Run

Analyze token usage and view the breakdown table without writing files or modifying clipboard contents:

```bash
ctxpack -d
```

---

## Output Formats

All output payloads automatically include aligned 1-based line numbers (`1 | ...`), enabling LLMs to cite exact line numbers when offering suggestions, explaining logic, or generating patches.

### XML Format (Default)

The XML output encapsulates directory structure and individual files inside semantic XML tags, making it ideal for LLMs such as Claude, GPT-4, and Gemini:

```xml
<project_context>
  <directory_structure>
    ├── ctxpack
    │   ├── cli.py
    │   ├── formatter.py
    │   ├── scanner.py
    │   ├── tokenizer.py
    │   ├── tui.py
    │   └── writer.py
    └── pyproject.toml
  </directory_structure>

  <file path="ctxpack/cli.py" language="python" tokens="863">
    1 | from pathlib import Path
    2 | import click
    3 | from rich.console import Console
    ...
  </file>

  <file path="pyproject.toml" language="toml" tokens="180">
    1 | [build-system]
    2 | requires = ["hatchling"]
    ...
  </file>
</project_context>
```

### Markdown Format

Markdown format organizes files under hierarchical headings and syntax-highlighted code blocks:

````markdown
# Project Context

## Directory Structure
```text
├── ctxpack
│   ├── cli.py
│   ├── formatter.py
│   ├── scanner.py
│   ├── tokenizer.py
│   ├── tui.py
│   └── writer.py
└── pyproject.toml
```

## Files

### `ctxpack/cli.py` (863 tokens)
```python
1 | from pathlib import Path
2 | import click
3 | from rich.console import Console
...
```

### `pyproject.toml` (180 tokens)
```toml
1 | [build-system]
2 | requires = ["hatchling"]
...
```
````

---

## File Filtering and Exclusion Rules

`ctxpack` applies multi-stage filtering during directory traversal:

1. **Default Ignore Patterns**: Automatically skips common build artifacts, package managers, and virtual environments:
   - `.git`, `.venv`, `venv`, `env`, `.env`
   - `__pycache__`, `*.pyc`, `.DS_Store`
   - `node_modules`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.lock`
   - `dist`, `build`, `target`, `bin`, `obj`
   - `.idea`, `.vscode`
2. **Gitignore Rules**: Parses and applies `.gitignore` patterns present in the target directory root.
3. **Custom Exclude Flags**: Evaluates user-specified `-e` / `--exclude` glob patterns.
4. **Binary Detection**: Reads the leading bytes of each file and filters out non-text or binary files.

---

## Architecture Overview

```text
ctxpack/
├── __init__.py       # Package entry point
├── cli.py            # Click command definitions, Rich terminal UI, and workflow orchestration
├── formatter.py      # XML / Markdown rendering and ASCII directory tree builder
├── scanner.py        # Recursive directory traversal, binary filtering, and gitignore evaluation
├── tokenizer.py      # tiktoken encoding, token measurement, and budget allocation logic
├── tui.py            # Interactive terminal file selection prompt with search bar & fuzzy filter
└── writer.py         # File system writer and clipboard integration handler

tests/                # Automated pytest test suite (70 tests)
├── test_cli.py
├── test_formatter.py
├── test_scanner.py
├── test_tokenizer.py
├── test_tui.py
└── test_writer.py
```

---

## Running Tests

Install test dependencies and run the full test suite with `pytest`:

```bash
pip install -e .[test]
pytest -v
```

---

## License

This project is licensed under the MIT License.
