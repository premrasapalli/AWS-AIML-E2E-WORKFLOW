# End-to-End from Scratch

This guide walks through building the entire project from an empty directory to a fully deployed CI/CD pipeline on AWS.

## Prerequisites

- macOS with Homebrew installed
- GitHub account with `gh` CLI authenticated
- AWS account with programmatic access
- Domain knowledge: Python, Docker, Kubernetes, Terraform

## Step 1: Initialize Repository

```bash
# Create project directory
mkdir AWS-AIML-E2E-WORKFLOW && cd AWS-AIML-E2E-WORKFLOW
git init

# Create structure
mkdir -p shared terraform-review-agent/app/agents terraform-review-agent/app/models
mkdir -p infrastructure-auditor/app/scanners infrastructure-auditor/app/ai infrastructure-auditor/app/models
mkdir -p k8s-debugger/app/collectors k8s-debugger/app/ai k8s-debugger/app/models
mkdir -p .github/workflows .github/docker docs kubernetes tests
```

## Step 2: Build Shared Library

### 2.1 Create `shared/config.py`
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "ollama"
    max_tokens: int = 2048

    class Config:
        env_file = ".env"
```

### 2.2 Create `shared/bedrock_client.py`
Multi-backend LLM client supporting:
- **Ollama** (local, free): qwen3, deepseek, llama3, mistral
- **AWS Bedrock** (paid): Nova Lite/Pro/Premier, Titan Express/Lite/Premier

Key methods:
- `generate(prompt, model)` — Generate text
- `generate_with_context(prompt, context, model)` — RAG-style generation
- `stream(prompt, model)` — Streaming response

### 2.3 Create `shared/__init__.py`
```python
from .bedrock_client import BedrockClient
from .config import Settings
```

## Step 3: Build Terraform Review Agent

### 3.1 Scanner: `app/agents/terrascan_scanner.py`
- Runs `terrascan scan -d <dir> -o json` via subprocess
- Parses JSON output into `SecurityFinding` objects
- Returns list of findings with severity, rule ID, resource

### 3.2 Parser: `app/agents/terraform_parser.py`
- Regex-based HCL parser (no external library needed)
- Extracts: resources, variables, outputs, providers
- Returns `TerraformResource` objects

### 3.3 Analyzer: `app/agents/bedrock_analyzer.py`
- Takes scan results + parsed resources
- Sends to LLM for risk scoring and remediation
- Returns `AIAnalysis` with score, summary, recommendations

### 3.4 Models: `app/models/__init__.py`
```python
class ReviewRequest(BaseModel):
    repo_path: str
    model: str = "ollama"

class SecurityFinding(BaseModel):
    rule_id: str
    severity: str
    resource: str
    message: str

class AIAnalysis(BaseModel):
    risk_score: int
    summary: str
    recommendations: list[str]
```

### 3.5 API: `app/main.py`
- `POST /review` — Scan and analyze Terraform
- `GET /health` — Health check

### 3.6 CLI: `cli.py`
```bash
python cli.py review --repo /path/to/tf --model ollama --output table
```

### 3.7 Dashboard: `dashboard.py`
Streamlit UI with:
- File uploader for Terraform files
- Model selector dropdown
- Real-time scan results
- Risk score gauge chart

## Step 4: Build Infrastructure Auditor

### 4.1 K8s Scanner: `app/scanners/k8s_scanner.py`
Checks for:
- Privileged containers
- Missing resource limits
- Host network usage
- Running as root
- Missing health probes

### 4.2 Docker Scanner: `app/scanners/docker_scanner.py`
Checks for:
- Privileged mode
- Host networking
- Writable filesystem
- Host path mounts
- Running as root

### 4.3 Terraform Scanner: `app/scanners/terraform_scanner.py`
- Wraps `tfsec` CLI
- Parses JSON output
- Returns unified `SecurityFinding` format

### 4.4 AI Explainer: `app/ai/bedrock_explainer.py`
- Takes security findings
- Generates explanations, impact, fixes, compliance mapping

### 4.5 API & CLI
- `POST /scan` — Scan infrastructure
- `GET /health` — Health check

## Step 5: Build K8s Debugger

### 5.1 Log Collector: `app/collectors/log_collector.py`
- Runs `kubectl logs <pod> -n <ns>` via subprocess
- Parses logs into `PodLog` objects

### 5.2 Event Collector: `app/collectors/event_collector.py`
- Runs `kubectl get events -n <ns> -o json`
- Parses into `PodEvent` objects

### 5.3 AI Diagnoser: `app/ai/bedrock_diagnoser.py`
- Takes logs + events
- Generates root cause analysis
- Suggests fixes

### 5.4 API & CLI
- `POST /debug` — Debug a pod
- `GET /health` — Health check

## Step 6: Add Unit Tests

### 6.1 Test Structure
```
terraform-review-agent/tests/test_parser.py
infrastructure-auditor/tests/test_scanners.py
k8s-debugger/tests/test_collectors.py
```

### 6.2 Example Tests
```python
# test_parser.py
def test_parse_s3_bucket():
    content = """
    resource "aws_s3_bucket" "example" {
      bucket = "my-bucket"
    }
    """
    parser = TerraformParser()
    resources = parser.parse(content)
    assert len(resources) == 1
    assert resources[0].type == "aws_s3_bucket"
```

## Step 7: Create Dockerfiles

### 7.1 Multi-stage Build Pattern
```dockerfile
FROM python:3.14-slim AS base
WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Copy shared library
COPY shared/ /app/shared/

