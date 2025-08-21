"""
Tests for JWT security middleware functionality.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import JWTMiddleware, jwt_middleware
from app.db.models import User


class TestJWTMiddleware:
    """Test cases for JWT middleware functionality."""

    @pytest.fixture
    def middleware(self):
        """JWT middleware fixture."""
        return JWTMiddleware()

    @pytest.fixture
    def mock_request(self):
        """Mock FastAPI request fixture."""
        request = Mock(spec=Request)
        request.cookies = {}
        request.headers = {}
        return request

    @pytest.fixture
    def mock_db(self):
        """Mock database session fixture."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_user(self):
        """Mock user fixture."""
        user = Mock(spec=User)
        user.id = 1
        user.username = "testuser"
        user.email = "test@example.com"
        user.tenant_id = 1
        user.roles = ["user"]
        return user

    async def test_validate_token_from_cookie(self, middleware, mock_request):
        """Test token validation from HttpOnly cookie."""
        # Create a valid token
        import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        payload = {"user_id": 1, "tenant_id": 1, "roles": ["user"]}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.cookies = {"access_token": token}
        
        result = await middleware.validate_token(mock_request)
        
        assert result is not None
        assert result["user_id"] == 1
        assert result["tenant_id"] == 1
        assert result["roles"] == ["user"]

    async def test_validate_token_from_header(self, middleware, mock_request):
        """Test token validation from Authorization header."""
        # Create a valid token
        import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        payload = {"user_id": 1, "tenant_id": 1, "roles": ["user"]}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.headers = {"authorization": f"Bearer {token}"}
        
        result = await middleware.validate_token(mock_request)
        
        assert result is not None
        assert result["user_id"] == 1
        assert result["tenant_id"] == 1
        assert result["roles"] == ["user"]

    async def test_validate_token_cookie_priority(self, middleware, mock_request):
        """Test that cookie takes priority over header."""
        import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        # Create different tokens for cookie and header
        cookie_payload = {"user_id": 1, "tenant_id": 1, "roles": ["user"]}
        header_payload = {"user_id": 2, "tenant_id": 2, "roles": ["admin"]}
        
        cookie_token = jwt.encode(cookie_payload, SECRET_KEY, algorithm=ALGORITHM)
        header_token = jwt.encode(header_payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.cookies = {"access_token": cookie_token}
        mock_request.headers = {"authorization": f"Bearer {header_token}"}
        
        result = await middleware.validate_token(mock_request)
        
        # Should use cookie token (user_id: 1)
        assert result["user_id"] == 1

    async def test_validate_token_invalid(self, middleware, mock_request):
        """Test validation of invalid token."""
        mock_request.cookies = {"access_token": "invalid-token"}
        
        result = await middleware.validate_token(mock_request)
        
        assert result is None

    async def test_validate_token_missing(self, middleware, mock_request):
        """Test validation when no token is provided."""
        result = await middleware.validate_token(mock_request)
        
        assert result is None

    async def test_validate_token_expired(self, middleware, mock_request):
        """Test validation of expired token."""
        import jwt
        from datetime import datetime, timedelta
        from app.core.security import SECRET_KEY, ALGORITHM
        
        # Create an expired token
        payload = {
            "user_id": 1,
            "tenant_id": 1,
            "roles": ["user"],
            "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.cookies = {"access_token": token}
        
        result = await middleware.validate_token(mock_request)
        
        assert result is None

    async def test_get_current_user_success(self, middleware, mock_request, mock_db, mock_user):
        """Test successful user retrieval."""
        import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        # Create a valid token
        payload = {"user_id": 1, "tenant_id": 1, "roles": ["user"]}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.cookies = {"access_token": token}
        
        # Mock database query
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        mock_db.execute.return_value = mock_result
        
        user = await middleware.get_current_user(mock_request, mock_db)
        
        assert user == mock_user
        mock_db.execute.assert_called_once()

    async def test_get_current_user_invalid_token(self, middleware, mock_request, mock_db):
        """Test user retrieval with invalid token."""
        mock_request.cookies = {"access_token": "invalid-token"}
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.get_current_user(mock_request, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    async def test_get_current_user_missing_token(self, middleware, mock_request, mock_db):
        """Test user retrieval with missing token."""
        with pytest.raises(HTTPException) as exc_info:
            await middleware.get_current_user(mock_request, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    async def test_get_current_user_user_not_found(self, middleware, mock_request, mock_db):
        """Test user retrieval when user doesn't exist in database."""
        import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        # Create a valid token
        payload = {"user_id": 999, "tenant_id": 1, "roles": ["user"]}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.cookies = {"access_token": token}
        
        # Mock database query returning None
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.get_current_user(mock_request, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)

    async def test_get_current_user_missing_user_id(self, middleware, mock_request, mock_db):
        """Test user retrieval with token missing user_id."""
        import jwt
        from app.core.security import SECRET_KEY, ALGORITHM
        
        # Create a token without user_id
        payload = {"tenant_id": 1, "roles": ["user"]}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        
        mock_request.cookies = {"access_token": token}
        
        with pytest.raises(HTTPException) as exc_info:
            await middleware.get_current_user(mock_request, mock_db)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)


class TestJWTMiddlewareIntegration:
    """Integration tests for JWT middleware with auth endpoints."""

    async def test_protected_endpoint_with_valid_cookie(self, client, test_user, test_db):
        """Test accessing protected endpoint with valid cookie."""
        # Login to get cookie
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123"
        })
        assert login_response.status_code == 200
        
        # Access protected endpoint
        me_response = await client.get("/api/v1/auth/me")
        assert me_response.status_code == 200
        
        user_data = me_response.json()
        assert user_data["email"] == test_user.email
        assert user_data["username"] == test_user.username

    async def test_protected_endpoint_with_authorization_header(self, client, test_user):
        """Test accessing protected endpoint with Authorization header."""
        # Login to get token
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123"
        })
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Access protected endpoint with header
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        
        user_data = me_response.json()
        assert user_data["email"] == test_user.email

    async def test_protected_endpoint_without_auth(self, client):
        """Test accessing protected endpoint without authentication."""
        me_response = await client.get("/api/v1/auth/me")
        assert me_response.status_code == 401
        assert "Could not validate credentials" in me_response.json()["detail"]

    async def test_logout_clears_cookie(self, client, test_user):
        """Test that logout clears the authentication cookie."""
        # Login to get cookie
        login_response = await client.post("/api/v1/auth/login", json={
            "email": test_user.email,
            "password": "testpassword123"
        })
        assert login_response.status_code == 200
        
        # Verify we can access protected endpoint
        me_response = await client.get("/api/v1/auth/me")
        assert me_response.status_code == 200
        
        # Logout
        logout_response = await client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        assert logout_response.json()["message"] == "Successfully logged out"
        
        # Verify we can no longer access protected endpoint
        me_response_after_logout = await client.get("/api/v1/auth/me")
        assert me_response_after_logout.status_code == 401