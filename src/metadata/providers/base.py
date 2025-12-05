"""
Base class for metadata providers.

This module defines the interface that all metadata providers (ComicVine, AniList, etc.)
must implement to ensure consistent behavior.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class MetadataResult(BaseModel):
    """
    Standardized metadata result from any provider.
    
    This normalizes data from different sources into a common format
    used by the rest of the application.
    """
    provider: str = Field(..., description="Name of the provider (e.g., 'comicvine')")
    provider_id: str = Field(..., description="Unique ID from the provider")
    series: str = Field(..., description="Series name")
    title: Optional[str] = Field(None, description="Issue title")
    issue_number: Optional[str] = Field(None, description="Issue number")
    volume: Optional[int] = Field(None, description="Volume number")
    year: Optional[int] = Field(None, description="Publication year")
    publisher: Optional[str] = Field(None, description="Publisher name")
    description: Optional[str] = Field(None, description="Summary/Description")
    image_url: Optional[str] = Field(None, description="Cover image URL")
    web_url: Optional[str] = Field(None, description="Link to provider page")
    score: float = Field(default=0.0, description="Match confidence score 0.0-1.0")

class BaseMetadataProvider(ABC):
    """
    Abstract base class for metadata providers.
    
    All providers must inherit from this class and implement the abstract methods.
    """
    
    def __init__(self, config: Any):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration object
        """
        self.config = config
        self.name = "base"
        self.enabled = True
        
    @abstractmethod
    def search_series(self, query: str) -> List[MetadataResult]:
        """
        Search for a comic series.
        
        Args:
            query: Search string (e.g., "Batman")
            
        Returns:
            List of MetadataResult objects representing series
        """
        pass
        
    @abstractmethod
    def get_issue_details(self, series_id: str, issue_number: str, year: Optional[int] = None) -> Optional[MetadataResult]:
        """
        Get details for a specific issue.
        
        Args:
            series_id: Provider-specific series ID
            issue_number: Issue number string
            year: Optional publication year to help disambiguation
            
        Returns:
            MetadataResult object or None if not found
        """
        pass
