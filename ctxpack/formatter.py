from pathlib import Path
from typing import Dict, List
from ctxpack.tokenizer import FileContext

LANGUAGE_MAP: Dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".cs": "csharp",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".dart": "dart",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".xml": "xml",
    ".md": "markdown",
    ".sh": "bash",
    ".zsh": "bash",
    ".dockerfile": "dockerfile",
}


def detect_language(path: Path) -> str:
    if path.name.lower() in ("dockerfile", "containerfile"):
        return "dockerfile"
    return LANGUAGE_MAP.get(path.suffix.lower(), "text")


def build_directory_tree(files: List[FileContext]) -> str:
    tree: dict = {}
    for f in files:
        parts = Path(f.relative_path).parts
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

    def render_tree(node: dict, prefix: str = "") -> List[str]:
        lines = []
        entries = sorted(node.keys())
        for idx, entry in enumerate(entries):
            is_last = idx == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry}")
            sub_prefix = "    " if is_last else "│   "
            lines.extend(render_tree(node[entry], prefix + sub_prefix))
        return lines

    return "\n".join(render_tree(tree))


def format_file_content(content: str) -> List[str]:
    lines = content.splitlines()
    if not lines:
        return []
    width = len(str(len(lines)))
    return [f"{i:{width}d} | {line}" for i, line in enumerate(lines, start=1)]


def format_to_xml(
    files: List[FileContext],
    include_tree: bool = True,
) -> str:
    lines = ["<project_context>"]

    if include_tree and files:
        lines.append("  <directory_structure>")
        for tree_line in build_directory_tree(files).splitlines():
            lines.append(f"    {tree_line}")
        lines.append("  </directory_structure>\n")

    for f in files:
        lang = detect_language(f.path)
        lines.append(f'  <file path="{f.relative_path}" language="{lang}" tokens="{f.token_count}">')
        formatted_lines = format_file_content(f.content)
        for content_line in formatted_lines:
            lines.append(f"    {content_line}")
        lines.append("  </file>\n")

    lines.append("</project_context>")
    return "\n".join(lines)


def format_to_markdown(
    files: List[FileContext],
    include_tree: bool = True,
) -> str:
    lines = ["# Project Context\n"]

    if include_tree and files:
        lines.append("## Directory Structure\n```text")
        lines.append(build_directory_tree(files))
        lines.append("```\n")

    lines.append("## Files\n")
    for f in files:
        lang = detect_language(f.path)
        lines.append(f"### `{f.relative_path}` ({f.token_count:,} tokens)")
        lines.append(f"```{lang}")
        formatted_lines = format_file_content(f.content)
        lines.append("\n".join(formatted_lines))
        lines.append("```\n")

    return "\n".join(lines)