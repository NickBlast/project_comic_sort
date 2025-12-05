"""
CLI entry point for Phase 3 - Mapping operations.

This module provides command-line interface for:
- Testing mapping logic with dummy data
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table

from src.core.config import load_config, AppConfig
from src.core.logger import setup_logging, get_logger
from src.mappers.selector import MapperSelector
from src.metadata.providers.base import MetadataResult

logger = get_logger(__name__)
console = Console()

def cmd_test_map(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Test mapping logic.
    """
    content_type = args.type
    series = args.series
    issue = args.issue
    year = args.year
    publisher = args.publisher
    volume = args.volume
    
    console.print(f"\n[bold blue]Testing Mapping Logic[/bold blue]")
    console.print(f"Type: [cyan]{content_type}[/cyan]")
    console.print(f"Metadata: Series='{series}', Issue='{issue}', Year={year}, Pub='{publisher}'")
    
    mapper = MapperSelector.get_mapper(content_type, config)
    if not mapper:
        console.print(f"[bold red]No mapper found for type: {content_type}[/bold red]")
        return 1
        
    # Create dummy metadata
    metadata = MetadataResult(
        provider="manual",
        provider_id="0",
        series=series,
        issue_number=str(issue),
        year=year,
        publisher=publisher,
        volume=volume
    )
    
    try:
        path = mapper.calculate_path(metadata, ".cbz")
        console.print(f"\n[bold green]Calculated Path:[/bold green]")
        console.print(f"[yellow]{path}[/yellow]")
        return 0
        
    except Exception as e:
        console.print(f"[bold red]Error calculating path: {e}[/bold red]")
        return 1

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for mapping CLI."""
    parser = argparse.ArgumentParser(
        prog="comic-map",
        description="Comic path mapper (Phase 3)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--paths-config", type=Path, help="Path to paths configuration file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test mapping logic")
    test_parser.add_argument("--type", choices=["western", "manga"], required=True, help="Content type")
    test_parser.add_argument("--series", required=True, help="Series name")
    test_parser.add_argument("--issue", type=int, default=1, help="Issue number")
    test_parser.add_argument("--year", type=int, default=2023, help="Year")
    test_parser.add_argument("--publisher", default="Marvel", help="Publisher (Western only)")
    test_parser.add_argument("--volume", type=int, default=1, help="Volume (Manga only)")
    
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        config = load_config(args.config, args.paths_config)
        setup_logging(config.logging)
        
        if args.command == "test":
            return cmd_test_map(args, config)
        else:
            parser.print_help()
            return 0
            
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
