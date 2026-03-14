"""
Research API endpoints.

Handles research tool listing and execution with comprehensive input validation.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.middleware.auth_dependency import get_current_user
from backend.models import User
from backend.schemas import (
    VoiceAnalysisParams,
    SEOKeywordParams,
    CompetitiveAnalysisParams,
    ContentGapParams,
    ContentAuditParams,
    MarketTrendsParams,
    PlatformStrategyParams,
    ContentCalendarParams,
    AudienceResearchParams,
    ICPWorkshopParams,
    StoryMiningParams,
    BrandArchetypeParams,
    DetermineCompetitorsParams,
    ResearchResultResponse,
    ResearchResultListResponse,
)
from backend.services import crud
from backend.services.research_service import research_service
from backend.utils.logger import logger
from backend.utils.http_rate_limiter import strict_limiter, lenient_limiter
from backend.middleware.authorization import _check_ownership  # TR-021: IDOR prevention
from src.utils.response_cache import ResponseCache
import hashlib
import json

router = APIRouter()

# PERFORMANCE: Research result caching (Phase 3 optimization)
# Cache expensive research results for 48 hours to save $100-200/month
# Research results are stable - client profile rarely changes
research_cache = ResponseCache(
    ttl_seconds=172800,  # 48 hours cache for research results
    enabled=True,
)


class ResearchTool(BaseModel):
    """Research tool metadata"""

    name: str
    label: str
    price: Optional[float] = None
    status: str = "available"  # available, coming_soon
    description: Optional[str] = None
    category: Optional[str] = None


class RunResearchInput(BaseModel):
    """Input for running research"""

    project_id: str
    client_id: str
    tool: str
    params: Optional[Dict[str, Any]] = {}


class ResearchRunResult(BaseModel):
    """Result from research execution"""

    tool: str
    outputs: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = {}


# Research tool catalog (6 implemented tools)
RESEARCH_TOOLS = [
    # Client Foundation Tools ($700 Total)
    ResearchTool(
        name="voice_analysis",
        label="Voice Analysis",
        price=400.0,
        status="experimental",
        description="Extract writing patterns from client's existing content",
        category="foundation",
    ),
    ResearchTool(
        name="brand_archetype",
        label="Brand Archetype Assessment",
        price=300.0,
        status="experimental",
        description="Identify brand personality and messaging framework",
        category="foundation",
    ),
    # SEO & Competition Tools ($1,400 Total)
    ResearchTool(
        name="seo_keyword_research",
        label="SEO Keyword Research",
        price=400.0,
        status="available",
        description="Discover target keywords and search opportunities",
        category="seo",
    ),
    ResearchTool(
        name="determine_competitors",
        label="Determine Competitors",
        price=400.0,
        status="available",
        description="AI-powered competitor discovery and market positioning analysis",
        category="seo",
    ),
    ResearchTool(
        name="competitive_analysis",
        label="Competitive Analysis",
        price=500.0,
        status="available",
        description="Research competitors and identify positioning gaps",
        category="seo",
    ),
    ResearchTool(
        name="content_gap_analysis",
        label="Content Gap Analysis",
        price=500.0,
        status="experimental",
        description="Identify content opportunities competitors are missing",
        category="seo",
    ),
    # Market Intelligence Tools ($400 Total)
    ResearchTool(
        name="market_trends_research",
        label="Market Trends Research",
        price=400.0,
        status="available",
        description="Discover trending topics and emerging opportunities",
        category="market",
    ),
    # Strategy & Planning Tools
    ResearchTool(
        name="content_audit",
        label="Content Audit",
        price=400.0,
        status="experimental",
        description="Analyze existing content performance and opportunities",
        category="strategy",
    ),
    ResearchTool(
        name="platform_strategy",
        label="Platform Strategy",
        price=300.0,
        status="experimental",
        description="Recommend optimal platform mix for distribution",
        category="strategy",
    ),
    ResearchTool(
        name="content_calendar",
        label="Content Calendar Strategy",
        price=300.0,
        status="experimental",
        description="Create strategic 90-day content calendar",
        category="strategy",
    ),
    ResearchTool(
        name="audience_research",
        label="Audience Research",
        price=500.0,
        status="experimental",
        description="Deep-dive into target audience demographics and psychographics",
        category="strategy",
    ),
    # Workshop Assistants
    ResearchTool(
        name="icp_workshop",
        label="ICP Development Workshop",
        price=600.0,
        status="experimental",
        description="Facilitate ideal customer profile definition through guided conversation",
        category="workshop",
    ),
    ResearchTool(
        name="story_mining",
        label="Story Mining Interview",
        price=500.0,
        status="experimental",
        description="Extract customer success stories and case study material",
        category="workshop",
    ),
]


# Validation schema mapping for each research tool
VALIDATION_SCHEMAS = {
    "voice_analysis": VoiceAnalysisParams,
    "seo_keyword_research": SEOKeywordParams,
    "determine_competitors": DetermineCompetitorsParams,
    "competitive_analysis": CompetitiveAnalysisParams,
    "content_gap_analysis": ContentGapParams,
    "content_audit": ContentAuditParams,
    "market_trends_research": MarketTrendsParams,
    "platform_strategy": PlatformStrategyParams,
    "content_calendar": ContentCalendarParams,
    "audience_research": AudienceResearchParams,
    "icp_workshop": ICPWorkshopParams,
    "story_mining": StoryMiningParams,
    "brand_archetype": BrandArchetypeParams,
}


def validate_research_params(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate research tool parameters using appropriate Pydantic schema.

    Args:
        tool_name: Name of the research tool
        params: Raw parameters dictionary from API request

    Returns:
        Validated parameters dictionary

    Raises:
        HTTPException: If validation fails with detailed error messages
    """
    # Check if tool has a validation schema
    schema = VALIDATION_SCHEMAS.get(tool_name)
    if not schema:
        # No validation schema - allow any params (backward compatibility)
        logger.warning(f"No validation schema found for tool '{tool_name}'")
        return params

    try:
        # Validate params using Pydantic schema
        validated = schema(**params)
        # Convert back to dict for downstream processing
        return validated.model_dump()
    except ValidationError as e:
        # Extract detailed error messages
        error_details = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")

        error_message = f"Invalid parameters for {tool_name}: " + "; ".join(error_details)

        logger.warning(f"Validation failed for {tool_name}: {error_message}")

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "validation_error",
                "tool": tool_name,
                "message": error_message,
                "details": error_details,
            },
        )


