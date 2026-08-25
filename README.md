# AWS AIML E2E Workflow - Category 3: Infrastructure as Code (IaC) & Security

AI-powered DevSecOps tools for infrastructure security analysis and Kubernetes debugging.

## Projects

### 1. AI Terraform Review Agent
Automates Terraform code review with AI-powered security analysis.

```bash
cd terraform-review-agent
pip install -r requirements.txt

# CLI
python cli.py review --repo /path/to/terraform --model titan-express

# Web UI
streamlit run dashboard.py

# API
uvicorn app.main:app --port 8001
```

### 2. AI Infrastructure Auditor
DevSecOps platform scanning Kubernetes, Docker Compose, and Terraform for security issues.

```bash
cd infrastructure-auditor
pip install -r requirements.txt

# CLI
python cli.py scan --path /path/to/infra --type all --model titan-express

# Web UI
streamlit run dashboard.py

# API
uvicorn app.main:app --port 8002
```

### 3. AI-Powered K8s Pod Debugger
Automatically diagnoses failing Kubernetes pods with AI root cause analysis.

```bash
cd k8s-debugger
pip install -r requirements.txt

# CLI
python cli.py debug -n default -p my-pod --model titan-express

# Web UI
streamlit run dashboard.py

# API
uvicorn app.main:app --port 8003
```

## Prerequisites

- Python 3.10+
- AWS CLI configured with Bedrock access
- kubectl (for K8s debugger)
- Terrascan (optional, for enhanced Terraform scanning)
- tfsec (optional, for enhanced Terraform scanning)

## AWS Bedrock Setup

Enable Amazon Titan models in your AWS account:

1. Go to AWS Console > Bedrock > Model access
2. Request access to Amazon Titan models
3. Configure AWS credentials:

```bash
export AIDECOPS_AWS_REGION=us-east-1
# or use ~/.aws/credentials
```

## Model Options

| Model | Alias | Best For |
|-------|-------|----------|
| titan-text-express-v1 | titan-express | Fast analysis, cost-effective |
| titan-text-lite-v1 | titan-lite | Quick scans, low latency |
| titan-text-premier-v1:0 | titan-premier | Complex reasoning, detailed analysis |

## Project Structure

```
AWS-AIML-E2E-WORKFLOW/
├── shared/                    # Shared components
│   ├── bedrock_client.py     # Multi-model Bedrock client
│   └── config.py             # Configuration
├── terraform-review-agent/   # Project 1
├── infrastructure-auditor/   # Project 2
└── k8s-debugger/             # Project 3
```

## License

MIT
