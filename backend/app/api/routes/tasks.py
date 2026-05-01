from fastapi import APIRouter, Depends

from backend.app.api.deps import current_user, rate_limit
from backend.app.schemas.email import TaskRequest, TaskResponse
from backend.app.services.inference import InferenceService
from backend.app.services.preprocessor import EmailPreprocessor

router = APIRouter()
preprocessor = EmailPreprocessor()
inference = InferenceService()


@router.post("/tasks", response_model=TaskResponse, dependencies=[Depends(rate_limit)])
async def extract_tasks(payload: TaskRequest, user: dict[str, str] = Depends(current_user)) -> TaskResponse:
    cleaned = preprocessor.clean(payload.email_text)
    return await inference.tasks(cleaned, user_id=user["sub"])
