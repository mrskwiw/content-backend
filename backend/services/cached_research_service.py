"""
Cached Research Service

Provides cached versions of expensive research operations.
Demonstrates the caching pattern that can be applied to other services.
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.models import ResearchResult
from backend.services import crud
from backend.utils.cache import cached


@cached(ttl=600, key_prefix="research_results")
async def get_project_research_results_cached(
    db: Session,
    project_id: str,
    tool_name: Optional[str] = None,
) -> List[ResearchResult]:
    """
    Get research results for a project (cached for 10 minutes).

    Cache is invalidated when:
    - New research is run for the project
    - Project is modified
    - Manual cache invalidation

    Args:
        db: Database session
        project_id: Project ID
        tool_name: Optional tool name filter

    Returns:
        List of research results
    """
    return crud.get_research_results_by_project(db, project_id, tool_name=tool_name)


@cached(ttl=600, key_prefix="research_results")
async def get_client_research_results_cached(
    db: Session,
    client_id: str,
    tool_name: Optional[str] = None,
) -> List[ResearchResult]:
    """
    Get research results for a client (cached for 10 minutes).

    Cache is invalidated when:
    - New research is run for the client
    - Client is modified
    - Manual cache invalidation

    Args:
        db: Database session
        client_id: Client ID
        tool_name: Optional tool name filter

    Returns:
        List of research results
    """
    return crud.get_research_results_by_client(db, client_id, tool_name=tool_name)
