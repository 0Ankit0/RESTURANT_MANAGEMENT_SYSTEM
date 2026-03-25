from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_session
from src.apps.iam.api.deps import get_current_user
from src.apps.iam.casbin_enforcer import CasbinEnforcer
from src.apps.iam.models.user import User
from src.apps.iam.utils.hashid import decode_id_or_404
from src.apps.iam.utils.rbac import check_permission, resolve_authorization_domain


def require_permission(resource: str, action: str):
    """
    Dependency factory for checking user permissions.
    
    Usage:
        @router.get("/users", dependencies=[Depends(require_permission("users", "read"))])
        async def list_users():
            ...
    
    Args:
        resource: Resource identifier (e.g., "users", "posts")
        action: Action to perform (e.g., "read", "write", "delete")
        
    Returns:
        Callable: Dependency function
    """
    async def permission_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
    ):
        organization_id = (
            request.path_params.get("organization_id")
            or request.query_params.get("organization_id")
            or request.path_params.get("tenant_id")
            or request.query_params.get("tenant_id")
        )
        organization_slug = (
            request.path_params.get("organization_slug")
            or request.query_params.get("organization_slug")
            or request.path_params.get("tenant_slug")
            or request.query_params.get("tenant_slug")
        )
        organization_db_id = decode_id_or_404(organization_id) if organization_id else None
        domain = await resolve_authorization_domain(
            session,
            organization_id=organization_db_id,
            organization_slug=organization_slug,
        )
        has_permission = await check_permission(
            user_id=current_user.id,
            resource=resource,
            action=action,
            session=session,
            domain=domain,
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {action} on {resource}"
            )
        
        return True
    
    return permission_checker


def require_role(role_name: str):
    """
    Dependency factory for checking user roles.
    
    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        async def admin_panel():
            ...
    
    Args:
        role_name: Name of the required role
        
    Returns:
        Callable: Dependency function
    """
    async def role_checker(
        request: Request,
        current_user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
    ):
        organization_id = (
            request.path_params.get("organization_id")
            or request.query_params.get("organization_id")
            or request.path_params.get("tenant_id")
            or request.query_params.get("tenant_id")
        )
        organization_slug = (
            request.path_params.get("organization_slug")
            or request.query_params.get("organization_slug")
            or request.path_params.get("tenant_slug")
            or request.query_params.get("tenant_slug")
        )
        organization_db_id = decode_id_or_404(organization_id) if organization_id else None
        domain = await resolve_authorization_domain(
            session,
            organization_id=organization_db_id,
            organization_slug=organization_slug,
        )
        roles = await CasbinEnforcer.get_roles_for_user(str(current_user.id), domain)

        if role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role_name}"
            )
        
        return True
    
    return role_checker
