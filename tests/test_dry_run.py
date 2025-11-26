"""
Tests for dry-run infrastructure.

These tests verify that:
- Dry-run decorator prevents execution in dry-run mode
- Operations execute normally in apply mode
- DryRunContext works correctly
- DryRunResult is returned appropriately
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from src.core.config import AppConfig, EnvironmentConfig
from src.core.dry_run import (
    dry_run_operation,
    DryRunContext,
    DryRunResult,
    is_dry_run,
    require_apply_mode
)

class TestDryRunDecorator:
    """Test the dry_run_operation decorator."""
    
    def test_decorator_prevents_execution_in_dry_run_mode(self):
        """Test that decorated function doesn't execute in dry-run mode."""
        # Create config with dry_run=True
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = True
        
        # Create a mock function that should NOT be called
        mock_func = Mock(return_value={"executed": True})
        
        # Decorate it
        @dry_run_operation(config)
        def test_func():
            return mock_func()
        
        # Call the decorated function
        result = test_func()
        
        # Function should NOT have been called
        mock_func.assert_not_called()
        
        # Should return DryRunResult instead
        assert isinstance(result, DryRunResult)
        assert result.would_execute is True
    
    def test_decorator_allows_execution_in_apply_mode(self):
        """Test that decorated function executes in apply mode."""
        # Create config with dry_run=False
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = False
        
        # Create a mock function that SHOULD be called
        expected_return = {"executed": True}
        mock_func = Mock(return_value=expected_return)
        
        # Decorate it
        @dry_run_operation(config)
        def test_func():
            return mock_func()
        
        # Call the decorated function
        result = test_func()
        
        # Function SHOULD have been called
        mock_func.assert_called_once()
        
        # Should return actual result
        assert result == expected_return

class TestDryRunContext:
    """Test the DryRunContext context manager."""
    
    def test_context_should_execute_in_apply_mode(self):
        """Test that should_execute is True in apply mode."""
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = False
        
        with DryRunContext(config, "test_operation") as ctx:
            assert ctx.should_execute is True
    
    def test_context_should_not_execute_in_dry_run_mode(self):
        """Test that should_execute is False in dry-run mode."""
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = True
        
        with DryRunContext(config, "test_operation") as ctx:
            assert ctx.should_execute is False

class TestDryRunHelpers:
    """Test dry-run helper functions."""
    
    def test_is_dry_run_returns_true_when_enabled(self):
        """Test is_dry_run() returns True when dry-run is enabled."""
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = True
        
        assert is_dry_run(config) is True
    
    def test_is_dry_run_returns_false_when_disabled(self):
        """Test is_dry_run() returns False when dry-run is disabled."""
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = False
        
        assert is_dry_run(config) is False
    
    def test_require_apply_mode_raises_in_dry_run(self):
        """Test that require_apply_mode() raises error in dry-run mode."""
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = True
        
        with pytest.raises(RuntimeError, match="cannot be executed in dry-run mode"):
            require_apply_mode(config, "test_operation")
    
    def test_require_apply_mode_passes_in_apply_mode(self):
        """Test that require_apply_mode() doesn't raise in apply mode."""
        config = Mock(spec=AppConfig)
        config.environment = Mock(spec=EnvironmentConfig)
        config.environment.dry_run = False
        
        # Should not raise
        require_apply_mode(config, "test_operation")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
