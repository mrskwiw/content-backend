"""
Database migration: Add target_platform to projects table.

This migration adds the target_platform column to support platform-specific
content generation optimization (LinkedIn, Twitter, Medium, etc.).

Run with: python backend/database/add_target_platform_migration.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from backend.database import engine


def upgrade():
    """Add target_platform column to projects table."""
    print("Adding target_platform column to projects table...")

    with engine.connect() as conn:
        # Add column (nullable first to allow existing rows)
        conn.execute(
            text(
                """
                ALTER TABLE projects
                ADD COLUMN IF NOT EXISTS target_platform VARCHAR DEFAULT 'generic'
                """
            )
        )

        # Update existing projects to have 'generic' as default
        conn.execute(
            text(
                """
                UPDATE projects
                SET target_platform = 'generic'
                WHERE target_platform IS NULL
                """
            )
        )

        conn.commit()

    print("✅ Migration completed successfully!")
    print("   - Added target_platform column")
    print("   - Set default value 'generic' for existing projects")


def downgrade():
    """Remove target_platform column from projects table."""
    print("Removing target_platform column from projects table...")

    with engine.connect() as conn:
        conn.execute(
            text(
                """
                ALTER TABLE projects
                DROP COLUMN IF EXISTS target_platform
                """
            )
        )
        conn.commit()

    print("✅ Downgrade completed successfully!")
    print("   - Removed target_platform column")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Database migration for target_platform")
    parser.add_argument(
        "--downgrade",
        action="store_true",
        help="Downgrade (remove) the migration instead of applying it",
    )

    args = parser.parse_args()

    if args.downgrade:
        downgrade()
    else:
        upgrade()
