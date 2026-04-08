"""Restaurant app package."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import APIRouter

__all__ = ["get_restaurant_router", "restaurant_router"]


def get_restaurant_router() -> "APIRouter":
    from .api import restaurant_router

    return restaurant_router


def __getattr__(name: str) -> Any:
    if name == "restaurant_router":
        return get_restaurant_router()
    raise AttributeError(name)
