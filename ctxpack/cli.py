from pathlib import Path
from typing import List
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ctxpack.formatter import format_to_markdown, format_to_xml
from ctxpack.scanner import scan_directory
from ctxpack.tokenizer import parse_budget, process_files
from ctxpack.writer import copy_to_clipboard, write_to_file

console = Console()


@click.command(name="ctxpack", help="Package codebase context for LLMs with token budgeting.")
@click.argument("target_path", default=".", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("-b", "--budget", help="Token budget limit (Example: 32k, 128k, 8000)")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Output file path")
@click.option("-c", "--copy", is_flag=True, help="Copy the generated output to the clipboard")
@click.option("-f", "--format", "fmt", type=click.Choice(["xml", "markdown"], case_sensitive=False), default="xml", help="Output format")
@click.option("-e", "--exclude", multiple=True, help="Extra glob patterns to exclude (e.g., -e '*.test.py')")
@click.option("--no-tree", is_flag=True, help="Do not include the directory tree output")
@click.option("-d", "--dry-run", is_flag=True, help="Show only token analysis table without generating package")
def main(
    target_path: Path,
    budget: str,
    output: Path,
    copy: bool,
    fmt: str,
    exclude: List[str],
    no_tree: bool,
    dry_run: bool,
):
    try:
        parsed_budget = parse_budget(budget) if budget else None
    except ValueError as err:
        console.print(f"[bold red]Error:[/bold red] {err}")
        return

    with console.status("[bold green]Scanning and filtering files...[/bold green]"):
        files = scan_directory(target_path, extra_excludes=list(exclude))

    if not files:
        console.print("[yellow]No suitable source code files found in the scanned directory.[/yellow]")
        return

    with console.status("[bold green]Calculating tokens...[/bold green]"):
        included, excluded, total_tokens = process_files(files, target_path, budget=parsed_budget)

    table = Table(title=f"Context Analysis ({target_path.resolve()})", show_header=True, header_style="bold magenta")
    table.add_column("File Path", style="cyan")
    table.add_column("Token", justify="right", style="green")

    for item in included:
        table.add_row(item.relative_path, f"{item.token_count:,}")

    console.print(table)
    console.print(f"\n[bold]Included Files:[/bold] {len(included)} | [bold green]Total Tokens:[/bold green] [bold]{total_tokens:,}[/bold]")

    if excluded:
        console.print(f"[bold yellow]Number of files excluded due to budget ({budget}):[/bold yellow] {len(excluded)}")

    if dry_run:
        return

    include_tree = not no_tree
    formatted_content = (
        format_to_xml(included, include_tree=include_tree)
        if fmt == "xml"
        else format_to_markdown(included, include_tree=include_tree)
    )

    actions_taken = []
    if output:
        saved_path = write_to_file(formatted_content, output)
        actions_taken.append(f"Saved to file: [bold cyan]{saved_path}[/bold cyan]")

    if copy or (not output and not copy):
        copied = copy_to_clipboard(formatted_content)
        if copied:
            actions_taken.append("[bold green]Context copied to clipboard![/bold green] (You can paste it directly to LLM)")
        else:
            actions_taken.append("[yellow]Failed to copy to clipboard.[/yellow]")

    console.print(Panel("\n".join(actions_taken), title="Result", expand=False))


if __name__ == "__main__":
    main()