"""Unit tests for template_cache module.

Tests cover:
- TemplateCacheEntry creation and validation
- TemplateCacheManager get/put operations
- LRU eviction policy
- TTL expiration
- File modification detection
- Cache statistics
"""

import time
import pytest
from pathlib import Path
from unittest.mock import patch

from src.models.template import Template, TemplateType, TemplateDifficulty
from src.utils.template_cache import (
    TemplateCacheEntry,
    TemplateCacheManager,
    get_cache_manager,
)


@pytest.fixture
def sample_templates():
    """Create sample templates for testing."""
    return [
        Template(
            template_id=1,
            name="Problem Recognition",
            template_type=TemplateType.PROBLEM_RECOGNITION,
            structure="[HOOK] [PROBLEM] [SOLUTION]",
            best_for="Awareness",
            difficulty=TemplateDifficulty.FAST,
        ),
        Template(
            template_id=2,
            name="Statistic + Insight",
            template_type=TemplateType.STATISTIC,
            structure="[STAT] [INSIGHT] [CTA]",
            best_for="Authority",
            difficulty=TemplateDifficulty.FAST,
        ),
    ]


class TestTemplateCacheEntry:
    """Tests for TemplateCacheEntry."""

    def test_create_entry(self, sample_templates):
        """Test creating a cache entry."""
        entry = TemplateCacheEntry(
            templates=sample_templates,
            mtime=1234567890.0,
            timestamp=time.time(),
        )

        assert entry.templates == sample_templates
        assert entry.mtime == 1234567890.0
        assert entry.timestamp > 0

    def test_is_valid_true(self, sample_templates, tmp_path):
        """Test entry is valid when TTL not expired and file unchanged."""
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        entry = TemplateCacheEntry(
            templates=sample_templates,
            mtime=mtime,
            timestamp=time.time(),
        )

        assert entry.is_valid(test_file, ttl_seconds=3600) is True

    def test_is_valid_ttl_expired(self, sample_templates, tmp_path):
        """Test entry is invalid when TTL expired."""
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        # Create entry with old timestamp
        entry = TemplateCacheEntry(
            templates=sample_templates,
            mtime=mtime,
            timestamp=time.time() - 100,  # 100 seconds ago
        )

        # TTL of 50 seconds means entry is expired
        assert entry.is_valid(test_file, ttl_seconds=50) is False

    def test_is_valid_file_modified(self, sample_templates, tmp_path):
        """Test entry is invalid when file was modified."""
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates v1")
        old_mtime = test_file.stat().st_mtime

        entry = TemplateCacheEntry(
            templates=sample_templates,
            mtime=old_mtime,
            timestamp=time.time(),
        )

        # Modify file
        time.sleep(0.01)  # Ensure different mtime
        test_file.write_text("# Templates v2")

        assert entry.is_valid(test_file, ttl_seconds=3600) is False

    def test_is_valid_file_not_found(self, sample_templates, tmp_path):
        """Test entry is invalid when file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.md"

        entry = TemplateCacheEntry(
            templates=sample_templates,
            mtime=1234567890.0,
            timestamp=time.time(),
        )

        assert entry.is_valid(nonexistent, ttl_seconds=3600) is False

    def test_is_valid_oserror(self, sample_templates, tmp_path):
        """Test entry is invalid when OSError occurs."""
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        entry = TemplateCacheEntry(
            templates=sample_templates,
            mtime=mtime,
            timestamp=time.time(),
        )

        # Mock stat to raise OSError
        with patch.object(Path, "stat", side_effect=OSError("Permission denied")):
            assert entry.is_valid(test_file, ttl_seconds=3600) is False


class TestTemplateCacheManager:
    """Tests for TemplateCacheManager."""

    def test_create_manager(self):
        """Test creating a cache manager."""
        manager = TemplateCacheManager(max_size=5, ttl_seconds=1800)

        assert manager.max_size == 5
        assert manager.ttl_seconds == 1800
        assert manager.size == 0

    def test_put_and_get(self, sample_templates, tmp_path):
        """Test storing and retrieving templates."""
        manager = TemplateCacheManager()
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        manager.put(test_file, sample_templates, mtime)

        result = manager.get(test_file)

        assert result is not None
        assert len(result) == 2
        assert result[0].name == "Problem Recognition"

    def test_get_cache_miss(self, tmp_path):
        """Test get returns None for cache miss."""
        manager = TemplateCacheManager()
        nonexistent = tmp_path / "nonexistent.md"

        result = manager.get(nonexistent)

        assert result is None

    def test_get_expired_entry(self, sample_templates, tmp_path):
        """Test get returns None for expired entry."""
        manager = TemplateCacheManager(ttl_seconds=0.1)  # Very short TTL
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        manager.put(test_file, sample_templates, mtime)
        time.sleep(0.15)  # Wait for TTL to expire

        result = manager.get(test_file)

        assert result is None

    def test_put_updates_existing(self, sample_templates, tmp_path):
        """Test put updates existing entry."""
        manager = TemplateCacheManager()
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        # Put initial
        manager.put(test_file, sample_templates, mtime)
        assert manager.size == 1

        # Put again (update)
        manager.put(test_file, sample_templates[:1], mtime)
        assert manager.size == 1  # Still just one entry

        result = manager.get(test_file)
        assert len(result) == 1  # Updated to have just 1 template

    def test_lru_eviction(self, sample_templates, tmp_path):
        """Test LRU eviction when cache is full."""
        manager = TemplateCacheManager(max_size=2)

        # Create 3 files
        files = []
        for i in range(3):
            f = tmp_path / f"templates_{i}.md"
            f.write_text(f"# Templates {i}")
            files.append((f, f.stat().st_mtime))

        # Fill cache
        manager.put(files[0][0], sample_templates, files[0][1])
        manager.put(files[1][0], sample_templates, files[1][1])
        assert manager.size == 2

        # Add third, should evict first (oldest)
        manager.put(files[2][0], sample_templates, files[2][1])
        assert manager.size == 2

        # First file should be evicted
        assert manager.get(files[0][0]) is None
        assert manager.get(files[1][0]) is not None
        assert manager.get(files[2][0]) is not None

    def test_invalidate(self, sample_templates, tmp_path):
        """Test invalidating a cache entry."""
        manager = TemplateCacheManager()
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        manager.put(test_file, sample_templates, mtime)
        assert manager.size == 1

        manager.invalidate(test_file)
        assert manager.size == 0

    def test_invalidate_nonexistent(self, tmp_path):
        """Test invalidating nonexistent entry."""
        manager = TemplateCacheManager()
        nonexistent = tmp_path / "nonexistent.md"

        # Should not raise
        manager.invalidate(nonexistent)
        assert manager.size == 0

    def test_clear(self, sample_templates, tmp_path):
        """Test clearing the cache."""
        manager = TemplateCacheManager()
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        manager.put(test_file, sample_templates, mtime)
        manager.get(test_file)  # Create hit

        assert manager.size == 1
        assert manager._hit_count > 0

        manager.clear()

        assert manager.size == 0
        assert manager._hit_count == 0
        assert manager._miss_count == 0

    def test_hit_rate_empty(self):
        """Test hit rate is 0 with no requests."""
        manager = TemplateCacheManager()

        assert manager.hit_rate == 0.0

    def test_hit_rate(self, sample_templates, tmp_path):
        """Test hit rate calculation."""
        manager = TemplateCacheManager()
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        manager.put(test_file, sample_templates, mtime)

        # 2 hits
        manager.get(test_file)
        manager.get(test_file)

        # 1 miss
        manager.get(tmp_path / "nonexistent.md")

        # Hit rate = 2 / 3 = 0.666...
        assert 0.66 < manager.hit_rate < 0.67

    def test_get_stats(self, sample_templates, tmp_path):
        """Test getting cache statistics."""
        manager = TemplateCacheManager(max_size=5, ttl_seconds=1800)
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        manager.put(test_file, sample_templates, mtime)
        manager.get(test_file)  # Hit
        manager.get(tmp_path / "nonexistent.md")  # Miss

        stats = manager.get_stats()

        assert stats["size"] == 1
        assert stats["max_size"] == 5
        assert stats["hit_count"] == 1
        assert stats["miss_count"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["ttl_seconds"] == 1800

    def test_move_to_end_on_access(self, sample_templates, tmp_path):
        """Test that accessing entry moves it to end (LRU)."""
        manager = TemplateCacheManager(max_size=2)

        # Create 2 files
        file1 = tmp_path / "templates_1.md"
        file1.write_text("# Templates 1")
        mtime1 = file1.stat().st_mtime

        file2 = tmp_path / "templates_2.md"
        file2.write_text("# Templates 2")
        mtime2 = file2.stat().st_mtime

        # Add both
        manager.put(file1, sample_templates, mtime1)
        manager.put(file2, sample_templates, mtime2)

        # Access file1 (moves it to end)
        manager.get(file1)

        # Add third file - should evict file2 (now oldest)
        file3 = tmp_path / "templates_3.md"
        file3.write_text("# Templates 3")
        mtime3 = file3.stat().st_mtime
        manager.put(file3, sample_templates, mtime3)

        # file2 should be evicted, file1 and file3 should remain
        assert manager.get(file2) is None
        assert manager.get(file1) is not None


class TestGetCacheManager:
    """Tests for get_cache_manager function."""

    def test_get_cache_manager_creates_instance(self):
        """Test getting global cache manager."""
        import src.utils.template_cache as tc

        # Reset global
        tc._global_cache_manager = None

        manager = get_cache_manager(max_size=20, ttl_seconds=7200)

        assert manager is not None
        assert manager.max_size == 20
        assert manager.ttl_seconds == 7200

        # Cleanup
        tc._global_cache_manager = None

    def test_get_cache_manager_returns_same_instance(self):
        """Test that get_cache_manager returns singleton."""
        import src.utils.template_cache as tc

        # Reset global
        tc._global_cache_manager = None

        manager1 = get_cache_manager()
        manager2 = get_cache_manager()

        assert manager1 is manager2

        # Cleanup
        tc._global_cache_manager = None


class TestThreadSafety:
    """Tests for thread safety."""

    def test_concurrent_access(self, sample_templates, tmp_path):
        """Test concurrent access to cache."""
        import threading

        manager = TemplateCacheManager()
        test_file = tmp_path / "templates.md"
        test_file.write_text("# Templates")
        mtime = test_file.stat().st_mtime

        errors = []

        def worker():
            try:
                for _ in range(100):
                    manager.put(test_file, sample_templates, mtime)
                    manager.get(test_file)
                    manager.invalidate(test_file)
                    manager.get_stats()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have no errors
        assert len(errors) == 0
