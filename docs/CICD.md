# CI/CD Pipeline

## Overview

GitHub Actions pipeline with 3 stages: CI, Build, Deploy.

## Triggers

| Event | Pipeline |
|-------|----------|
| PR to main | CI (lint + test + security) |
| Push to main | CI + Build Docker + Push to ECR |
| CI passes | Deploy to EKS |

## Pipeline Jobs

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

### 4. Build Docker
- Build 3 images in parallel
- Push to ECR with commit SHA tag
- Tag as latest

### 5. Deploy to EKS
- Update kubeconfig
- kubectl apply
- Rolling update
- Health check verification

## Required GitHub Secrets

| Secret | Value |
|--------|-------|
| AWS_ACCESS_KEY_ID | IAM user access key |
| AWS_SECRET_ACCESS_KEY | IAM user secret key |
| AWS_REGION | us-east-1 |
| AWS_ACCOUNT_ID | 730767193869 |
| EKS_CLUSTER | aimlops-cluster |
| ECR_REGISTRY | 730767193869.dkr.ecr.us-east-1.amazonaws.com |

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
