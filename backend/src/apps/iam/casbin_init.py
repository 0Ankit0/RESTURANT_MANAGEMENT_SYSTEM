"""
Casbin initialization utilities for FastAPI application.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.apps.iam.casbin_enforcer import CasbinEnforcer, GLOBAL_DOMAIN
from src.db.session import engine


@asynccontextmanager
async def init_casbin(app: FastAPI):
    """
    Initialize Casbin enforcer on application startup.
    
    Usage in main.py:
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            async with init_casbin(app):
                yield
        
        app = FastAPI(lifespan=lifespan)
    
    Args:
        app: FastAPI application instance
    """
    # Initialize Casbin enforcer
    enforcer = await CasbinEnforcer.get_enforcer(engine)
    app.state.casbin_enforcer = enforcer
    
    yield
    
    # Cleanup if needed
    pass


async def setup_default_roles_and_permissions(session):
    """
    Setup default roles and permissions for the application.
    Call this function after database migrations to initialize the RBAC system.

    This seeds two layers at once:
    - SQL tables for `Role`, `Permission`, and assignment joins
    - Casbin policy rows through the RBAC utility helpers
    
    Args:
        session: AsyncSession instance
        
    Example:
        from sqlmodel import Session
        from src.apps.iam.casbin_init import setup_default_roles_and_permissions
        
        async with get_session() as session:
            await setup_default_roles_and_permissions(session)
    """
    from src.apps.iam.models import Role, Permission
    from src.apps.iam.utils.rbac import assign_permission_to_role
    from sqlmodel import select
    
    # Check if roles already exist
    result = await session.execute(select(Role))
    existing_roles = result.scalars().all()
    
    if existing_roles:
        print("Roles already exist. Skipping initialization.")
        return
    
    # Create default roles
    admin_role = Role(
        name="admin",
        description="Administrator with full system access"
    )
    editor_role = Role(
        name="editor",
        description="Can create and edit content"
    )
    viewer_role = Role(
        name="viewer",
        description="Can view content only"
    )
    
    session.add_all([admin_role, editor_role, viewer_role])
    await session.commit()
    await session.refresh(admin_role)
    await session.refresh(editor_role)
    await session.refresh(viewer_role)
    
    # Create default permissions
    permissions = [
        Permission(resource="users", action="read", description="View users"),
        Permission(resource="users", action="write", description="Create/edit users"),
        Permission(resource="users", action="delete", description="Delete users"),
        Permission(resource="posts", action="read", description="View posts"),
        Permission(resource="posts", action="write", description="Create/edit posts"),
        Permission(resource="posts", action="delete", description="Delete posts"),
        Permission(resource="settings", action="read", description="View settings"),
        Permission(resource="settings", action="write", description="Edit settings"),
    ]
    
    session.add_all(permissions)
    await session.commit()
    
    # Refresh all permissions to get their IDs
    for perm in permissions:
        await session.refresh(perm)
    
    # Assign permissions to admin role (full access)
    for perm in permissions:
        assert admin_role.id is not None and perm.id is not None
        await assign_permission_to_role(admin_role.id, perm.id, session, GLOBAL_DOMAIN)
    
    # Assign read/write permissions to editor role
    for perm in permissions:
        assert editor_role.id is not None and perm.id is not None
        if perm.action in ["read", "write"]:
            await assign_permission_to_role(editor_role.id, perm.id, session, GLOBAL_DOMAIN)
    
    # Assign only read permissions to viewer role
    for perm in permissions:
        assert viewer_role.id is not None and perm.id is not None
        if perm.action == "read":
            await assign_permission_to_role(viewer_role.id, perm.id, session, GLOBAL_DOMAIN)
    
    print("Default roles and permissions created successfully!")
    print(f"- Admin role ID: {admin_role.id}")
    print(f"- Editor role ID: {editor_role.id}")
    print(f"- Viewer role ID: {viewer_role.id}")
