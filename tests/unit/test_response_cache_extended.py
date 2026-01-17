"""Extended unit tests for response_cache module.

Tests cover additional paths not covered by existing tests:
- Cache directory initialization edge cases
- get() method error handling
- get_stats() method with various states
- clear() method with files and errors
"""

import time
from pathlib import Path
from unittest.mock import patch

from src.utils.response_cache import ResponseCache


class TestResponseCacheInit:
    """Tests for ResponseCache initialization."""

    def test_init_default_directory(self, tmp_path, monkeypatch):
        """Test default cache directory creation."""
        monkeypatch.chdir(tmp_path)

        cache = ResponseCache()

        assert cache.enabled is True

    def test_init_custom_directory(self, tmp_path):
        """Test custom cache directory."""
        custom_dir = tmp_path / "custom_cache"
        cache = ResponseCache(cache_dir=custom_dir)

        assert cache.cache_dir == custom_dir
        assert custom_dir.exists()

    def test_init_disabled(self, tmp_path):
        """Test cache disabled on init."""
        cache = ResponseCache(cache_dir=tmp_path, enabled=False)

        assert cache.enabled is False

    def test_init_creates_parent_directories(self, tmp_path):
        """Test that init creates nested directories."""
        nested_dir = tmp_path / "a" / "b" / "c" / "cache"
        cache = ResponseCache(cache_dir=nested_dir)

        assert nested_dir.exists()
        assert cache.enabled is True

    def test_init_permission_error_disables_cache(self, tmp_path, monkeypatch):
        """Test that permission error disables cache."""
        # Mock mkdir to raise PermissionError
        with patch.object(Path, "mkdir", side_effect=PermissionError("No access")):
            cache = ResponseCache(cache_dir=tmp_path / "new_dir")
            assert cache.enabled is False


class TestResponseCacheGet:
    """Tests for ResponseCache get() method."""

    def test_get_disabled_cache(self, tmp_path):
        """Test get returns None when cache disabled."""
        cache = ResponseCache(cache_dir=tmp_path, enabled=False)
        messages = [{"role": "user", "content": "test"}]

        result = cache.get(messages, "system", 0.7)

        assert result is None

    def test_get_cache_miss(self, tmp_path):
        """Test get returns None for cache miss."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "not cached"}]

        result = cache.get(messages, "system", 0.7)

        assert result is None

    def test_get_cache_hit(self, tmp_path):
        """Test get returns cached value."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        cache.put(messages, "system", 0.7, "cached response")
        result = cache.get(messages, "system", 0.7)

        assert result == "cached response"

    def test_get_expired_cache(self, tmp_path):
        """Test get returns None for expired cache."""
        cache = ResponseCache(cache_dir=tmp_path, ttl_seconds=1)
        messages = [{"role": "user", "content": "test"}]

        cache.put(messages, "system", 0.7, "cached response")
        time.sleep(1.1)

        result = cache.get(messages, "system", 0.7)

        assert result is None

    def test_get_invalid_json_removes_file(self, tmp_path):
        """Test that invalid JSON cache file is removed."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        # Create cache entry
        cache.put(messages, "system", 0.7, "response")
        key = cache._get_cache_key(messages, "system", 0.7)
        cache_file = cache.cache_dir / f"{key}.json"

        # Corrupt the file
        cache_file.write_text("not valid json{{{")

        result = cache.get(messages, "system", 0.7)

        assert result is None
        assert not cache_file.exists()  # File should be removed

    def test_get_missing_fields_removes_file(self, tmp_path):
        """Test that cache file with missing fields is removed."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        # Create cache entry
        cache.put(messages, "system", 0.7, "response")
        key = cache._get_cache_key(messages, "system", 0.7)
        cache_file = cache.cache_dir / f"{key}.json"

        # Write file without required fields
        cache_file.write_text('{"only_one_field": "value"}')

        result = cache.get(messages, "system", 0.7)

        assert result is None
        assert not cache_file.exists()

    def test_get_invalid_structure_removes_file(self, tmp_path):
        """Test that cache file with invalid structure is removed."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        # Create cache entry
        cache.put(messages, "system", 0.7, "response")
        key = cache._get_cache_key(messages, "system", 0.7)
        cache_file = cache.cache_dir / f"{key}.json"

        # Write array instead of dict
        cache_file.write_text("[1, 2, 3]")

        result = cache.get(messages, "system", 0.7)

        assert result is None
        assert not cache_file.exists()

    def test_get_handles_read_error(self, tmp_path):
        """Test get handles file read errors."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        # Create cache entry
        cache.put(messages, "system", 0.7, "response")

        # Mock open to raise an error
        with patch("builtins.open", side_effect=IOError("Read error")):
            result = cache.get(messages, "system", 0.7)

        assert result is None


class TestResponseCachePut:
    """Tests for ResponseCache put() method."""

    def test_put_disabled_cache(self, tmp_path):
        """Test put does nothing when cache disabled."""
        cache = ResponseCache(cache_dir=tmp_path, enabled=False)
        messages = [{"role": "user", "content": "test"}]

        cache.put(messages, "system", 0.7, "response")

        # No files should be created
        cache_files = list(tmp_path.glob("*.json"))
        assert len(cache_files) == 0

    def test_put_creates_cache_file(self, tmp_path):
        """Test put creates cache file."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        cache.put(messages, "system", 0.7, "response")

        cache_files = list(tmp_path.glob("*.json"))
        assert len(cache_files) == 1

    def test_put_handles_write_error(self, tmp_path):
        """Test put handles write errors gracefully."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        # Mock open to raise an error
        with patch("builtins.open", side_effect=IOError("Write error")):
            # Should not raise
            cache.put(messages, "system", 0.7, "response")


