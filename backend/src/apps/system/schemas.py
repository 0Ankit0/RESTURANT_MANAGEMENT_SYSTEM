from typing import Literal

from pydantic import BaseModel


class GeneralSettingRead(BaseModel):
    key: str
    env_value: str | None
    db_value: str | None
    effective_value: str | None
    source: Literal["environment", "database"]
    use_db_value: bool
    is_runtime_editable: bool
