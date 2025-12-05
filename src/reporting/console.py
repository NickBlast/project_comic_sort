"""
Console reporting for dry-run.

Uses rich to display simulation results.
"""

import os
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from src.core.simulator import MigrationAction

console = Console()

def print_simulation_report(actions: List[MigrationAction]):
    """
    Print a summary of the simulation to the console.
    """
    if not actions:
        console.print("[yellow]No files processed.[/yellow]")
        return

    # Statistics
    total = len(actions)
    copy = sum(1 for a in actions if a.status == "COPY")
    skip = sum(1 for a in actions if a.status == "SKIP")
    conflict = sum(1 for a in actions if a.status == "CONFLICT")
    error = sum(1 for a in actions if a.status == "ERROR")
    
    # Summary Panel
    summary = f"""[bold]Total Files:[/bold] {total}
[green]Ready to Copy:[/green] {copy}
[yellow]Skipped:[/yellow] {skip}
[red]Conflicts:[/red] {conflict}
[bold red]Errors:[/bold red] {error}"""
    
    console.print(Panel(summary, title="Dry-Run Summary", expand=False))
    
    # Detailed Table (limit to first 50 to avoid spamming)
    table = Table(title="Proposed Actions (First 50)", show_lines=True)
    table.add_column("Status", style="bold")
    table.add_column("Source")
    table.add_column("Target")
    table.add_column("Reason")
    
    for action in actions[:50]:
        style = "green"
        if action.status == "SKIP": style = "yellow"
        elif action.status == "CONFLICT": style = "red"
        elif action.status == "ERROR": style = "bold red"
        
        # Truncate paths for display
        src_name = action.source_path.split(os.sep)[-1]
        tgt_name = action.target_path.split(os.sep)[-1] if action.target_path else ""
        
        table.add_row(
            f"[{style}]{action.status}[/{style}]",
            src_name,
            tgt_name,
            action.reason or ""
        )
        
    console.print(table)
    
    if total > 50:
        console.print(f"[italic]... and {total - 50} more items. See JSON report for full details.[/italic]")
