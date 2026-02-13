import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from core.database import get_session
from app import app

# Use in-memory SQLite with StaticPool so all connections share the same DB
TEST_ENGINE = create_engine(
    "sqlite://",
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def get_test_session():
    with Session(TEST_ENGINE) as session:
        yield session


@pytest.fixture(autouse=True)
def setup_db():
    """Create fresh tables for every test."""
    SQLModel.metadata.create_all(TEST_ENGINE)
    yield
    SQLModel.metadata.drop_all(TEST_ENGINE)


@pytest.fixture
def client():
    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_header(client):
    """Signup a test user and return the auth header."""
    resp = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
