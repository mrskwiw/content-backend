"""
Generator API endpoints.

Handles content generation, regeneration, and export operations.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db, SessionLocal
from backend.middleware.auth_dependency import get_current_user
from backend.models import User
from backend.schemas.run import RunResponse, LogEntry
from backend.schemas.deliverable import DeliverableResponse
from backend.services import crud
from backend.services.generator_service import generator_service
from backend.utils.logger import logger
from backend.utils.http_rate_limiter import strict_limiter, standard_limiter
from src.validators.prompt_injection_defense import sanitize_prompt_input
from src.utils.template_parser import template_parser

router = APIRouter()


class GenerateAllInput(BaseModel):
    """Input for generate-all endpoint"""

    project_id: str
    client_id: str
    is_batch: bool = True
    num_posts: Optional[int] = (
        None  # Number of posts to generate (defaults to project setting or 30)
    )
    template_quantities: Optional[dict[str, int]] = (
        None  # Optional template quantities from frontend
    )
    custom_topics: Optional[list[str]] = None  # NEW: topic override for content generation
    target_platform: Optional[str] = "generic"  # NEW: target platform for generation optimization


class RegenerateInput(BaseModel):
    """Input for regenerate endpoint"""

    project_id: str
    post_ids: list[str]


class ExportInput(BaseModel):
    """Input for export endpoint"""

    project_id: str
    format: str = "txt"  # txt, md, docx
    include_audit_log: bool = False
    include_research: bool = False  # NEW: Include research results appendix


async def run_generation_background(
    run_id: str,
    project_id: str,
    client_id: str,
    num_posts: int = 30,
    template_quantities: Optional[dict[str, int]] = None,
    custom_topics: Optional[list[str]] = None,  # NEW: topic override for generation
    target_platform: Optional[str] = "generic",  # NEW: target platform for generation
):
    """
    Background task to run content generation.

    This prevents HTTP timeouts by running generation asynchronously.
    Updates the Run record with progress and results.
    """
    # Create new DB session for background task
    db = SessionLocal()

    try:
        logger.info(f"Background generation started for run {run_id}")
        if template_quantities:
            logger.info(f"Using template quantities from request: {template_quantities}")

        # SECURITY (TR-020): Sanitize custom_topics before passing to LLM
        sanitized_topics = None
        if custom_topics:
            try:
                sanitized_topics = [
                    sanitize_prompt_input(topic, strict=False) for topic in custom_topics
                ]
                logger.info(f"Sanitized {len(custom_topics)} custom topics for generation")
            except ValueError as e:
                logger.error(f"Prompt injection detected in custom_topics: {e}")
                # Update run to failed status
                crud.update_run(
                    db,
                    run_id,
                    status="failed",
                    error_message=f"Security validation failed: {str(e)}",
                )
                return

        # Execute content generation via service
        result = await generator_service.generate_all_posts(
            db=db,
            project_id=project_id,
            client_id=client_id,
            num_posts=num_posts,
            template_quantities=template_quantities,
            custom_topics=sanitized_topics,  # Use sanitized topics
            platform=target_platform,  # NEW: Pass target platform for platform-specific generation
            run_id=run_id,  # Pass run_id so posts can reference the run
        )

        # Update run status to succeeded (use LogEntry format)
        from datetime import datetime
        from backend.schemas.run import LogEntry

        timestamp = datetime.now().isoformat()
        logs = [
            LogEntry(timestamp=timestamp, message="Generation started"),
            LogEntry(timestamp=timestamp, message="CLI execution completed"),
            LogEntry(
                timestamp=timestamp,
                message=f"Created {result['posts_created']} post records",
            ),
            LogEntry(timestamp=timestamp, message=f"Output directory: {result['output_dir']}"),
        ]

        crud.update_run(db, run_id, status="succeeded", logs=[log.model_dump() for log in logs])

        logger.info(f"Background generation completed successfully for run {run_id}")

    except Exception as e:
        logger.error(f"Background generation failed for run {run_id}: {str(e)}", exc_info=True)

        # Update run status to failed
        crud.update_run(db, run_id, status="failed", error_message=str(e))

    finally:
        db.close()


@router.get("/template-dependencies/{template_number}")
@standard_limiter.limit("100/minute")
async def get_template_dependencies(
    request: Request,
    template_number: int,
    current_user: User = Depends(get_current_user),
):
    """
    Get research dependencies for a specific template.

    Returns the required and recommended research tools for a given template,
    helping users understand what research to run before generating content.

    Args:
        template_number: Template number (1-15)

    Returns:
        Dict with template info and research dependencies:
        {
            "template_number": 1,
            "template_title": "The Problem-Recognition Post",
            "research_dependencies": {
                "required": ["audience_research"],
                "recommended": ["icp_workshop", "seo_keyword_research"]
            }
        }

    Raises:
        HTTPException 404: Template not found
    """
    if not 1 <= template_number <= 15:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template {template_number} not found. Valid range: 1-15",
        )

    try:
        templates = template_parser.parse_all_templates()
        template = templates.get(template_number)

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Template {template_number} not found",
            )

        return {
            "template_number": template["number"],
            "template_title": template["title"],
            "research_dependencies": template["research_dependencies"],
        }

    except FileNotFoundError as e:
        logger.error(f"Template library file not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Template library file not found",
        )
    except Exception as e:
        logger.error(f"Failed to parse template dependencies: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse template dependencies: {str(e)}",
        )


@router.post("/generate-all", response_model=RunResponse)
@strict_limiter.limit("10/hour")  # TR-004: Expensive AI generation (composite key: IP+user)
async def generate_all(
    request: Request,
    background_tasks: BackgroundTasks,
    input: GenerateAllInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Generate all posts for a project.

    Authorization: TR-021 - User must own project

    This endpoint:
    1. Creates a Run record with status="pending"
    2. Queues background task to run generation
    3. Returns immediately with run_id
    4. Client polls GET /api/runs/{run_id} for status updates

    Prevents HTTP timeouts by running generation asynchronously.
    """
    # TR-021: Manual authorization check (project_id comes from request body)
    project = crud.get_project(db, input.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {input.project_id} not found",
        )

    # TR-021: Verify user owns the project
    if (
        hasattr(project, "user_id")
        and project.user_id != current_user.id
        and not current_user.is_superuser
    ):
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

    # Create Run record with status="pending"
    db_run = crud.create_run(db, project_id=input.project_id, is_batch=input.is_batch)

    logger.info(f"Created run {db_run.id} for project {input.project_id}")

    # Determine num_posts: input > project setting > default 30
    num_posts = input.num_posts or project.num_posts or 30

    # Determine target_platform: input > project setting > default 'generic'
    target_platform = input.target_platform or project.target_platform or "generic"

    # Queue background task (returns immediately)
    background_tasks.add_task(
        run_generation_background,
        run_id=db_run.id,
        project_id=input.project_id,
        client_id=input.client_id,
        num_posts=num_posts,
        template_quantities=input.template_quantities,  # Pass template quantities from frontend
        custom_topics=input.custom_topics,  # NEW: pass topic override for generation
        target_platform=target_platform,  # NEW: pass target platform for platform-specific generation
    )

    # Update run status to running (background task will update to succeeded/failed)
    db_run = crud.update_run(db, db_run.id, status="running")

    logger.info(f"Queued background generation task for run {db_run.id}")

    return db_run


