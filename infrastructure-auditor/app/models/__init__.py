from pydantic import BaseModel
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class FileType(str, Enum):
    KUBERNETES = "kubernetes"
    DOCKER_COMPOSE = "docker_compose"
    TERRAFORM = "terraform"
    UNKNOWN = "unknown"


class SecurityIssue(BaseModel):
    rule_id: str
    severity: RiskLevel
    file_path: str
    resource_type: str
    resource_name: str
    message: str
    line_number: Optional[int] = None
    remediation: Optional[str] = None


class AIExplanation(BaseModel):
    issue_id: str
    explanation: str
    impact: str
    fix_suggestion: str
    compliance_references: list[str]


class AuditResult(BaseModel):
    file_path: str
    file_type: FileType
    issues: list[SecurityIssue]
    ai_explanations: list[AIExplanation]
    risk_score: int
    risk_level: RiskLevel


class AuditRequest(BaseModel):
    path: str
    file_type: Optional[FileType] = None
    model_alias: str = "ollama"
    include_ai_explanations: bool = True


class AuditResponse(BaseModel):
    results: list[AuditResult]
    summary: dict
    model_used: str
