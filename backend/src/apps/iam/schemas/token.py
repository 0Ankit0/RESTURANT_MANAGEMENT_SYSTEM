from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    access: str
    refresh: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    refresh: Optional[bool] = False
