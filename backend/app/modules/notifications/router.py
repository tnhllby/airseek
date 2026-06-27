from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.modules.notifications import service
from app.modules.notifications.schemas import NotificationResponse
from app.modules.users.models import User

router = APIRouter(prefix="/notifications", tags=["notifications"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    current_user: CurrentUser,
    db: DbSession,
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
) -> list[NotificationResponse]:
    notifications = await service.get_user_notifications(
        db, current_user.id, limit=limit, unread_only=unread_only
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    await service.delete_notification(db, current_user.id, notification_id)
