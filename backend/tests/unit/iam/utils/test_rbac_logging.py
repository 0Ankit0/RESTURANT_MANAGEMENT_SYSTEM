import logging
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.apps.iam.models import User
from src.apps.iam.utils import rbac


class _ScalarOneOrNoneResult:
    def scalar_one_or_none(self):
        return None


@pytest.mark.asyncio
async def test_assign_role_rollback_compensation_failure_is_logged(monkeypatch, caplog):
    session = AsyncMock()
    session.get.side_effect = lambda model, _id: (
        SimpleNamespace(id=1) if model is User else SimpleNamespace(id=2, name="admin")
    )
    session.execute.return_value = _ScalarOneOrNoneResult()
    session.commit.side_effect = RuntimeError("commit failed")

    monkeypatch.setattr(rbac.CasbinEnforcer, "add_role_for_user", AsyncMock(return_value=True))
    monkeypatch.setattr(
        rbac.CasbinEnforcer,
        "remove_role_for_user",
        AsyncMock(side_effect=RuntimeError("casbin compensation failed")),
    )

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError, match="commit failed"):
            await rbac.assign_role_to_user(user_id=1, role_id=2, session=session)

    assert "rbac.assign_role_to_user.rollback_compensation_failed" in caplog.text
    assert any(getattr(record, "operation", None) == "assign_role_to_user" for record in caplog.records)
