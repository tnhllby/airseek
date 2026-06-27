from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.notifications.models import Notification


async def get_user_notifications(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 50,
    unread_only: bool = False,
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(desc(Notification.created_at))
        .limit(limit)
    )
    if unread_only:
        stmt = stmt.where(Notification.is_sent == False)  # noqa: E712
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_notification(
    db: AsyncSession,
    user_id: UUID,
    notification_id: int,
) -> None:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise NotFoundError("Notification not found")
    await db.delete(notification)
    await db.commit()
