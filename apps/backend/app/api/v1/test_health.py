import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test the health check endpoint returns correct status."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_response_model():
    """Test that the health check response follows the expected model."""
    response = client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert isinstance(data["status"], str)
    assert data["status"] == "ok"