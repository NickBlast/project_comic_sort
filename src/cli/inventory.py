"""
CLI entry point for Phase 1 - Inventory and Backup operations.

This module provides command-line interface for:
- Scanning source libraries and generating inventories
- Verifying backups against original inventories
- Running safety checks before operations

Phase 0: Basic skeleton with safety checks integration
Phase 1: Full implementation of scan and verify commands (TODO)

Usage:
    python -m src.cli.inventory --help
    python -m src.cli.inventory scan --source /path/to/comics
    python -m src.cli.inventory verify --original inventory.json --backup /path
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from src.core.config import load_config, AppConfig
from src.core.logger import setup_logging, get_logger
from src.operations.safety_checks import run_safety_checks, print_safety_check_results

logger = get_logger(__name__)

# ==============================================================================
# COMMAND HANDLERS (STUBS FOR PHASE 1)
# ==============================================================================

def cmd_scan(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Scan source libraries and generate inventory.
    
    TODO Phase 1: Implement full scanning logic
    - Recursively discover comic files (.cbz, .cbr, .cb7, .pdf)
    - Calculate SHA256 hash for each file
    - Collect file metadata (size, modified time)
    - Output to JSON inventory file
    
    Args:
        args: Parsed command-line arguments
        config: Application configuration
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info(
        "Scan command invoked (STUB)",
        extra={
            "phase": "inventory",
            "operation": "scan",
            "metadata": {
                "source": args.source if args.source else "from config",
                "output": args.output,
            }
        }
    )
    
    print("\n" + "="*70)
    print("INVENTORY SCAN (Phase 1 - NOT YET IMPLEMENTED)")
    print("="*70)
    print("\nThis command will be implemented in Phase 1.")
    print("\nPlanned functionality:")
    print("  - Recursively scan source directories for comic files")
    print("  - Calculate SHA256 hashes for integrity verification")
    print("  - Generate JSON inventory with file metadata")
    print("  - Support for CBZ, CBR, CB7, and PDF formats")
    print("\n" + "="*70 + "\n")
    
    return 0

def cmd_verify(args: argparse.Namespace, config: AppConfig) -> int:
    """
    Verify backup against original inventory.
    
    TODO Phase 1: Implement verification logic
    - Load original inventory JSON
    - Scan backup location
    - Compare file lists and hashes
    - Report any missing or corrupted files
    
    Args:
        args: Parsed command-line arguments
        config: Application configuration
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    logger.info(
        "Verify command invoked (STUB)",
        extra={
            "phase": "inventory",
            "operation": "verify",
            "metadata": {
                "original": args.original,
                "backup": args.backup,
            }
        }
    )
    
    print("\n" + "="*70)
    print("BACKUP VERIFICATION (Phase 1 - NOT YET IMPLEMENTED)")
    print("="*70)
    print("\nThis command will be implemented in Phase 1.")
    print("\nPlanned functionality:")
    print("  - Load original pre-migration inventory")
    print("  - Re-scan backup location")
    print("  - Compare file counts and SHA256 hashes")
    print("  - Report missing or corrupted files")
    print("  - Generate diff report")
    print("\n" + "="*70 + "\n")
    
    return 0

# ==============================================================================
# CLI SETUP AND MAIN
# ==============================================================================

def create_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for inventory CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="comic-inventory",
        description="Comic library inventory and backup verification tool (Phase 1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run safety checks only
  python -m src.cli.inventory --safety-checks-only
  
  # Scan source library (Phase 1 - TODO)
  python -m src.cli.inventory scan --source /path/to/comics --output inventory.json
  
  # Verify backup (Phase 1 - TODO)
  python -m src.cli.inventory verify --original inventory.json --backup /path/to/backup

For more information, see docs/README.md
        """
    )
    
    # Global options
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: config/example_config.yml)"
    )
    
    parser.add_argument(
        "--paths-config",
        type=Path,
        help="Path to paths configuration file (default: config/paths.example.yml)"
    )
    
    parser.add_argument(
        "--safety-checks-only",
        action="store_true",
        help="Run safety checks only and exit"
    )
    
    parser.add_argument(
        "--skip-safety-checks",
        action="store_true",
        help="Skip safety checks (NOT RECOMMENDED)"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Scan command
    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan source libraries and generate inventory"
    )
    scan_parser.add_argument(
        "--source",
        type=Path,
        help="Source library path to scan (overrides config)"
    )
    scan_parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/inventories/inventory.json"),
        help="Output path for inventory JSON file"
    )
    
    # Verify command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify backup against original inventory"
    )
    verify_parser.add_argument(
        "--original",
        type=Path,
        required=True,
        help="Path to original inventory JSON file"
    )
    verify_parser.add_argument(
        "--backup",
        type=Path,
        required=True,
        help="Path to backup location to verify"
    )
    
    return parser

def main(argv: Optional[list[str]] = None) -> int:
    """
    Main entry point for inventory CLI.
    
    This function:
    1. Parses command-line arguments
    2. Loads configuration
    3. Initializes logging
    4. Runs safety checks (unless skipped)
    5. Dispatches to appropriate command handler
    
    Args:
        argv: Command-line arguments (default: sys.argv[1:])
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        # Load configuration
        config = load_config(
            config_path=args.config,
            paths_config_path=args.paths_config
        )
        
        # Initialize logging
        setup_logging(config.logging)
        
        logger.info(
            "Inventory CLI started",
            extra={
                "phase": "bootstrap",
                "operation": "cli_startup",
                "metadata": {
                    "command": args.command,
                    "dry_run": config.environment.dry_run,
                }
            }
        )
        
        # Display mode warning
        if config.environment.dry_run:
            print("\n⚠️  DRY-RUN MODE ENABLED - No files will be modified\n")
        else:
            print("\n⚠️  APPLY MODE - Files WILL be modified\n")
        
        # Run safety checks unless explicitly skipped
        if not args.skip_safety_checks:
            print("Running safety checks...\n")
            
            passed, results = run_safety_checks(config)
            print_safety_check_results(results)
            
            if not passed:
                logger.error(
                    "Safety checks failed - cannot proceed",
                    extra={
                        "phase": "safety_checks",
                        "operation": "validation",
                        "status": "failed",
                    }
                )
                return 1
            
            # If only running safety checks, exit now
            if args.safety_checks_only:
                print("Safety checks passed. Exiting (--safety-checks-only)\n")
                return 0
        else:
            print("⚠️  WARNING: Safety checks skipped (NOT RECOMMENDED)\n")
        
        # Dispatch to command handler
        if args.command == "scan":
            return cmd_scan(args, config)
        elif args.command == "verify":
            return cmd_verify(args, config)
        else:
            # No command specified - show help
            parser.print_help()
            return 0
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        print("Ensure configuration files exist:", file=sys.stderr)
        print("  - config/example_config.yml", file=sys.stderr)
        print("  - config/paths.example.yml", file=sys.stderr)
        return 1
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user", file=sys.stderr)
        logger.warning(
            "Operation cancelled by user (Ctrl+C)",
            extra={
                "phase": "inventory",
                "operation": "user_cancel",
            }
        )
        return 130  # Standard exit code for SIGINT
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        logger.error(
            f"Unexpected error in inventory CLI: {e}",
            extra={
                "phase": "inventory",
                "operation": "cli_error",
                "error": str(e),
            },
            exc_info=True
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())
