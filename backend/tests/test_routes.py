from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.core.config import settings


client = TestClient(app)


def test_health() -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_root_route() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"


def test_metrics_route() -> None:
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "ai_email_api_requests_total" in response.text


def test_demo_token_route() -> None:
    response = client.post("/api/auth/demo-token")
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_summarize_route() -> None:
    old_local_enabled = settings.hf_local_enabled
    old_provider_enabled = settings.hf_use_provider
    settings.hf_local_enabled = False
    settings.hf_use_provider = False
    try:
        response = client.post(
            "/api/summarize",
            json={"email_text": "Please review the updated route test proposal by EOD and confirm next steps."},
        )
    finally:
        settings.hf_local_enabled = old_local_enabled
        settings.hf_use_provider = old_provider_enabled
    assert response.status_code == 200
    body = response.json()
    assert len(body["bullets"]) == 3
    assert body["model_version"] == "local-extractive-summarizer-v1"


def test_tasks_route_extracts_action_and_deadline() -> None:
    response = client.post(
        "/api/tasks",
        json={"email_text": "Please send the revised proposal by Friday. Can you confirm the meeting time tomorrow?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["model_version"] == "heuristic-task-extractor-v1"
    assert body["tasks"][0]["deadline"].lower() == "by friday"


def test_classify_route() -> None:
    response = client.post(
        "/api/classify",
        json={"email_text": "Urgent: please review the launch proposal by EOD."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["label"] == "urgent"
    assert body["score"] >= 0.55
    assert body["model_version"] == "heuristic-classifier-v3"


def test_feedback_route() -> None:
    response = client.post(
        "/api/feedback",
        json={
            "email_text": "Please review this by EOD.",
            "generated_reply": "Thanks. I will review and follow up.",
            "rating": "up",
        },
    )
    assert response.status_code == 202
    assert response.json()["feedback_count"] >= 1


def test_usage_routes() -> None:
    recorded = client.post("/api/users/me/usage", json={"feature": "summarize"})
    assert recorded.status_code == 200
    assert recorded.json()["processed_today"] >= 1

    stats = client.get("/api/users/me/usage")
    assert stats.status_code == 200
    assert stats.json()["most_used_feature"]


def test_preferences_are_saved() -> None:
    response = client.post(
        "/api/users/me/preferences",
        json={"tone": "concise", "model_version": "test-model"},
    )
    assert response.status_code == 200
    assert response.json()["tone"] == "concise"

    saved = client.get("/api/users/me/preferences")
    assert saved.status_code == 200
    assert saved.json()["model_version"] == "test-model"


def test_gdpr_delete_removes_user_data() -> None:
    response = client.delete("/api/users/me")
    assert response.status_code == 202
    assert response.json()["status"] == "delete_requested"

    preferences = client.get("/api/users/me/preferences")
    assert preferences.status_code == 200
    assert preferences.json()["tone"] == "formal"
