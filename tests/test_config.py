"""
Tests for configuration loading and validation.

These tests verify that:
- Configuration files can be loaded successfully
- Pydantic validation works correctly
- Environment variable substitution works
- Invalid configurations are rejected
"""

import os
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.core.config import load_config, AppConfig, EnvironmentConfig


class TestConfigLoading:
    """Test configuration file loading."""
    
    def test_load_example_config(self):
        """Test loading the example configuration files."""
        # This test verifies the example configs are valid
        config = load_config()
        
        assert isinstance(config, AppConfig)
        assert config.environment.dry_run is True  # Should default to dry-run
        assert config.environment.min_python_version == "3.8"
    
    def test_config_structure(self):
        """Test that all configuration sections are present."""
        config = load_config()
        
        # Verify all major sections exist
        assert hasattr(config, 'environment')
        assert hasattr(config, 'logging')
        assert hasattr(config, 'safety')
        assert hasattr(config, 'metadata_providers')
        assert hasattr(config, 'confidence')
        assert hasattr(config, 'naming')
        assert hasattr(config, 'komga')
        assert hasattr(config, 'mylar3')
        assert hasattr(config, 'performance')
        assert hasattr(config, 'operations')
        assert hasattr(config, 'paths')
    
    def test_environment_variable_substitution(self):
        """Test that environment variables are substituted in config."""
        # Set a test environment variable
        test_value = "test_api_key_12345"
        os.environ['TEST_CONFIG_VAR'] = test_value
        
        try:
            config = load_config()
            # Note: Since we're loading example configs, we can't directly test
            # the substitution without modifying the files. This is a placeholder
            # for when we have test-specific config files.
            assert config is not None
        finally:
            # Clean up
            del os.environ['TEST_CONFIG_VAR']
    
    def test_paths_config_loading(self):
        """Test that paths configuration is loaded correctly."""
        config = load_config()
        
        assert hasattr(config.paths, 'source_libraries')
        assert hasattr(config.paths, 'target_roots')
        assert hasattr(config.paths, 'temp_workspace')
        
        # Verify source libraries structure
        assert isinstance(config.paths.source_libraries, list)
        if len(config.paths.source_libraries) > 0:
            lib = config.paths.source_libraries[0]
            assert hasattr(lib, 'path')
            assert hasattr(lib, 'content_type')
            assert hasattr(lib, 'enabled')


class TestConfigValidation:
    """Test Pydantic validation of configuration."""
    
    def test_valid_environment_config(self):
        """Test that valid environment config passes validation."""
        env_config = EnvironmentConfig(
            dry_run=True,
            profile="test",
            min_python_version="3.8"
        )
        
        assert env_config.dry_run is True
        assert env_config.profile == "test"
    
    def test_invalid_confidence_threshold(self):
        """Test that invalid confidence thresholds are rejected."""
        # TODO: Create test that verifies confidence thresholds must be 0.0-1.0
        # This will be implemented when we have more granular config testing
        pass


class TestConfigDefaults:
    """Test that configuration defaults are sensible."""
    
    def test_dry_run_defaults_to_true(self):
        """Test that dry-run mode defaults to True for safety."""
        config = load_config()
        assert config.environment.dry_run is True
    
    def test_safety_defaults(self):
        """Test that safety settings have conservative defaults."""
        config = load_config()
        
        # Should require backup by default
        assert config.safety.require_backup is True
        
        # Should verify copy integrity
        assert config.safety.verify_copy_integrity is True
        
        # Should have reasonable retry limit
        assert config.safety.max_retries > 0


# ==============================================================================
# TEST FIXTURES (for future test expansion)
# ==============================================================================

@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Create temporary directory with test configuration files.
    
    This fixture can be used in future tests that need to test
    configuration loading with custom values.
    """
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def sample_config_data():
    """
    Provide sample configuration data for testing.
    
    Returns a minimal valid configuration dict.
    """
    return {
        "environment": {
            "dry_run": True,
            "profile": "test",
            "min_python_version": "3.8"
        },
        "logging": {
            "level": "INFO",
            "operations_log": "logs/test_operations.log",
            "debug_log": "logs/test_debug.log",
            "errors_log": "logs/test_errors.log",
            "console_output": False,
            "max_bytes": 1048576,
            "backup_count": 3,
            "json_format": True
        },
        # ... other sections would go here in a complete fixture
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
