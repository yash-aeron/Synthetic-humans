from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class FrictionFindingRead(BaseModel):
    id: str
    experiment_id: str
    severity: str
    category: str
    title: str
    description: str
    evidence: Dict[str, Any]
    recommendation: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExperimentMetricsRead(BaseModel):
    id: str
    experiment_id: str
    task_completion_rate: float
    task_abandonment_rate: float
    average_task_duration: float
    median_task_duration: float
    p95_task_duration: float
    average_actions: float
    average_errors: float
    retry_rate: float
    back_navigation_rate: float
    dead_end_rate: float
    confusion_rate: float
    time_to_first_successful_action: float
    segment_metrics: Dict[str, Any]
    funnel_steps: List[Dict[str, Any]]
    heatmap_data: List[Dict[str, Any]]
    action_distribution: Dict[str, Any]
    total_llm_calls: int
    estimated_tokens_used: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExperimentComparisonRead(BaseModel):
    id: str
    baseline_experiment_id: str
    variant_experiment_id: str
    completion_rate_delta: float
    duration_delta: float
    error_delta: float
    abandonment_delta: float
    segment_deltas: Dict[str, Any]
    summary: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExperimentDetailResponse(BaseModel):
    experiment: Any
    metrics: Optional[ExperimentMetricsRead] = None
    findings: List[FrictionFindingRead] = []
