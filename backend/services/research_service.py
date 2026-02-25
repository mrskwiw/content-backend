"""
Research Service - Orchestrates research tool execution

Handles:
- Mapping research tool names to implementations
- Brief file creation for research tools
- Research tool execution
- Output file management
"""

import sys
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy.orm import Session

# Add src directory to path for imports
# In Docker: /app/src
# In local dev: {project_root}/src
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if src_path.exists():
    sys.path.insert(0, str(project_root))
else:
    # Fallback: might be in /app in Docker
    app_src = Path("/app/src")
    if app_src.exists():
        sys.path.insert(0, "/app")

# Try importing research tools
RESEARCH_TOOLS_AVAILABLE = False
RESEARCH_TOOL_MAP = {}

try:
    from src.research.voice_analysis import VoiceAnalyzer
    from src.research.brand_archetype import BrandArchetypeAnalyzer
    from src.research.seo_keyword_research import SEOKeywordResearcher
    from src.research.competitive_analysis import CompetitiveAnalyzer
    from src.research.content_gap_analysis import ContentGapAnalyzer
    from src.research.market_trends_research import MarketTrendsResearcher
    from src.research.content_audit import ContentAuditor
    from src.research.platform_strategy import PlatformStrategist
    from src.research.content_calendar_strategy import ContentCalendarStrategist
    from src.research.audience_research import AudienceResearcher
    from src.research.icp_workshop import ICPWorkshopFacilitator
    from src.research.story_mining import StoryMiner

    RESEARCH_TOOLS_AVAILABLE = True
    RESEARCH_TOOL_MAP = {
        "voice_analysis": VoiceAnalyzer,
        "brand_archetype": BrandArchetypeAnalyzer,
        "seo_keyword_research": SEOKeywordResearcher,
        "competitive_analysis": CompetitiveAnalyzer,
        "content_gap_analysis": ContentGapAnalyzer,
        "market_trends_research": MarketTrendsResearcher,
        "content_audit": ContentAuditor,
        "platform_strategy": PlatformStrategist,
        "content_calendar": ContentCalendarStrategist,
        "audience_research": AudienceResearcher,
        "icp_workshop": ICPWorkshopFacilitator,
        "story_mining": StoryMiner,
    }
except ImportError as e:
    # Research tools not available - service will return stub responses
    RESEARCH_TOOLS_AVAILABLE = False
    RESEARCH_TOOL_MAP = {}
    logger = __import__("logging").getLogger(__name__)
    logger.warning(f"Research tools not available: {str(e)}")

# IMPORTANT: Use relative imports to avoid SQLAlchemy table redefinition errors
# Absolute imports (backend.models) cause circular dependencies in production
from backend.models import Project, Client  # noqa: E402
from backend.services import crud  # noqa: E402

# Logger import with fallback
try:
    import sys
    from pathlib import Path

    # Add src to path for logger
    project_root = Path(__file__).parent.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from utils.logger import logger
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


