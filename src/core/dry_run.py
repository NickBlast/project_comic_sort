"""
Dry-run infrastructure for safe operation testing.

This module provides decorators and context managers that wrap file operations
to prevent actual execution in dry-run mode. Instead of performing operations,
they log what would have been done and return structured results.

This is the primary safety mechanism that allows users to preview all changes
before committing to them.

Usage:
    from src.core.dry_run import dry_run_operation
    from src.core.config import load_config
    
    config = load_config()
    
    @dry_run_operation(config)
    def copy_file(source, target):
        # This will only execute if config.environment.dry_run is False
        shutil.copy2(source, target)
        return {"success": True, "bytes_copied": 1024}
    
    result = copy_file("/path/to/source.cbz", "/path/to/target.cbz")
    # In dry-run mode: logs intent, returns mock result
    # In apply mode: executes copy, returns actual result
"""

import functools
from typing import Any, Callable, Dict, Optional, TypeVar, cast
from pathlib import Path
from dataclasses import dataclass, field

from src.core.config import AppConfig
from src.core.logger import get_logger

logger = get_logger(__name__)

# Type variable for generic decorator
F = TypeVar('F', bound=Callable[..., Any])

# ==============================================================================
# DRY-RUN RESULT DATA STRUCTURES
# ==============================================================================

@dataclass
class DryRunResult:
    """
    Result object returned when an operation is executed in dry-run mode.
    
    This provides a structured way to communicate what would have been done
    without actually doing it. Future phases can use this to generate accurate
    reports and validation checks.
    
    Attributes:
        operation: Name of the operation that was simulated
        would_execute: Whether this operation would have executed (always True for dry-run)
        parameters: Dictionary of parameters that would have been used
        estimated_result: What the result would likely have been
        log_message: Human-readable description of what would have happened
    """
    operation: str
    would_execute: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)
    estimated_result: Optional[Dict[str, Any]] = None
    log_message: str = ""

# ==============================================================================
# DRY-RUN DECORATOR
# ==============================================================================

