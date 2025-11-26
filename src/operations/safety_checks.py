"""
Environment safety checks module.

This module validates the execution environment before any file operations.
It ensures that source paths exist, target paths are writable, sufficient
disk space is available, and there are no dangerous path overlaps.

These checks are critical for preventing data loss and system issues. All
checks must pass before proceeding with migration operations.

Usage:
    from src.operations.safety_checks import run_safety_checks
    
    passed, issues = run_safety_checks(config)
    if not passed:
        for issue in issues:
            print(f"FAIL: {issue}")
        sys.exit(1)
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass

from src.core.config import AppConfig
from src.core.logger import get_logger, log_safety_check

logger = get_logger(__name__)

# ==============================================================================
# SAFETY CHECK RESULT DATA STRUCTURES
# ==============================================================================

@dataclass
class SafetyCheckResult:
    """
    Result of an individual safety check.
    
    Attributes:
        check_name: Name of the safety check
        passed: Whether the check passed
        message: Human-readable description of the result
        details: Additional structured details about the check
        critical: Whether failure of this check should block execution
    """
    check_name: str
    passed: bool
    message: str
    details: Dict[str, Any]
    critical: bool = True

# ==============================================================================
# INDIVIDUAL SAFETY CHECK FUNCTIONS
# ==============================================================================

def check_python_version(config: AppConfig) -> SafetyCheckResult:
    """
    Verify that Python version meets minimum requirements.
    
    This check ensures compatibility with language features and libraries
    used throughout the application.
    
    Args:
        config: Application configuration
        
    Returns:
        SafetyCheckResult indicating whether Python version is sufficient
    """
    current_version = sys.version_info
    min_version_str = config.environment.min_python_version
    min_version_parts = min_version_str.split('.')
    min_version = (int(min_version_parts[0]), int(min_version_parts[1]))
    
    current_version_str = f"{current_version.major}.{current_version.minor}.{current_version.micro}"
    passed = (current_version.major, current_version.minor) >= min_version
    
    result = SafetyCheckResult(
        check_name="python_version",
        passed=passed,
        message=f"Python {current_version_str} (minimum: {min_version_str})",
        details={
            "current_version": current_version_str,
            "min_version": min_version_str,
        },
        critical=True
    )
    
    log_safety_check(logger, "python_version", passed, result.message)
    return result

def check_source_libraries_exist(config: AppConfig) -> SafetyCheckResult:
    """
    Verify that all enabled source library paths exist and are readable.
    
    Source paths must exist before we can scan them for files. This check
    also verifies read permissions to prevent failures during scanning.
    
    Args:
        config: Application configuration
        
    Returns:
        SafetyCheckResult indicating whether all source paths are accessible
    """
    issues = []
    accessible_count = 0
    total_enabled = 0
    
    for source_lib in config.paths.source_libraries:
        if not source_lib.enabled:
            continue
            
        total_enabled += 1
        source_path = Path(source_lib.path)
        
        if not source_path.exists():
            issues.append(f"Path does not exist: {source_path}")
        elif not source_path.is_dir():
            issues.append(f"Path is not a directory: {source_path}")
        elif not os.access(source_path, os.R_OK):
            issues.append(f"Path is not readable: {source_path}")
        else:
            accessible_count += 1
    
    passed = len(issues) == 0
    
    result = SafetyCheckResult(
        check_name="source_libraries_exist",
        passed=passed,
        message=f"{accessible_count}/{total_enabled} source libraries accessible",
        details={
            "accessible": accessible_count,
            "total": total_enabled,
            "issues": issues,
        },
        critical=True
    )
    
    log_safety_check(logger, "source_libraries_exist", passed, result.message)
    return result

def check_target_paths_writable(config: AppConfig) -> SafetyCheckResult:
    """
    Verify that target root paths exist (or can be created) and are writable.
    
    Target paths need write permission for creating organized library structure.
    If paths don't exist, we attempt to create them (dry-run check only, no
    actual creation in this function).
    
    Args:
        config: Application configuration
        
    Returns:
        SafetyCheckResult indicating whether targets are writable
    """
    issues = []
    writable_count = 0
    
    target_paths = [
        ("western", config.paths.target_roots.western),
        ("manga", config.paths.target_roots.manga),
        ("hentai", config.paths.target_roots.hentai),
    ]
    
    for content_type, target_path_str in target_paths:
        target_path = Path(target_path_str)
        
        if target_path.exists():
            # Path exists - check if it's a directory and writable
            if not target_path.is_dir():
                issues.append(f"{content_type} target is not a directory: {target_path}")
            elif not os.access(target_path, os.W_OK):
                issues.append(f"{content_type} target is not writable: {target_path}")
            else:
                writable_count += 1
        else:
            # Path doesn't exist - check if parent is writable (can create)
            parent = target_path.parent
            if not parent.exists():
                issues.append(
                    f"{content_type} target parent does not exist: {parent}. "
                    f"Cannot create {target_path}"
                )
            elif not os.access(parent, os.W_OK):
                issues.append(
                    f"{content_type} target parent is not writable: {parent}. "
                    f"Cannot create {target_path}"
                )
            else:
                # Parent is writable, we can create target path when needed
                writable_count += 1
    
    passed = len(issues) == 0
    
    result = SafetyCheckResult(
        check_name="target_paths_writable",
        passed=passed,
        message=f"{writable_count}/{len(target_paths)} target roots writable/creatable",
        details={
            "writable": writable_count,
            "total": len(target_paths),
            "issues": issues,
        },
        critical=True
    )
    
    log_safety_check(logger, "target_paths_writable", passed, result.message)
    return result

def check_no_path_overlaps(config: AppConfig) -> SafetyCheckResult:
    """
    Verify that source and target paths don't overlap dangerously.
    
    Overlapping paths can cause:
    - Source files being overwritten during migration
    - Infinite loops during directory scanning
    - Data loss if source is subdirectory of target
    
    This check prevents these dangerous scenarios.
    
    Args:
        config: Application configuration
        
    Returns:
        SafetyCheckResult indicating whether paths are safely separated
    """
    issues = []
    
    # Collect all paths to check
    source_paths = [
        Path(lib.path).resolve()
        for lib in config.paths.source_libraries
        if lib.enabled
    ]
    
    target_paths = [
        Path(config.paths.target_roots.western).resolve(),
        Path(config.paths.target_roots.manga).resolve(),
        Path(config.paths.target_roots.hentai).resolve(),
    ]
    
    # Check if any source is a parent or child of any target
    for source in source_paths:
        for target in target_paths:
            # Check if source is parent of target
            try:
                target.relative_to(source)
                issues.append(
                    f"Target {target} is inside source {source}. "
                    f"This would cause files to be copied into themselves."
                )
            except ValueError:
                pass  # Not a child, this is good
            
            # Check if target is parent of source
            try:
                source.relative_to(target)
                issues.append(
                    f"Source {source} is inside target {target}. "
                    f"This could cause source files to be overwritten."
                )
            except ValueError:
                pass  # Not a child, this is good
    
    # Also check sources don't overlap with each other
    for i, source1 in enumerate(source_paths):
        for source2 in source_paths[i+1:]:
            try:
                source2.relative_to(source1)
                issues.append(
                    f"Source {source2} is inside source {source1}. "
                    f"This may cause duplicate processing."
                )
            except ValueError:
                pass
            
            try:
                source1.relative_to(source2)
                issues.append(
                    f"Source {source1} is inside source {source2}. "
                    f"This may cause duplicate processing."
                )
            except ValueError:
                pass
    
    passed = len(issues) == 0
    
    result = SafetyCheckResult(
        check_name="no_path_overlaps",
        passed=passed,
        message="No dangerous path overlaps detected" if passed else f"{len(issues)} path overlaps found",
        details={
            "issues": issues,
        },
        critical=True
    )
    
    log_safety_check(logger, "no_path_overlaps", passed, result.message)
    return result

def check_disk_space(config: AppConfig) -> SafetyCheckResult:
    """
    Verify sufficient free disk space on target filesystems.
    
    This is a rough estimate check - we check that minimum free space is
    available on each target root. For more accurate space estimation,
    Phase 1 inventory will calculate actual source size.
    
    Args:
        config: Application configuration
        
    Returns:
        SafetyCheckResult indicating whether disk space is sufficient
    """
    issues = []
    min_free_bytes = config.safety.min_free_space_bytes
    
    # Check each target root
    target_paths = {
        "western": config.paths.target_roots.western,
        "manga": config.paths.target_roots.manga,
        "hentai": config.paths.target_roots.hentai,
    }
    
    checked_filesystems = set()
    
    for content_type, target_path_str in target_paths.items():
        target_path = Path(target_path_str)
        
        # Use parent if target doesn't exist yet
        check_path = target_path if target_path.exists() else target_path.parent
        
        # Resolve to absolute path to handle symlinks
        try:
            check_path = check_path.resolve()
        except (OSError, RuntimeError):
            issues.append(f"Cannot resolve path for {content_type}: {check_path}")
            continue
        
        # Skip if we already checked this filesystem
        # (multiple targets may be on same filesystem)
        if check_path in checked_filesystems:
            continue
        checked_filesystems.add(check_path)
        
        try:
            usage = shutil.disk_usage(check_path)
            free_gb = usage.free / (1024**3)
            min_gb = min_free_bytes / (1024**3)
            
            if usage.free < min_free_bytes:
                issues.append(
                    f"{content_type} target has insufficient space: "
                    f"{free_gb:.2f}GB free (minimum: {min_gb:.2f}GB) at {check_path}"
                )
        except (OSError, PermissionError) as e:
            issues.append(f"Cannot check disk space for {content_type}: {e}")
    
    passed = len(issues) == 0
    
    result = SafetyCheckResult(
        check_name="disk_space",
        passed=passed,
        message="Sufficient disk space available" if passed else f"{len(issues)} space issues found",
        details={
            "min_free_gb": min_free_bytes / (1024**3),
            "issues": issues,
        },
        critical=True
    )
    
    log_safety_check(logger, "disk_space", passed, result.message)
    return result

def check_temp_workspace(config: AppConfig) -> SafetyCheckResult:
    """
    Verify temporary workspace path is accessible.
    
    The temp workspace is used for intermediate processing. It should be
    on fast storage (SSD preferred) with sufficient space.
    
    Args:
        config: Application configuration
        
    Returns:
        SafetyCheckResult indicating whether temp workspace is usable
    """
    temp_path = Path(config.paths.temp_workspace)
    issues = []
    
    if temp_path.exists():
        if not temp_path.is_dir():
            issues.append(f"Temp workspace is not a directory: {temp_path}")
        elif not os.access(temp_path, os.W_OK):
            issues.append(f"Temp workspace is not writable: {temp_path}")
    else:
        # Check if we can create it
        parent = temp_path.parent
        if not parent.exists():
            issues.append(f"Temp workspace parent does not exist: {parent}")
        elif not os.access(parent, os.W_OK):
            issues.append(f"Temp workspace parent is not writable: {parent}")
    
    passed = len(issues) == 0
    
    result = SafetyCheckResult(
        check_name="temp_workspace",
        passed=passed,
        message="Temp workspace accessible" if passed else f"{len(issues)} issues found",
        details={
            "temp_workspace": str(temp_path),
            "issues": issues,
        },
        critical=False  # Non-critical, can work without temp workspace
    )
    
    log_safety_check(logger, "temp_workspace", passed, result.message)
    return result

# ==============================================================================
# MAIN SAFETY CHECK RUNNER
# ==============================================================================

def run_safety_checks(config: AppConfig) -> Tuple[bool, List[SafetyCheckResult]]:
    """
    Run all safety checks and return overall pass/fail status.
    
    This function coordinates all individual safety checks and aggregates
    their results. It logs the outcome of each check and provides a summary.
    
    All critical checks must pass for overall success. Non-critical checks
    are informational and don't block execution.
    
    Args:
        config: Application configuration
        
    Returns:
        Tuple of (all_critical_passed, list_of_all_results)
    """
    logger.info(
        "Starting safety checks",
        extra={
            "phase": "safety_checks",
            "operation": "run_all_checks",
        }
    )
    
    # Run all checks
    results = [
        check_python_version(config),
        check_source_libraries_exist(config),
        check_target_paths_writable(config),
        check_no_path_overlaps(config),
        check_disk_space(config),
        check_temp_workspace(config),
    ]
    
    # Determine overall pass/fail
    critical_results = [r for r in results if r.critical]
    all_critical_passed = all(r.passed for r in critical_results)
    
    # Count results
    total_checks = len(results)
    passed_checks = sum(1 for r in results if r.passed)
    critical_failed = sum(1 for r in critical_results if not r.passed)
    
    # Log summary
    summary_level = "INFO" if all_critical_passed else "ERROR"
    logger.log(
        getattr(logger, summary_level.lower()).__self__.level,
        f"Safety checks complete: {passed_checks}/{total_checks} passed",
        extra={
            "phase": "safety_checks",
            "operation": "summary",
            "metadata": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": total_checks - passed_checks,
                "critical_failed": critical_failed,
                "overall_passed": all_critical_passed,
            }
        }
    )
    
    return all_critical_passed, results

def print_safety_check_results(results: List[SafetyCheckResult]) -> None:
    """
    Print human-readable safety check results to console.
    
    This provides a clear summary for users reviewing the checks before
    proceeding with operations.
    
    Args:
        results: List of SafetyCheckResult objects
    """
    print("\n" + "="*70)
    print("SAFETY CHECK RESULTS")
    print("="*70)
    
    for result in results:
        status_symbol = "✓" if result.passed else "✗"
        status_text = "PASS" if result.passed else "FAIL"
        critical_marker = " [CRITICAL]" if result.critical else ""
        
        print(f"\n{status_symbol} {result.check_name.upper()}: {status_text}{critical_marker}")
        print(f"  {result.message}")
        
        if not result.passed and result.details.get("issues"):
            for issue in result.details["issues"]:
                print(f"    - {issue}")
    
    print("\n" + "="*70)
    
    critical_failed = sum(1 for r in results if r.critical and not r.passed)
    if critical_failed > 0:
        print(f"❌ {critical_failed} CRITICAL CHECKS FAILED - CANNOT PROCEED")
    else:
        print("✅ ALL CRITICAL CHECKS PASSED")
    print("="*70 + "\n")
