from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.deps import current_user, db_session
from backend.app.schemas.users import FeedbackRequest, PreferenceRequest, PreferenceResponse, UsageRequest, UsageStatsResponse
from backend.app.services.users import UserService

router = APIRouter()


@router.get("/users/me/preferences", response_model=PreferenceResponse)
async def get_preferences(
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> PreferenceResponse:
    return UserService(session).get_preferences(user["sub"])


@router.post("/users/me/preferences", response_model=PreferenceResponse)
async def save_preferences(
    payload: PreferenceRequest,
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> PreferenceResponse:
    return UserService(session).save_preferences(user["sub"], payload)


@router.post("/feedback", status_code=status.HTTP_202_ACCEPTED)
async def save_feedback(
    payload: FeedbackRequest,
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> dict[str, str | int]:
    feedback_count = UserService(session).save_feedback(user["sub"], payload)
    return {"status": "accepted", "user_id": user["sub"], "rating": payload.rating, "feedback_count": feedback_count}


@router.get("/users/me/usage", response_model=UsageStatsResponse)
async def get_usage(
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> UsageStatsResponse:
    return UserService(session).usage_stats(user["sub"])


@router.post("/users/me/usage", response_model=UsageStatsResponse)
async def record_usage(
    payload: UsageRequest,
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> UsageStatsResponse:
    return UserService(session).record_usage(user["sub"], payload)


@router.delete("/users/me/usage", response_model=UsageStatsResponse)
async def reset_usage(
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> UsageStatsResponse:
    return UserService(session).reset_usage(user["sub"])


@router.delete("/users/me", status_code=status.HTTP_202_ACCEPTED)
async def gdpr_delete(
    user: dict[str, str] = Depends(current_user),
    session: Session = Depends(db_session),
) -> dict[str, str]:
    UserService(session).delete_user_data(user["sub"])
    return {"status": "delete_requested", "user_id": user["sub"]}
