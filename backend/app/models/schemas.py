from pydantic import BaseModel, Field, HttpUrl
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class TargetType(str, Enum):
    openai = "openai"
    azure_openai = "azure_openai"
    ollama = "ollama"
    huggingface = "huggingface"
    custom_rest = "custom_rest"
    anthropic = "anthropic"


class TargetConfig(BaseModel):
    type: TargetType = TargetType.openai
    model_name: str = "gpt-4o-mini"
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    extra_headers: Dict[str, str] = Field(default_factory=dict)
    # For custom REST
    request_template: Optional[Dict[str, Any]] = None
    response_path: Optional[str] = "choices.0.message.content"


class ScanRequest(BaseModel):
    target_name: str = Field(..., min_length=1, max_length=255)
    target: TargetConfig
    tools: List[str] = Field(
        default=["garak", "deepteam"],
        description="Tools to run: garak, deepteam, pyrit, promptmap, llmfuzzer, ..."
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool-specific options, e.g. {'garak': {'probes': 'encoding,dan'}, 'deepteam': {'framework': 'OWASPTop10'}}"
    )


class JobSummary(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: str
    status: JobStatus
    target_name: str
    tools_selected: List[str]
    progress: Dict[str, Any] = {}
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class JobDetail(JobSummary):
    target_config: Dict[str, Any]
    options: Dict[str, Any]
    results: List[Dict[str, Any]] = []


class ConsolidatedReport(BaseModel):
    job_id: uuid.UUID
    target_name: str
    generated_at: datetime
    overall_risk: str  # low / medium / high / critical
    summary: str
    tool_results: Dict[str, Any]
    recommendations: List[str] = []
