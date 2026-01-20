"""
Hook Copywriting Frameworks Configuration

Based on hook-creator skill's framework library.
Provides proven copywriting frameworks for generating attention-grabbing hooks.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class HookCategory(str, Enum):
    """Categories of hook frameworks"""

    BENEFIT_DRIVEN = "benefit_driven"
    CURIOSITY_BASED = "curiosity_based"
    SOCIAL_PROOF = "social_proof"
    URGENCY_FOMO = "urgency_fomo"
    PATTERN_INTERRUPT = "pattern_interrupt"


@dataclass
class HookFramework:
    """A copywriting framework for generating hooks"""

    name: str
    description: str
    category: HookCategory
    template: str  # Template with placeholders
    example: str
    best_for: List[str] = field(default_factory=list)
    power_words: List[str] = field(default_factory=list)


# Primary Hook Frameworks (most versatile)
PRIMARY_FRAMEWORKS: List[HookFramework] = [
    HookFramework(
        name="Curiosity Gap",
        description="Creates incomplete information that demands resolution",
        category=HookCategory.CURIOSITY_BASED,
        template="[SURPRISING_FACT] ... [HINT_AT_ANSWER]",
        example="73% of teams miss deadlines. The reason isn't what you think.",
        best_for=["Problem Recognition", "Statistic + Insight", "Myth Busting"],
        power_words=["surprising", "unknown", "hidden", "revealed", "truth about", "why"],
    ),
    HookFramework(
        name="Pain-Agitation-Solution",
        description="Calls out pain, intensifies it, then hints at solution",
        category=HookCategory.BENEFIT_DRIVEN,
        template="[PAIN_POINT]. [AGITATION]. [HINT_AT_SOLUTION].",
        example="Spending 4 hours on reports? That's a full workday lost weekly. Here's the fix.",
        best_for=["Problem Recognition", "How-To", "Comparison"],
        power_words=["struggling", "frustrating", "costly", "solved", "finally"],
    ),
    HookFramework(
        name="Benefit-Driven",
        description="Leads with clear, specific value proposition",
        category=HookCategory.BENEFIT_DRIVEN,
        template="[SPECIFIC_BENEFIT] in [TIMEFRAME] without [PAIN_POINT]",
        example="Save 10 hours weekly without sacrificing quality.",
        best_for=["How-To", "Comparison", "What Changed"],
        power_words=["free", "bonus", "save", "guaranteed", "proven", "results"],
    ),
    HookFramework(
        name="Contrarian",
        description="Challenges common assumptions or industry norms",
        category=HookCategory.PATTERN_INTERRUPT,
        template="[COMMON_BELIEF] is wrong. Here's why [CONTRARIAN_TRUTH].",
        example="More meetings don't improve communication. They destroy it.",
        best_for=["Contrarian Take", "Myth Busting", "What Changed"],
        power_words=["wrong", "myth", "actually", "contrary", "rethink"],
    ),
    HookFramework(
        name="Specific Numbers",
        description="Uses odd, precise numbers for credibility",
        category=HookCategory.SOCIAL_PROOF,
        template="[PRECISE_NUMBER]% of [AUDIENCE] [ACTION]. [INSIGHT].",
        example="147% more engagement with this one change.",
        best_for=["Statistic + Insight", "What Changed", "Milestone"],
        power_words=["data", "research", "study", "proven", "measured"],
    ),
]

# Secondary Hook Frameworks
SECONDARY_FRAMEWORKS: List[HookFramework] = [
    HookFramework(
        name="Question + Benefit",
        description="Problem question with implied solution",
        category=HookCategory.CURIOSITY_BASED,
        template="[PROBLEM_QUESTION]? Here's how to [BENEFIT].",
        example="Still manually tracking leads? Here's how top teams automate it.",
        best_for=["Question Post", "How-To", "Reader Q Response"],
        power_words=["wondering", "struggling", "how to", "finally"],
    ),
    HookFramework(
        name="Social Proof",
        description="Leverages popularity, authority, or testimonials",
        category=HookCategory.SOCIAL_PROOF,
        template="[AUTHORITY/NUMBER] [AUDIENCE] are [ACTION]. Here's what they know.",
        example="500+ CTOs made this switch last quarter. Here's what they discovered.",
        best_for=["Milestone", "Statistic + Insight", "Inside Look"],
        power_words=["top", "leading", "experts", "industry", "trusted"],
    ),
    HookFramework(
        name="Time/Urgency",
        description="Creates FOMO, deadlines, limited availability",
        category=HookCategory.URGENCY_FOMO,
        template="[TIME_ELEMENT] [ACTION] or [CONSEQUENCE].",
        example="This trend is reshaping 2025. Early adopters are already ahead.",
        best_for=["Future Thinking", "What Changed", "Milestone"],
        power_words=["now", "today", "limited", "last chance", "deadline", "don't miss"],
    ),
    HookFramework(
        name="Transformation",
        description="Before → after framing showing change",
        category=HookCategory.BENEFIT_DRIVEN,
        template="From [BEFORE_STATE] to [AFTER_STATE]. [HOW/WHY].",
        example="From 60-hour weeks to 40-hour weeks. One decision changed everything.",
        best_for=["What Changed", "Personal Story", "Things I Got Wrong"],
        power_words=["transformed", "changed", "from...to", "became", "evolved"],
    ),
    HookFramework(
        name="Listicle",
        description="Numbered format promising structured value",
        category=HookCategory.BENEFIT_DRIVEN,
        template="[NUMBER] [THINGS] that [OUTCOME]. Number [X] changed my [RESULT].",
        example="7 habits of high-performing teams. Number 4 changed my perspective.",
        best_for=["How-To", "Things I Got Wrong", "Myth Busting"],
        power_words=["ways", "steps", "secrets", "habits", "mistakes"],
    ),
]

# Advanced Hook Frameworks
ADVANCED_FRAMEWORKS: List[HookFramework] = [
    HookFramework(
        name="How-To Promise",
        description="Promises result without the typical pain point",
        category=HookCategory.BENEFIT_DRIVEN,
        template="How to [ACHIEVE_RESULT] without [PAIN_POINT]",
        example="How to 10x your output without working longer hours.",
        best_for=["How-To", "Comparison"],
        power_words=["without", "never", "easily", "finally"],
    ),
    HookFramework(
        name="Mistake Warning",
        description="Warns about common mistake to avoid",
        category=HookCategory.PATTERN_INTERRUPT,
        template="The #1 mistake [AUDIENCE] make with [TOPIC]. And how to fix it.",
        example="The #1 mistake founders make with hiring. (And it's not salary.)",
        best_for=["Myth Busting", "Things I Got Wrong", "Contrarian Take"],
        power_words=["mistake", "error", "avoid", "costly", "common"],
    ),
    HookFramework(
        name="Secret/Insider",
        description="Positions information as exclusive or insider",
        category=HookCategory.CURIOSITY_BASED,
        template="What [AUTHORITY] won't tell you about [TOPIC].",
        example="What top VCs won't tell you about raising your Series A.",
        best_for=["Inside Look", "Contrarian Take", "Future Thinking"],
        power_words=["secret", "insider", "private", "exclusive", "revealed"],
    ),
    HookFramework(
        name="Comparison",
        description="Pits two options against each other",
        category=HookCategory.PATTERN_INTERRUPT,
        template="[OPTION_A] vs [OPTION_B]: Why [AUDIENCE] is switching",
        example="Remote vs hybrid: Why top companies are choosing a third path.",
        best_for=["Comparison", "Contrarian Take", "What Changed"],
        power_words=["vs", "compared", "better", "switching", "choosing"],
    ),
    HookFramework(
        name="Future Pacing",
        description="Projects audience into a desirable future state",
        category=HookCategory.BENEFIT_DRIVEN,
        template="Imagine [DESIRABLE_FUTURE_STATE]...",
        example="Imagine your team hitting every deadline with time to spare...",
        best_for=["Future Thinking", "Personal Story", "What I Learned From"],
        power_words=["imagine", "picture", "what if", "future", "tomorrow"],
    ),
]

# All frameworks combined
ALL_FRAMEWORKS: List[HookFramework] = (
    PRIMARY_FRAMEWORKS + SECONDARY_FRAMEWORKS + ADVANCED_FRAMEWORKS
)

# Power words organized by emotion
POWER_WORDS_BY_EMOTION: Dict[str, List[str]] = {
    "urgency": ["now", "today", "limited", "last chance", "deadline", "expires", "don't miss"],
    "exclusivity": ["secret", "insider", "private", "members-only", "exclusive", "VIP"],
    "value": ["free", "bonus", "save", "discount", "guaranteed", "proven", "results"],
    "curiosity": ["surprising", "unknown", "hidden", "revealed", "truth about", "why"],
    "trust": ["certified", "official", "verified", "backed by", "research-proven"],
}

# Template type to recommended frameworks mapping
TEMPLATE_FRAMEWORK_MAP: Dict[str, List[str]] = {
    "problem_recognition": ["Pain-Agitation-Solution", "Curiosity Gap", "Question + Benefit"],
    "statistic_insight": ["Specific Numbers", "Curiosity Gap", "Social Proof"],
    "contrarian_take": ["Contrarian", "Mistake Warning", "Comparison"],
    "what_changed": ["Transformation", "Time/Urgency", "Benefit-Driven"],
    "question_post": ["Question + Benefit", "Curiosity Gap", "Future Pacing"],
    "personal_story": ["Transformation", "Future Pacing", "Curiosity Gap"],
    "myth_busting": ["Contrarian", "Mistake Warning", "Listicle"],
    "things_i_got_wrong": ["Transformation", "Mistake Warning", "Listicle"],
    "how_to": ["How-To Promise", "Benefit-Driven", "Listicle"],
    "comparison": ["Comparison", "Benefit-Driven", "How-To Promise"],
    "what_i_learned_from": ["Transformation", "Future Pacing", "Curiosity Gap"],
    "inside_look": ["Secret/Insider", "Social Proof", "Curiosity Gap"],
    "future_thinking": ["Future Pacing", "Time/Urgency", "Secret/Insider"],
    "reader_q_response": ["Question + Benefit", "Social Proof", "Benefit-Driven"],
    "milestone": ["Specific Numbers", "Social Proof", "Time/Urgency"],
}


def get_frameworks_for_template(template_type: str) -> List[HookFramework]:
    """
    Get recommended hook frameworks for a template type.

    Args:
        template_type: Template type name (e.g., "problem_recognition")

    Returns:
        List of recommended HookFramework objects
    """
    # Normalize template type
    normalized_type = template_type.lower().replace(" ", "_").replace("-", "_")

    # Get framework names for this template type
    framework_names = TEMPLATE_FRAMEWORK_MAP.get(normalized_type, [])

    if not framework_names:
        # Default to primary frameworks if no mapping
        return PRIMARY_FRAMEWORKS[:3]

    # Find matching frameworks
    frameworks = []
    for name in framework_names:
        for fw in ALL_FRAMEWORKS:
            if fw.name == name:
                frameworks.append(fw)
                break

    return frameworks if frameworks else PRIMARY_FRAMEWORKS[:3]


def get_framework_by_name(name: str) -> Optional[HookFramework]:
    """
    Get a specific hook framework by name.

    Args:
        name: Framework name (e.g., "Curiosity Gap")

    Returns:
        HookFramework or None if not found
    """
    for fw in ALL_FRAMEWORKS:
        if fw.name.lower() == name.lower():
            return fw
    return None


def get_power_words_for_emotion(emotion: str) -> List[str]:
    """
    Get power words for a specific emotion.

    Args:
        emotion: Emotion type (urgency, exclusivity, value, curiosity, trust)

    Returns:
        List of power words
    """
    return POWER_WORDS_BY_EMOTION.get(emotion.lower(), [])


def get_all_power_words() -> List[str]:
    """Get all power words from all emotions combined."""
    words = []
    for word_list in POWER_WORDS_BY_EMOTION.values():
        words.extend(word_list)
    return list(set(words))


def build_hook_guidance(
    template_type: str,
    platform: str = "linkedin",
    include_examples: bool = True,
) -> str:
    """
    Build hook guidance text for system prompt.

    Args:
        template_type: Template type for framework selection
        platform: Target platform
        include_examples: Whether to include examples

    Returns:
        Hook guidance string for system prompt
    """
    frameworks = get_frameworks_for_template(template_type)

    lines = [
        "\n" + "=" * 60,
        "HOOK WRITING FRAMEWORKS (Professional Copywriting Techniques)",
        "=" * 60,
        "",
        "Use these proven frameworks to craft compelling opening hooks:",
        "",
    ]

    for i, fw in enumerate(frameworks[:3], 1):
        lines.append(f"**Framework {i}: {fw.name}**")
        lines.append(f"   - {fw.description}")
        lines.append(f"   - Template: {fw.template}")
        if include_examples:
            lines.append(f'   - Example: "{fw.example}"')
        lines.append("")

    # Add power words section
    lines.append("**Power Words to Consider:**")
    for emotion, words in list(POWER_WORDS_BY_EMOTION.items())[:3]:
        lines.append(f"   - {emotion.title()}: {', '.join(words[:4])}")

    lines.append("")
    lines.append("-" * 40)
    lines.append("Choose ONE framework for your hook. Make it specific to the client's context.")
    lines.append("-" * 40)

    return "\n".join(lines)
