from typing import Generic, Sequence, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    skip: int = Field(default=0, ge=0, description="Number of items to skip")
    limit: int = Field(default=10, ge=1, le=100, description="Number of items to return (max 100)")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    items: Sequence[T]
    total: int
    skip: int
    limit: int
    has_more: bool
    
    @classmethod
    def create(cls, items: Sequence[T], total: int, skip: int, limit: int):
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )
