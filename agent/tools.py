"""
Agent tools - wrappers for existing CLI commands and operations

Security (TR-003): Input validation added to prevent command injection.
All user-controlled inputs are validated before use in subprocess calls.

Lazy Loading Strategy:
- EAGER (loaded at init): ProjectDatabase - needed for answering questions
- LAZY (loaded on first use): Skills, Backend API, AI Agents, Research Tools

This minimizes startup time while keeping database queries fast.
"""

import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, TYPE_CHECKING

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# EAGER: ProjectDatabase for answering questions from local DB
from src.database.project_db import ProjectDatabase

# TYPE_CHECKING: Import types for hints without runtime cost
if TYPE_CHECKING:
    from src.utils.skill_loader import SkillLoader, Skill

logger = logging.getLogger(__name__)


# =============================================================================
# INPUT VALIDATION (TR-003: Command Injection Prevention)
# =============================================================================

# Allowed values for constrained inputs
ALLOWED_PLATFORMS = {"linkedin", "twitter", "facebook", "blog", "email"}
ALLOWED_SOURCES = {"linkedin", "blog", "twitter", "mixed", "email", "website"}
ALLOWED_REPORT_TYPES = {"summary", "detailed", "csv", "json"}

# Validation patterns
# Client names: alphanumeric, spaces, hyphens, underscores, apostrophes, periods
CLIENT_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9\s\-_'.]+$")
# Project IDs: alphanumeric, hyphens, underscores (typical UUID or slug format)
PROJECT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9\-_]+$")
# File patterns for glob: alphanumeric, wildcards, dots, hyphens, underscores
FILE_PATTERN_PATTERN = re.compile(r"^[a-zA-Z0-9\*\?\.\-_/\\]+$")


class InputValidationError(ValueError):
    """Raised when input validation fails."""

    pass


def validate_client_name(client_name: str) -> str:
    """
    Validate client name to prevent injection attacks.

    Args:
        client_name: The client name to validate

    Returns:
        Sanitized client name

    Raises:
        InputValidationError: If validation fails
    """
    if not client_name or not isinstance(client_name, str):
        raise InputValidationError("Client name is required and must be a string")

    client_name = client_name.strip()

    if len(client_name) < 1 or len(client_name) > 100:
        raise InputValidationError("Client name must be 1-100 characters")

    if not CLIENT_NAME_PATTERN.match(client_name):
        raise InputValidationError(
            "Client name contains invalid characters. "
            "Only letters, numbers, spaces, hyphens, underscores, apostrophes, and periods allowed."
        )

    return client_name


def validate_project_id(project_id: str) -> str:
    """
    Validate project ID format.

    Args:
        project_id: The project ID to validate

    Returns:
        Validated project ID

    Raises:
        InputValidationError: If validation fails
    """
    if not project_id or not isinstance(project_id, str):
        raise InputValidationError("Project ID is required and must be a string")

    project_id = project_id.strip()

    if len(project_id) < 1 or len(project_id) > 100:
        raise InputValidationError("Project ID must be 1-100 characters")

    if not PROJECT_ID_PATTERN.match(project_id):
        raise InputValidationError(
            "Project ID contains invalid characters. "
            "Only letters, numbers, hyphens, and underscores allowed."
        )

    return project_id


def validate_platform(platform: str) -> str:
    """
    Validate platform is in allowed list.

    Args:
        platform: The platform to validate

    Returns:
        Validated platform (lowercase)

    Raises:
        InputValidationError: If validation fails
    """
    if not platform or not isinstance(platform, str):
        raise InputValidationError("Platform is required and must be a string")

    platform = platform.strip().lower()

    if platform not in ALLOWED_PLATFORMS:
        raise InputValidationError(
            f"Invalid platform '{platform}'. Allowed: {', '.join(sorted(ALLOWED_PLATFORMS))}"
        )

    return platform


def validate_source(source: str) -> str:
    """
    Validate source is in allowed list.

    Args:
        source: The source to validate

    Returns:
        Validated source (lowercase)

    Raises:
        InputValidationError: If validation fails
    """
    if not source or not isinstance(source, str):
        raise InputValidationError("Source is required and must be a string")

    source = source.strip().lower()

    if source not in ALLOWED_SOURCES:
        raise InputValidationError(
            f"Invalid source '{source}'. Allowed: {', '.join(sorted(ALLOWED_SOURCES))}"
        )

    return source


def validate_report_type(report_type: str) -> str:
    """
    Validate report type is in allowed list.

    Args:
        report_type: The report type to validate

    Returns:
        Validated report type (lowercase)

    Raises:
        InputValidationError: If validation fails
    """
    if not report_type or not isinstance(report_type, str):
        raise InputValidationError("Report type is required and must be a string")

    report_type = report_type.strip().lower()

    if report_type not in ALLOWED_REPORT_TYPES:
        raise InputValidationError(
            f"Invalid report type '{report_type}'. Allowed: {', '.join(sorted(ALLOWED_REPORT_TYPES))}"
        )

    return report_type


def validate_num_posts(num_posts: int) -> int:
    """
    Validate number of posts is in reasonable range.

    Args:
        num_posts: Number of posts to generate

    Returns:
        Validated number

    Raises:
        InputValidationError: If validation fails
    """
    if not isinstance(num_posts, int):
        try:
            num_posts = int(num_posts)
        except (ValueError, TypeError):
            raise InputValidationError("Number of posts must be an integer")

    if num_posts < 1 or num_posts > 100:
        raise InputValidationError("Number of posts must be between 1 and 100")

    return num_posts


def validate_file_path(file_path: str, base_dir: Path) -> Path:
    """
    Validate file path is within allowed directory (prevents path traversal).

    Args:
        file_path: The file path to validate
        base_dir: The base directory paths must be within

    Returns:
        Resolved Path object

    Raises:
        InputValidationError: If validation fails
    """
    if not file_path or not isinstance(file_path, str):
        raise InputValidationError("File path is required and must be a string")

    # Resolve the path to handle .. and symlinks
    try:
        resolved = Path(file_path).resolve()
        base_resolved = base_dir.resolve()

        # Check if the resolved path is within the base directory
        # Use is_relative_to for Python 3.9+
        try:
            resolved.relative_to(base_resolved)
        except ValueError:
            raise InputValidationError(
                f"File path must be within the project directory. "
                f"Path '{file_path}' resolves outside allowed area."
            )

        return resolved

    except Exception as e:
        if isinstance(e, InputValidationError):
            raise
        raise InputValidationError(f"Invalid file path: {str(e)}")


def validate_directory(directory: str, base_dir: Path) -> Path:
    """
    Validate directory is within allowed base directory.

    Args:
        directory: The directory to validate
        base_dir: The base directory that must contain the target

    Returns:
        Resolved Path object

    Raises:
        InputValidationError: If validation fails
    """
    if not directory or not isinstance(directory, str):
        raise InputValidationError("Directory is required and must be a string")

    # Resolve the path
    try:
        target = (base_dir / directory).resolve()
        base_resolved = base_dir.resolve()

        # Check if target is within base
        try:
            target.relative_to(base_resolved)
        except ValueError:
            raise InputValidationError(
                f"Directory must be within the project. "
                f"'{directory}' resolves outside allowed area."
            )

        return target

    except Exception as e:
        if isinstance(e, InputValidationError):
            raise
        raise InputValidationError(f"Invalid directory: {str(e)}")


def validate_file_pattern(pattern: str) -> str:
    """
    Validate file search pattern.

    Args:
        pattern: Glob pattern to validate

    Returns:
        Validated pattern

    Raises:
        InputValidationError: If validation fails
    """
    if not pattern or not isinstance(pattern, str):
        raise InputValidationError("Pattern is required and must be a string")

    pattern = pattern.strip()

    if len(pattern) > 100:
        raise InputValidationError("Pattern must be 100 characters or less")

    if not FILE_PATTERN_PATTERN.match(pattern):
        raise InputValidationError(
            "Pattern contains invalid characters. "
            "Only alphanumeric, wildcards (*, ?), dots, hyphens, underscores, and path separators allowed."
        )

    return pattern


