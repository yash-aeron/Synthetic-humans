import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class TrajectoryStep(Base):
    __tablename__ = "trajectories"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    synthetic_user_id = Column(String(36), ForeignKey("synthetic_users.id", ondelete="CASCADE"), nullable=False, index=True)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)

    step_number = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    url = Column(String(1024), nullable=False)
    page_title = Column(String(512), nullable=False, default="")
    visible_text_summary = Column(Text, nullable=False, default="")
    interactive_elements_count = Column(Integer, nullable=False, default=0)
    screenshot_path = Column(String(1024), nullable=True)

    # Action executed
    action_type = Column(String(32), nullable=False) # CLICK, TYPE, SELECT, SCROLL, PRESS_KEY, GO_BACK, WAIT, ABANDON
    action_target = Column(String(512), nullable=False, default="")
    action_parameters = Column(JSON, nullable=False, default=dict)
    action_reason = Column(Text, nullable=False, default="")
    action_confidence = Column(Float, nullable=False, default=1.0)

    # Outcome
    action_result = Column(String(32), nullable=False, default="SUCCESS") # SUCCESS, FAILED, NOOP
    resulting_url = Column(String(1024), nullable=False, default="")
    resulting_page_state = Column(JSON, nullable=False, default=dict)
    frustration_after = Column(Float, nullable=False, default=0.0)
    confidence_after = Column(Float, nullable=False, default=1.0)
    latency_ms = Column(Float, nullable=False, default=0.0)
    error_message = Column(Text, nullable=True)

    # Relationships
    synthetic_user = relationship("SyntheticUser", back_populates="trajectories")
    experiment = relationship("Experiment", back_populates="trajectories")
