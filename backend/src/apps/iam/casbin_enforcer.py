from pathlib import Path
from typing import Optional

from casbin import AsyncEnforcer
from casbin_async_sqlalchemy_adapter import Adapter as AsyncAdapter
from sqlalchemy.ext.asyncio import AsyncEngine

GLOBAL_DOMAIN = "global"


class CasbinEnforcer:
    """
    Thin wrapper around the shared Casbin enforcer instance.

    The project uses domain-aware RBAC with four request fields:
    `(subject, domain, object, action)`.

    - `subject`: usually a user id string, for example `"42"`
    - `domain`: `"global"` for application-wide access or an organization slug
    - `object`: permission resource, for example `"users"`
    - `action`: permission action, for example `"read"`

    Role memberships are stored as grouping policies:
    `g, <user_id>, <role_name>, <domain>`

    Permissions are stored as regular policies:
    `p, <role_name>, <domain>, <resource>, <action>`
    """

    _enforcer: Optional[AsyncEnforcer] = None

    @classmethod
    async def get_enforcer(cls, engine: AsyncEngine) -> AsyncEnforcer:
        """Create the shared enforcer once and load persisted policies."""
        if cls._enforcer is None:
            model_path = Path(__file__).parent / "casbin_model.conf"
            adapter = AsyncAdapter(engine, db_class=None)
            cls._enforcer = AsyncEnforcer(str(model_path), adapter)
            await cls._enforcer.load_policy()
        return cls._enforcer

    @classmethod
    def normalize_domain(cls, domain: str | None) -> str:
        """Collapse empty domain values to the global authorization namespace."""
        normalized = (domain or "").strip()
        return normalized or GLOBAL_DOMAIN

    @classmethod
    def _require_enforcer(cls) -> AsyncEnforcer:
        if cls._enforcer is None:
            raise RuntimeError("Enforcer not initialized. Call get_enforcer first.")
        return cls._enforcer

    # ── Policy management ─────────────────────────────────────────────────

    @classmethod
    async def add_policy(
        cls,
        sub: str,
        obj: str,
        act: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> bool:
        enforcer = cls._require_enforcer()
        return await enforcer.add_policy(sub, cls.normalize_domain(domain), obj, act)

    @classmethod
    async def remove_policy(
        cls,
        sub: str,
        obj: str,
        act: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> bool:
        enforcer = cls._require_enforcer()
        return await enforcer.remove_policy(sub, cls.normalize_domain(domain), obj, act)

    # ── Role / grouping management ────────────────────────────────────────

    @classmethod
    async def add_role_for_user(
        cls,
        user: str,
        role: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> bool:
        enforcer = cls._require_enforcer()
        return await enforcer.add_role_for_user_in_domain(
            user,
            role,
            cls.normalize_domain(domain),
        )

    @classmethod
    async def remove_role_for_user(
        cls,
        user: str,
        role: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> bool:
        """
        Remove one exact `(user, role, domain)` grouping tuple.

        Using the explicit grouping policy API is safer than a bulk role-delete
        helper here because callers intend to revoke one role assignment, not
        wipe every role in a domain.
        """
        enforcer = cls._require_enforcer()
        return await enforcer.remove_grouping_policy(
            user,
            role,
            cls.normalize_domain(domain),
        )

    @classmethod
    async def get_roles_for_user(
        cls,
        user: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> list[str]:
        enforcer = cls._require_enforcer()
        return await enforcer.get_roles_for_user_in_domain(
            user,
            cls.normalize_domain(domain),
        )

    @classmethod
    async def get_users_for_role(
        cls,
        role: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> list[str]:
        enforcer = cls._require_enforcer()
        return await enforcer.get_users_for_role_in_domain(
            role,
            cls.normalize_domain(domain),
        )

    # ── Permission checking ───────────────────────────────────────────────

    @classmethod
    async def enforce(
        cls,
        sub: str,
        obj: str,
        act: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> bool:
        enforcer = cls._require_enforcer()
        return enforcer.enforce(sub, cls.normalize_domain(domain), obj, act)

    @classmethod
    async def get_permissions_for_user(
        cls,
        user: str,
        domain: str = GLOBAL_DOMAIN,
    ) -> list[list[str]]:
        enforcer = cls._require_enforcer()
        return await enforcer.get_permissions_for_user_in_domain(
            user,
            cls.normalize_domain(domain),
        )
