import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
import os

from models import Base
from schemas import SignupRequest, LoginRequest, TokenResponse, UserResponse
from services import create_user, authenticate_user, create_access_token

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Auth Service...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    yield
    logger.info("Shutting down Auth Service...")


app = FastAPI(
    title="Auth Service",
    description="JWT-based authentication microservice",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}


@app.post("/auth/signup", response_model=UserResponse)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    try:
        user = create_user(db, request.email, request.password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = authenticate_user(db, request.email, request.password)
        token = create_access_token({"user_id": user.id, "email": user.email})
        return TokenResponse(access_token=token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
