"""
AniList API provider implementation.

Handles searching and fetching manga metadata from AniList using GraphQL.
"""

import time
from typing import List, Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.logger import get_logger
from src.metadata.providers.base import BaseMetadataProvider, MetadataResult

logger = get_logger(__name__)

class AniListProvider(BaseMetadataProvider):
    """
    Metadata provider for AniList API (GraphQL).
    
    Docs: https://anilist.gitbook.io/anilist-apiv2-docs/
    """
    
    URL = 'https://graphql.anilist.co'
    
    def __init__(self, config: Any):
        super().__init__(config)
        self.name = "anilist"
        # AniList doesn't require an API key for read-only public data
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def _make_request(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Make a GraphQL request to AniList."""
        if not self.enabled:
            return {}
            
        try:
            response = requests.post(
                self.URL, 
                json={'query': query, 'variables': variables},
                timeout=30
            )
            
            # Handle rate limits (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"AniList rate limit exceeded. Waiting {retry_after}s...")
                time.sleep(retry_after)
                raise requests.exceptions.RequestException("Rate limit exceeded")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"AniList API error: {e}")
            raise
            
    def search_series(self, query: str) -> List[MetadataResult]:
        """Search for a manga series on AniList."""
        if not self.enabled:
            return []
            
        logger.info(f"Searching AniList for manga: {query}")
        
        gql = '''
        query ($search: String) {
            Page(page: 1, perPage: 10) {
                media(search: $search, type: MANGA, sort: SEARCH_MATCH) {
                    id
                    title {
                        romaji
                        english
                        native
                    }
                    startDate {
                        year
                    }
                    coverImage {
                        medium
                    }
                    siteUrl
                    description
                }
            }
        }
        '''
        
        try:
            data = self._make_request(gql, {'search': query})
            media_list = data.get('data', {}).get('Page', {}).get('media', [])
            results = []
            
            for item in media_list:
                # Prefer English title, fallback to Romaji
                title = item.get('title', {}).get('english') or item.get('title', {}).get('romaji')
                
                result = MetadataResult(
                    provider=self.name,
                    provider_id=str(item.get('id')),
                    series=title,
                    year=item.get('startDate', {}).get('year'),
                    image_url=item.get('coverImage', {}).get('medium'),
                    web_url=item.get('siteUrl'),
                    description=item.get('description')
                )
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching AniList: {e}")
            return []

    def get_issue_details(self, series_id: str, issue_number: str, year: Optional[int] = None) -> Optional[MetadataResult]:
        """
        Get details for a specific manga volume/chapter.
        
        Note: AniList is series-focused, not issue-focused. 
        This method mainly confirms the series exists and returns series info.
        """
        if not self.enabled:
            return None
            
        # For manga, "issue_number" usually maps to volume or chapter
        # AniList doesn't provide per-chapter metadata via public API easily
        # So we return the series metadata which is often sufficient for folder naming
        
        gql = '''
        query ($id: Int) {
            Media(id: $id, type: MANGA) {
                id
                title {
                    romaji
                    english
                }
                startDate {
                    year
                }
                coverImage {
                    medium
                }
                siteUrl
                description
            }
        }
        '''
        
        try:
            data = self._make_request(gql, {'id': int(series_id)})
            item = data.get('data', {}).get('Media')
            
            if not item:
                return None
                
            title = item.get('title', {}).get('english') or item.get('title', {}).get('romaji')
            
            result = MetadataResult(
                provider=self.name,
                provider_id=str(item.get('id')),
                series=title,
                issue_number=issue_number, # Pass through
                year=item.get('startDate', {}).get('year'),
                image_url=item.get('coverImage', {}).get('medium'),
                web_url=item.get('siteUrl'),
                description=item.get('description')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching AniList details: {e}")
            return None
