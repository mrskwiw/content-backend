"""Keyword Quality Scorer - Evaluates keyword quality for SEO research

Provides objective quality scoring for keywords based on:
- Relevance to business context
- Specificity (not too generic)
- Search volume potential
- Competition level
- Trend momentum
"""

from typing import Any, Dict, List, Optional
from ..models.seo_models import Keyword, KeywordDifficulty, SearchIntent
from ..utils.logger import logger


class KeywordQualityScorer:
    """Score keywords on a 0-100 scale for quality"""

    # Generic/overly broad keywords that should be penalized
    GENERIC_KEYWORDS = {
        "marketing",
        "business",
        "software",
        "service",
        "services",
        "company",
        "solution",
        "solutions",
        "product",
        "products",
        "tool",
        "tools",
        "platform",
        "app",
        "website",
        "online",
        "best",
        "top",
        "good",
        "great",
    }

    # Minimum quality thresholds
    MIN_QUALITY_SCORE = 70  # Keywords below this are considered low quality
    TARGET_HIGH_QUALITY = 5  # Aim for this many high-quality keywords

    def __init__(self, business_context: str, industry: Optional[str] = None):
        """
        Initialize scorer with business context

        Args:
            business_context: Business description for relevance scoring
            industry: Industry for specificity checking
        """
        self.business_context = business_context.lower()
        self.industry = (industry or "").lower()

    def score_keyword(self, keyword: Keyword) -> float:
        """
        Score a keyword on a 0-100 scale

        Scoring factors:
        - Base relevance score (from Keyword model): 0-40 points
        - Specificity (not generic): 0-20 points
        - Volume potential: 0-15 points
        - Difficulty (prefer medium): 0-10 points
        - Trend momentum: 0-10 points
        - Search intent value: 0-5 points

        Args:
            keyword: Keyword object to score

        Returns:
            Quality score (0-100, higher is better)
        """
        score = 0.0

        # 1. Base relevance (0-40 points)
        # Use the keyword's own relevance_score (1-10) and scale it
        relevance_points = (keyword.relevance_score / 10.0) * 40.0
        score += relevance_points

        # 2. Specificity check (0-20 points)
        specificity_points = self._score_specificity(keyword)
        score += specificity_points

        # 3. Volume potential (0-15 points)
        volume_points = self._score_volume(keyword)
        score += volume_points

        # 4. Difficulty balance (0-10 points)
        # Medium difficulty is ideal (sweet spot), low is good, high is penalized
        if keyword.difficulty == KeywordDifficulty.MEDIUM:
            difficulty_points = 10.0
        elif keyword.difficulty == KeywordDifficulty.LOW:
            difficulty_points = 8.0
        else:  # HIGH
            difficulty_points = 3.0
        score += difficulty_points

        # 5. Trend momentum (0-10 points)
        trend_points = self._score_trends(keyword)
        score += trend_points

        # 6. Search intent value (0-5 points)
        # Commercial and transactional intents are most valuable
        intent_values = {
            SearchIntent.TRANSACTIONAL: 5.0,
            SearchIntent.COMMERCIAL: 4.0,
            SearchIntent.INFORMATIONAL: 3.0,
            SearchIntent.NAVIGATIONAL: 2.0,
        }
        intent_points = intent_values.get(keyword.search_intent, 2.0)
        score += intent_points

        # Round to 1 decimal place
        final_score = round(score, 1)

        logger.debug(
            f"Keyword '{keyword.keyword}': "
            f"relevance={relevance_points:.1f}, "
            f"specificity={specificity_points:.1f}, "
            f"volume={volume_points:.1f}, "
            f"difficulty={difficulty_points:.1f}, "
            f"trend={trend_points:.1f}, "
            f"intent={intent_points:.1f} "
            f"→ TOTAL={final_score:.1f}"
        )

        return final_score

    def _score_specificity(self, keyword: Keyword) -> float:
        """
        Score keyword specificity (0-20 points)

        Penalizes generic keywords, rewards specific terms

        Args:
            keyword: Keyword to evaluate

        Returns:
            Specificity score (0-20)
        """
        kw_lower = keyword.keyword.lower()
        words = kw_lower.split()

        # Penalty for generic single-word keywords
        if len(words) == 1:
            if kw_lower in self.GENERIC_KEYWORDS:
                return 0.0  # Highly generic
            else:
                return 10.0  # Specific single word (e.g., "dentistry", "podiatry")

        # Reward for long-tail (3+ words)
        if keyword.long_tail and len(words) >= 3:
            points = 18.0

            # Extra bonus for question-based long-tail
            if keyword.question_based:
                points = 20.0

            return points

        # Multi-word but not long-tail (2 words)
        # Check if it contains generic terms
        generic_count = sum(1 for word in words if word in self.GENERIC_KEYWORDS)

        if generic_count > 0:
            # Penalize for generic words
            return max(5.0, 15.0 - (generic_count * 5.0))
        else:
            # Specific 2-word phrase
            return 15.0

    def _score_volume(self, keyword: Keyword) -> float:
        """
        Score search volume potential (0-15 points)

        Estimates based on volume_estimate string

        Args:
            keyword: Keyword with volume estimate

        Returns:
            Volume score (0-15)
        """
        volume_str = keyword.monthly_volume_estimate.lower()

        # Parse volume ranges
        if "unknown" in volume_str or not volume_str:
            return 5.0  # Neutral score for unknown

        # Extract numbers from ranges like "1K-10K", "100-1K", etc.
        try:
            # High volume (10K+)
            if any(term in volume_str for term in ["10k", "100k", "million", "1m", "50k", "20k"]):
                return 15.0

            # Medium-high volume (1K-10K)
            if any(term in volume_str for term in ["1k", "5k", "2k", "3k"]):
                return 12.0

            # Medium volume (100-1K)
            if any(term in volume_str for term in ["100", "500", "1,000"]):
                return 9.0

            # Low volume (10-100)
            if any(term in volume_str for term in ["10", "50"]):
                return 5.0

            # Very low (<10)
            return 3.0

        except Exception:
            return 5.0  # Default to neutral

    def _score_trends(self, keyword: Keyword) -> float:
        """
        Score trend momentum (0-10 points)

        Rewards rising trends, stable is neutral, declining penalized

        Args:
            keyword: Keyword with trend data

        Returns:
            Trend score (0-10)
        """
        if not keyword.trend_direction:
            return 5.0  # Neutral if no trend data

        # Score based on trend direction
        trend_scores = {
            "rising": 10.0,  # Best - growing interest
            "stable": 6.0,  # Good - consistent demand
            "seasonal": 7.0,  # Decent - predictable spikes
            "declining": 2.0,  # Poor - losing interest
        }

        base_score = trend_scores.get(keyword.trend_direction, 5.0)

        # Bonus for high trend score (Google Trends interest)
        if keyword.trend_score is not None and keyword.trend_score > 70:
            base_score = min(10.0, base_score + 2.0)

        return base_score

    def filter_high_quality(
        self, keywords: List[Keyword], min_score: Optional[float] = None
    ) -> List[Keyword]:
        """
        Filter keywords to only high-quality ones

        Args:
            keywords: List of keywords to filter
            min_score: Minimum quality score (default: MIN_QUALITY_SCORE)

        Returns:
            List of high-quality keywords (scored >= min_score)
        """
        min_threshold = min_score or self.MIN_QUALITY_SCORE

        scored_keywords = []
        for kw in keywords:
            quality_score = self.score_keyword(kw)
            kw.quality_score = quality_score  # Attach score to keyword

            if quality_score >= min_threshold:
                scored_keywords.append(kw)

        # Sort by quality score (highest first)
        scored_keywords.sort(key=lambda k: k.quality_score or 0.0, reverse=True)

        logger.info(
            f"Filtered {len(scored_keywords)}/{len(keywords)} high-quality keywords "
            f"(min score: {min_threshold})"
        )

        return scored_keywords

    def get_keyword_stats(self, keywords: List[Keyword]) -> Dict[str, Any]:
        """
        Get statistics about keyword quality distribution

        Args:
            keywords: List of keywords to analyze

        Returns:
            Dictionary with quality statistics
        """
        if not keywords:
            return {
                "total": 0,
                "avg_quality": 0.0,
                "high_quality_count": 0,
                "medium_quality_count": 0,
                "low_quality_count": 0,
                "top_keywords": [],
            }

        scores = [self.score_keyword(kw) for kw in keywords]
        avg_score = sum(scores) / len(scores)

        high_quality = sum(1 for s in scores if s >= self.MIN_QUALITY_SCORE)
        medium_quality = sum(1 for s in scores if 50 <= s < self.MIN_QUALITY_SCORE)
        low_quality = sum(1 for s in scores if s < 50)

        # Get top 10 keywords by score
        scored_kws = list(zip(keywords, scores))
        scored_kws.sort(key=lambda x: x[1], reverse=True)
        top_keywords = [{"keyword": kw.keyword, "score": score} for kw, score in scored_kws[:10]]

        return {
            "total": len(keywords),
            "avg_quality": round(avg_score, 1),
            "high_quality_count": high_quality,
            "medium_quality_count": medium_quality,
            "low_quality_count": low_quality,
            "top_keywords": top_keywords,
        }
