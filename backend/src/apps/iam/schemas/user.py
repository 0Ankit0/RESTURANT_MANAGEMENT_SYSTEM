from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_serializer, field_validator, model_validator, ValidationInfo
from src.apps.core.security import validate_password_strength
from ..utils.hashid import encode_id


class UserBase(BaseModel):
    username: str
    email: EmailStr
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str
    confirm_password: str

    @field_validator("password")
    def validate_password_strength(cls, value):
        validate_password_strength(value)
        return value

    @field_validator("confirm_password")
    def validate_confirm_password(cls, value, info: ValidationInfo):
        if "password" in info.data and value != info.data["password"]:
            raise ValueError("Passwords do not match")
        return value


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordConfirm(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    def validate_confirm_password(cls, value, info: ValidationInfo):
        if "new_password" in info.data and value != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return value

    @field_validator("new_password")
    def validate_password_strength(cls, value):
        validate_password_strength(value)
        return value


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

    @field_validator("confirm_password")
    def validate_confirm_password(cls, value, info: ValidationInfo):
        if "new_password" in info.data and value != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return value

    @field_validator("new_password")
    def validate_password_strength(cls, value):
        validate_password_strength(value)
        return value


class VerifyOTPRequest(BaseModel):
    otp_code: str
    temp_token: str


class DisableOTPRequest(BaseModel):
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool = True
    is_superuser: bool = False
    is_confirmed: bool = False
    otp_enabled: bool = False
    otp_verified: bool = False
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    image_url: Optional[str] = None
    bio: Optional[str] = None
    roles: List[str] = []

    model_config = {"from_attributes": True}

    @model_validator(mode='before')
    @classmethod
    def extract_profile_and_roles(cls, data):
        """Flatten eager-loaded profile and user_roles onto the response dict."""
        if isinstance(data, dict):
            return data
        result = dict(data.__dict__)
        profile = result.get('profile')
        if profile:
            result['first_name'] = profile.first_name or None
            result['last_name'] = profile.last_name or None
            result['phone'] = profile.phone or None
            result['image_url'] = profile.image_url or None
            result['bio'] = profile.bio or None
        result['roles'] = [
            ur.role.name for ur in (result.get('user_roles') or []) if ur.role
        ]
        return result

    @field_serializer("id")
    def serialize_id(self, value: int) -> str:
        return encode_id(value)
