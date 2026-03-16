"""Voice pattern analyzer for enhanced brand voice guide generation"""

import re
from collections import Counter
from difflib import SequenceMatcher
from typing import Dict, List

from ..config.brand_frameworks import infer_archetype_from_voice_dimensions
from ..models.client_brief import ClientBrief
from ..models.post import Post
from ..models.voice_guide import EnhancedVoiceGuide, VoicePattern
from ..utils.logger import logger
from ..utils.voice_metrics import VoiceMetrics


class VoiceAnalyzer:
    """Analyzes generated posts to extract voice patterns"""

    def __init__(self):
        """Initialize voice analyzer with metrics calculator."""
        self.voice_metrics = VoiceMetrics()

    def analyze_voice_patterns(
        self, posts: List[Post], client_brief: ClientBrief
    ) -> EnhancedVoiceGuide:
        """Main analysis method"""
        logger.info(f"Analyzing {len(posts)} posts")

        hooks = [self._extract_hook(p.content) for p in posts]
        hook_patterns = self._cluster_patterns(hooks, "opening")

        transitions = []
        for post in posts:
            transitions.extend(self._extract_transitions(post.content))
        transition_patterns = self._cluster_patterns(transitions, "transition")

        ctas = [self._extract_cta(p.content) for p in posts if p.has_cta]
        cta_patterns = self._cluster_patterns(ctas, "cta")

        all_text = " ".join([p.content for p in posts])
        key_phrases = self._find_recurring_ngrams(all_text, min_freq=3)

        avg_words = sum(p.word_count for p in posts) / len(posts)
        avg_paragraphs = self._calculate_avg_paragraphs(posts)
        question_rate = sum(1 for p in posts if "?" in p.content) / len(posts)

        tone_score = self._calculate_tone_consistency(posts, client_brief)
        dos = self._generate_dos(hook_patterns, transition_patterns, cta_patterns)
        donts = self._generate_donts(posts, client_brief)
        examples = self._select_best_examples(posts, hook_patterns)
        dominant_tones = self._extract_dominant_tones(posts, client_brief)

        # NEW: Calculate voice metrics from content-creator skill
        logger.info("Calculating advanced voice metrics...")
        readability_score = self.voice_metrics.calculate_readability(all_text)
        voice_dimensions = self.voice_metrics.analyze_voice_dimensions(all_text)
        sentence_analysis = self.voice_metrics.analyze_sentence_variety(all_text)

        # NEW: Determine brand archetype
        archetype = self._determine_archetype(voice_dimensions, client_brief)

        # NEW: Add readability recommendations to dos/donts
        if readability_score < 50:
            donts.append("DON'T: Use overly complex sentences (consider simpler language)")
        elif readability_score > 80:
            dos.append("DO: Maintain accessible, easy-to-read language")

        if sentence_analysis["variety"] == "low":
            dos.append("DO: Vary sentence length for better engagement")

        logger.info(
            f"Voice analysis complete - Archetype: {archetype}, Readability: {readability_score:.1f}"
        )

        # NEW: Generate enhanced voice guide fields from brand-voice-guide skill
        voice_spectrum = self._generate_voice_spectrum(voice_dimensions, readability_score)
        words_to_use, words_to_avoid = self._generate_word_guidelines(all_text, key_phrases)
        tone_by_channel = self._generate_tone_by_channel(archetype, voice_dimensions)
        consistency_checklist = self._generate_consistency_checklist(archetype, dominant_tones)

        return EnhancedVoiceGuide(
            company_name=client_brief.company_name,
            generated_from_posts=len(posts),
            dominant_tones=dominant_tones,
            tone_consistency_score=tone_score,
            common_opening_hooks=hook_patterns[:5],
            common_transitions=transition_patterns[:5],
            common_ctas=cta_patterns[:5],
            key_phrases_used=key_phrases,
            average_word_count=int(avg_words),
            average_paragraph_count=avg_paragraphs,
            question_usage_rate=question_rate,
            dos=dos,
            donts=donts,
            examples=examples,
            # NEW: Voice metrics fields
            average_readability_score=readability_score,
            voice_dimensions=voice_dimensions,
            sentence_variety=sentence_analysis["variety"],
            voice_archetype=archetype,
            # NEW: Brand-voice-guide skill fields
            voice_spectrum=voice_spectrum,
            words_to_use=words_to_use,
            words_to_avoid=words_to_avoid,
            tone_by_channel=tone_by_channel,
            consistency_checklist=consistency_checklist,
        )

    def analyze_voice_samples(
        self, samples: List[str], client_name: str, source: str = "mixed"
    ) -> EnhancedVoiceGuide:
        """
        Analyze client's existing content samples for authentic voice

        This method analyzes real client samples (not generated content) to create
        a voice guide that represents their true writing style.

        Args:
            samples: List of text samples (each 100-2000 words)
            client_name: Client name
            source: Source type (linkedin, blog, twitter, email, mixed)

        Returns:
            Voice guide based on real client samples
        """
        from datetime import datetime

        # Convert samples to Post objects for analysis
        mock_posts = [
            Post(
                content=sample,
                template_id=0,  # Not from a template
                template_name="client_sample",
                variant=idx + 1,
                client_name=client_name,
            )
            for idx, sample in enumerate(samples)
        ]

        # Create minimal brief for analysis
        from src.models.client_brief import ClientBrief

        minimal_brief = ClientBrief(
            company_name=client_name,
            business_description=f"Analyzing uploaded samples from {source}",
            ideal_customer="Unknown - inferring from samples",
            main_problem_solved="Unknown",
        )

        # Use existing voice analysis logic
        voice_guide = self.analyze_voice_patterns(posts=mock_posts, client_brief=minimal_brief)

        # Mark as sample-based (not generated)
        voice_guide.source = "client_samples"
        voice_guide.sample_count = len(samples)
        voice_guide.sample_source = source
        voice_guide.sample_upload_date = datetime.now()

        # Analyze emoji patterns
        combined_text = "\n\n".join(samples)
        emoji_freq, common_emojis = self._analyze_emoji_patterns(combined_text)
        voice_guide.emoji_frequency = emoji_freq
        voice_guide.common_emojis = common_emojis

        # Analyze jargon
        jargon_ratio, industry_terms = self._analyze_jargon(combined_text)
        voice_guide.jargon_ratio = jargon_ratio
        voice_guide.industry_terms = industry_terms

        return voice_guide

    def _analyze_emoji_patterns(self, text: str) -> tuple[float, List[str]]:
        """
        Analyze emoji usage in text

        Returns:
            Tuple of (emojis_per_100_words, list_of_common_emojis)
        """
        import re
        from collections import Counter

        # Emoji regex pattern (basic Unicode ranges)
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map symbols
            "\U0001f1e0-\U0001f1ff"  # flags
            "\U00002702-\U000027b0"  # dingbats
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )

        emojis = emoji_pattern.findall(text)
        word_count = len(text.split())

        if word_count == 0:
            return 0.0, []

        # Calculate frequency (per 100 words)
        emoji_frequency = (len(emojis) / word_count) * 100

        # Get most common emojis
        emoji_counts = Counter(emojis)
        common_emojis = [emoji for emoji, count in emoji_counts.most_common(5)]

        return emoji_frequency, common_emojis

    def _analyze_jargon(self, text: str) -> tuple[float, List[str]]:
        """
        Analyze industry jargon and technical terms

        Returns:
            Tuple of (jargon_ratio, list_of_industry_terms)
        """
        import re
        from collections import Counter

        # Common industry/technical term patterns
        # (This is a simple heuristic - could be improved with NLP)
        jargon_patterns = [
            r"\b[A-Z]{2,}\b",  # Acronyms (ROI, SEO, API)
            r"\b\w+(-\w+)+\b",  # Hyphenated terms (data-driven, real-time)
            r"\b\w+\s+\w+ing\b",  # "-ing" phrases (content marketing, lead generation)
        ]

        all_jargon = []
        for pattern in jargon_patterns:
            matches = re.findall(pattern, text)
            all_jargon.extend(matches)

        # Filter out common non-jargon
        common_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
        }
        jargon_terms = [term for term in all_jargon if term.lower() not in common_words]

        word_count = len(text.split())
        if word_count == 0:
            return 0.0, []

        # Calculate jargon ratio
        jargon_ratio = len(jargon_terms) / word_count

        # Get most common jargon terms
        jargon_counts = Counter(jargon_terms)
        top_terms = [term for term, count in jargon_counts.most_common(10) if count >= 2]

        return jargon_ratio, top_terms

    def _extract_hook(self, content: str) -> str:
        """Extract opening hook (first 1-2 sentences)"""
        sentences = content.split(". ")
        hook = ". ".join(sentences[:2])
        if not hook.endswith("."):
            hook += "."
        return hook.strip()

    def _extract_transitions(self, content: str) -> List[str]:
        """Find transitional phrases"""
        transition_markers = [
            "but here's",
            "here's why",
            "here's the thing",
            "the reality is",
            "in other words",
            "what does this mean",
            "so what",
            "bottom line",
            "that said",
            "however",
            "meanwhile",
        ]

        found = []
        content_lower = content.lower()

        for marker in transition_markers:
            if marker in content_lower:
                sentences = content.split(".")
                for sent in sentences:
                    if marker in sent.lower():
                        found.append(sent.strip())

        return found

    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action"""
        sentences = [s.strip() for s in content.split(".") if s.strip()]
        cta_indicators = ["?", "reply", "comment", "share", "thoughts", "experience", "let me know"]

        for sent in reversed(sentences[-3:]):
            if any(indicator in sent.lower() for indicator in cta_indicators):
                return sent

        return sentences[-1] if sentences else ""

    def _cluster_patterns(self, items: List[str], pattern_type: str) -> List[VoicePattern]:
        """Group similar patterns using fuzzy matching"""
        if not items:
            return []

        counter = Counter(items)
        clusters = []
        seen = set()

        for item, freq in counter.most_common():
            if item in seen or not item.strip():
                continue

            cluster = [item]
            for other_item in counter.keys():
                if other_item != item and other_item not in seen and other_item.strip():
                    similarity = SequenceMatcher(None, item.lower(), other_item.lower()).ratio()
                    if similarity > 0.7:
                        cluster.append(other_item)
                        seen.add(other_item)

            seen.add(item)
            total_freq = sum(counter[c] for c in cluster)

            clusters.append(
                VoicePattern(
                    pattern_type=pattern_type,
                    examples=cluster[:3],
                    frequency=total_freq,
                    description=self._describe_pattern(item, pattern_type),
                )
            )

        return sorted(clusters, key=lambda x: x.frequency, reverse=True)

    def _find_recurring_ngrams(self, text: str, min_freq: int = 3) -> List[str]:
        """Find phrases that appear 3+ times"""
        text = re.sub(r"[^\w\s]", "", text.lower())
        words = text.split()

        ngrams = []
        for n in range(2, 6):
            for i in range(len(words) - n + 1):
                ngram = " ".join(words[i : i + n])
                ngrams.append(ngram)

        counter = Counter(ngrams)
        recurring = [phrase for phrase, count in counter.items() if count >= min_freq]

        filtered: list[str] = []
        for phrase in sorted(recurring, key=len, reverse=True):
            if not any(phrase in longer for longer in filtered):
                filtered.append(phrase)

        return filtered[:10]

    def _calculate_avg_paragraphs(self, posts: List[Post]) -> float:
        """Calculate average paragraph count"""
        paragraph_counts = []
        for post in posts:
            paragraphs = [p for p in post.content.split("\n\n") if p.strip()]
            paragraph_counts.append(len(paragraphs))
        return sum(paragraph_counts) / len(paragraph_counts) if paragraph_counts else 1.0

    def _calculate_tone_consistency(self, posts: List[Post], client_brief: ClientBrief) -> float:
        """Calculate tone consistency score"""
        score = 0.0
        checks = 0

        all_content = " ".join([post.content.lower() for post in posts])

        tone_indicators = {
            "approachable": ["we", "you", "your", "us"],
            "direct": ["simple", "clear", "bottom line", "here's"],
            "authoritative": ["research shows", "data", "studies", "proven"],
            "witty": ["?", "!", "ironically"],
            "data_driven": ["statistic", "%", "number", "data", "metric"],
            "conversational": ["you know", "think about", "imagine", "ever"],
        }

        for tone in client_brief.brand_personality:
            tone_str = str(tone)
            if tone_str in tone_indicators:
                indicators = tone_indicators[tone_str]
                presence = sum(1 for ind in indicators if ind in all_content) / len(indicators)
                score += presence
                checks += 1

        if client_brief.key_phrases:
            phrases_used = sum(
                1 for phrase in client_brief.key_phrases if phrase.lower() in all_content
            )
            score += phrases_used / len(client_brief.key_phrases)
            checks += 1

        return score / checks if checks > 0 else 0.5

    def _extract_dominant_tones(self, posts: List[Post], client_brief: ClientBrief) -> List[str]:
        """Identify top 3 tones"""
        tones = [str(tone) for tone in client_brief.brand_personality]
        return tones[:3] if tones else ["conversational", "professional"]

    def _generate_dos(
        self,
        hook_patterns: List[VoicePattern],
        transition_patterns: List[VoicePattern],
        cta_patterns: List[VoicePattern],
    ) -> List[str]:
        """Generate DO recommendations"""
        dos = []

        if hook_patterns:
            dos.append(
                f"DO: Start posts with {self._generalize_pattern(hook_patterns[0].examples[0])}"
            )
        if transition_patterns:
            dos.append("DO: Use clear transitions to guide readers")
        if cta_patterns:
            dos.append("DO: End with engaging questions or calls-to-action")

        dos.extend(
            [
                "DO: Maintain consistent paragraph length (2-3 sentences)",
                "DO: Use line breaks for readability",
            ]
        )

        return dos

    def _generate_donts(self, posts: List[Post], client_brief: ClientBrief) -> List[str]:
        """Generate DON'T recommendations"""
        donts = []

        if client_brief.tone_to_avoid:
            donts.append(f"DON'T: Use {client_brief.tone_to_avoid} tone")

        donts.extend(
            [
                "DON'T: Start every post the same way",
                "DON'T: Write walls of text without line breaks",
                "DON'T: End posts without a clear CTA or question",
            ]
        )

        avg_length = sum(p.word_count for p in posts) / len(posts)
        if avg_length > 250:
            donts.append("DON'T: Exceed 250-300 words")

        return donts

    def _select_best_examples(
        self, posts: List[Post], hook_patterns: List[VoicePattern]
    ) -> List[str]:
        """Select 3-5 strong post examples"""
        examples = []

        if hook_patterns:
            strong_hooks = hook_patterns[0].examples
            for hook in strong_hooks[:2]:
                for post in posts:
                    if hook in post.content:
                        excerpt = (
                            post.content[:200] + "..." if len(post.content) > 200 else post.content
                        )
                        examples.append(f'Strong hook: "{excerpt}"')
                        break

        cta_posts = [p for p in posts if p.has_cta]
        if cta_posts:
            best_cta = sorted(cta_posts, key=lambda x: x.word_count)[len(cta_posts) // 2]
            excerpt = best_cta.content[-150:]
            examples.append(f'Strong CTA: "...{excerpt}"')

        return examples[:5]

    def _describe_pattern(self, pattern: str, pattern_type: str) -> str:
        """Generate description for a pattern"""
        descriptions = {
            "opening": "Hooks reader attention immediately",
            "transition": "Guides reader through logical progression",
            "cta": "Encourages engagement and response",
        }
        return descriptions.get(pattern_type, "Common pattern in content")

    def _generalize_pattern(self, example: str) -> str:
        """Convert specific example to general pattern"""
        if any(char.isupper() for char in example):
            return "specific examples or case studies"
        elif example.lower().startswith("what if"):
            return "thought-provoking questions"
        elif example.lower().startswith("most"):
            return "statements about common challenges"
        else:
            return "concrete, relatable examples"

    def _determine_archetype(self, voice_dimensions: Dict, client_brief: ClientBrief) -> str:
        """
        Determine brand archetype based on voice dimensions.

        Args:
            voice_dimensions: Voice dimension analysis from VoiceMetrics
            client_brief: Client brief for additional context

        Returns:
            Brand archetype name
        """
        # Extract dominant dimensions
        formality = voice_dimensions.get("formality", {}).get("dominant", "conversational")
        tone = voice_dimensions.get("tone", {}).get("dominant", "friendly")
        perspective = voice_dimensions.get("perspective", {}).get("dominant", "collaborative")

        # Infer archetype from dimensions
        archetype = infer_archetype_from_voice_dimensions(formality, tone, perspective)

        logger.info(
            f"Archetype determination: formality={formality}, tone={tone}, "
            f"perspective={perspective} → {archetype}"
        )

        return archetype

    def _generate_voice_spectrum(
        self, voice_dimensions: Dict, readability_score: float
    ) -> Dict[str, str]:
        """
        Generate voice spectrum positioning based on voice dimensions.

        Returns dictionary with positions on key spectrums.
        """
        spectrum = {}

        # Formal ←→ Casual
        formality = voice_dimensions.get("formality", {}).get("dominant", "conversational")
        if formality == "formal":
            spectrum["formal_casual"] = "Leans formal - professional tone maintained"
        elif formality == "conversational":
            spectrum["formal_casual"] = "Center-casual - approachable but professional"
        else:
            spectrum["formal_casual"] = "Casual - friendly, conversational style"

        # Serious ←→ Playful (based on tone)
        tone = voice_dimensions.get("tone", {}).get("dominant", "friendly")
        if tone in ["authoritative", "urgent"]:
            spectrum["serious_playful"] = "Leans serious - focused, purposeful"
        elif tone in ["friendly", "enthusiastic"]:
            spectrum["serious_playful"] = "Center - warm but not overly casual"
        else:
            spectrum["serious_playful"] = "Leans playful - energetic, engaging"

        # Authoritative ←→ Collaborative
        perspective = voice_dimensions.get("perspective", {}).get("dominant", "collaborative")
        if perspective == "expert":
            spectrum["authoritative_collaborative"] = "Authoritative - positions as expert"
        elif perspective == "collaborative":
            spectrum["authoritative_collaborative"] = "Collaborative - partner approach"
        else:
            spectrum["authoritative_collaborative"] = "Center - guides without preaching"

        # Technical ←→ Simple (based on readability)
        if readability_score < 50:
            spectrum["technical_simple"] = "Leans technical - advanced vocabulary"
        elif readability_score > 70:
            spectrum["technical_simple"] = "Simple - accessible to all readers"
        else:
            spectrum["technical_simple"] = "Center - technical when needed, simple by default"

        # Traditional ←→ Innovative (inferred from tone and perspective)
        if tone in ["authoritative", "urgent"] and perspective == "expert":
            spectrum["traditional_innovative"] = "Traditional - established, proven approaches"
        elif tone in ["enthusiastic", "friendly"]:
            spectrum["traditional_innovative"] = "Innovative - fresh perspectives, new ideas"
        else:
            spectrum["traditional_innovative"] = "Center - respects tradition, embraces innovation"

        return spectrum

    def _generate_word_guidelines(
        self, all_text: str, key_phrases: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Generate lists of words to use and avoid based on analysis.

        Returns tuple of (words_to_use, words_to_avoid).
        """
        # Words to use - extracted from successful patterns
        words_to_use = []

        # Add key phrases that work well
        for phrase in key_phrases[:5]:
            words_to_use.append(phrase)

        # Add common power words found in text
        power_words = ["discover", "proven", "simple", "transform", "achieve", "build"]
        text_lower = all_text.lower()
        for word in power_words:
            if word in text_lower:
                words_to_use.append(word)

        # Words to avoid - common weak/corporate words
        words_to_avoid = [
            "synergy",
            "leverage",
            "utilize",
            "best-in-class",
            "disrupt",
            "paradigm shift",
            "circle back",
            "low-hanging fruit",
        ]

        # Filter to words NOT found in successful content
        words_to_avoid = [w for w in words_to_avoid if w.lower() not in text_lower][:8]

        return words_to_use[:10], words_to_avoid

    def _generate_tone_by_channel(self, archetype: str, voice_dimensions: Dict) -> Dict[str, str]:
        """
        Generate tone guidance for different channels based on archetype.
        """
        tone_guidance = {}

        formality = voice_dimensions.get("formality", {}).get("dominant", "conversational")

        # LinkedIn
        if archetype == "Expert":
            tone_guidance["linkedin"] = (
                "Professional thought leadership. Share insights, data, and industry analysis. Be direct and authoritative."
            )
        elif archetype == "Friend":
            tone_guidance["linkedin"] = (
                "Warm but professional. Share stories and engage conversationally while maintaining credibility."
            )
        else:
            tone_guidance["linkedin"] = (
                "Balanced professional tone. Mix insights with relatable examples."
            )

        # Twitter
        tone_guidance["twitter"] = (
            "Punchy and engaging. Lead with hooks. Use threads for longer content. More casual than LinkedIn."
        )

        # Email
        if formality == "formal":
            tone_guidance["email"] = (
                "Respectful but direct. Clear subject lines. Value-first approach."
            )
        else:
            tone_guidance["email"] = (
                "Conversational and personal. Write like you're speaking to one person."
            )

        # Blog
        tone_guidance["blog"] = (
            "Can be longer-form. Maintain voice consistency but allow for more depth and examples."
        )

        return tone_guidance

    def _generate_consistency_checklist(
        self, archetype: str, dominant_tones: List[str]
    ) -> List[str]:
        """
        Generate voice consistency checklist for content review.
        """
        checklist = [
            "Opening hook grabs attention immediately",
            "Tone matches brand personality throughout",
            "Content provides clear value to reader",
            "Call-to-action is clear and relevant",
            "Line breaks used for readability",
        ]

        # Add archetype-specific checks
        if archetype == "Expert":
            checklist.append("Data or evidence supports key claims")
            checklist.append("Maintains authoritative but accessible tone")
        elif archetype == "Friend":
            checklist.append("Includes relatable examples or stories")
            checklist.append("Language feels warm and genuine")
        elif archetype == "Innovator":
            checklist.append("Offers fresh perspective or new angle")
            checklist.append("Challenges conventional thinking appropriately")
        elif archetype == "Guide":
            checklist.append("Actionable advice is clear and specific")
            checklist.append("Reader knows what to do next")
        elif archetype == "Motivator":
            checklist.append("Inspires action or positive change")
            checklist.append("Energy level matches brand personality")

        # Add tone-specific checks
        if "conversational" in [t.lower() for t in dominant_tones]:
            checklist.append("Reads naturally when spoken aloud")

        return checklist
