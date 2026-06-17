import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db, engine
from models import Base, Question
from services import get_answer, get_history
from auth import verify_token

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting QA Service...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down QA Service...")


app = FastAPI(
    title="QA Service",
    description="AI-powered Q&A microservice",
    version="0.1.0",
    lifespan=lifespan,
)


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str


class HistoryItem(BaseModel):
    id: int
    question_text: str
    answer_text: str
    created_at: str

    class Config:
        from_attributes = True


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qa-service"}


@app.post("/qa/ask", response_model=AnswerResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    sanitized_question = request.question.replace("\n", " ").replace("\r", " ")
    logger.info(f"Received question from user {current_user.get('user_id')}: {sanitized_question}")
    try:
        answer = get_answer(request.question, current_user.get("user_id"), db)
        return AnswerResponse(question=request.question, answer=answer)
    except Exception as e:
        logger.error(f"Error getting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to get answer from LLM")


@app.get("/qa/history", response_model=list[HistoryItem])
async def get_question_history(
    current_user: dict = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("user_id")
    logger.info(f"Fetching history for user {user_id}")
    history = get_history(user_id, db)
    return [
        HistoryItem(
            id=q.id,
            question_text=q.question_text,
            answer_text=q.answer_text,
            created_at=q.created_at.isoformat(),
        )
        for q in history
    ]
