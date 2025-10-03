# app/auth/dependencies.py
"""FastAPI dependencies for authentication and authorization."""

from typing import Literal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.models import User, TokenData
from app.auth.security import decode_token, verify_token_type
from app.auth.database import get_user

# Security scheme for JWT bearer tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token from request header

    Returns:
        User object for the authenticated user

    Raises:
        HTTPException: If token is invalid, expired, or user not found
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify it's an access token
    if not verify_token_type(payload, "access"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract username
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user_db = await get_user(username)
    if user_db is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is disabled
    if user_db.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Return user without password
    return User(
        username=user_db.username,
        email=user_db.email,
        full_name=user_db.full_name,
        role=user_db.role,
        disabled=user_db.disabled,
    )


def require_role(*allowed_roles: Literal["admin", "developer", "viewer"]):
    """
    Factory function to create role-based authorization dependency.

    Args:
        *allowed_roles: One or more roles that are allowed access

    Returns:
        Dependency function that checks user role

    Example:
        @app.get("/admin-only")
        async def admin_endpoint(user: User = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}
    """

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        """
        Check if user has required role.

        Args:
            user: Current authenticated user

        Returns:
            User object if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker


# Convenience dependencies for common role checks
require_admin = require_role("admin")
require_developer = require_role("admin", "developer")
require_viewer = require_role("admin", "developer", "viewer")
