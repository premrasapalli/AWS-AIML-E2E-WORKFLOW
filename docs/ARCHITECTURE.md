# System Architecture

## Overview

The AWS-AIML-E2E-WORKFLOW repository contains three AI-powered DevSecOps tools that scan infrastructure code for security vulnerabilities and provide AI-driven analysis and remediation.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                        │
├─────────────────────────────────────────────────────────────────┤
│  .github/workflows/                                            │
│  ├── ci.yml        (Lint, Test, Security Scan)                 │
│  ├── build.yml     (Docker Build + ECR Push)                   │
│  └── deploy.yml    (EKS Deployment)                             │
├─────────────────────────────────────────────────────────────────┤
│  .github/docker/                                               │
│  ├── Dockerfile.terraform-review-agent                         │
│  ├── Dockerfile.infrastructure-auditor                         │
│  ├── Dockerfile.k8s-debugger                                   │
│  └── docker-compose.yml                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD Pipeline                              │
├─────────────────────────────────────────────────────────────────┤
│  PR Created ──► Lint & Test ──► Security Scan ──► Build Docker  │
│                                                              │
│  Merge to main ──► Push to ECR ──► Deploy to EKS              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AWS Infrastructure                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ ECR Repo     │  │ EKS Cluster  │  │ Load Balancer│        │
│  │ (3 repos)    │  │ (3 nodes)    │  │ (3 services) │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐│
│  │ Terraform Review │  │ Infrastructure   │  │ K8s Debugger ││
│  │ Agent :8001      │  │ Auditor :8002    │  │ :8003        ││
│  └──────────────────┘  └──────────────────┘  └──────────────┘│
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Shared Library (bedrock_client.py, config.py)           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AI Layer (Ollama)                           │
├─────────────────────────────────────────────────────────────────┤
│  Local LLM Server (localhost:11434)                            │
│  ├── qwen3:0.6b (default, fastest)                            │
│  ├── deepseek-r1:7b (best reasoning)                          │
│  ├── llama3.2:1b                                               │
│  └── mistral                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Terraform Review Agent
- **Port**: 8001
- **Function**: Scans Terraform code for security issues
- **Scanners**: Terrascan, custom Terraform parser
- **AI**: Provides risk scoring and remediation advice

### 2. Infrastructure Auditor
- **Port**: 8002
- **Function**: Multi-format infrastructure scanner
- **Scanners**: K8s manifest scanner, Docker Compose scanner, tfsec
- **AI**: Explains security issues and compliance mapping

### 3. K8s Pod Debugger
- **Port**: 8003
- **Function**: Debug Kubernetes pod issues
- **Collectors**: kubectl logs, kubectl events
- **AI**: Root cause analysis and fix suggestions

## Data Flow

```
User Input ──► CLI/API ──► Scanner ──► Findings ──► AI Analysis ──► Output
     │                         │              │              │
     │                         ▼              ▼              ▼
     │                    Terrascan      Risk Score     Remediation
     │                    tfsec          Compliance     Explanation
     │                    K8s Scanner    Severity       Fix Suggestions
     │                    Docker Scanner
     │
     └──► Streamlit Dashboard ──► Real-time Results
```

## Network Architecture

```
Internet
    │
    ▼
┌─────────────┐
│ ALB (AWS)   │
│ Port 80/443 │
└─────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ EKS Cluster (aimlops-cluster)               │
│ VPC: 10.0.0.0/16                            │
│ Subnets: us-east-1a, 1b, 1c                │
├─────────────────────────────────────────────┤
│  Namespace: default                         │
│  ├── Deployment: terraform-review-agent     │
│  │   └── Service: LoadBalancer :8001        │
│  ├── Deployment: infrastructure-auditor     │
│  │   └── Service: LoadBalancer :8002        │
│  └── Deployment: k8s-debugger               │
│      └── Service: LoadBalancer :8003        │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ ECR Repositories                            │
│ ├── aimlops-terraform-review-agent          │
│ ├── aimlops-infrastructure-auditor          │
│ └── aimlops-k8s-debugger                    │
└─────────────────────────────────────────────┘
```