# Copy requirements and install
COPY terraform-review-agent/requirements.txt /app/terraform-review-agent/requirements.txt
RUN pip install --no-cache-dir -r /app/terraform-review-agent/requirements.txt

# Copy application code
COPY terraform-review-agent/ /app/terraform-review-agent/
WORKDIR /app/terraform-review-agent

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### 7.2 Docker Compose (Local Dev)
```yaml
services:
  terraform-review-agent:
    build:
      context: ..
      dockerfile: .github/docker/Dockerfile.terraform-review-agent
    ports:
      - "8001:8001"
    environment:
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
```

## Step 8: Create GitHub Actions Workflows

### 8.1 CI Workflow (`.github/workflows/ci.yml`)
Triggers: PRs and pushes to main
Jobs:
1. **lint** — ruff check + format
2. **test** — pytest + import tests
3. **security** — trivy + bandit
4. **build-docker** — Build and push to ECR (main only)

### 8.2 Deploy Workflow (`.github/workflows/deploy.yml`)
Triggers: After CI passes, manual dispatch
Jobs:
1. **deploy** — kubectl apply to EKS
2. **verify** — Check rollout status

### 8.3 Key GitHub Actions
```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
- uses: aws-actions/configure-aws-credentials@v4
- uses: aws-actions/amazon-ecr-login@v2
- uses: aquasecurity/trivy-action@master
```

## Step 9: Set Up AWS Infrastructure

### 9.1 Create ECR Repos
```bash
for project in terraform-review-agent infrastructure-auditor k8s-debugger; do
  aws ecr create-repository --repository-name "aimlops-${project}" --region us-east-1
done
```

### 9.2 Create VPC
```bash
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)
# Create 3 subnets across AZs
# Create internet gateway
# Create route table
# Enable public IP auto-assign
```

### 9.3 Create EKS Cluster
```bash
# Create IAM role with AmazonEKSClusterPolicy
aws eks create-cluster --name aimlops-cluster \
  --role-arn arn:aws:iam::730767193869:role/eks-cluster-role \
  --resources-vpc-config subnetIds=...,securityGroupIds=... \
  --version 1.31

# Wait for cluster to become ACTIVE
aws eks wait cluster-active --name aimlops-cluster
```

### 9.4 Configure kubectl
```bash
aws eks update-kubeconfig --name aimlops-cluster --region us-east-1
```

## Step 10: Add GitHub Secrets

```bash
gh secret set AWS_ACCESS_KEY_ID --body "<YOUR-AWS-ACCESS-KEY-ID>"
gh secret set AWS_SECRET_ACCESS_KEY --body "<YOUR-AWS-SECRET-ACCESS-KEY>"
gh secret set AWS_REGION --body "us-east-1"
gh secret set AWS_ACCOUNT_ID --body "<YOUR-AWS-ACCOUNT-ID>"
gh secret set EKS_CLUSTER --body "aimlops-cluster"
gh secret set ECR_REGISTRY --body "<YOUR-AWS-ACCOUNT-ID>.dkr.ecr.us-east-1.amazonaws.com"
```

## Step 11: Deploy to EKS

### 11.1 Create Kubernetes Manifests
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: terraform-review-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: terraform-review-agent
  template:
    spec:
      containers:
      - name: terraform-review-agent
        image: 730767193869.dkr.ecr.us-east-1.amazonaws.com/aimlops-terraform-review-agent:latest
        ports:
        - containerPort: 8001
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 8001
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
---
apiVersion: v1
kind: Service
metadata:
  name: terraform-review-agent
spec:
  type: LoadBalancer
  selector:
    app: terraform-review-agent
  ports:
  - port: 8001
    targetPort: 8001
```

### 11.2 Apply Manifests
```bash
kubectl apply -f kubernetes/
```

### 11.3 Verify
```bash
kubectl get deployments
kubectl get services
kubectl get pods
kubectl rollout status deployment/terraform-review-agent
```

## Step 12: Test the Pipeline

### 12.1 Create a PR
```bash
git checkout -b feature/test-pipeline
# Make a change
git add . && git commit -m "test: trigger CI pipeline"
git push origin feature/test-pipeline
# Create PR on GitHub
gh pr create --title "Test CI Pipeline" --body "Testing the CI/CD pipeline"
```

### 12.2 Monitor CI
```bash
gh run list
gh run watch <run-id>
```

### 12.3 Merge and Deploy
```bash
gh pr merge <pr-number> --merge
# This triggers the deploy workflow
gh run list --workflow=deploy.yml
```

## Step 13: Access the Deployed Apps

```bash
# Get LoadBalancer URLs
kubectl get services -o wide

# Test health endpoints
curl http://<EXTERNAL-IP>:8001/health
curl http://<EXTERNAL-IP>:8002/health
curl http://<EXTERNAL-IP>:8003/health
```

## Summary of Files Created

| File | Purpose |
|------|---------|
| `shared/bedrock_client.py` | Multi-backend AI client |
| `shared/config.py` | Pydantic settings |
| `terraform-review-agent/**` | Terraform security scanner |
| `infrastructure-auditor/**` | Multi-format infra auditor |
| `k8s-debugger/**` | K8s pod debugger |
| `.github/workflows/ci.yml` | CI pipeline |
| `.github/workflows/deploy.yml` | Deploy pipeline |
| `.github/docker/Dockerfile.*` | Docker builds |
| `.github/docker/docker-compose.yml` | Local dev |
| `kubernetes/*.yaml` | K8s manifests |
| `docs/*.md` | Documentation |
