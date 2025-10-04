# tools/auth.py
"""JWT authentication utilities for MCP server."""

import os
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration - must match app/auth/security.py
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode

    Returns:
        Dictionary containing the token payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> bool:
    """
    Verify that a token payload has the expected type.

    Args:
        payload: The decoded token payload
        expected_type: The expected token type ('access' or 'refresh')

    Returns:
        True if token type matches, False otherwise
    """
    return payload.get("type") == expected_type


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """
    Extract JWT token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        The extracted token if valid format, None otherwise
    """
    if not authorization:
        return None

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    return parts[1]


def validate_access_token(authorization: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Validate an access token from Authorization header.

    Args:
        authorization: Authorization header value (e.g., "Bearer <token>")

    Returns:
        Token payload if valid, None otherwise
    """
    # Extract token from header
    token = extract_bearer_token(authorization)
    if not token:
        return None

    # Decode token
    payload = decode_token(token)
    if not payload:
        return None

    # Verify it's an access token
    if not verify_token_type(payload, "access"):
        return None

    # Verify required claims exist
    if "sub" not in payload or "role" not in payload:
        return None

    return payload
