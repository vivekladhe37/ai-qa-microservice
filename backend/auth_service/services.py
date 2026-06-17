import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from models import User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expiry = datetime.now(timezone.utc) + timedelta(
        minutes=int(os.getenv("JWT_EXPIRY_MINUTES", 30))
    )
    payload.update({"exp": expiry})
    return jwt.encode(
        payload,
        os.getenv("JWT_SECRET_KEY"),
        algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        os.getenv("JWT_SECRET_KEY"),
        algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
    )



def create_user(db: Session, email: str, password: str) -> User:
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("Email already registered")
    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User created with email: {email}")
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password")
    logger.info(f"User authenticated: {email}")
    return user
