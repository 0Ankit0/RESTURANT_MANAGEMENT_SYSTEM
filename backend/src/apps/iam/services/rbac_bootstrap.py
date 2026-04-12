from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.iam.casbin_init import setup_default_roles_and_permissions
from src.apps.iam.models import RbacBootstrapState


async def bootstrap_rbac_defaults(
    session: AsyncSession,
    *,
    actor_user_id: int,
    version: str = "v1",
) -> RbacBootstrapState:
    result = await setup_default_roles_and_permissions(session)
    state = await session.get(RbacBootstrapState, 1)
    if state is None:
        state = RbacBootstrapState(
            id=1,
            version=version,
            actor_user_id=actor_user_id,
            bootstrapped_at=datetime.now(),
            applied=bool(result.get("created")),
            run_count=1,
            details=result,
        )
        session.add(state)
    else:
        state.version = version
        state.actor_user_id = actor_user_id
        state.bootstrapped_at = datetime.now()
        state.applied = bool(result.get("created"))
        state.run_count += 1
        state.details = result
    await session.commit()
    await session.refresh(state)
    return state
