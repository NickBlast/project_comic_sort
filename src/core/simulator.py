"""
Migration Simulator.

Orchestrates the dry-run process by:
1. Scanning source files
2. Extracting metadata
3. Calculating target paths
4. Detecting conflicts
5. Generating a plan of action
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

from src.core.config import AppConfig
from src.core.logger import get_logger
from src.operations.scanner import scan_library
from src.metadata.comic_info import extract_comic_info, ComicInfo
import src.metadata.comic_info
sys.stderr.write(f"DEBUG: src.metadata.comic_info loaded from: {src.metadata.comic_info.__file__}\n")

from src.metadata.providers.base import MetadataResult
from src.mappers.selector import MapperSelector

logger = get_logger(__name__)

@dataclass
class MigrationAction:
    """Represents a proposed action for a single file."""
    source_path: str
    target_path: str
    status: str  # COPY, SKIP, CONFLICT, ERROR
    reason: Optional[str] = None
    metadata_source: str = "none"  # comicinfo, filename, provider
    file_size: int = 0

class MigrationSimulator:
    """
    Simulates the migration process without moving files.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        self.actions: List[MigrationAction] = []
        self.target_map: Dict[str, str] = {}  # target_path -> source_path (for conflict detection)
        
    def _comic_info_to_metadata(self, info: ComicInfo) -> MetadataResult:
        """Convert ComicInfo to MetadataResult."""
        return MetadataResult(
            provider="comicinfo",
            provider_id="0",
            series=info.Series,
            title=info.Title,
            issue_number=info.Number,
            volume=info.Volume,
            year=info.Year,
            publisher=info.Publisher,
            description=info.Summary
        )
        
    def _create_fallback_metadata(self, file_path: Path) -> MetadataResult:
        """Create minimal metadata from filename if extraction fails."""
        # Very basic fallback
        return MetadataResult(
            provider="filename",
            provider_id="0",
            series=file_path.stem,  # Use filename as series/title
            title=file_path.stem
        )

    def run(self, source_path: Path) -> List[MigrationAction]:
        """
        Run the simulation on the given source path.
        """
        logger.info(f"Starting simulation on {source_path}")
        sys.stderr.write(f"DEBUG: Starting simulation on {source_path}\n")
        self.actions = []
        self.target_map = {}
        
        # 1. Scan
        sys.stderr.write("DEBUG: Calling scan_library...\n")
        files = scan_library(source_path)
        sys.stderr.write(f"DEBUG: scan_library returned {len(files)} files\n")
        
        for file_data in files:
            source_file = Path(file_data['path'])
            sys.stderr.write(f"DEBUG: Processing {source_file}\n")
            
            try:
                # 2. Extract Metadata
                # Try ComicInfo.xml first
                sys.stderr.write("DEBUG: Calling extract_comic_info...\n")
                comic_info = extract_comic_info(source_file)
                sys.stderr.write(f"DEBUG: extract_comic_info returned {comic_info}\n")
                
                if comic_info:
                    metadata = self._comic_info_to_metadata(comic_info)
                    meta_source = "comicinfo"
                else:
                    # Fallback to filename
                    metadata = self._create_fallback_metadata(source_file)
                    meta_source = "filename"
                
                # 3. Select Mapper
                # Determine content type (simple logic for now, could be improved)
                # If metadata has "Manga" field set to Yes, or path contains "Manga"
                content_type = "western" # Default
                if comic_info and comic_info.Manga == "Yes":
                    content_type = "manga"
                elif "manga" in str(source_file).lower():
                    content_type = "manga"
                    
                mapper = MapperSelector.get_mapper(content_type, self.config)
                
                if not mapper:
                    self.actions.append(MigrationAction(
                        source_path=str(source_file),
                        target_path="",
                        status="ERROR",
                        reason=f"No mapper for type {content_type}",
                        file_size=file_data['size_bytes']
                    ))
                    continue
                    
                # 4. Calculate Target
                target_path = mapper.calculate_path(metadata, source_file.suffix)
                target_str = str(target_path)
                
                # 5. Check Conflicts
                status = "COPY"
                reason = None
                
                if target_path.exists():
                    status = "SKIP"
                    reason = "Target already exists"
                elif target_str in self.target_map:
                    status = "CONFLICT"
                    reason = f"Clash with {self.target_map[target_str]}"
                else:
                    self.target_map[target_str] = str(source_file)
                    
                self.actions.append(MigrationAction(
                    source_path=str(source_file),
                    target_path=target_str,
                    status=status,
                    reason=reason,
                    metadata_source=meta_source,
                    file_size=file_data['size_bytes']
                ))
                
            except Exception as e:
                sys.stderr.write(f"DEBUG: Exception in loop: {e}\n")
                logger.error(f"Error processing {source_file}: {e}")
                self.actions.append(MigrationAction(
                    source_path=str(source_file),
                    target_path="",
                    status="ERROR",
                    reason=str(e),
                    file_size=file_data.get('size_bytes', 0)
                ))
                
        return self.actions
