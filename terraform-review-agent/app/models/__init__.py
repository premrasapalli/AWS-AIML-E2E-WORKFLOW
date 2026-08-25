from pydantic import BaseModel
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TerraformChange(BaseModel):
    file: str
    resource_type: str
    resource_name: str
    change_type: str
    before: Optional[dict] = None
    after: Optional[dict] = None


class SecurityFinding(BaseModel):
    rule_id: str
    severity: RiskLevel
    resource: str
    message: str
    remediation: Optional[str] = None


class AIAnalysis(BaseModel):
    summary: str
    risk_score: int
    risk_level: RiskLevel
    findings: list[SecurityFinding]
    recommendations: list[str]


class ReviewRequest(BaseModel):
    repo_path: str
    pr_number: Optional[int] = None
    branch: Optional[str] = None
    model_alias: str = "ollama"


class ReviewResponse(BaseModel):
    changes: list[TerraformChange]
    terrascan_results: list[SecurityFinding]
    ai_analysis: AIAnalysis
    model_used: str
