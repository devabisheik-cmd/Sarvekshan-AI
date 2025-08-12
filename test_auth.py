import pytest
from fastapi.testclient import TestClient

def test_register_user(client: TestClient):
    """Test user registration"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "newpassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data

def test_register_duplicate_username(client: TestClient, test_user):
    """Test registration with duplicate username"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password",
            "full_name": "Different User"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_register_duplicate_email(client: TestClient, test_user):
    """Test registration with duplicate email"""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "differentuser",
            "email": test_user.email,
            "password": "password",
            "full_name": "Different User"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]

def test_login_success(client: TestClient, test_user):
    """Test successful login"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_username(client: TestClient):
    """Test login with invalid username"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent",
            "password": "password"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_invalid_password(client: TestClient, test_user):
    """Test login with invalid password"""
    response = client.post(
        "/api/auth/login",
        data={
            "username": test_user.username,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_get_current_user(client: TestClient, auth_headers):
    """Test getting current user info"""
    response = client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "hashed_password" not in data

def test_get_current_user_unauthorized(client: TestClient):
    """Test getting current user without authentication"""
    response = client.get("/api/auth/me")
    assert response.status_code == 401

def test_get_current_user_invalid_token(client: TestClient):
    """Test getting current user with invalid token"""
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401

def test_password_validation():
    """Test password validation requirements"""
    # This would test password strength requirements
    # Implementation depends on your password validation logic
    pass

def test_token_expiration():
    """Test token expiration handling"""
    # This would test expired token handling
    # Implementation depends on your token expiration logic
    pass

class TestAuthSecurity:
    """Security-focused authentication tests"""
    
    def test_sql_injection_in_login(self, client: TestClient):
        """Test SQL injection protection in login"""
        response = client.post(
            "/api/auth/login",
            data={
                "username": "admin'; DROP TABLE users; --",
                "password": "password"
            }
        )
        assert response.status_code == 401
        # Ensure the injection attempt doesn't succeed
    
    def test_xss_in_registration(self, client: TestClient):
        """Test XSS protection in registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "<script>alert('xss')</script>",
                "email": "test@example.com",
                "password": "password",
                "full_name": "<img src=x onerror=alert('xss')>"
            }
        )
        # Should either reject or sanitize the input
        if response.status_code == 201:
            data = response.json()
            assert "<script>" not in data["username"]
            assert "<img" not in data["full_name"]
    
    def test_rate_limiting_login(self, client: TestClient):
        """Test rate limiting on login attempts"""
        # Make multiple failed login attempts
        for _ in range(10):
            response = client.post(
                "/api/auth/login",
                data={
                    "username": "nonexistent",
                    "password": "wrongpassword"
                }
            )
        
        # After many attempts, should be rate limited
        # Implementation depends on your rate limiting strategy
        pass
    
    def test_password_hashing(self, db_session, test_user):
        """Test that passwords are properly hashed"""
        # Verify password is not stored in plain text
        assert test_user.hashed_password != "testpassword"
        assert len(test_user.hashed_password) > 50  # Hashed passwords are long
    
    def test_session_security(self, client: TestClient, auth_headers):
        """Test session security measures"""
        # Test that tokens are properly validated
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        # Test with modified token
        modified_headers = auth_headers.copy()
        token = modified_headers["Authorization"].split(" ")[1]
        modified_token = token[:-5] + "xxxxx"  # Modify last 5 characters
        modified_headers["Authorization"] = f"Bearer {modified_token}"
        
        response = client.get("/api/auth/me", headers=modified_headers)
        assert response.status_code == 401

