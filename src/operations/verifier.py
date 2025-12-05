"""
Backup verification operations.

This module handles the comparison between original inventory and backup locations
to ensure data integrity.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import logging

from src.core.logger import get_logger
from src.operations.scanner import scan_library

logger = get_logger(__name__)

def load_inventory(inventory_path: Path) -> List[Dict[str, Any]]:
    """Load inventory from JSON file."""
    try:
        with open(inventory_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load inventory from {inventory_path}: {e}")
        raise

def verify_backup(
    original_inventory_path: Path,
    backup_path: Path
) -> Dict[str, Any]:
    """
    Verify a backup against an original inventory.
    
    Args:
        original_inventory_path: Path to the original inventory JSON
        backup_path: Path to the backup directory
        
    Returns:
        Dictionary containing verification results (matches, missing, extra, corrupted)
    """
    logger.info(f"Verifying backup at {backup_path} against {original_inventory_path}")
    
    # Load original inventory
    original_items = load_inventory(original_inventory_path)
    
    # Create a map of hash -> item for quick lookup
    # We use hash as the primary key for content verification
    original_map = {item['hash']: item for item in original_items}
    
    # Scan backup
    backup_items = scan_library(backup_path)
    
    results = {
        "total_original": len(original_items),
        "total_backup": len(backup_items),
        "matches": [],
        "missing": [],
        "extra": [],
        "corrupted": []  # Same path but different hash (if we matched by path)
    }
    
    # Check for matches and extras
    backup_hashes = set()
    for item in backup_items:
        file_hash = item['hash']
        backup_hashes.add(file_hash)
        
        if file_hash in original_map:
            results["matches"].append(item)
        else:
            results["extra"].append(item)
            
    # Check for missing files
    for item in original_items:
        if item['hash'] not in backup_hashes:
            results["missing"].append(item)
            
    return results
