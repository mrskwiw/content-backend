"""
Migration: Add story template columns to mined_stories and story_usage.
Date: 2026-04-01

Changes:
  mined_stories:
    - eligible_templates (JSON)
  story_usage:
    - template_name (VARCHAR 100)
    - project_id    (VARCHAR)
    - UNIQUE INDEX uix_story_template_project(story_id, template_name, project_id)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.database import engine  # noqa: E402
from sqlalchemy import text  # noqa: E402


def _column_exists(conn, table: str, column: str) -> bool:
    """Check whether a column already exists in the given table."""
    try:
        result = conn.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name = :table AND column_name = :column"
            ),
            {"table": table, "column": column},
        )
        return result.scalar() > 0
    except Exception:
        result = conn.execute(text(f"PRAGMA table_info({table})"))
        cols = [row[1] for row in result.fetchall()]
        return column in cols


def _index_exists(conn, index_name: str) -> bool:
    """Check whether an index already exists."""
    try:
        result = conn.execute(
            text("SELECT COUNT(*) FROM information_schema.statistics " "WHERE index_name = :name"),
            {"name": index_name},
        )
        return result.scalar() > 0
    except Exception:
        try:
            result = conn.execute(text(f"PRAGMA index_info({index_name})"))
            return len(result.fetchall()) > 0
        except Exception:
            return False


def run_migration() -> bool:
    """Execute the migration and return True on success."""
    print("Starting migration: add_story_template_columns")

    # Step 1: Add eligible_templates to mined_stories
    print("Step 1: Adding eligible_templates to mined_stories...")
    try:
        with engine.connect() as conn:
            if _column_exists(conn, "mined_stories", "eligible_templates"):
                print("  Column already exists -- skipping.")
            else:
                conn.execute(text("ALTER TABLE mined_stories ADD COLUMN eligible_templates JSON"))
                print("  Added eligible_templates JSON column.")
            conn.commit()
    except Exception as exc:
        print(f"ERROR step 1: {exc}")
        return False

    # Step 2: Add template_name and project_id to story_usage
    print("Step 2: Adding template_name and project_id to story_usage...")
    try:
        with engine.connect() as conn:
            if _column_exists(conn, "story_usage", "template_name"):
                print("  template_name already exists -- skipping.")
            else:
                conn.execute(text("ALTER TABLE story_usage ADD COLUMN template_name VARCHAR(100)"))
                print("  Added template_name VARCHAR(100).")

            if _column_exists(conn, "story_usage", "project_id"):
                print("  project_id already exists -- skipping.")
            else:
                conn.execute(text("ALTER TABLE story_usage ADD COLUMN project_id VARCHAR"))
                print("  Added project_id VARCHAR.")

            conn.commit()
    except Exception as exc:
        print(f"ERROR step 2: {exc}")
        return False

    # Step 3: Create unique index
    print("Step 3: Creating unique index uix_story_template_project...")
    try:
        with engine.connect() as conn:
            if _index_exists(conn, "uix_story_template_project"):
                print("  Index already exists -- skipping.")
            else:
                conn.execute(
                    text(
                        "CREATE UNIQUE INDEX uix_story_template_project "
                        "ON story_usage(story_id, template_name, project_id)"
                    )
                )
                print("  Index created.")
            conn.commit()
    except Exception as exc:
        print(f"WARNING step 3 (index may already exist): {exc}")

    print("Migration add_story_template_columns completed!")
    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
