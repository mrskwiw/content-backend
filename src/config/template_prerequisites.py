"""Template research tool prerequisites mapping.

Maps each post template to recommended and required research tools.
This helps users understand which research tools enhance specific template types.
"""

from typing import Dict, List

# Template ID to research tool mapping
# Template IDs correspond to templates in 02_POST_TEMPLATE_LIBRARY.md
TEMPLATE_PREREQUISITES: Dict[int, Dict[str, List[str]]] = {
    # Template 1: Problem Recognition Post
    1: {
        "required": [],
        "recommended": ["audience_research", "seo_keyword_research"],
    },
    # Template 2: Statistic Post
    2: {
        "required": [],
        "recommended": ["content_gap_analysis", "market_trends_research", "seo_keyword_research"],
    },
    # Template 3: Contrarian Post
    3: {
        "required": [],
        "recommended": ["competitive_analysis", "market_trends_research", "voice_analysis"],
    },
    # Template 4: Evolution Post
    4: {
        "required": [],
        "recommended": ["market_trends_research", "competitive_analysis"],
    },
    # Template 5: Question Post
    5: {
        "required": [],
        "recommended": ["audience_research", "content_gap_analysis"],
    },
    # Template 6: Story Post (Personal Experience)
    6: {
        "required": [],
        "recommended": ["story_mining", "voice_analysis", "brand_archetype"],
    },
    # Template 7: Myth-Busting Post
    7: {
        "required": [],
        "recommended": ["content_gap_analysis", "audience_research", "seo_keyword_research"],
    },
    # Template 8: Vulnerability Post
    8: {
        "required": [],
        "recommended": ["story_mining", "voice_analysis", "brand_archetype"],
    },
    # Template 9: How-To Guide
    9: {
        "required": [],
        "recommended": ["seo_keyword_research", "content_gap_analysis", "audience_research"],
    },
    # Template 10: Comparison Post
    10: {
        "required": [],
        "recommended": ["competitive_analysis", "content_gap_analysis"],
    },
    # Template 11: Learning Post
    11: {
        "required": [],
        "recommended": ["voice_analysis", "content_audit"],
    },
    # Template 12: Behind-the-Scenes
    12: {
        "required": [],
        "recommended": ["story_mining", "brand_archetype", "voice_analysis"],
    },
    # Template 13: Future/Prediction Post
    13: {
        "required": [],
        "recommended": ["market_trends_research", "competitive_analysis"],
    },
    # Template 14: Q&A Post
    14: {
        "required": [],
        "recommended": ["audience_research", "content_gap_analysis"],
    },
    # Template 15: Milestone/Achievement Post
    15: {
        "required": [],
        "recommended": ["story_mining", "brand_archetype"],
    },
}


def get_template_prerequisites(template_id: int) -> Dict[str, List[str]]:
    """Get prerequisites for a specific template.

    Args:
        template_id: Template ID (1-15)

    Returns:
        Dict with 'required' and 'recommended' tool lists
    """
    return TEMPLATE_PREREQUISITES.get(template_id, {"required": [], "recommended": []})
