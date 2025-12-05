"""
Mapper selector factory.

Selects the appropriate mapper based on content type.
"""

from typing import Optional
from src.core.config import AppConfig
from src.mappers.base import BaseMapper
from src.mappers.western import WesternMapper
from src.mappers.manga import MangaMapper

class MapperSelector:
    """
    Factory for creating mappers.
    """
    
    @staticmethod
    def get_mapper(content_type: str, config: AppConfig) -> Optional[BaseMapper]:
        """
        Get the mapper for the given content type.
        
        Args:
            content_type: 'western', 'manga', or 'hentai'
            config: Application configuration
            
        Returns:
            Mapper instance or None if type not supported
        """
        if content_type == 'western':
            return WesternMapper(config)
        elif content_type == 'manga':
            return MangaMapper(config)
        # Hentai mapper TODO
        
        return None
