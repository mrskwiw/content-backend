"""Create unit test file for research_context_builder"""

import os

# Create directory
test_dir = os.path.join('tests', 'unit', 'services')
os.makedirs(test_dir, exist_ok=True)

test_content = '''"""
Unit tests for research_context_builder.py

Target: 90%+ coverage
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from backend.services.research_context_builder import (
    build_research_context,
    invalidate_cache,
    _format_all_results,
    _format_tool_result,
    _format_voice_analysis,
    _format_seo_keywords,
    _format_brand_archetype,
    CACHE_PREFIX,
    CACHE_TTL,
    MAX_TOTAL_TOKENS,
)


class TestBuildResearchContext:
    """Test the main build_research_context function."""

    def test_returns_cached_result_when_available(self):
        """Test that cached results are returned without DB query."""
        mock_db = Mock(spec=Session)
        client_id = "test-client-123"
        cached_data = {
            "formatted_text": "Cached insights",
            "tools_included": ["voice_analysis"],
            "total_tokens": 100,
        }

        with patch("backend.services.research_context_builder.cache") as mock_cache:
            mock_cache.get.return_value = cached_data

            result = build_research_context(mock_db, client_id)

            assert result == cached_data
            mock_cache.get.assert_called_once_with(f"{CACHE_PREFIX}:{client_id}")

    def test_fetches_from_db_on_cache_miss(self):
        """Test that DB is queried when cache misses."""
        mock_db = Mock(spec=Session)
        client_id = "test-client-123"

        mock_result = Mock()
        mock_result.tool_name = "voice_analysis"
        mock_result.result_data = {"readability_score": 8.5}
        mock_result.created_at = datetime.now()

        with patch("backend.services.research_context_builder.cache") as mock_cache, \
             patch("backend.services.research_context_builder.crud") as mock_crud:
            mock_cache.get.return_value = None
            mock_crud.get_research_results_by_client.return_value = [mock_result]

            result = build_research_context(mock_db, client_id)

            mock_cache.get.assert_called_once()
            mock_crud.get_research_results_by_client.assert_called_once_with(mock_db, client_id)
            assert isinstance(result, dict)
            assert "formatted_text" in result

    def test_caches_result_after_db_fetch(self):
        """Test that results are cached after DB fetch."""
        mock_db = Mock(spec=Session)
        client_id = "test-client-123"

        mock_result = Mock()
        mock_result.tool_name = "voice_analysis"
        mock_result.result_data = {"readability_score": 8.5}
        mock_result.created_at = datetime.now()

        with patch("backend.services.research_context_builder.cache") as mock_cache, \
             patch("backend.services.research_context_builder.crud") as mock_crud:
            mock_cache.get.return_value = None
            mock_crud.get_research_results_by_client.return_value = [mock_result]

            result = build_research_context(mock_db, client_id)

            assert mock_cache.set.called
            call_args = mock_cache.set.call_args
            assert call_args[0][0] == f"{CACHE_PREFIX}:{client_id}"
            assert call_args[1]["ttl"] == CACHE_TTL

    def test_returns_empty_when_no_results(self):
        """Test behavior when no research results exist."""
        mock_db = Mock(spec=Session)
        client_id = "test-client-123"

        with patch("backend.services.research_context_builder.cache") as mock_cache, \
             patch("backend.services.research_context_builder.crud") as mock_crud:
            mock_cache.get.return_value = None
            mock_crud.get_research_results_by_client.return_value = []

            result = build_research_context(mock_db, client_id)

            assert result["formatted_text"] == ""
            assert result["tools_included"] == []
            assert result["total_tokens"] == 0

    def test_handles_db_error_gracefully(self):
        """Test error handling when DB query fails."""
        mock_db = Mock(spec=Session)
        client_id = "test-client-123"

        with patch("backend.services.research_context_builder.cache") as mock_cache, \
             patch("backend.services.research_context_builder.crud") as mock_crud, \
             patch("backend.services.research_context_builder.logger") as mock_logger:
            mock_cache.get.return_value = None
            mock_crud.get_research_results_by_client.side_effect = Exception("DB Error")

            result = build_research_context(mock_db, client_id)

            assert result["formatted_text"] == ""
            assert result["tools_included"] == []
            mock_logger.error.assert_called_once()


class TestInvalidateCache:
    """Test cache invalidation function."""

    def test_invalidates_correct_key(self):
        """Test that correct cache key is invalidated."""
        client_id = "test-client-123"

        with patch("backend.services.research_context_builder.cache") as mock_cache:
            invalidate_cache(client_id)

            mock_cache.delete.assert_called_once_with(f"{CACHE_PREFIX}:{client_id}")

    def test_handles_cache_error(self):
        """Test that cache errors don't raise exceptions."""
        client_id = "test-client-123"

        with patch("backend.services.research_context_builder.cache") as mock_cache, \
             patch("backend.services.research_context_builder.logger") as mock_logger:
            mock_cache.delete.side_effect = Exception("Cache Error")

            invalidate_cache(client_id)

            mock_logger.error.assert_called_once()


class TestTokenBudgetEnforcement:
    """Test token budget enforcement."""

    def test_enforces_total_budget_across_tools(self):
        """Test that total across all tools doesn't exceed 500."""
        results = []

        tool_names = [
            "voice_analysis", "seo_keyword_research", "brand_archetype",
            "competitive_analysis", "content_gap_analysis", "market_trends_research",
            "platform_strategy", "content_calendar", "audience_research",
            "icp_workshop", "story_mining", "content_audit"
        ]

        for tool_name in tool_names:
            mock_result = Mock()
            mock_result.tool_name = tool_name
            mock_result.result_data = {
                "key1": "x" * 500,
                "key2": "y" * 500,
            }
            mock_result.created_at = datetime.now()
            results.append(mock_result)

        formatted = _format_all_results(results)

        assert formatted["total_tokens"] <= MAX_TOTAL_TOKENS
'''

# Write file
test_file = os.path.join(test_dir, 'test_research_context_builder.py')
with open(test_file, 'w', encoding='utf-8') as f:
    f.write(test_content)

print(f"Created {test_file}")
