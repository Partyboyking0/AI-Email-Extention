import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.models.user import Base
from backend.app.main import app
from backend.app.api.deps import db_session

# In-memory SQLite, single shared connection across all tests
TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)


def override_db_session():
    """Drop-in replacement for the db_session FastAPI dependency."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    # Create all tables once before any test runs
    Base.metadata.create_all(bind=TEST_ENGINE)
    # Route all DB calls to the in-memory test database
    app.dependency_overrides[db_session] = override_db_session

    yield

    Base.metadata.drop_all(bind=TEST_ENGINE)
    app.dependency_overrides.clear()