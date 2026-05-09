from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from arkhe_os.db.session import Base

class Intention(Base):
    __tablename__ = "intentions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    intention_text = Column(String, nullable=False)
    target_branch = Column(String)
    resonance_score = Column(Float)
    status = Column(String) # queued, manifest, requires_review
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CoherenceLog(Base):
    __tablename__ = "coherence_logs"
    id = Column(Integer, primary_key=True, index=True)
    coherence_M = Column(Float, nullable=False)
    phase_rad = Column(Float)
    turbulence = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