@router.post("/regenerate", response_model=RunResponse)
@strict_limiter.limit("20/hour")  # TR-004: Expensive AI regeneration (composite key: IP+user)
async def regenerate(
    request: Request,
    input: RegenerateInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Regenerate specific posts.

    Authorization: TR-021 - User must own project

    Used for quality gate - regenerate flagged posts.
    """
    # Verify project exists
    project = crud.get_project(db, input.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {input.project_id} not found",
        )

    # TR-021: Verify user owns the project
    if (
        hasattr(project, "user_id")
        and project.user_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You don't own this project",
        )

    # Create Run record for regeneration
    db_run = crud.create_run(db, project_id=input.project_id, is_batch=False)

    # Update run status to running
    crud.update_run(db, db_run.id, status="running")

    try:
        logger.info(
            f"Starting regeneration for {len(input.post_ids)} posts in project {input.project_id}"
        )

        # Execute regeneration via service
        result = await generator_service.regenerate_posts(
            db=db,
            project_id=input.project_id,
            post_ids=input.post_ids,
        )

        # Update run status to succeeded (use LogEntry format)
        timestamp = datetime.now().isoformat()
        logs = [
            LogEntry(timestamp=timestamp, message="Regeneration started"),
            LogEntry(
                timestamp=timestamp,
                message=f"Regenerated {result.get('posts_regenerated', 0)} posts",
            ),
            LogEntry(
                timestamp=timestamp,
                message=f"Status: {result.get('status', 'completed')}",
            ),
        ]

        crud.update_run(
            db,
            db_run.id,
            status="succeeded",
            logs=[log.model_dump() for log in logs],  # Convert to dicts for JSON serialization
        )

        db.refresh(db_run)
        logger.info(f"Regeneration completed successfully for run {db_run.id}")
        return db_run

    except Exception as e:
        logger.error(f"Regeneration failed: {str(e)}", exc_info=True)
        crud.update_run(db, db_run.id, status="failed", error_message=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Regeneration failed: {str(e)}",
        )


@router.post("/export", response_model=DeliverableResponse)
@standard_limiter.limit("100/hour")  # TR-004: Standard operation (file generation)
async def export_package(
    request: Request,
    input: ExportInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export deliverable package.

    Authorization: TR-021 - User must own project

    Creates a deliverable file (TXT/DOCX) from generated posts.
    Supports format selection and optional audit log inclusion.
    """
    try:
        # Verify project exists
        project = crud.get_project(db, input.project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {input.project_id} not found",
            )

        # TR-021: Verify user owns the project
        if (
            hasattr(project, "user_id")
            and project.user_id != current_user.id
            and not current_user.is_superuser
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't own this project",
            )

        # Get client data
        client = crud.get_client(db, project.client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client {project.client_id} not found",
            )

        # Get posts for this project
        from backend.models import Post as PostModel

        posts = db.query(PostModel).filter(PostModel.project_id == input.project_id).all()

        if not posts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No posts found for this project. Generate content first.",
            )

        logger.info(
            f"Creating deliverable export for project {input.project_id} in format {input.format} "
            f"with {len(posts)} posts (audit_log={input.include_audit_log})"
        )

        from backend.models import Deliverable
        from backend.services.export_service import generate_export_file
        import uuid
        from datetime import datetime

        # Generate actual file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{project.name}_{timestamp}_deliverable.{input.format}"
        relative_path = f"{project.name}/{filename}"

        # Generate the file using export service
        file_path, file_size = await generate_export_file(
            posts=posts,
            client=client,
            project=project,
            format=input.format,
            relative_path=relative_path,
            include_audit_log=input.include_audit_log,
            include_research=input.include_research,  # NEW
            db=db,
        )

        # Get the latest run_id for this project (if any)
        from backend.models import Run as RunModel

        latest_run = (
            db.query(RunModel)
            .filter(RunModel.project_id == input.project_id)
            .order_by(RunModel.started_at.desc())
            .first()
        )

        # Create deliverable record
        db_deliverable = Deliverable(
            id=f"del-{uuid.uuid4().hex[:12]}",
            project_id=input.project_id,
            client_id=project.client_id,
            run_id=latest_run.id if latest_run else None,
            format=input.format,
            path=relative_path,
            status="ready",
            created_at=datetime.utcnow(),
            file_size_bytes=file_size,
        )

        db.add(db_deliverable)
        db.commit()
        db.refresh(db_deliverable)

        logger.info(f"Deliverable created successfully: {db_deliverable.id} at {file_path}")
        return db_deliverable

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}",
        )
