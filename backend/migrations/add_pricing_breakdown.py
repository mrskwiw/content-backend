"""
Migration: Add pricing breakdown columns to projects table.
Date: 2026-02-16

Adds five columns that store a granular cost breakdown captured at project
creation time:
  - posts_cost         (FLOAT)  num_posts * price_per_post
  - research_addon_cost(FLOAT)  num_posts * research_price_per_post
  - tools_cost         (FLOAT)  tool cost after bundle discounts
  - discount_amount    (FLOAT)  bundle savings amount
  - selected_tools     (JSON)   List[str] of selected tool IDs

Existing projects are backfilled:
  - posts_cost set to total_price where available, otherwise 0
  - remaining columns set to 0 / []
"""

import sys
from pathlib import Path

# Allow importing from backend package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load environment variables before importing ORM
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from backend.database import engine  # noqa: E402
from sqlalchemy import text  # noqa: E402


# Columns to add: (column_name, sql_type, default_expression)
_NEW_COLUMNS = [
    ("posts_cost", "FLOAT", "0"),
    ("research_addon_cost", "FLOAT", "0"),
    ("tools_cost", "FLOAT", "0"),
    ("discount_amount", "FLOAT", "0"),
    ("selected_tools", "JSON", None),  # NULL default — no expression needed
]


def _column_exists(conn, table: str, column: str) -> bool:
    """Check whether a column already exists in the given table."""
    result = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :column"
        ),
        {"table": table, "column": column},
    )
    return result.scalar() > 0


def run_migration() -> bool:
    """Execute the migration and return True on success."""
    print("Starting migration: add_pricing_breakdown")

    # ------------------------------------------------------------------ #
    # Step 1: Add new columns                                              #
    # ------------------------------------------------------------------ #
    print("\nStep 1: Adding columns to projects table...")
    try:
        with engine.connect() as conn:
            for col_name, col_type, default_expr in _NEW_COLUMNS:
                if _column_exists(conn, "projects", col_name):
                    print(f"  Column '{col_name}' already exists — skipping.")
                    continue

                if default_expr is not None:
                    ddl = (
                        f"ALTER TABLE projects "
                        f"ADD COLUMN {col_name} {col_type} DEFAULT {default_expr}"
                    )
                else:
                    ddl = f"ALTER TABLE projects ADD COLUMN {col_name} {col_type}"

                conn.execute(text(ddl))
                print(f"  Added column '{col_name}' ({col_type}).")

            conn.commit()
    except Exception as exc:
        print(f"ERROR adding columns: {exc}")
        return False

    # ------------------------------------------------------------------ #
    # Step 2: Backfill existing projects                                   #
    # ------------------------------------------------------------------ #
    print("\nStep 2: Backfilling existing projects...")
    try:
        with engine.connect() as conn:
            # Set posts_cost = total_price where it is non-null and posts_cost is NULL/0
            conn.execute(
                text(
                    "UPDATE projects "
                    "SET posts_cost = total_price "
                    "WHERE total_price IS NOT NULL "
                    "  AND (posts_cost IS NULL OR posts_cost = 0)"
                )
            )
            # Zero-fill the cost columns that have no historical data
            conn.execute(
                text(
                    "UPDATE projects "
                    "SET research_addon_cost = 0 "
                    "WHERE research_addon_cost IS NULL"
                )
            )
            conn.execute(text("UPDATE projects " "SET tools_cost = 0 " "WHERE tools_cost IS NULL"))
            conn.execute(
                text("UPDATE projects " "SET discount_amount = 0 " "WHERE discount_amount IS NULL")
            )
            # Empty array for selected_tools (stored as JSON '[]')
            conn.execute(
                text("UPDATE projects " "SET selected_tools = '[]' " "WHERE selected_tools IS NULL")
            )
            conn.commit()
            print("  Backfill complete.")
    except Exception as exc:
        print(f"ERROR during backfill: {exc}")
        return False

    print("\n" + "=" * 50)
    print("Migration add_pricing_breakdown completed successfully!")
    print("=" * 50)
    return True


if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
