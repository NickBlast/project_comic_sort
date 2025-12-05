"""
ComicInfo.xml handling module.

This module provides functionality to parse ComicInfo.xml files,
typically found in CBZ/CBR archives.
"""

import sys
import zipfile
from pathlib import Path
from typing import Optional, Union
from xml.etree import ElementTree
from pydantic import BaseModel, Field, ValidationError

from src.core.logger import get_logger

logger = get_logger(__name__)
sys.stderr.write("DEBUG: src.metadata.comic_info IMPORTED\n")

class ComicInfo(BaseModel):
    """
    Pydantic model for ComicInfo.xml data.
    Based on the schema commonly used by ComicRack and other tools.
    """
    Title: Optional[str] = None
    Series: Optional[str] = None
    Number: Optional[str] = None
    Count: Optional[int] = None
    Volume: Optional[int] = None
    AlternateSeries: Optional[str] = None
    AlternateNumber: Optional[str] = None
    AlternateCount: Optional[int] = None
    Summary: Optional[str] = None
    Notes: Optional[str] = None
    Year: Optional[int] = None
    Month: Optional[int] = None
    Day: Optional[int] = None
    Writer: Optional[str] = None
    Penciller: Optional[str] = None
    Inker: Optional[str] = None
    Colorist: Optional[str] = None
    Letterer: Optional[str] = None
    CoverArtist: Optional[str] = None
    Editor: Optional[str] = None
    Publisher: Optional[str] = None
    Imprint: Optional[str] = None
    Genre: Optional[str] = None
    Web: Optional[str] = None
    PageCount: Optional[int] = None
    LanguageISO: Optional[str] = None
    Format: Optional[str] = None
    BlackAndWhite: Optional[str] = None
    Manga: Optional[str] = None
    Characters: Optional[str] = None
    Teams: Optional[str] = None
    Locations: Optional[str] = None
    ScanInformation: Optional[str] = None
    StoryArc: Optional[str] = None
    SeriesGroup: Optional[str] = None
    AgeRating: Optional[str] = None
    CommunityRating: Optional[float] = None

def parse_comic_info_xml(xml_string: Union[str, bytes]) -> Optional[ComicInfo]:
    """
    Parse ComicInfo.xml content into a ComicInfo object.
    """
    try:
        root = ElementTree.fromstring(xml_string)
        data = {}
        
        for child in root:
            if child.text:
                data[child.tag] = child.text.strip()
                
        return ComicInfo(**data)
        
    except (ElementTree.ParseError, ValidationError) as e:
        sys.stderr.write(f"DEBUG: Failed to parse ComicInfo.xml: {e}\n")
        logger.warning(f"Failed to parse ComicInfo.xml: {e}")
        return None

def extract_comic_info(archive_path: Path) -> Optional[ComicInfo]:
    """
    Extract and parse ComicInfo.xml from a comic archive.
    """
    suffix = archive_path.suffix.lower()
    
    try:
        sys.stderr.write(f"DEBUG: Extracting from {archive_path}\n")
        if suffix in ['.cbz', '.zip']:
            if not zipfile.is_zipfile(archive_path):
                sys.stderr.write(f"DEBUG: File is not a valid zip: {archive_path}\n")
                logger.warning(f"File is not a valid zip: {archive_path}")
                return None
                
            with zipfile.ZipFile(archive_path, 'r') as zf:
                if 'ComicInfo.xml' in zf.namelist():
                    sys.stderr.write("DEBUG: Found ComicInfo.xml\n")
                    with zf.open('ComicInfo.xml') as f:
                        return parse_comic_info_xml(f.read())
    except Exception as e:
        sys.stderr.write(f"DEBUG: Caught exception in extract_comic_info: {e}\n")
        logger.error(f"Error reading archive {archive_path}: {e}")
    return None