class ResearchService:
    """Service for research tool execution"""

    def __init__(self):
        # No specific initialization needed
        pass

    async def execute_research_tool(
        self,
        db: Session,
        project_id: str,
        client_id: str,
        tool_name: str,
        params: Optional[Dict] = None,
    ) -> Dict[str, any]:
        """
        Execute a research tool

        Args:
            db: Database session
            project_id: Project ID
            client_id: Client ID
            tool_name: Name of research tool to execute
            params: Optional parameters for the tool

        Returns:
            Dict with:
                - success: bool
                - outputs: Dict[str, str] (format -> file path)
                - metadata: Dict with execution metadata
                - error: Optional error message
        """
        logger.info(f"Executing research tool '{tool_name}' for project {project_id}")

        # Get project and client
        project = crud.get_project(db, project_id)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        client = crud.get_client(db, client_id)
        if not client:
            raise ValueError(f"Client {client_id} not found")

        # Check if research tools are available
        if not RESEARCH_TOOLS_AVAILABLE:
            logger.warning(
                f"Research tools not available - returning demo response for '{tool_name}'"
            )
            # Return demo response with realistic sample data
            return self._get_demo_response(tool_name, project_id, client)

        # Check if tool exists
        if tool_name not in RESEARCH_TOOL_MAP:
            raise ValueError(f"Research tool '{tool_name}' not found")

        # Get tool class
        ToolClass = RESEARCH_TOOL_MAP[tool_name]

        # Prepare inputs based on tool requirements
        inputs = self._prepare_inputs(project, client, tool_name, params or {})

        try:
            # Instantiate and execute tool
            tool = ToolClass(project_id=project_id)
            result = tool.execute(inputs)

            # Get tool metadata for database storage
            from backend.routers.research import RESEARCH_TOOLS

            tool_class_metadata = next(
                (t.dict() for t in RESEARCH_TOOLS if t.name == tool_name),
                {"label": tool_name, "price": None},
            )

            # Save result to database
            import uuid
            from datetime import datetime
            from backend.models import ResearchResult

            research_result = ResearchResult(
                id=f"res-{uuid.uuid4().hex[:12]}",
                user_id=project.user_id,
                client_id=client_id,
                project_id=project_id,
                tool_name=tool_name,
                tool_label=tool_class_metadata.get("label"),
                tool_price=tool_class_metadata.get("price"),
                params=params,
                outputs=result.outputs,
                data=result.metadata.get("data"),  # Tool-specific structured data
                status="completed" if result.success else "failed",
                error_message=result.error,
                duration_seconds=result.metadata.get("duration_seconds"),
                created_at=datetime.utcnow(),
            )

            db.add(research_result)
            db.commit()
            db.refresh(research_result)

            # Convert result to backend format with database ID
            return {
                "success": result.success,
                "outputs": {k: str(v) for k, v in result.outputs.items()},
                "metadata": {
                    **result.metadata,
                    "executed_at": result.executed_at.isoformat(),
                    "tool_name": result.tool_name,
                    "result_id": research_result.id,  # Add database ID for cache storage
                },
                "error": result.error,
            }

        except Exception as e:
            logger.error(f"Research tool execution failed: {str(e)}", exc_info=True)
            return {
                "success": False,
                "outputs": {},
                "metadata": {
                    "tool_name": tool_name,
                    "project_id": project_id,
                },
                "error": str(e),
            }

    def _get_demo_response(
        self,
        tool_name: str,
        project_id: str,
        client: Client,
    ) -> Dict:
        """
        Generate realistic demo response for research tools when actual tools unavailable.
        This allows the UI to demonstrate the feature during demos.
        """
        from datetime import datetime

        client_name = client.name if client else "Demo Client"
        base_response = {
            "success": True,
            "metadata": {
                "status": "completed",
                "duration_seconds": 2.5,
                "tool_name": tool_name,
                "project_id": project_id,
                "executed_at": datetime.utcnow().isoformat(),
                "note": "Demo data - full analysis requires API key configuration",
            },
            "error": None,
        }

        # Tool-specific demo data
        demo_data = {
            "voice_analysis": {
                "summary": f"Voice analysis for {client_name}",
                "tone": "Professional and approachable",
                "readability_score": 72.5,
                "reading_level": "8th grade",
                "voice_dimensions": {
                    "formality": 0.7,
                    "enthusiasm": 0.6,
                    "technical_depth": 0.5,
                    "warmth": 0.65,
                },
                "recommendations": [
                    "Maintain conversational tone while keeping authority",
                    "Use more storytelling elements",
                    "Add concrete examples to abstract concepts",
                ],
            },
            "brand_archetype": {
                "summary": f"Brand archetype analysis for {client_name}",
                "primary_archetype": "Expert/Sage",
                "secondary_archetype": "Guide/Mentor",
                "archetype_traits": [
                    "Knowledge-focused",
                    "Trustworthy advisor",
                    "Clear communicator",
                ],
                "content_themes": [
                    "Industry insights and trends",
                    "How-to guides and tutorials",
                    "Thought leadership pieces",
                ],
                "voice_guidelines": {
                    "do": ["Share expertise generously", "Use data to support claims"],
                    "avoid": ["Being condescending", "Oversimplifying complex topics"],
                },
            },
            "competitive_analysis": {
                "summary": f"Competitive landscape for {client_name}",
                "competitors_analyzed": 3,
                "market_position": "Challenger with differentiation opportunity",
                "content_gaps": [
                    "Video content underutilized by competitors",
                    "LinkedIn presence stronger than competitors",
                    "Educational content opportunity",
                ],
                "differentiation_opportunities": [
                    "More personal storytelling",
                    "Behind-the-scenes content",
                    "Customer success stories",
                ],
            },
            "market_trends_research": {
                "summary": f"Market trends for {client_name}'s industry",
                "trending_topics": [
                    "AI integration in workflows",
                    "Remote work optimization",
                    "Sustainability practices",
                ],
                "content_opportunities": [
                    "Thought leadership on industry changes",
                    "Practical implementation guides",
                    "Case studies and results",
                ],
                "recommended_hashtags": ["#Innovation", "#FutureOfWork", "#Leadership"],
            },
            "seo_keyword_research": {
                "summary": f"SEO keyword analysis for {client_name}",
                "primary_keywords": [
                    {"keyword": "business solutions", "volume": 12000, "difficulty": 65},
                    {"keyword": "workflow automation", "volume": 8500, "difficulty": 55},
                ],
                "long_tail_opportunities": [
                    "how to improve team productivity",
                    "best practices for remote teams",
                ],
                "content_recommendations": [
                    "Create pillar content around primary keywords",
                    "Build topic clusters with long-tail content",
                ],
            },
        }

        # Get tool-specific data or generic response
        tool_data = demo_data.get(
            tool_name,
            {
                "summary": f"Analysis completed for {client_name}",
                "status": "Demo data generated",
                "recommendations": ["Full analysis available with API configuration"],
            },
        )

        base_response["data"] = tool_data
        base_response["outputs"] = {}  # No file outputs for demo mode

        return base_response

    def _prepare_inputs(
        self,
        project: Project,
        client: Client,
        tool_name: str,
        params: Dict,
    ) -> Dict:
        """
        Prepare inputs for research tool execution

        Args:
            project: Project model
            client: Client model
            tool_name: Name of research tool
            params: Additional parameters

        Returns:
            Dict of inputs for the research tool
        """
        # Base inputs common to all tools
        # Use Client model fields (business_description, ideal_customer) instead of non-existent Project fields
        inputs = {
            "company_name": client.name,
            "business_description": client.business_description or "",
            "target_audience": client.ideal_customer or "",
            "platforms": project.platforms or ["LinkedIn"],
            **params,  # Merge in additional parameters
        }

        # Tool-specific input preparation
        if tool_name == "voice_analysis":
            # Voice analysis needs sample content
            inputs["content_samples"] = params.get("content_samples", [])

        elif tool_name == "brand_archetype":
            # Brand archetype needs tone and values
            inputs["tone_preference"] = project.tone or "professional"
            inputs["brand_values"] = params.get("brand_values", [])

        elif tool_name == "seo_keyword_research":  # Fixed: was "seo_keyword"
            # SEO keyword research needs industry/niche
            inputs["industry"] = (
                params.get("industry") or client.business_description or "General business"
            )
            inputs["target_keywords"] = params.get("target_keywords", [])
            inputs["main_topics"] = params.get("main_topics", [])  # Required by tool

        elif tool_name == "competitive_analysis":
            # Competitive analysis needs competitor list
            inputs["competitors"] = params.get("competitors", [])

        elif tool_name == "content_gap_analysis":
            # Content gap needs current topics
            inputs["current_content_topics"] = params.get("current_content_topics", [])

        elif tool_name == "market_trends":
            # Market trends needs industry context
            inputs["industry"] = (
                params.get("industry") or client.business_description or "General business"
            )

        return inputs


# Global instance
research_service = ResearchService()
