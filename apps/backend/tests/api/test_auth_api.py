import pytest
from httpx import AsyncClient
import os
import uuid
import asyncio
from sqlalchemy import text
from tests.conftest import TestingSessionLocal

# Define the base URL for the backend service
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

@pytest.mark.asyncio
async def test_database_tables_exist():
    """
    Verify that the required database tables exist before running API tests.
    """
    db = TestingSessionLocal()
    try:
        # Check if tenants table exists
        result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'tenants'"))
        assert result.scalar() == 1, "Tenants table does not exist"
        
        # Check if users table exists
        result = db.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'users'"))
        assert result.scalar() == 1, "Users table does not exist"
        
    finally:
        db.close()

@pytest.mark.asyncio
async def test_health_check():
    """
    Tests if the backend service is running and accessible.
    """
    async with AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_user_registration_success():
    """
    Test successful user registration.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        
        register_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "testpassword123"
            }
        )
        assert register_response.status_code == 201
        data = register_response.json()
        assert "id" in data
        assert data["username"] == unique_username
        assert data["email"] == unique_email
        assert "tenant_id" in data
        assert "roles" in data
        assert "created_at" in data

@pytest.mark.asyncio
async def test_user_registration_with_custom_tenant():
    """
    Test user registration with custom tenant name.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        tenant_name = f"custom_tenant_{unique_id}"
        
        register_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": "testpassword123",
                "tenant_name": tenant_name
            }
        )
        assert register_response.status_code == 201
        data = register_response.json()
        assert data["username"] == unique_username
        assert data["email"] == unique_email

@pytest.mark.asyncio
async def test_user_registration_duplicate_email():
    """
    Test registration with duplicate email address.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_email = f"testuser_{unique_id}@example.com"
        
        # First registration
        await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": f"user1_{unique_id}",
                "email": unique_email,
                "password": "testpassword123"
            }
        )
        
        # Second registration with same email
        duplicate_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": f"user2_{unique_id}",
                "email": unique_email,
                "password": "testpassword123"
            }
        )
        assert duplicate_response.status_code == 400
        assert "Email already registered" in duplicate_response.json()["detail"]

@pytest.mark.asyncio
async def test_user_registration_validation_errors():
    """
    Test registration with invalid data.
    """
    async with AsyncClient() as client:
        # Test missing fields
        response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={}
        )
        assert response.status_code == 422
        
        # Test invalid email
        response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "invalid-email",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 422
        
        # Test short password
        response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "short"
            }
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_user_login_success():
    """
    Test successful user login.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        password = "testpassword123"
        
        # Register user first
        await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": password
            }
        )
        
        # Login
        login_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
        assert login_response.status_code == 200
        data = login_response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_user_login_invalid_credentials():
    """
    Test login with invalid credentials.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_email = f"testuser_{unique_id}@example.com"
        
        # Register user first
        await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": f"testuser_{unique_id}",
                "email": unique_email,
                "password": "correctpassword"
            }
        )
        
        # Test wrong password
        login_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": unique_email, "password": "wrongpassword"}
        )
        assert login_response.status_code == 401
        assert "Incorrect email or password" in login_response.json()["detail"]
        
        # Test non-existent email
        login_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "anypassword"}
        )
        assert login_response.status_code == 401
        assert "Incorrect email or password" in login_response.json()["detail"]

@pytest.mark.asyncio
async def test_user_login_validation_errors():
    """
    Test login with invalid request data.
    """
    async with AsyncClient() as client:
        # Test missing fields
        response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={}
        )
        assert response.status_code == 422
        
        # Test missing password
        response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": "test@example.com"}
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_jwt_token_structure():
    """
    Test that JWT tokens contain expected claims.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        password = "testpassword123"
        
        # Register and login
        await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": password
            }
        )
        
        login_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
        
        token = login_response.json()["access_token"]
        
        # Decode token with proper signature verification
        import os
        from jose import jwt
        
        # Try multiple possible secret keys that the backend service might be using
        possible_keys = [
            os.getenv("JWT_SECRET_KEY"),  # Environment variable
            "testsecret",  # Test environment default
            "dev-secret-key-not-for-production-use",  # Development fallback
        ]
        
        # Filter out None values
        possible_keys = [key for key in possible_keys if key is not None]
        
        decoded = None
        last_error = None
        
        for secret_key in possible_keys:
            try:
                decoded = jwt.decode(token, secret_key, algorithms=["HS256"])
                break  # Success, stop trying
            except jwt.JWTError as e:
                last_error = e
                continue  # Try next key
        
        if decoded is None:
            raise AssertionError(f"JWT signature verification failed with all possible keys. Last error: {last_error}")
        
        assert "user_id" in decoded
        assert "tenant_id" in decoded
        assert "roles" in decoded
        assert "exp" in decoded

