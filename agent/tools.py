"""
Agent tools - wrappers for existing CLI commands and operations

Security (TR-003): Input validation added to prevent command injection.
All user-controlled inputs are validated before use in subprocess calls.
"""

import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.project_db import ProjectDatabase
from src.utils.skill_loader import SkillLoader, Skill, load_skill, list_skills

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
    """Tools available to the agent for executing operations"""

    def __init__(self):
        self.db = ProjectDatabase()
        self.project_dir = Path(__file__).parent.parent

        # Load skills for agent access
        self.skill_loader = SkillLoader()
        self._loaded_skills: Dict[str, Skill] = {}
        self._init_skills()

    def _init_skills(self) -> None:
        """Initialize available skills for agent access."""
        # Load content-creator skill for content generation guidance
        content_skill = load_skill("content-creator")
        if content_skill:
            self._loaded_skills["content-creator"] = content_skill
            logger.info(f"Loaded skill: content-creator v{content_skill.metadata.version}")

        # Load marketing-strategy-pmm skill for strategic guidance
        pmm_skill = load_skill("marketing-strategy-pmm")
        if pmm_skill:
            self._loaded_skills["marketing-strategy-pmm"] = pmm_skill
            logger.info(f"Loaded skill: marketing-strategy-pmm v{pmm_skill.metadata.version}")

        # Log available skills
        available = list_skills()
        logger.info(f"Available skills: {available}")

    # ============================================================================
    # SKILL ACCESS TOOLS
    # ============================================================================

    def get_available_skills(self) -> Dict[str, Any]:
        """
        List all available skills the agent can access.

        Returns:
            Dictionary with skill names, descriptions, and loaded status.
        """
        try:
            available = list_skills()
            skills_info = []

            for skill_name in available:
                skill = self._loaded_skills.get(skill_name)
                if skill:
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
                    # Try to load it for summary
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

            skill_name = skill_name.strip().lower()

            # Get or load the skill
            skill = self._loaded_skills.get(skill_name)
            if not skill:
                skill = load_skill(skill_name)
                if skill:
                    self._loaded_skills[skill_name] = skill

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

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with skill metadata and documentation.
        """
        try:
            if not skill_name or not isinstance(skill_name, str):
                return {"success": False, "error": "Skill name is required"}

            skill_name = skill_name.strip().lower()

            # Get or load the skill
            skill = self._loaded_skills.get(skill_name)
            if not skill:
                skill = load_skill(skill_name)
                if skill:
                    self._loaded_skills[skill_name] = skill

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

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with all reference contents.
        """
        try:
            if not skill_name or not isinstance(skill_name, str):
                return {"success": False, "error": "Skill name is required"}

            skill_name = skill_name.strip().lower()

            # Get or load the skill
            skill = self._loaded_skills.get(skill_name)
            if not skill:
                skill = load_skill(skill_name)
                if skill:
                    self._loaded_skills[skill_name] = skill

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
        ]
