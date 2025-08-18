"""Authentication and authorization Pydantic models."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from .common import BaseResponse

class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1)
    tenant_id: Optional[str] = None

class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str = Field(min_length=1)

class AuthTokens(BaseResponse):
    """Authentication tokens response model."""
    access_token: str
    refresh_token: str
    expires_in: int = Field(ge=1)
    token_type: str = Field(default="Bearer")

class TokenValidationRequest(BaseModel):
    """Token validation request model."""
    token: str = Field(min_length=1)

class TokenValidationResponse(BaseResponse):
    """Token validation response model."""
    valid: bool
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    roles: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None

class JWKSResponse(BaseResponse):
    """JWKS (JSON Web Key Set) response model."""
    keys: list[dict] = Field(description="Array of JWK objects")

class LogoutRequest(BaseModel):
    """Logout request model."""
    refresh_token: Optional[str] = None

class PasswordChangeRequest(BaseModel):
    """Password change request model."""
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: str = Field(pattern="^[^@]+@[^@]+\.[^@]+$")

class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation request model."""
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=8, max_length=128)

class UserRegistrationRequest(BaseModel):
    """User registration request model."""
    username: str = Field(min_length=1, max_length=50)
    email: str = Field(pattern="^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(min_length=8, max_length=128)
    tenant_id: Optional[str] = None
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)

class UserProfile(BaseResponse):
    """User profile response model."""
    id: str
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    tenant_id: str
    roles: list[str]
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True

class UpdateUserProfileRequest(BaseModel):
    """Update user profile request model."""
    first_name: Optional[str] = Field(None, max_length=50)
    last_name: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, pattern="^[^@]+@[^@]+\.[^@]+$")

class RoleAssignmentRequest(BaseModel):
    """Role assignment request model."""
    user_id: str
    role_ids: list[str] = Field(min_length=1)

class PermissionCheckRequest(BaseModel):
    """Permission check request model."""
    resource: str = Field(min_length=1)
    action: str = Field(min_length=1)
    user_id: Optional[str] = None  # If None, uses current user from token

class PermissionCheckResponse(BaseResponse):
    """Permission check response model."""
    allowed: bool
    reason: Optional[str] = None