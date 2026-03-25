"""
Tenant (multitenancy) API endpoints — CRUD, member management, invitations.
"""
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, col

from src.apps.iam.api.deps import get_current_user, get_db
from src.apps.iam.casbin_enforcer import CasbinEnforcer
from src.apps.multitenancy.models.tenant import (
    InvitationStatus,
    Tenant,
    TenantInvitation,
    TenantMember,
    TenantRole,
)
from src.apps.iam.models.user import User
from src.apps.multitenancy.schemas.tenant import (
    AcceptInvitationRequest,
    TenantCreate,
    TenantInvitationCreate,
    TenantInvitationResponse,
    TenantMemberResponse,
    TenantMemberUpdate,
    TenantResponse,
    TenantUpdate,
    TenantWithMembersResponse,
)
from src.apps.core.cache import RedisCache
from src.apps.core.schemas import PaginatedResponse
from src.apps.analytics.dependencies import get_analytics
from src.apps.analytics.service import AnalyticsService
from src.apps.analytics.events import TenantEvents
from src.apps.iam.utils.hashid import decode_id_or_404

router = APIRouter()

_INVITATION_TTL_HOURS = 48


# ── helpers ───────────────────────────────────────────────────────────────────

def _serialize_tenant_response(tenant: Tenant | TenantResponse) -> dict[str, object]:
    response = tenant if isinstance(tenant, TenantResponse) else TenantResponse.model_validate(tenant)
    return {
        "id": response.id,
        "name": response.name,
        "slug": response.slug,
        "description": response.description,
        "is_active": response.is_active,
        "owner_id": response.owner_id,
        "created_at": response.created_at,
        "updated_at": response.updated_at,
    }


def _serialize_tenant_member_response(
    member: TenantMember | TenantMemberResponse,
) -> dict[str, object]:
    response = (
        member if isinstance(member, TenantMemberResponse) else TenantMemberResponse.model_validate(member)
    )
    return {
        "id": response.id,
        "tenant_id": response.tenant_id,
        "user_id": response.user_id,
        "role": response.role,
        "is_active": response.is_active,
        "joined_at": response.joined_at,
    }


async def _get_tenant_or_404(tenant_id: int, db: AsyncSession) -> Tenant:
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return tenant


async def _require_tenant_role(
    tenant_id: int,
    user: User,
    db: AsyncSession,
    min_role: TenantRole = TenantRole.ADMIN,
) -> TenantMember:
    """Raise 403 if user does not have at least `min_role` in this tenant."""
    membership = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == tenant_id,
                TenantMember.user_id == user.id,
                TenantMember.is_active == True,
            )
        )
    ).scalars().first()

    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this tenant")

    role_order = {TenantRole.MEMBER: 0, TenantRole.ADMIN: 1, TenantRole.OWNER: 2}
    if role_order[membership.role] < role_order[min_role]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions in tenant")

    return membership


# ── Tenant CRUD ───────────────────────────────────────────────────────────────

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
):
    """Create a new tenant. The calling user becomes the owner."""
    existing = (
        await db.execute(select(Tenant).where(Tenant.slug == data.slug))
    ).scalars().first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Slug already taken")

    tenant = Tenant(
        name=data.name,
        slug=data.slug,
        description=data.description,
        owner_id=current_user.id,
    )
    db.add(tenant)
    await db.flush()  # get tenant.id before commit

    # Auto-add owner as a member
    membership = TenantMember(
        tenant_id=tenant.id,
        user_id=current_user.id,
        role=TenantRole.OWNER,
    )
    db.add(membership)
    await db.flush()  # ensure tenant/member rows exist before mirroring to Casbin
    try:
        await CasbinEnforcer.add_role_for_user(str(current_user.id), TenantRole.OWNER, tenant.slug)
    except Exception:
        await db.rollback()
        raise

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        try:
            await CasbinEnforcer.remove_role_for_user(str(current_user.id), TenantRole.OWNER, tenant.slug)
        except Exception:
            pass
        raise

    await db.refresh(tenant)

    await RedisCache.clear_pattern("tenants:list:*")
    await analytics.capture(
        str(current_user.id),
        TenantEvents.TENANT_CREATED,
        {"tenant_id": tenant.id, "tenant_slug": tenant.slug, "tenant_name": tenant.name},
    )
    return tenant


