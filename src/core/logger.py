"""
Centralized logging setup for structured, JSON-formatted logs.

This module provides a consistent logging interface across the entire application.
All logs are output in JSON Lines format for easy parsing and analysis. Multiple
log files are maintained based on severity levels.

Key features:
- JSON-formatted logs with structured fields
- Multiple log files (operations, debug, errors)
- Optional console output for development
- Log rotation to prevent disk space issues
- Consistent log entry format across all phases

Usage:
    from src.core.logger import setup_logging, get_logger
    
    # Initialize logging (call once at application start)
    setup_logging(config.logging)
    
    # Get a logger for your module
    logger = get_logger(__name__)
    
    # Log with context
    logger.info("Processing file", extra={
        "phase": "metadata_enrichment",
        "operation": "fetch_comicvine",
        "file_path": "/path/to/file.cbz",
        "metadata": {"series": "Batman", "issue": "1"}
    })
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler

from src.core.config import LoggingConfig

# ==============================================================================
# JSON FORMATTER FOR STRUCTURED LOGGING
# ==============================================================================

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs log records as JSON lines.
    
    Each log entry includes standard fields plus any extra context provided
    via the 'extra' parameter in log calls. This makes it easy to filter and
    analyze logs programmatically.
    
    Standard fields:
    - timestamp: ISO 8601 format
    - level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - logger: Logger name (usually module name)
    - message: Log message
    
    Optional context fields (via 'extra'):
    - phase: Current processing phase (e.g., "inventory", "metadata_enrichment")
    - operation: Specific operation being performed
    - file_path: Path to file being processed
    - metadata: Dictionary of metadata fields
    - error: Error details for exceptions
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string.
        
        Args:
            record: LogRecord to format
            
        Returns:
            JSON string representing the log entry
        """
        # Build base log entry with standard fields
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add optional context fields from 'extra' parameter
        # These fields are set by passing extra={...} to log calls
        context_fields = [
            "phase",
            "operation", 
            "file_path",
            "metadata",
            "error",
            "source_path",
            "target_path",
            "confidence",
            "reasoning",
            "status",
        ]
        
        for field in context_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Convert to JSON string (one line per log entry)
        return json.dumps(log_entry, default=str)

# ==============================================================================
# LOGGING SETUP AND ACCESS
# ==============================================================================

# Global flag to track if logging has been initialized
_logging_initialized = False

def setup_logging(config: LoggingConfig) -> None:
    """
    Initialize the logging system based on configuration.
    
    This should be called once at application startup before any logging occurs.
    It configures:
    - Root logger level
    - Multiple file handlers (operations, debug, errors)
    - Optional console handler
    - JSON formatting for all handlers
    - Log rotation settings
    
    The logging system creates separate files for different severity levels,
    making it easy to focus on specific types of issues. Timestamps in filenames
    allow multiple runs to maintain separate logs.
    
    Args:
        config: LoggingConfig object from application configuration
        
    Raises:
        OSError: If log directory cannot be created
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for log filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.level.upper()))
    
    # Remove any existing handlers (in case of reconfiguration)
    root_logger.handlers.clear()
    
    # Create formatter
    if config.json_format:
        formatter = JSONFormatter()
    else:
        # Fallback to standard format if JSON disabled
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Operations log (INFO and above)
    operations_log_path = config.operations_log.replace("{timestamp}", timestamp)
    operations_handler = RotatingFileHandler(
        operations_log_path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    operations_handler.setLevel(logging.INFO)
    operations_handler.setFormatter(formatter)
    root_logger.addHandler(operations_handler)
    
    # Debug log (DEBUG and above)
    debug_log_path = config.debug_log.replace("{timestamp}", timestamp)
    debug_handler = RotatingFileHandler(
        debug_log_path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    root_logger.addHandler(debug_handler)
    
    # Errors log (ERROR and above)
    errors_log_path = config.errors_log.replace("{timestamp}", timestamp)
    error_handler = RotatingFileHandler(
        errors_log_path,
        maxBytes=config.max_bytes,
        backupCount=config.backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    root_logger.addHandler(error_handler)
    
    # Console output (optional, for development)
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Use simpler formatting for console
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    _logging_initialized = True
    
    # Log that logging has been initialized
    init_logger = logging.getLogger(__name__)
    init_logger.info(
        "Logging system initialized",
        extra={
            "phase": "bootstrap",
            "operation": "logging_setup",
            "metadata": {
                "operations_log": operations_log_path,
                "debug_log": debug_log_path,
                "errors_log": errors_log_path,
                "level": config.level,
                "json_format": config.json_format,
            }
        }
    )

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module or component.
    
    This is the primary way to access logging throughout the application.
    Each module should get its own logger using __name__ as the parameter.
    
    Example:
        logger = get_logger(__name__)
        logger.info("Processing started", extra={"phase": "inventory"})
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        
    Returns:
        Logger instance configured with the application's logging setup
    """
    if not _logging_initialized:
        # If logging not initialized, set up basic config
        # This prevents errors if logging is accessed before setup
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s - %(name)s - %(message)s'
        )
        logging.warning(
            "Logging accessed before setup_logging() was called. "
            "Using basic configuration."
        )
    
    return logging.getLogger(name)

