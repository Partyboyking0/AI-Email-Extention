from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.routes import auth, classify, reply, summarize, tasks, users
from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.core.metrics import MetricsMiddleware, metrics_response
from backend.app.core.observability import init_observability
from backend.app.core.rate_limit import SlidingWindowRateLimiter

init_observability()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="AI Email Automation Assistant API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["POST", "GET", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
app.add_middleware(MetricsMiddleware)

app.include_router(summarize.router, prefix="/api", tags=["summarize"])
app.include_router(reply.router, prefix="/api", tags=["reply"])
app.include_router(classify.router, prefix="/api", tags=["classify"])
app.include_router(tasks.router, prefix="/api", tags=["tasks"])
app.include_router(users.router, prefix="/api", tags=["users"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.state.rate_limiter = SlidingWindowRateLimiter(redis_url=settings.redis_url)


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "AI Email Automation Assistant API", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
async def metrics() -> Response:
    return metrics_response()
