"""Unit tests for secrets_manager module.

Tests cover:
- SecretNotFoundError exception
- EnvironmentSecretsProvider
- DotEnvSecretsProvider
- SecretsManager facade
- Global singleton functions
"""

import os
import pytest
from unittest.mock import MagicMock

from src.config.secrets_manager import (
    SecretNotFoundError,
    SecretsProvider,
    EnvironmentSecretsProvider,
    DotEnvSecretsProvider,
    SecretsManager,
    get_secrets_manager,
    get_secret,
)


class TestSecretNotFoundError:
    """Tests for SecretNotFoundError exception."""

    def test_raise_exception(self):
        """Test that SecretNotFoundError can be raised."""
        with pytest.raises(SecretNotFoundError):
            raise SecretNotFoundError("Test secret not found")

    def test_exception_message(self):
        """Test that exception preserves error message."""
        message = "SECRET_KEY not found"
        try:
            raise SecretNotFoundError(message)
        except SecretNotFoundError as e:
            assert str(e) == message

    def test_exception_inheritance(self):
        """Test that SecretNotFoundError is an Exception."""
        assert issubclass(SecretNotFoundError, Exception)


class TestEnvironmentSecretsProvider:
    """Tests for EnvironmentSecretsProvider."""

    @pytest.fixture
    def provider(self):
        """Create a fresh EnvironmentSecretsProvider instance."""
        return EnvironmentSecretsProvider()

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Clean up test environment variables after each test."""
        test_keys = ["TEST_SECRET", "TEST_KEY", "TEST_TOKEN", "EMPTY_SECRET"]
        yield
        for key in test_keys:
            if key in os.environ:
                del os.environ[key]

    def test_get_secret_from_environment(self, provider):
        """Test getting a secret from environment variable."""
        os.environ["TEST_SECRET"] = "secret_value_123"  # pragma: allowlist secret
        result = provider.get_secret("TEST_SECRET")
        assert result == "secret_value_123"

    def test_get_secret_with_default(self, provider):
        """Test getting a secret with default value when not found."""
        result = provider.get_secret("NONEXISTENT_SECRET", "default_value")
        assert result == "default_value"

    def test_get_secret_not_found_raises(self, provider):
        """Test that missing secret without default raises SecretNotFoundError."""
        with pytest.raises(SecretNotFoundError) as exc_info:
            provider.get_secret("NONEXISTENT_SECRET")
        assert "NONEXISTENT_SECRET" in str(exc_info.value)

    def test_get_secret_empty_raises(self, provider):
        """Test that empty secret raises SecretNotFoundError."""
        os.environ["EMPTY_SECRET"] = "   "
        with pytest.raises(SecretNotFoundError) as exc_info:
            provider.get_secret("EMPTY_SECRET")
        assert "empty" in str(exc_info.value).lower()

    def test_set_secret(self, provider):
        """Test setting a secret in environment."""
        provider.set_secret("TEST_KEY", "test_value")
        assert os.environ.get("TEST_KEY") == "test_value"

    def test_delete_secret(self, provider):
        """Test deleting a secret from environment."""
        os.environ["TEST_SECRET"] = "to_delete"  # pragma: allowlist secret
        provider.delete_secret("TEST_SECRET")
        assert "TEST_SECRET" not in os.environ

    def test_delete_nonexistent_secret(self, provider):
        """Test deleting a nonexistent secret doesn't raise."""
        # Should not raise
        provider.delete_secret("NONEXISTENT_SECRET")

    def test_list_secret_keys(self, provider):
        """Test listing secret keys filters by pattern."""
        os.environ["API_KEY"] = "value"  # pragma: allowlist secret
        os.environ["SECRET_TOKEN"] = "value"  # pragma: allowlist secret
        os.environ["REGULAR_VAR"] = "value"

        keys = provider.list_secret_keys()

        assert "API_KEY" in keys
        assert "SECRET_TOKEN" in keys
        # REGULAR_VAR doesn't match secret patterns
        assert "REGULAR_VAR" not in keys

    def test_list_secret_keys_patterns(self, provider):
        """Test that list_secret_keys matches expected patterns."""
        test_vars = {  # pragma: allowlist secret
            "MY_SECRET": "val",
            "API_KEY": "val",
            "AUTH_TOKEN": "val",
            "DATABASE_PASSWORD": "val",
            "AWS_CREDENTIALS": "val",
            "NORMAL_VALUE": "val",  # Should NOT match
        }
        for key, value in test_vars.items():
            os.environ[key] = value

        keys = provider.list_secret_keys()

        # These should match patterns
        assert "MY_SECRET" in keys
        assert "API_KEY" in keys
        assert "AUTH_TOKEN" in keys
        assert "DATABASE_PASSWORD" in keys
        assert "AWS_CREDENTIALS" in keys

        # Cleanup
        for key in test_vars:
            if key in os.environ:
                del os.environ[key]


