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

# Import shared fixtures for integration tests
from tests.fixtures.anthropic_responses import (  # noqa: E402, F401
    mock_anthropic_client,
    mock_anthropic_client_with_custom_response,
    mock_anthropic_client_with_error,
)


@pytest.fixture(autouse=True)
def mock_background_tasks(monkeypatch):
    """
    Mock background tasks to not actually run during tests.

    Background tasks in routers create their own database sessions which
    bypass test database mocking. For integration tests, we test the
    endpoint behavior (returns 202 Accepted) without actually running
    the background generation.
    """
    from unittest.mock import Mock

    # Mock BackgroundTasks.add_task to do nothing
    mock_add_task = Mock(return_value=None)

    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    yield mock_add_task


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiting():
    """
    Reset rate limiter storage before each test.

    Rate limiters use in-memory storage that accumulates across tests,
    causing tests to fail when run together due to rate limit exhaustion.
    This fixture resets the storage before each test.
    """
    from backend.utils.http_rate_limiter import (
        limiter,
        strict_limiter,
        standard_limiter,
        lenient_limiter,
    )

    # Reset all rate limiters by clearing their internal storage
    # slowapi uses limits library which stores data in the storage backend
    for rate_limiter in [limiter, strict_limiter, standard_limiter, lenient_limiter]:
        try:
            # Access the storage backend and reset it
            if hasattr(rate_limiter, "_storage") and rate_limiter._storage:
                storage = rate_limiter._storage
                # For memory storage, reset by calling reset() or clearing storage dict
                if hasattr(storage, "reset"):
                    storage.reset()
                elif hasattr(storage, "storage"):
                    storage.storage.clear()
                elif hasattr(storage, "_cache"):
                    storage._cache.clear()
        except Exception:
            pass  # Ignore errors if storage doesn't support reset

    yield

    # No cleanup needed - fixture runs before each test


@pytest.fixture(scope="function", autouse=False)
def db_session(monkeypatch):
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

    # CRITICAL: Also monkeypatch SessionLocal for background tasks
    # Background tasks in generator.py and other routers create their own
    # database sessions using SessionLocal() directly, bypassing dependency injection.
    # We need to patch it to return our test session instead.
    from backend import database

    def mock_sessionlocal():
        """Return the test session for background tasks"""
        print(f"[DEBUG] SessionLocal() called, returning test session {id(session)}")
        return session

    # Patch the SessionLocal callable
    monkeypatch.setattr(database, "SessionLocal", mock_sessionlocal)
    print("[DEBUG] Monkeypatched SessionLocal for background tasks")

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
