import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class ExperimentMetrics(Base):
    __tablename__ = "experiment_metrics"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    task_completion_rate = Column(Float, nullable=False, default=0.0)
    task_abandonment_rate = Column(Float, nullable=False, default=0.0)
    average_task_duration = Column(Float, nullable=False, default=0.0)
    median_task_duration = Column(Float, nullable=False, default=0.0)
    p95_task_duration = Column(Float, nullable=False, default=0.0)
    average_actions = Column(Float, nullable=False, default=0.0)
    average_errors = Column(Float, nullable=False, default=0.0)
    retry_rate = Column(Float, nullable=False, default=0.0)
    back_navigation_rate = Column(Float, nullable=False, default=0.0)
    dead_end_rate = Column(Float, nullable=False, default=0.0)
    confusion_rate = Column(Float, nullable=False, default=0.0)
    time_to_first_successful_action = Column(Float, nullable=False, default=0.0)

    # Segment breakdowns
    segment_metrics = Column(JSON, nullable=False, default=dict)
    funnel_steps = Column(JSON, nullable=False, default=list)
    heatmap_data = Column(JSON, nullable=False, default=list)
    action_distribution = Column(JSON, nullable=False, default=dict)

    total_llm_calls = Column(Integer, nullable=False, default=0)
    estimated_tokens_used = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    experiment = relationship("Experiment", back_populates="metrics")
