import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/users/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_register_duplicate_username(client):
    """Test registration with duplicate username."""
    # First registration
    client.post(
        "/users/register",
        json={
            "username": "duplicateuser",
            "email": "unique@example.com",
            "password": "testpassword123"
        }
    )
    
    # Second registration with same username
    response = client.post(
        "/users/register",
        json={
            "username": "duplicateuser",
            "email": "another@example.com",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 400


def test_login(client):
    """Test user login."""
    # First register a user
    client.post(
        "/users/register",
        json={
            "username": "loginuser",
            "email": "login@example.com",
            "password": "testpassword123"
        }
    )
    
    # Then login
    response = client.post(
        "/users/login",
        data={
            "username": "loginuser",
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/users/login",
        data={
            "username": "nonexistent",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
