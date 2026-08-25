from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .models import ReviewRequest, ReviewResponse
from .agents.terraform_parser import TerraformParser
from .agents.terrascan_scanner import TerrascanScanner
from .agents.bedrock_analyzer import BedrockAnalyzer

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


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "terraform-review-agent"}


@app.post("/review", response_model=ReviewResponse)
async def review_terraform(request: ReviewRequest):
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