class TestResponseCacheClear:
    """Tests for ResponseCache clear() method."""

    def test_clear_removes_all_files(self, tmp_path):
        """Test clear removes all cache files."""
        cache = ResponseCache(cache_dir=tmp_path)

        # Create multiple cache entries
        for i in range(3):
            messages = [{"role": "user", "content": f"test{i}"}]
            cache.put(messages, "system", 0.7, f"response{i}")

        assert len(list(tmp_path.glob("*.json"))) == 3

        cache.clear()

        assert len(list(tmp_path.glob("*.json"))) == 0

    def test_clear_disabled_cache(self, tmp_path):
        """Test clear does nothing when cache disabled."""
        cache = ResponseCache(cache_dir=tmp_path, enabled=True)
        messages = [{"role": "user", "content": "test"}]
        cache.put(messages, "system", 0.7, "response")

        cache.enabled = False
        cache.clear()

        # File should still exist
        assert len(list(tmp_path.glob("*.json"))) == 1

    def test_clear_nonexistent_directory(self, tmp_path):
        """Test clear handles nonexistent directory."""
        cache = ResponseCache(cache_dir=tmp_path / "subdir")

        # Remove directory
        cache.cache_dir.rmdir()

        # Should not raise
        cache.clear()

    def test_clear_handles_delete_error(self, tmp_path):
        """Test clear handles file delete errors."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]
        cache.put(messages, "system", 0.7, "response")

        # Mock unlink to raise an error
        with patch.object(Path, "unlink", side_effect=PermissionError("Cannot delete")):
            # Should not raise
            cache.clear()


class TestResponseCacheGetStats:
    """Tests for ResponseCache get_stats() method."""

    def test_get_stats_disabled_cache(self, tmp_path):
        """Test get_stats when cache disabled."""
        cache = ResponseCache(cache_dir=tmp_path, enabled=False)

        stats = cache.get_stats()

        assert stats["enabled"] is False
        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0

    def test_get_stats_empty_cache(self, tmp_path):
        """Test get_stats with empty cache."""
        cache = ResponseCache(cache_dir=tmp_path)

        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["total_files"] == 0
        assert stats["total_size_bytes"] == 0

    def test_get_stats_with_files(self, tmp_path):
        """Test get_stats with cached files."""
        cache = ResponseCache(cache_dir=tmp_path)

        # Create multiple cache entries
        for i in range(3):
            messages = [{"role": "user", "content": f"test{i}"}]
            cache.put(messages, "system", 0.7, f"response{i}")

        stats = cache.get_stats()

        assert stats["enabled"] is True
        assert stats["total_files"] == 3
        assert stats["total_size_bytes"] > 0
        assert stats["total_size_mb"] > 0
        assert stats["oldest_timestamp"] is not None
        assert stats["newest_timestamp"] is not None

    def test_get_stats_nonexistent_directory(self, tmp_path):
        """Test get_stats when cache directory doesn't exist."""
        cache = ResponseCache(cache_dir=tmp_path / "subdir")

        # Remove directory
        cache.cache_dir.rmdir()

        stats = cache.get_stats()

        assert stats["enabled"] is False
        assert stats["total_files"] == 0

    def test_get_stats_handles_corrupted_files(self, tmp_path):
        """Test get_stats handles corrupted cache files."""
        cache = ResponseCache(cache_dir=tmp_path)

        # Create valid cache entry
        messages = [{"role": "user", "content": "test"}]
        cache.put(messages, "system", 0.7, "response")

        # Create corrupted file
        (tmp_path / "corrupted.json").write_text("not valid json")

        # Should not raise
        stats = cache.get_stats()

        assert stats["total_files"] == 2  # Both files counted
        assert stats["oldest_timestamp"] is not None  # Only valid file has timestamp


class TestResponseCacheKey:
    """Tests for cache key generation."""

    def test_same_content_same_key(self, tmp_path):
        """Test that identical content produces identical keys."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        key1 = cache._get_cache_key(messages, "system", 0.7)
        key2 = cache._get_cache_key(messages, "system", 0.7)

        assert key1 == key2

    def test_different_messages_different_key(self, tmp_path):
        """Test that different messages produce different keys."""
        cache = ResponseCache(cache_dir=tmp_path)

        key1 = cache._get_cache_key([{"role": "user", "content": "a"}], "system", 0.7)
        key2 = cache._get_cache_key([{"role": "user", "content": "b"}], "system", 0.7)

        assert key1 != key2

    def test_different_system_different_key(self, tmp_path):
        """Test that different system prompts produce different keys."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        key1 = cache._get_cache_key(messages, "system1", 0.7)
        key2 = cache._get_cache_key(messages, "system2", 0.7)

        assert key1 != key2

    def test_different_temperature_different_key(self, tmp_path):
        """Test that different temperatures produce different keys."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        key1 = cache._get_cache_key(messages, "system", 0.7)
        key2 = cache._get_cache_key(messages, "system", 0.8)

        assert key1 != key2

    def test_key_is_valid_hex(self, tmp_path):
        """Test that cache key is valid hex string."""
        cache = ResponseCache(cache_dir=tmp_path)
        messages = [{"role": "user", "content": "test"}]

        key = cache._get_cache_key(messages, "system", 0.7)

        # Should be 64 character hex string (SHA-256)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)
