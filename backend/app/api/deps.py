"""API dependencies."""

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from google.auth.transport import requests
from google.oauth2 import id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()
security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Get current authenticated user from Google OAuth token.

    Args:
        credentials: HTTP authorization credentials with Bearer token
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If token is invalid or user not authorized
    """
    token = credentials.credentials

    try:
        # Verify Google ID token
        idinfo = id_token.verify_oauth2_token(
            token, requests.Request(), settings.google_client_id
        )

        # Check domain restriction (stanford.edu)
        if settings.environment == "production" and idinfo.get("hd") != "stanford.edu":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only stanford.edu accounts are allowed",
            )

        email = idinfo.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email not found in token",
            )

        # Fetch user from database
        result = await db.execute(select(User).where(User.email == email, User.is_active == True))
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User not authorized. Please contact an administrator.",
            )

        return user

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
        )


def require_role(*allowed_roles: str):
    """
    Dependency to require specific user roles.

    Args:
        *allowed_roles: Roles that are allowed (admin, senior_editor, member_editor)

    Returns:
        Dependency function that checks user role
    """

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}",
            )
        return user

    return role_checker


# Common dependency annotations
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_role("admin"))]
SeniorOrAdminUser = Annotated[User, Depends(require_role("senior_editor", "admin"))]
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
