"""
File scanning and hashing operations.

This module handles the discovery of comic files and calculation of their
checksums for inventory generation.
"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Set, Generator, Any, Callable
import logging

from src.core.logger import get_logger

logger = get_logger(__name__)

# Default extensions to scan for
DEFAULT_EXTENSIONS = {'.cbz', '.cbr', '.cb7', '.pdf', '.epub'}

def calculate_file_hash(
    file_path: Path,
    algorithm: str = 'sha256',
    chunk_size: int = 65536,
    progress_callback: Optional[Callable[[int], None]] = None
) -> str:
    """
    Calculate the hash of a file efficiently using chunks.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use (default: sha256)
        chunk_size: Size of chunks to read (default: 64KB)
        progress_callback: Optional callback for progress updates (bytes read)
        
    Returns:
        Hex digest of the hash
    """
    hasher = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                hasher.update(chunk)
                if progress_callback:
                    progress_callback(len(chunk))
                    
        return hasher.hexdigest()
    except OSError as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise

def scan_library(
    source_path: Path,
    extensions: Set[str] = DEFAULT_EXTENSIONS,
    progress_callback: Optional[Callable[[str], None]] = None
) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for comic files.
    
    Args:
        source_path: Root directory to scan
        extensions: Set of file extensions to include (must include dot)
        progress_callback: Optional callback when a file is found
        
    Returns:
        List of dictionaries containing file metadata
    """
    inventory = []
    source_path = Path(source_path).resolve()
    
    if not source_path.exists():
        logger.error(f"Source path does not exist: {source_path}")
        return []
        
    logger.info(f"Scanning {source_path} for extensions: {extensions}")
    
    try:
        # Walk through directory
        for root, _, files in os.walk(source_path):
            root_path = Path(root)
            
            for filename in files:
                file_path = root_path / filename
                
                # Check extension (case-insensitive)
                if file_path.suffix.lower() in extensions:
                    if progress_callback:
                        progress_callback(str(file_path))
                        
                    try:
                        stat = file_path.stat()
                        
                        # Basic metadata
                        file_data = {
                            "path": str(file_path),
                            "rel_path": str(file_path.relative_to(source_path)),
                            "name": filename,
                            "extension": file_path.suffix.lower(),
                            "size_bytes": stat.st_size,
                            "modified_time": stat.st_mtime,
                            # Hash will be calculated separately or here depending on needs
                            # For now, we'll calculate it here as part of the scan
                            # In a real large-scale system, we might want to separate this
                            "hash": calculate_file_hash(file_path)
                        }
                        
                        inventory.append(file_data)
                        
                    except (OSError, PermissionError) as e:
                        logger.warning(f"Could not access file {file_path}: {e}")
                        
    except Exception as e:
        logger.error(f"Error during scan of {source_path}: {e}")
        raise
        
    return inventory
