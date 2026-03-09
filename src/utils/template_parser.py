"""Template Parser Utility

Parses post templates and extracts research dependencies.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config.settings import settings


class TemplateParser:
    """Parse post templates and extract metadata including research dependencies"""

    def __init__(self):
        """Initialize template parser"""
        self.template_path = Path(settings.TEMPLATE_LIBRARY_PATH)

    def parse_all_templates(self) -> Dict[int, Dict[str, Any]]:
        """
        Parse all templates from the library file

        Returns:
            Dict mapping template number to template metadata:
            {
                1: {
                    "number": 1,
                    "title": "The Problem-Recognition Post",
                    "best_for": "Building awareness, getting engagement",
                    "format": "Hook problem → Validate feeling → Hint at solution",
                    "research_dependencies": {
                        "required": ["audience_research"],
                        "recommended": ["icp_workshop", "seo_keyword_research"]
                    }
                },
                ...
            }
        """
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template library not found: {self.template_path}")

        content = self.template_path.read_text(encoding="utf-8")

        # Split by template headers
        template_pattern = r"## TEMPLATE (\d+): (.+?)\n"
        template_sections = re.split(template_pattern, content)

        templates = {}

        # Process templates (skip first element which is file header)
        for i in range(1, len(template_sections), 3):
            if i + 2 >= len(template_sections):
                break

            template_num = int(template_sections[i])
            template_title = template_sections[i + 1].strip()
            template_body = template_sections[i + 2]

            templates[template_num] = self._parse_template_metadata(
                template_num, template_title, template_body
            )

        return templates

    def _parse_template_metadata(self, number: int, title: str, body: str) -> Dict[str, Any]:
        """Parse metadata from a single template section"""
        metadata = {
            "number": number,
            "title": title,
            "best_for": None,
            "format": None,
            "research_dependencies": {"required": [], "recommended": []},
        }

        # Extract "Best for"
        best_for_match = re.search(r"\*\*Best for:\*\*\s*(.+?)(?:\n|\*\*)", body)
        if best_for_match:
            metadata["best_for"] = best_for_match.group(1).strip()

        # Extract "Format"
        format_match = re.search(r"\*\*Format:\*\*\s*(.+?)(?:\n|\*\*)", body)
        if format_match:
            metadata["format"] = format_match.group(1).strip()

        # Extract research dependencies
        research_section_match = re.search(
            r"\*\*Research Tools:\*\*\n(.+?)(?:\n\n|\n```|$)", body, re.DOTALL
        )
        if research_section_match:
            research_text = research_section_match.group(1)
            metadata["research_dependencies"] = self._parse_research_dependencies(research_text)

        return metadata

    def _parse_research_dependencies(self, research_text: str) -> Dict[str, List[str]]:
        """
        Parse research dependencies from the text

        Expected format:
        - **Required:** Tool Name (description)
        - **Recommended:** Tool Name (description), Another Tool (description)
        """
        dependencies: Dict[str, List[str]] = {"required": [], "recommended": []}

        # Parse required tools
        required_match = re.search(r"\*\*Required:\*\*\s*(.+?)(?:\n|-|\*\*|$)", research_text)
        if required_match:
            required_text = required_match.group(1)
            dependencies["required"] = self._extract_tool_names(required_text)

        # Parse recommended tools
        recommended_match = re.search(r"\*\*Recommended:\*\*\s*(.+?)(?:\n|$)", research_text)
        if recommended_match:
            recommended_text = recommended_match.group(1)
            dependencies["recommended"] = self._extract_tool_names(recommended_text)

        return dependencies

    def _extract_tool_names(self, text: str) -> List[str]:
        """
        Extract tool names from dependency text

        Converts tool labels to internal tool names:
        - "Audience Research" → "audience_research"
        - "SEO Keywords" → "seo_keyword_research"
        - "Story Mining" → "story_mining"
        """
        # Map of label keywords to tool names
        tool_mapping = {
            "audience research": "audience_research",
            "seo keyword": "seo_keyword_research",
            "competitive analysis": "competitive_analysis",
            "market trends": "market_trends",
            "story mining": "story_mining",
            "brand archetype": "brand_archetype",
            "icp workshop": "icp_workshop",
            "content gap": "content_gap_analysis",
            "voice analysis": "voice_analysis",
            "platform strategy": "platform_strategy",
            "content calendar": "content_calendar",
            "content audit": "content_audit",
        }

        tools = []
        text_lower = text.lower()

        for label, tool_name in tool_mapping.items():
            if label in text_lower:
                if tool_name not in tools:  # Avoid duplicates
                    tools.append(tool_name)

        return tools

    def get_template_dependencies(self, template_number: int) -> Optional[Dict[str, List[str]]]:
        """
        Get research dependencies for a specific template

        Args:
            template_number: Template number (1-15)

        Returns:
            Dict with "required" and "recommended" lists, or None if template not found
        """
        templates = self.parse_all_templates()
        template = templates.get(template_number)

        if not template:
            return None

        deps: Dict[str, List[str]] = template["research_dependencies"]
        return deps


# Global instance
template_parser = TemplateParser()
