"""
Migration configuration loader and validator.

Loads schema migration rules from schema_mapping.json and provides
utilities for retrieving migrations for version ranges.
"""

import json
from pathlib import Path
from typing import Any

from backend.utils.logger import logger

# Load migration configuration
_config_path = Path(__file__).parent / "schema_mapping.json"
_migration_config: dict[str, Any] = {}


def load_migration_rules() -> dict[str, Any]:
    """
    Load migration rules from schema_mapping.json.

    Returns:
        Dictionary with version_migrations and current_version
    """
    global _migration_config

    if _migration_config:
        return _migration_config

    try:
        with open(_config_path, "r", encoding="utf-8") as f:
            _migration_config = json.load(f)
        logger.info(
            f"Loaded migration config: current version {_migration_config['current_version']}"
        )
        return _migration_config
    except Exception as e:
        logger.error(f"Failed to load migration config: {e}")
        # Return minimal config
        return {"current_version": 4, "version_migrations": {}}


def get_migrations_for_version_range(start: int, end: int) -> list[dict[str, Any]]:
    """
    Get all migrations needed to migrate from start version to end version.

    Args:
        start: Starting version (exclusive)
        end: Ending version (inclusive)

    Returns:
        List of migration rules in order
    """
    config = load_migration_rules()
    migrations = []

    for version in range(start + 1, end + 1):
        version_str = str(version)
        if version_str in config["version_migrations"]:
            migration = config["version_migrations"][version_str]
            migration["version"] = version
            migrations.append(migration)
        else:
            logger.warning(f"No migration found for version {version}")

    logger.info(f"Found {len(migrations)} migrations from v{start} to v{end}")
    return migrations


def validate_migration_config() -> bool:
    """
    Validate the migration configuration.

    Returns:
        True if valid, False otherwise
    """
    try:
        config = load_migration_rules()

        if "current_version" not in config:
            logger.error("Missing 'current_version' in migration config")
            return False

        if "version_migrations" not in config:
            logger.error("Missing 'version_migrations' in migration config")
            return False

        # Validate each migration
        for version, migration in config["version_migrations"].items():
            if "description" not in migration:
                logger.warning(f"Migration v{version} missing description")

            # Check for table specifications
            table_count = sum(
                1
                for key in migration.keys()
                if key not in ["description", "version"] and isinstance(migration[key], dict)
            )

            if table_count == 0:
                logger.warning(f"Migration v{version} has no table modifications")

        logger.info("Migration config validation passed")
        return True

    except Exception as e:
        logger.error(f"Migration config validation failed: {e}")
        return False


# Auto-load and validate on import
_migration_config = load_migration_rules()
validate_migration_config()
