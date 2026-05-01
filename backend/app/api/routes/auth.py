from datetime import timedelta

from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.core.security import create_token
from backend.app.schemas.auth import TokenResponse

router = APIRouter()


@router.post("/auth/demo-token", response_model=TokenResponse)
async def demo_token() -> TokenResponse:
    expires_in = 30 * 60
    token = create_token(settings.demo_auth_subject, expires_delta=timedelta(seconds=expires_in))
    return TokenResponse(access_token=token, expires_in=expires_in)
