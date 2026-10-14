import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_url = Column(String(1024), nullable=False)
    population_size = Column(Integer, nullable=False, default=10)
    task_definition = Column(JSON, nullable=False)
    population_distributions = Column(JSON, nullable=True)
    max_steps_per_user = Column(Integer, nullable=False, default=30)
    max_duration_seconds = Column(Integer, nullable=False, default=180)
    concurrency = Column(Integer, nullable=False, default=5)
    random_seed = Column(Integer, nullable=False, default=42)
    model_configuration = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="CREATED")
    is_authorized = Column(Boolean, nullable=False, default=True)
    allowed_origins = Column(JSON, nullable=False, default=list)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    synthetic_users = relationship("SyntheticUser", back_populates="experiment", cascade="all, delete-orphan")
    trajectories = relationship("TrajectoryStep", back_populates="experiment", cascade="all, delete-orphan")
    metrics = relationship("ExperimentMetrics", back_populates="experiment", uselist=False, cascade="all, delete-orphan")
    findings = relationship("FrictionFinding", back_populates="experiment", cascade="all, delete-orphan")