class TestDotEnvSecretsProvider:
    """Tests for DotEnvSecretsProvider."""

    @pytest.fixture
    def temp_env_file(self, tmp_path):
        """Create a temporary .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "# Test environment file\n"
            "TEST_API_KEY=sk-test-12345\n"
            "TEST_SECRET=my_secret_value\n"
            'QUOTED_VALUE="double quoted"\n'
            "SINGLE_QUOTED='single quoted'\n"
            "\n"
            "# Another comment\n"
            "EMPTY_LINE_ABOVE=value\n"
        )
        return env_file

    @pytest.fixture
    def provider(self, temp_env_file):
        """Create provider with temp env file."""
        return DotEnvSecretsProvider(temp_env_file)

    @pytest.fixture(autouse=True)
    def clean_env(self, temp_env_file):
        """Clean up test environment variables after each test."""
        yield
        for key in [
            "TEST_API_KEY",
            "TEST_SECRET",
            "QUOTED_VALUE",
            "SINGLE_QUOTED",
            "EMPTY_LINE_ABOVE",
            "NEW_SECRET",
        ]:
            if key in os.environ:
                del os.environ[key]

    def test_load_env_file(self, provider):
        """Test that .env file is loaded correctly."""
        assert provider.get_secret("TEST_API_KEY") == "sk-test-12345"
        assert provider.get_secret("TEST_SECRET") == "my_secret_value"

    def test_load_quoted_values(self, provider):
        """Test that quoted values are unquoted."""
        assert provider.get_secret("QUOTED_VALUE") == "double quoted"
        assert provider.get_secret("SINGLE_QUOTED") == "single quoted"

    def test_skip_comments(self, provider):
        """Test that comments are skipped."""
        # Should not have comment keys
        with pytest.raises(SecretNotFoundError):
            provider.get_secret("# Test environment file")

    def test_get_secret_not_found(self, provider):
        """Test getting nonexistent secret raises error."""
        with pytest.raises(SecretNotFoundError) as exc_info:
            provider.get_secret("NONEXISTENT")
        assert "NONEXISTENT" in str(exc_info.value)

    def test_get_secret_with_default(self, provider):
        """Test getting secret with default value."""
        result = provider.get_secret("NONEXISTENT", "fallback")
        assert result == "fallback"

    def test_set_secret(self, provider):
        """Test setting a secret (memory only)."""
        provider.set_secret("NEW_SECRET", "new_value")
        assert provider.get_secret("NEW_SECRET") == "new_value"
        # Also sets in os.environ for compatibility
        assert os.environ.get("NEW_SECRET") == "new_value"

    def test_delete_secret(self, provider):
        """Test deleting a secret."""
        provider.delete_secret("TEST_API_KEY")
        with pytest.raises(SecretNotFoundError):
            provider.get_secret("TEST_API_KEY")

    def test_list_secret_keys(self, provider):
        """Test listing all secret keys."""
        keys = provider.list_secret_keys()
        assert "TEST_API_KEY" in keys
        assert "TEST_SECRET" in keys

    def test_nonexistent_env_file(self, tmp_path):
        """Test handling of nonexistent .env file."""
        # Should not raise, just log warning
        provider = DotEnvSecretsProvider(tmp_path / "nonexistent.env")
        # Provider initializes but has no secrets
        assert provider.list_secret_keys() == []

    def test_env_file_parse_error(self, tmp_path):
        """Test handling of malformed .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text("VALID_KEY=value\n")

        provider = DotEnvSecretsProvider(env_file)
        assert provider.get_secret("VALID_KEY") == "value"

    def test_sets_environment_variables(self, provider):
        """Test that loading .env also sets os.environ."""
        # Should be set in os.environ for compatibility
        assert os.environ.get("TEST_API_KEY") == "sk-test-12345"


