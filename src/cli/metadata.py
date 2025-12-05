"""
CLI entry point for Phase 2 - Metadata operations.

This module provides command-line interface for:
- Fetching metadata for a specific series
- Testing provider connectivity
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

from rich.console import Console
from rich.table import Table

from src.core.config import load_config, AppConfig
from src.core.logger import setup_logging, get_logger
from src.metadata.providers import ComicVineProvider, AniListProvider
from src.metadata.confidence import ConfidenceScorer

logger = get_logger(__name__)
console = Console()

def cmd_search(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Search for a series using enabled providers.
    """
    query = args.query
    provider_name = args.provider
    
    console.print(f"\n[bold blue]Searching for: {query}[/bold blue]")
    
    providers = []
    if provider_name == "comicvine" or provider_name == "all":
        providers.append(ComicVineProvider(config.metadata_providers.comicvine))
    if provider_name == "anilist" or provider_name == "all":
        providers.append(AniListProvider(config.metadata_providers.anilist))
        
    scorer = ConfidenceScorer(config.confidence)
    
    for provider in providers:
        if not provider.enabled:
            console.print(f"[yellow]Provider {provider.name} is disabled.[/yellow]")
            continue
            
        console.print(f"\n[bold cyan]Results from {provider.name}:[/bold cyan]")
        
        try:
            results = provider.search_series(query)
            
            if not results:
                console.print("No results found.")
                continue
                
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("ID")
            table.add_column("Series")
            table.add_column("Year")
            table.add_column("Score")
            table.add_column("Confidence")
            
            for result in results:
                score = scorer.calculate_score(query, result)
                confidence = scorer.evaluate_match(score)
                
                conf_style = "green" if confidence == "HIGH" else "yellow" if confidence == "MEDIUM" else "red"
                
                table.add_row(
                    result.provider_id,
                    result.series,
                    str(result.year) if result.year else "N/A",
                    f"{score:.2f}",
                    f"[{conf_style}]{confidence}[/{conf_style}]"
                )
                
            console.print(table)
            
        except Exception as e:
            console.print(f"[bold red]Error querying {provider.name}: {e}[/bold red]")
            logger.error(f"Search failed for {provider.name}: {e}", exc_info=True)
            
    return 0

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for metadata CLI."""
    parser = argparse.ArgumentParser(
        prog="comic-metadata",
        description="Comic metadata fetcher (Phase 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("--config", type=Path, help="Path to configuration file")
    parser.add_argument("--paths-config", type=Path, help="Path to paths configuration file")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for a series")
    search_parser.add_argument("query", help="Series name to search for")
    search_parser.add_argument("--provider", choices=["comicvine", "anilist", "all"], default="all", help="Provider to use")
    
    return parser

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        config = load_config(args.config, args.paths_config)
        setup_logging(config.logging)
        
        if args.command == "search":
            return cmd_search(args, config)
        else:
            parser.print_help()
            return 0
            
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {e}[/bold red]")
        return 1

if __name__ == "__main__":
    sys.exit(main())
