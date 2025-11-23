"""Users API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser, CurrentUser, DatabaseSession
from app.models.user import User as UserModel
from app.schemas.common import PaginatedResponse
from app.schemas.user import User, UserCreate, UserUpdate

router = APIRouter()


@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: CurrentUser) -> User:
    """Get current user profile."""
    return User.model_validate(current_user)


@router.get("", response_model=PaginatedResponse[User])
async def list_users(
    db: DatabaseSession,
    current_user: CurrentUser,
    role: str | None = None,
    is_active: bool | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
) -> PaginatedResponse[User]:
    """List all users (with pagination and filters)."""
    # Build query
    query = select(UserModel)

    if role:
        query = query.where(UserModel.role == role)
    if is_active is not None:
        query = query.where(UserModel.is_active == is_active)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.offset((page - 1) * per_page).limit(per_page)

    # Execute query
    result = await db.execute(query)
    users = result.scalars().all()

    return PaginatedResponse(
        items=[User.model_validate(user) for user in users],
        total=total or 0,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page if total else 0,
    )


@router.post("", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: DatabaseSession,
    admin: AdminUser,
) -> User:
    """Create new user (admin only)."""
    # Check if user already exists
    result = await db.execute(select(UserModel).where(UserModel.email == user_in.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # Create user
    user = UserModel(**user_in.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return User.model_validate(user)


@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: uuid.UUID,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> User:
    """Get user by ID."""
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return User.model_validate(user)


@router.patch("/{user_id}", response_model=User)
async def update_user(
    user_id: uuid.UUID,
    user_update: UserUpdate,
    db: DatabaseSession,
    current_user: CurrentUser,
) -> User:
    """Update user (admin or self for limited fields)."""
    # Get user
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check permissions
    if user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update other users",
        )

    # Update fields
    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return User.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: DatabaseSession,
    admin: AdminUser,
) -> None:
    """Soft delete user (admin only)."""
    result = await db.execute(select(UserModel).where(UserModel.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.commit()
