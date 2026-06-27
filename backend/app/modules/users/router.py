from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import AuthError
from app.core.security import create_access_token
from app.database import get_db
from app.modules.users import service
from app.modules.users.models import User
from app.modules.users.schemas import (
    LoginRequest,
    SubscriptionCreate,
    SubscriptionResponse,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)

router = APIRouter(tags=["users"])

DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user_in: UserCreate, db: DbSession) -> UserResponse:
    user = await service.create_user(db, user_in)
    return UserResponse.model_validate(user)


@router.post("/auth/login", response_model=Token)
async def login(credentials: LoginRequest, db: DbSession) -> Token:
    user = await service.authenticate_user(db, credentials.email, credentials.password)
    if user is None:
        raise AuthError("Invalid email or password")
    token = create_access_token(str(user.id))
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/users/me", response_model=UserResponse)
async def update_me(update: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserResponse:
    user = await service.update_user(db, current_user, update)
    return UserResponse.model_validate(user)


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def get_subscriptions(current_user: CurrentUser, db: DbSession) -> list[SubscriptionResponse]:
    subs = await service.get_subscriptions(db, current_user.id)
    return [SubscriptionResponse.model_validate(s) for s in subs]


@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    sub_in: SubscriptionCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> SubscriptionResponse:
    sub = await service.create_subscription(db, current_user.id, sub_in)
    return SubscriptionResponse.model_validate(sub)


@router.delete("/subscriptions/{subscription_id}", status_code=204)
async def delete_subscription(
    subscription_id: UUID,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    await service.delete_subscription(db, current_user.id, subscription_id)
