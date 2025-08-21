"""
Security middleware and utilities for JWT validation and authentication.
"""

import os
from typing import Optional
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import User

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    if os.getenv("ENVIRONMENT") == "development":
        SECRET_KEY = "dev-secret-key-not-for-production-use"
        print("WARNING: Using development JWT secret key. Set JWT_SECRET_KEY environment variable for production.")
    else:
        raise ValueError("JWT_SECRET_KEY environment variable is required in non-development environments")

ALGORITHM = "HS256"


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
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
        
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise credentials_exception
        
        return user


# Global instance
jwt_middleware = JWTMiddleware()