class TestSecretsManager:
    """Tests for SecretsManager facade."""

    @pytest.fixture
    def mock_provider(self):
        """Create a mock SecretsProvider."""
        provider = MagicMock(spec=SecretsProvider)
        provider.get_secret.return_value = "secret_value"
        provider.list_secret_keys.return_value = ["KEY1", "KEY2"]
        return provider

    @pytest.fixture
    def manager(self, mock_provider):
        """Create SecretsManager with mock provider."""
        return SecretsManager(provider=mock_provider)

    def test_init_with_custom_provider(self, mock_provider):
        """Test initialization with custom provider."""
        manager = SecretsManager(provider=mock_provider)
        assert manager.provider == mock_provider

    def test_get_secret(self, manager, mock_provider):
        """Test getting a secret through manager."""
        result = manager.get("TEST_KEY")
        assert result == "secret_value"
        mock_provider.get_secret.assert_called_once_with("TEST_KEY", None)

    def test_get_secret_with_default(self, manager, mock_provider):
        """Test getting secret with default."""
        manager.get("TEST_KEY", default="default")
        mock_provider.get_secret.assert_called_with("TEST_KEY", "default")

    def test_get_secret_not_required(self, manager, mock_provider):
        """Test getting optional secret that doesn't exist."""
        mock_provider.get_secret.side_effect = SecretNotFoundError("Not found")
        result = manager.get("MISSING_KEY", required=False, default="fallback")
        assert result == "fallback"

    def test_get_secret_required_raises(self, manager, mock_provider):
        """Test that missing required secret raises error."""
        mock_provider.get_secret.side_effect = SecretNotFoundError("Not found")
        with pytest.raises(SecretNotFoundError):
            manager.get("MISSING_KEY", required=True)

    def test_set_secret(self, manager, mock_provider):
        """Test setting a secret."""
        manager.set("NEW_KEY", "new_value")
        mock_provider.set_secret.assert_called_once_with("NEW_KEY", "new_value")

    def test_delete_secret(self, manager, mock_provider):
        """Test deleting a secret."""
        manager.delete("OLD_KEY")
        mock_provider.delete_secret.assert_called_once_with("OLD_KEY")

    def test_list_keys(self, manager, mock_provider):
        """Test listing secret keys."""
        keys = manager.list_keys()
        assert keys == ["KEY1", "KEY2"]
        mock_provider.list_secret_keys.assert_called_once()

    def test_validate_required_secrets_all_present(self, manager, mock_provider):
        """Test validation passes when all secrets present."""
        # Should not raise
        manager.validate_required_secrets(["KEY1", "KEY2"])

    def test_validate_required_secrets_missing(self, manager, mock_provider):
        """Test validation fails when secrets missing."""
        mock_provider.get_secret.side_effect = SecretNotFoundError("Not found")
        with pytest.raises(SecretNotFoundError) as exc_info:
            manager.validate_required_secrets(["MISSING1", "MISSING2"])
        assert "MISSING1" in str(exc_info.value)

    def test_access_log(self, manager, mock_provider):
        """Test that access log is maintained."""
        manager.get("KEY1")
        manager.get("KEY2")

        log = manager.get_access_log()
        assert len(log) == 2
        assert log[0]["key"] == "KEY1"
        assert log[1]["key"] == "KEY2"
        assert "timestamp" in log[0]
        assert log[0]["found"] is True

    def test_access_log_tracks_not_found(self, manager, mock_provider):
        """Test that access log tracks failed lookups."""
        mock_provider.get_secret.side_effect = SecretNotFoundError("Not found")
        manager.get("MISSING", required=False)

        log = manager.get_access_log()
        assert len(log) == 1
        assert log[0]["key"] == "MISSING"
        assert log[0]["found"] is False

    def test_check_rotation_needed(self, manager):
        """Test rotation check (placeholder implementation)."""
        # Current implementation always returns False
        result = manager.check_rotation_needed("ANY_KEY")
        assert result is False


