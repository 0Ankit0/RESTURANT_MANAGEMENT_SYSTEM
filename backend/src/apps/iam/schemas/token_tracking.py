from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_serializer
from src.apps.core.security import TokenType
from ..utils.hashid import encode_id


class TokenTrackingResponse(BaseModel):
    id: int
    user_id: int
    token_jti: str
    token_type: TokenType
    ip_address: str
    user_agent: str
    is_active: bool
    revoked_at: Optional[datetime]
    revoke_reason: str
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_serializer("id", "user_id")
    def serialize_ids(self, value: int) -> str:
        return encode_id(value)

