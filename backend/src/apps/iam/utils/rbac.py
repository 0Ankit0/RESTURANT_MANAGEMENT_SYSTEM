"""
RBAC helpers that keep the relational catalog and the Casbin policy store aligned.

The SQL tables remain the source of truth for the global RBAC catalog that admins
manage through the API. Organization-scoped membership lives in the multitenancy
tables and is mirrored into Casbin with the organization slug as the domain.
Casbin stores the runtime authorization tuples that are used during permission
checks.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from src.apps.iam.models import User, Role, UserRole, Permission, RolePermission
from src.apps.iam.casbin_enforcer import CasbinEnforcer, GLOBAL_DOMAIN
from src.apps.multitenancy.models.tenant import Tenant


async def get_user_roles(user_id: int, session: AsyncSession) -> list[Role]:
    statement = (
        select(Role)
        .join(UserRole)
        .where(UserRole.user_id == user_id)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_role_permissions(role_id: int, session: AsyncSession) -> list[Permission]:
    statement = (
        select(Permission)
        .join(RolePermission)
        .where(RolePermission.role_id == role_id)
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


def _require_global_catalog_domain(domain: str) -> str:
    """
    The SQL RBAC catalog is global.

    Organization-scoped role membership is modeled separately through
    `TenantMember` and mirrored into Casbin with the tenant/org slug as
    the domain. Keeping that boundary explicit avoids pretending that a
    `UserRole` or `RolePermission` row can be organization-specific when
    the schema does not store that scope.
    """
    normalized = CasbinEnforcer.normalize_domain(domain)
    if normalized != GLOBAL_DOMAIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Organization-scoped role assignments are managed through the "
                "organization membership APIs. The RBAC catalog helpers only "
                "support the global domain."
            ),
        )
    return normalized


async def resolve_authorization_domain(
    session: AsyncSession,
    *,
    organization_id: int | None = None,
    organization_slug: str | None = None,
) -> str:
    """
    Resolve the Casbin domain from the organization stored in the database.

    - `organization_id` is the preferred input and maps to `Tenant.id`
    - `organization_slug` is accepted for already-resolved callers
    - falling back to `global` is only used for application-wide checks
    """
    if organization_id is not None:
        organization = await session.get(Tenant, organization_id)
        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found",
            )
        return organization.slug

    normalized_slug = CasbinEnforcer.normalize_domain(organization_slug)
    if normalized_slug == GLOBAL_DOMAIN:
        return GLOBAL_DOMAIN

    result = await session.execute(select(Tenant).where(Tenant.slug == normalized_slug))
    organization = result.scalars().first()
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )
    return organization.slug


async def assign_role_to_user(
    user_id: int,
    role_id: int,
    session: AsyncSession,
    domain: str = GLOBAL_DOMAIN,
) -> UserRole:
    domain = _require_global_catalog_domain(domain)
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    existing = (await session.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role already assigned to user")

    user_role = UserRole(user_id=user_id, role_id=role_id)
    session.add(user_role)
    await session.flush()
    try:
        await CasbinEnforcer.add_role_for_user(str(user_id), role.name, domain)
    except Exception:
        await session.rollback()
        raise

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        try:
            await CasbinEnforcer.remove_role_for_user(str(user_id), role.name, domain)
        except Exception:
            pass
        raise

    await session.refresh(user_role)
    return user_role


async def remove_role_from_user(
    user_id: int,
    role_id: int,
    session: AsyncSession,
    domain: str = GLOBAL_DOMAIN,
) -> bool:
    domain = _require_global_catalog_domain(domain)
    user_role = (await session.execute(
        select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
    )).scalar_one_or_none()
    if not user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not assigned to user")

    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    await session.delete(user_role)
    await session.flush()
    try:
        await CasbinEnforcer.remove_role_for_user(str(user_id), role.name, domain)
    except Exception:
        await session.rollback()
        raise

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        try:
            await CasbinEnforcer.add_role_for_user(str(user_id), role.name, domain)
        except Exception:
            pass
        raise
    return True


async def assign_permission_to_role(
    role_id: int,
    permission_id: int,
    session: AsyncSession,
    domain: str = GLOBAL_DOMAIN,
) -> RolePermission:
    domain = _require_global_catalog_domain(domain)
    role = await session.get(Role, role_id)
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    permission = await session.get(Permission, permission_id)
    if not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    existing = (await session.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Permission already assigned to role")

    role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
    session.add(role_permission)
    await session.flush()
    try:
        await CasbinEnforcer.add_policy(role.name, permission.resource, permission.action, domain)
    except Exception:
        await session.rollback()
        raise

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        try:
            await CasbinEnforcer.remove_policy(role.name, permission.resource, permission.action, domain)
        except Exception:
            pass
        raise

    await session.refresh(role_permission)
    return role_permission


async def remove_permission_from_role(
    role_id: int,
    permission_id: int,
    session: AsyncSession,
    domain: str = GLOBAL_DOMAIN,
) -> bool:
    domain = _require_global_catalog_domain(domain)
    role_permission = (await session.execute(
        select(RolePermission).where(
            RolePermission.role_id == role_id,
            RolePermission.permission_id == permission_id,
        )
    )).scalar_one_or_none()
    if not role_permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not assigned to role")

    role = await session.get(Role, role_id)
    permission = await session.get(Permission, permission_id)
    if not role or not permission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role or permission not found")

    await session.delete(role_permission)
    await session.flush()
    try:
        await CasbinEnforcer.remove_policy(role.name, permission.resource, permission.action, domain)
    except Exception:
        await session.rollback()
        raise

    try:
        await session.commit()
    except Exception:
        await session.rollback()
        try:
            await CasbinEnforcer.add_policy(role.name, permission.resource, permission.action, domain)
        except Exception:
            pass
        raise
    return True


async def check_permission(
    user_id: int,
    resource: str,
    action: str,
    session: AsyncSession,
    domain: str = GLOBAL_DOMAIN,
) -> bool:
    del session
    return await CasbinEnforcer.enforce(str(user_id), resource, action, domain)
