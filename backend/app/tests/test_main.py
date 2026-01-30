# backend/tests/test_main.py

"""
Test main application endpoints.
"""


def test_root_endpoint(client):
    """Test root endpoint returns correct info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "ClearDrive.lk API"
    assert "version" in data
    assert "docs" in data


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data
