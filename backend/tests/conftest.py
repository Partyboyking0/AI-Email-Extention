import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_session
from backend.app.main import app

# In-memory SQLite — shared across the same connection (StaticPool)
TEST_DATABASE_URL = "sqlite://"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def override_get_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables once for the entire test session."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_session] = override_get_session
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()