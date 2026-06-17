import logging
import os

from groq import Groq
from sqlalchemy.orm import Session

from models import Question

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant. Answer questions clearly and concisely."""


def get_answer(question: str, user_id: int, db: Session) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("Sending question to Groq LLM")
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    answer = response.choices[0].message.content
    logger.info("Received answer from Groq LLM")
    db_question = Question(user_id=user_id, question_text=question, answer_text=answer)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return answer


def get_history(user_id: int, db: Session) -> list[Question]:
    return db.query(Question).filter(Question.user_id == user_id).order_by(Question.created_at.desc()).all()
