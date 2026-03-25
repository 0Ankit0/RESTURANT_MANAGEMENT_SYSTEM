from datetime import timedelta, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.apps.core.config import settings
from src.apps.core import security
from src.apps.core.security import TokenType
from src.apps.core.cookies import auth_cookie_options
from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.models.user import User, UserProfile
from src.apps.iam.models.token_tracking import TokenTracking
from src.apps.iam.schemas.token import Token
from src.apps.iam.schemas.user import UserCreate
from src.apps.core.cache import RedisCache

from src.apps.iam.utils.ip_access import revoke_tokens_for_ip, get_client_ip
from src.apps.analytics.dependencies import get_analytics
from src.apps.analytics.service import AnalyticsService
from src.apps.analytics.events import AuthEvents
from src.apps.observability.service import record_token_event

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup/")
@limiter.limit(lambda: settings.RATE_LIMIT_SIGNUP)
async def signup(
    request: Request,
    response: Response,
    set_cookie: bool,
    login_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> Token | dict[str, str]:
    """
    Create a new user account
    """
    ip_address = get_client_ip(request)
    
    try:
        result = await db.execute(
            select(User).where(User.username == login_data.username)
        )
        user = result.scalars().first()

        if user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        hashed_password = security.get_password_hash(login_data.password)
        new_user = User(
           username=login_data.username,
           email=login_data.email,
            hashed_password=hashed_password,
            profile=None
        )
        user_profile = UserProfile(
            first_name=login_data.first_name or "",
            last_name=login_data.last_name or "",
            phone=login_data.phone or "",
            user=new_user
        )
        
        db.add(new_user)
        db.add(user_profile)
        await db.commit()
        
        # Invalidate users list cache
        await RedisCache.clear_pattern("users:list:*")
        
        from src.apps.iam.services.email import EmailService
        await EmailService.send_welcome_email(new_user)
        
        user_agent = request.headers.get("user-agent", "unknown")
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            new_user.id, expires_delta=access_token_expires
        )
        
        refresh_token = security.create_refresh_token(new_user.id)
        
        # Decode tokens to get JTI
        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])

        # Revoke any existing active tokens for this user+IP before issuing new ones
        await revoke_tokens_for_ip(db, new_user.id, ip_address)

        # Track access token
        access_token_tracking = TokenTracking(
            user_id=new_user.id,
            token_jti=access_payload["jti"],
            token_type=TokenType.ACCESS,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)
        )
        db.add(access_token_tracking)
        
        # Track refresh token
        refresh_token_tracking = TokenTracking(
            user_id=new_user.id,
            token_jti=refresh_payload["jti"],
            token_type=TokenType.REFRESH,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)
        )
        db.add(refresh_token_tracking)
        await db.commit()
        await record_token_event(
            db,
            user_id=new_user.id,
            ip_address=ip_address,
            action="issued",
            request=request,
            metadata={"issued_tokens": 2, "auth_method": "signup"},
        )
        await db.commit()

        await analytics.identify(
            str(new_user.id),
            {"email": new_user.email, "username": new_user.username, "created_at": str(new_user.created_at)},
        )
        await analytics.capture(
            str(new_user.id),
            AuthEvents.SIGNED_UP,
            {"ip_address": ip_address, "user_agent": user_agent},
        )

        if set_cookie:
            response.set_cookie(
                key=settings.ACCESS_TOKEN_COOKIE,
                value=access_token,
                **auth_cookie_options(max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            )
            return {"message": "Account created successfully"}
        
        return Token(
            access=access_token,
            refresh=refresh_token,
            token_type=TokenType.BEARER.value
        )
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during signup"
        )


@router.post("/verify-email/")
async def verify_email(
    t: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
) -> dict[str, str]:
    """
    Verify user email with secure token sent via email
    """
    try:
        from src.apps.iam.models.used_token import UsedToken
        
        # Decrypt and verify the secure URL token
        try:
            token_data = security.verify_secure_url_token(t)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification link"
            )
        
        user_id = token_data.get("user_id")
        jwt_token = token_data.get("token")
        purpose = token_data.get("purpose")
        
        if not all([user_id, jwt_token]) or purpose != "email_verification":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token data"
            )
        
        
        # Verify the embedded JWT token
        payload = security.verify_token(str(jwt_token), token_type=TokenType.EMAIL_VERIFICATION)
        token_jti = payload.get("jti")
        
        # Verify user_id matches
        if str(payload.get("sub")) != str(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token data mismatch - possible tampering detected"
            )
        
        # Check if token has already been used
        if token_jti:
            used_check = await db.execute(
                select(UsedToken).where(UsedToken.token_jti == token_jti)
            )
            if used_check.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This verification link has already been used"
                )
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    try:
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token data"
            )
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalars().first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_confirmed = True
        
        # Mark token as used
        if token_jti:
            used_token = UsedToken(
                token_jti=token_jti,
                user_id=int(user_id),
                token_purpose="email_verification"
            )
            db.add(used_token)
        
        await db.commit()

        # Invalidate user cache
        await RedisCache.delete(f"user:profile:{user_id}")

        await analytics.capture(str(user_id), AuthEvents.EMAIL_VERIFIED)

        return {"message": "Email verified successfully"}
    except HTTPException:
        raise
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during email verification"
        )


@router.post("/resend-verification/")
async def resend_verification_email(
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    """
    Resend email verification link
    """
    try:
        if current_user.is_confirmed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already verified"
            )
        
        verification_token = security.create_email_verification_token(current_user.id)
        
        from src.apps.iam.services.email import EmailService
        await EmailService.send_verification_email(current_user, verification_token)
        
        return {"message": "Verification email sent"}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred sending verification email"
        )
