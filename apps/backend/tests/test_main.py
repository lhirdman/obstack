import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test the root endpoint returns the expected message."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Observastack Backend is running."}


def test_health_check():
    """Test that the API is responsive."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()