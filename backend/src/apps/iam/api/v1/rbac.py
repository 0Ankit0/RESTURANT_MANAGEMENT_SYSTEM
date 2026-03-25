"""
RBAC API endpoints — roles, permissions, assignments and Casbin integration.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, col
from src.db.session import get_session
from src.apps.iam.models import Role, Permission, User
from src.apps.iam.api.deps import get_current_active_superuser
from src.apps.iam.schemas.rbac import (
    RoleCreate,
    RoleResponse,
    PermissionCreate,
    PermissionResponse,
    RoleAssignment,
    PermissionAssignment,
    PermissionAssignmentResponse,
    CheckPermissionResponse,
    UserRolesResponse,
    RolePermissionsResponse,
    RoleAssignmentResponse,
    CasbinRolesResponse,
    CasbinPermissionsResponse,
)
from src.apps.iam.utils.rbac import (
    assign_role_to_user,
    remove_role_from_user,
    assign_permission_to_role,
    remove_permission_from_role,
    get_user_roles,
    get_role_permissions,
    check_permission,
    resolve_authorization_domain,
)
from src.apps.iam.casbin_enforcer import CasbinEnforcer, GLOBAL_DOMAIN
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.core.schemas import PaginatedResponse
from src.apps.core.cache import RedisCache
from src.apps.observability.service import record_admin_role_change


router = APIRouter()


def _serialize_role_cache(role: Role | RoleResponse) -> dict[str, object]:
    response = role if isinstance(role, RoleResponse) else RoleResponse.model_validate(role)
    return {
        "id": response.id,
        "name": response.name,
        "description": response.description,
        "created_at": response.created_at,
        "updated_at": response.updated_at,
    }


def _serialize_permission_cache(permission: Permission | PermissionResponse) -> dict[str, object]:
    response = (
        permission
        if isinstance(permission, PermissionResponse)
        else PermissionResponse.model_validate(permission)
    )
    return {
        "id": response.id,
        "resource": response.resource,
        "action": response.action,
        "description": response.description,
        "created_at": response.created_at,
    }


async def _invalidate_user_authorization_cache(user_id: int) -> None:
    await RedisCache.clear_pattern(f"user:{user_id}:roles*")
    await RedisCache.clear_pattern(f"casbin:roles:{user_id}:*")
    await RedisCache.clear_pattern(f"casbin:permissions:{user_id}:*")
    await RedisCache.clear_pattern(f"permission:check:{user_id}:*")
    await RedisCache.delete(f"user:profile:{user_id}")


async def _invalidate_role_authorization_cache(role_id: int) -> None:
    await RedisCache.clear_pattern(f"role:{role_id}:permissions*")
    await RedisCache.clear_pattern("casbin:permissions:*")
    await RedisCache.clear_pattern("permission:check:*")


# ==== Role Management ====

@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Create a new role."""
    del current_user
    role = Role(name=role_data.name, description=role_data.description)
    session.add(role)
    await session.commit()
    await session.refresh(role)
    await RedisCache.clear_pattern("roles:list:*")
    return role


