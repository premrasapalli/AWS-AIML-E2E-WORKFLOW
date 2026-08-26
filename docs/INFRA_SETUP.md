# Infrastructure Setup

## AWS Resources Created

### 1. ECR Repositories
```bash
aws ecr create-repository --repository-name aimlops-terraform-review-agent --region us-east-1
aws ecr create-repository --repository-name aimlops-infrastructure-auditor --region us-east-1
aws ecr create-repository --repository-name aimlops-k8s-debugger --region us-east-1
```

**Repository URIs:**
- `730767193869.dkr.ecr.us-east-1.amazonaws.com/aimlops-terraform-review-agent`
- `730767193869.dkr.ecr.us-east-1.amazonaws.com/aimlops-infrastructure-auditor`
- `730767193869.dkr.ecr.us-east-1.amazonaws.com/aimlops-k8s-debugger`

### 2. EKS Cluster
- **Name**: aimlops-fargate
- **Region**: us-east-1
- **Version**: 1.31
- **Mode**: Fargate (serverless, no EC2 nodes)

### 3. VPC Configuration
- **VPC ID**: vpc-09348b528487de0b4
- **CIDR**: 10.0.0.0/16
- **Subnets**:
  - subnet-07da2d58491a867fa (us-east-1a)
  - subnet-01150990efdd39518 (us-east-1b)
  - subnet-0c93296315f1e6f96 (us-east-1c)
- **Internet Gateway**: igw-05fa01dc530dbd955
- **Security Group**: sg-09ceefa87143f1ea7

### 4. IAM Roles
- **EKS Cluster Role**: arn:aws:iam::730767193869:role/eks-cluster-role
  - AmazonEKSClusterPolicy
  - AmazonEKSServicePolicy

## GitHub Secrets Configured

```bash
gh secret set AWS_ACCESS_KEY_ID --body "AKIAXXXXXXXXXXXXXXXX"
gh secret set AWS_SECRET_ACCESS_KEY --body "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
gh secret set AWS_REGION --body "us-east-1"
gh secret set AWS_ACCOUNT_ID --body "730767193869"
gh secret set EKS_CLUSTER --body "aimlops-cluster"
gh secret set ECR_REGISTRY --body "730767193869.dkr.ecr.us-east-1.amazonaws.com"
```

## Local Development Setup

### Prerequisites
```bash
# Install tools
brew install awscli kubectl terrascan tfsec gh ollama

# Install Python dependencies
cd terraform-review-agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd ../infrastructure-auditor && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cd ../k8s-debugger && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Install and start Ollama
ollama pull qwen3:0.6b
ollama serve
```

### Run Locally
```bash
# CLI
cd terraform-review-agent && source .venv/bin/activate
python cli.py review --repo /path/to/terraform

# API
uvicorn app.main:app --port 8001

# Dashboard
streamlit run dashboard.py
```

## Cost Estimate

| Resource | Monthly Cost |
|----------|-------------|
| EKS Cluster | $73 (control plane) |
| Fargate (3 tasks) | $100-150 |
| ECR Storage | $1-5 |
| ALB | $20-30 |
| Data Transfer | $5-10 |
| **Total** | **$200-270/month** |

## Cleanup

```bash
# Delete EKS cluster
aws eks delete-cluster --name aimlops-fargate --region us-east-1

# Delete ECR repos
aws ecr delete-repository --repository-name aimlops-terraform-review-agent --force
aws ecr delete-repository --repository-name aimlops-infrastructure-auditor --force
aws ecr delete-repository --repository-name aimlops-k8s-debugger --force

# Delete VPC
aws ec2 delete-subnet --subnet-id subnet-07da2d58491a867fa
aws ec2 delete-subnet --subnet-id subnet-01150990efdd39518
aws ec2 delete-subnet --subnet-id subnet-0c93296315f1e6f96
aws ec2 detach-internet-gateway --internet-gateway-id igw-05fa01dc530dbd955 --vpc-id vpc-09348b528487de0b4
aws ec2 delete-internet-gateway --internet-gateway-id igw-05fa01dc530dbd955
aws ec2 delete-security-group --group-id sg-09ceefa87143f1ea7
aws ec2 delete-vpc --vpc-id vpc-09348b528487de0b4

# Delete IAM role
aws iam detach-role-policy --role-name eks-cluster-role --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
aws iam detach-role-policy --role-name eks-cluster-role --policy-arn arn:aws:iam::aws:policy/AmazonEKSServicePolicy
aws iam delete-role --role-name eks-cluster-role
```
