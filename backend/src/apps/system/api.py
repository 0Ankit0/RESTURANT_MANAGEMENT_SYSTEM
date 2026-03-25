from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.communications import get_communications_service
from src.apps.core.config import settings
from src.apps.core.settings_store import build_general_setting_payload, get_general_settings
from src.apps.iam.api.deps import get_db
from src.apps.system.schemas import GeneralSettingRead

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/capabilities/")
async def get_capabilities() -> dict:
    return get_communications_service().get_capabilities().model_dump()


@router.get("/providers/")
async def get_providers() -> dict:
    return {
        "providers": [
            status.model_dump()
            for status in get_communications_service().get_provider_statuses()
        ]
    }


@router.get("/general-settings/", response_model=list[GeneralSettingRead])
async def get_general_settings_status(
    db: AsyncSession = Depends(get_db),
) -> list[GeneralSettingRead]:
    rows = await get_general_settings(db)
    return [
        GeneralSettingRead.model_validate(item)
        for item in build_general_setting_payload(rows, public_only=True)
    ]


@router.get("/maps/config/")
async def get_maps_config() -> dict:
    return get_communications_service().get_map_public_config()


@router.get("/health/")
async def health() -> dict:
    return {"status": "ok", "service": settings.PROJECT_NAME}


@router.get("/ready/")
async def ready() -> dict:
    return {"ready": True, "project": settings.PROJECT_NAME}