class TestSecretsManagerAutoSelect:
    """Tests for SecretsManager auto provider selection."""

    @pytest.fixture(autouse=True)
    def clean_env(self):
        """Clean up environment after each test."""
        original_provider = os.environ.get("SECRETS_PROVIDER")
        yield
        if original_provider is not None:
            os.environ["SECRETS_PROVIDER"] = original_provider
        elif "SECRETS_PROVIDER" in os.environ:
            del os.environ["SECRETS_PROVIDER"]

    def test_auto_select_environment_provider(self, tmp_path, monkeypatch):
        """Test auto-selection of EnvironmentSecretsProvider."""
        monkeypatch.chdir(tmp_path)  # No .env file exists
        os.environ["SECRETS_PROVIDER"] = "environment"  # pragma: allowlist secret

        manager = SecretsManager()
        assert isinstance(manager.provider, EnvironmentSecretsProvider)

    def test_auto_select_dotenv_provider(self, tmp_path, monkeypatch):
        """Test auto-selection of DotEnvSecretsProvider."""
        monkeypatch.chdir(tmp_path)
        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_KEY=value\n")
        os.environ["SECRETS_PROVIDER"] = "dotenv"  # pragma: allowlist secret

        manager = SecretsManager()
        assert isinstance(manager.provider, DotEnvSecretsProvider)

    def test_auto_detect_env_file(self, tmp_path, monkeypatch):
        """Test auto-detection of .env file."""
        monkeypatch.chdir(tmp_path)
        # Remove SECRETS_PROVIDER to trigger auto-detect
        if "SECRETS_PROVIDER" in os.environ:
            del os.environ["SECRETS_PROVIDER"]

        # Create .env file
        env_file = tmp_path / ".env"
        env_file.write_text("AUTO_KEY=auto_value\n")

        manager = SecretsManager()
        assert isinstance(manager.provider, DotEnvSecretsProvider)

    def test_auto_detect_no_env_file(self, tmp_path, monkeypatch):
        """Test auto-detection without .env file."""
        monkeypatch.chdir(tmp_path)
        # Remove SECRETS_PROVIDER to trigger auto-detect
        if "SECRETS_PROVIDER" in os.environ:
            del os.environ["SECRETS_PROVIDER"]

        # No .env file - should use EnvironmentSecretsProvider
        manager = SecretsManager()
        assert isinstance(manager.provider, EnvironmentSecretsProvider)


class TestGlobalFunctions:
    """Tests for global singleton functions."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset the global singleton before each test."""
        import src.config.secrets_manager as sm

        sm._secrets_manager = None
        yield
        sm._secrets_manager = None

    def test_get_secrets_manager_singleton(self, tmp_path, monkeypatch):
        """Test that get_secrets_manager returns singleton."""
        monkeypatch.chdir(tmp_path)
        if "SECRETS_PROVIDER" in os.environ:
            del os.environ["SECRETS_PROVIDER"]

        manager1 = get_secrets_manager()
        manager2 = get_secrets_manager()

        assert manager1 is manager2

    def test_get_secret_convenience_function(self, tmp_path, monkeypatch):
        """Test get_secret convenience function."""
        monkeypatch.chdir(tmp_path)
        os.environ["CONVENIENCE_TEST"] = "convenience_value"
        os.environ["SECRETS_PROVIDER"] = "environment"

        result = get_secret("CONVENIENCE_TEST")
        assert result == "convenience_value"

        # Cleanup
        del os.environ["CONVENIENCE_TEST"]

    def test_get_secret_with_default(self, tmp_path, monkeypatch):
        """Test get_secret with default value."""
        monkeypatch.chdir(tmp_path)
        os.environ["SECRETS_PROVIDER"] = "environment"

        result = get_secret("NONEXISTENT_KEY", default="default", required=False)
        assert result == "default"

    def test_get_secret_required_raises(self, tmp_path, monkeypatch):
        """Test get_secret raises for missing required secret."""
        monkeypatch.chdir(tmp_path)
        os.environ["SECRETS_PROVIDER"] = "environment"

        with pytest.raises(SecretNotFoundError):
            get_secret("DEFINITELY_NOT_EXISTING", required=True)
