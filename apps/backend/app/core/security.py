"""
Security middleware and utilities for JWT validation and authentication.
"""

import logging
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings, AuthMethod
from app.db.models import User, Tenant
from app.services.keycloak_service import keycloak_service

logger = logging.getLogger(__name__)


class JWTMiddleware:
    """Middleware for JWT token validation on protected routes."""
    
    def __init__(self):
        self.security = HTTPBearer(auto_error=False)
    
    async def validate_token(self, request: Request) -> Optional[dict]:
        """
        Validate JWT token from cookie or Authorization header.
        
        Returns:
            dict: Token payload if valid, None if invalid or missing
        """
        token = None
        
        # First try to get token from HttpOnly cookie
        token = request.cookies.get("access_token")
        
        # If no cookie, try Authorization header (for API clients)
        if not token:
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return None
        
        # Validate token based on authentication method
        if settings.auth_method == AuthMethod.KEYCLOAK:
            return keycloak_service.validate_jwt_token(token)
        else:
            # Local JWT validation
            try:
                payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
                return payload
            except JWTError:
                return None
    
    async def get_current_user(self, request: Request, db: AsyncSession) -> User:
        """
        Get current authenticated user from JWT token.
        
        Args:
            request: FastAPI request object
            db: Database session
            
        Returns:
            User: Authenticated user object
            
        Raises:
            HTTPException: If authentication fails
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        payload = await self.validate_token(request)
        if not payload:
            raise credentials_exception
        
        if settings.auth_method == AuthMethod.KEYCLOAK:
            return await self._get_keycloak_user(payload, db, credentials_exception)
        else:
            return await self._get_local_user(payload, db, credentials_exception)
    
    async def _get_local_user(self, payload: dict, db: AsyncSession, credentials_exception: HTTPException) -> User:
        """Get user for local authentication."""
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        
        return user
    
    async def _get_keycloak_user(self, payload: dict, db: AsyncSession, credentials_exception: HTTPException) -> User:
        """Get or create user for Keycloak authentication."""
        # Extract user information from Keycloak token
        user_info = keycloak_service.extract_user_info(payload)
        keycloak_roles = keycloak_service.extract_roles(payload)
        tenant_name = keycloak_service.extract_tenant_info(payload)
        
        # Map Keycloak roles to internal roles
        internal_roles = keycloak_service.map_keycloak_roles_to_internal(keycloak_roles)
        
        user_id = user_info.get("user_id")
        email = user_info.get("email")
        username = user_info.get("username")
        
        if not user_id or not email:
            logger.error("Missing required user information in Keycloak token")
            raise credentials_exception
        
        # Try to find existing user by Keycloak user ID (stored in username field for Keycloak users)
        result = await db.execute(select(User).where(User.username == f"keycloak:{user_id}"))
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user's roles and information
            user.email = email
            user.roles = internal_roles
            await db.commit()
            await db.refresh(user)
            logger.debug(f"Updated existing Keycloak user: {username}")
        else:
            # Create new user for Keycloak authentication
            # Get or create tenant
            tenant_result = await db.execute(select(Tenant).where(Tenant.name == tenant_name))
            tenant = tenant_result.scalar_one_or_none()
            
            if not tenant:
                tenant = Tenant(name=tenant_name)
                db.add(tenant)
                await db.flush()  # Get the tenant ID
                logger.info(f"Created new tenant: {tenant_name}")
            
            user = User(
                username=f"keycloak:{user_id}",  # Prefix to distinguish from local users
                email=email,
                hashed_password="",  # No password for Keycloak users
                tenant_id=tenant.id,
                roles=internal_roles
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created new Keycloak user: {username}")
        
        return user


# Global instance
jwt_middleware = JWTMiddleware()