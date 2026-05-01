from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.database import session_scope
from backend.app.core.security import decode_token
from backend.app.core.config import settings


async def current_user(authorization: str | None = Header(default=None)) -> dict[str, str]:
    if not authorization:
        return {"sub": settings.demo_auth_subject}

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")

    return decode_token(token)


async def rate_limit(request: Request, user: dict[str, str] = Depends(current_user)) -> None:
    limiter = getattr(request.app.state, "rate_limiter", None)
    if limiter is not None:
        await limiter.check(user["sub"])


def db_session() -> Session:
    with session_scope() as session:
        yield session