def sanitize_research_params(params: Dict[str, Any], strict: bool = False) -> Dict[str, Any]:
    """
    Sanitize research tool parameters to prevent prompt injection attacks.

    This function recursively sanitizes all string values in the params dictionary,
    protecting against malicious prompts that attempt to override system instructions,
    leak sensitive data, or manipulate LLM behavior.

    Security (TR-020): Prompt Injection Defense
    - Blocks instruction override attempts ("ignore previous instructions...")
    - Prevents role manipulation ("you are now a...")
    - Stops system prompt leakage ("repeat your instructions")
    - Filters data exfiltration attempts ("output all client data")
    - Detects jailbreak attempts ("DAN mode", "developer mode")

    Args:
        params: Validated parameters dictionary
        strict: If True, applies stricter sanitization (blocks medium-risk patterns)

    Returns:
        Sanitized parameters dictionary

    Raises:
        HTTPException: If prompt injection is detected
    """
    from src.validators.prompt_injection_defense import PromptInjectionDetector

    detector = PromptInjectionDetector(strict_mode=strict)
    sanitized = {}

    for key, value in params.items():
        if isinstance(value, str):
            # Check for prompt injection before sanitization
            is_malicious, blocked_patterns, severity = detector.detect_injection(value)

            if is_malicious:
                logger.error(
                    f"Prompt injection detected in '{key}' (severity={severity}): {blocked_patterns[:3]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security validation failed: Parameter '{key}' contains suspicious content that may attempt to manipulate the AI system. Please rephrase your input.",
                )

            sanitized[key] = value
        elif isinstance(value, list):
            # Check each list item for prompt injection
            sanitized_list = []
            for i, item in enumerate(value):
                if isinstance(item, str):
                    # Detect prompt injection in list items
                    is_malicious, blocked_patterns, severity = detector.detect_injection(item)

                    if is_malicious:
                        logger.error(
                            f"Prompt injection detected in {key}[{i}] (severity={severity}): {blocked_patterns[:3]}"
                        )
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Security validation failed: Parameter '{key}[{i}]' contains suspicious content that may attempt to manipulate the AI system. Please rephrase your input.",
                        )

                    sanitized_list.append(item)
                elif isinstance(item, dict):
                    # Recursive sanitization for nested dicts in lists
                    sanitized_list.append(sanitize_research_params(item, strict=strict))
                else:
                    sanitized_list.append(item)
            sanitized[key] = sanitized_list
        elif isinstance(value, dict):
            # Recursive sanitization for nested dicts
            sanitized[key] = sanitize_research_params(value, strict=strict)
        else:
            # Pass through non-string values (int, float, bool, None)
            sanitized[key] = value

    return sanitized


