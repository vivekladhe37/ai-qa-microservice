import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from main import app
from database import get_db
from models import Base

TEST_DATABASE_URL = "sqlite:///./test_qa.db"
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

MOCK_TOKEN_PAYLOAD = {"user_id": 1, "email": "test@example.com"}


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "qa-service"}


def test_ask_question_without_token():
    response = client.post("/qa/ask", json={"question": "What is Python?"})
    assert response.status_code == 401


def test_ask_question_with_invalid_token():
    response = client.post(
        "/qa/ask",
        json={"question": "What is Python?"},
        headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401


def test_ask_question_success():
    with patch("services.get_cached_answer", return_value=None), \
         patch("services.Groq") as mock_groq, \
         patch("services.set_cached_answer"), \
         patch("auth.jwt.decode", return_value=MOCK_TOKEN_PAYLOAD):

        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[0].message.content = "Python is a programming language."

        response = client.post(
            "/qa/ask",
            json={"question": "What is Python?"},
            headers={"Authorization": "Bearer validtoken"}
        )
        assert response.status_code == 200
        assert response.json()["answer"] == "Python is a programming language."
        assert response.json()["question"] == "What is Python?"


def test_get_history_without_token():
    response = client.get("/qa/history")
    assert response.status_code == 401


def test_get_history_empty():
    with patch("auth.jwt.decode", return_value=MOCK_TOKEN_PAYLOAD):
        response = client.get(
            "/qa/history",
            headers={"Authorization": "Bearer validtoken"}
        )
        assert response.status_code == 200
        assert response.json() == []


def test_get_history_with_data():
    with patch("services.get_cached_answer", return_value=None), \
         patch("services.Groq") as mock_groq, \
         patch("services.set_cached_answer"), \
         patch("auth.jwt.decode", return_value=MOCK_TOKEN_PAYLOAD):

        mock_client = MagicMock()
        mock_groq.return_value = mock_client
        mock_client.chat.completions.create.return_value.choices[0].message.content = "Python is a programming language."

        client.post(
            "/qa/ask",
            json={"question": "What is Python?"},
            headers={"Authorization": "Bearer validtoken"}
        )

        response = client.get(
            "/qa/history",
            headers={"Authorization": "Bearer validtoken"}
        )
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["question_text"] == "What is Python?"
