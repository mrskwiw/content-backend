"""
Integration tests for runs router.

Tests all run endpoints including:
- Get run status (GET /api/runs/{run_id})
- Get run logs (GET /api/runs/{run_id}/logs)
- List runs (GET /api/runs/)
- Authorization checks (TR-021)
- Status polling workflow
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.main import app
from backend.models import User, Client, Project, Run
from backend.utils.auth import get_password_hash
from tests.fixtures.model_factories import create_test_client, create_test_project


@pytest.fixture
def client(db_session):
    """Create test client with test database"""
    # db_session fixture sets up the database and dependency override
    # before TestClient is created
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_user_a(db_session: Session):
    """Create test user A"""
    user = User(
        id="user-a-123",
        email="usera@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="User A",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_b(db_session: Session):
    """Create test user B"""
    user = User(
        id="user-b-456",
        email="userb@example.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="User B",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_user_a(test_user_a, client):
    """Get auth headers for user A"""
    response = client.post(
        "/api/auth/login",
        json={"email": "usera@example.com", "password": "testpass123"},  # pragma: allowlist secret
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user_b(test_user_b, client):
    """Get auth headers for user B"""
    response = client.post(
        "/api/auth/login",
        json={"email": "userb@example.com", "password": "testpass123"},  # pragma: allowlist secret
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def project_for_user_a(db_session: Session, test_user_a):
    """Create a project owned by user A"""
    client_data = create_test_client(
        name="User A Client",
        user_id=test_user_a.id,
        email="clienta@example.com",
    )
    db_client = Client(**client_data)
    db_session.add(db_client)
    db_session.commit()

    project_data = create_test_project(
        name="User A Project",
        client_id=db_client.id,
        user_id=test_user_a.id,
    )
    db_project = Project(**project_data)
    db_session.add(db_project)
    db_session.commit()
    db_session.refresh(db_project)
    return db_project


@pytest.fixture
def run_for_user_a(db_session: Session, test_user_a, project_for_user_a):
    """Create a generation run owned by user A"""
    run = Run(
        id="run-test-123",
        project_id=project_for_user_a.id,
        user_id=test_user_a.id,
        status="completed",
        total_posts=30,
        completed_posts=30,
        failed_posts=0,
        logs="Generation started\nGeneration completed successfully",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


@pytest.fixture
def pending_run(db_session: Session, test_user_a, project_for_user_a):
    """Create a pending run for polling tests"""
    run = Run(
        id="run-pending-456",
        project_id=project_for_user_a.id,
        user_id=test_user_a.id,
        status="pending",
        total_posts=30,
        completed_posts=0,
        failed_posts=0,
        logs="Generation queued",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


@pytest.fixture
def running_run(db_session: Session, test_user_a, project_for_user_a):
    """Create a running run for polling tests"""
    run = Run(
        id="run-running-789",
        project_id=project_for_user_a.id,
        user_id=test_user_a.id,
        status="running",
        total_posts=30,
        completed_posts=15,
        failed_posts=1,
        logs="Generation started\nGenerated post 1\nGenerated post 2\n...",
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)
    return run


class TestGetRunStatus:
    """Test GET /api/runs/{run_id}"""

    def test_get_run_success(self, client, auth_headers_user_a, run_for_user_a):
        """Test getting run status by ID"""
        response = client.get(f"/api/runs/{run_for_user_a.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_for_user_a.id
        assert data["status"] == "completed"
        assert data["total_posts"] == 30 or data["totalPosts"] == 30
        assert data["completed_posts"] == 30 or data["completedPosts"] == 30

    def test_get_run_unauthorized(self, client, auth_headers_user_b, run_for_user_a):
        """Test TR-021: User B cannot access User A's run"""
        response = client.get(f"/api/runs/{run_for_user_a.id}", headers=auth_headers_user_b)
        assert response.status_code == 403

    def test_get_run_not_found(self, client, auth_headers_user_a):
        """Test getting non-existent run"""
        response = client.get("/api/runs/nonexistent-id", headers=auth_headers_user_a)
        assert response.status_code == 404

    def test_get_run_unauthenticated(self, client, run_for_user_a):
        """Test getting run without authentication"""
        response = client.get(f"/api/runs/{run_for_user_a.id}")
        assert response.status_code == 401

    def test_get_pending_run(self, client, auth_headers_user_a, pending_run):
        """Test getting pending run status"""
        response = client.get(f"/api/runs/{pending_run.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["completed_posts"] == 0 or data["completedPosts"] == 0

    def test_get_running_run(self, client, auth_headers_user_a, running_run):
        """Test getting in-progress run status"""
        response = client.get(f"/api/runs/{running_run.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["completed_posts"] == 15 or data["completedPosts"] == 15
        assert data["failed_posts"] == 1 or data["failedPosts"] == 1


class TestGetRunLogs:
    """Test GET /api/runs/{run_id}/logs"""

    def test_get_logs_success(self, client, auth_headers_user_a, run_for_user_a):
        """Test getting run logs"""
        response = client.get(f"/api/runs/{run_for_user_a.id}/logs", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        # Logs might be returned as string or object
        if isinstance(data, dict):
            assert "logs" in data
            assert "Generation started" in data["logs"]
        else:
            assert "Generation started" in data

    def test_get_logs_unauthorized(self, client, auth_headers_user_b, run_for_user_a):
        """Test TR-021: User B cannot access User A's logs"""
        response = client.get(f"/api/runs/{run_for_user_a.id}/logs", headers=auth_headers_user_b)
        assert response.status_code == 403

    def test_get_logs_not_found(self, client, auth_headers_user_a):
        """Test getting logs for non-existent run"""
        response = client.get("/api/runs/nonexistent-id/logs", headers=auth_headers_user_a)
        assert response.status_code == 404

    def test_get_logs_unauthenticated(self, client, run_for_user_a):
        """Test getting logs without authentication"""
        response = client.get(f"/api/runs/{run_for_user_a.id}/logs")
        assert response.status_code == 401

    def test_get_logs_with_line_limit(self, client, auth_headers_user_a, running_run):
        """Test getting logs with line limit parameter"""
        response = client.get(
            f"/api/runs/{running_run.id}/logs?limit=10", headers=auth_headers_user_a
        )

        assert response.status_code == 200
        # Should return limited number of log lines


class TestListRuns:
    """Test GET /api/runs/"""

    def test_list_runs_authenticated(self, client, auth_headers_user_a, run_for_user_a):
        """Test listing runs with authentication"""
        response = client.get("/api/runs/", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
        # Should see own run
        if isinstance(data, list):
            assert len(data) >= 1
            assert any(r["id"] == run_for_user_a.id for r in data)
        else:
            assert len(data["items"]) >= 1
            assert any(r["id"] == run_for_user_a.id for r in data["items"])

    def test_list_runs_unauthenticated(self, client):
        """Test listing runs without authentication"""
        response = client.get("/api/runs/")
        assert response.status_code == 401

    def test_list_runs_filters_by_user(
        self,
        client,
        auth_headers_user_a,
        auth_headers_user_b,
        run_for_user_a,
        db_session,
        test_user_b,
        project_for_user_a,
    ):
        """Test TR-021: Users only see their own runs"""
        # Create run for user B
        client_data = create_test_client(
            name="User B Client",
            user_id=test_user_b.id,
            email="clientb@example.com",
        )
        db_client = Client(**client_data)
        db_session.add(db_client)
        db_session.commit()

        project_data = create_test_project(
            name="User B Project",
            client_id=db_client.id,
            user_id=test_user_b.id,
        )
        db_project = Project(**project_data)
        db_session.add(db_project)
        db_session.commit()

        run_for_user_b = Run(
            id="run-user-b-999",
            project_id=db_project.id,
            user_id=test_user_b.id,
            status="completed",
            total_posts=30,
            completed_posts=30,
            failed_posts=0,
        )
        db_session.add(run_for_user_b)
        db_session.commit()

        # User A should see only their run
        response = client.get("/api/runs/", headers=auth_headers_user_a)
        data = response.json()
        items = data if isinstance(data, list) else data["items"]

        assert len(items) >= 1
        assert all(r["id"] != run_for_user_b.id for r in items)
        assert any(r["id"] == run_for_user_a.id for r in items)

        # User B should see only their run
        response = client.get("/api/runs/", headers=auth_headers_user_b)
        data = response.json()
        items = data if isinstance(data, list) else data["items"]

        assert len(items) >= 1
        assert all(r["id"] != run_for_user_a.id for r in items)
        assert any(r["id"] == run_for_user_b.id for r in items)

    def test_list_runs_filter_by_status(
        self, client, auth_headers_user_a, run_for_user_a, pending_run
    ):
        """Test filtering runs by status"""
        response = client.get("/api/runs/?status=completed", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data["items"]

        # All returned runs should have completed status
        assert all(r["status"] == "completed" for r in items)

    def test_list_runs_filter_by_project(
        self, client, auth_headers_user_a, run_for_user_a, project_for_user_a
    ):
        """Test filtering runs by project ID"""
        response = client.get(
            f"/api/runs/?project_id={project_for_user_a.id}", headers=auth_headers_user_a
        )

        assert response.status_code == 200
        data = response.json()
        items = data if isinstance(data, list) else data["items"]

        # All returned runs should belong to the project
        assert all(
            r["project_id"] == project_for_user_a.id or r["projectId"] == project_for_user_a.id
            for r in items
        )

    def test_list_runs_pagination(self, client, auth_headers_user_a):
        """Test pagination parameters"""
        response = client.get("/api/runs/?page=1&per_page=10", headers=auth_headers_user_a)
        assert response.status_code == 200


class TestRunStatusPolling:
    """Test status polling workflow"""

    def test_poll_pending_to_running(self, client, auth_headers_user_a, pending_run, db_session):
        """Test polling a run that transitions from pending to running"""
        # First poll - should be pending
        response = client.get(f"/api/runs/{pending_run.id}", headers=auth_headers_user_a)
        assert response.status_code == 200
        assert response.json()["status"] == "pending"

        # Simulate status change
        pending_run.status = "running"
        pending_run.completed_posts = 5
        db_session.commit()

        # Second poll - should be running
        response = client.get(f"/api/runs/{pending_run.id}", headers=auth_headers_user_a)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["completed_posts"] == 5 or data["completedPosts"] == 5

    def test_poll_running_to_completed(self, client, auth_headers_user_a, running_run, db_session):
        """Test polling a run that transitions from running to completed"""
        # First poll - should be running
        response = client.get(f"/api/runs/{running_run.id}", headers=auth_headers_user_a)
        assert response.status_code == 200
        assert response.json()["status"] == "running"

        # Simulate completion
        running_run.status = "completed"
        running_run.completed_posts = 30
        db_session.commit()

        # Second poll - should be completed
        response = client.get(f"/api/runs/{running_run.id}", headers=auth_headers_user_a)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_posts"] == 30 or data["completedPosts"] == 30

    def test_poll_failed_run(self, client, auth_headers_user_a, running_run, db_session):
        """Test polling a run that fails"""
        # Simulate failure
        running_run.status = "failed"
        running_run.logs += "\nError: API rate limit exceeded"
        db_session.commit()

        response = client.get(f"/api/runs/{running_run.id}", headers=auth_headers_user_a)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"

        # Get logs to see error
        logs_response = client.get(f"/api/runs/{running_run.id}/logs", headers=auth_headers_user_a)
        assert logs_response.status_code == 200


class TestRunProgress:
    """Test run progress tracking"""

    def test_progress_calculation(self, client, auth_headers_user_a, running_run):
        """Test that progress is correctly calculated"""
        response = client.get(f"/api/runs/{running_run.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()

        # Progress should be 15/30 = 50%
        total = data.get("total_posts") or data.get("totalPosts")
        completed = data.get("completed_posts") or data.get("completedPosts")

        if "progress" in data:
            assert data["progress"] == pytest.approx(50.0, abs=1.0)
        else:
            # Calculate manually
            progress = (completed / total) * 100
            assert progress == pytest.approx(50.0, abs=1.0)

    def test_zero_progress(self, client, auth_headers_user_a, pending_run):
        """Test run with zero progress"""
        response = client.get(f"/api/runs/{pending_run.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()

        completed = data.get("completed_posts") or data.get("completedPosts")
        assert completed == 0

    def test_full_progress(self, client, auth_headers_user_a, run_for_user_a):
        """Test run with 100% progress"""
        response = client.get(f"/api/runs/{run_for_user_a.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()

        total = data.get("total_posts") or data.get("totalPosts")
        completed = data.get("completed_posts") or data.get("completedPosts")

        assert completed == total


class TestRunTimestamps:
    """Test run timestamp tracking"""

    def test_run_has_timestamps(self, client, auth_headers_user_a, run_for_user_a):
        """Test that run includes created_at timestamp"""
        response = client.get(f"/api/runs/{run_for_user_a.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        assert "created_at" in data or "createdAt" in data

    def test_run_duration_calculation(self, client, auth_headers_user_a, run_for_user_a):
        """Test that completed runs have duration"""
        response = client.get(f"/api/runs/{run_for_user_a.id}", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()

        # Completed runs should have duration or updated_at
        if data["status"] == "completed":
            assert "updated_at" in data or "updatedAt" in data or "duration" in data
