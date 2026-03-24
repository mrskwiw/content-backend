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
    BusinessReportInput,
    ResearchResultResponse,
    ResearchResultListResponse,
)
from backend.services import crud
from backend.services.research_service import research_service
from backend.services import credit_service
from backend.services.credit_service import InsufficientCreditsError
from backend.pricing.credit_pricing import get_research_tool_cost
from backend.utils.logger import logger
from backend.utils.research_rate_limiter import research_rate_limiter
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
    credits: Optional[int] = None  # Credit cost (not dollars)
    status: str = "available"  # available, coming_soon
    description: Optional[str] = None
    category: Optional[str] = None
    required_integrations: Optional[List[str]] = (
        []
    )  # List of required integrations: 'web_search', 'serpapi', etc.


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


# Research tool catalog - Credit costs based on labor replacement value
# See backend/config/credit_pricing.py for pricing rationale
RESEARCH_TOOLS = [
    # Client Foundation Tools
    ResearchTool(
        name="voice_analysis",
        label="Voice Analysis",
        credits=100,  # Replaces 6-8 hours of manual tone extraction
        status="available",
        description="Extract writing patterns from client's existing content",
        category="foundation",
    ),
    ResearchTool(
        name="brand_archetype",
        label="Brand Archetype Assessment",
        credits=75,  # Replaces 4-6 hours of brand strategy work
        status="available",
        description="Identify brand personality and messaging framework",
        category="foundation",
    ),
    # SEO & Competition Tools
    ResearchTool(
        name="seo_keyword_research",
        label="SEO Keyword Research",
        credits=150,  # Replaces 8-12 hours of keyword research
        status="available",
        description="Discover target keywords and search opportunities",
        category="seo",
    ),
    ResearchTool(
        name="determine_competitors",
        label="Determine Competitors",
        credits=100,  # Replaces competitive intelligence research
        status="available",
        description="AI-powered competitor discovery and market positioning analysis",
        category="seo",
        required_integrations=["web_search"],  # Requires web search (Brave, Tavily, or SerpAPI)
    ),
    ResearchTool(
        name="competitive_analysis",
        label="Competitive Analysis",
        credits=100,  # Replaces 6-8 hours of competitive strategy analysis
        status="available",
        description="Research competitors and identify positioning gaps",
        required_integrations=["web_search"],  # Requires web search (Brave, Tavily, or SerpAPI)
        category="seo",
    ),
    ResearchTool(
        name="content_gap_analysis",
        label="Content Gap Analysis",
        credits=100,  # Replaces deep market analysis
        status="available",
        description="Identify content opportunities competitors are missing",
        category="seo",
    ),
    # Market Intelligence Tools
    ResearchTool(
        name="market_trends_research",
        label="Market Trends Research",
        credits=100,  # Replaces industry research
        status="available",
        description="Discover trending topics and emerging opportunities",
        category="market",
    ),
    ResearchTool(
        name="business_report",
        label="Business Report",
        credits=50,  # Light research tier (~$100-125, replaces 3-4 hours)
        status="available",
        description="Analyze company perception, strengths, pain points, and value proposition",
        category="competitive_analysis",
        required_integrations=["web_search", "serpapi"],
    ),
    # Strategy & Planning Tools
    ResearchTool(
        name="content_audit",
        label="Content Audit",
        credits=75,  # Replaces manual content inventory
        status="available",
        description="Analyze existing content performance and opportunities",
        category="strategy",
    ),
    ResearchTool(
        name="platform_strategy",
        label="Platform Strategy",
        credits=50,  # Replaces platform evaluation
        status="available",
        description="Recommend optimal platform mix for distribution",
        category="strategy",
    ),
    ResearchTool(
        name="content_calendar",
        label="Content Calendar Strategy",
        credits=50,  # Replaces editorial planning
        status="available",
        description="Create strategic 90-day content calendar",
        category="strategy",
    ),
    ResearchTool(
        name="audience_research",
        label="Audience Research",
        credits=75,  # Replaces persona interviews and analysis
        status="available",
        description="Deep-dive into target audience demographics and psychographics",
        category="strategy",
    ),
    # Workshop Assistants
    ResearchTool(
        name="icp_workshop",
        label="ICP Development Workshop",
        credits=150,  # Replaces full workshop (8-12 hours, most labor-intensive)
        status="available",
        description="Facilitate ideal customer profile definition through guided conversation",
        category="workshop",
    ),
    ResearchTool(
        name="story_mining",
        label="Story Mining Interview",
        credits=125,  # Replaces interview and story extraction
        status="available",
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
    "business_report": BusinessReportInput,
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
    # TR-003: Check per-user rate limits (hourly, daily, monthly)
    tool_cost = get_research_tool_cost(input.tool_name)
    usage_stats = research_rate_limiter.check_and_increment(
        user=current_user, tool_name=input.tool_name, cost_credits=tool_cost
    )
    logger.info(f"Research tool rate limit check passed. Usage: {usage_stats}")

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

    cached_result = None  # Track whether we got a cache hit (for credit refund logic)
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
                f"- saved {tool.credits} credits"
            )
        else:
            # CREDIT DEDUCTION: Deduct credits before executing expensive research tool
            credit_cost = get_research_tool_cost(input.tool)
            try:
                credit_service.deduct_credits(
                    db=db,
                    user_id=current_user.id,
                    amount=credit_cost,
                    description=f"Research tool: {tool.label}",
                    reference_id=input.project_id,
                    reference_type="research",
                )
                logger.info(
                    f"Deducted {credit_cost} credits from user {current_user.id} for {input.tool}"
                )
            except InsufficientCreditsError:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=f"Insufficient credits. Required: {credit_cost} credits for {tool.label}. "
                    f"Your balance: {current_user.credit_balance} credits. Please purchase more credits.",
                )

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
                f"- executed {tool.credits} credits"
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
                "credits": tool.credits,
                "project_id": input.project_id,
                "client_id": input.client_id,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Research execution failed: {str(e)}", exc_info=True)

        # CREDIT REFUND: Refund credits if research execution failed (only if credits were deducted)
        # Credits are only deducted on cache MISS, so check if we had a cache MISS
        if not cached_result:
            try:
                credit_cost = get_research_tool_cost(input.tool)
                credit_service.refund_credits(
                    db=db,
                    user_id=current_user.id,
                    amount=credit_cost,
                    description=f"Refund for failed research: {tool.label}",
                    reference_id=input.project_id,
                    reference_type="research_refund",
                )
                logger.info(
                    f"Refunded {credit_cost} credits to user {current_user.id} for failed {input.tool}"
                )
            except Exception as refund_err:
                logger.error(f"Failed to refund credits for {input.tool}: {refund_err}")

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
            status_code=404,
            detail=f"Output format '{output_format}' not found for this result",
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


