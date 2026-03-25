from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Body
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from src.apps.core.config import settings
from src.apps.core import security
from src.apps.core.security import TokenType
from src.apps.core.cache import RedisCache
from src.apps.core.cookies import auth_cookie_options
from src.apps.iam.api.deps import get_db
from src.apps.iam.models.user import User
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.iam.schemas.token import Token
from src.apps.iam.utils.ip_access import revoke_tokens_for_ip, get_client_ip
from src.apps.observability.service import record_token_event

router = APIRouter()


@router.post("/refresh/")
async def refresh_token(
    response: Response,
    request: Request,
    set_cookie: bool,
    refresh_token: str | None = Body(None, embed=True),
    db: AsyncSession = Depends(get_db),
) -> Token | dict[str, str]:
    """
    Refresh access token using a valid refresh token
    """
    try:
        if not refresh_token:
            refresh_token = request.cookies.get(settings.REFRESH_TOKEN_COOKIE)
        
        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token missing"
            )
        
        user = security.verify_token(refresh_token, token_type=TokenType.REFRESH)
        user_id = user.get("sub") if user else None
        if not user or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Extract user_id from payload
        user_id = int(user_id)
        
        # Check if refresh token is tracked and active
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        refresh_jti = refresh_payload.get("jti")
        token_tracking = None

        if refresh_jti:
            token_result = await db.execute(
                select(TokenTracking).where(
                    TokenTracking.token_jti == refresh_jti,
                    TokenTracking.is_active
                )
            )
            token_tracking = token_result.scalars().first()
            
            if not token_tracking:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked or is invalid"
                )
        
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalars().first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Revoke old refresh token
        if refresh_jti and token_tracking:
            token_tracking.is_active = False
            token_tracking.revoked_at = datetime.now(timezone.utc)
            token_tracking.revoke_reason = "Token refreshed"
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        new_refresh_token = security.create_refresh_token(user.id)
        
        # Track new tokens
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        new_refresh_payload = jwt.decode(new_refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])

        # Revoke any remaining active tokens for this user+IP before issuing new ones
        await revoke_tokens_for_ip(db, user.id, ip_address)

        access_token_tracking = TokenTracking(
            user_id=user.id,
            token_jti=access_payload["jti"],
            token_type=TokenType.ACCESS,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        )
        db.add(access_token_tracking)
        
        refresh_token_tracking = TokenTracking(
            user_id=user.id,
            token_jti=new_refresh_payload["jti"],
            token_type=TokenType.REFRESH,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.fromtimestamp(new_refresh_payload["exp"], tz=timezone.utc)
        )
        db.add(refresh_token_tracking)
        await db.commit()
        await record_token_event(
            db,
            user_id=user.id,
            ip_address=ip_address,
            action="issued",
            request=request,
            metadata={"issued_tokens": 2, "auth_method": "refresh"},
        )
        await record_token_event(
            db,
            user_id=user.id,
            ip_address=ip_address,
            action="revoked",
            request=request,
            metadata={"reason": "refresh_rotation"},
        )
        await db.commit()

        # Old tokens revoked, new tokens saved — invalidate cached token list
        await RedisCache.clear_pattern(f"tokens:active:{user_id}:*")

        if set_cookie:
            response.set_cookie(
                key=settings.ACCESS_TOKEN_COOKIE,
                value=access_token,
                **auth_cookie_options(max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            )
            response.set_cookie(
                key=settings.REFRESH_TOKEN_COOKIE,
                value=new_refresh_token,
                **auth_cookie_options(
                    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
                ),
            )
            return {"message": "Token refreshed successfully"}
        
        return Token(
            access=access_token,
            refresh=new_refresh_token,
            token_type=TokenType.BEARER.value
        )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during token refresh"
        )
