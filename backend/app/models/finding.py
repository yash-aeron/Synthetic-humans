import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

def utc_now():
    return datetime.now(timezone.utc)

class FrictionFinding(Base):
    __tablename__ = "friction_findings"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)

    severity = Column(String(16), nullable=False, default="MEDIUM") # HIGH, MEDIUM, LOW
    category = Column(String(64), nullable=False) # DEAD_END, NAVIGATION_LOOP, UNNOTICED_ACTION, CONFUSING_FORM, MISCLICK, ABANDONMENT_HOTSPOT
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    evidence = Column(JSON, nullable=False, default=dict)
    recommendation = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    experiment = relationship("Experiment", back_populates="findings")

class ExperimentComparison(Base):
    __tablename__ = "experiment_comparisons"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    baseline_experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    variant_experiment_id = Column(String(36), ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True)

    completion_rate_delta = Column(Float, nullable=False, default=0.0)
    duration_delta = Column(Float, nullable=False, default=0.0)
    error_delta = Column(Float, nullable=False, default=0.0)
    abandonment_delta = Column(Float, nullable=False, default=0.0)
    segment_deltas = Column(JSON, nullable=False, default=dict)
    summary = Column(Text, nullable=False, default="")

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
