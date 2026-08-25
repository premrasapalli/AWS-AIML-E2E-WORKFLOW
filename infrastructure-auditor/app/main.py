from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import AuditRequest, AuditResponse, AuditResult, FileType, RiskLevel
from .scanners.k8s_scanner import K8sScanner
from .scanners.docker_scanner import DockerScanner
from .scanners.terraform_scanner import TerraformScanner
from .ai.bedrock_explainer import BedrockExplainer

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


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "infrastructure-auditor"}


@app.post("/audit", response_model=AuditResponse)
async def audit_infrastructure(request: AuditRequest):
    all_results = []
    explainer = BedrockExplainer(model_alias=request.model_alias) if request.include_ai_explanations else None

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
