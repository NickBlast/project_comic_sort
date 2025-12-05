"""
CLI entry point for Phase 4 - Dry-Run operations.

This module provides command-line interface for:
- Running migration simulation
- Generating reports
"""

import sys
import argparse
import os
from pathlib import Path
from typing import Optional, List

from rich.console import Console

from src.core.config import load_config, AppConfig
from src.core.logger import setup_logging, get_logger
from src.core.simulator import MigrationSimulator
from src.reporting.console import print_simulation_report
from src.reporting.json_report import generate_json_report

logger = get_logger(__name__)
console = Console()

def cmd_dry_run(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Run migration simulation.
    """
    source_path = args.source
    output_report = args.output_report
    
    if not source_path:
        # Use first enabled source
        enabled_sources = [s for s in config.paths.source_libraries if s.enabled]
        if not enabled_sources:
            console.print("[bold red]No enabled source libraries found in config.[/bold red]")
            return 1
        source_path = Path(enabled_sources[0].path)
        console.print(f"[yellow]No source specified, using first enabled source: {source_path}[/yellow]")
    
    console.print(f"\n[bold blue]Starting Dry-Run Simulation[/bold blue]")
    console.print(f"Source: [cyan]{source_path}[/cyan]")
    
    try:
        simulator = MigrationSimulator(config)
        actions = simulator.run(source_path)
        
        # Console Report
        print_simulation_report(actions)
        
        # JSON Report
        generate_json_report(actions, output_report)
        console.print(f"\nDetailed report saved to: [cyan]{output_report}[/cyan]")
        
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error during simulation: {e}[/bold red]")
        logger.error(f"Simulation failed: {e}", exc_info=True)
        return 1

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for dry-run CLI."""
    parser = argparse.ArgumentParser(
        prog="comic-dry-run",
        description="Comic migration simulator (Phase 4)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--paths-config", type=Path, help="Path to paths configuration file")
    
    parser.add_argument("--source", type=Path, help="Source library path to scan")
    parser.add_argument("--output-report", type=Path, default=Path("output/reports/dry_run.json"), help="Output path for JSON report")
    
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        config = load_config(args.config, args.paths_config)
        setup_logging(config.logging)
        
        return cmd_dry_run(args, config)
            
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
