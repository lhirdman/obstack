"""JWT token handling and validation."""

import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from jose.constants import ALGORITHMS
from pydantic import ValidationError

from .models import JWTPayload, UserContext, TokenRefreshContext
from ..exceptions import AuthenticationError, AuthorizationError


class JWTHandler:
    """Handles JWT token creation, validation, and refresh operations."""
    
    def __init__(
        self,
        secret_key: Optional[str] = None,
        algorithm: str = ALGORITHMS.HS256,
        access_token_expire_minutes: int = 30,
        refresh_token_expire_days: int = 7
    ):
        """Initialize JWT handler with configuration."""
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes
        self.refresh_token_expire_days = refresh_token_expire_days
        
        if self.secret_key == "dev-secret-key-change-in-production" and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("JWT_SECRET_KEY must be set in production environment")
    
    def create_access_token(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a new access token."""
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = JWTPayload(
            sub=user_id,
            tenant_id=tenant_id,
            roles=roles,
            exp=int(expire.timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti=str(uuid.uuid4()),
            scope="access"
        )
        
        return jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
    
    def create_refresh_token(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str]
    ) -> str:
        """Create a new refresh token."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.refresh_token_expire_days)
        
        payload = JWTPayload(
            sub=user_id,
            tenant_id=tenant_id,
            roles=roles,
            exp=int(expire.timestamp()),
            iat=int(datetime.now(timezone.utc).timestamp()),
            jti=str(uuid.uuid4()),
            scope="refresh"
        )
        
        return jwt.encode(payload.model_dump(), self.secret_key, algorithm=self.algorithm)
    
    def validate_token(self, token: str) -> UserContext:
        """Validate and decode a JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jwt_payload = JWTPayload(**payload)
            
            # Check if token is expired
            if datetime.now(timezone.utc).timestamp() > jwt_payload.exp:
                raise AuthenticationError("Token has expired")
            
            return UserContext(
                user_id=jwt_payload.sub,
                tenant_id=jwt_payload.tenant_id,
                roles=jwt_payload.roles,
                token_id=jwt_payload.jti,
                expires_at=datetime.fromtimestamp(jwt_payload.exp, tz=timezone.utc)
            )
            
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except ValidationError as e:
            raise AuthenticationError(f"Invalid token payload: {str(e)}")
    
    def validate_refresh_token(self, token: str) -> TokenRefreshContext:
        """Validate a refresh token and return context for new token generation."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            jwt_payload = JWTPayload(**payload)
            
            # Check if token is expired
            if datetime.now(timezone.utc).timestamp() > jwt_payload.exp:
                raise AuthenticationError("Refresh token has expired")
            
            # Verify this is a refresh token
            if jwt_payload.scope != "refresh":
                raise AuthenticationError("Invalid token type")
            
            return TokenRefreshContext(
                user_id=jwt_payload.sub,
                tenant_id=jwt_payload.tenant_id,
                roles=jwt_payload.roles,
                refresh_token_id=jwt_payload.jti or "",
                issued_at=datetime.fromtimestamp(jwt_payload.iat, tz=timezone.utc)
            )
            
        except JWTError as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")
        except ValidationError as e:
            raise AuthenticationError(f"Invalid refresh token payload: {str(e)}")
    
    def get_token_claims(self, token: str) -> Dict[str, Any]:
        """Get token claims without validation (for debugging/logging)."""
        try:
            return jwt.get_unverified_claims(token)
        except JWTError:
            return {}
    
    def is_token_expired(self, token: str) -> bool:
        """Check if a token is expired without full validation."""
        try:
            claims = self.get_token_claims(token)
            exp = claims.get("exp")
            if exp:
                return datetime.now(timezone.utc).timestamp() > exp
            return True
        except Exception:
            return True