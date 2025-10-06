# app/auth/routes.py
"""API routes for authentication and user management."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from asyncpg.exceptions import UniqueViolationError

from app.auth.models import (
    User,
    UserCreate,
    UserLogin,
    Token,
    RefreshTokenRequest,
    PasswordChange,
    PasswordReset,
    EmailUpdate,
    RoleUpdate,
)
from app.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type,
)
from app.auth.database import (
    get_user,
    create_user,
    list_users,
    update_user_password,
    update_user_role,
    delete_user,
    disable_user,
    enable_user,
    update_user_email,
)
from app.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Authenticate user and return access and refresh tokens.

    Args:
        credentials: Username and password

    Returns:
        Token object with access_token and refresh_token

    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user from database
    user = await get_user(credentials.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is disabled
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create tokens
    token_data = {"sub": user.username, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(request: RefreshTokenRequest):
    """
    Refresh access token using a valid refresh token.

    Args:
        request: Refresh token request

    Returns:
        New Token object with fresh access_token and refresh_token

    Raises:
        HTTPException: If refresh token is invalid or expired
    """
    # Decode refresh token
    payload = decode_token(request.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify it's a refresh token
    if not verify_token_type(payload, "refresh"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract username
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    user = await get_user(username)
    if user is None or user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create new tokens
    token_data = {"sub": user.username, "role": user.role}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user from token

    Returns:
        User object with current user information
    """
    return current_user


@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
):
    """
    Change password for current user.

    Args:
        password_change: Old and new password
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If old password is incorrect
    """
    # Get user with password from database
    user = await get_user(current_user.username)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify old password
    if not verify_password(password_change.old_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect old password",
        )

    # Update password
    new_hashed_password = get_password_hash(password_change.new_password)
    await update_user_password(current_user.username, new_hashed_password)

    return {"message": "Password changed successfully"}


@router.post("/change-email")
async def change_email(
    payload: EmailUpdate,
    current_user: User = Depends(get_current_user),
):
    """
    Change email for current user.
    """
    try:
        success = await update_user_email(current_user.username, payload.new_email)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use",
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": "Email changed successfully"}


# Admin-only endpoints


@router.post("/users", response_model=User)
async def create_new_user(
    user_create: UserCreate,
    current_user: User = Depends(require_admin),
):
    """
    Create a new user (admin only).

    Args:
        user_create: User creation data
        current_user: Current admin user

    Returns:
        Created User object

    Raises:
        HTTPException: If username or email already exists
    """
    try:
        hashed_password = get_password_hash(user_create.password)
        user = await create_user(
            username=user_create.username,
            email=user_create.email,
            hashed_password=hashed_password,
            full_name=user_create.full_name,
            role=user_create.role,
        )

        # Return user without password
        return User(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            disabled=user.disabled,
            created_at=user.created_at,
        )

    except UniqueViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already exists",
        )


@router.get("/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(require_admin)):
    """
    List all users (admin only).

    Args:
        current_user: Current admin user

    Returns:
        List of all users
    """
    return await list_users()


@router.put("/users/{username}/role")
async def update_user_role_endpoint(
    username: str,
    payload: RoleUpdate,
    current_user: User = Depends(require_admin),
):
    """
    Update a user's role (admin only).

    Args:
        username: Username to update
        role: New role (admin, developer, viewer)
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    role = payload.role
    if role not in ["admin", "developer", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be admin, developer, or viewer",
        )

    success = await update_user_role(username, role)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"User {username} role updated to {role}"}


@router.put("/users/{username}/password")
async def admin_reset_password(
    username: str,
    payload: PasswordReset,
    current_user: User = Depends(require_admin),
):
    """
    Reset a user's password (admin only).

    Args:
        username: Username to update
        payload: New password
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    new_hashed_password = get_password_hash(payload.new_password)
    success = await update_user_password(username, new_hashed_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"Password for {username} updated"}


@router.put("/users/{username}/email")
async def admin_update_email(
    username: str,
    payload: EmailUpdate,
    current_user: User = Depends(require_admin),
):
    """Update a user's email (admin only)."""
    try:
        success = await update_user_email(username, payload.new_email)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already in use",
        )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"Email for {username} updated"}


@router.put("/users/{username}/disable")
async def disable_user_endpoint(
    username: str,
    current_user: User = Depends(require_admin),
):
    """
    Disable a user account (admin only).

    Args:
        username: Username to disable
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    success = await disable_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"User {username} disabled"}


@router.put("/users/{username}/enable")
async def enable_user_endpoint(
    username: str,
    current_user: User = Depends(require_admin),
):
    """
    Enable a user account (admin only).

    Args:
        username: Username to enable
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found
    """
    success = await enable_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"User {username} enabled"}


@router.delete("/users/{username}")
async def delete_user_endpoint(
    username: str,
    current_user: User = Depends(require_admin),
):
    """
    Delete a user (admin only).

    Args:
        username: Username to delete
        current_user: Current admin user

    Returns:
        Success message

    Raises:
        HTTPException: If user not found or trying to delete self
    """
    # Prevent admin from deleting themselves
    if username == current_user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    success = await delete_user(username)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {"message": f"User {username} deleted"}
