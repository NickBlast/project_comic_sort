"""
Configuration loading and validation module.

This module provides centralized configuration management using Pydantic for
validation and YAML for human-readable config files. It supports:
- Environment variable substitution (${VAR_NAME} syntax)
- Multiple config file loading (main config + paths config)
- Type validation and default values
- Cross-platform path handling

Usage:
    from src.core.config import load_config
    
    config = load_config()
    if config.environment.dry_run:
        print("Running in dry-run mode")
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv


# Load environment variables from .env file if present
# This allows local development without setting system env vars
load_dotenv()


# ==============================================================================
# PYDANTIC MODELS FOR CONFIGURATION VALIDATION
# ==============================================================================

class EnvironmentConfig(BaseModel):
    """
    Environment-level settings controlling overall behavior.
    
    The dry_run flag is the most critical safety feature - it ensures that
    no actual file operations occur until explicitly disabled after review.
    """
    dry_run: bool = Field(default=True, description="Enable dry-run mode (no actual file changes)")
    profile: str = Field(default="development", description="Configuration profile name")
    min_python_version: str = Field(default="3.8", description="Minimum required Python version")


class LoggingConfig(BaseModel):
    """
    Logging configuration for structured output to multiple destinations.
    
    JSON formatting enables easy parsing and analysis of logs by external tools.
    Multiple log files allow filtering by severity without post-processing.
    """
    level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    operations_log: str = Field(default="logs/operations_{timestamp}.log")
    debug_log: str = Field(default="logs/debug_{timestamp}.log")
    errors_log: str = Field(default="logs/errors_{timestamp}.log")
    console_output: bool = Field(default=True, description="Also output to console")
    max_bytes: int = Field(default=10485760, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of rotated log files to keep")
    json_format: bool = Field(default=True, description="Use JSON formatting for structured logs")


class SafetyConfig(BaseModel):
    """
    Safety settings to prevent data loss and system issues.
    
    These checks run before any destructive operations to ensure the
    environment is suitable for migration.
    """
    require_backup: bool = Field(default=True, description="Require backup before destructive ops")
    min_free_space_bytes: int = Field(default=107374182400, description="Min free space (100GB default)")
    operation_timeout: int = Field(default=300, description="Timeout in seconds per operation")
    verify_copy_integrity: bool = Field(default=True, description="Verify hash after copy")
    max_retries: int = Field(default=3, description="Max retries for transient failures")


class MetadataProviderConfig(BaseModel):
    """Individual metadata provider configuration."""
    enabled: bool = Field(default=True)
    api_key: Optional[str] = Field(default=None)
    url: Optional[str] = Field(default=None)
    timeout: int = Field(default=30)
    rate_limit: Optional[float] = Field(default=None)
    required: bool = Field(default=False, description="Exit if provider unavailable")


class MetadataProvidersConfig(BaseModel):
    """
    Configuration for all metadata providers.
    
    Each provider can be independently enabled/disabled. API keys are
    loaded from environment variables for security.
    """
    comicvine: MetadataProviderConfig = Field(default_factory=MetadataProviderConfig)
    anilist: MetadataProviderConfig = Field(default_factory=MetadataProviderConfig)
    mangadex: MetadataProviderConfig = Field(default_factory=MetadataProviderConfig)
    lanraragi: MetadataProviderConfig = Field(default_factory=MetadataProviderConfig)


class ConfidenceConfig(BaseModel):
    """
    Confidence level thresholds and behavior configuration.
    
    These thresholds determine how aggressively the system will automatically
    organize files vs. flagging them for manual review.
    """
    high_confidence_threshold: float = Field(default=0.9, ge=0.0, le=1.0)
    medium_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    best_guess_separate_folder: bool = Field(default=False)
    auto_approve_high_confidence: bool = Field(default=True)


class NamingConfig(BaseModel):
    """
    Naming templates for different content types.
    
    Templates use Python format string syntax with named variables.
    These patterns ensure consistency with Komga and Mylar3 expectations.
    """
    western_format: str = Field(default="{series} ({year}) #{issue:03d} ({date})")
    western_folder_format: str = Field(default="{publisher}/{series} ({start_year})")
    manga_volume_format: str = Field(default="{series} v{volume:02d}")
    manga_chapter_format: str = Field(default="{series} c{chapter:03d}")
    manga_folder_format: str = Field(default="{series}")
    hentai_oneshot_format: str = Field(default="({id}) - {title} ({language}) [{source}]")
    hentai_series_format: str = Field(default="{title} v{volume:02d}")
    hentai_folder_format: str = Field(default="[{circle}]/{title}")


class KomgaConfig(BaseModel):
    """Komga integration settings."""
    url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    comics_library_id: Optional[str] = Field(default=None)
    manga_library_id: Optional[str] = Field(default=None)
    hentai_library_id: Optional[str] = Field(default=None)
    auto_scan: bool = Field(default=True)


class Mylar3Config(BaseModel):
    """Mylar3 integration settings (optional)."""
    enabled: bool = Field(default=False)
    url: Optional[str] = Field(default=None)
    api_key: Optional[str] = Field(default=None)
    update_database: bool = Field(default=False)


class PerformanceConfig(BaseModel):
    """
    Performance tuning settings for parallel operations.
    
    Worker counts should be tuned based on system resources and API rate limits.
    Too many workers can overwhelm APIs or saturate I/O.
    """
    max_api_workers: int = Field(default=5, ge=1, le=20)
    max_hash_workers: int = Field(default=4, ge=1, le=16)
    max_copy_workers: int = Field(default=2, ge=1, le=10)
    batch_size: int = Field(default=100, ge=1)
    show_progress: bool = Field(default=True)


class OperationsConfig(BaseModel):
    """File operation behavior settings."""
    convert_cbr_to_cbz: bool = Field(default=False)
    set_permissions: Optional[str] = Field(default=None)
    preserve_timestamps: bool = Field(default=True)


class SourceLibrary(BaseModel):
    """Configuration for a single source library."""
    path: str
    content_type: str = Field(pattern="^(western|manga|hentai)$")
    enabled: bool = Field(default=True)
    
    @field_validator('path')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Expand environment variables in path."""
        return os.path.expandvars(v)