def dry_run_operation(config: AppConfig) -> Callable[[F], F]:
    """
    Decorator that wraps file operations to respect dry-run mode.
    
    When dry-run mode is enabled in config, the decorated function will NOT
    execute. Instead, it will:
    1. Log what would have been done (with all parameters)
    2. Return a DryRunResult object with estimated outcome
    
    When dry-run mode is disabled (apply mode), the function executes normally.
    
    This decorator is the primary mechanism for ensuring safety. All file
    operations (copy, move, delete, modify) should be wrapped with this.
    
    Args:
        config: Application configuration containing dry_run flag
        
    Returns:
        Decorator function that can wrap operation functions
        
    Example:
        @dry_run_operation(config)
        def copy_file(source: Path, target: Path) -> Dict[str, Any]:
            shutil.copy2(source, target)
            return {"success": True, "size": source.stat().st_size}
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function name for logging
            operation_name = func.__name__
            
            # Build parameter description for logging
            # Convert Path objects to strings for better logging
            params = {}
            for i, arg in enumerate(args):
                if isinstance(arg, Path):
                    params[f"arg_{i}"] = str(arg)
                elif not isinstance(arg, (AppConfig,)):  # Skip config objects
                    params[f"arg_{i}"] = str(arg)
            
            for key, value in kwargs.items():
                if isinstance(value, Path):
                    params[key] = str(value)
                elif not isinstance(value, (AppConfig,)):
                    params[key] = str(value)
            
            if config.environment.dry_run:
                # DRY-RUN MODE: Log intent but don't execute
                log_message = f"DRY-RUN: Would execute {operation_name}"
                
                logger.info(
                    log_message,
                    extra={
                        "phase": "dry_run",
                        "operation": operation_name,
                        "metadata": {
                            "dry_run": True,
                            "parameters": params,
                        }
                    }
                )
                
                # Return a DryRunResult instead of executing
                return DryRunResult(
                    operation=operation_name,
                    would_execute=True,
                    parameters=params,
                    estimated_result={"simulated": True},
                    log_message=log_message
                )
            else:
                # APPLY MODE: Execute the actual operation
                logger.info(
                    f"APPLY MODE: Executing {operation_name}",
                    extra={
                        "phase": "apply",
                        "operation": operation_name,
                        "metadata": {
                            "dry_run": False,
                            "parameters": params,
                        }
                    }
                )
                
                try:
                    result = func(*args, **kwargs)
                    
                    logger.info(
                        f"Operation {operation_name} completed successfully",
                        extra={
                            "phase": "apply",
                            "operation": operation_name,
                            "status": "success",
                        }
                    )
                    
                    return result
                    
                except Exception as e:
                    logger.error(
                        f"Operation {operation_name} failed: {e}",
                        extra={
                            "phase": "apply",
                            "operation": operation_name,
                            "status": "failed",
                            "error": str(e),
                        },
                        exc_info=True
                    )
                    raise
        
        return cast(F, wrapper)
    
    return decorator

# ==============================================================================
# DRY-RUN CONTEXT MANAGER
# ==============================================================================

class DryRunContext:
    """
    Context manager for dry-run aware operations.
    
    This provides an alternative to the decorator for cases where you want
    to wrap multiple operations in a single dry-run check, or when you need
    more fine-grained control over dry-run behavior.
    
    Usage:
        with DryRunContext(config, "copy_files") as ctx:
            if ctx.should_execute:
                # Perform actual file operations
                shutil.copy2(source, target)
            else:
                # Log what would have been done
                ctx.log_would_do(f"Copy {source} to {target}")
    """
    
    def __init__(
        self,
        config: AppConfig,
        operation_name: str,
        phase: str = "operations"
    ):
        """
        Initialize dry-run context.
        
        Args:
            config: Application configuration
            operation_name: Name of the operation being performed
            phase: Processing phase (for logging)
        """
        self.config = config
        self.operation_name = operation_name
        self.phase = phase
        self.should_execute = not config.environment.dry_run
        self.actions_logged: list[str] = []
    
    def __enter__(self) -> "DryRunContext":
        """Enter the context."""
        if self.should_execute:
            logger.info(
                f"Starting operation: {self.operation_name} (APPLY MODE)",
                extra={
                    "phase": self.phase,
                    "operation": self.operation_name,
                    "dry_run": False,
                }
            )
        else:
            logger.info(
                f"Simulating operation: {self.operation_name} (DRY-RUN MODE)",
                extra={
                    "phase": self.phase,
                    "operation": self.operation_name,
                    "dry_run": True,
                }
            )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context."""
        if exc_type is None:
            # Successful completion
            if self.should_execute:
                logger.info(
                    f"Completed operation: {self.operation_name}",
                    extra={
                        "phase": self.phase,
                        "operation": self.operation_name,
                        "status": "success",
                    }
                )
            else:
                logger.info(
                    f"Dry-run simulation complete: {self.operation_name}",
                    extra={
                        "phase": self.phase,
                        "operation": self.operation_name,
                        "metadata": {
                            "actions_simulated": len(self.actions_logged),
                            "actions": self.actions_logged,
                        }
                    }
                )
        else:
            # Exception occurred
            logger.error(
                f"Operation failed: {self.operation_name} - {exc_val}",
                extra={
                    "phase": self.phase,
                    "operation": self.operation_name,
                    "status": "failed",
                    "error": str(exc_val),
                },
                exc_info=True
            )
        
        return False  # Don't suppress exceptions
    
    def log_would_do(self, action: str, **metadata: Any) -> None:
        """
        Log an action that would have been performed in apply mode.
        
        This should be called from the 'else' branch when should_execute is False.
        
        Args:
            action: Description of what would have been done
            **metadata: Additional metadata to include in log
        """
        self.actions_logged.append(action)
        
        logger.info(
            f"DRY-RUN: Would {action}",
            extra={
                "phase": self.phase,
                "operation": self.operation_name,
                "metadata": metadata,
            }
        )
    
    def log_did(self, action: str, **metadata: Any) -> None:
        """
        Log an action that was actually performed in apply mode.
        
        This should be called from the 'if' branch when should_execute is True.
        
        Args:
            action: Description of what was done
            **metadata: Additional metadata to include in log
        """
        logger.info(
            f"APPLY: {action}",
            extra={
                "phase": self.phase,
                "operation": self.operation_name,
                "metadata": metadata,
            }
        )

# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def is_dry_run(config: AppConfig) -> bool:
    """
    Simple check if dry-run mode is enabled.
    
    This is a convenience function for quick checks in code.
    
    Args:
        config: Application configuration
        
    Returns:
        True if in dry-run mode, False if in apply mode
    """
    return config.environment.dry_run

def require_apply_mode(config: AppConfig, operation_name: str) -> None:
    """
    Raise an error if not in apply mode.
    
    This should be called at the start of operations that absolutely cannot
    run in dry-run mode (e.g., database modifications, external API calls
    with side effects).
    
    Args:
        config: Application configuration
        operation_name: Name of the operation that requires apply mode
        
    Raises:
        RuntimeError: If in dry-run mode
    """
    if config.environment.dry_run:
        error_msg = (
            f"Operation '{operation_name}' cannot be executed in dry-run mode. "
            f"Set environment.dry_run to false in configuration to proceed."
        )
        logger.error(
            error_msg,
            extra={
                "phase": "validation",
                "operation": operation_name,
                "error": "dry_run_not_allowed",
            }
        )
        raise RuntimeError(error_msg)
