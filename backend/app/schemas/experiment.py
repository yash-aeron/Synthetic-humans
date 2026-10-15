from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TaskCondition(BaseModel):
    type: str = Field(..., description="Condition type: url_contains, text_present, element_visible, url_matches")
    value: str = Field(..., description="Target value or selector or text")
    description: Optional[str] = None

class TaskDefinition(BaseModel):
    goal: str = Field(..., description="High-level user goal, e.g. Purchase a laptop")
    success_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="All required success conditions")
    optional_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Bonus / optional conditions")
    failure_conditions: List[Dict[str, Any]] = Field(default_factory=list, description="Explicit failure triggers")

class ModelConfigSchema(BaseModel):
    provider: str = Field(default="mock", description="mock, openai, or gemini")
    model_name: Optional[str] = "default"
    temperature: float = 0.2
    max_tokens: int = 500

class ExperimentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target_url: str = Field(..., description="Target web application URL")
    description: Optional[str] = None
    population_size: int = Field(default=10, ge=1, le=10000)
    task_definition: TaskDefinition
    population_distributions: Optional[Dict[str, Dict[str, float]]] = None
    max_steps_per_user: int = Field(default=30, ge=1, le=200)
    max_duration_seconds: int = Field(default=180, ge=5, le=1800)
    concurrency: int = Field(default=5, ge=1, le=50)
    random_seed: int = Field(default=42)
    model_configuration: Optional[Dict[str, Any]] = Field(default_factory=dict)
    is_authorized: bool = Field(default=True, description="Explicit authorization confirmation")
    allowed_origins: Optional[List[str]] = None

class ExperimentCreate(ExperimentBase):
    pass

class ExperimentRead(ExperimentBase):
    id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    completed_users_count: Optional[int] = 0
    abandoned_users_count: Optional[int] = 0
    failed_users_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class ExperimentRunRequest(BaseModel):
    concurrency: Optional[int] = None
    random_seed: Optional[int] = None
    provider: Optional[str] = None
