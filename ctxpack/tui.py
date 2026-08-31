# ctxpack/tui.py
from pathlib import Path
from typing import List, Optional
import questionary
import questionary.prompts.common as common
from prompt_toolkit.filters import Condition, IsDone
from prompt_toolkit.layout.containers import ConditionalContainer, HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import LayoutDimension
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.shortcuts.prompt import PromptSession
from questionary import Choice, Separator

from ctxpack.tokenizer import FileContext


def fuzzy_score(pattern: str, target: str) -> float:
    pattern = pattern.lower().strip()
    target_lower = target.lower()
    if not pattern:
        return 0.0

    filename = Path(target_lower).name

    # 1. Exact substring in filename (highest weight)
    if pattern in filename:
        return 1000.0 - len(filename) + (500.0 if filename.startswith(pattern) else 0.0)

    # 2. Exact substring in full relative path
    if pattern in target_lower:
        return 500.0 - len(target_lower)

    # 3. Subsequence / fuzzy match in filename
    it = iter(filename)
    if all(c in it for c in pattern):
        return 300.0 - len(filename)

    # 4. Subsequence / fuzzy match in full relative path
    it = iter(target_lower)
    if all(c in it for c in pattern):
        return 100.0 - len(target_lower)

    return -1.0


def _patch_fuzzy_search():
    """Enhance questionary's InquirerControl to display a top search bar with live fuzzy filtering and token metrics."""
    def fuzzy_filtered_choices(self):
        if not self.search_filter:
            self.found_in_search = True
            return self.choices

        query = self.search_filter.strip().lower()
        if not query:
            self.found_in_search = True
            return self.choices

        scored = []
        for c in self.choices:
            if isinstance(c, Separator):
                continue
            target = getattr(c.value, "relative_path", None) or (
                c.title if isinstance(c.title, str) else str(c.title)
            )
            score = fuzzy_score(query, target)
            if score >= 0:
                scored.append((score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        filtered = [c for _, c in scored]

        self.found_in_search = len(filtered) > 0
        if not self.found_in_search:
            return [Separator(f'  (no files matching "{self.search_filter}")')]
        return filtered

    def custom_search_tokens(self):
        total_files = len([c for c in self.choices if not isinstance(c, Separator)])
        matched_files = len([c for c in self.filtered_choices if not isinstance(c, Separator)])
        selected_count = len(self.selected_options)
        total_tokens = sum(
            getattr(c.value, "token_count", 0)
            for c in self.choices
            if not isinstance(c, Separator) and c.value in self.selected_options
        )

        query = self.search_filter or ""

        tokens = [
            ("class:search_bar_label", "  Search: "),
            ("class:search_bar_bracket", "["),
        ]

        if query:
            status_class = "class:search_success" if self.found_in_search else "class:search_none"
            tokens.append((status_class, f" {query}"))
            tokens.append(("class:search_bar_cursor", "█ "))
        else:
            tokens.append(("class:search_bar_placeholder", " Type to fuzzy search... "))

        tokens.append(("class:search_bar_bracket", "]  "))
        tokens.append(
            (
                "class:search_bar_stats",
                f"• Found: {matched_files}/{total_files} • Selected: {selected_count} files ({total_tokens:,} tokens)",
            )
        )
        tokens.append(("", "\n"))

        return tokens

    def custom_create_inquirer_layout(
        ic: common.InquirerControl,
        get_prompt_tokens,
        **kwargs,
    ) -> Layout:
        ps: PromptSession = PromptSession(
            get_prompt_tokens, reserve_space_for_menu=0, **kwargs
        )
        common._fix_unecessary_blank_lines(ps)

        @Condition
        def has_search_bar():
            return ic.get_search_string_tokens() is not None

        validation_prompt: PromptSession = PromptSession(
            bottom_toolbar=lambda: ic.error_message, **kwargs
        )

        return Layout(
            HSplit(
                [
                    ps.layout.container,
                    ConditionalContainer(
                        Window(
                            height=LayoutDimension.exact(2),
                            content=FormattedTextControl(ic.get_search_string_tokens),
                        ),
                        filter=has_search_bar & ~IsDone(),
                    ),
                    ConditionalContainer(Window(ic), filter=~IsDone()),
                    ConditionalContainer(
                        validation_prompt.layout.container,
                        filter=Condition(lambda: ic.error_message is not None),
                    ),
                ]
            )
        )

    common.InquirerControl.filtered_choices = property(fuzzy_filtered_choices)
    common.InquirerControl.get_search_string_tokens = custom_search_tokens
    common.create_inquirer_layout = custom_create_inquirer_layout


# Apply the fuzzy search and search bar patch
_patch_fuzzy_search()


def prompt_file_selection(contexts: List[FileContext]) -> Optional[List[FileContext]]:
    if not contexts:
        return []

    choices = [
        Choice(
            title=f"{ctx.relative_path} ({ctx.token_count:,} tokens)",
            value=ctx,
            checked=False,
        )
        for ctx in contexts
    ]

    instruction_msg = (
        "Space: Toggle | Ctrl+A: All | Ctrl+I: Invert | Type to search | Enter: Done"
    )

    custom_style = questionary.Style(
        [
            ("qmark", "fg:#5f819d bold"),
            ("question", "bold"),
            ("pointer", "fg:#81a2be bold"),
            ("highlighted", "fg:#8abeb7 bold"),
            ("selected", "fg:#b5bd68 bold"),
            ("separator", "fg:#707880 italic"),
            ("instruction", "fg:#707880 italic"),
            ("search_bar_label", "fg:#81a2be bold"),
            ("search_bar_bracket", "fg:#5f819d bold"),
            ("search_bar_placeholder", "fg:#707880 italic"),
            ("search_bar_cursor", "fg:#8abeb7 bold"),
            ("search_success", "fg:#b5bd68 bold"),
            ("search_none", "fg:#cc6666 bold"),
            ("search_bar_stats", "fg:#b294bb"),
        ]
    )

    selected: Optional[List[FileContext]] = questionary.checkbox(
        "Select files to include in context:",
        choices=choices,
        instruction=instruction_msg,
        use_search_filter=True,
        use_jk_keys=False,
        style=custom_style,
    ).ask()

    if selected is None:
        return None

    # Maintain original file order for deterministic context generation
    path_order = {ctx.path: idx for idx, ctx in enumerate(contexts)}
    return sorted(selected, key=lambda c: path_order.get(c.path, 0))