import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, get_db
from models import Base

# Use in-memory SQLite for tests — no real Postgres needed
TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "auth-service"}


def test_signup_success():
    response = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert "id" in response.json()


def test_signup_duplicate_email():
    client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    response = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_signup_invalid_email():
    response = client.post("/auth/signup", json={
        "email": "notanemail",
        "password": "testpassword123"
    })
    assert response.status_code == 422


def test_signup_short_password():
    response = client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "short"
    })
    assert response.status_code == 422


def test_login_success():
    client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password():
    client.post("/auth/signup", json={
        "email": "test@example.com",
        "password": "testpassword123"
    })
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_login_nonexistent_user():
    response = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "testpassword123"
    })
    assert response.status_code == 401
