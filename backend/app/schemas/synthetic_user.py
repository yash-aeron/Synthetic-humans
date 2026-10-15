from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TrajectoryStepRead(BaseModel):
    id: str
    synthetic_user_id: str
    experiment_id: str
    step_number: int
    timestamp: datetime
    url: str
    page_title: str
    visible_text_summary: str
    interactive_elements_count: int
    screenshot_path: Optional[str] = None
    action_type: str
    action_target: str
    action_parameters: Dict[str, Any]
    action_reason: str
    action_confidence: float
    action_result: str
    resulting_url: str
    resulting_page_state: Dict[str, Any]
    frustration_after: float
    confidence_after: float
    latency_ms: float
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class SyntheticUserRead(BaseModel):
    id: str
    experiment_id: str
    demographic_attributes: Dict[str, Any]
    technical_proficiency: str
    patience: float
    risk_tolerance: float
    goal_orientation: float
    reading_behavior: str
    error_tolerance: float
    familiarity_level: str
    device_profile: Dict[str, Any]
    network_profile: Dict[str, Any]
    personality_traits: Dict[str, Any]
    knowledge_state: Dict[str, Any]
    memory_state: Dict[str, Any]
    current_goal: str
    current_subgoal: str
    frustration_level: float
    confidence_level: float
    status: str
    steps_taken: int
    duration_seconds: float
    error_count: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class SyntheticUserDetail(SyntheticUserRead):
    trajectories: List[TrajectoryStepRead] = []
