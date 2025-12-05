"""
Confidence scoring logic for metadata matching.

This module provides the ConfidenceScorer class, which calculates a similarity score
between local file metadata and remote provider metadata.
"""

import difflib
from typing import Optional, Dict, Any
from src.core.logger import get_logger
from src.metadata.providers.base import MetadataResult
from src.core.config import ConfidenceConfig

logger = get_logger(__name__)

class ConfidenceScorer:
    """
    Calculates confidence scores for metadata matches.
    """
    
    def __init__(self, config: ConfidenceConfig):
        self.config = config
        
    def calculate_score(self, local_name: str, remote_metadata: MetadataResult) -> float:
        """
        Calculate the confidence score between a local filename/metadata and a remote result.
        
        Args:
            local_name: The local filename or parsed series name
            remote_metadata: The metadata result from a provider
            
        Returns:
            Float between 0.0 and 1.0
        """
        score = 0.0
        
        # 1. Series Name Match (Weighted 60%)
        # Normalize strings (lowercase, remove special chars could be added here)
        local_series = local_name.lower()
        remote_series = remote_metadata.series.lower()
        
        series_similarity = difflib.SequenceMatcher(None, local_series, remote_series).ratio()
        score += series_similarity * 0.6
        
        # 2. Year Match (Weighted 20%)
        # If we have year info, it's a strong indicator
        # For now, we might not have local year easily without parsing, 
        # so this is a placeholder for when we pass parsed local metadata
        
        # 3. Issue Number Match (Weighted 20%)
        # Similarly, if we extracted issue number, we check it
        
        # For now, since we are just searching by series name mostly:
        # If exact match, boost score
        if local_series == remote_series:
            score = 1.0
            
        return round(score, 2)

    def evaluate_match(self, score: float) -> str:
        """
        Return the confidence level string based on score and config.
        """
        if score >= self.config.high_confidence_threshold:
            return "HIGH"
        elif score >= self.config.medium_confidence_threshold:
            return "MEDIUM"
        else:
            return "LOW"