@router.get("/", response_model=PaginatedResponse[TenantResponse])
async def list_my_tenants(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tenants the current user is a member of."""
    cache_key = f"tenants:list:{current_user.id}:{skip}:{limit}"
    cached = await RedisCache.get(cache_key)
    if cached:
        return cached

    total = (
        await db.execute(
            select(func.count(col(Tenant.id)))
            .join(TenantMember)
            .where(TenantMember.user_id == current_user.id, TenantMember.is_active == True)
        )
    ).scalar_one()

    items = (
        await db.execute(
            select(Tenant)
            .join(TenantMember)
            .where(TenantMember.user_id == current_user.id, TenantMember.is_active == True)
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()

    items_resp = [TenantResponse.model_validate(t) for t in items]
    response = PaginatedResponse[TenantResponse].create(items=items_resp, total=total, skip=skip, limit=limit)
    await RedisCache.set(
        cache_key,
        {
            "items": [_serialize_tenant_response(item) for item in items_resp],
            "total": total,
            "skip": skip,
            "limit": limit,
        },
        ttl=120,
    )
    return response


@router.get("/{tenant_id}", response_model=TenantWithMembersResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant details (must be a member)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.MEMBER)
    tenant = await _get_tenant_or_404(tenant_db_id, db)

    members_raw = (
        await db.execute(
            select(TenantMember).where(TenantMember.tenant_id == tenant_db_id)
        )
    ).scalars().all()

    response = TenantWithMembersResponse.model_validate(
        {
            **_serialize_tenant_response(tenant),
            "members": [TenantMemberResponse.model_validate(m) for m in members_raw],
        }
    )
    return response


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    data: TenantUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant details (admin or owner only)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.ADMIN)
    tenant = await _get_tenant_or_404(tenant_db_id, db)

    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(tenant, field, value)
    tenant.updated_at = datetime.now()

    await db.commit()
    await db.refresh(tenant)

    await RedisCache.clear_pattern("tenants:list:*")
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tenant (owner only)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.OWNER)
    tenant = await _get_tenant_or_404(tenant_db_id, db)
    memberships = (
        await db.execute(
            select(TenantMember).where(TenantMember.tenant_id == tenant_db_id)
        )
    ).scalars().all()
    await db.delete(tenant)
    await db.flush()
    removed_groupings: list[tuple[int, TenantRole]] = []
    try:
        for membership in memberships:
            if membership.user_id is None:
                continue
            await CasbinEnforcer.remove_role_for_user(
                str(membership.user_id),
                membership.role,
                tenant.slug,
            )
            removed_groupings.append((membership.user_id, membership.role))
    except Exception:
        await db.rollback()
        raise

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        for user_id, role in removed_groupings:
            try:
                await CasbinEnforcer.add_role_for_user(str(user_id), role, tenant.slug)
            except Exception:
                pass
        raise

    await RedisCache.clear_pattern("tenants:list:*")


# ── Member management ─────────────────────────────────────────────────────────

@router.get("/{tenant_id}/members", response_model=PaginatedResponse[TenantMemberResponse])
async def list_members(
    tenant_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all members of a tenant."""
    tenant_db_id = decode_id_or_404(tenant_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.MEMBER)

    total = (
        await db.execute(
            select(func.count(col(TenantMember.id))).where(TenantMember.tenant_id == tenant_db_id)
        )
    ).scalar_one()

    items = (
        await db.execute(
            select(TenantMember)
            .where(TenantMember.tenant_id == tenant_db_id)
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()

    items_resp = [TenantMemberResponse.model_validate(m) for m in items]
    return PaginatedResponse[TenantMemberResponse].create(items=items_resp, total=total, skip=skip, limit=limit)


@router.patch("/{tenant_id}/members/{user_id}", response_model=TenantMemberResponse)
async def update_member_role(
    tenant_id: str,
    user_id: str,
    data: TenantMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a member's role (admin/owner only; only owner can promote to owner)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    user_db_id = decode_id_or_404(user_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.ADMIN)

    if data.role == TenantRole.OWNER:
        # Only current owner can hand off ownership
        await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.OWNER)

    membership = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == tenant_db_id,
                TenantMember.user_id == user_db_id,
            )
        )
    ).scalars().first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    tenant = await _get_tenant_or_404(tenant_db_id, db)
    previous_role = membership.role
    if previous_role == data.role:
        return membership

    membership.role = data.role
    await db.flush()
    try:
        await CasbinEnforcer.remove_role_for_user(str(user_db_id), previous_role, tenant.slug)
        await CasbinEnforcer.add_role_for_user(str(user_db_id), data.role, tenant.slug)
    except Exception:
        await db.rollback()
        raise

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        try:
            await CasbinEnforcer.remove_role_for_user(str(user_db_id), data.role, tenant.slug)
            await CasbinEnforcer.add_role_for_user(str(user_db_id), previous_role, tenant.slug)
        except Exception:
            pass
        raise

    await db.refresh(membership)
    await RedisCache.clear_pattern("tenants:list:*")
    return membership


