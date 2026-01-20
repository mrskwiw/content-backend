"""
Skill Loader Utility

Loads and provides access to external skill definitions (SKILL.md files)
and their associated resources (references, scripts, assets).

Skills are structured directories containing:
- SKILL.md: Metadata and documentation (YAML frontmatter + markdown)
- references/: Reference documentation (brand guidelines, frameworks, etc.)
- scripts/: Executable Python tools
- assets/: Templates and other assets
"""

import re
import yaml  # type: ignore[import-untyped]
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class SkillMetadata:
    """Metadata from a skill's YAML frontmatter."""

    name: str
    description: str
    version: str = "1.0.0"
    author: str = ""
    license: str = "MIT"
    category: str = ""
    domain: str = ""
    python_tools: List[str] = field(default_factory=list)
    tech_stack: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


@dataclass
class SkillReference:
    """A reference document from a skill."""

    name: str
    path: Path
    content: str


@dataclass
class SkillScript:
    """A Python script from a skill."""

    name: str
    path: Path
    module: Optional[Any] = None


@dataclass
class Skill:
    """A complete loaded skill with all resources."""

    metadata: SkillMetadata
    path: Path
    documentation: str
    references: Dict[str, SkillReference] = field(default_factory=dict)
    scripts: Dict[str, SkillScript] = field(default_factory=dict)
    assets: Dict[str, Path] = field(default_factory=dict)

    def get_reference(self, name: str) -> Optional[str]:
        """Get reference content by name (without extension)."""
        ref = self.references.get(name)
        return ref.content if ref else None

    def get_all_references(self) -> Dict[str, str]:
        """Get all reference contents as a dictionary."""
        return {name: ref.content for name, ref in self.references.items()}

    def get_script_module(self, name: str) -> Optional[Any]:
        """Get a loaded Python module for a script."""
        script = self.scripts.get(name)
        return script.module if script else None


