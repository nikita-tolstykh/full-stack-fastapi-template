from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import col, func, select

from app.api.deps import SessionDep, require_permission
from app.core.permissions import Permission, Role
from app.models import Item, MetricsPublic, User

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get(
    "/",
    dependencies=[Depends(require_permission(Permission.METRICS_READ))],
    response_model=MetricsPublic,
)
def read_metrics(session: SessionDep) -> Any:
    """
    Get usage metrics.
    """
    users_per_role = dict(
        session.exec(select(User.role, func.count()).group_by(User.role)).all()
    )
    active_users = session.exec(
        select(func.count()).select_from(User).where(col(User.is_active))
    ).one()
    total_items = session.exec(select(func.count()).select_from(Item)).one()

    return MetricsPublic(
        total_users=sum(users_per_role.values()),
        active_users=active_users,
        total_items=total_items,
        users_by_role={role: users_per_role.get(role, 0) for role in Role},
    )