class TargetRoots(BaseModel):
    """Target root directories for each content type."""
    western: str
    manga: str
    hentai: str
    
    @field_validator('western', 'manga', 'hentai')
    @classmethod
    def validate_path(cls, v: str) -> str:
        """Expand environment variables in path."""
        return os.path.expandvars(v)


class PathsConfig(BaseModel):
    """
    Path configuration loaded from paths.yml.
    
    Paths are kept in a separate file to allow easy environment-specific
    overrides without modifying the main configuration.
    """
    source_libraries: List[SourceLibrary]
    target_roots: TargetRoots
    temp_workspace: str
    backup_location: Optional[str] = Field(default=None)
    content_type_overrides: Dict[str, str] = Field(default_factory=dict)
    
    @field_validator('temp_workspace', 'backup_location')
    @classmethod
    def validate_path(cls, v: Optional[str]) -> Optional[str]:
        """Expand environment variables in path."""
        if v is None:
            return None
        return os.path.expandvars(v)


class AppConfig(BaseModel):
    """
    Top-level application configuration.
    
    This aggregates all configuration sections into a single validated object
    that is passed throughout the application.
    """
    environment: EnvironmentConfig
    logging: LoggingConfig
    safety: SafetyConfig
    metadata_providers: MetadataProvidersConfig
    confidence: ConfidenceConfig
    naming: NamingConfig
    komga: KomgaConfig
    mylar3: Mylar3Config
    performance: PerformanceConfig
    operations: OperationsConfig
    paths: PathsConfig


# ==============================================================================
# CONFIGURATION LOADING FUNCTIONS
# ==============================================================================

def _substitute_env_vars(data: Any) -> Any:
    """
    Recursively substitute environment variables in configuration data.
    
    Supports ${VAR_NAME} and $VAR_NAME syntax. If the environment variable
    is not set, keeps the original string for later error handling.
    
    Args:
        data: Configuration data (dict, list, str, or primitive)
        
    Returns:
        Data with environment variables substituted
    """
    if isinstance(data, dict):
        return {k: _substitute_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_substitute_env_vars(item) for item in data]
    elif isinstance(data, str):
        # Pattern matches ${VAR_NAME} or $VAR_NAME
        pattern = re.compile(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?')
        
        def replace_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        
        return pattern.sub(replace_var, data)
    else:
        return data


def load_config(
    config_path: Optional[Path] = None,
    paths_config_path: Optional[Path] = None
) -> AppConfig:
    """
    Load and validate application configuration from YAML files.
    
    This function:
    1. Loads the main configuration file (defaults to config/example_config.yml)
    2. Loads the paths configuration file (defaults to config/paths.example.yml)
    3. Substitutes environment variables using ${VAR_NAME} syntax
    4. Validates all configuration using Pydantic models
    5. Returns a fully validated AppConfig object
    
    Future agents should extend this by:
    - Adding new Pydantic models for additional config sections
    - Adding those models as fields in AppConfig
    - The validation will automatically apply to new sections
    
    Args:
        config_path: Path to main config file (optional, defaults to example_config.yml)
        paths_config_path: Path to paths config file (optional, defaults to paths.example.yml)
        
    Returns:
        Validated AppConfig object
        
    Raises:
        FileNotFoundError: If config files don't exist
        ValueError: If config validation fails
        yaml.YAMLError: If YAML parsing fails
    """
    # Determine config file paths
    if config_path is None:
        config_path = Path("config/example_config.yml")
    else:
        config_path = Path(config_path)
        
    if paths_config_path is None:
        paths_config_path = Path("config/paths.example.yml")
    else:
        paths_config_path = Path(paths_config_path)
    
    # Verify files exist
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    if not paths_config_path.exists():
        raise FileNotFoundError(f"Paths configuration file not found: {paths_config_path}")
    
    # Load YAML files
    with open(config_path, 'r', encoding='utf-8') as f:
        config_data = yaml.safe_load(f)
    
    with open(paths_config_path, 'r', encoding='utf-8') as f:
        paths_data = yaml.safe_load(f)
    
    # Substitute environment variables in both configs
    config_data = _substitute_env_vars(config_data)
    paths_data = _substitute_env_vars(paths_data)
    
    # Combine configurations
    config_data['paths'] = paths_data
    
    # Validate and create AppConfig object
    # Pydantic will raise ValidationError if config is invalid
    try:
        app_config = AppConfig(**config_data)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}") from e
    
    return app_config


def get_config_value(config: AppConfig, key_path: str) -> Any:
    """
    Get a configuration value using dot notation.
    
    Example:
        value = get_config_value(config, "environment.dry_run")
        
    Args:
        config: AppConfig object
        key_path: Dot-separated path to config value
        
    Returns:
        Configuration value
        
    Raises:
        AttributeError: If key path is invalid
    """
    keys = key_path.split('.')
    value = config
    for key in keys:
        value = getattr(value, key)
    return value
