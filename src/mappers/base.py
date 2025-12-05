"""
Base class for path mappers.

Mappers are responsible for calculating the target path for a comic file
based on its metadata and the project's naming conventions.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any

from src.core.config import AppConfig
from src.metadata.providers.base import MetadataResult

class BaseMapper(ABC):
    """
    Abstract base class for path mappers.
    """
    
    def __init__(self, config: AppConfig):
        self.config = config
        
    @abstractmethod
    def calculate_path(self, metadata: MetadataResult, original_extension: str) -> Path:
        """
        Calculate the target path for a file.
        
        Args:
            metadata: The normalized metadata for the file
            original_extension: The file extension (e.g., '.cbz')
            
        Returns:
            Absolute Path object for the target location
        """
        pass
        
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string to be safe for filenames.
        """
        # Replace illegal characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '')
            
        # Remove trailing/leading spaces and dots
        name = name.strip('. ')
        
        return name
