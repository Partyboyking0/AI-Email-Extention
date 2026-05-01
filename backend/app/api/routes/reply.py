from fastapi import APIRouter, Depends

from backend.app.api.deps import current_user, rate_limit
from backend.app.schemas.email import ReplyRequest, ReplyResponse
from backend.app.services.inference import InferenceService
from backend.app.services.preprocessor import EmailPreprocessor

router = APIRouter()
preprocessor = EmailPreprocessor()
inference = InferenceService()


@router.post("/reply", response_model=ReplyResponse, dependencies=[Depends(rate_limit)])
async def generate_reply(payload: ReplyRequest, user: dict[str, str] = Depends(current_user)) -> ReplyResponse:
    cleaned = preprocessor.clean(payload.email_text)
    return await inference.reply(cleaned, payload.tone, user_id=user["sub"])
