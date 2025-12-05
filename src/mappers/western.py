"""
Western comic path mapper.

Handles naming for Western comics (DC, Marvel, Image, etc.).
Format: Publisher/Series (Year)/Series #Issue (Date).cbz
"""

from pathlib import Path
from src.mappers.base import BaseMapper
from src.metadata.providers.base import MetadataResult

class WesternMapper(BaseMapper):
    """
    Mapper for Western comics.
    """
    
    def calculate_path(self, metadata: MetadataResult, original_extension: str) -> Path:
        # Get naming templates from config
        folder_fmt = self.config.naming.western_folder_format
        file_fmt = self.config.naming.western_format
        root_path = Path(self.config.paths.target_roots.western)
        
        # Prepare data for formatting
        data = {
            "publisher": self.sanitize_filename(metadata.publisher or "Unknown Publisher"),
            "series": self.sanitize_filename(metadata.series or "Unknown Series"),
            "start_year": str(metadata.year) if metadata.year else "0000",
            "year": str(metadata.year) if metadata.year else "0000", # Issue year vs Series year?
            "issue": int(metadata.issue_number) if metadata.issue_number and metadata.issue_number.isdigit() else 0,
            "date": str(metadata.year) if metadata.year else "0000-00-00", # Placeholder for full date
            "title": self.sanitize_filename(metadata.title or "")
        }
        
        # Format strings
        try:
            folder_name = folder_fmt.format(**data)
            file_name = file_fmt.format(**data)
        except KeyError as e:
            # Fallback if template uses keys we don't have
            folder_name = f"{data['publisher']}/{data['series']} ({data['start_year']})"
            file_name = f"{data['series']} #{data['issue']:03d}"
            
        return root_path / folder_name / (file_name + original_extension)
