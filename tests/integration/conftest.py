"""
Configuration for integration tests.

Sets up Python path to allow backend imports to work correctly.
Provides database fixtures and mocks for integration testing.
"""

import sys
from pathlib import Path
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to Python path so relative imports work
backend_dir = Path(__file__).parent.parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Add project root to path for src imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import database and models FIRST before app
from backend.database import Base, get_db  # noqa: E402
import backend.models  # noqa: E402, F401 - Import models before app to register them

from backend.main import app  # noqa: E402


@pytest.fixture(scope="function", autouse=False)
def db_session():
    """
    Create a fresh database session for each test.

    This fixture creates an in-memory SQLite database, sets up all tables,
    and overrides the FastAPI dependency to use this test database.

    Each test gets a completely isolated database that is torn down after
    the test completes.
    """
    # Create a new engine for each test
    # CRITICAL: Use StaticPool for in-memory SQLite to ensure all connections
    # share the same database. Without this, each connection gets a separate
    # empty database and tests fail with "no such table" errors.
    engine = create_engine(
        "sqlite:///:memory:",
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Debug: Print registered tables
    print(f"\n[DEBUG] Registered tables in Base.metadata: {list(Base.metadata.tables.keys())}")
    print(f"[DEBUG] Test engine ID: {id(engine)}, URL: {engine.url}")

    # Create all tables
    Base.metadata.create_all(engine)

    # Debug: Verify tables were created
    from sqlalchemy import inspect

    inspector = inspect(engine)
    created_tables = inspector.get_table_names()
    print(f"[DEBUG] Created tables in database: {created_tables}")

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create the session
    session = SessionLocal()

    # Override the get_db dependency
    def override_get_db():
        print(
            f"[DEBUG] override_get_db called, yielding session {id(session)}, engine {id(session.bind)}"
        )
        # Verify this session can access tables
        from sqlalchemy import inspect

        inspector = inspect(session.bind)
        tables_in_session = inspector.get_table_names()
        print(f"[DEBUG] Tables visible in override session: {tables_in_session}")
        try:
            yield session
        finally:
            pass  # Session will be closed in fixture cleanup

    # Apply the override
    app.dependency_overrides[get_db] = override_get_db
    print("[DEBUG] Dependency override set for get_db")
    print(f"[DEBUG] App dependency overrides: {list(app.dependency_overrides.keys())}")

    # Provide the session to the test
    yield session

    # Cleanup after test
    try:
        session.rollback()  # Rollback any uncommitted transactions
    except Exception:
        pass

    try:
        session.close()
    except Exception:
        pass

    # Clear the override
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]

    # Drop all tables
    try:
        Base.metadata.drop_all(engine)
    except Exception:
        pass

    # Dispose of the engine
    try:
        engine.dispose()
    except Exception:
        pass
