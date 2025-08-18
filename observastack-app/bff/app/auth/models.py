"""Authentication models for JWT handling."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class JWTPayload(BaseModel):
    """JWT token payload model."""
    sub: str = Field(description="Subject (user ID)")
    tenant_id: str = Field(description="Tenant ID for multi-tenant isolation")
    roles: List[str] = Field(default_factory=list, description="User roles")
    exp: int = Field(description="Expiration timestamp")
    iat: int = Field(description="Issued at timestamp")
    jti: Optional[str] = Field(None, description="JWT ID for token tracking")
    scope: Optional[str] = Field(None, description="Token scope")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: int(v.timestamp())
        }


class UserContext(BaseModel):
    """User context extracted from JWT token."""
    user_id: str
    tenant_id: str
    roles: List[str] = Field(default_factory=list)
    token_id: Optional[str] = None
    expires_at: datetime
    
    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles
    
    def has_any_role(self, roles: List[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)
    
    def is_admin(self) -> bool:
        """Check if user has admin role."""
        return self.has_role("admin")


class TokenRefreshContext(BaseModel):
    """Context for token refresh operations."""
    user_id: str
    tenant_id: str
    roles: List[str]
    refresh_token_id: str
    issued_at: datetime