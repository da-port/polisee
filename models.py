import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
