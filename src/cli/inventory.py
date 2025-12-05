"""
CLI entry point for Phase 1 - Inventory and Backup operations.

This module provides command-line interface for:
- Scanning source libraries and generating inventories
- Verifying backups against original inventories
- Running safety checks before operations
"""

import sys
import argparse
import json
import time
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from src.core.config import load_config, AppConfig
from src.core.logger import setup_logging, get_logger
from src.operations.safety_checks import run_safety_checks, print_safety_check_results
from src.operations.scanner import scan_library
from src.operations.verifier import verify_backup

logger = get_logger(__name__)
console = Console()

# ==============================================================================
# COMMAND HANDLERS
# ==============================================================================

def cmd_scan(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Scan source libraries and generate inventory.
    """
    source_path = args.source
    output_path = args.output
    
    if not source_path:
        # If no source provided, use the first enabled source from config
        # In a real scenario, we might want to scan all sources
        enabled_sources = [s for s in config.paths.source_libraries if s.enabled]
        if not enabled_sources:
            console.print("[bold red]No enabled source libraries found in config.[/bold red]")
            return 1
        source_path = Path(enabled_sources[0].path)
        console.print(f"[yellow]No source specified, using first enabled source: {source_path}[/yellow]")
    
    console.print(f"\n[bold blue]Starting Inventory Scan[/bold blue]")
    console.print(f"Source: [cyan]{source_path}[/cyan]")
    console.print(f"Output: [cyan]{output_path}[/cyan]")
    
    start_time = time.time()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            task = progress.add_task("Scanning...", total=None)
            
            def progress_callback(path: str):
                progress.update(task, description=f"Scanning: {Path(path).name}")
            
            inventory = scan_library(
                source_path, 
                progress_callback=progress_callback
            )
            
        duration = time.time() - start_time
        
        # Save inventory
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2)
            
        # Print summary
        table = Table(title="Scan Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Files", str(len(inventory)))
        table.add_row("Duration", f"{duration:.2f}s")
        table.add_row("Output File", str(output_path))
        
        console.print(table)
        
        logger.info(f"Scan complete. Found {len(inventory)} files in {duration:.2f}s")
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error during scan: {e}[/bold red]")
        logger.error(f"Scan failed: {e}", exc_info=True)
        return 1

def cmd_verify(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Verify backup against original inventory.
    """
    original_path = args.original
    backup_path = args.backup
    
    console.print(f"\n[bold blue]Starting Backup Verification[/bold blue]")
    console.print(f"Original Inventory: [cyan]{original_path}[/cyan]")
    console.print(f"Backup Location: [cyan]{backup_path}[/cyan]")
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True
        ) as progress:
            progress.add_task("Verifying...", total=None)
            results = verify_backup(original_path, backup_path)
            
        # Print results
        table = Table(title="Verification Results")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta")
        table.add_column("Status", style="bold")
        
        match_count = len(results["matches"])
        missing_count = len(results["missing"])
        extra_count = len(results["extra"])
        
        table.add_row("Matches", str(match_count), "[green]OK[/green]")
        table.add_row("Missing", str(missing_count), "[red]FAIL[/red]" if missing_count > 0 else "[green]OK[/green]")
        table.add_row("Extra", str(extra_count), "[yellow]WARN[/yellow]" if extra_count > 0 else "[green]OK[/green]")
        
        console.print(table)
        
        if missing_count > 0:
            console.print("\n[bold red]Missing Files:[/bold red]")
            for item in results["missing"][:10]:
                console.print(f"  - {item['rel_path']}")
            if missing_count > 10:
                console.print(f"  ... and {missing_count - 10} more")
                
        if extra_count > 0:
            console.print("\n[bold yellow]Extra Files (in backup but not original):[/bold yellow]")
            for item in results["extra"][:10]:
                console.print(f"  - {item['rel_path']}")
            if extra_count > 10:
                console.print(f"  ... and {extra_count - 10} more")
        
        return 1 if missing_count > 0 else 0
        
    except Exception as e:
        console.print(f"[bold red]Error during verification: {e}[/bold red]")
        logger.error(f"Verification failed: {e}", exc_info=True)
        return 1

# ==============================================================================
# CLI SETUP AND MAIN
# ==============================================================================

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for inventory CLI."""
    parser = argparse.ArgumentParser(
        prog="comic-inventory",
        description="Comic library inventory and backup verification tool (Phase 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--paths-config", type=Path, help="Path to paths configuration file")
    parser.add_argument("--safety-checks-only", action="store_true", help="Run safety checks only and exit")
    parser.add_argument("--skip-safety-checks", action="store_true", help="Skip safety checks")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan source libraries and generate inventory")
    scan_parser.add_argument("--source", type=Path, help="Source library path to scan")
    scan_parser.add_argument("--output", type=Path, default=Path("output/inventories/inventory.json"), help="Output path for inventory JSON")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify backup against original inventory")
    verify_parser.add_argument("--original", type=Path, required=True, help="Path to original inventory JSON")
    verify_parser.add_argument("--backup", type=Path, required=True, help="Path to backup location")
    
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        config = load_config(args.config, args.paths_config)
        setup_logging(config.logging)
        
        if config.environment.dry_run:
            console.print("[bold yellow]⚠️  DRY-RUN MODE ENABLED[/bold yellow]")
        
        if not args.skip_safety_checks:
            console.print("Running safety checks...")
            passed, results = run_safety_checks(config)
            print_safety_check_results(results)
            
            if not passed:
                console.print("[bold red]Safety checks failed - cannot proceed[/bold red]")
                return 1
                
            if args.safety_checks_only:
                return 0
        
        if args.command == "scan":
            return cmd_scan(args, config)
        elif args.command == "verify":
            return cmd_verify(args, config)
        else:
            parser.print_help()
            return 0
            
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
