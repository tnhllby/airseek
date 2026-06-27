from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.users.models import User, UserSubscription
from app.modules.users.schemas import SubscriptionCreate, UserCreate, UserUpdate


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    user = User(
        email=user_in.email.lower(),
        password_hash=hash_password(user_in.password),
        name=user_in.name,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Email already registered")
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email.lower(), User.is_active == True)  # noqa: E712
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")
    return user


async def update_user(db: AsyncSession, user: User, update: UserUpdate) -> User:
    if update.name is not None:
        user.name = update.name
    if update.fcm_token is not None:
        user.fcm_token = update.fcm_token
    await db.commit()
    await db.refresh(user)
    return user


async def get_subscriptions(db: AsyncSession, user_id: UUID) -> list[UserSubscription]:
    result = await db.execute(
        select(UserSubscription).where(UserSubscription.user_id == user_id)
    )
    return list(result.scalars().all())


async def create_subscription(
    db: AsyncSession,
    user_id: UUID,
    sub_in: SubscriptionCreate,
) -> UserSubscription:
    sub = UserSubscription(
        user_id=user_id,
        station_id=sub_in.station_id,
        aqi_threshold=sub_in.aqi_threshold,
    )
    db.add(sub)
    try:
        await db.commit()
        await db.refresh(sub)
    except IntegrityError:
        await db.rollback()
        raise ConflictError("Already subscribed to this station")
    return sub


async def delete_subscription(
    db: AsyncSession,
    user_id: UUID,
    subscription_id: UUID,
) -> None:
    result = await db.execute(
        select(UserSubscription).where(
            UserSubscription.id == subscription_id,
            UserSubscription.user_id == user_id,
        )
    )
    sub = result.scalar_one_or_none()
    if sub is None:
        raise NotFoundError("Subscription not found")
    await db.delete(sub)
    await db.commit()
