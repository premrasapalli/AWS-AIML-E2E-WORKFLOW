# CI/CD Pipeline

## Overview

GitHub Actions pipeline with 2 workflows: CI (build and test) and CD (deploy).

## Triggers

| Event | Pipeline |
|-------|----------|
| PR to main | CI (lint + test + security + reports) |
| Push to main | CI + Build Docker + Push to ECR |
| CI passes on main | Deploy to EKS + CD Reports |

## CI Pipeline Jobs (ci.yml)

### 1. Lint
- Python 3.14
- ruff check (E,F,W rules)
- ruff format check

### 2. Test
- pytest (if tests exist)
- Import validation
- CLI smoke tests

### 3. Security
- trivy vulnerability scanner
- bandit security scan

### 4. Generate Reports
- Runs all 3 scanners on the repository
- Creates per-tool report files:
  - `infrastructure-auditor_*.txt`
  - `terraform-review-agent_*.txt`
  - `k8s-debugger_*.txt`
  - `CI_SUMMARY.txt`
- Uploads reports as GitHub artifact (30-day retention)

### 5. Build Docker
- Build 3 images in parallel
- Push to ECR with commit SHA tag
- Tag as latest

## CD Pipeline Jobs (deploy.yml)

### 1. Deploy to EKS Fargate
- Update kubeconfig
- kubectl apply for each tool (Deployment + Service)
- Wait for Fargate startup (60s)
- Verify rollout status

### 2. Generate Reports
- Creates CD deployment report
- Creates infrastructure review report
- Creates `CD_SUMMARY.txt`
- Uploads as GitHub artifact

### 3. Verify
- kubectl get deployments
- kubectl get services
- kubectl get pods

## Required GitHub Secrets

| Secret | Value |
|--------|-------|
| AWS_ACCESS_KEY_ID | IAM user access key |
| AWS_SECRET_ACCESS_KEY | IAM user secret key |
| AWS_REGION | us-east-1 |
| AWS_ACCOUNT_ID | AWS account ID |
| EKS_CLUSTER | aimlops-fargate |

## Downloading Reports

Reports are saved as GitHub artifacts and can be downloaded from any workflow run.

**Steps to download:**
1. Go to: `https://github.com/premrasapalli/AWS-AIML-E2E-WORKFLOW/actions`
2. Click on any workflow run
3. Scroll down to **Artifacts** section
4. Click the artifact name to download:
   - `scan-reports-{sha}` (from CI workflow)
   - `cd-reports-{sha}` (from CD workflow)
5. Extract the zip file

**Report contents:**
```
WHAT IS IMPLEMENTED CORRECTLY
  - Lists working features in plain English

IMPROVEMENTS NEEDED
  - Lists suggestions for improvement (or "None")
```

## Manual Trigger

```bash
# Trigger deploy manually
gh workflow run deploy.yml
```

## Monitoring

```bash
# List runs
gh run list --repo premrasapalli/AWS-AIML-E2E-WORKFLOW

# Watch a run
gh run watch <run-id>

# View logs
gh run view <run-id> --log
```
