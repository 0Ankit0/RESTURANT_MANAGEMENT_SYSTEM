from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.apps.iam.models.user import User
from src.apps.iam.models.role import UserRole
from src.apps.iam.models.token_tracking import TokenTracking
from src.db.session import get_session
from pydantic import ValidationError
from jose import JWTError, jwt
from src.apps.core.config import settings
from src.apps.core import security
from src.apps.core.logging import set_log_context
from src.apps.iam.schemas.token import TokenPayload

# HTTPBearer with auto_error=False so cookie fallback still works,
# but FastAPI registers the BearerAuth security scheme on all
# routes that depend on get_current_user — enabling the Swagger
# "Authorize" button and lock icons on protected endpoints.
_bearer_scheme = HTTPBearer(auto_error=False)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_session():
        yield session

async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(_bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
    ) -> User:
    # Prefer the Authorization: Bearer header (captured by HTTPBearer above),
    # fall back to the access_token cookie for browser-based clients.
    token: Optional[str] = credentials.credentials if credentials else None
    if not token:
        token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",        
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    
    if not token_data.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    
    # Check if token is tracked and active
    jti = payload.get("jti")
    if jti:
        token_result = await db.execute(
            select(TokenTracking).where(
                TokenTracking.token_jti == jti,
                TokenTracking.is_active
            )
        )
        token_tracking = token_result.scalars().first()
        
        if not token_tracking:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked or is invalid"
            )
    
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.user_roles).selectinload(UserRole.role),
        )
        .where(User.id == int(token_data.sub))
    )
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive"
        )

    request.state.current_user_id = user.id
    set_log_context(user_id=user.id)
    return user

async def get_current_active_superuser(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user
