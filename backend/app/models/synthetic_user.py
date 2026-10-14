import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class SyntheticUser(Base):
    __tablename__ = "synthetic_users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core Behavioral & Demographic Attributes
    demographic_attributes = Column(JSON, nullable=False, default=dict)
    technical_proficiency = Column(String(32), nullable=False, default="INTERMEDIATE") # BEGINNER, INTERMEDIATE, EXPERT
    patience = Column(Float, nullable=False, default=0.5) # 0.0 - 1.0
    risk_tolerance = Column(Float, nullable=False, default=0.5) # 0.0 - 1.0
    goal_orientation = Column(Float, nullable=False, default=0.7) # 0.0 - 1.0
    reading_behavior = Column(String(32), nullable=False, default="SCANNER") # SCANNER, THOROUGH, SELECTIVE
    error_tolerance = Column(Float, nullable=False, default=0.5) # 0.0 - 1.0
    familiarity_level = Column(String(32), nullable=False, default="NONE") # NONE, LOW, MEDIUM, HIGH

    # Environment profiles
    device_profile = Column(JSON, nullable=False, default=dict)
    network_profile = Column(JSON, nullable=False, default=dict)
    personality_traits = Column(JSON, nullable=False, default=dict)

    # Persistent Cognitive & Affective State
    knowledge_state = Column(JSON, nullable=False, default=dict)
    memory_state = Column(JSON, nullable=False, default=dict)
    current_goal = Column(Text, nullable=False, default="")
    current_subgoal = Column(Text, nullable=False, default="")
    frustration_level = Column(Float, nullable=False, default=0.0)
    confidence_level = Column(Float, nullable=False, default=1.0)
    action_history = Column(JSON, nullable=False, default=list)

    # Execution tracking
    status = Column(String(32), nullable=False, default="PENDING") # PENDING, RUNNING, COMPLETED, ABANDONED, FAILED, TIMEOUT
    steps_taken = Column(Integer, nullable=False, default=0)
    duration_seconds = Column(Float, nullable=False, default=0.0)
    error_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    experiment = relationship("Experiment", back_populates="synthetic_users")
    trajectories = relationship("TrajectoryStep", back_populates="synthetic_user", cascade="all, delete-orphan", order_by="TrajectoryStep.step_number")
