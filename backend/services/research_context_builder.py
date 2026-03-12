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
            "determine_competitors": _format_determine_competitors,
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


def _format_determine_competitors(result):
    """Extract competitor insights for content generation context"""
    data = result.data if hasattr(result, "data") else result

    parts = []

    # Primary competitors (names only, concise)
    if data.get("primary_competitors"):
        names = [
            c.get("name", c) if isinstance(c, dict) else c for c in data["primary_competitors"][:3]
        ]
        parts.append(f"Main Competitors: {', '.join(names)}")

    # Market gaps (opportunities)
    if data.get("market_gaps"):
        gaps = data["market_gaps"][:2]
        parts.append(f"Market Gaps: {', '.join(gaps)}")

    # Positioning recommendation (how to differentiate)
    if data.get("recommended_positioning"):
        positioning = data["recommended_positioning"][:80]  # First 80 chars
        parts.append(f"Positioning: {positioning}")

    return " | ".join(parts) if parts else "Competitors: Identified"


def _format_competitive_analysis(result):
    """Extract key competitive insights for content generation."""
    data = result.data if hasattr(result, "data") else result

    parts = []

    # Quick wins (immediate opportunities)
    if data.get("quick_wins"):
        wins = data["quick_wins"][:2]  # Top 2
        parts.append(f"Quick Wins: {', '.join(wins)}")

    # Content gaps (opportunity areas)
    if data.get("content_gaps"):
        gaps = [
            g.get("topic", g.get("gap_title", str(g))) if isinstance(g, dict) else str(g)
            for g in data["content_gaps"][:3]
        ]
        parts.append(f"Content Gaps: {', '.join(gaps)}")

    # Differentiation strategies (positioning)
    if data.get("differentiation_strategies"):
        strategies = [
            s.get("strategy", s.get("title", str(s))) if isinstance(s, dict) else str(s)
            for s in data["differentiation_strategies"][:2]
        ]
        parts.append(f"Differentiate Via: {', '.join(strategies)}")

    # Recommended position (market positioning)
    if data.get("recommended_position"):
        pos = data["recommended_position"]
        if isinstance(pos, dict):
            positioning = pos.get("positioning_statement", pos.get("statement", ""))
            if positioning:
                parts.append(f"Position As: {positioning[:100]}")

    # Competitive threats (what to watch)
    if data.get("competitive_threats"):
        threats = data["competitive_threats"][:2]
        parts.append(f"Watch: {', '.join(threats)}")

    return " | ".join(parts) if parts else "Competitive Analysis: Available"


def _format_content_gap(result):
    return "Content Gap Analysis: See data field"


def _format_market_trends(result):
    """Extract key market trends insights for content generation."""
    data = result.data if hasattr(result, "data") else result

    parts = []

    # Market summary (high-level context)
    if data.get("market_summary"):
        parts.append(f"Market Context: {data['market_summary']}")

    # Immediate opportunities (most actionable for content)
    if data.get("immediate_opportunities"):
        opps = data["immediate_opportunities"][:3]  # Top 3
        parts.append(f"Hot Topics: {', '.join(opps)}")

    # Top rising trends (trending now)
    if data.get("top_rising_trends"):
        trends = [
            t.get("title", t) if isinstance(t, dict) else t for t in data["top_rising_trends"][:3]
        ]
        parts.append(f"Rising Trends: {', '.join(trends)}")

    # Key themes (overarching narratives)
    if data.get("key_themes"):
        themes = data["key_themes"][:3]
        parts.append(f"Key Themes: {', '.join(themes)}")

    # Declining topics (what to avoid)
    if data.get("declining_topics"):
        declining = data["declining_topics"][:2]
        parts.append(f"Avoid: {', '.join(declining)}")

    return " | ".join(parts) if parts else "Market Trends: Available"


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
