from fastapi import APIRouter, Depends

from backend.app.api.deps import current_user, rate_limit
from backend.app.schemas.email import ClassifyRequest, ClassifyResponse
from backend.app.services.classifier import HeuristicEmailClassifier

router = APIRouter()
classifier = HeuristicEmailClassifier()


@router.post("/classify", response_model=ClassifyResponse, dependencies=[Depends(rate_limit)])
async def classify_email(
    payload: ClassifyRequest,
    user: dict[str, str] = Depends(current_user),
) -> ClassifyResponse:
    result = classifier.classify(payload.email_text)
    return ClassifyResponse(label=result.label, score=result.score, model_version=result.model_version)
