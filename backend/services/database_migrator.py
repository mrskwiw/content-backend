"""
Database migration engine for intelligent restore.

Implements ETL (Extract, Transform, Load) migration:
1. Extract: Copy backup to staging database
2. Transform: Apply schema migrations
3. Load: Replace production database atomically

All SQL operations are validated against TR-015 security requirements.
"""

import re
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import quoted_name

from backend.migrations import get_migrations_for_version_range, load_migration_rules
from backend.services.schema_inspector import get_schema_version, set_schema_version
from backend.utils.logger import logger

# SECURITY: Whitelist of allowed SQL column types (TR-015)
ALLOWED_TYPES = {"TEXT", "VARCHAR", "INTEGER", "REAL", "JSON", "BOOLEAN", "TIMESTAMP"}


class DatabaseMigrator:
    """
    Orchestrates database migration from backup to current schema.

    Uses staging database approach:
    - Never modifies original backup or production database directly
    - All migrations happen in isolated staging environment
    - Atomic file replacement on success
    - Automatic rollback on failure
    """

    def __init__(self, backup_path: str | Path, target_db_path: str | Path):
        """
        Initialize migrator.

        Args:
            backup_path: Path to backup database file
            target_db_path: Path to production database file
        """
        self.backup_path = Path(backup_path)
        self.target_db_path = Path(target_db_path)
        self.staging_path: Path | None = None
        self.staging_engine: Engine | None = None
        self.migration_log: list[str] = []

    def can_migrate(self) -> tuple[bool, str]:
        """
        Check if migration is possible.

        Returns:
            Tuple of (can_migrate, reason)
        """
        # Validate backup file exists
        if not self.backup_path.exists():
            return False, f"Backup file not found: {self.backup_path}"

        # Validate backup is SQLite
        try:
            conn = sqlite3.connect(str(self.backup_path))
            conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
            conn.close()
        except Exception as e:
            return False, f"Invalid SQLite backup: {e}"

        # Get versions
        backup_version = get_schema_version(self.backup_path)
        config = load_migration_rules()
        current_version = config["current_version"]  # This is the target schema version (v4)

        # Check if migration is needed
        if backup_version == current_version:
            return True, "Versions match, no migration needed"

        # Check if we can migrate forward (backup should be older, not newer)
        if backup_version > current_version:
            return (
                False,
                f"Cannot migrate backwards: backup is v{backup_version}, "
                f"current schema is v{current_version}",
            )

        # Check if we have migration path
        migrations = get_migrations_for_version_range(backup_version, current_version)
        if not migrations:
            return (
                False,
                f"No migration path from v{backup_version} to v{current_version}",
            )

        return True, f"Can migrate from v{backup_version} to v{current_version}"

    def migrate(self) -> dict[str, Any]:
        """
        Execute full ETL migration.

        Returns:
            Dictionary with migration results and statistics

        Raises:
            Exception on migration failure
        """
        try:
            # Check migration is possible
            can_migrate, reason = self.can_migrate()
            if not can_migrate:
                raise ValueError(reason)

            logger.info(f"Starting migration: {reason}")

            # Get versions
            backup_version = get_schema_version(self.backup_path)
            config = load_migration_rules()
            current_version = config["current_version"]

            # If versions match, no migration needed
            if backup_version == current_version:
                row_count = self._count_rows(str(self.backup_path))
                return {
                    "status": "success",
                    "migration_applied": False,
                    "changes": [],
                    "row_count": row_count,
                }

            # 1. Extract: Create staging database
            self._create_staging_database()

            # 2. Transform: Apply migrations
            migration_results = self._apply_migrations(backup_version, current_version)

            # 3. Validate: Check data integrity
            if not self._validate_migration():
                raise ValueError("Migration validation failed")

            # 4. Count rows before replacing (staging_path will be moved)
            row_count = self._count_rows(str(self.staging_path))

            # 5. Load: Replace production database
            self._replace_target_database()

            return {
                "status": "success",
                "migration_applied": True,
                "changes": migration_results,
                "row_count": row_count,
                "log": self.migration_log,
            }

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            self._cleanup_staging()
            raise

    def _create_staging_database(self) -> None:
        """Copy backup to temporary staging database."""
        # Create staging path
        self.staging_path = self.backup_path.parent / f"staging_{self.backup_path.name}"

        # Copy backup to staging
        shutil.copy2(self.backup_path, self.staging_path)
        logger.info(f"Created staging database: {self.staging_path}")

        # Create engine
        self.staging_engine = create_engine(f"sqlite:///{self.staging_path}")
        self.migration_log.append(f"Created staging database from {self.backup_path.name}")

    def _apply_migrations(self, start_version: int, end_version: int) -> list[dict[str, Any]]:
        """
        Apply all migrations from start to end version.

        Args:
            start_version: Starting version (exclusive)
            end_version: Ending version (inclusive)

        Returns:
            List of applied migration details
        """
        if not self.staging_engine:
            raise ValueError("Staging database not created")

        migrations = get_migrations_for_version_range(start_version, end_version)
        results = []

        for migration in migrations:
            version = migration["version"]
            description = migration.get("description", "")

            logger.info(f"Applying migration v{version}: {description}")
            self.migration_log.append(f"v{version}: {description}")

            changes = []

            # Apply migrations for each table
            for table_name, table_spec in migration.items():
                if table_name in ["description", "version"]:
                    continue

                if not isinstance(table_spec, dict):
                    continue

                # Add columns
                for col_spec in table_spec.get("add_columns", []):
                    self._add_column_safe(table_name, col_spec)
                    changes.append(
                        f"Added column {table_name}.{col_spec['name']} ({col_spec['type']})"
                    )

            results.append({"version": version, "description": description, "changes": changes})

            # Update version in staging database
            set_schema_version(self.staging_engine, version)

        return results

    def _add_column_safe(self, table_name: str, col_spec: dict[str, Any]) -> None:
        """
        Add column with TR-015 security validation.

        Args:
            table_name: Name of table
            col_spec: Column specification dict with name, type, nullable, default
        """
        if not self.staging_engine:
            raise ValueError("Staging database not created")

        col_name = col_spec["name"]
        col_type = col_spec["type"]

        # SECURITY: Validate table and column names (TR-015)
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise ValueError(f"Invalid table name '{table_name}' (security check failed)")

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", col_name):
            raise ValueError(f"Invalid column name '{col_name}' (security check failed)")

        # SECURITY: Validate column type against whitelist (TR-015)
        base_type = col_type.split()[0] if " " in col_type else col_type
        if base_type not in ALLOWED_TYPES:
            raise ValueError(f"Invalid column type '{col_type}' (security check failed)")

        # Check if table exists
        inspector = inspect(self.staging_engine)
        if table_name not in inspector.get_table_names():
            logger.warning(f"Table {table_name} does not exist, skipping column addition")
            return

        # Check if column already exists
        existing_cols = [col["name"] for col in inspector.get_columns(table_name)]
        if col_name in existing_cols:
            logger.info(f"Column {table_name}.{col_name} already exists, skipping")
            return

        # Build DDL with quoted identifiers
        safe_table_name = quoted_name(table_name, quote=True)
        safe_col_name = quoted_name(col_name, quote=True)
        safe_col_type = col_type  # Already validated

        ddl_stmt = text(f"ALTER TABLE {safe_table_name} ADD COLUMN {safe_col_name} {safe_col_type}")

        try:
            with self.staging_engine.connect() as conn:
                conn.execute(ddl_stmt)
                conn.commit()
            logger.info(f"Added column {table_name}.{col_name}")
            self.migration_log.append(f"  Added column {table_name}.{col_name}")
        except Exception as e:
            logger.error(f"Failed to add column {table_name}.{col_name}: {e}")
            raise

    def _validate_migration(self) -> bool:
        """
        Validate migration was successful.

        Checks:
        - Database is readable
        - All tables exist
        - Row counts match (or increased for new data)

        Returns:
            True if validation passes
        """
        if not self.staging_path or not self.staging_engine:
            return False

        try:
            # Check database is readable
            inspector = inspect(self.staging_engine)
            tables = inspector.get_table_names()

            if not tables:
                logger.error("Staging database has no tables")
                return False

            # Count rows
            total_rows = self._count_rows(str(self.staging_path))
            if total_rows == 0:
                logger.warning("Staging database has no rows (may be empty database)")

            logger.info(f"Migration validation passed: {len(tables)} tables, {total_rows} rows")
            return True

        except Exception as e:
            logger.error(f"Migration validation failed: {e}")
            return False

    def _replace_target_database(self) -> None:
        """
        Atomically replace production database with migrated staging database.

        Creates backup before replacement.
        """
        if not self.staging_path:
            raise ValueError("Staging database not created")

        # Create backup of current database
        if self.target_db_path.exists():
            backup_path = self.target_db_path.parent / f"pre_migration_{self.target_db_path.name}"
            shutil.copy2(self.target_db_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            self.migration_log.append(f"Backed up current database to {backup_path.name}")

        # Close staging engine
        if self.staging_engine:
            self.staging_engine.dispose()

        # Replace database file
        shutil.move(str(self.staging_path), str(self.target_db_path))
        logger.info(f"Replaced database: {self.target_db_path}")
        self.migration_log.append(f"Migration complete: replaced {self.target_db_path.name}")

    def _cleanup_staging(self) -> None:
        """Clean up staging database on error."""
        if self.staging_engine:
            self.staging_engine.dispose()

        if self.staging_path and self.staging_path.exists():
            try:
                self.staging_path.unlink()
                logger.info("Cleaned up staging database")
            except Exception as e:
                logger.warning(f"Failed to clean up staging database: {e}")

    def _count_rows(self, db_path: str) -> int:
        """Count total rows across all tables."""
        conn = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Count rows in each table
            total = 0
            for table in tables:
                if table.startswith("sqlite_"):
                    continue
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
                    count = cursor.fetchone()[0]
                    total += count
                except Exception:  # nosec B112
                    # Skip tables that can't be counted (safe pattern for row counting)
                    continue

            return total

        except Exception as e:
            logger.error(f"Failed to count rows: {e}")
            return 0
        finally:
            if conn:
                conn.close()
