# app/auth/database.py
"""Database management for user authentication using PostgreSQL."""

import os
import asyncpg
from typing import Optional, List
import logging

from app.auth.models import UserInDB, User
from app.auth.security import get_password_hash

logger = logging.getLogger(__name__)

# PostgreSQL connection configuration
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
DB_USER = os.getenv("POSTGRES_USER", "argus")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "argus123")
DB_NAME = os.getenv("POSTGRES_DB", "argus_auth")

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    """
    Get or create PostgreSQL connection pool.

    Returns:
        asyncpg.Pool: Connection pool
    """
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            min_size=2,
            max_size=10,
        )
        logger.info(f"PostgreSQL connection pool created: {DB_HOST}:{DB_PORT}/{DB_NAME}")
    return _pool


async def close_pool():
    """Close PostgreSQL connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL connection pool closed")


async def init_db():
    """
    Initialize the PostgreSQL database and create tables if they don't exist.
    Also creates a default admin user if no users exist.
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        # Create users table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                disabled BOOLEAN NOT NULL DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create index on email
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)
        """)

        logger.info("Database tables initialized")

        # Check if any users exist
        user_count = await conn.fetchval("SELECT COUNT(*) FROM users")

        # Create default admin user if no users exist
        if user_count == 0:
            default_admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
            logger.warning(
                "No users found in database. Creating default admin user. "
                "Please change the password immediately!"
            )

            await conn.execute(
                """
                INSERT INTO users (username, email, full_name, hashed_password, role)
                VALUES ($1, $2, $3, $4, $5)
                """,
                "admin",
                "admin@example.com",
                "Default Administrator",
                get_password_hash(default_admin_password),
                "admin",
            )
            logger.info("Default admin user created: username=admin, password=admin123")


async def get_user(username: str) -> Optional[UserInDB]:
    """
    Retrieve a user by username.

    Args:
        username: The username to search for

    Returns:
        UserInDB object if found, None otherwise
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE username = $1",
            username
        )

        if row is None:
            return None

        return UserInDB(
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            hashed_password=row["hashed_password"],
            role=row["role"],
            disabled=row["disabled"],
        )


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """
    Retrieve a user by email.

    Args:
        email: The email to search for

    Returns:
        UserInDB object if found, None otherwise
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM users WHERE email = $1",
            email
        )

        if row is None:
            return None

        return UserInDB(
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            hashed_password=row["hashed_password"],
            role=row["role"],
            disabled=row["disabled"],
        )


async def create_user(
    username: str,
    email: str,
    hashed_password: str,
    full_name: Optional[str] = None,
    role: str = "viewer",
) -> UserInDB:
    """
    Create a new user in the database.

    Args:
        username: Unique username
        email: User's email address
        hashed_password: Pre-hashed password
        full_name: Optional full name
        role: User role (admin, developer, viewer)

    Returns:
        The created UserInDB object

    Raises:
        asyncpg.UniqueViolationError: If username or email already exists
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (username, email, full_name, hashed_password, role)
            VALUES ($1, $2, $3, $4, $5)
            """,
            username, email, full_name, hashed_password, role,
        )

    return UserInDB(
        username=username,
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        role=role,
        disabled=False,
    )


async def update_user_password(username: str, hashed_password: str) -> bool:
    """
    Update a user's password.

    Args:
        username: The username to update
        hashed_password: New hashed password

    Returns:
        True if successful, False if user not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE users
            SET hashed_password = $1, updated_at = CURRENT_TIMESTAMP
            WHERE username = $2
            """,
            hashed_password, username,
        )
        # result format: "UPDATE N" where N is number of rows affected
        return result.endswith("1")


async def list_users() -> List[User]:
    """
    List all users (without passwords).

    Returns:
        List of User objects
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM users ORDER BY username")

        return [
            User(
                username=row["username"],
                email=row["email"],
                full_name=row["full_name"],
                role=row["role"],
                disabled=row["disabled"],
            )
            for row in rows
        ]


async def delete_user(username: str) -> bool:
    """
    Delete a user from the database.

    Args:
        username: The username to delete

    Returns:
        True if successful, False if user not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM users WHERE username = $1",
            username
        )
        return result.endswith("1")


async def update_user_role(username: str, role: str) -> bool:
    """
    Update a user's role.

    Args:
        username: The username to update
        role: New role (admin, developer, viewer)

    Returns:
        True if successful, False if user not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE users
            SET role = $1, updated_at = CURRENT_TIMESTAMP
            WHERE username = $2
            """,
            role, username,
        )
        return result.endswith("1")


async def disable_user(username: str) -> bool:
    """
    Disable a user account.

    Args:
        username: The username to disable

    Returns:
        True if successful, False if user not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE users
            SET disabled = TRUE, updated_at = CURRENT_TIMESTAMP
            WHERE username = $1
            """,
            username,
        )
        return result.endswith("1")


async def enable_user(username: str) -> bool:
    """
    Enable a user account.

    Args:
        username: The username to enable

    Returns:
        True if successful, False if user not found
    """
    pool = await get_pool()

    async with pool.acquire() as conn:
        result = await conn.execute(
            """
            UPDATE users
            SET disabled = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE username = $1
            """,
            username,
        )
        return result.endswith("1")
