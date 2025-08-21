import os
import bcrypt
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, jwt

from app.db.session import get_db
from app.db.models import User, Tenant
from app.core.security import jwt_middleware

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "development":
        # Use a development-only default key with clear warning
        SECRET_KEY = "dev-secret-key-not-for-production-use"
        print("WARNING: Using development JWT secret key. Set JWT_SECRET_KEY environment variable for production.")
    else:
        raise ValueError("JWT_SECRET_KEY environment variable is required in non-development environments")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# Pydantic models for request/response
class UserRegister(BaseModel):
    """User registration request model."""
    username: str = Field(..., description="Unique username for the user")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, description="Password (minimum 8 characters)")
    tenant_name: Optional[str] = Field("default", description="Organization name")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "john_doe",
                "email": "john@example.com",
                "password": "securepassword123",
                "tenant_name": "my-company"
            }
        }
    }


class UserLogin(BaseModel):
    """User login request model."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john@example.com",
                "password": "securepassword123"
            }
        }
    }


class Token(BaseModel):
    """JWT token response model."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type (always 'bearer')")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class UserResponse(BaseModel):
    """User information response model."""
    id: int = Field(..., description="Unique user identifier")
    username: str = Field(..., description="User's username")
    email: str = Field(..., description="User's email address")
    tenant_id: int = Field(..., description="User's tenant/organization ID")
    roles: Optional[list] = Field(None, description="User's assigned roles")
    created_at: datetime = Field(..., description="Account creation timestamp")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "tenant_id": 1,
                "roles": ["user"],
                "created_at": "2023-01-01T12:00:00Z"
            }
        }
    }


# Password hashing utilities
def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


# JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current user from JWT token (from cookie or Authorization header)."""
    return await jwt_middleware.get_current_user(request, db)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account.
    
    Creates a new user with the provided credentials and assigns them to a tenant.
    If the specified tenant doesn't exist, it will be created automatically.
    
    - **username**: Unique username for the user
    - **email**: Valid email address (must be unique)
    - **password**: Password (minimum 8 characters, will be securely hashed)
    - **tenant_name**: Organization name (optional, defaults to 'default')
    
    Returns the created user information including assigned tenant and roles.
    """
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Get or create tenant
    tenant_result = await db.execute(select(Tenant).where(Tenant.name == user_data.tenant_name))
    tenant = tenant_result.scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(name=user_data.tenant_name)
        db.add(tenant)
        await db.flush()  # Get the tenant ID
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        tenant_id=tenant.id,
        roles=["user"]
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        tenant_id=user.tenant_id,
        roles=user.roles if user.roles else [],
        created_at=user.created_at
    )


@router.post("/login", response_model=Token)
async def login_user(user_data: UserLogin, response: Response, db: AsyncSession = Depends(get_db)):
    """
    Authenticate user and return access token.
    
    Validates user credentials and returns a JWT access token that can be used
    for authenticated requests. The token contains user_id, tenant_id, and roles.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns a JWT access token with 30-minute expiration and token type.
    """
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "roles": user.roles if user.roles else []
        },
        expires_delta=access_token_expires
    )
    
    # Set HttpOnly cookie for web clients
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        httponly=True,
        secure=True,  # Use HTTPS in production
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Returns detailed information about the currently authenticated user
    including their profile, tenant association, and assigned roles.
    
    Requires a valid JWT token in the Authorization header.
    """
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        tenant_id=current_user.tenant_id,
        roles=current_user.roles if current_user.roles else [],
        created_at=current_user.created_at
    )


@router.post("/logout")
async def logout_user(response: Response):
    """
    Logout user by clearing the access token cookie.
    
    Clears the HttpOnly cookie containing the JWT access token,
    effectively logging out the user from web clients.
    
    Returns a success message confirming logout.
    """
    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=True,
        samesite="lax"
    )
    
    return {"message": "Successfully logged out"}
