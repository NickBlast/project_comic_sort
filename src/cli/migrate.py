"""
CLI entry point for Phase 5 - Live Migration.

This module provides command-line interface for:
- Executing migration (Copy/Move)
- Safety prompts and limits
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.prompt import Confirm

from src.core.config import load_config, AppConfig
from src.core.logger import setup_logging, get_logger
from src.core.simulator import MigrationSimulator
from src.core.executor import MigrationExecutor
from src.reporting.console import print_simulation_report

logger = get_logger(__name__)
console = Console()

def cmd_migrate(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Run live migration.
    """
    source_path = args.source
    move_mode = args.move
    limit = args.limit
    skip_confirm = args.yes
    
    if not source_path:
        # Use first enabled source
        enabled_sources = [s for s in config.paths.source_libraries if s.enabled]
        if not enabled_sources:
            console.print("[bold red]No enabled source libraries found in config.[/bold red]")
            return 1
        source_path = Path(enabled_sources[0].path)
        console.print(f"[yellow]No source specified, using first enabled source: {source_path}[/yellow]")
    
    mode_str = "MOVE" if move_mode else "COPY"
    console.print(f"\n[bold blue]Starting Migration ({mode_str})[/bold blue]")
    console.print(f"Source: [cyan]{source_path}[/cyan]")
    if limit:
        console.print(f"Limit: [yellow]{limit} files[/yellow]")
    
    try:
        # 1. Run Simulation
        console.print("\n[bold]Step 1: Simulating...[/bold]")
        simulator = MigrationSimulator(config)
        actions = simulator.run(source_path)
        
        # Filter actions based on limit and status
        valid_actions = [a for a in actions if a.status in ["COPY", "MOVE"]] # Simulator returns COPY/SKIP/CONFLICT
        # Note: Simulator returns COPY by default. We interpret that as "Ready to Process".
        # The Executor decides whether to actually copy or move based on the flag.
        
        if not valid_actions:
            console.print("[yellow]No files to process.[/yellow]")
            print_simulation_report(actions)
            return 0
            
        if limit:
            valid_actions = valid_actions[:limit]
            console.print(f"[yellow]Limiting execution to first {limit} files.[/yellow]")
            
        # Display Summary
        print_simulation_report(actions) # Show full report first
        
        console.print(f"\n[bold]Ready to {mode_str} {len(valid_actions)} files.[/bold]")
        
        # 2. Confirmation
        if not skip_confirm:
            if not Confirm.ask(f"Are you sure you want to proceed with {mode_str}?"):
                console.print("[red]Migration cancelled by user.[/red]")
                return 0
        
        # 3. Execution
        console.print(f"\n[bold]Step 2: Executing {mode_str}...[/bold]")
        executor = MigrationExecutor()
        results = executor.execute(valid_actions, move_mode=move_mode)
        
        # 4. Final Report
        success_count = sum(1 for r in results if r['success'])
        fail_count = sum(1 for r in results if not r['success'])
        
        console.print(f"\n[bold green]Migration Complete![/bold green]")
        console.print(f"Successful: {success_count}")
        if fail_count > 0:
            console.print(f"[bold red]Failed: {fail_count}[/bold red]")
            
        console.print(f"Undo log saved to: [cyan]{executor.undo_log_path}[/cyan]")
        
        return 0 if fail_count == 0 else 1
        
    except Exception as e:
        console.print(f"[bold red]Error during migration: {e}[/bold red]")
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for migrate CLI."""
    parser = argparse.ArgumentParser(
        prog="comic-migrate",
        description="Comic migration executor (Phase 5)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--paths-config", type=Path, help="Path to paths configuration file")
    
    parser.add_argument("--source", type=Path, help="Source library path to scan")
    parser.add_argument("--move", action="store_true", help="Move files instead of copying")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        config = load_config(args.config, args.paths_config)
        setup_logging(config.logging)
        
        return cmd_migrate(args, config)
            
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