class AgentTools:
    """Tools available to the agent for executing operations.

    Lazy Loading Strategy:
    ----------------------
    EAGER (loaded at __init__):
    - ProjectDatabase: Required for answering questions from local DB

    LAZY (loaded on first use):
    - SkillLoader & Skills: Loaded when skill methods are called
    - Backend API (SessionLocal, crud): Imported inside API methods
    - AI Agents (BriefParser, etc.): Imported inside agent methods
    - Research Service: Imported inside research methods

    This ensures fast startup while keeping database queries responsive.
    """

    def __init__(self):
        # EAGER: Local database for answering questions
        self.db = ProjectDatabase()
        self.project_dir = Path(__file__).parent.parent

        # LAZY: Skills (loaded on first access)
        self._skill_loader: Optional["SkillLoader"] = None
        self._loaded_skills: Dict[str, "Skill"] = {}
        self._available_skills: Optional[List[str]] = None

        # LAZY: Backend database session factory (loaded on first API call)
        self._backend_session_factory = None

        logger.info("AgentTools initialized (non-essential tools will be lazy-loaded)")

    # =========================================================================
    # LAZY LOADERS
    # =========================================================================

    @property
    def skill_loader(self) -> "SkillLoader":
        """Lazy-load the skill loader on first access."""
        if self._skill_loader is None:
            from src.utils.skill_loader import SkillLoader
            self._skill_loader = SkillLoader()
            logger.debug("SkillLoader initialized (lazy)")
        return self._skill_loader

    def _get_backend_session(self):
        """Lazy-load backend database session factory."""
        if self._backend_session_factory is None:
            from backend.database import SessionLocal
            self._backend_session_factory = SessionLocal
            logger.debug("Backend SessionLocal initialized (lazy)")
        return self._backend_session_factory()

    def _get_available_skill_names(self) -> List[str]:
        """Get available skill names (cached after first call)."""
        if self._available_skills is None:
            from src.utils.skill_loader import list_skills
            self._available_skills = list_skills()
            logger.debug(f"Available skills discovered: {self._available_skills}")
        return self._available_skills

    def _get_skill(self, skill_name: str) -> Optional["Skill"]:
        """
        Lazy-load a skill on first access.

        Args:
            skill_name: Name of the skill to load

        Returns:
            Skill object or None if not found
        """
        skill_name = skill_name.strip().lower()

        # Check if already loaded
        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]

        # Try to load the skill (lazy import)
        from src.utils.skill_loader import load_skill
        skill = load_skill(skill_name)
        if skill:
            self._loaded_skills[skill_name] = skill
            logger.info(f"Lazy-loaded skill: {skill_name} v{skill.metadata.version}")
            return skill

        logger.warning(f"Skill '{skill_name}' not found")
        return None

    # ============================================================================
    # SKILL ACCESS TOOLS
    # ============================================================================

    def get_available_skills(self) -> Dict[str, Any]:
        """
        List all available skills the agent can access.

        Uses lazy loading - only loads skill summaries, not full skills.

        Returns:
            Dictionary with skill names, descriptions, and loaded status.
        """
        try:
            available = self._get_available_skill_names()
            skills_info = []

            for skill_name in available:
                # Check if already loaded (without triggering a load)
                if skill_name in self._loaded_skills:
                    skill = self._loaded_skills[skill_name]
                    skills_info.append({
                        "name": skill_name,
                        "description": skill.metadata.description,
                        "version": skill.metadata.version,
                        "category": skill.metadata.category,
                        "loaded": True,
                        "references": list(skill.references.keys()),
                        "scripts": list(skill.scripts.keys()),
                    })
                else:
                    # Get summary without fully loading the skill (lazy)
                    summary = self.skill_loader.get_skill_summary(skill_name)
                    if summary:
                        skills_info.append({
                            "name": skill_name,
                            "description": summary.get("description", ""),
                            "version": summary.get("version", ""),
                            "category": summary.get("category", ""),
                            "loaded": False,
                            "references": summary.get("references", []),
                            "scripts": summary.get("scripts", []),
                        })

            return {
                "success": True,
                "skills": skills_info,
                "count": len(skills_info),
            }

        except Exception as e:
            logger.error(f"Error listing skills: {e}")
            return {"success": False, "error": str(e), "skills": []}

    def get_skill_reference(self, skill_name: str, reference_name: str) -> Dict[str, Any]:
        """
        Get a specific reference document from a skill.

        Uses lazy loading - skill is loaded on first access.

        Args:
            skill_name: Name of the skill (e.g., "content-creator")
            reference_name: Name of the reference (without .md extension)

        Returns:
            Dictionary with reference content or error.
        """
        try:
            # Validate skill name
            if not skill_name or not isinstance(skill_name, str):
                return {"success": False, "error": "Skill name is required"}

            # Lazy load the skill
            skill = self._get_skill(skill_name)
            if not skill:
                return {"success": False, "error": f"Skill '{skill_name}' not found"}

            # Get the reference
            content = skill.get_reference(reference_name)
            if content is None:
                available_refs = list(skill.references.keys())
                return {
                    "success": False,
                    "error": f"Reference '{reference_name}' not found in skill '{skill_name}'",
                    "available_references": available_refs,
                }

            return {
                "success": True,
                "skill_name": skill_name,
                "reference_name": reference_name,
                "content": content,
                "length": len(content),
            }

        except Exception as e:
            logger.error(f"Error getting skill reference: {e}")
            return {"success": False, "error": str(e)}

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific skill.

        Uses lazy loading - skill is loaded on first access.

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with skill metadata and documentation.
        """
        try:
            if not skill_name or not isinstance(skill_name, str):
                return {"success": False, "error": "Skill name is required"}

            # Lazy load the skill
            skill = self._get_skill(skill_name)
            if not skill:
                return {"success": False, "error": f"Skill '{skill_name}' not found"}

            return {
                "success": True,
                "name": skill.metadata.name,
                "description": skill.metadata.description,
                "version": skill.metadata.version,
                "author": skill.metadata.author,
                "category": skill.metadata.category,
                "domain": skill.metadata.domain,
                "documentation": skill.documentation[:2000] + "..." if len(skill.documentation) > 2000 else skill.documentation,
                "references": list(skill.references.keys()),
                "scripts": list(skill.scripts.keys()),
                "assets": list(skill.assets.keys()),
                "tech_stack": skill.metadata.tech_stack,
                "python_tools": skill.metadata.python_tools,
            }

        except Exception as e:
            logger.error(f"Error getting skill info: {e}")
            return {"success": False, "error": str(e)}

    def get_all_skill_references(self, skill_name: str) -> Dict[str, Any]:
        """
        Get all reference documents from a skill.

        Uses lazy loading - skill is loaded on first access.

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with all reference contents.
        """
        try:
            if not skill_name or not isinstance(skill_name, str):
                return {"success": False, "error": "Skill name is required"}

            # Lazy load the skill
            skill = self._get_skill(skill_name)
            if not skill:
                return {"success": False, "error": f"Skill '{skill_name}' not found"}

            references = skill.get_all_references()

            return {
                "success": True,
                "skill_name": skill_name,
                "references": references,
                "count": len(references),
            }

        except Exception as e:
            logger.error(f"Error getting all skill references: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # RESEARCH TOOLS
    # ============================================================================

    # Available research tools with pricing
    RESEARCH_TOOLS = {
        "voice_analysis": {"price": 400, "description": "Extract exact writing patterns from voice samples"},
        "brand_archetype": {"price": 300, "description": "Identify brand personality type and voice characteristics"},
        "seo_keyword_research": {"price": 400, "description": "Discover high-value keywords for content"},
        "competitive_analysis": {"price": 500, "description": "Map competitor content strategies"},
        "content_gap_analysis": {"price": 600, "description": "Find untapped content opportunities"},
        "market_trends_research": {"price": 600, "description": "Industry insights and trends analysis"},
        "audience_research": {"price": 400, "description": "Deep audience profiling and insights"},
        "content_calendar": {"price": 300, "description": "Strategic content scheduling"},
        "platform_strategy": {"price": 300, "description": "Channel-specific tactics"},
        "icp_workshop": {"price": 600, "description": "Define ideal customer profile"},
        "content_audit": {"price": 400, "description": "Evaluate existing content performance"},
        "story_mining": {"price": 500, "description": "Extract compelling client stories"},
    }

    def list_research_tools(self) -> Dict[str, Any]:
        """
        List all available research tools with pricing.

        Returns:
            Dictionary with tool names, descriptions, and prices.
        """
        return {
            "success": True,
            "tools": [
                {"name": name, **info}
                for name, info in self.RESEARCH_TOOLS.items()
            ],
            "count": len(self.RESEARCH_TOOLS),
            "total_value": sum(t["price"] for t in self.RESEARCH_TOOLS.values()),
        }

    async def run_research_tool(
        self,
        tool_name: str,
        client_name: str,
        project_id: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a research tool for a client/project.

        Args:
            tool_name: Name of the research tool (e.g., "voice_analysis", "seo_keyword_research")
            client_name: Client name for context
            project_id: Project ID to associate results with
            params: Optional tool-specific parameters

        Returns:
            Dictionary with research results or error.

        Research Tools Available:
        - voice_analysis ($400): Extract writing patterns from samples
        - brand_archetype ($300): Identify brand personality type
        - seo_keyword_research ($400): Discover high-value keywords
        - competitive_analysis ($500): Map competitor strategies
        - content_gap_analysis ($600): Find untapped opportunities
        - market_trends_research ($600): Industry insights
        - audience_research ($400): Deep audience profiling
        - content_calendar ($300): Strategic scheduling
        - platform_strategy ($300): Channel-specific tactics
        - icp_workshop ($600): Define ideal customer
        - content_audit ($400): Evaluate existing content
        - story_mining ($500): Extract client stories
        """
        try:
            # Validate inputs
            if not tool_name or tool_name not in self.RESEARCH_TOOLS:
                available = list(self.RESEARCH_TOOLS.keys())
                return {
                    "success": False,
                    "error": f"Unknown research tool '{tool_name}'. Available: {available}",
                }

            client_name = validate_client_name(client_name)
            project_id = validate_project_id(project_id)

            logger.info(f"Running research tool '{tool_name}' for {client_name} (project: {project_id})")

            # Try to use the research service
            try:
                from backend.services.research_service import research_service
                from backend.services import crud

                db = self._get_backend_session()
                try:
                    # Get client ID from name
                    clients = crud.list_clients(db)
                    client = next((c for c in clients if c.name == client_name), None)

                    if not client:
                        return {
                            "success": False,
                            "error": f"Client '{client_name}' not found in database",
                        }

                    # Execute research tool
                    result = await research_service.execute_research_tool(
                        db=db,
                        project_id=project_id,
                        client_id=client.id,
                        tool_name=tool_name,
                        params=params or {},
                    )

                    return {
                        "success": result.get("success", False),
                        "tool_name": tool_name,
                        "client_name": client_name,
                        "project_id": project_id,
                        "price": self.RESEARCH_TOOLS[tool_name]["price"],
                        "outputs": result.get("outputs", {}),
                        "metadata": result.get("metadata", {}),
                        "error": result.get("error"),
                    }

                finally:
                    db.close()

            except ImportError as e:
                # Research service not available - return informative error
                logger.warning(f"Research service not available: {e}")
                return {
                    "success": False,
                    "error": "Research tools require backend service. Start the API server first.",
                    "hint": "Run: uvicorn backend.main:app --reload --port 8000",
                }

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Error running research tool: {e}")
            return {"success": False, "error": str(e)}

    def get_research_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific research tool.

        Args:
            tool_name: Name of the research tool

        Returns:
            Dictionary with tool details, use cases, and required inputs.
        """
        if tool_name not in self.RESEARCH_TOOLS:
            return {
                "success": False,
                "error": f"Unknown tool '{tool_name}'",
                "available": list(self.RESEARCH_TOOLS.keys()),
            }

        tool_info = self.RESEARCH_TOOLS[tool_name]

        # Add detailed use cases and parameters per tool
        tool_details = {
            "voice_analysis": {
                "use_cases": ["Match client writing style", "Maintain consistency", "Train team on voice"],
                "required_params": ["content_samples"],
                "optional_params": [],
                "output_formats": ["json", "markdown"],
            },
            "brand_archetype": {
                "use_cases": ["Define brand personality", "Guide content tone", "Align messaging"],
                "required_params": [],
                "optional_params": ["brand_values", "tone_preference"],
                "output_formats": ["json", "markdown"],
            },
            "seo_keyword_research": {
                "use_cases": ["Improve search rankings", "Content planning", "Competitive positioning"],
                "required_params": ["main_topics"],
                "optional_params": ["industry", "target_keywords"],
                "output_formats": ["json", "markdown", "csv"],
            },
            "competitive_analysis": {
                "use_cases": ["Benchmark against competitors", "Find gaps", "Differentiation strategy"],
                "required_params": ["competitors"],
                "optional_params": [],
                "output_formats": ["json", "markdown"],
            },
            "content_gap_analysis": {
                "use_cases": ["Find missed topics", "Content opportunities", "Audience needs"],
                "required_params": [],
                "optional_params": ["current_content_topics"],
                "output_formats": ["json", "markdown"],
            },
            "market_trends_research": {
                "use_cases": ["Industry insights", "Trend identification", "Future planning"],
                "required_params": [],
                "optional_params": ["industry"],
                "output_formats": ["json", "markdown"],
            },
            "audience_research": {
                "use_cases": ["Audience profiling", "Persona development", "Pain point mapping"],
                "required_params": [],
                "optional_params": [],
                "output_formats": ["json", "markdown"],
            },
            "content_calendar": {
                "use_cases": ["Strategic scheduling", "Content mix planning", "Consistency"],
                "required_params": [],
                "optional_params": ["posts_per_week", "start_date"],
                "output_formats": ["json", "markdown", "csv", "ical"],
            },
            "platform_strategy": {
                "use_cases": ["Platform optimization", "Channel tactics", "Format guidance"],
                "required_params": [],
                "optional_params": ["platforms"],
                "output_formats": ["json", "markdown"],
            },
            "icp_workshop": {
                "use_cases": ["Define ideal customer", "Sales alignment", "Messaging focus"],
                "required_params": [],
                "optional_params": [],
                "output_formats": ["json", "markdown"],
            },
            "content_audit": {
                "use_cases": ["Evaluate existing content", "Performance analysis", "Optimization"],
                "required_params": [],
                "optional_params": ["content_urls"],
                "output_formats": ["json", "markdown", "csv"],
            },
            "story_mining": {
                "use_cases": ["Extract client stories", "Case studies", "Social proof"],
                "required_params": [],
                "optional_params": ["story_prompts"],
                "output_formats": ["json", "markdown"],
            },
        }

        details = tool_details.get(tool_name, {})

        return {
            "success": True,
            "name": tool_name,
            "description": tool_info["description"],
            "price": tool_info["price"],
            **details,
        }

    # ============================================================================
    # DIRECT AI AGENT ACCESS
    # ============================================================================

    def parse_brief_direct(self, brief_text: str) -> Dict[str, Any]:
        """
        Parse a client brief directly using BriefParserAgent.

        This provides direct access to the brief parsing agent without
        going through the CLI wrapper.

        Args:
            brief_text: Raw text from client brief

        Returns:
            Dictionary with parsed brief data or error.
        """
        try:
            from src.agents.brief_parser import BriefParserAgent

            agent = BriefParserAgent()
            client_brief = agent.parse_brief(brief_text)

            return {
                "success": True,
                "parsed_brief": client_brief.model_dump(),
                "company_name": client_brief.company_name,
                "platforms": [p.value for p in client_brief.target_platforms],
            }

        except Exception as e:
            logger.error(f"Brief parsing failed: {e}")
            return {"success": False, "error": str(e)}

    def classify_client_direct(self, brief_text: str) -> Dict[str, Any]:
        """
        Classify a client type directly using ClientClassifier.

        This helps determine which templates are best suited for the client.

        Args:
            brief_text: Raw text from client brief (will be parsed first)

        Returns:
            Dictionary with client type, confidence, and reasoning.
        """
        try:
            from src.agents.brief_parser import BriefParserAgent
            from src.agents.client_classifier import ClientClassifier

            # First parse the brief
            parser = BriefParserAgent()
            client_brief = parser.parse_brief(brief_text)

            # Then classify
            classifier = ClientClassifier()
            client_type, confidence = classifier.classify_client(client_brief)
            reasoning = classifier.get_classification_reasoning(client_brief, client_type, confidence)

            return {
                "success": True,
                "client_type": client_type.value,
                "confidence": confidence,
                "reasoning": reasoning,
                "company_name": client_brief.company_name,
            }

        except Exception as e:
            logger.error(f"Client classification failed: {e}")
            return {"success": False, "error": str(e)}

    def validate_posts_direct(
        self,
        project_id: str,
        client_name: str,
    ) -> Dict[str, Any]:
        """
        Run QA validation on posts directly using QAAgent.

        This provides detailed quality validation results without
        regenerating any posts.

        Args:
            project_id: Project ID to validate posts for
            client_name: Client name for the report

        Returns:
            Dictionary with QA report data.
        """
        try:
            project_id = validate_project_id(project_id)
            client_name = validate_client_name(client_name)

            # Try to get posts from database
            try:
                from backend.models import Post as PostModel
                from src.models.post import Post

                db = self._get_backend_session()
                try:
                    db_posts = db.query(PostModel).filter(PostModel.project_id == project_id).all()

                    if not db_posts:
                        return {"success": False, "error": f"No posts found for project {project_id}"}

                    # Convert to src Post objects
                    posts = [
                        Post(
                            content=p.content,
                            template_name=p.template_name or "Unknown",
                            word_count=p.word_count or len(p.content.split()),
                            has_cta=p.has_cta or False,
                            target_platform=p.target_platform,
                        )
                        for p in db_posts
                    ]

                finally:
                    db.close()

            except ImportError:
                return {
                    "success": False,
                    "error": "Database access requires backend service",
                }

            # Run QA validation
            from src.agents.qa_agent import QAAgent

            qa_agent = QAAgent()
            qa_report = qa_agent.validate_posts(posts, client_name)

            return {
                "success": True,
                "overall_passed": qa_report.overall_passed,
                "quality_score": qa_report.quality_score,
                "hook_validation": qa_report.hook_validation,
                "cta_validation": qa_report.cta_validation,
                "length_validation": qa_report.length_validation,
                "issues": qa_report.all_issues[:10],  # First 10 issues
                "total_issues": len(qa_report.all_issues),
                "posts_validated": len(posts),
            }

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"QA validation failed: {e}")
            return {"success": False, "error": str(e)}

    def analyze_voice_direct(
        self,
        project_id: str,
        brief_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze voice patterns directly using VoiceAnalyzer.

        This extracts detailed voice characteristics from generated posts.

        Args:
            project_id: Project ID to analyze posts for
            brief_text: Optional brief text (if not provided, uses stored brief)

        Returns:
            Dictionary with voice analysis results.
        """
        try:
            project_id = validate_project_id(project_id)

            # Get posts from database
            try:
                from backend.services import crud
                from backend.models import Post as PostModel
                from src.models.post import Post
                from src.models.client_brief import ClientBrief, Platform

                db = self._get_backend_session()
                try:
                    db_posts = db.query(PostModel).filter(PostModel.project_id == project_id).all()

                    if not db_posts:
                        return {"success": False, "error": f"No posts found for project {project_id}"}

                    # Convert to src Post objects
                    posts = [
                        Post(
                            content=p.content,
                            template_name=p.template_name or "Unknown",
                            word_count=p.word_count or len(p.content.split()),
                            has_cta=p.has_cta or False,
                            target_platform=p.target_platform,
                        )
                        for p in db_posts
                    ]

                    # Get project and client data for brief
                    project = crud.get_project(db, project_id)
                    if project:
                        client = crud.get_client(db, project.client_id)
                        # Create minimal client brief
                        client_brief = ClientBrief(
                            company_name=client.name if client else "Unknown",
                            business_description=client.business_description or "" if client else "",
                            ideal_customer=client.ideal_customer or "" if client else "",
                            main_problem_solved=client.main_problem_solved or "" if client else "",
                            target_platforms=[Platform.LINKEDIN],
                        )
                    else:
                        # Fallback brief
                        client_brief = ClientBrief(
                            company_name="Unknown",
                            business_description="",
                            ideal_customer="",
                            main_problem_solved="",
                            target_platforms=[Platform.LINKEDIN],
                        )

                finally:
                    db.close()

            except ImportError:
                return {
                    "success": False,
                    "error": "Database access requires backend service",
                }

            # Run voice analysis
            from src.agents.voice_analyzer import VoiceAnalyzer

            analyzer = VoiceAnalyzer()
            voice_guide = analyzer.analyze_voice_patterns(posts, client_brief)

            return {
                "success": True,
                "company_name": voice_guide.company_name,
                "posts_analyzed": voice_guide.generated_from_posts,
                "dominant_tones": voice_guide.dominant_tones,
                "tone_consistency_score": voice_guide.tone_consistency_score,
                "average_readability_score": voice_guide.average_readability_score,
                "voice_archetype": voice_guide.voice_archetype,
                "voice_dimensions": voice_guide.voice_dimensions,
                "common_opening_hooks": [p.pattern for p in voice_guide.common_opening_hooks[:3]],
                "common_ctas": [p.pattern for p in voice_guide.common_ctas[:3]],
                "dos": voice_guide.dos[:5],
                "donts": voice_guide.donts[:5],
                "key_phrases": voice_guide.key_phrases_used[:10],
            }

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Voice analysis failed: {e}")
            return {"success": False, "error": str(e)}

    def list_ai_agents(self) -> Dict[str, Any]:
        """
        List all available AI agents with their capabilities.

        Returns:
            Dictionary with agent names and descriptions.
        """
        agents = [
            {
                "name": "brief_parser",
                "method": "parse_brief_direct",
                "description": "Parse raw client brief text into structured data",
                "input": "brief_text (raw text)",
                "output": "Structured ClientBrief with company, audience, pain points",
            },
            {
                "name": "client_classifier",
                "method": "classify_client_direct",
                "description": "Classify client type for optimal template selection",
                "input": "brief_text (raw text)",
                "output": "ClientType (B2B_SAAS, AGENCY, COACH, CREATOR), confidence score",
            },
            {
                "name": "qa_agent",
                "method": "validate_posts_direct",
                "description": "Run quality validation on generated posts",
                "input": "project_id, client_name",
                "output": "QAReport with hooks, CTAs, length validation",
            },
            {
                "name": "voice_analyzer",
                "method": "analyze_voice_direct",
                "description": "Analyze voice patterns from generated posts",
                "input": "project_id",
                "output": "VoiceGuide with tones, archetypes, readability",
            },
        ]

        return {
            "success": True,
            "agents": agents,
            "count": len(agents),
            "note": "Use these methods for direct agent access without CLI wrappers",
        }

    # ============================================================================
    # PROJECT MANAGEMENT TOOLS
    # ============================================================================

    async def generate_posts(
        self, client_name: str, brief_path: str, num_posts: int = 30, platform: str = "linkedin"
    ) -> Dict[str, Any]:
        """
        Generate posts for a client.

        Wraps: python 03_post_generator.py generate [brief] -c [client] -n [num]

        Security (TR-003): All inputs validated before subprocess execution.
        """
        # Validate all inputs before subprocess execution
        try:
            client_name = validate_client_name(client_name)
            platform = validate_platform(platform)
            num_posts = validate_num_posts(num_posts)
            validated_brief_path = validate_file_path(brief_path, self.project_dir)
        except InputValidationError as e:
            logger.warning(f"Input validation failed in generate_posts: {e}")
            return {"success": False, "error": str(e), "message": "Validation failed"}

        cmd = [
            sys.executable,
            str(self.project_dir / "03_post_generator.py"),
            "generate",
            str(validated_brief_path),
            "-c",
            client_name,
            "-n",
            str(num_posts),
            "--platform",
            platform,
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_dir),
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                # Extract project ID from output
                project_id = self._extract_project_id(stdout)

                return {
                    "success": True,
                    "message": f"Generated {num_posts} posts for {client_name}",
                    "project_id": project_id,
                    "output": stdout,
                }
            else:
                return {"success": False, "error": stderr or stdout, "message": "Generation failed"}

        except Exception as e:
            logger.error(f"Exception in generate_posts: {e}")
            return {"success": False, "error": str(e), "message": "Exception during generation"}

    def list_projects(self, client_name: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
        """
        List projects, optionally filtered by client.

        Wraps: python 03_post_generator.py list-projects

        Security (TR-003): Client name validated if provided.
        """
        try:
            # Validate client_name if provided
            if client_name:
                try:
                    client_name = validate_client_name(client_name)
                except InputValidationError as e:
                    return {"success": False, "error": str(e), "projects": []}

            # Validate limit
            if not isinstance(limit, int) or limit < 1 or limit > 1000:
                limit = 10

            projects = self.db.get_projects(limit=limit)

            if client_name:
                projects = [p for p in projects if p.get("client_name") == client_name]

            return {"success": True, "projects": projects, "count": len(projects)}

        except Exception as e:
            return {"success": False, "error": str(e), "projects": []}

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """
        Get detailed status of a specific project.

        Wraps: python 03_post_generator.py project-status [project_id]

        Security (TR-003): Project ID validated before database query.
        """
        try:
            # Validate project_id
            project_id = validate_project_id(project_id)
        except InputValidationError as e:
            return {"success": False, "error": str(e)}

        try:
            project = self.db.get_project(project_id)

            if not project:
                return {"success": False, "error": f"Project {project_id} not found"}

            # Get additional stats
            feedback = self.db.get_post_feedback(project_id=project_id)
            satisfaction = self.db.get_client_satisfaction(project_id=project_id)

            return {
                "success": True,
                "project": project,
                "feedback_count": len(feedback),
                "has_satisfaction": len(satisfaction) > 0,
                "status": project.get("status", "unknown"),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # CLIENT MANAGEMENT TOOLS
    # ============================================================================

    def list_clients(self) -> Dict[str, Any]:
        """Query database for unique clients"""
        try:
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT DISTINCT client_name
                    FROM client_history
                    ORDER BY client_name
                """
                )

                clients = [row[0] for row in cursor.fetchall()]

                return {"success": True, "clients": clients, "count": len(clients)}

        except Exception as e:
            return {"success": False, "error": str(e), "clients": []}

    def get_client_history(self, client_name: str) -> Dict[str, Any]:
        """
        Get client's project history and statistics.

        Security (TR-003): Client name validated before database query.
        """
        try:
            # Validate client_name
            client_name = validate_client_name(client_name)
        except InputValidationError as e:
            return {"success": False, "error": str(e)}

        try:
            # Get projects
            projects = self.db.get_projects()
            client_projects = [p for p in projects if p.get("client_name") == client_name]

            # Get feedback summary
            feedback_summary = self.db.get_post_feedback_summary(client_name=client_name)

            # Get satisfaction summary
            satisfaction_records = self.db.get_client_satisfaction(client_name=client_name)

            return {
                "success": True,
                "client_name": client_name,
                "total_projects": len(client_projects),
                "projects": client_projects,
                "feedback_summary": feedback_summary,
                "satisfaction_records": satisfaction_records,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # ============================================================================
    # FEEDBACK & SATISFACTION TOOLS
    # ============================================================================

    async def collect_feedback(self, client_name: str, project_id: str) -> Dict[str, Any]:
        """
        Collect post feedback from client.

        Wraps: python 03_post_generator.py feedback [project_id]

        Security (TR-003): All inputs validated before subprocess execution.
        """
        # Validate inputs
        try:
            client_name = validate_client_name(client_name)
            project_id = validate_project_id(project_id)
        except InputValidationError as e:
            logger.warning(f"Input validation failed in collect_feedback: {e}")
            return {"success": False, "error": str(e)}

        cmd = [
            sys.executable,
            str(self.project_dir / "03_post_generator.py"),
            "feedback",
            project_id,
            "-c",
            client_name,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))

            return {
                "success": result.returncode == 0,
                "message": "Feedback collection initiated" if result.returncode == 0 else "Failed",
                "output": result.stdout,
            }

        except Exception as e:
            logger.error(f"Exception in collect_feedback: {e}")
            return {"success": False, "error": str(e)}

    async def collect_satisfaction(self, client_name: str, project_id: str) -> Dict[str, Any]:
        """
        Collect satisfaction survey from client.

        Wraps: python 03_post_generator.py satisfaction [project_id]

        Security (TR-003): All inputs validated before subprocess execution.
        """
        # Validate inputs
        try:
            client_name = validate_client_name(client_name)
            project_id = validate_project_id(project_id)
        except InputValidationError as e:
            logger.warning(f"Input validation failed in collect_satisfaction: {e}")
            return {"success": False, "error": str(e)}

        cmd = [
            sys.executable,
            str(self.project_dir / "03_post_generator.py"),
            "satisfaction",
            project_id,
            "-c",
            client_name,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))

            return {
                "success": result.returncode == 0,
                "message": "Satisfaction survey initiated" if result.returncode == 0 else "Failed",
                "output": result.stdout,
            }

        except Exception as e:
            logger.error(f"Exception in collect_satisfaction: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # VOICE SAMPLE TOOLS
    # ============================================================================

    async def upload_voice_samples(
        self, client_name: str, file_paths: List[str], source: str = "mixed"
    ) -> Dict[str, Any]:
        """
        Upload voice samples for a client.

        Wraps: python 03_post_generator.py upload-voice-samples

        Security (TR-003): All inputs validated before subprocess execution.
        """
        # Validate inputs
        try:
            client_name = validate_client_name(client_name)
            source = validate_source(source)

            # Validate each file path
            validated_paths = []
            for fp in file_paths:
                validated_path = validate_file_path(fp, self.project_dir)
                validated_paths.append(str(validated_path))

            if not validated_paths:
                return {"success": False, "error": "At least one file path is required"}

        except InputValidationError as e:
            logger.warning(f"Input validation failed in upload_voice_samples: {e}")
            return {"success": False, "error": str(e)}

        cmd = [
            sys.executable,
            str(self.project_dir / "03_post_generator.py"),
            "upload-voice-samples",
            "--client",
            client_name,
            "--source",
            source,
        ]

        for file_path in validated_paths:
            cmd.extend(["--file", file_path])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))

            return {
                "success": result.returncode == 0,
                "message": (
                    f"Uploaded {len(validated_paths)} voice samples"
                    if result.returncode == 0
                    else "Upload failed"
                ),
                "output": result.stdout,
            }

        except Exception as e:
            logger.error(f"Exception in upload_voice_samples: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # ANALYTICS TOOLS
    # ============================================================================

    async def show_dashboard(self, client_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Show analytics dashboard.

        Wraps: python 03_post_generator.py dashboard

        Security (TR-003): Client name validated if provided.
        """
        # Validate client_name if provided
        if client_name:
            try:
                client_name = validate_client_name(client_name)
            except InputValidationError as e:
                logger.warning(f"Input validation failed in show_dashboard: {e}")
                return {"success": False, "error": str(e)}

        cmd = [sys.executable, str(self.project_dir / "03_post_generator.py"), "dashboard"]

        if client_name:
            cmd.extend(["-c", client_name])

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(self.project_dir))

            return {"success": result.returncode == 0, "output": result.stdout}

        except Exception as e:
            logger.error(f"Exception in show_dashboard: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # FILE OPERATIONS
    # ============================================================================

    def read_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read a file (brief, feedback, etc.).

        Security (TR-003): File path validated to prevent path traversal.
        """
        try:
            # Validate file path is within project directory
            validated_path = validate_file_path(file_path, self.project_dir)
        except InputValidationError as e:
            logger.warning(f"Path traversal attempt blocked in read_file: {file_path}")
            return {"success": False, "error": str(e)}

        try:
            if not validated_path.exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            content = validated_path.read_text(encoding="utf-8")

            return {
                "success": True,
                "content": content,
                "file_path": str(validated_path),
                "size": len(content),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def search_files(self, pattern: str, directory: str = "data") -> Dict[str, Any]:
        """
        Search for files matching a pattern.

        Security (TR-003): Directory and pattern validated to prevent traversal.
        """
        try:
            # Validate directory is within project
            validated_dir = validate_directory(directory, self.project_dir)
            # Validate pattern
            validated_pattern = validate_file_pattern(pattern)
        except InputValidationError as e:
            logger.warning(f"Input validation failed in search_files: {e}")
            return {"success": False, "error": str(e), "matches": []}

        try:
            matches = list(validated_dir.rglob(validated_pattern))

            return {"success": True, "matches": [str(m) for m in matches], "count": len(matches)}

        except Exception as e:
            return {"success": False, "error": str(e), "matches": []}

    async def process_revision(
        self, client_name: str, project_id: str, revision_notes: str, regenerate_count: int = 5
    ) -> Dict[str, Any]:
        """
        Process revision request for a project.

        Wraps: python 03_post_generator.py revision command

        Security (TR-003): All inputs validated before subprocess execution.
        """
        # Validate inputs
        try:
            client_name = validate_client_name(client_name)
            project_id = validate_project_id(project_id)

            # Validate regenerate_count
            if not isinstance(regenerate_count, int):
                try:
                    regenerate_count = int(regenerate_count)
                except (ValueError, TypeError):
                    raise InputValidationError("Regenerate count must be an integer")

            if regenerate_count < 1 or regenerate_count > 30:
                raise InputValidationError("Regenerate count must be between 1 and 30")

            # Validate revision_notes length (prevent DoS via huge input)
            if not revision_notes or len(revision_notes) > 10000:
                raise InputValidationError("Revision notes must be 1-10000 characters")

        except InputValidationError as e:
            logger.warning(f"Input validation failed in process_revision: {e}")
            return {"success": False, "error": str(e), "message": "Validation failed"}

        try:
            # Create revision notes file (project_id is validated, safe for filename)
            revision_file = self.project_dir / "data" / "revisions" / f"{project_id}_revision.txt"
            revision_file.parent.mkdir(parents=True, exist_ok=True)
            revision_file.write_text(revision_notes, encoding="utf-8")

            cmd = [
                sys.executable,
                str(self.project_dir / "03_post_generator.py"),
                "revision",
                project_id,
                str(revision_file),
                "-n",
                str(regenerate_count),
            ]

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_dir),
            )

            stdout, stderr = process.communicate(timeout=180)  # 3 minute timeout

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": f"Revision processed for {client_name}",
                    "project_id": project_id,
                    "regenerated_posts": regenerate_count,
                    "output": stdout,
                }
            else:
                return {
                    "success": False,
                    "error": stderr or stdout,
                    "message": "Revision processing failed",
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Revision processing timed out (>3 minutes)"}
        except Exception as e:
            logger.error(f"Exception in process_revision: {e}")
            return {"success": False, "error": str(e)}

    def generate_analytics_report(
        self, client_name: Optional[str] = None, report_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Generate analytics report for client(s).

        Wraps: python 03_post_generator.py analytics command

        Security (TR-003): All inputs validated before subprocess execution.
        """
        # Validate inputs
        try:
            if client_name:
                client_name = validate_client_name(client_name)
            report_type = validate_report_type(report_type)
        except InputValidationError as e:
            logger.warning(f"Input validation failed in generate_analytics_report: {e}")
            return {"success": False, "error": str(e)}

        try:
            cmd = [sys.executable, str(self.project_dir / "03_post_generator.py"), "analytics"]

            if client_name:
                cmd.extend(["-c", client_name])

            cmd.extend(["--format", report_type])

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.project_dir),
            )

            stdout, stderr = process.communicate(timeout=30)

            if process.returncode == 0:
                return {
                    "success": True,
                    "message": "Analytics report generated",
                    "client": client_name or "All clients",
                    "report_type": report_type,
                    "output": stdout,
                }
            else:
                return {"success": False, "error": stderr or stdout}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Analytics generation timed out"}
        except Exception as e:
            logger.error(f"Exception in generate_analytics_report: {e}")
            return {"success": False, "error": str(e)}

    def create_posting_schedule(
        self,
        client_name: str,
        project_id: str,
        posts_per_week: int = 4,
        start_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create posting schedule for a project.

        Wraps: posting schedule generation functionality

        Security (TR-003): All inputs validated before use.
        """
        # Validate inputs
        try:
            client_name = validate_client_name(client_name)
            project_id = validate_project_id(project_id)

            # Validate posts_per_week
            if not isinstance(posts_per_week, int):
                try:
                    posts_per_week = int(posts_per_week)
                except (ValueError, TypeError):
                    raise InputValidationError("Posts per week must be an integer")

            if posts_per_week < 1 or posts_per_week > 14:
                raise InputValidationError("Posts per week must be between 1 and 14")

            # Validate start_date format if provided
            if start_date:
                # Basic ISO date format validation
                if not re.match(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?", start_date):
                    raise InputValidationError("Start date must be in ISO format (YYYY-MM-DD)")

        except InputValidationError as e:
            logger.warning(f"Input validation failed in create_posting_schedule: {e}")
            return {"success": False, "error": str(e)}

        try:
            from datetime import datetime

            from src.utils.schedule_generator import ScheduleGenerator

            # Get project posts
            with self.db._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM client_history
                    WHERE project_id = ?
                """,
                    (project_id,),
                )
                row = cursor.fetchone()
                total_posts = row[0] if row else 30

            # Generate schedule
            generator = ScheduleGenerator()
            schedule_start = datetime.fromisoformat(start_date) if start_date else datetime.now()

            schedule = generator.generate_schedule(
                total_posts=total_posts, posts_per_week=posts_per_week, start_date=schedule_start
            )

            # Save schedule to file (project_id is validated, safe for filename)
            schedule_file = self.project_dir / "data" / "schedules" / f"{project_id}_schedule.json"
            schedule_file.parent.mkdir(parents=True, exist_ok=True)

            import json

            schedule_file.write_text(
                json.dumps(
                    {
                        "client_name": client_name,
                        "project_id": project_id,
                        "posts_per_week": posts_per_week,
                        "start_date": schedule_start.isoformat(),
                        "schedule": [s.model_dump(mode="json") for s in schedule.posting_schedule],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            return {
                "success": True,
                "message": f"Posting schedule created for {client_name}",
                "project_id": project_id,
                "total_posts": total_posts,
                "posts_per_week": posts_per_week,
                "schedule_file": str(schedule_file),
                "duration_weeks": len(schedule.posting_schedule) // posts_per_week,
            }

        except Exception as e:
            logger.error(f"Exception in create_posting_schedule: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # BACKEND API CLIENT MANAGEMENT (CRUD)
    # ============================================================================

    def list_clients_api(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List all clients from the backend API.

        Provides richer data than list_clients() which uses local DB.

        Args:
            skip: Number of records to skip (pagination)
            limit: Maximum number of records to return

        Returns:
            Dictionary with clients list and count.
        """
        try:
            from backend.services import crud

            db = self._get_backend_session()
            try:
                clients = crud.list_clients(db, skip=skip, limit=limit)

                return {
                    "success": True,
                    "clients": [
                        {
                            "id": c.id,
                            "name": c.name,
                            "business_description": c.business_description,
                            "ideal_customer": c.ideal_customer,
                            "main_problem_solved": c.main_problem_solved,
                            "created_at": c.created_at.isoformat() if c.created_at else None,
                        }
                        for c in clients
                    ],
                    "count": len(clients),
                    "skip": skip,
                    "limit": limit,
                }

            finally:
                db.close()

        except ImportError:
            return {
                "success": False,
                "error": "Backend API not available. Start the API server first.",
            }
        except Exception as e:
            logger.error(f"Error listing clients: {e}")
            return {"success": False, "error": str(e)}

    def create_client_api(
        self,
        name: str,
        business_description: str = "",
        ideal_customer: str = "",
        main_problem_solved: str = "",
        customer_pain_points: Optional[List[str]] = None,
        tone_preferences: Optional[List[str]] = None,
        platforms: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new client via the backend API.

        Args:
            name: Client name (required)
            business_description: What the business does
            ideal_customer: Target customer description
            main_problem_solved: Core value proposition
            customer_pain_points: List of customer pain points
            tone_preferences: Preferred brand tone/voice
            platforms: Target social platforms

        Returns:
            Dictionary with created client data or error.
        """
        try:
            name = validate_client_name(name)

            from backend.services import crud
            from backend.schemas.client import ClientCreate

            db = self._get_backend_session()
            try:
                client_data = ClientCreate(
                    name=name,
                    business_description=business_description,
                    ideal_customer=ideal_customer,
                    main_problem_solved=main_problem_solved,
                    customer_pain_points=customer_pain_points or [],
                    tone_preferences=tone_preferences or [],
                    platforms=platforms or [],
                )

                client = crud.create_client(db, client_data)

                return {
                    "success": True,
                    "client": {
                        "id": client.id,
                        "name": client.name,
                        "business_description": client.business_description,
                        "created_at": client.created_at.isoformat() if client.created_at else None,
                    },
                    "message": f"Client '{name}' created successfully",
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error creating client: {e}")
            return {"success": False, "error": str(e)}

    def get_client_api(self, client_id: str) -> Dict[str, Any]:
        """
        Get a specific client by ID from the backend API.

        Args:
            client_id: Client ID to retrieve

        Returns:
            Dictionary with client data or error.
        """
        try:
            from backend.services import crud

            db = self._get_backend_session()
            try:
                client = crud.get_client(db, client_id)

                if not client:
                    return {"success": False, "error": f"Client {client_id} not found"}

                return {
                    "success": True,
                    "client": {
                        "id": client.id,
                        "name": client.name,
                        "business_description": client.business_description,
                        "ideal_customer": client.ideal_customer,
                        "main_problem_solved": client.main_problem_solved,
                        "customer_pain_points": client.customer_pain_points,
                        "tone_preferences": client.tone_preferences,
                        "platforms": client.platforms,
                        "created_at": client.created_at.isoformat() if client.created_at else None,
                        "updated_at": client.updated_at.isoformat() if client.updated_at else None,
                    },
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting client: {e}")
            return {"success": False, "error": str(e)}

    def update_client_api(
        self,
        client_id: str,
        name: Optional[str] = None,
        business_description: Optional[str] = None,
        ideal_customer: Optional[str] = None,
        main_problem_solved: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a client via the backend API.

        Args:
            client_id: Client ID to update
            name: New client name (optional)
            business_description: New description (optional)
            ideal_customer: New ideal customer (optional)
            main_problem_solved: New problem solved (optional)

        Returns:
            Dictionary with updated client data or error.
        """
        try:
            if name:
                name = validate_client_name(name)

            from backend.services import crud
            from backend.schemas.client import ClientUpdate

            db = self._get_backend_session()
            try:
                # Build update data
                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if business_description is not None:
                    update_data["business_description"] = business_description
                if ideal_customer is not None:
                    update_data["ideal_customer"] = ideal_customer
                if main_problem_solved is not None:
                    update_data["main_problem_solved"] = main_problem_solved

                if not update_data:
                    return {"success": False, "error": "No update fields provided"}

                client_update = ClientUpdate(**update_data)
                client = crud.update_client(db, client_id, client_update)

                if not client:
                    return {"success": False, "error": f"Client {client_id} not found"}

                return {
                    "success": True,
                    "client": {
                        "id": client.id,
                        "name": client.name,
                        "business_description": client.business_description,
                        "updated_at": client.updated_at.isoformat() if client.updated_at else None,
                    },
                    "message": f"Client '{client.name}' updated successfully",
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error updating client: {e}")
            return {"success": False, "error": str(e)}

    def delete_client_api(self, client_id: str) -> Dict[str, Any]:
        """
        Delete a client via the backend API.

        Args:
            client_id: Client ID to delete

        Returns:
            Dictionary with success status or error.
        """
        try:
            from backend.services import crud

            db = self._get_backend_session()
            try:
                success = crud.delete_client(db, client_id)

                if not success:
                    return {"success": False, "error": f"Client {client_id} not found"}

                return {
                    "success": True,
                    "message": f"Client {client_id} deleted successfully",
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error deleting client: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # BACKEND API PROJECT MANAGEMENT (CRUD)
    # ============================================================================

    def list_projects_api(
        self,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List projects from the backend API with optional filters.

        Args:
            client_id: Filter by client ID (optional)
            status: Filter by status (optional)
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            Dictionary with projects list and count.
        """
        try:
            from backend.services import crud

            db = self._get_backend_session()
            try:
                projects = crud.list_projects(
                    db, client_id=client_id, status=status, skip=skip, limit=limit
                )

                return {
                    "success": True,
                    "projects": [
                        {
                            "id": p.id,
                            "name": p.name,
                            "client_id": p.client_id,
                            "status": p.status,
                            "total_posts": p.total_posts,
                            "completed_posts": p.completed_posts,
                            "created_at": p.created_at.isoformat() if p.created_at else None,
                        }
                        for p in projects
                    ],
                    "count": len(projects),
                    "filters": {"client_id": client_id, "status": status},
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            return {"success": False, "error": str(e)}

    def create_project_api(
        self,
        name: str,
        client_id: str,
        total_posts: int = 30,
        platform: str = "linkedin",
    ) -> Dict[str, Any]:
        """
        Create a new project via the backend API.

        Args:
            name: Project name
            client_id: Client ID this project belongs to
            total_posts: Target number of posts (default 30)
            platform: Target platform (default linkedin)

        Returns:
            Dictionary with created project data or error.
        """
        try:
            platform = validate_platform(platform)
            total_posts = validate_num_posts(total_posts)

            from backend.services import crud
            from backend.schemas.project import ProjectCreate

            db = self._get_backend_session()
            try:
                # Verify client exists
                client = crud.get_client(db, client_id)
                if not client:
                    return {"success": False, "error": f"Client {client_id} not found"}

                project_data = ProjectCreate(
                    name=name,
                    client_id=client_id,
                    total_posts=total_posts,
                    platform=platform,
                )

                project = crud.create_project(db, project_data)

                return {
                    "success": True,
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "client_id": project.client_id,
                        "status": project.status,
                        "total_posts": project.total_posts,
                        "created_at": project.created_at.isoformat() if project.created_at else None,
                    },
                    "message": f"Project '{name}' created for client {client.name}",
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return {"success": False, "error": str(e)}

    def get_project_api(self, project_id: str) -> Dict[str, Any]:
        """
        Get a specific project by ID from the backend API.

        Args:
            project_id: Project ID to retrieve

        Returns:
            Dictionary with project data or error.
        """
        try:
            project_id = validate_project_id(project_id)

            from backend.services import crud

            db = self._get_backend_session()
            try:
                project = crud.get_project(db, project_id)

                if not project:
                    return {"success": False, "error": f"Project {project_id} not found"}

                # Get client name
                client = crud.get_client(db, project.client_id) if project.client_id else None

                return {
                    "success": True,
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "client_id": project.client_id,
                        "client_name": client.name if client else None,
                        "status": project.status,
                        "total_posts": project.total_posts,
                        "completed_posts": project.completed_posts,
                        "platform": project.platform,
                        "created_at": project.created_at.isoformat() if project.created_at else None,
                        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                    },
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return {"success": False, "error": str(e)}

    def update_project_api(
        self,
        project_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
        total_posts: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Update a project via the backend API.

        Args:
            project_id: Project ID to update
            name: New project name (optional)
            status: New status (optional)
            total_posts: New total posts target (optional)

        Returns:
            Dictionary with updated project data or error.
        """
        try:
            project_id = validate_project_id(project_id)
            if total_posts is not None:
                total_posts = validate_num_posts(total_posts)

            from backend.services import crud
            from backend.schemas.project import ProjectUpdate

            db = self._get_backend_session()
            try:
                update_data = {}
                if name is not None:
                    update_data["name"] = name
                if status is not None:
                    update_data["status"] = status
                if total_posts is not None:
                    update_data["total_posts"] = total_posts

                if not update_data:
                    return {"success": False, "error": "No update fields provided"}

                project_update = ProjectUpdate(**update_data)
                project = crud.update_project(db, project_id, project_update)

                if not project:
                    return {"success": False, "error": f"Project {project_id} not found"}

                return {
                    "success": True,
                    "project": {
                        "id": project.id,
                        "name": project.name,
                        "status": project.status,
                        "total_posts": project.total_posts,
                        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                    },
                    "message": f"Project '{project.name}' updated successfully",
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            return {"success": False, "error": str(e)}

    def delete_project_api(self, project_id: str) -> Dict[str, Any]:
        """
        Delete a project via the backend API.

        Args:
            project_id: Project ID to delete

        Returns:
            Dictionary with success status or error.
        """
        try:
            project_id = validate_project_id(project_id)

            from backend.services import crud

            db = self._get_backend_session()
            try:
                success = crud.delete_project(db, project_id)

                if not success:
                    return {"success": False, "error": f"Project {project_id} not found"}

                return {
                    "success": True,
                    "message": f"Project {project_id} deleted successfully",
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # BACKEND API POST MANAGEMENT
    # ============================================================================

    def list_posts_api(
        self,
        project_id: Optional[str] = None,
        qa_status: Optional[str] = None,
        template_id: Optional[str] = None,
        platform: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List posts from the backend API with optional filters.

        Args:
            project_id: Filter by project ID (optional)
            qa_status: Filter by QA status: approved, rejected, pending (optional)
            template_id: Filter by template ID (optional)
            platform: Filter by platform (optional)
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            Dictionary with posts list and count.
        """
        try:
            if project_id:
                project_id = validate_project_id(project_id)
            if platform:
                platform = validate_platform(platform)

            from backend.models import Post as PostModel

            db = self._get_backend_session()
            try:
                query = db.query(PostModel)

                # Apply filters
                if project_id:
                    query = query.filter(PostModel.project_id == project_id)
                if qa_status:
                    query = query.filter(PostModel.qa_status == qa_status)
                if template_id:
                    query = query.filter(PostModel.template_id == template_id)
                if platform:
                    query = query.filter(PostModel.target_platform == platform)

                # Apply pagination
                total = query.count()
                posts = query.offset(skip).limit(limit).all()

                return {
                    "success": True,
                    "posts": [
                        {
                            "id": p.id,
                            "project_id": p.project_id,
                            "template_name": p.template_name,
                            "target_platform": p.target_platform,
                            "word_count": p.word_count,
                            "qa_status": p.qa_status,
                            "has_cta": p.has_cta,
                            "readability_score": p.readability_score,
                            "content_preview": p.content[:200] + "..." if p.content and len(p.content) > 200 else p.content,
                            "created_at": p.created_at.isoformat() if p.created_at else None,
                        }
                        for p in posts
                    ],
                    "count": len(posts),
                    "total": total,
                    "filters": {
                        "project_id": project_id,
                        "qa_status": qa_status,
                        "template_id": template_id,
                        "platform": platform,
                    },
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error listing posts: {e}")
            return {"success": False, "error": str(e)}

    def get_post_api(self, post_id: str) -> Dict[str, Any]:
        """
        Get a specific post by ID from the backend API.

        Args:
            post_id: Post ID to retrieve

        Returns:
            Dictionary with full post data or error.
        """
        try:
            from backend.models import Post as PostModel

            db = self._get_backend_session()
            try:
                post = db.query(PostModel).filter(PostModel.id == post_id).first()

                if not post:
                    return {"success": False, "error": f"Post {post_id} not found"}

                return {
                    "success": True,
                    "post": {
                        "id": post.id,
                        "project_id": post.project_id,
                        "run_id": post.run_id,
                        "content": post.content,
                        "template_name": post.template_name,
                        "template_id": post.template_id,
                        "target_platform": post.target_platform,
                        "word_count": post.word_count,
                        "qa_status": post.qa_status,
                        "has_cta": post.has_cta,
                        "readability_score": post.readability_score,
                        "variant_number": post.variant_number,
                        "created_at": post.created_at.isoformat() if post.created_at else None,
                        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                    },
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting post: {e}")
            return {"success": False, "error": str(e)}

    def update_post_api(
        self,
        post_id: str,
        content: Optional[str] = None,
        qa_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a post via the backend API.

        Use qa_status to approve or reject posts:
        - "approved" - Post passed QA review
        - "rejected" - Post failed QA review
        - "pending" - Reset to pending status

        Args:
            post_id: Post ID to update
            content: New post content (optional)
            qa_status: New QA status: approved, rejected, pending (optional)

        Returns:
            Dictionary with updated post data or error.
        """
        try:
            from backend.models import Post as PostModel

            db = self._get_backend_session()
            try:
                post = db.query(PostModel).filter(PostModel.id == post_id).first()

                if not post:
                    return {"success": False, "error": f"Post {post_id} not found"}

                # Apply updates
                if content is not None:
                    post.content = content
                    post.word_count = len(content.split())
                if qa_status is not None:
                    if qa_status not in ["approved", "rejected", "pending"]:
                        return {"success": False, "error": f"Invalid qa_status: {qa_status}. Use: approved, rejected, pending"}
                    post.qa_status = qa_status

                db.commit()
                db.refresh(post)

                return {
                    "success": True,
                    "post": {
                        "id": post.id,
                        "content_preview": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                        "qa_status": post.qa_status,
                        "word_count": post.word_count,
                        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
                    },
                    "message": f"Post {post_id} updated successfully",
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error updating post: {e}")
            return {"success": False, "error": str(e)}

    def approve_post(self, post_id: str) -> Dict[str, Any]:
        """
        Approve a post (shortcut for update_post_api with qa_status='approved').

        Args:
            post_id: Post ID to approve

        Returns:
            Dictionary with result.
        """
        return self.update_post_api(post_id, qa_status="approved")

    def reject_post(self, post_id: str) -> Dict[str, Any]:
        """
        Reject a post (shortcut for update_post_api with qa_status='rejected').

        Args:
            post_id: Post ID to reject

        Returns:
            Dictionary with result.
        """
        return self.update_post_api(post_id, qa_status="rejected")

    # ============================================================================
    # BACKEND API DELIVERABLE MANAGEMENT
    # ============================================================================

    def list_deliverables_api(
        self,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List deliverables from the backend API with optional filters.

        Args:
            client_id: Filter by client ID (optional)
            status: Filter by status: ready, pending, delivered (optional)
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            Dictionary with deliverables list and count.
        """
        try:
            from backend.models import Deliverable

            db = self._get_backend_session()
            try:
                query = db.query(Deliverable)

                # Apply filters
                if client_id:
                    query = query.filter(Deliverable.client_id == client_id)
                if status:
                    query = query.filter(Deliverable.status == status)

                # Apply pagination
                total = query.count()
                deliverables = query.offset(skip).limit(limit).all()

                return {
                    "success": True,
                    "deliverables": [
                        {
                            "id": d.id,
                            "project_id": d.project_id,
                            "client_id": d.client_id,
                            "format": d.format,
                            "status": d.status,
                            "path": d.path,
                            "file_size_bytes": d.file_size_bytes,
                            "created_at": d.created_at.isoformat() if d.created_at else None,
                            "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
                        }
                        for d in deliverables
                    ],
                    "count": len(deliverables),
                    "total": total,
                    "filters": {"client_id": client_id, "status": status},
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error listing deliverables: {e}")
            return {"success": False, "error": str(e)}

    def get_deliverable_api(self, deliverable_id: str) -> Dict[str, Any]:
        """
        Get a specific deliverable by ID from the backend API.

        Args:
            deliverable_id: Deliverable ID to retrieve

        Returns:
            Dictionary with deliverable data or error.
        """
        try:
            from backend.models import Deliverable

            db = self._get_backend_session()
            try:
                deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()

                if not deliverable:
                    return {"success": False, "error": f"Deliverable {deliverable_id} not found"}

                return {
                    "success": True,
                    "deliverable": {
                        "id": deliverable.id,
                        "project_id": deliverable.project_id,
                        "client_id": deliverable.client_id,
                        "run_id": deliverable.run_id,
                        "format": deliverable.format,
                        "status": deliverable.status,
                        "path": deliverable.path,
                        "file_size_bytes": deliverable.file_size_bytes,
                        "created_at": deliverable.created_at.isoformat() if deliverable.created_at else None,
                        "delivered_at": deliverable.delivered_at.isoformat() if deliverable.delivered_at else None,
                        "proof_url": deliverable.proof_url,
                        "proof_notes": deliverable.proof_notes,
                    },
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting deliverable: {e}")
            return {"success": False, "error": str(e)}

    def get_deliverable_details_api(self, deliverable_id: str) -> Dict[str, Any]:
        """
        Get detailed deliverable info including file preview and related posts.

        Args:
            deliverable_id: Deliverable ID to retrieve details for

        Returns:
            Dictionary with detailed deliverable data or error.
        """
        try:
            from backend.services.deliverable_service import get_deliverable_details

            db = self._get_backend_session()
            try:
                details = get_deliverable_details(db, deliverable_id)

                if not details:
                    return {"success": False, "error": f"Deliverable {deliverable_id} not found"}

                return {
                    "success": True,
                    "deliverable": {
                        "id": details.id,
                        "project_id": details.project_id,
                        "client_id": details.client_id,
                        "format": details.format,
                        "status": details.status,
                        "path": details.path,
                        "file_size_bytes": details.file_size_bytes,
                        "file_preview": details.file_preview[:1000] if details.file_preview else None,
                        "posts_count": details.posts_count,
                        "qa_summary": details.qa_summary,
                        "file_modified_at": details.file_modified_at.isoformat() if details.file_modified_at else None,
                    },
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting deliverable details: {e}")
            return {"success": False, "error": str(e)}

    def mark_deliverable_delivered_api(
        self,
        deliverable_id: str,
        proof_url: Optional[str] = None,
        proof_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Mark a deliverable as delivered.

        Args:
            deliverable_id: Deliverable ID to mark as delivered
            proof_url: Optional URL as proof of delivery (e.g., email link)
            proof_notes: Optional notes about delivery

        Returns:
            Dictionary with updated deliverable or error.
        """
        try:
            from datetime import datetime
            from backend.services import crud

            db = self._get_backend_session()
            try:
                deliverable = crud.mark_deliverable_delivered(
                    db,
                    deliverable_id,
                    delivered_at=datetime.utcnow(),
                    proof_url=proof_url,
                    proof_notes=proof_notes,
                )

                if not deliverable:
                    return {"success": False, "error": f"Deliverable {deliverable_id} not found"}

                return {
                    "success": True,
                    "deliverable": {
                        "id": deliverable.id,
                        "status": deliverable.status,
                        "delivered_at": deliverable.delivered_at.isoformat() if deliverable.delivered_at else None,
                        "proof_url": deliverable.proof_url,
                    },
                    "message": f"Deliverable {deliverable_id} marked as delivered",
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error marking deliverable delivered: {e}")
            return {"success": False, "error": str(e)}

    def get_deliverable_download_path(self, deliverable_id: str) -> Dict[str, Any]:
        """
        Get the file path for downloading a deliverable.

        Args:
            deliverable_id: Deliverable ID to get download path for

        Returns:
            Dictionary with file path and download info.
        """
        try:
            from pathlib import Path
            from backend.models import Deliverable

            db = self._get_backend_session()
            try:
                deliverable = db.query(Deliverable).filter(Deliverable.id == deliverable_id).first()

                if not deliverable:
                    return {"success": False, "error": f"Deliverable {deliverable_id} not found"}

                # Construct file path
                base_path = Path("data/outputs")
                file_path = base_path / deliverable.path

                if not file_path.exists():
                    return {
                        "success": False,
                        "error": f"File not found: {deliverable.path}",
                        "hint": "The deliverable file may have been moved or deleted",
                    }

                return {
                    "success": True,
                    "file_path": str(file_path.resolve()),
                    "filename": file_path.name,
                    "format": deliverable.format,
                    "file_size_bytes": deliverable.file_size_bytes,
                    "hint": "Use this path to read or share the file",
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting download path: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # BACKEND API RUN MANAGEMENT
    # ============================================================================

    def list_runs_api(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """
        List generation runs from the backend API with optional filters.

        Args:
            project_id: Filter by project ID (optional)
            status: Filter by status: pending, running, succeeded, failed (optional)
            skip: Pagination offset
            limit: Maximum records to return

        Returns:
            Dictionary with runs list and count.
        """
        try:
            if project_id:
                project_id = validate_project_id(project_id)

            from backend.models import Run

            db = self._get_backend_session()
            try:
                query = db.query(Run)

                # Apply filters
                if project_id:
                    query = query.filter(Run.project_id == project_id)
                if status:
                    query = query.filter(Run.status == status)

                # Order by most recent first
                query = query.order_by(Run.started_at.desc())

                # Apply pagination
                total = query.count()
                runs = query.offset(skip).limit(limit).all()

                return {
                    "success": True,
                    "runs": [
                        {
                            "id": r.id,
                            "project_id": r.project_id,
                            "status": r.status,
                            "is_batch": r.is_batch,
                            "started_at": r.started_at.isoformat() if r.started_at else None,
                            "ended_at": r.ended_at.isoformat() if r.ended_at else None,
                            "error_message": r.error_message,
                        }
                        for r in runs
                    ],
                    "count": len(runs),
                    "total": total,
                    "filters": {"project_id": project_id, "status": status},
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error listing runs: {e}")
            return {"success": False, "error": str(e)}

    def get_run_api(self, run_id: str) -> Dict[str, Any]:
        """
        Get a specific run by ID from the backend API.

        Args:
            run_id: Run ID to retrieve

        Returns:
            Dictionary with run data including logs.
        """
        try:
            from backend.models import Run

            db = self._get_backend_session()
            try:
                run = db.query(Run).filter(Run.id == run_id).first()

                if not run:
                    return {"success": False, "error": f"Run {run_id} not found"}

                return {
                    "success": True,
                    "run": {
                        "id": run.id,
                        "project_id": run.project_id,
                        "status": run.status,
                        "is_batch": run.is_batch,
                        "started_at": run.started_at.isoformat() if run.started_at else None,
                        "ended_at": run.ended_at.isoformat() if run.ended_at else None,
                        "error_message": run.error_message,
                        "logs": run.logs,
                    },
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting run: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # BACKEND API BRIEF MANAGEMENT
    # ============================================================================

    def create_brief_api(
        self,
        project_id: str,
        content: str,
    ) -> Dict[str, Any]:
        """
        Create a brief for a project via the backend API.

        Args:
            project_id: Project ID to create brief for
            content: Brief text content

        Returns:
            Dictionary with created brief data or error.
        """
        try:
            project_id = validate_project_id(project_id)

            if not content or len(content) < 50:
                return {"success": False, "error": "Brief content must be at least 50 characters"}

            from backend.services import crud
            from backend.schemas.brief import BriefCreate

            db = self._get_backend_session()
            try:
                # Verify project exists
                project = crud.get_project(db, project_id)
                if not project:
                    return {"success": False, "error": f"Project {project_id} not found"}

                # Check if brief already exists
                existing = crud.get_brief_by_project(db, project_id)
                if existing:
                    return {
                        "success": False,
                        "error": f"Brief already exists for project {project_id}",
                        "existing_brief_id": existing.id,
                    }

                brief_data = BriefCreate(project_id=project_id, content=content)
                brief = crud.create_brief(db, brief_data, source="agent", file_path=None)

                return {
                    "success": True,
                    "brief": {
                        "id": brief.id,
                        "project_id": brief.project_id,
                        "content_preview": brief.content[:200] + "..." if len(brief.content) > 200 else brief.content,
                        "source": brief.source,
                        "created_at": brief.created_at.isoformat() if brief.created_at else None,
                    },
                    "message": f"Brief created for project {project_id}",
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error creating brief: {e}")
            return {"success": False, "error": str(e)}

    def get_brief_api(self, brief_id: str) -> Dict[str, Any]:
        """
        Get a specific brief by ID from the backend API.

        Args:
            brief_id: Brief ID to retrieve

        Returns:
            Dictionary with brief data or error.
        """
        try:
            from backend.models import Brief

            db = self._get_backend_session()
            try:
                brief = db.query(Brief).filter(Brief.id == brief_id).first()

                if not brief:
                    return {"success": False, "error": f"Brief {brief_id} not found"}

                return {
                    "success": True,
                    "brief": {
                        "id": brief.id,
                        "project_id": brief.project_id,
                        "content": brief.content,
                        "source": brief.source,
                        "file_path": brief.file_path,
                        "created_at": brief.created_at.isoformat() if brief.created_at else None,
                    },
                }

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting brief: {e}")
            return {"success": False, "error": str(e)}

    def get_brief_by_project_api(self, project_id: str) -> Dict[str, Any]:
        """
        Get a brief by project ID from the backend API.

        Args:
            project_id: Project ID to get brief for

        Returns:
            Dictionary with brief data or error.
        """
        try:
            project_id = validate_project_id(project_id)

            from backend.services import crud

            db = self._get_backend_session()
            try:
                brief = crud.get_brief_by_project(db, project_id)

                if not brief:
                    return {"success": False, "error": f"No brief found for project {project_id}"}

                return {
                    "success": True,
                    "brief": {
                        "id": brief.id,
                        "project_id": brief.project_id,
                        "content": brief.content,
                        "source": brief.source,
                        "file_path": brief.file_path,
                        "created_at": brief.created_at.isoformat() if brief.created_at else None,
                    },
                }

            finally:
                db.close()

        except InputValidationError as e:
            return {"success": False, "error": str(e)}
        except ImportError:
            return {"success": False, "error": "Backend API not available"}
        except Exception as e:
            logger.error(f"Error getting brief by project: {e}")
            return {"success": False, "error": str(e)}

    # ============================================================================
    # GOOGLE TRENDS INTEGRATION
    # ============================================================================

    def search_trends_interest(
        self,
        keywords: List[str],
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe: str = "past_12_months",
        geo: str = "",
        category: str = "all",
    ) -> Dict[str, Any]:
        """
        Search Google Trends for keyword interest over time.

        Args:
            keywords: List of 1-5 keywords to search
            client_id: Optional client to associate with search
            project_id: Optional project to associate with search
            timeframe: Time range (past_hour, past_day, past_week, past_month,
                      past_3_months, past_12_months, past_5_years, all_time)
            geo: Geographic region code (e.g., "US", "GB", "" for worldwide)
            category: Category filter (all, business_industrial, health, etc.)

        Returns:
            Dictionary with search results and historical data points.
        """
        try:
            if not keywords:
                return {"success": False, "error": "At least one keyword is required"}
            if len(keywords) > 5:
                return {"success": False, "error": "Maximum 5 keywords allowed"}

            from backend.services.trends_service import trends_service

            db = self._get_backend_session()
            try:
                # Get current user ID (use a default for agent context)
                user_id = "agent-system"

                result = trends_service.search_interest_over_time(
                    db=db,
                    keywords=keywords,
                    user_id=user_id,
                    client_id=client_id,
                    project_id=project_id,
                    timeframe=timeframe,
                    geo=geo,
                    category=category,
                )

                return result

            finally:
                db.close()

        except ImportError:
            return {
                "success": False,
                "error": "pytrends not installed. Run: pip install pytrends",
            }
        except Exception as e:
            logger.error(f"Error searching trends: {e}")
            return {"success": False, "error": str(e)}

    def search_trends_related_queries(
        self,
        keywords: List[str],
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        timeframe: str = "past_12_months",
        geo: str = "",
        category: str = "all",
    ) -> Dict[str, Any]:
        """
        Search Google Trends for related queries.

        Returns "top" (most popular) and "rising" (fastest growing) related queries.
        Useful for keyword expansion and content ideation.

        Args:
            keywords: List of 1-5 keywords to search
            client_id: Optional client to associate with search
            project_id: Optional project to associate with search
            timeframe: Time range
            geo: Geographic region code
            category: Category filter

        Returns:
            Dictionary with top and rising related queries.
        """
        try:
            if not keywords:
                return {"success": False, "error": "At least one keyword is required"}
            if len(keywords) > 5:
                return {"success": False, "error": "Maximum 5 keywords allowed"}

            from backend.services.trends_service import trends_service

            db = self._get_backend_session()
            try:
                user_id = "agent-system"

                result = trends_service.search_related_queries(
                    db=db,
                    keywords=keywords,
                    user_id=user_id,
                    client_id=client_id,
                    project_id=project_id,
                    timeframe=timeframe,
                    geo=geo,
                    category=category,
                )

                return result

            finally:
                db.close()

        except ImportError:
            return {
                "success": False,
                "error": "pytrends not installed. Run: pip install pytrends",
            }
        except Exception as e:
            logger.error(f"Error searching related queries: {e}")
            return {"success": False, "error": str(e)}

    def compute_trends_insight(
        self,
        keyword: str,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Compute insights for a keyword from stored trends data.

        Analyzes historical search data to determine:
        - Trend direction (rising/declining/stable/seasonal)
        - Average/peak interest levels
        - Seasonality patterns
        - Content recommendations

        Args:
            keyword: Keyword to analyze
            client_id: Optional client filter
            project_id: Optional project filter

        Returns:
            Dictionary with trend analysis and recommendations.
        """
        try:
            if not keyword:
                return {"success": False, "error": "Keyword is required"}

            from backend.services.trends_service import trends_service

            db = self._get_backend_session()
            try:
                result = trends_service.compute_keyword_insights(
                    db=db,
                    keyword=keyword,
                    client_id=client_id,
                    project_id=project_id,
                )

                return result

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend not available"}
        except Exception as e:
            logger.error(f"Error computing trends insight: {e}")
            return {"success": False, "error": str(e)}

    def get_trends_history(
        self,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get Google Trends search history.

        Returns previous searches with optional filtering.

        Args:
            client_id: Filter by client
            project_id: Filter by project
            limit: Maximum results (default 50)

        Returns:
            Dictionary with search history.
        """
        try:
            from backend.services.trends_service import trends_service

            db = self._get_backend_session()
            try:
                result = trends_service.get_search_history(
                    db=db,
                    user_id=None,  # Get all for agent
                    client_id=client_id,
                    project_id=project_id,
                    limit=limit,
                )

                return result

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend not available"}
        except Exception as e:
            logger.error(f"Error getting trends history: {e}")
            return {"success": False, "error": str(e)}

    def get_trends_insights(
        self,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        min_priority: float = 0,
    ) -> Dict[str, Any]:
        """
        Get all computed keyword insights from trends data.

        Returns actionable insights for content optimization.

        Args:
            client_id: Filter by client
            project_id: Filter by project
            min_priority: Minimum priority score (0-100)

        Returns:
            Dictionary with keyword insights sorted by priority.
        """
        try:
            from backend.services.trends_service import trends_service

            db = self._get_backend_session()
            try:
                result = trends_service.get_keyword_insights(
                    db=db,
                    client_id=client_id,
                    project_id=project_id,
                    min_priority=min_priority,
                )

                return result

            finally:
                db.close()

        except ImportError:
            return {"success": False, "error": "Backend not available"}
        except Exception as e:
            logger.error(f"Error getting trends insights: {e}")
            return {"success": False, "error": str(e)}

    def get_trends_timeframes(self) -> Dict[str, Any]:
        """
        Get available timeframe options for trends searches.

        Returns:
            Dictionary with available timeframes and their codes.
        """
        try:
            from backend.services.trends_service import trends_service

            return {
                "success": True,
                "timeframes": trends_service.TIMEFRAMES,
                "default": "past_12_months",
            }
        except ImportError:
            return {"success": False, "error": "Trends service not available"}

    def get_trends_categories(self) -> Dict[str, Any]:
        """
        Get available category options for trends searches.

        Returns:
            Dictionary with available categories and their IDs.
        """
        try:
            from backend.services.trends_service import trends_service

            return {
                "success": True,
                "categories": trends_service.CATEGORIES,
                "default": "all",
            }
        except ImportError:
            return {"success": False, "error": "Trends service not available"}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _extract_project_id(self, output: str) -> Optional[str]:
        """Extract project ID from CLI output"""
        for line in output.split("\n"):
            if "Project ID:" in line or "project_id:" in line:
                parts = line.split(":")
                if len(parts) > 1:
                    return parts[1].strip()

        return None

    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools with descriptions"""
        return [
            {
                "name": "generate_posts",
                "description": "Generate 30 social media posts from a client brief",
                "parameters": "client_name, brief_path, num_posts (default 30), platform (default linkedin)",
            },
            {
                "name": "list_projects",
                "description": "List all projects, optionally filtered by client",
                "parameters": "client_name (optional), limit (default 10)",
            },
            {
                "name": "get_project_status",
                "description": "Get detailed status of a specific project",
                "parameters": "project_id",
            },
            {
                "name": "list_clients",
                "description": "Get list of all clients in the system",
                "parameters": "none",
            },
            {
                "name": "get_client_history",
                "description": "Get client's project history and statistics",
                "parameters": "client_name",
            },
            {
                "name": "collect_feedback",
                "description": "Collect post feedback from a client",
                "parameters": "client_name, project_id",
            },
            {
                "name": "collect_satisfaction",
                "description": "Collect satisfaction survey from a client",
                "parameters": "client_name, project_id",
            },
            {
                "name": "upload_voice_samples",
                "description": "Upload voice samples for better voice matching",
                "parameters": "client_name, file_paths (list), source (default mixed)",
            },
            {
                "name": "show_dashboard",
                "description": "Show analytics dashboard for all clients or specific client",
                "parameters": "client_name (optional)",
            },
            {
                "name": "read_file",
                "description": "Read content from a file (brief, feedback, etc.)",
                "parameters": "file_path",
            },
            {
                "name": "search_files",
                "description": "Search for files matching a pattern",
                "parameters": "pattern, directory (default data)",
            },
            {
                "name": "process_revision",
                "description": "Process revision request and regenerate posts based on client feedback",
                "parameters": "client_name, project_id, revision_notes, regenerate_count (default 5)",
            },
            {
                "name": "generate_analytics_report",
                "description": "Generate analytics report for client(s) showing performance metrics",
                "parameters": "client_name (optional), report_type (default summary)",
            },
            {
                "name": "create_posting_schedule",
                "description": "Create posting schedule for a project with specified frequency",
                "parameters": "client_name, project_id, posts_per_week (default 4), start_date (optional)",
            },
            # Skill access tools
            {
                "name": "get_available_skills",
                "description": "List all available skills (content-creator, marketing-strategy-pmm) with their references and capabilities",
                "parameters": "none",
            },
            {
                "name": "get_skill_info",
                "description": "Get detailed information about a specific skill including documentation and available references",
                "parameters": "skill_name (e.g., 'content-creator', 'marketing-strategy-pmm')",
            },
            {
                "name": "get_skill_reference",
                "description": "Get a specific reference document from a skill (e.g., brand guidelines, content frameworks)",
                "parameters": "skill_name, reference_name (without .md extension)",
            },
            {
                "name": "get_all_skill_references",
                "description": "Get all reference documents from a skill as a dictionary",
                "parameters": "skill_name",
            },
            # Research tools (paid add-ons $300-$600 each)
            {
                "name": "list_research_tools",
                "description": "List all available research tools with pricing ($300-$600 each)",
                "parameters": "none",
            },
            {
                "name": "run_research_tool",
                "description": "Execute a research tool (voice_analysis, seo_keyword_research, competitive_analysis, etc.)",
                "parameters": "tool_name, client_name, project_id, params (optional dict)",
            },
            {
                "name": "get_research_tool_info",
                "description": "Get detailed info about a specific research tool including use cases and required parameters",
                "parameters": "tool_name",
            },
            # Direct AI Agent access (no CLI wrappers)
            {
                "name": "list_ai_agents",
                "description": "List all available AI agents with their capabilities",
                "parameters": "none",
            },
            {
                "name": "parse_brief_direct",
                "description": "Parse raw client brief text into structured data using BriefParserAgent",
                "parameters": "brief_text",
            },
            {
                "name": "classify_client_direct",
                "description": "Classify client type (B2B_SAAS, AGENCY, COACH, CREATOR) for template selection",
                "parameters": "brief_text",
            },
            {
                "name": "validate_posts_direct",
                "description": "Run QA validation on posts using QAAgent (hooks, CTAs, length)",
                "parameters": "project_id, client_name",
            },
            {
                "name": "analyze_voice_direct",
                "description": "Analyze voice patterns from posts using VoiceAnalyzer (tones, archetypes, readability)",
                "parameters": "project_id, brief_text (optional)",
            },
            # Backend API - Client Management (CRUD)
            {
                "name": "list_clients_api",
                "description": "List all clients from backend API with pagination",
                "parameters": "skip (default 0), limit (default 100)",
            },
            {
                "name": "create_client_api",
                "description": "Create a new client in the system",
                "parameters": "name, business_description, ideal_customer, main_problem_solved, customer_pain_points, tone_preferences, platforms",
            },
            {
                "name": "get_client_api",
                "description": "Get a specific client by ID with full details",
                "parameters": "client_id",
            },
            {
                "name": "update_client_api",
                "description": "Update an existing client's information",
                "parameters": "client_id, name (optional), business_description (optional), ideal_customer (optional), main_problem_solved (optional)",
            },
            {
                "name": "delete_client_api",
                "description": "Delete a client from the system",
                "parameters": "client_id",
            },
            # Backend API - Project Management (CRUD)
            {
                "name": "list_projects_api",
                "description": "List projects with optional filters (client_id, status)",
                "parameters": "client_id (optional), status (optional), skip (default 0), limit (default 100)",
            },
            {
                "name": "create_project_api",
                "description": "Create a new project for a client",
                "parameters": "name, client_id, total_posts (default 30), platform (default linkedin)",
            },
            {
                "name": "get_project_api",
                "description": "Get a specific project by ID with full details",
                "parameters": "project_id",
            },
            {
                "name": "update_project_api",
                "description": "Update an existing project",
                "parameters": "project_id, name (optional), status (optional), total_posts (optional)",
            },
            {
                "name": "delete_project_api",
                "description": "Delete a project from the system",
                "parameters": "project_id",
            },
            # Backend API - Post Management
            {
                "name": "list_posts_api",
                "description": "List posts with filters (project_id, qa_status, template_id, platform)",
                "parameters": "project_id (optional), qa_status (optional), template_id (optional), platform (optional), skip, limit",
            },
            {
                "name": "get_post_api",
                "description": "Get a specific post by ID with full content",
                "parameters": "post_id",
            },
            {
                "name": "update_post_api",
                "description": "Update a post's content or QA status",
                "parameters": "post_id, content (optional), qa_status (optional: approved, rejected, pending)",
            },
            {
                "name": "approve_post",
                "description": "Approve a post (shortcut for updating qa_status to approved)",
                "parameters": "post_id",
            },
            {
                "name": "reject_post",
                "description": "Reject a post (shortcut for updating qa_status to rejected)",
                "parameters": "post_id",
            },
            # Backend API - Deliverable Management
            {
                "name": "list_deliverables_api",
                "description": "List deliverables with filters (client_id, status)",
                "parameters": "client_id (optional), status (optional: ready, pending, delivered), skip, limit",
            },
            {
                "name": "get_deliverable_api",
                "description": "Get a specific deliverable by ID",
                "parameters": "deliverable_id",
            },
            {
                "name": "get_deliverable_details_api",
                "description": "Get detailed deliverable info with file preview and QA summary",
                "parameters": "deliverable_id",
            },
            {
                "name": "mark_deliverable_delivered_api",
                "description": "Mark a deliverable as delivered with optional proof",
                "parameters": "deliverable_id, proof_url (optional), proof_notes (optional)",
            },
            {
                "name": "get_deliverable_download_path",
                "description": "Get the file path for downloading a deliverable",
                "parameters": "deliverable_id",
            },
            # Backend API - Run Management
            {
                "name": "list_runs_api",
                "description": "List generation runs with filters (project_id, status)",
                "parameters": "project_id (optional), status (optional: pending, running, succeeded, failed), skip, limit",
            },
            {
                "name": "get_run_api",
                "description": "Get a specific run by ID with logs",
                "parameters": "run_id",
            },
            # Backend API - Brief Management
            {
                "name": "create_brief_api",
                "description": "Create a brief for a project",
                "parameters": "project_id, content",
            },
            {
                "name": "get_brief_api",
                "description": "Get a specific brief by ID",
                "parameters": "brief_id",
            },
            {
                "name": "get_brief_by_project_api",
                "description": "Get a brief by project ID",
                "parameters": "project_id",
            },
            # Google Trends Integration
            {
                "name": "search_trends_interest",
                "description": "Search Google Trends for keyword interest over time",
                "parameters": "keywords (list, max 5), client_id (optional), project_id (optional), timeframe (optional), geo (optional), category (optional)",
            },
            {
                "name": "search_trends_related_queries",
                "description": "Search Google Trends for related top and rising queries",
                "parameters": "keywords (list, max 5), client_id (optional), project_id (optional), timeframe (optional), geo (optional), category (optional)",
            },
            {
                "name": "compute_trends_insight",
                "description": "Compute insights for a keyword from stored trends data (trend direction, seasonality, recommendations)",
                "parameters": "keyword, client_id (optional), project_id (optional)",
            },
            {
                "name": "get_trends_history",
                "description": "Get Google Trends search history with optional filters",
                "parameters": "client_id (optional), project_id (optional), limit (default 50)",
            },
            {
                "name": "get_trends_insights",
                "description": "Get all computed keyword insights sorted by priority",
                "parameters": "client_id (optional), project_id (optional), min_priority (default 0)",
            },
            {
                "name": "get_trends_timeframes",
                "description": "Get available timeframe options for trends searches",
                "parameters": "none",
            },
            {
                "name": "get_trends_categories",
                "description": "Get available category options for trends searches",
                "parameters": "none",
            },
        ]
