"""
ComicVine API provider implementation.

Handles searching and fetching metadata from ComicVine.
Includes rate limiting and error handling.
"""

import time
from typing import List, Optional, Dict, Any
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.core.logger import get_logger
from src.metadata.providers.base import BaseMetadataProvider, MetadataResult

logger = get_logger(__name__)

class ComicVineProvider(BaseMetadataProvider):
    """
    Metadata provider for ComicVine API.
    
    Requires an API key.
    Docs: https://comicvine.gamespot.com/api/documentation
    """
    
    BASE_URL = "https://comicvine.gamespot.com/api"
    
    def __init__(self, config: Any):
        super().__init__(config)
        self.name = "comicvine"
        self.api_key = config.api_key
        self.user_agent = "ProjectComicSort/0.1"
        
        if not self.api_key:
            logger.warning("ComicVine API key not configured. Provider will be disabled.")
            self.enabled = False
            
    def _get_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": self.user_agent
        }
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException)
    )
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to ComicVine API with retries and rate limiting.
        """
        if not self.enabled:
            return {}
            
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Add required params
        params["api_key"] = self.api_key
        params["format"] = "json"
        
        try:
            response = requests.get(url, params=params, headers=self._get_headers(), timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("error") != "OK":
                logger.error(f"ComicVine API error: {data.get('error')}")
                return {}
                
            return data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 420: # Rate limit
                logger.warning("ComicVine rate limit exceeded. Waiting...")
                time.sleep(5)
                raise # Retry will handle it
            raise
            
    def search_series(self, query: str) -> List[MetadataResult]:
        """Search for a comic series on ComicVine."""
        if not self.enabled:
            return []
            
        logger.info(f"Searching ComicVine for series: {query}")
        
        params = {
            "query": query,
            "resources": "volume", # In CV, 'volume' = series
            "field_list": "id,name,start_year,publisher,count_of_issues,image,site_detail_url"
        }
        
        try:
            data = self._make_request("search", params)
            results = []
            
            for item in data.get("results", []):
                publisher_name = item.get("publisher", {}).get("name") if item.get("publisher") else None
                
                result = MetadataResult(
                    provider=self.name,
                    provider_id=str(item.get("id")),
                    series=item.get("name"),
                    year=int(item.get("start_year")) if item.get("start_year") else None,
                    publisher=publisher_name,
                    image_url=item.get("image", {}).get("medium_url"),
                    web_url=item.get("site_detail_url"),
                    description=f"Issues: {item.get('count_of_issues')}"
                )
                results.append(result)
                
            return results
            
        except Exception as e:
            logger.error(f"Error searching ComicVine: {e}")
            return []

    def get_issue_details(self, series_id: str, issue_number: str, year: Optional[int] = None) -> Optional[MetadataResult]:
        """Get details for a specific issue."""
        if not self.enabled:
            return None
            
        logger.info(f"Fetching details for series {series_id} issue {issue_number}")
        
        # First we need to find the issue ID. 
        # ComicVine doesn't have a direct lookup by series_id + issue_number in one go easily without filtering
        # We use the 'issues' endpoint with filter
        
        params = {
            "filter": f"volume:{series_id},issue_number:{issue_number}",
            "field_list": "id,name,issue_number,volume,cover_date,description,image,site_detail_url"
        }
        
        try:
            data = self._make_request("issues", params)
            results = data.get("results", [])
            
            if not results:
                return None
                
            # If multiple matches (rare for same volume+number), pick first or use year to disambiguate
            item = results[0]
            
            # Parse date for year
            pub_year = None
            if item.get("cover_date"):
                try:
                    pub_year = int(item.get("cover_date").split("-")[0])
                except (ValueError, IndexError):
                    pass
            
            result = MetadataResult(
                provider=self.name,
                provider_id=str(item.get("id")),
                series=item.get("volume", {}).get("name"),
                title=item.get("name"),
                issue_number=item.get("issue_number"),
                year=pub_year,
                description=item.get("description"),
                image_url=item.get("image", {}).get("medium_url"),
                web_url=item.get("site_detail_url")
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching issue details: {e}")
            return None
