"""
Migration: Add settings table for storing user preferences and API keys

Version: 5
"""

from sqlalchemy import text
from backend.database import engine


def upgrade():
    """Add settings table"""
    with engine.connect() as conn:
        # Create settings table
        conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                key VARCHAR(100) NOT NULL,
                value TEXT,
                category VARCHAR(50) NOT NULL,
                is_encrypted INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """
            )
        )

        # Create indexes
        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_settings_user_id
            ON settings(user_id)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_settings_key
            ON settings(key)
        """
            )
        )

        conn.execute(
            text(
                """
            CREATE INDEX IF NOT EXISTS idx_settings_category
            ON settings(category)
        """
            )
        )

        # Create unique constraint on user_id + key + category
        conn.execute(
            text(
                """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_settings_unique
            ON settings(user_id, key, category)
        """
            )
        )

        # Update schema version to 5
        conn.execute(text("PRAGMA user_version = 5"))

        conn.commit()

    print("[OK] Settings table created successfully")
    print("[OK] Schema version updated to 5")


def downgrade():
    """Remove settings table"""
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS settings"))
        conn.execute(text("PRAGMA user_version = 4"))
        conn.commit()

    print("[OK] Settings table removed")
    print("[OK] Schema version downgraded to 4")


if __name__ == "__main__":
    print("Running migration: Add settings table (v5)")
    upgrade()
