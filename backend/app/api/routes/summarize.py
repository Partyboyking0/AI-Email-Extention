from fastapi import APIRouter, Depends

from backend.app.api.deps import current_user, rate_limit
from backend.app.schemas.email import SummarizeRequest, SummaryResponse
from backend.app.services.inference import InferenceService
from backend.app.services.preprocessor import EmailPreprocessor

router = APIRouter()
preprocessor = EmailPreprocessor()
inference = InferenceService()


@router.post("/summarize", response_model=SummaryResponse, dependencies=[Depends(rate_limit)])
async def summarize_email(payload: SummarizeRequest, user: dict[str, str] = Depends(current_user)) -> SummaryResponse:
    cleaned = preprocessor.clean(payload.email_text)
    return await inference.summarize(cleaned, user_id=user["sub"])