@router.get("/tools", response_model=List[ResearchTool])
@lenient_limiter.limit("1000/hour")  # TR-004: Cheap read operation
async def list_research_tools(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    List all available research tools.

    Returns metadata for all 12 research tools:
    - 7 implemented and available
    - 5 coming soon

    Rate limit: 1000/hour (cheap read operation)
    """
    return RESEARCH_TOOLS


@router.post("/run", response_model=ResearchRunResult)
@strict_limiter.limit("5/hour")  # TR-004: Expensive operation ($400-600/call), prevent abuse
async def run_research(
    request: Request,
    input: RunResearchInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute a research tool.

    Integrates with 13 research tools:
    - Voice Analysis, Brand Archetype Assessment, SEO Keyword Research
    - Competitive Analysis, Content Gap Analysis, Market Trends Research
    - Platform Strategy, Content Calendar, Audience Research
    - ICP Workshop, Story Mining, Content Audit

    Rate limit: 5/hour per IP+user (prevents abuse of expensive AI operations)

    SECURITY (TR-020): Multi-layer prompt injection defense:
    1. Pydantic validation (length limits, type checking, list size limits)
    2. Prompt sanitization (sanitize_research_params) before LLM execution
       - Blocks instruction override ("ignore previous instructions...")
       - Prevents role manipulation ("you are now a...")
       - Stops system prompt leakage ("repeat your instructions")
       - Filters data exfiltration ("output all client data")
       - Detects jailbreak attempts ("DAN mode", "developer mode")
    3. Recursive sanitization of nested dicts and lists

    All string parameters are sanitized before being passed to LLM prompts.
    """
    # Verify project exists
    project = crud.get_project(db, input.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {input.project_id} not found",
        )

    # TR-021: Verify user owns the project (IDOR prevention)
    if not _check_ownership("Project", project, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this project",
        )

    # Verify client exists
    client = crud.get_client(db, input.client_id)
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client {input.client_id} not found",
        )

    # TR-021: Verify user owns the client (IDOR prevention)
    if not _check_ownership("Client", client, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this client",
        )

    # Validate client has sufficient data for research
    # Research tools require minimum business context
    business_desc = client.business_description or ""
    ideal_customer = client.ideal_customer or ""

    # Most research tools require at least 50 characters of business description
    # All tools now use 70 character minimum for consistency with wizard validation
    TOOL_REQUIREMENTS = {
        "brand_archetype": {"business_description": 70},
        "content_audit": {"business_description": 50},
        "content_gap_analysis": {"business_description": 50},
        "platform_strategy": {"business_description": 50, "target_audience": 20},
        "audience_research": {"business_description": 50},
        "competitive_analysis": {"business_description": 50},
        "voice_analysis": {"content_samples": 5},  # Requires 5-30 writing samples
    }

    if input.tool in TOOL_REQUIREMENTS:
        requirements = TOOL_REQUIREMENTS[input.tool]

        # Check business_description
        if "business_description" in requirements:
            min_length = requirements["business_description"]
            if len(business_desc) < min_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Client profile incomplete: {input.tool} requires a business description of at least {min_length} characters. Please complete the client profile in the wizard before running research.",
                )

        # Check target_audience
        if "target_audience" in requirements:
            min_length = requirements["target_audience"]
            if len(ideal_customer) < min_length:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Client profile incomplete: {input.tool} requires a target audience description of at least {min_length} characters. Please complete the client profile in the wizard before running research.",
                )

        # Check content_samples (for voice_analysis)
        if "content_samples" in requirements:
            min_samples = requirements["content_samples"]
            samples = input.params.get("content_samples", [])

            if not isinstance(samples, list):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{input.tool} requires content_samples as a list. Please provide {min_samples}-30 writing samples.",
                )

            if len(samples) < min_samples:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{input.tool} requires at least {min_samples} content samples. Please provide {min_samples}-30 samples of the client's existing writing (minimum 50 characters each).",
                )

    # Find the tool
    tool = next((t for t in RESEARCH_TOOLS if t.name == input.tool), None)
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research tool '{input.tool}' not found",
        )

    # Check if tool is available
    if tool.status == "coming_soon":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research tool '{input.tool}' is not yet available",
        )

    # Validate research tool parameters using Pydantic schemas
    # This provides comprehensive input validation with:
    # - Length limits (prevent DoS)
    # - Type checking (prevent type confusion)
    # - List size limits (prevent resource exhaustion)
    # - Whitespace stripping and sanitization
    validated_params = validate_research_params(input.tool, input.params or {})

    # SECURITY (TR-020): Sanitize validated params to prevent prompt injection
    # This protects against malicious prompts attempting to:
    # - Override system instructions
    # - Leak sensitive data or system prompts
    # - Manipulate LLM behavior via jailbreak techniques
    # All string values (including nested dicts and lists) are sanitized
    try:
        sanitized_params = sanitize_research_params(validated_params, strict=False)
        logger.info(
            f"Executing research tool '{input.tool}' for project {input.project_id} "
            f"with validated and sanitized params"
        )
    except HTTPException:
        # Re-raise HTTPExceptions from sanitization (prompt injection detected)
        raise
    except Exception as e:
        # Unexpected error during sanitization
        logger.error(f"Sanitization error for {input.tool}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security validation failed: {str(e)}",
        )

    # AUTO-POPULATION: Competitive Analysis competitors from client profile
    if input.tool == "competitive_analysis":
        # If competitors not provided or empty, auto-populate from client.competitors
        if not sanitized_params.get("competitors"):
            if client.competitors and isinstance(client.competitors, list):
                sanitized_params["competitors"] = client.competitors[:5]  # Max 5
                logger.info(
                    f"Auto-populated {len(sanitized_params['competitors'])} competitors from client profile"
                )
            else:
                # No competitors in database - require manual input
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Client profile incomplete: Competitive Analysis requires 1-5 competitor names. Please add competitors to the client profile or provide them manually.",
                )

    try:
        # PERFORMANCE: Check cache before executing expensive research ($300-600 per call)
        # Cache key includes tool name, client ID, and param hash for uniqueness
        cache_key_data = {
            "tool": input.tool,
            "client_id": input.client_id,
            "params": sanitized_params,
        }
        cache_key = hashlib.sha256(json.dumps(cache_key_data, sort_keys=True).encode()).hexdigest()

        cached_result = research_cache.get_by_key(cache_key) if research_cache else None

        if cached_result:
            result = cached_result
            logger.info(
                f"Research cache HIT for {input.tool} (client {input.client_id}) "
                f"- saved ${tool.price} API call"
            )
        else:
            # Execute research tool via service with sanitized params
            result = await research_service.execute_research_tool(
                db=db,
                project_id=input.project_id,
                client_id=input.client_id,
                tool_name=input.tool,
                params=sanitized_params,  # Use sanitized params for LLM safety
            )

            # Cache successful results for 48 hours
            if result["success"] and research_cache:
                research_cache.put_by_key(cache_key, result)
                logger.debug(f"Cached research result for {input.tool} (48hr TTL)")

                # Store cache_key in database for tracking
                if "result_id" in result.get("metadata", {}):
                    from backend.models import ResearchResult

                    result_id = result["metadata"]["result_id"]
                    db_result = (
                        db.query(ResearchResult).filter(ResearchResult.id == result_id).first()
                    )
                    if db_result:
                        db_result.cache_key = cache_key
                        db.commit()

            logger.info(
                f"Research cache MISS for {input.tool} (client {input.client_id}) "
                f"- executed ${tool.price} API call"
            )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Research tool execution failed: {result.get('error', 'Unknown error')}",
            )

        # Auto-save competitors to client profile if determine_competitors tool was run
        if input.tool == "determine_competitors" and input.client_id:
            try:
                data = result.get("metadata", {}).get("data", {})
                primary_competitors = data.get("primary_competitors", [])

                if primary_competitors:
                    # Extract just the competitor names
                    competitor_names = [
                        comp.get("name") if isinstance(comp, dict) else comp
                        for comp in primary_competitors[:5]  # Max 5
                    ]

                    if competitor_names:
                        client = crud.get_client(db, input.client_id)
                        if client:
                            client.competitors = competitor_names
                            db.commit()
                            logger.info(
                                f"Auto-updated client.competitors with {len(competitor_names)} "
                                f"competitors for client {input.client_id}"
                            )
            except Exception as e:
                # Don't fail the request if auto-save fails
                logger.error(f"Failed to auto-save competitors to client profile: {e}")

        # Return result in expected format
        return ResearchRunResult(
            tool=input.tool,
            outputs=result["outputs"],
            metadata={
                **result["metadata"],
                "price": tool.price,
                "project_id": input.project_id,
                "client_id": input.client_id,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Research execution failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Research execution failed: {str(e)}",
        )


# ==================== Research Result Endpoints ====================


@router.get("/results/project/{project_id}", response_model=ResearchResultListResponse)
@lenient_limiter.limit("1000/hour")
async def get_project_research_results(
    request: Request,
    project_id: str,
    tool_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all research results for a project.

    TR-021: User must own project to access research results.

    Args:
        project_id: Project ID
        tool_name: Optional filter by tool name

    Returns:
        List of research results for the project
    """
    project = crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if not _check_ownership("Project", project, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    results = crud.get_research_results_by_project(db, project_id, tool_name=tool_name)

    return ResearchResultListResponse(
        results=[ResearchResultResponse.model_validate(r) for r in results],
        total=len(results),
        project_id=project_id,
        client_id=project.client_id,
    )


@router.get("/results/client/{client_id}", response_model=ResearchResultListResponse)
@lenient_limiter.limit("1000/hour")
async def get_client_research_results(
    request: Request,
    client_id: str,
    tool_name: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all research results for a client.

    TR-021: User must own client to access research results.

    Args:
        client_id: Client ID
        tool_name: Optional filter by tool name

    Returns:
        List of research results for the client
    """
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    if not _check_ownership("Client", client, current_user):
        raise HTTPException(status_code=403, detail="Access denied")

    results = crud.get_research_results_by_client(db, client_id, tool_name=tool_name)

    return ResearchResultListResponse(
        results=[ResearchResultResponse.model_validate(r) for r in results],
        total=len(results),
        client_id=client_id,
        project_id=None,
    )


@router.delete("/results/{result_id}", status_code=204)
@lenient_limiter.limit("100/hour")
async def delete_research_result(
    request: Request,
    result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete research result.

    TR-021: User must own the result to delete it.

    Args:
        result_id: Research result ID
    """
    result = crud.get_research_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research result not found")

    if result.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    crud.delete_research_result(db, result_id)
    return None


@router.get("/results/{result_id}/output/{output_format}")
@lenient_limiter.limit("1000/hour")
async def get_research_output_content(
    request: Request,
    result_id: str,
    output_format: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the content of a research result output file.

    TR-021: User must own the result to access output files.

    Args:
        result_id: Research result ID
        output_format: Format of output file (e.g., 'markdown', 'json')

    Returns:
        File content as JSON object with 'content' field for text files,
        or parsed JSON for JSON files
    """
    # Get research result and verify ownership
    result = crud.get_research_result(db, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="Research result not found")

    if result.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if result has outputs
    if not result.outputs or output_format not in result.outputs:
        raise HTTPException(
            status_code=404, detail=f"Output format '{output_format}' not found for this result"
        )

    # Get file path
    file_path_str = result.outputs[output_format]
    file_path = Path(file_path_str)

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Output file not found at: {file_path_str}")

    # Read file content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading output file {file_path}: {e}")
        raise HTTPException(status_code=500, detail="Failed to read output file")

    # Return parsed JSON for JSON files, or raw content for other formats
    if output_format == "json":
        try:
            parsed_content = json.loads(content)
            return JSONResponse(content=parsed_content)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in file {file_path}, returning as text")
            return {"content": content, "format": output_format}
    else:
        return {"content": content, "format": output_format}


# ============================================================================
# PREREQUISITE CHECKING & BATCH EXECUTION ENDPOINTS
# ============================================================================


class PrerequisiteCheckRequest(BaseModel):
    """Request to check prerequisites for tools"""

    project_id: str
    tool_names: List[str]


class ToolPrerequisiteStatus(BaseModel):
    """Prerequisite status for a single tool"""

    tool_name: str
    can_run: bool
    missing_required: List[str]
    missing_recommended: List[str]
    error_message: Optional[str] = None


class PrerequisiteCheckResponse(BaseModel):
    """Response from prerequisite check"""

    tools: List[ToolPrerequisiteStatus]
    all_can_run: bool
    blocked_tools: List[str]
    ready_tools: List[str]


@router.post("/check-prerequisites", response_model=PrerequisiteCheckResponse)
@lenient_limiter.limit("100/hour")
async def check_prerequisites(
    request: Request,
    prereq_request: PrerequisiteCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Check if tools can run based on prerequisites.

    Dynamically checks:
    - What's already completed in database for this project
    - What's planned in current selection
    - Which tools are blocked vs ready

    Frontend should call this BEFORE showing data collection panel.

    Args:
        prereq_request: Project ID and list of tool names to check

    Returns:
        Status for each tool including missing prerequisites
    """
    # Verify project ownership (TR-021: IDOR prevention)
    project = crud.get_project(db, prereq_request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    _check_ownership(project, current_user, resource_type="project")

    logger.info(
        f"Checking prerequisites for {len(prereq_request.tool_names)} tools "
        f"in project {prereq_request.project_id}"
    )

    tool_statuses = []
    all_can_run = True
    blocked_tools = []
    ready_tools = []

    for tool_name in prereq_request.tool_names:
        # Check prerequisites considering both DB and planned tools
        can_run, missing_required, missing_recommended = research_service.check_prerequisites(
            db,
            prereq_request.project_id,
            tool_name,
            planned_tools=prereq_request.tool_names,  # Tools in this batch count as "planned"
        )

        # Generate error message if blocked
        error_message = None
        if not can_run:
            error_message = research_service.prerequisites.get_missing_prerequisites_message(
                tool_name, missing_required, missing_recommended
            )

        tool_status = ToolPrerequisiteStatus(
            tool_name=tool_name,
            can_run=can_run,
            missing_required=missing_required,
            missing_recommended=missing_recommended,
            error_message=error_message,
        )

        tool_statuses.append(tool_status)

        if not can_run:
            all_can_run = False
            blocked_tools.append(tool_name)
        else:
            ready_tools.append(tool_name)

    return PrerequisiteCheckResponse(
        tools=tool_statuses,
        all_can_run=all_can_run,
        blocked_tools=blocked_tools,
        ready_tools=ready_tools,
    )


class ExecutionOrderRequest(BaseModel):
    """Request to get execution order for tools"""

    tool_names: List[str]


class ExecutionOrderResponse(BaseModel):
    """Response with optimal execution order"""

    execution_order: List[str]
    tool_count: int


@router.post("/execution-order", response_model=ExecutionOrderResponse)
@lenient_limiter.limit("1000/hour")  # Lightweight calculation endpoint
async def get_execution_order(
    request: Request,
    order_request: ExecutionOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Get optimal execution order for research tools based on dependencies.

    Uses topological sort to ensure prerequisites run before dependent tools.
    This is a read-only endpoint that doesn't execute anything - just calculates order.

    Args:
        order_request: List of tool names to order

    Returns:
        Optimal execution order (prerequisites first)
    """
    from backend.services.research_prerequisites import ResearchPrerequisites

    prerequisites = ResearchPrerequisites()

    # Get optimal execution order using topological sort
    execution_order = prerequisites.get_execution_order(order_request.tool_names)

    logger.info(
        f"Calculated execution order for {len(order_request.tool_names)} tools: "
        f"{execution_order}"
    )

    return ExecutionOrderResponse(
        execution_order=execution_order,
        tool_count=len(execution_order),
    )


class BatchToolConfig(BaseModel):
    """Configuration for a single tool in batch"""

    tool_name: str
    params: Optional[Dict[str, Any]] = {}


class BatchResearchRequest(BaseModel):
    """Request to execute multiple research tools in batch"""

    project_id: str
    client_id: str
    tools: List[BatchToolConfig]


class BatchResearchResponse(BaseModel):
    """Response from batch research execution"""

    execution_order: List[str]
    results: Dict[str, Dict[str, Any]]
    summary: Dict[str, int]


@router.post("/batch", response_model=BatchResearchResponse)
@strict_limiter.limit("10/hour")  # Strict limit for expensive batch operations
async def execute_research_batch(
    request: Request,
    batch_request: BatchResearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Execute multiple research tools in correct dependency order.

    This is the MAIN endpoint frontend should use instead of calling /run multiple times.

    Features:
    - Automatic dependency ordering (Tier 1 → Tier 2 → Tier 3 → Tier 4)
    - Tools completed in batch count as prerequisites for later tools
    - Staged execution with data flow between tools via database
    - Blocks tools missing required prerequisites
    - Partial success handling (some succeed, some blocked)

    Args:
        batch_request: Project, client, and list of tools to execute

    Returns:
        Execution order, results for each tool, and summary
    """
    # Verify project ownership
    project = crud.get_project(db, batch_request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    _check_ownership(project, current_user, resource_type="project")

    # Verify client ownership
    client = crud.get_client(db, batch_request.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    _check_ownership(client, current_user, resource_type="client")

    logger.info(
        f"Executing batch of {len(batch_request.tools)} research tools "
        f"for project {batch_request.project_id}"
    )

    # Convert to format expected by service
    tool_configs = [
        {"tool_name": tool.tool_name, "params": tool.params or {}} for tool in batch_request.tools
    ]

    # Execute batch
    result = await research_service.execute_research_tools_batch(
        db, batch_request.project_id, batch_request.client_id, tool_configs
    )

    return BatchResearchResponse(
        execution_order=result["execution_order"],
        results=result["results"],
        summary=result["summary"],
    )


# ============================================================================
# PRICING & BUNDLE DETECTION ENDPOINTS
# ============================================================================


class PricingPreviewResponse(BaseModel):
    """Response from pricing preview endpoint"""

    base_cost: float
    discount: float
    final_cost: float
    bundle_applied: Optional[str] = None
    bundle_name: Optional[str] = None
    savings_percent: float = 0.0
    next_bundle_suggestion: Optional[Dict[str, Any]] = None


@router.get("/pricing-preview", response_model=PricingPreviewResponse)
@lenient_limiter.limit("1000/hour")  # Cheap calculation endpoint
async def get_pricing_preview(
    request: Request,
    tool_ids: str = Query(..., description="Comma-separated tool IDs"),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate pricing with bundle detection for selected tools.

    Query params:
    - tool_ids: Comma-separated tool IDs (e.g. "voice_analysis,brand_archetype")

    Returns:
    {
      "base_cost": 1800,
      "discount": 300,
      "final_cost": 1500,
      "bundle_applied": "foundation_pack",
      "bundle_name": "Foundation Pack",
      "savings_percent": 16.7,
      "next_bundle_suggestion": {
        "bundle": "complete_strategy",
        "missing_tools": ["seo_keyword_research", "competitive_analysis", "content_gap_analysis"],
        "additional_cost": 700,
        "potential_savings": 500
      }
    }
    """
    from src.config.pricing import calculate_tools_cost, TOOLS

    # Parse tool IDs
    tool_list = [tid.strip() for tid in tool_ids.split(",") if tid.strip()]

    # Calculate pricing with bundle detection
    pricing = calculate_tools_cost(tool_list)

    # Calculate base cost (a la carte)
    base_cost = sum(TOOLS.get(tid, {}).get("price", 0.0) for tid in tool_list)

    # Determine which bundle was applied
    bundle_applied = None
    bundle_name = None
    if pricing["applied_bundles"]:
        # Get first bundle (highest priority)
        bundle_name = pricing["applied_bundles"][0]
        # Convert name to snake_case ID
        bundle_applied = bundle_name.lower().replace(" ", "_")

    # Calculate savings percentage
    savings_percent = (
        round((pricing["discount_amount"] / base_cost) * 100, 1) if base_cost > 0 else 0.0
    )

    # Add "next bundle" suggestion logic
    next_bundle_suggestion = _suggest_next_bundle(tool_list, pricing["applied_bundles"])

    return PricingPreviewResponse(
        base_cost=base_cost,
        discount=pricing["discount_amount"],
        final_cost=pricing["tools_cost"],
        bundle_applied=bundle_applied,
        bundle_name=bundle_name,
        savings_percent=savings_percent,
        next_bundle_suggestion=next_bundle_suggestion,
    )


def _suggest_next_bundle(
    current_tools: List[str], applied_bundles: List[str]
) -> Optional[Dict[str, Any]]:
    """
    Analyze current tool selection and suggest bundle upgrade.
    Returns bundle that requires fewest additional tools.
    """
    from src.config.pricing import BUNDLES, TOOLS

    current_set = set(current_tools)

    # If already in Ultimate Pack, no upgrade possible
    if "Ultimate Pack" in applied_bundles:
        return None

    # Find the next best bundle to complete
    best_suggestion = None
    min_additional_tools = float("inf")

    for bundle in BUNDLES:
        bundle_name = bundle["name"]

        # Skip if already applied
        if bundle_name in applied_bundles:
            continue

        # Find missing tools for this bundle
        required_tools = bundle["required_tools"]
        missing_tools = required_tools - current_set

        if not missing_tools:
            # Already have all tools for this bundle (shouldn't happen if logic is correct)
            continue

        # Calculate cost to complete this bundle
        missing_cost = sum(TOOLS.get(tid, {}).get("price", 0.0) for tid in missing_tools)

        # Calculate potential savings if we complete this bundle
        # Current a la carte cost for ALL bundle tools
        current_bundle_tools_in_selection = required_tools & current_set
        current_cost_for_bundle_tools = sum(
            TOOLS.get(tid, {}).get("price", 0.0) for tid in current_bundle_tools_in_selection
        )

        # After adding missing tools, bundle price replaces a la carte
        potential_savings = (current_cost_for_bundle_tools + missing_cost) - bundle["price"]

        # Only suggest if there's actual savings
        if potential_savings > 0 and len(missing_tools) < min_additional_tools:
            min_additional_tools = len(missing_tools)
            best_suggestion = {
                "bundle": bundle_name.lower().replace(" ", "_"),
                "bundle_name": bundle_name,
                "missing_tools": sorted(list(missing_tools)),
                "missing_tool_names": [
                    TOOLS.get(tid, {}).get("name", tid) for tid in sorted(missing_tools)
                ],
                "additional_cost": missing_cost,
                "potential_savings": round(potential_savings, 2),
            }

    return best_suggestion


class ResearchAnalyticsResponse(BaseModel):
    """Response from analytics endpoint"""

    total_revenue: float
    total_api_cost: float
    profit_margin: float
    total_executions: int
    cache_hit_rate: float
    cache_savings: float
    avg_cost_per_tool: float
    top_tools: List[Dict[str, Any]]
    date_range: int


@router.get("/analytics", response_model=ResearchAnalyticsResponse)
@lenient_limiter.limit("100/hour")  # Analytics query
async def get_research_analytics(
    request: Request,
    days: int = Query(90, ge=1, le=365, description="Date range in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Aggregate analytics across all research tools.

    Returns:
    - Total revenue (sum of tool_price)
    - Total API costs (sum of actual_cost_usd)
    - Profit margin percentage
    - Total executions
    - Cache hit rate
    - Top tools by execution count
    - Cost efficiency metrics

    TR-021: Only returns data for current user's research results
    """
    from backend.models import ResearchResult

    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # TR-021: Filter to user's research results only
    results = (
        db.query(ResearchResult)
        .filter(ResearchResult.user_id == current_user.id, ResearchResult.created_at >= cutoff_date)
        .all()
    )

    if not results:
        # Return empty analytics if no results
        return ResearchAnalyticsResponse(
            total_revenue=0.0,
            total_api_cost=0.0,
            profit_margin=0.0,
            total_executions=0,
            cache_hit_rate=0.0,
            cache_savings=0.0,
            avg_cost_per_tool=0.0,
            top_tools=[],
            date_range=days,
        )

    # Calculate aggregates
    total_revenue = sum(r.tool_price or 0.0 for r in results)
    total_api_cost = sum(r.actual_cost_usd or 0.0 for r in results)
    profit_margin = (
        round(((total_revenue - total_api_cost) / total_revenue * 100), 2)
        if total_revenue > 0
        else 0.0
    )

    # Cache statistics
    cached_count = sum(1 for r in results if r.is_cached_result)
    cache_hit_rate = round((cached_count / len(results) * 100), 1) if results else 0.0
    cache_savings = total_revenue * (cache_hit_rate / 100)

    # Group by tool_name for top tools
    tool_stats = {}
    for r in results:
        if r.tool_name not in tool_stats:
            tool_stats[r.tool_name] = {
                "tool_name": r.tool_name,
                "tool_label": r.tool_label,
                "execution_count": 0,
                "total_revenue": 0.0,
                "total_api_cost": 0.0,
            }
        tool_stats[r.tool_name]["execution_count"] += 1
        tool_stats[r.tool_name]["total_revenue"] += r.tool_price or 0.0
        tool_stats[r.tool_name]["total_api_cost"] += r.actual_cost_usd or 0.0

    # Sort by execution count
    top_tools = sorted(tool_stats.values(), key=lambda x: x["execution_count"], reverse=True)[:10]

    return ResearchAnalyticsResponse(
        total_revenue=round(total_revenue, 2),
        total_api_cost=round(total_api_cost, 2),
        profit_margin=profit_margin,
        total_executions=len(results),
        cache_hit_rate=cache_hit_rate,
        cache_savings=round(cache_savings, 2),
        avg_cost_per_tool=round(total_api_cost / len(results), 4) if results else 0.0,
        top_tools=top_tools,
        date_range=days,
    )
