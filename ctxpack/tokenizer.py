from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import tiktoken


@dataclass
class FileContext:
    path: Path
    relative_path: str
    content: str
    token_count: int


def get_tokenizer(model_name: str = "cl100k_base") -> tiktoken.Encoding:
    try:
        return tiktoken.get_encoding(model_name)
    except Exception:
        return tiktoken.get_encoding("cl100k_base")


def parse_budget(budget_str: Optional[str]) -> Optional[int]:
    if not budget_str:
        return None

    cleaned = budget_str.strip().lower()
    try:
        if cleaned.endswith("k"):
            return int(float(cleaned[:-1]) * 1000)
        elif cleaned.endswith("m"):
            return int(float(cleaned[:-1]) * 1_000_000)
        return int(cleaned)
    except ValueError:
        raise ValueError(f"Invalid budget format: '{budget_str}'. Example: '32k', '128k', '8000'")


def process_files(
    file_paths: List[Path],
    root_path: Path,
    budget: Optional[int] = None,
    encoding_name: str = "cl100k_base",
) -> Tuple[List[FileContext], List[FileContext], int]:
    tokenizer = get_tokenizer(encoding_name)
    all_contexts: List[FileContext] = []

    for file_path in file_paths:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            rel_path = str(file_path.relative_to(root_path))
            tokens = len(tokenizer.encode(content, disallowed_special=()))
            all_contexts.append(
                FileContext(
                    path=file_path,
                    relative_path=rel_path,
                    content=content,
                    token_count=tokens,
                )
            )
        except OSError:
            continue

    if budget is None:
        total_tokens = sum(c.token_count for c in all_contexts)
        return all_contexts, [], total_tokens

    included: List[FileContext] = []
    excluded: List[FileContext] = []
    current_tokens = 0

    for context in all_contexts:
        if current_tokens + context.token_count <= budget:
            included.append(context)
            current_tokens += context.token_count
        else:
            excluded.append(context)

    return included, excluded, current_tokens