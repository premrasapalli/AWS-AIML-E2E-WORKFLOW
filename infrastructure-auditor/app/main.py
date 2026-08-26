import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import AuditRequest, AuditResponse, AuditResult, FileType, RiskLevel
from .scanners.k8s_scanner import K8sScanner
from .scanners.docker_scanner import DockerScanner
from .scanners.terraform_scanner import TerraformScanner
from .ai.bedrock_explainer import BedrockExplainer
from shared.report_generator import ReportGenerator

app = FastAPI(title="AI Infrastructure Auditor", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

k8s_scanner = K8sScanner()
docker_scanner = DockerScanner()
terraform_scanner = TerraformScanner()
report_gen = ReportGenerator("infrastructure-auditor")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "infrastructure-auditor"}


@app.post("/audit", response_model=AuditResponse)
async def audit_infrastructure(request: AuditRequest):
    all_results = []
    explainer = BedrockExplainer(model_alias=request.model_alias) if request.include_ai_explanations else None

    try:
        if request.file_type == FileType.KUBERNETES or request.file_type is None:
            issues = k8s_scanner.scan_directory(request.path)
            if issues:
                all_results.append(_create_result(request.path, FileType.KUBERNETES, issues, explainer))

        if request.file_type == FileType.DOCKER_COMPOSE or request.file_type is None:
            issues = docker_scanner.scan_directory(request.path)
            if issues:
                all_results.append(_create_result(request.path, FileType.DOCKER_COMPOSE, issues, explainer))

        if request.file_type == FileType.TERRAFORM or request.file_type is None:
            issues = terraform_scanner.scan_directory(request.path)
            if issues:
                all_results.append(_create_result(request.path, FileType.TERRAFORM, issues, explainer))

        summary = _generate_summary(all_results)
        status = "success"
        suggestions = _generate_suggestions(summary, all_results)
    except Exception as e:
        summary = {"error": str(e)}
        status = "failed"
        suggestions = ["Fix the underlying error before running again"]

    report_path = report_gen.generate_report(
        status=status,
        implemented_correctly=_get_implemented(summary, all_results),
        improvements_needed=suggestions,
    )

    return AuditResponse(
        results=all_results,
        summary=summary,
        model_used=request.model_alias,
    )


def _create_result(path: str, file_type: FileType, issues: list, explainer=None) -> AuditResult:
    ai_explanations = []
    if explainer:
        for issue in issues[:10]:
            ai_explanations.append(explainer.explain_issue(issue))

    severity_scores = {"critical": 100, "high": 75, "medium": 50, "low": 25, "info": 10}
    max_score = max([severity_scores.get(i.severity.value, 0) for i in issues]) if issues else 0

    return AuditResult(
        file_path=path,
        file_type=file_type,
        issues=issues,
        ai_explanations=ai_explanations,
        risk_score=min(100, max_score),
        risk_level=RiskLevel("critical" if max_score >= 90 else "high" if max_score >= 70 else "medium" if max_score >= 40 else "low"),
    )


def _generate_summary(results: list[AuditResult]) -> dict:
    total_issues = sum(len(r.issues) for r in results)
    critical = sum(1 for r in results for i in r.issues if i.severity == RiskLevel.CRITICAL)
    high = sum(1 for r in results for i in r.issues if i.severity == RiskLevel.HIGH)
    medium = sum(1 for r in results for i in r.issues if i.severity == RiskLevel.MEDIUM)
    low = sum(1 for r in results for i in r.issues if i.severity == RiskLevel.LOW)

    return {
        "total_issues": total_issues,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "files_scanned": len(results),
    }


def _get_implemented(summary: dict, results: list[AuditResult]) -> list[str]:
    items = []
    items.append(f"K8s YAML security scanner with {len(K8sScanner.UNSAFE_CONFIGS)} security checks")
    items.append(f"Docker Compose security scanner with {len(DockerScanner.UNSAFE_CONFIGS)} security checks")
    items.append("Terraform scanning via tfsec integration")
    items.append("Risk scoring and severity classification (critical/high/medium/low)")
    items.append("AI-powered explanations for security findings")
    if summary.get("total_issues", 0) == 0:
        items.append("All scans passed - no security issues found")
    return items


def _generate_suggestions(summary: dict, results: list[AuditResult]) -> list[str]:
    suggestions = []
    if summary.get("total_issues", 0) == 0:
        return suggestions
    if summary.get("critical", 0) > 0:
        suggestions.append("Address critical security issues immediately - they pose severe risk")
    if summary.get("high", 0) > 0:
        suggestions.append("Review high-severity issues before deploying to production")
    if summary.get("medium", 0) > 0:
        suggestions.append("Plan to fix medium-severity issues in upcoming sprints")
    for result in results:
        for issue in result.issues:
            if hasattr(issue, "remediation") and issue.remediation:
                suggestions.append(f"[{issue.severity.value}] {issue.remediation}")
                if len(suggestions) >= 10:
                    return suggestions
    return suggestions


@app.get("/scanners")
async def list_scanners():
    return {
        "available_scanners": ["kubernetes", "docker_compose", "terraform"],
        "tools": {
            "kubernetes": "Built-in YAML scanner",
            "docker_compose": "Built-in YAML scanner",
            "terraform": "tfsec (if installed)",
        },
    }
