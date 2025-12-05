"""
Manga path mapper.

Handles naming for Manga.
Format: Series/Series v01.cbz
"""

from pathlib import Path
from src.mappers.base import BaseMapper
from src.metadata.providers.base import MetadataResult

class MangaMapper(BaseMapper):
    """
    Mapper for Manga.
    """
    
    def calculate_path(self, metadata: MetadataResult, original_extension: str) -> Path:
        # Get naming templates from config
        folder_fmt = self.config.naming.manga_folder_format
        file_fmt = self.config.naming.manga_volume_format
        root_path = Path(self.config.paths.target_roots.manga)
        
        # Prepare data for formatting
        data = {
            "series": self.sanitize_filename(metadata.series or "Unknown Series"),
            "volume": int(metadata.volume) if metadata.volume else 0,
            "chapter": int(metadata.issue_number) if metadata.issue_number and metadata.issue_number.isdigit() else 0,
            "year": str(metadata.year) if metadata.year else "0000"
        }
        
        # Format strings
        try:
            folder_name = folder_fmt.format(**data)
            file_name = file_fmt.format(**data)
        except KeyError:
            folder_name = f"{data['series']}"
            file_name = f"{data['series']} v{data['volume']:02d}"
            
        return root_path / folder_name / (file_name + original_extension)