class SkillLoader:
    """
    Loads skills from the file system.

    Skills are located relative to the project root in sibling directories.
    """

    def __init__(self, skills_base_path: Optional[Path] = None):
        """
        Initialize the skill loader.

        Args:
            skills_base_path: Base path where skill directories are located.
                            Defaults to project parent directory.
        """
        if skills_base_path:
            self.skills_base = Path(skills_base_path)
        else:
            # Default: skills are in parent of project directory
            project_root = Path(__file__).parent.parent.parent  # src/utils -> src -> project
            self.skills_base = project_root.parent  # Go up to parent of project

        self._loaded_skills: Dict[str, Skill] = {}

    def _parse_yaml_frontmatter(self, content: str) -> tuple[dict, str]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown content with YAML frontmatter

        Returns:
            Tuple of (frontmatter dict, remaining markdown content)
        """
        # Match YAML frontmatter between --- markers
        pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            return {}, content

        yaml_content = match.group(1)
        markdown_content = match.group(2)

        try:
            frontmatter = yaml.safe_load(yaml_content)
            return frontmatter or {}, markdown_content
        except yaml.YAMLError:
            return {}, content

    def _parse_metadata(self, frontmatter: dict) -> SkillMetadata:
        """
        Parse skill metadata from frontmatter dictionary.

        Args:
            frontmatter: Parsed YAML frontmatter

        Returns:
            SkillMetadata instance
        """
        metadata_section = frontmatter.get("metadata", {})

        # Parse python-tools (comma-separated string or list)
        python_tools = metadata_section.get("python-tools", [])
        if isinstance(python_tools, str):
            python_tools = [t.strip() for t in python_tools.split(",")]

        # Parse tech-stack
        tech_stack = metadata_section.get("tech-stack", [])
        if isinstance(tech_stack, str):
            tech_stack = [t.strip() for t in tech_stack.split(",")]

        return SkillMetadata(
            name=frontmatter.get("name", "unknown"),
            description=frontmatter.get("description", ""),
            version=metadata_section.get("version", "1.0.0"),
            author=metadata_section.get("author", ""),
            license=frontmatter.get("license", "MIT"),
            category=metadata_section.get("category", ""),
            domain=metadata_section.get("domain", ""),
            python_tools=python_tools,
            tech_stack=tech_stack,
        )

    def _load_references(self, skill_path: Path) -> Dict[str, SkillReference]:
        """
        Load all reference documents from a skill's references/ directory.

        Args:
            skill_path: Path to the skill directory

        Returns:
            Dictionary of reference name -> SkillReference
        """
        references = {}
        refs_dir = skill_path / "references"

        if refs_dir.exists():
            for ref_file in refs_dir.glob("*.md"):
                name = ref_file.stem
                content = ref_file.read_text(encoding="utf-8")
                references[name] = SkillReference(name=name, path=ref_file, content=content)

        return references

    def _load_scripts(self, skill_path: Path, load_modules: bool = False) -> Dict[str, SkillScript]:
        """
        Load script information from a skill's scripts/ directory.

        Args:
            skill_path: Path to the skill directory
            load_modules: If True, actually import the Python modules

        Returns:
            Dictionary of script name -> SkillScript
        """
        scripts = {}
        scripts_dir = skill_path / "scripts"

        if scripts_dir.exists():
            for script_file in scripts_dir.glob("*.py"):
                name = script_file.stem
                module = None

                if load_modules:
                    try:
                        spec = importlib.util.spec_from_file_location(
                            f"skill_script_{name}", script_file
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                    except Exception as e:
                        # Log but don't fail - scripts may have dependencies
                        print(f"Warning: Could not load script {name}: {e}")

                scripts[name] = SkillScript(name=name, path=script_file, module=module)

        return scripts

    def _load_assets(self, skill_path: Path) -> Dict[str, Path]:
        """
        Load asset paths from a skill's assets/ directory.

        Args:
            skill_path: Path to the skill directory

        Returns:
            Dictionary of asset name -> file path
        """
        assets = {}
        assets_dir = skill_path / "assets"

        if assets_dir.exists():
            for asset_file in assets_dir.iterdir():
                if asset_file.is_file():
                    assets[asset_file.stem] = asset_file

        return assets

    def load_skill(self, skill_name: str, load_scripts: bool = False) -> Optional[Skill]:
        """
        Load a skill by name.

        Args:
            skill_name: Name of the skill directory (e.g., "content-creator")
            load_scripts: If True, import Python scripts as modules

        Returns:
            Loaded Skill instance, or None if not found
        """
        # Check cache first
        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]

        skill_path = self.skills_base / skill_name

        if not skill_path.exists():
            return None

        skill_file = skill_path / "SKILL.md"
        if not skill_file.exists():
            return None

        # Parse SKILL.md
        content = skill_file.read_text(encoding="utf-8")
        frontmatter, documentation = self._parse_yaml_frontmatter(content)
        metadata = self._parse_metadata(frontmatter)

        # Load resources
        references = self._load_references(skill_path)
        scripts = self._load_scripts(skill_path, load_modules=load_scripts)
        assets = self._load_assets(skill_path)

        skill = Skill(
            metadata=metadata,
            path=skill_path,
            documentation=documentation,
            references=references,
            scripts=scripts,
            assets=assets,
        )

        # Cache the loaded skill
        self._loaded_skills[skill_name] = skill

        return skill

    def list_available_skills(self) -> List[str]:
        """
        List all available skills in the skills base directory.

        Returns:
            List of skill directory names
        """
        skills = []
        if self.skills_base.exists():
            for path in self.skills_base.iterdir():
                if path.is_dir() and (path / "SKILL.md").exists():
                    skills.append(path.name)
        return skills

    def get_skill_summary(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a summary of a skill without fully loading it.

        Args:
            skill_name: Name of the skill

        Returns:
            Dictionary with skill summary info
        """
        skill = self.load_skill(skill_name)
        if not skill:
            return None

        return {
            "name": skill.metadata.name,
            "description": skill.metadata.description,
            "version": skill.metadata.version,
            "category": skill.metadata.category,
            "references": list(skill.references.keys()),
            "scripts": list(skill.scripts.keys()),
            "assets": list(skill.assets.keys()),
        }


# Singleton instance for easy access
_skill_loader: Optional[SkillLoader] = None


def get_skill_loader() -> SkillLoader:
    """Get or create the singleton SkillLoader instance."""
    global _skill_loader
    if _skill_loader is None:
        _skill_loader = SkillLoader()
    return _skill_loader


def load_skill(skill_name: str, load_scripts: bool = False) -> Optional[Skill]:
    """
    Convenience function to load a skill.

    Args:
        skill_name: Name of the skill directory
        load_scripts: If True, import Python scripts as modules

    Returns:
        Loaded Skill instance
    """
    return get_skill_loader().load_skill(skill_name, load_scripts)


def get_skill_reference(skill_name: str, reference_name: str) -> Optional[str]:
    """
    Convenience function to get a specific reference from a skill.

    Args:
        skill_name: Name of the skill
        reference_name: Name of the reference (without .md extension)

    Returns:
        Reference content as string, or None
    """
    skill = load_skill(skill_name)
    if skill:
        return skill.get_reference(reference_name)
    return None


def list_skills() -> List[str]:
    """
    Convenience function to list available skills.

    Returns:
        List of skill names
    """
    return get_skill_loader().list_available_skills()
