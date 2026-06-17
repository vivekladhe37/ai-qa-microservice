import logging
import os

from groq import Groq

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a helpful assistant. Answer questions clearly and concisely."""


def get_answer(question: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    logger.info("Sending question to Groq LLM")
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    answer = response.choices[0].message.content
    logger.info("Received answer from Groq LLM")
    return answer