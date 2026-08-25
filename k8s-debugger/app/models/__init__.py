from pydantic import BaseModel
from typing import Optional
from enum import Enum


class PodPhase(str, Enum):
    PENDING = "Pending"
    RUNNING = "Running"
    SUCCEEDED = "Succeeded"
    FAILED = "Failed"
    UNKNOWN = "Unknown"


class ContainerStatus(BaseModel):
    name: str
    ready: bool
    restart_count: int
    image: str
    state: Optional[str] = None
    last_state: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None


class PodEvent(BaseModel):
    type: str
    reason: str
    message: str
    age: str
    field_path: Optional[str] = None


class PodLog(BaseModel):
    container: str
    logs: str
    truncated: bool = False


class RootCauseAnalysis(BaseModel):
    root_cause: str
    category: str
    confidence: int
    explanation: str
    suggested_fixes: list[str]
    related_events: list[str]


class DebugRequest(BaseModel):
    namespace: str
    pod_name: Optional[str] = None
    label_selector: Optional[str] = None
    container: Optional[str] = None
    tail_lines: int = 100
    model_alias: str = "ollama"


class DebugResponse(BaseModel):
    namespace: str
    pod_name: str
    phase: PodPhase
    container_statuses: list[ContainerStatus]
    events: list[PodEvent]
    logs: list[PodLog]
    root_cause_analysis: Optional[RootCauseAnalysis] = None
    model_used: str