@pytest.mark.asyncio
async def test_get_current_user():
    """
    Test the /me endpoint to get current user info.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        password = "testpassword123"
        
        # Register and login
        register_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": password
            }
        )
        
        login_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
        
        token = login_response.json()["access_token"]
        
        # Get current user info
        me_response = await client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert me_response.status_code == 200
        data = me_response.json()
        assert data["username"] == unique_username
        assert data["email"] == unique_email
        assert "tenant_id" in data
        assert "roles" in data

@pytest.mark.asyncio
async def test_protected_endpoint_without_token():
    """
    Test accessing protected endpoint without authentication.
    """
    async with AsyncClient() as client:
        response = await client.get(f"{BACKEND_URL}/api/v1/auth/me")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token():
    """
    Test accessing protected endpoint with invalid token.
    """
    async with AsyncClient() as client:
        response = await client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_password_hashing_security():
    """
    Test that passwords are properly hashed and not stored in plain text.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        password = "testpassword123"
        
        # Register user
        await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": password
            }
        )
        
        # Check database directly to ensure password is hashed
        db = TestingSessionLocal()
        try:
            result = db.execute(text("SELECT hashed_password FROM users WHERE email = :email"), {"email": unique_email})
            hashed_password = result.scalar()
            
            # Password should be hashed (bcrypt hash starts with $2b$)
            assert hashed_password.startswith("$2b$")
            assert hashed_password != password
            assert len(hashed_password) == 60  # bcrypt hash length
        finally:
            db.close()

@pytest.mark.asyncio
async def test_tenant_creation_on_registration():
    """
    Test that tenants are created automatically during registration.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        tenant_name = f"test_tenant_{unique_id}"
        
        # Register user with custom tenant
        await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": f"testuser_{unique_id}",
                "email": f"testuser_{unique_id}@example.com",
                "password": "testpassword123",
                "tenant_name": tenant_name
            }
        )
        
        # Check that tenant was created
        db = TestingSessionLocal()
        try:
            result = db.execute(text("SELECT COUNT(*) FROM tenants WHERE name = :name"), {"name": tenant_name})
            count = result.scalar()
            assert count == 1
        finally:
            db.close()

@pytest.mark.asyncio
async def test_user_roles_assignment():
    """
    Test that users are assigned default roles on registration.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_email = f"testuser_{unique_id}@example.com"
        
        # Register user
        register_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": f"testuser_{unique_id}",
                "email": unique_email,
                "password": "testpassword123"
            }
        )
        
        data = register_response.json()
        assert "roles" in data
        assert isinstance(data["roles"], list)
        assert "user" in data["roles"]

@pytest.mark.asyncio
async def test_full_authentication_flow():
    """
    Test complete authentication flow from registration to accessing protected resources.
    """
    async with AsyncClient() as client:
        unique_id = uuid.uuid4()
        unique_username = f"testuser_{unique_id}"
        unique_email = f"testuser_{unique_id}@example.com"
        password = "testpassword123"
        
        # 1. Register user
        register_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/register",
            json={
                "username": unique_username,
                "email": unique_email,
                "password": password
            }
        )
        assert register_response.status_code == 201
        
        # 2. Login to get token
        login_response = await client.post(
            f"{BACKEND_URL}/api/v1/auth/login",
            json={"email": unique_email, "password": password}
        )
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Access protected endpoint
        me_response = await client.get(
            f"{BACKEND_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        
        # 4. Verify user data consistency
        user_data = me_response.json()
        register_data = register_response.json()
        
        assert user_data["id"] == register_data["id"]
        assert user_data["username"] == register_data["username"]
        assert user_data["email"] == register_data["email"]
        assert user_data["tenant_id"] == register_data["tenant_id"]
