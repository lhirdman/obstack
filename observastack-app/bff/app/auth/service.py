"""Authentication service for handling login, logout, and token management."""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from redis import Redis
import json

from .jwt_handler import JWTHandler
from .models import UserContext, TokenRefreshContext
from ..models.auth import AuthTokens, LoginRequest, RefreshTokenRequest
from ..exceptions import AuthenticationError, AuthorizationError

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(
        self,
        jwt_handler: Optional[JWTHandler] = None,
        redis_client: Optional[Redis] = None,
        session_prefix: str = "session:",
        blacklist_prefix: str = "blacklist:"
    ):
        """Initialize the authentication service."""
        self.jwt_handler = jwt_handler or JWTHandler()
        self.redis_client = redis_client
        self.session_prefix = session_prefix
        self.blacklist_prefix = blacklist_prefix
    
    async def authenticate_user(self, login_request: LoginRequest) -> AuthTokens:
        """
        Authenticate user and return tokens.
        
        This is a placeholder implementation. In production, this would:
        1. Validate credentials against Keycloak or another identity provider
        2. Retrieve user roles and tenant information
        3. Create and store session information
        """
        # TODO: Replace with actual Keycloak integration
        # For now, using demo authentication
        
        if login_request.username == "demo" and login_request.password == "demo":
            user_id = "demo-user-id"
            tenant_id = login_request.tenant_id or "demo-tenant"
            roles = ["user", "viewer"]
        elif login_request.username == "admin" and login_request.password == "admin":
            user_id = "admin-user-id"
            tenant_id = login_request.tenant_id or "demo-tenant"
            roles = ["admin", "user", "viewer"]
        else:
            raise AuthenticationError("Invalid username or password")
        
        # Create tokens
        access_token = self.jwt_handler.create_access_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles
        )
        
        refresh_token = self.jwt_handler.create_refresh_token(
            user_id=user_id,
            tenant_id=tenant_id,
            roles=roles
        )
        
        # Store session information if Redis is available
        if self.redis_client:
            await self._store_session(user_id, tenant_id, roles, refresh_token)
        
        logger.info(f"User {user_id} authenticated successfully for tenant {tenant_id}")
        
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.jwt_handler.access_token_expire_minutes * 60,
            token_type="Bearer"
        )
    
    async def refresh_tokens(self, refresh_request: RefreshTokenRequest) -> AuthTokens:
        """Refresh access token using refresh token."""
        try:
            # Validate refresh token
            refresh_context = self.jwt_handler.validate_refresh_token(refresh_request.refresh_token)
            
            # Check if refresh token is blacklisted
            if self.redis_client and await self._is_token_blacklisted(refresh_context.refresh_token_id):
                raise AuthenticationError("Refresh token has been revoked")
            
            # Verify session is still valid
            if self.redis_client:
                session_valid = await self._verify_session(
                    refresh_context.user_id,
                    refresh_context.refresh_token_id
                )
                if not session_valid:
                    raise AuthenticationError("Session is no longer valid")
            
            # Create new tokens
            access_token = self.jwt_handler.create_access_token(
                user_id=refresh_context.user_id,
                tenant_id=refresh_context.tenant_id,
                roles=refresh_context.roles
            )
            
            new_refresh_token = self.jwt_handler.create_refresh_token(
                user_id=refresh_context.user_id,
                tenant_id=refresh_context.tenant_id,
                roles=refresh_context.roles
            )
            
            # Update session with new refresh token
            if self.redis_client:
                await self._update_session(
                    refresh_context.user_id,
                    refresh_context.tenant_id,
                    refresh_context.roles,
                    new_refresh_token
                )
                
                # Blacklist old refresh token
                await self._blacklist_token(refresh_context.refresh_token_id)
            
            logger.info(f"Tokens refreshed for user {refresh_context.user_id}")
            
            return AuthTokens(
                access_token=access_token,
                refresh_token=new_refresh_token,
                expires_in=self.jwt_handler.access_token_expire_minutes * 60,
                token_type="Bearer"
            )
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise AuthenticationError("Token refresh failed")
    
    async def logout(self, user_context: UserContext, refresh_token: Optional[str] = None) -> None:
        """Logout user and invalidate tokens."""
        try:
            # Blacklist access token
            if user_context.token_id and self.redis_client:
                await self._blacklist_token(user_context.token_id)
            
            # Blacklist refresh token if provided
            if refresh_token and self.redis_client:
                try:
                    refresh_context = self.jwt_handler.validate_refresh_token(refresh_token)
                    await self._blacklist_token(refresh_context.refresh_token_id)
                except AuthenticationError:
                    # Refresh token might already be invalid, continue with logout
                    pass
            
            # Remove session
            if self.redis_client:
                await self._remove_session(user_context.user_id)
            
            logger.info(f"User {user_context.user_id} logged out successfully")
            
        except Exception as e:
            logger.error(f"Logout failed for user {user_context.user_id}: {str(e)}")
            # Don't raise exception for logout failures
    
    async def validate_session(self, user_context: UserContext) -> bool:
        """Validate if user session is still active."""
        if not self.redis_client:
            return True  # No session storage, assume valid
        
        try:
            session_key = f"{self.session_prefix}{user_context.user_id}"
            session_data = await self.redis_client.get(session_key)
            
            if not session_data:
                return False
            
            session = json.loads(session_data)
            return session.get("tenant_id") == user_context.tenant_id
            
        except Exception as e:
            logger.error(f"Session validation failed: {str(e)}")
            return False
    
    async def _store_session(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
        refresh_token: str
    ) -> None:
        """Store session information in Redis."""
        if not self.redis_client:
            return
        
        try:
            # Extract refresh token ID
            refresh_context = self.jwt_handler.validate_refresh_token(refresh_token)
            
            session_data = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "roles": roles,
                "refresh_token_id": refresh_context.refresh_token_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
            
            session_key = f"{self.session_prefix}{user_id}"
            await self.redis_client.setex(
                session_key,
                self.jwt_handler.refresh_token_expire_days * 24 * 3600,  # Same as refresh token
                json.dumps(session_data)
            )
            
        except Exception as e:
            logger.error(f"Failed to store session: {str(e)}")
    
    async def _update_session(
        self,
        user_id: str,
        tenant_id: str,
        roles: list[str],
        new_refresh_token: str
    ) -> None:
        """Update session with new refresh token."""
        if not self.redis_client:
            return
        
        try:
            session_key = f"{self.session_prefix}{user_id}"
            session_data = await self.redis_client.get(session_key)
            
            if session_data:
                session = json.loads(session_data)
                
                # Extract new refresh token ID
                refresh_context = self.jwt_handler.validate_refresh_token(new_refresh_token)
                
                session.update({
                    "refresh_token_id": refresh_context.refresh_token_id,
                    "last_activity": datetime.now(timezone.utc).isoformat()
                })
                
                await self.redis_client.setex(
                    session_key,
                    self.jwt_handler.refresh_token_expire_days * 24 * 3600,
                    json.dumps(session)
                )
            
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
    
    async def _remove_session(self, user_id: str) -> None:
        """Remove session from Redis."""
        if not self.redis_client:
            return
        
        try:
            session_key = f"{self.session_prefix}{user_id}"
            await self.redis_client.delete(session_key)
        except Exception as e:
            logger.error(f"Failed to remove session: {str(e)}")
    
    async def _verify_session(self, user_id: str, refresh_token_id: str) -> bool:
        """Verify session is valid and matches refresh token."""
        if not self.redis_client:
            return True
        
        try:
            session_key = f"{self.session_prefix}{user_id}"
            session_data = await self.redis_client.get(session_key)
            
            if not session_data:
                return False
            
            session = json.loads(session_data)
            return session.get("refresh_token_id") == refresh_token_id
            
        except Exception as e:
            logger.error(f"Session verification failed: {str(e)}")
            return False
    
    async def _blacklist_token(self, token_id: str) -> None:
        """Add token to blacklist."""
        if not self.redis_client:
            return
        
        try:
            blacklist_key = f"{self.blacklist_prefix}{token_id}"
            # Set expiration to match longest token lifetime
            expire_seconds = max(
                self.jwt_handler.access_token_expire_minutes * 60,
                self.jwt_handler.refresh_token_expire_days * 24 * 3600
            )
            await self.redis_client.setex(blacklist_key, expire_seconds, "1")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
    
    async def _is_token_blacklisted(self, token_id: str) -> bool:
        """Check if token is blacklisted."""
        if not self.redis_client:
            return False
        
        try:
            blacklist_key = f"{self.blacklist_prefix}{token_id}"
            return await self.redis_client.exists(blacklist_key)
        except Exception as e:
            logger.error(f"Blacklist check failed: {str(e)}")
            return False