# Step-by-Step Actions

## Phase 1: Repository Setup

### 1.1 Clone Repository
```bash
git clone https://github.com/premrasapalli/AWS-AIML-E2E-WORKFLOW.git
cd AWS-AIML-E2E-WORKFLOW
```

### 1.2 Install Python Dependencies
```bash
# For each project
cd terraform-review-agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && deactivate

cd ../infrastructure-auditor && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && deactivate

cd ../k8s-debugger && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && deactivate
```

### 1.3 Install System Tools
```bash
brew install awscli kubectl terrascan tfsec gh ollama
```

## Phase 2: AI Backend Setup

### 2.1 Install and Configure Ollama
```bash
# Pull lightweight model
ollama pull qwen3:0.6b

# Start Ollama server (in background)
ollama serve &

# Verify it's running
curl http://localhost:11434/api/tags
```

### 2.2 Test AI Connection
```bash
cd terraform-review-agent && source .venv/bin/activate
python -c "from shared.bedrock_client import BedrockClient; c = BedrockClient(); print(c.generate('Say hello'))"
```

## Phase 3: Local Testing

### 3.1 Test Terraform Review Agent
```bash
cd terraform-review-agent && source .venv/bin/activate

# CLI test
python cli.py review --repo /tmp/test-terraform --model ollama

# API test
uvicorn app.main:app --port 8001 &
curl http://localhost:8001/health

# Dashboard test
streamlit run dashboard.py
```

### 3.2 Test Infrastructure Auditor
```bash
cd infrastructure-auditor && source .venv/bin/activate

# CLI test
python cli.py scan --path /tmp/test-infra --model ollama

# API test
uvicorn app.main:app --port 8002 &
curl http://localhost:8002/health
```

### 3.3 Test K8s Debugger
```bash
cd k8s-debugger && source .venv/bin/activate

# CLI test
python cli.py debug --namespace default --model ollama

# API test
uvicorn app.main:app --port 8003 &
curl http://localhost:8003/health
```

## Phase 4: AWS Infrastructure

### 4.1 Configure AWS CLI
```bash
aws configure
# Enter credentials:
# AWS Access Key ID: <YOUR-AWS-ACCESS-KEY-ID>
# AWS Secret Access Key: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
# Default region: us-east-1
```

### 4.2 Create ECR Repositories
```bash
for project in terraform-review-agent infrastructure-auditor k8s-debugger; do
  aws ecr create-repository --repository-name "aimlops-${project}" --region us-east-1
done
```

### 4.3 Create EKS Cluster
```bash
# Create IAM role
aws iam create-role --role-name eks-cluster-role \
  --assume-role-policy-document '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"eks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

aws iam attach-role-policy --role-name eks-cluster-role --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy
aws iam attach-role-policy --role-name eks-cluster-role --policy-arn arn:aws:iam::aws:policy/AmazonEKSServicePolicy

# Create VPC
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)

# Create subnets
SUBNET1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text)
SUBNET2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)
SUBNET3=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.3.0/24 --availability-zone us-east-1c --query 'Subnet.SubnetId' --output text)

# Create internet gateway and route table
IGW=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW --vpc-id $VPC_ID

# Create EKS cluster
aws eks create-cluster --cli-input-json '{
  "name": "aimlops-cluster",
  "roleArn": "arn:aws:iam::730767193869:role/eks-cluster-role",
  "resourcesVpcConfig": {
    "subnetIds": ["'$SUBNET1'","'$SUBNET2'","'$SUBNET3'"]
  },
  "version": "1.31"
}'
```

## Phase 5: CI/CD Pipeline

### 5.1 Add GitHub Secrets
```bash
gh secret set AWS_ACCESS_KEY_ID --body "<YOUR-AWS-ACCESS-KEY-ID>"
gh secret set AWS_SECRET_ACCESS_KEY --body "<YOUR-AWS-SECRET-ACCESS-KEY>"
gh secret set AWS_REGION --body "us-east-1"
gh secret set AWS_ACCOUNT_ID --body "<YOUR-AWS-ACCOUNT-ID>"
gh secret set EKS_CLUSTER --body "aimlops-cluster"
gh secret set ECR_REGISTRY --body "<YOUR-AWS-ACCOUNT-ID>.dkr.ecr.us-east-1.amazonaws.com"
```

### 5.2 Push Code to Trigger Pipeline
```bash
git add .
git commit -m "feat: Add CI/CD pipeline with GitHub Actions"
git push origin main
```

### 5.3 Monitor Pipeline
```bash
# Watch workflow runs
gh run list --repo premrasapalli/AWS-AIML-E2E-WORKFLOW

# Watch specific run
gh run watch <run-id>
```

## Phase 6: Deployment

### 6.1 Update kubeconfig
```bash
aws eks update-kubeconfig --name aimlops-cluster --region us-east-1
```

### 6.2 Verify Deployment
```bash
kubectl get deployments
kubectl get services
kubectl get pods
```

### 6.3 Access Services
```bash
# Get LoadBalancer URLs
kubectl get services -o jsonpath='{.items[*].status.loadBalancer.ingress[0].hostname}'

# Test endpoints
curl http://<LB-URL>:8001/health
curl http://<LB-URL>:8002/health
curl http://<LB-URL>:8003/health
```
