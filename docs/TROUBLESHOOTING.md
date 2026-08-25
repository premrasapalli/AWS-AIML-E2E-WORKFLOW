# Troubleshooting

## Common Issues

### 1. Ollama Connection Refused
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check if model is pulled
ollama list
```

### 2. EKS Cluster Creation Fails
```bash
# Check cluster status
aws eks describe-cluster --name aimlops-cluster --region us-east-1

# Check IAM role
aws iam get-role --role-name eks-cluster-role

# Check VPC/subnets
aws ec2 describe-vpcs --vpc-ids vpc-09348b528487de0b4
```

### 3. Docker Build Fails
```bash
# Build locally to debug
docker build -f .github/docker/Dockerfile.terraform-review-agent -t test .

# Check shared module path
ls -la shared/
```

### 4. GitHub Actions Fails
```bash
# Check secrets
gh secret list

# View workflow logs
gh run view <run-id> --log

# Re-run failed jobs
gh run rerun <run-id>
```

### 5. K8s Pods CrashLoopBackOff
```bash
# Check pod logs
kubectl logs <pod-name> --previous

# Check events
kubectl get events --sort-by='.lastTimestamp'

# Check resource limits
kubectl describe pod <pod-name>
```

### 6. ECR Push Fails
```bash
# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 730767193869.dkr.ecr.us-east-1.amazonaws.com

# Check repo exists
aws ecr describe-repositories --region us-east-1
```

### 7. LoadBalancer Not Responding
```bash
# Check service status
kubectl get svc

# Check endpoints
kubectl get endpoints

# Check security group
aws ec2 describe-security-groups --group-ids sg-09ceefa87143f1ea7
```

## Cost Optimization

### Downgrade EKS Nodes
```bash
# Use t3.small instead of t3.medium
# Or use Fargate for serverless
```

### Delete Resources When Not in Use
```bash
# Scale down deployments
kubectl scale deployment terraform-review-agent --replicas=0

# Or delete cluster
aws eks delete-cluster --name aimlops-cluster --region us-east-1
```

## Getting Help

- GitHub Issues: https://github.com/premrasapalli/AWS-AIML-E2E-WORKFLOW/issues
- AWS EKS Docs: https://docs.aws.amazon.com/eks/
- Ollama Docs: https://ollama.com/docs
