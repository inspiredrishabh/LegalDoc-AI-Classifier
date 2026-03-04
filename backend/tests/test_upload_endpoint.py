"""Tests for upload endpoint using FastAPI TestClient."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create test client with mocked services."""
    with patch("app.dependencies.init_services"), \
         patch("app.dependencies.get_settings") as mock_settings:
        # Mock settings
        settings = MagicMock()
        settings.ALLOWED_ORIGINS = ["http://localhost:5173"]
        settings.LLM_MODE = "local"
        settings.MAX_FILE_SIZE_MB = 50
        settings.DATA_DIR = "."
        mock_settings.return_value = settings

        from app.main import create_app
        app = create_app()
        yield TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "LegalDoc AI Backend"


def test_upload_no_files(client):
    response = client.post("/v1/files/upload-batch")
    # FastAPI returns 422 for missing required field
    assert response.status_code == 422


def test_upload_batch_with_file(client):
    """Test uploading a valid file (MIME validation mocked)."""
    with patch("app.routes.upload.validate_file_type", return_value=(True, "image/png")):
        # Create a fake PNG file (1x1 pixel)
        fake_png = b'\x89PNG\r\n\x1a\n' + b'\x00' * 100
        response = client.post(
            "/v1/files/upload-batch",
            files=[("files", ("test.png", fake_png, "image/png"))],
        )
        assert response.status_code == 200
        data = response.json()
        assert "batch_id" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] in ["pending", "processing"]


def test_upload_empty_file(client):
    """Empty file should be rejected."""
    response = client.post(
        "/v1/files/upload-batch",
        files=[("files", ("empty.png", b"", "image/png"))],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["results"][0]["status"] == "failed"
    assert "Empty file" in data["results"][0]["error"]


def test_upload_invalid_mime(client):
    """Invalid MIME type should be rejected."""
    with patch("app.routes.upload.validate_file_type", return_value=(False, "text/plain")):
        response = client.post(
            "/v1/files/upload-batch",
            files=[("files", ("test.txt", b"hello world", "text/plain"))],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["results"][0]["status"] == "failed"
        assert "Unsupported file type" in data["results"][0]["error"]


def test_batch_status_not_found(client):
    response = client.get("/v1/files/batch/nonexistent-id")
    assert response.status_code == 404