# Client-specific prerequisite checking
class ClientToolStatus(BaseModel):
    """Prerequisite status for a tool for a specific client"""

    tool_name: str
    can_run: bool
    completed: bool  # Has this tool been run for this client
    missing_required: List[str]
    missing_recommended: List[str]


class ClientPrerequisiteResponse(BaseModel):
    """Response from client prerequisite check"""

    client_id: str
    tools: List[ClientToolStatus]
    completed_tools: List[str]  # All tools completed for this client


@router.get("/prerequisites/client/{client_id}", response_model=ClientPrerequisiteResponse)
@lenient_limiter.limit("100/hour")
async def get_client_prerequisites(
    request: Request,
    client_id: str,
    tool_names: Optional[str] = Query(None, description="Comma-separated tool names to check"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get prerequisite status for tools based on a specific client's completed research.

    This endpoint enables client-specific dependency tracking in the Tool Library page.
    Returns which tools have been completed for this client and what prerequisites
    are missing for tools that haven't been run yet.

    Args:
        client_id: Client ID to check research completion status
        tool_names: Optional comma-separated list of tools to check. If not provided,
                   checks all available tools.

    Returns:
        Status for each tool including whether it's been completed for this client
        and what prerequisites are missing.

    Authorization: TR-021 - User must own the client
    """
    # Verify client ownership (TR-021: IDOR prevention)
    client = crud.get_client(db, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    _check_ownership(client, current_user, resource_type="client")

    # Determine which tools to check
    if tool_names:
        tools_to_check = [t.strip() for t in tool_names.split(",")]
    else:
        # Check all available tools
        tools_to_check = [tool.name for tool in RESEARCH_TOOLS]

    logger.info(f"Checking prerequisites for {len(tools_to_check)} tools for client {client_id}")

    # Get prerequisite status for all tools
    status_map = research_service.get_client_prerequisite_status(db, client_id, tools_to_check)

    # Build response
    tool_statuses = []
    completed_tools = []

    for tool_name, tool_status_data in status_map.items():
        tool_status = ClientToolStatus(
            tool_name=tool_name,
            can_run=tool_status_data["can_run"],
            completed=tool_status_data["completed"],
            missing_required=tool_status_data["missing_required"],
            missing_recommended=tool_status_data["missing_recommended"],
        )
        tool_statuses.append(tool_status)

        if tool_status_data["completed"]:
            completed_tools.append(tool_name)

    return ClientPrerequisiteResponse(
        client_id=client_id,
        tools=tool_statuses,
        completed_tools=completed_tools,
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
    # TR-003: Check per-user rate limits for batch operations
    # Batch operations count as multiple tool calls
    total_tools = len(batch_request.tool_names)
    logger.info(f"Batch research request: {total_tools} tools")

    # Check limits for first tool (will increment for each tool executed)
    if total_tools > 0:
        tool_cost = get_research_tool_cost(batch_request.tool_names[0])
        usage_stats = research_rate_limiter.check_and_increment(
            user=current_user,
            tool_name=f"batch[{total_tools}]",
            cost_credits=tool_cost * total_tools,
        )
        logger.info(f"Batch research rate limit check passed. Usage: {usage_stats}")

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
    """Response from pricing preview endpoint (credit-based)"""

    base_cost: int  # Total credits needed
    discount: int  # Always 0 (no bundle discounts in credit system)
    final_cost: int  # Same as base_cost
    bundle_applied: Optional[str] = None  # Always None (no bundles)
    bundle_name: Optional[str] = None  # Always None (no bundles)
    savings_percent: float = 0.0  # Always 0 (no discounts)
    next_bundle_suggestion: Optional[Dict[str, Any]] = None  # Always None (no bundles)


@router.get("/pricing-preview", response_model=PricingPreviewResponse)
@lenient_limiter.limit("1000/hour")  # Cheap calculation endpoint
async def get_pricing_preview(
    request: Request,
    tool_ids: str = Query(..., description="Comma-separated tool IDs"),
    current_user: User = Depends(get_current_user),
):
    """
    Calculate credit cost for selected research tools.

    Query params:
    - tool_ids: Comma-separated tool IDs (e.g. "voice_analysis,brand_archetype")

    Returns:
    {
      "base_cost": 175,  # Total credits needed
      "discount": 0,      # No discounts in credit system
      "final_cost": 175,  # Same as base_cost
      "bundle_applied": null,
      "bundle_name": null,
      "savings_percent": 0.0,
      "next_bundle_suggestion": null
    }

    Note: Bundle discounts removed - credit system uses flat per-tool pricing.
    """
    # Parse tool IDs
    tool_list = [tid.strip() for tid in tool_ids.split(",") if tid.strip()]

    # Calculate total credit cost
    total_credits = 0
    for tool_id in tool_list:
        tool = next((t for t in RESEARCH_TOOLS if t.name == tool_id), None)
        if tool and tool.credits:
            total_credits += tool.credits

    # No discounts or bundles in credit system
    return PricingPreviewResponse(
        base_cost=total_credits,
        discount=0,
        final_cost=total_credits,
        bundle_applied=None,
        bundle_name=None,
        savings_percent=0.0,
        next_bundle_suggestion=None,
    )


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
        .filter(
            ResearchResult.user_id == current_user.id,
            ResearchResult.created_at >= cutoff_date,
        )
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
