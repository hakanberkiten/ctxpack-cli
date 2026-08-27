# ctxpack/tui.py
from typing import List, Optional, Set
import questionary
from questionary import Choice

from ctxpack.tokenizer import FileContext


def prompt_file_selection(contexts: List[FileContext]) -> Optional[List[FileContext]]:
    if not contexts:
        return []

    selected_indices: Set[int] = set()
    SUBMIT_ACTION = "__SUBMIT__"
    TOGGLE_ALL_ACTION = "__TOGGLE_ALL__"

    while True:
        choices = []

        for idx, ctx in enumerate(contexts):
            is_checked = idx in selected_indices
            status_box = "[x]" if is_checked else "[ ]"
            title = f"{status_box} {ctx.relative_path} ({ctx.token_count:,} tokens)"
            choices.append(Choice(title=title, value=idx))

        choices.append(questionary.Separator())
        
        all_selected = len(selected_indices) == len(contexts)
        toggle_label = "[Deselect All]" if all_selected else "[Select All]"
        choices.append(Choice(title=f"  {toggle_label}", value=TOGGLE_ALL_ACTION))
        
        selected_count = len(selected_indices)
        choices.append(
            Choice(
                title=f"[ ] SUBMIT ({selected_count}) Files",
                value=SUBMIT_ACTION,
            )
        )

        instruction_msg = (
            "Enter: Select | Choose SUBMIT to finish | Ctrl+C: Cancel"
        )

        answer = questionary.select(
            "Select files to include in context:",
            choices=choices,
            instruction=instruction_msg,
            use_shortcuts=False,
            style=questionary.Style(
                [
                    ("qmark", "fg:#5f819d bold"),
                    ("question", "bold"),
                    ("pointer", "fg:#81a2be bold"),
                    ("highlighted", "fg:#8abeb7 bold"),
                    ("instruction", "fg:#707880 italic"),
                ]
            ),
        ).ask()

        if answer is None:
            return None

        if answer == SUBMIT_ACTION:
            break
        elif answer == TOGGLE_ALL_ACTION:
            if len(selected_indices) == len(contexts):
                selected_indices.clear()
            else:
                selected_indices = set(range(len(contexts)))
        else:
            idx = int(answer)
            if idx in selected_indices:
                selected_indices.remove(idx)
            else:
                selected_indices.add(idx)

    return [contexts[i] for i in sorted(selected_indices)]