def log_operation(
    logger: logging.Logger,
    level: str,
    message: str,
    phase: str,
    operation: str,
    file_path: Optional[str] = None,
    **kwargs
) -> None:
    """
    Convenience function for logging operations with consistent structure.
    
    This helper ensures all operation logs include the required context fields
    (phase, operation) and makes it easier to maintain consistency.
    
    Args:
        logger: Logger instance
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        message: Log message
        phase: Current phase (e.g., "inventory", "metadata_enrichment")
        operation: Specific operation being performed
        file_path: Optional path to file being processed
        **kwargs: Additional context fields to include in log
    """
    log_level = getattr(logging, level.upper())
    
    extra = {
        "phase": phase,
        "operation": operation,
    }
    
    if file_path:
        extra["file_path"] = file_path
    
    # Add any additional context
    extra.update(kwargs)
    
    logger.log(log_level, message, extra=extra)

# ==============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON LOG PATTERNS
# ==============================================================================

def log_safety_check(
    logger: logging.Logger,
    check_name: str,
    passed: bool,
    details: Optional[str] = None
) -> None:
    """
    Log the result of a safety check.
    
    Args:
        logger: Logger instance
        check_name: Name of the safety check
        passed: Whether the check passed
        details: Optional additional details about the check
    """
    level = "INFO" if passed else "ERROR"
    status = "PASS" if passed else "FAIL"
    
    message = f"Safety check: {check_name} - {status}"
    if details:
        message += f" - {details}"
    
    log_operation(
        logger,
        level,
        message,
        phase="safety_checks",
        operation=check_name,
        status=status,
        details=details
    )

def log_file_operation(
    logger: logging.Logger,
    operation: str,
    source_path: str,
    target_path: Optional[str] = None,
    success: bool = True,
    error: Optional[str] = None
) -> None:
    """
    Log a file operation (copy, move, hash, etc.).
    
    Args:
        logger: Logger instance
        operation: Type of operation (e.g., "copy", "hash", "verify")
        source_path: Source file path
        target_path: Target file path (if applicable)
        success: Whether operation succeeded
        error: Error message if operation failed
    """
    level = "INFO" if success else "ERROR"
    status = "success" if success else "failed"
    
    message = f"File operation: {operation} - {status}"
    
    extra_fields = {
        "source_path": source_path,
        "status": status,
    }
    
    if target_path:
        extra_fields["target_path"] = target_path
    
    if error:
        extra_fields["error"] = error
    
    log_operation(
        logger,
        level,
        message,
        phase="file_operations",
        operation=operation,
        **extra_fields
    )
