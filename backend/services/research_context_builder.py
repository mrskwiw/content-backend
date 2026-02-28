"""
Research Context Builder Service

Fetches and formats research results for inclusion in content generation context.
Provides concise, actionable insights from completed research tools with usage guidance.

Phase 1 Implementation - Research Context Integration Feature
"""

from typing import Dict, Any
from sqlalchemy.orm import Session

from backend.models.research_result import ResearchResult
from backend.services import crud
from src.utils.response_cache import ResponseCache
from backend.utils.logger import logger


# Initialize cache (48-hour TTL for research context)
cache = ResponseCache()
CACHE_TTL = 48 * 3600  # 48 hours
CACHE_PREFIX = "research_context"

# Token limits
MAX_TOTAL_TOKENS = 500  # Maximum tokens for all research insights
MAX_TOOL_TOKENS = 150  # Maximum tokens per tool summary
PRIORITY_TOOLS = ["voice_analysis", "seo_keyword_research", "brand_archetype"]


def build_research_context(db: Session, client_id: str) -> Dict[str, Any]:
    """
    Build formatted research context for a client.

    Fetches all completed research results for the client and formats them
    as concise, actionable insights for content generation.

    Args:
        db: Database session
        client_id: Client ID to fetch research for

    Returns:
        Dict with:
        - formatted_text: String of formatted research insights
        - tool_count: Number of tools included
        - total_tokens: Approximate token count
        - tools_included: List of tool names included
    """
    # Check cache first
    cache_key = f"{CACHE_PREFIX}:{client_id}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Using cached research context for client {client_id}")
        return cached

    # Fetch research results from database
    results = crud.get_research_results_by_client(db, client_id)

    # Filter to completed results only
    completed_results = [r for r in results if r.status == "completed"]

    if not completed_results:
        logger.info(f"No completed research results found for client {client_id}")
        return {"formatted_text": "", "tool_count": 0, "total_tokens": 0, "tools_included": []}

    # Group by tool name and keep most recent for each tool
    tool_results = {}
    for result in completed_results:
        if result.tool_name not in tool_results:
            tool_results[result.tool_name] = result
        else:
            # Keep most recent
            if result.created_at > tool_results[result.tool_name].created_at:
                tool_results[result.tool_name] = result

    # Format all results
    formatted = _format_all_results(tool_results)

    # Cache result
    cache.set(cache_key, formatted, ttl=CACHE_TTL)
    logger.info(
        f"Formatted research context for client {client_id}: "
        f"{formatted['tool_count']} tools, ~{formatted['total_tokens']} tokens"
    )

    return formatted


def _format_all_results(tool_results: Dict[str, ResearchResult]) -> Dict[str, Any]:
    """
    Format all research results into concise context string.

    Args:
        tool_results: Dict mapping tool_name to ResearchResult

    Returns:
        Dict with formatted_text, tool_count, total_tokens, tools_included
    """
    formatted_sections = []
    total_tokens = 0
    tools_included = []

    # Prioritize tools: voice, SEO, archetype first
    priority_tools = [name for name in PRIORITY_TOOLS if name in tool_results]
    other_tools = [name for name in tool_results.keys() if name not in PRIORITY_TOOLS]
    ordered_tools = priority_tools + other_tools

    for tool_name in ordered_tools:
        result = tool_results[tool_name]

        # Format this tool's result
        formatted = _format_tool_result(tool_name, result)

        if not formatted:
            continue

        # Estimate tokens (rough: 4 chars = 1 token)
        tool_tokens = len(formatted) // 4

        # Check if adding this would exceed limit
        if total_tokens + tool_tokens > MAX_TOTAL_TOKENS:
            # Skip if not priority tool
            if tool_name not in PRIORITY_TOOLS:
                logger.info(f"Skipping {tool_name} - would exceed token limit")
                continue
            # Truncate if priority tool
            truncate_to = (MAX_TOTAL_TOKENS - total_tokens) * 4
            formatted = formatted[:truncate_to] + "..."
            tool_tokens = len(formatted) // 4

        formatted_sections.append(formatted)
        total_tokens += tool_tokens
        tools_included.append(tool_name)

        # Stop if we hit the limit
        if total_tokens >= MAX_TOTAL_TOKENS:
            break

    # Assemble final text
    if not formatted_sections:
        formatted_text = ""
    else:
        header = "RESEARCH INSIGHTS (from completed research tools):\n\n"
        formatted_text = header + "\n\n".join(formatted_sections)

    return {
        "formatted_text": formatted_text,
        "tool_count": len(tools_included),
        "total_tokens": total_tokens,
        "tools_included": tools_included,
    }


def _format_tool_result(tool_name: str, result: ResearchResult) -> str:
    """Format a single research tool result."""
    try:
        formatters = {
            "voice_analysis": _format_voice_analysis,
            "seo_keyword_research": _format_seo_keywords,
            "brand_archetype": _format_brand_archetype,
            "competitive_analysis": _format_competitive_analysis,
            "content_gap_analysis": _format_content_gap,
            "market_trends_research": _format_market_trends,
            "platform_strategy": _format_platform_strategy,
            "content_calendar": _format_content_calendar,
            "audience_research": _format_audience_research,
            "icp_workshop": _format_icp_workshop,
            "story_mining": _format_story_mining,
            "content_audit": _format_content_audit,
        }
        formatter = formatters.get(tool_name)
        if not formatter:
            logger.warning(f"No formatter found for tool: {tool_name}")
            return ""
        return formatter(result)
    except Exception as e:
        logger.error(f"Error formatting {tool_name}: {e}")
        return ""


def _format_voice_analysis(result):
    data = result.data or {}
    date = result.created_at.strftime("%b %d") if result.created_at else "recently"
    return f"Voice Analysis ({date}): Tone={data.get('tone','?')}, Readability={data.get('readability_grade','?')}"


def _format_seo_keywords(result):
    data = result.data or {}
    date = result.created_at.strftime("%b %d") if result.created_at else "recently"
    return f"SEO Keywords ({date}): Primary={','.join((data.get('primary_keywords',[]))[:3])}"


def _format_brand_archetype(result):
    data = result.data or {}
    date = result.created_at.strftime("%b %d") if result.created_at else "recently"
    return f"Brand Archetype ({date}): {data.get('archetype','?')}"


def _format_competitive_analysis(result):
    return "Competitive Analysis: See data field"


def _format_content_gap(result):
    return "Content Gap Analysis: See data field"


def _format_market_trends(result):
    return "Market Trends: See data field"


def _format_platform_strategy(result):
    return "Platform Strategy: See data field"


def _format_content_calendar(result):
    return "Content Calendar: See data field"


def _format_audience_research(result):
    return "Audience Research: See data field"


def _format_icp_workshop(result):
    return "ICP Workshop: See data field"


def _format_story_mining(result):
    return "Story Mining: See data field"


def _format_content_audit(result):
    return "Content Audit: See data field"


def invalidate_cache(client_id):
    cache_key = f"{CACHE_PREFIX}:{client_id}"
    cache.delete(cache_key)
    logger.info(f"Invalidated cache for {client_id}")
