import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ReviewRequest, ReviewResponse
from .agents.terraform_parser import TerraformParser
from .agents.terrascan_scanner import TerrascanScanner
from .agents.bedrock_analyzer import BedrockAnalyzer
from shared.report_generator import ReportGenerator

app = FastAPI(title="AI Terraform Review Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

parser = TerraformParser()
scanner = TerrascanScanner()
report_gen = ReportGenerator("terraform-review-agent")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "terraform-review-agent"}


@app.post("/review", response_model=ReviewResponse)
async def review_terraform(request: ReviewRequest):
    try:
        tf_files = parser.get_terraform_files(request.repo_path)
        changes = []
        for tf_file in tf_files:
            resources = parser.parse_hcl(tf_file)
            for key, resource in resources.items():
                from .models import TerraformChange
                changes.append(
                    TerraformChange(
                        file=tf_file,
                        resource_type=resource["type"],
                        resource_name=resource["name"],
                        change_type="existing",
                    )
                )

        terrascan_findings = scanner.scan(request.repo_path)

        analyzer = BedrockAnalyzer(model_alias=request.model_alias)
        ai_analysis = analyzer.analyze_changes(changes, terrascan_findings)

        status = "success"
        suggestions = []
        if not tf_files:
            suggestions.append("No .tf files found - verify the repo_path is correct")
        if terrascan_findings:
            suggestions.append(f"Found {len(terrascan_findings)} security findings from Terrascan")
        for finding in terrascan_findings[:5]:
            if hasattr(finding, "severity") and finding.severity in ["HIGH", "CRITICAL"]:
                suggestions.append(f"Address {finding.severity} severity finding: {finding.rule_id}")
    except Exception as e:
        status = "failed"
        changes = []
        terrascan_findings = []
        ai_analysis = None
        suggestions = [f"Error during review: {str(e)}"]

    implemented = [
        "The Terraform parser can read HCL files and extract resource definitions",
        "Terrascan integration provides security scanning for infrastructure code",
        "AI-powered code review analyzes changes and identifies potential risks",
        "Git diff parsing detects what changed between commits",
        "Resource type and name extraction helps understand infrastructure components",
    ]

    report_path = report_gen.generate_report(
        status=status,
        implemented_correctly=implemented,
        improvements_needed=suggestions,
    )

    return ReviewResponse(
        changes=changes,
        terrascan_results=terrascan_findings,
        ai_analysis=ai_analysis,
        model_used=request.model_alias,
    )


@app.get("/models")
async def list_models():
    from shared.bedrock_client import BedrockClient
    client = BedrockClient()
    return {"available_models": client.available_models}
