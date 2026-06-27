from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError
from app.core.security import decode_access_token
from app.database import get_db

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Import here to avoid circular import at module load time
    from app.modules.users.models import User

    if credentials is None:
        raise AuthError()

    try:
        user_id = decode_access_token(credentials.credentials)
    except JWTError:
        raise AuthError()

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise AuthError()

    return user


# Convenience aliases
CurrentUser = Annotated[object, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_db)]