@router.delete("/{tenant_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    tenant_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
):
    """Remove a member from the tenant (admin/owner, or user removing themselves)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    user_db_id = decode_id_or_404(user_id)
    if user_db_id != current_user.id:
        await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.ADMIN)

    membership = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == tenant_db_id,
                TenantMember.user_id == user_db_id,
            )
        )
    ).scalars().first()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    tenant = await _get_tenant_or_404(tenant_db_id, db)

    # Prevent removing the last owner
    if membership.role == TenantRole.OWNER:
        owners_count = (
            await db.execute(
                select(func.count(col(TenantMember.id))).where(
                    TenantMember.tenant_id == tenant_db_id,
                    TenantMember.role == TenantRole.OWNER,
                )
            )
        ).scalar_one()
        if owners_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last owner. Transfer ownership first.",
            )

    await db.delete(membership)
    await db.flush()
    try:
        await CasbinEnforcer.remove_role_for_user(str(user_db_id), membership.role, tenant.slug)
    except Exception:
        await db.rollback()
        raise

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        try:
            await CasbinEnforcer.add_role_for_user(str(user_db_id), membership.role, tenant.slug)
        except Exception:
            pass
        raise

    await RedisCache.clear_pattern("tenants:list:*")

    await analytics.capture(
        str(current_user.id),
        TenantEvents.TENANT_MEMBER_REMOVED,
        {"tenant_id": tenant_db_id, "removed_user_id": user_db_id},
    )


# ── Invitations ───────────────────────────────────────────────────────────────

@router.post("/{tenant_id}/invitations", response_model=TenantInvitationResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    tenant_id: str,
    data: TenantInvitationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
):
    """Invite a user to a tenant by email (admin/owner only)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.ADMIN)
    await _get_tenant_or_404(tenant_db_id, db)

    # Check for active pending invitation for this email
    existing = (
        await db.execute(
            select(TenantInvitation).where(
                TenantInvitation.tenant_id == tenant_db_id,
                TenantInvitation.email == data.email,
                TenantInvitation.status == InvitationStatus.PENDING,
            )
        )
    ).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An active invitation already exists for this email",
        )

    invitation = TenantInvitation(
        tenant_id=tenant_db_id,
        email=str(data.email),
        role=data.role,
        invited_by=current_user.id,
        token=str(uuid.uuid4()),
        expires_at=datetime.now() + timedelta(hours=_INVITATION_TTL_HOURS),
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    await analytics.capture(
        str(current_user.id),
        TenantEvents.TENANT_MEMBER_INVITED,
        {"tenant_id": tenant_db_id, "invitee_email": str(data.email), "role": data.role.value},
    )
    return invitation


@router.get("/{tenant_id}/invitations", response_model=PaginatedResponse[TenantInvitationResponse])
async def list_invitations(
    tenant_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List invitations for a tenant (admin/owner only)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.ADMIN)

    total = (
        await db.execute(
            select(func.count(col(TenantInvitation.id))).where(
                TenantInvitation.tenant_id == tenant_db_id
            )
        )
    ).scalar_one()

    items = (
        await db.execute(
            select(TenantInvitation)
            .where(TenantInvitation.tenant_id == tenant_db_id)
            .offset(skip)
            .limit(limit)
        )
    ).scalars().all()

    items_resp = [TenantInvitationResponse.model_validate(i) for i in items]
    return PaginatedResponse[TenantInvitationResponse].create(items=items_resp, total=total, skip=skip, limit=limit)


@router.post("/invitations/accept", response_model=TenantMemberResponse)
async def accept_invitation(
    body: AcceptInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics),
):
    """Accept an invitation token and join the tenant."""
    invitation = (
        await db.execute(
            select(TenantInvitation).where(TenantInvitation.token == body.token)
        )
    ).scalars().first()

    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invitation is {invitation.status}",
        )

    if invitation.expires_at < datetime.now():
        invitation.status = InvitationStatus.EXPIRED
        await db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation has expired")

    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation was sent to a different email address",
        )

    # Check already a member
    already = (
        await db.execute(
            select(TenantMember).where(
                TenantMember.tenant_id == invitation.tenant_id,
                TenantMember.user_id == current_user.id,
            )
        )
    ).scalars().first()
    if already:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already a member of this tenant")

    tenant = await _get_tenant_or_404(invitation.tenant_id, db)

    membership = TenantMember(
        tenant_id=invitation.tenant_id,
        user_id=current_user.id,
        role=invitation.role,
    )
    db.add(membership)

    invitation.status = InvitationStatus.ACCEPTED
    invitation.accepted_at = datetime.now()
    await db.flush()
    try:
        await CasbinEnforcer.add_role_for_user(str(current_user.id), invitation.role, tenant.slug)
    except Exception:
        await db.rollback()
        raise

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        try:
            await CasbinEnforcer.remove_role_for_user(str(current_user.id), invitation.role, tenant.slug)
        except Exception:
            pass
        raise

    await db.refresh(membership)
    await RedisCache.clear_pattern("tenants:list:*")
    await analytics.capture(
        str(current_user.id),
        TenantEvents.TENANT_MEMBER_JOINED,
        {"tenant_id": tenant.id, "tenant_slug": tenant.slug, "role": invitation.role.value},
    )
    return membership


@router.delete("/{tenant_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    tenant_id: str,
    invitation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a pending invitation (admin/owner only)."""
    tenant_db_id = decode_id_or_404(tenant_id)
    invitation_db_id = decode_id_or_404(invitation_id)
    await _require_tenant_role(tenant_db_id, current_user, db, min_role=TenantRole.ADMIN)

    invitation = (
        await db.execute(
            select(TenantInvitation).where(
                TenantInvitation.id == invitation_db_id,
                TenantInvitation.tenant_id == tenant_db_id,
            )
        )
    ).scalars().first()
    if not invitation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitation not found")

    if invitation.status != InvitationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only pending invitations can be revoked",
        )

    invitation.status = InvitationStatus.REVOKED
    await db.commit()
