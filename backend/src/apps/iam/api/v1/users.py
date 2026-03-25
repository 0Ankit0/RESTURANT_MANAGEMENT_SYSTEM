"""
User management endpoints with caching and pagination
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, func, or_, col
from typing import Optional
from src.apps.iam.api.deps import get_current_user, get_current_active_superuser, get_db
from src.apps.iam.models.user import User
from src.apps.iam.models.role import UserRole
from src.apps.iam.schemas.user import UserResponse, UserUpdate
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.core.schemas import PaginatedResponse
from src.apps.core.cache import RedisCache
from src.apps.core.config import settings
from src.apps.core.storage import delete_media, save_media_bytes
from src.apps.analytics.dependencies import get_analytics
from src.apps.analytics.service import AnalyticsService
from src.apps.analytics.events import UserEvents
from src.apps.iam.models.user import UserProfile
from src.apps.observability.service import record_admin_privilege_change

router = APIRouter(prefix="/users")


def _serialize_user_response(user: User) -> dict[str, object]:
    response = UserResponse.model_validate(user)
    return {
        "id": response.id,
        "username": response.username,
        "email": str(response.email),
        "is_active": response.is_active,
        "is_superuser": response.is_superuser,
        "is_confirmed": response.is_confirmed,
        "otp_enabled": response.otp_enabled,
        "otp_verified": response.otp_verified,
        "first_name": response.first_name,
        "last_name": response.last_name,
        "phone": response.phone,
        "image_url": response.image_url,
        "bio": response.bio,
        "roles": response.roles,
    }


async def _invalidate_user_cache(user_id: int) -> None:
    await RedisCache.delete(f"user:profile:{user_id}")
    await RedisCache.clear_pattern(f"user:{user_id}:*")
    await RedisCache.clear_pattern(f"casbin:roles:{user_id}:*")
    await RedisCache.clear_pattern(f"casbin:permissions:{user_id}:*")
    await RedisCache.clear_pattern(f"permission:check:{user_id}:*")


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of items to return"),
    search: Optional[str] = Query(default=None, description="Search by email or name"),
    is_active: Optional[bool] = Query(default=None, description="Filter by active status"),
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users with pagination and optional filters (admin only)
    """
    # Create cache key including filters
    cache_key = f"users:list:{skip}:{limit}:{search}:{is_active}"
    
    # Try cache
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached
    
    
    # Build query
    query = select(User).options(
        selectinload(User.profile),
        selectinload(User.user_roles).selectinload(UserRole.role),
    )
    count_query = select(func.count(col(User.id)))
    
    # Apply filters
    if search:
        search_filter = or_(
            col(User.email).ilike(f"%{search}%"),
            col(User.username).ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)
    
    # Get total count
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()
    
    # Get paginated data
    query = query.offset(skip).limit(limit).order_by(col(User.id))
    result = await db.execute(query)
    items = result.scalars().all()
    items_response = [UserResponse.model_validate(user) for user in items]
    
    # Create response
    response = PaginatedResponse[UserResponse].create(
        items=items_response,
        total=total,
        skip=skip,
        limit=limit
    )
    
    # Cache for 2 minutes (users data changes frequently)
    await RedisCache.set(
        cache_key,
        {
            "items": [_serialize_user_response(user) for user in items],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
        ttl=120,
    )
    
    return response


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    """
    cache_key = f"user:profile:{current_user.id}"
    
    # Try cache
    cached = await RedisCache.get(cache_key)
    if cached:
        return UserResponse.model_validate(cached)
    
    cache_data = _serialize_user_response(current_user)
    # Cache for 5 minutes
    await RedisCache.set(cache_key, cache_data, ttl=300)
    
    return current_user


@router.post("/me/avatar", response_model=UserResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
):
    """Upload or replace the current user's avatar image."""
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    MAX_SIZE = settings.MAX_AVATAR_SIZE_MB * 1024 * 1024

    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type: {file.content_type}. Allowed: jpeg, png, gif, webp",
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.MAX_AVATAR_SIZE_MB} MB",
        )

    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename and "." in file.filename else "jpg"
    filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{ext}"
    relative_path = f"avatars/{filename}"

    if current_user.profile and current_user.profile.image_url:
        delete_media(current_user.profile.image_url)

    image_url = save_media_bytes(
        relative_path,
        contents,
        content_type=file.content_type,
    )

    if current_user.profile:
        current_user.profile.image_url = image_url
        db.add(current_user.profile)
    else:
        from src.apps.iam.models.user import UserProfile
        profile = UserProfile(user_id=current_user.id, image_url=image_url)
        db.add(profile)
        current_user.profile = profile

    await db.commit()
    await db.refresh(current_user)
    if current_user.profile:
        await db.refresh(current_user.profile)

    await _invalidate_user_cache(current_user.id)

    await analytics.capture(
        str(current_user.id),
        UserEvents.AVATAR_UPLOADED,
        {"file_type": file.content_type, "file_size_bytes": len(contents)},
    )

    return current_user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (admin only)
    """
    uid = decode_id_or_404(user_id)
    cache_key = f"user:profile:{uid}"
    
    # Try cache
    cached = await RedisCache.get(cache_key)
    if cached:
        return UserResponse.model_validate(cached)
    
    result = await db.execute(
        select(User).options(
            selectinload(User.profile),
            selectinload(User.user_roles).selectinload(UserRole.role),
        ).where(User.id == uid)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    cache_data = _serialize_user_response(user)
    # Cache for 5 minutes
    await RedisCache.set(cache_key, cache_data, ttl=300)
    
    return user


@router.patch("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
):
    """
    Update current user's profile
    """
    # Update user fields
    if user_update.email is not None:
        # Check if email is already taken
        result = await db.execute(
            select(User).where(
                User.email == user_update.email,
                User.id != current_user.id
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        current_user.email = user_update.email
        current_user.is_confirmed = False  # Re-verify email

    # Update profile fields
    if current_user.profile:
        if user_update.first_name is not None:
            current_user.profile.first_name = user_update.first_name
        if user_update.last_name is not None:
            current_user.profile.last_name = user_update.last_name
        if user_update.phone is not None:
            current_user.profile.phone = user_update.phone
    
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    if current_user.profile:
        await db.refresh(current_user.profile)
    
    # Invalidate caches
    await _invalidate_user_cache(current_user.id)
    await RedisCache.clear_pattern("users:list:*")

    updated_fields = user_update.model_dump(exclude_unset=True)
    await analytics.capture(
        str(current_user.id),
        UserEvents.PROFILE_UPDATED,
        {"updated_fields": list(updated_fields.keys())},
    )

    return current_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user by ID (admin only)
    """
    uid = decode_id_or_404(user_id)
    result = await db.execute(
        select(User).options(
            selectinload(User.profile),
            selectinload(User.user_roles).selectinload(UserRole.role),
        ).where(User.id == uid)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_update.email is not None:
        # Check if email is already taken
        result = await db.execute(
            select(User).where(
                User.email == user_update.email,
                User.id != uid
            )
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        user.email = user_update.email
    privilege_changes: dict[str, object] = {}
    if user_update.is_active is not None:
        if user.is_active != user_update.is_active:
            privilege_changes["is_active"] = {"from": user.is_active, "to": user_update.is_active}
        user.is_active = user_update.is_active
    if user_update.is_superuser is not None:
        if user.is_superuser != user_update.is_superuser:
            privilege_changes["is_superuser"] = {"from": user.is_superuser, "to": user_update.is_superuser}
        user.is_superuser = user_update.is_superuser

    profile_result = await db.execute(select(UserProfile).where(UserProfile.user_id == uid))
    profile = profile_result.scalars().first()

    # Update profile fields
    if profile:
        if user_update.first_name is not None:
            profile.first_name = user_update.first_name
        if user_update.last_name is not None:
            profile.last_name = user_update.last_name
        if user_update.phone is not None:
            profile.phone = user_update.phone
        db.add(profile)
    elif any(
        value is not None
        for value in [user_update.first_name, user_update.last_name, user_update.phone]
    ):
        profile = UserProfile(
            user_id=user.id,
            first_name=user_update.first_name,
            last_name=user_update.last_name,
            phone=user_update.phone,
        )
        db.add(profile)

    db.add(user)
    await db.commit()
    if profile:
        await db.refresh(profile)
        user.profile = profile
    result = await db.execute(
        select(User).options(
            selectinload(User.profile),
            selectinload(User.user_roles).selectinload(UserRole.role),
        ).where(User.id == uid)
    )
    user = result.scalars().first()
    assert user is not None
    
    # Invalidate caches
    await _invalidate_user_cache(uid)
    await RedisCache.clear_pattern("users:list:*")
    if privilege_changes:
        await record_admin_privilege_change(
            db,
            actor_user_id=current_user.id,
            subject_user_id=uid,
            changes=privilege_changes,
            request=request,
        )
        await db.commit()

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user by ID (admin only)
    """
    uid = decode_id_or_404(user_id)

    if uid == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await db.delete(user)
    await db.commit()
    
    # Invalidate caches
    await _invalidate_user_cache(uid)
    await RedisCache.clear_pattern("users:list:*")
    
    return {"message": "User deleted successfully"}
