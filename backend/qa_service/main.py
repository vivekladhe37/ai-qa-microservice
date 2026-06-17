import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from dotenv import load_dotenv

from services import get_answer
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "qa-service"}


@app.post("/qa/ask", response_model=AnswerResponse)
async def ask_question(request: QuestionRequest, current_user: dict = Depends(verify_token)):
    sanitized_question = request.question.replace("\n", " ").replace("\r", " ")
    logger.info(f"Received question from user {current_user.get('user_id')}: {sanitized_question}")
    try:
        answer = get_answer(request.question)
        return AnswerResponse(question=request.question, answer=answer)
    except Exception as e:
        logger.error(f"Error getting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to get answer from LLM")