@router.get("/roles", response_model=PaginatedResponse[RoleResponse])
async def list_roles(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """List all roles with pagination."""
    del current_user
    cache_key = f"roles:list:{skip}:{limit}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    total = (await session.execute(select(func.count(col(Role.id))))).scalar_one()
    items = (await session.execute(select(Role).offset(skip).limit(limit))).scalars().all()
    items_response = [RoleResponse.model_validate(r) for r in items]

    response = PaginatedResponse[RoleResponse].create(items=items_response, total=total, skip=skip, limit=limit)
    await RedisCache.set(
        cache_key,
        {
            "items": [_serialize_role_cache(role) for role in items_response],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
        ttl=600,
    )
    return response


@router.get("/roles/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: str,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Get role details."""
    del current_user
    rid = decode_id_or_404(role_id)
    cache_key = f"role:{rid}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return RoleResponse.model_validate(cached)

    role = await session.get(Role, rid)
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    response = RoleResponse.model_validate(role)
    await RedisCache.set(cache_key, _serialize_role_cache(response), ttl=900)
    return response


# ==== Permission Management ====

@router.post("/permissions", response_model=PermissionResponse, status_code=status.HTTP_201_CREATED)
async def create_permission(
    perm_data: PermissionCreate,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Create a new permission."""
    del current_user
    permission = Permission(
        resource=perm_data.resource,
        action=perm_data.action,
        description=perm_data.description,
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    await RedisCache.clear_pattern("permissions:list:*")
    return permission


@router.get("/permissions", response_model=PaginatedResponse[PermissionResponse])
async def list_permissions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """List all permissions with pagination."""
    del current_user
    cache_key = f"permissions:list:{skip}:{limit}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    total = (await session.execute(select(func.count(col(Permission.id))))).scalar_one()
    items = (await session.execute(select(Permission).offset(skip).limit(limit))).scalars().all()
    items_response = [PermissionResponse.model_validate(p) for p in items]

    response = PaginatedResponse[PermissionResponse].create(items=items_response, total=total, skip=skip, limit=limit)
    await RedisCache.set(
        cache_key,
        {
            "items": [_serialize_permission_cache(permission) for permission in items_response],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
        ttl=600,
    )
    return response


# ==== Role-User Assignment ====

@router.post("/users/assign-role", status_code=status.HTTP_200_OK, response_model=RoleAssignmentResponse)
async def assign_role(
    assignment: RoleAssignment,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Assign a role to a user."""
    user_db_id = decode_id_or_404(assignment.user_id)
    role_db_id = decode_id_or_404(assignment.role_id)
    user_role = await assign_role_to_user(
        user_id=user_db_id,
        role_id=role_db_id,
        session=session,
    )
    await _invalidate_user_authorization_cache(user_db_id)
    await record_admin_role_change(
        session,
        actor_user_id=current_user.id,
        subject_user_id=user_db_id,
        action="assign_role",
        metadata={"user_id": user_db_id, "role_id": role_db_id},
    )
    await session.commit()
    return RoleAssignmentResponse(message="Role assigned to user", user_role_id=user_role.id)


@router.delete("/users/remove-role", status_code=status.HTTP_200_OK)
async def remove_role(
    assignment: RoleAssignment,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Remove a role from a user."""
    user_db_id = decode_id_or_404(assignment.user_id)
    role_db_id = decode_id_or_404(assignment.role_id)
    result = await remove_role_from_user(
        user_id=user_db_id,
        role_id=role_db_id,
        session=session,
    )
    await _invalidate_user_authorization_cache(user_db_id)
    await record_admin_role_change(
        session,
        actor_user_id=current_user.id,
        subject_user_id=user_db_id,
        action="remove_role",
        metadata={"user_id": user_db_id, "role_id": role_db_id},
    )
    await session.commit()
    return {"message": "Role removed from user", "success": result}


@router.get("/users/{user_id}/roles", response_model=UserRolesResponse)
async def get_user_roles_endpoint(
    user_id: str,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Get all globally assigned roles for a user."""
    del current_user
    uid = decode_id_or_404(user_id)
    cache_key = f"user:{uid}:roles:{GLOBAL_DOMAIN}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    roles = await get_user_roles(uid, session)
    response = UserRolesResponse(
        user_id=uid,
        roles=[RoleResponse.model_validate(r) for r in roles],
    )
    await RedisCache.set(
        cache_key,
        {
            "user_id": uid,
            "roles": [_serialize_role_cache(role) for role in response.roles],
        },
        ttl=300,
    )
    return response


# ==== Permission-Role Assignment ====

@router.post("/roles/assign-permission", status_code=status.HTTP_200_OK, response_model=PermissionAssignmentResponse)
async def assign_permission(
    assignment: PermissionAssignment,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Assign a permission to a role."""
    role_db_id = decode_id_or_404(assignment.role_id)
    perm_db_id = decode_id_or_404(assignment.permission_id)
    role_permission = await assign_permission_to_role(
        role_id=role_db_id,
        permission_id=perm_db_id,
        session=session,
    )
    await _invalidate_role_authorization_cache(role_db_id)
    await record_admin_role_change(
        session,
        actor_user_id=current_user.id,
        subject_user_id=None,
        action="assign_permission",
        metadata={"role_id": role_db_id, "permission_id": perm_db_id},
    )
    await session.commit()
    return PermissionAssignmentResponse(
        message="Permission assigned to role",
        role_permission_id=role_permission.id,
    )


@router.delete("/roles/remove-permission", status_code=status.HTTP_200_OK)
async def remove_permission(
    assignment: PermissionAssignment,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Remove a permission from a role."""
    role_db_id = decode_id_or_404(assignment.role_id)
    perm_db_id = decode_id_or_404(assignment.permission_id)
    result = await remove_permission_from_role(
        role_id=role_db_id,
        permission_id=perm_db_id,
        session=session,
    )
    await _invalidate_role_authorization_cache(role_db_id)
    await record_admin_role_change(
        session,
        actor_user_id=current_user.id,
        subject_user_id=None,
        action="remove_permission",
        metadata={"role_id": role_db_id, "permission_id": perm_db_id},
    )
    await session.commit()
    return {"message": "Permission removed from role", "success": result}


@router.get("/roles/{role_id}/permissions", response_model=RolePermissionsResponse)
async def get_role_permissions_endpoint(
    role_id: str,
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Get all permissions for a role."""
    del current_user
    rid = decode_id_or_404(role_id)
    cache_key = f"role:{rid}:permissions"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    permissions = await get_role_permissions(rid, session)
    response = RolePermissionsResponse(
        role_id=rid,
        permissions=[PermissionResponse.model_validate(p) for p in permissions],
    )
    await RedisCache.set(
        cache_key,
        {
            "role_id": rid,
            "permissions": [_serialize_permission_cache(permission) for permission in response.permissions],
        },
        ttl=300,
    )
    return response


# ==== Permission Checking ====

@router.get("/check-permission/{user_id}", response_model=CheckPermissionResponse)
async def check_user_permission(
    user_id: str,
    resource: str,
    action: str,
    organization_id: str | None = Query(default=None, description="Organization hashid"),
    organization_slug: str | None = Query(default=None, description="Organization slug"),
    domain: str | None = Query(
        default=None,
        description="Legacy alias for organization slug. Falls back to 'global' when omitted.",
    ),
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Check if a user has a specific permission in an organization domain."""
    del current_user
    uid = decode_id_or_404(user_id)
    organization_db_id = decode_id_or_404(organization_id) if organization_id else None
    resolved_domain = await resolve_authorization_domain(
        session,
        organization_id=organization_db_id,
        organization_slug=organization_slug or domain,
    )
    cache_key = f"permission:check:{uid}:{resolved_domain}:{resource}:{action}"
    cached = await RedisCache.get(cache_key)
    if cached is not None:
        return cached

    has_permission = await check_permission(uid, resource, action, session, resolved_domain)
    response = CheckPermissionResponse(
        user_id=uid,
        resource=resource,
        action=action,
        allowed=has_permission,
    )
    await RedisCache.set(
        cache_key,
        {
            "user_id": uid,
            "resource": resource,
            "action": action,
            "allowed": has_permission,
        },
        ttl=120,
    )
    return response


# ==== Casbin Direct Operations ====

@router.get("/casbin/roles/{user_id}", response_model=CasbinRolesResponse)
async def get_casbin_roles(
    user_id: str,
    organization_id: str | None = Query(default=None, description="Organization hashid"),
    organization_slug: str | None = Query(default=None, description="Organization slug"),
    domain: str | None = Query(default=None, description="Legacy alias for organization slug"),
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Get roles from Casbin for a user in a resolved organization domain."""
    del current_user
    uid = decode_id_or_404(user_id)
    organization_db_id = decode_id_or_404(organization_id) if organization_id else None
    resolved_domain = await resolve_authorization_domain(
        session,
        organization_id=organization_db_id,
        organization_slug=organization_slug or domain,
    )
    cache_key = f"casbin:roles:{uid}:{resolved_domain}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    roles = await CasbinEnforcer.get_roles_for_user(str(uid), resolved_domain)
    response = CasbinRolesResponse(user_id=uid, domain=resolved_domain, roles=roles)
    await RedisCache.set(
        cache_key,
        {"user_id": uid, "domain": resolved_domain, "roles": roles},
        ttl=300,
    )
    return response


@router.get("/casbin/permissions/{user_id}", response_model=CasbinPermissionsResponse)
async def get_casbin_permissions(
    user_id: str,
    organization_id: str | None = Query(default=None, description="Organization hashid"),
    organization_slug: str | None = Query(default=None, description="Organization slug"),
    domain: str | None = Query(default=None, description="Legacy alias for organization slug"),
    current_user: User = Depends(get_current_active_superuser),
    session: AsyncSession = Depends(get_session),
):
    """Get all permissions from Casbin for a user in a resolved organization domain."""
    del current_user
    uid = decode_id_or_404(user_id)
    organization_db_id = decode_id_or_404(organization_id) if organization_id else None
    resolved_domain = await resolve_authorization_domain(
        session,
        organization_id=organization_db_id,
        organization_slug=organization_slug or domain,
    )
    cache_key = f"casbin:permissions:{uid}:{resolved_domain}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    permissions = await CasbinEnforcer.get_permissions_for_user(str(uid), resolved_domain)
    response = CasbinPermissionsResponse(user_id=uid, domain=resolved_domain, permissions=permissions)
    await RedisCache.set(
        cache_key,
        {"user_id": uid, "domain": resolved_domain, "permissions": permissions},
        ttl=300,
    )
    return response
