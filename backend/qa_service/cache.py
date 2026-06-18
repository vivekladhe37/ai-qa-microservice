import hashlib
import html
import logging
import os

import redis
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CACHE_TTL = 3600  # 1 hour

redis_client = redis.from_url(os.getenv("REDIS_URL"))


def get_cache_key(question: str) -> str:
    return f"qa:{hashlib.sha256(question.lower().strip().encode()).hexdigest()}"


def get_cached_answer(question: str) -> str | None:
    try:
        key = get_cache_key(question)
        cached = redis_client.get(key)
        if cached:
            logger.info("Cache hit for question")
            return html.escape(cached.decode("utf-8"))
        logger.info("Cache miss for question")
        return None
    except Exception as e:
        logger.warning(f"Redis get failed: {e}")
        return None


def set_cached_answer(question: str, answer: str) -> None:
    try:
        key = get_cache_key(question)
        redis_client.setex(key, CACHE_TTL, answer)
        logger.info("Answer cached successfully")
    except Exception as e:
        logger.warning(f"Redis set failed: {e}")
