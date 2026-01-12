import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment (works on Railway, Replit, and local)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Railway Postgres URLs may start with postgres:// but SQLAlchemy needs postgresql://
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Converted postgres:// to postgresql:// for SQLAlchemy compatibility")

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set!")
    raise ValueError("DATABASE_URL environment variable is required")

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    analyses = relationship("PolicyAnalysisResult", back_populates="user")


class PolicyAnalysisResult(Base):
    __tablename__ = "policy_analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    scenario = Column(Text, nullable=False)
    file_id = Column(Text, nullable=False)
    openai_response_json = Column(Text)
    out_of_pocket_estimate = Column(Numeric)
    gap_alerts = Column(Text)
    
    user = relationship("User", back_populates="analyses")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
