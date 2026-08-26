# How Everything Works Together - End to End

This document explains how all the parts of this project talk to each other and work as one big team.

---

## The Big Picture

Think of this project like a **security guard team** for computer code. There are **3 security guard tools** that check different things, and they all work together using a **shared brain (AI)** and are delivered to the cloud using a **factory assembly line (CI/CD pipeline)**.

```
Developer writes code
        |
        v
   Push to GitHub
        |
        v
   CI/CD Pipeline runs automatically
        |
        v
   3 Docker containers are built and sent to AWS cloud
        |
        v
   3 services run on Kubernetes (EKS)
        |
        v
   Users can access each tool via web browser
```

---

## The 3 Security Guard Tools

### Tool 1: Terraform Review Agent (Port 8001)

**What it does:** Checks Terraform files (infrastructure code) for security problems before they go live.

**How it works, step by step:**

```
Step 1: You give it a folder path containing .tf files
            |
            v
Step 2: TerraformParser reads all .tf files and extracts resource definitions
        (like: "I found an S3 bucket named my-data-bucket")
            |
            v
Step 3: TerrascanScanner runs a security scan tool called "terrascan"
        (like: "This S3 bucket has public access enabled - that is dangerous!")
            |
            v
Step 4: BedrockAnalyzer sends everything to the AI brain
        The AI says: "Risk score is 75 out of 100. Here is how to fix it."
            |
            v
Step 5: Report is generated and saved as a .txt file
```

**Real-life example:** Imagine you are building a house. Before you start building, this tool checks your blueprint and says "Hey, you forgot to put a lock on the front door!"

---

### Tool 2: Infrastructure Auditor (Port 8002)

**What it does:** Checks Kubernetes YAML files, Docker Compose files, and Terraform files for security problems.

**How it works, step by step:**

```
Step 1: You give it a folder path
            |
            v
Step 2: K8sScanner looks for Kubernetes YAML files
        Checks: Is the container running as root? Does it have resource limits?
        (like: "This container has no memory limit - it could crash the whole server!")
            |
            v
Step 3: DockerScanner looks for Docker Compose files
        Checks: Is the container in privileged mode? Does it use host network?
        (like: "This container has too much power - it could take over the whole machine!")
            |
            v
Step 4: TerraformScanner runs tfsec security checks
            |
            v
Step 5: BedrockExplainer sends each issue to the AI brain
        The AI explains each problem in simple English and suggests fixes
            |
            v
Step 6: Report is generated showing all findings
```

**Real-life example:** Imagine you are inspecting a building. This tool goes room by room and checks if the windows are locked, if the fire exits are clear, and if the electrical wiring is safe.

---

### Tool 3: K8s Debugger (Port 8003)

**What it does:** When a Kubernetes pod is broken or failing, this tool figures out why.

**How it works, step by step:**

```
Step 1: You tell it which pod to look at (by name or label)
            |
            v
Step 2: kubectl get pod runs to find pod information
        (like: "Pod is in CrashLoopBackOff state, restarted 5 times")
            |
            v
Step 3: EventCollector gets Kubernetes events for that pod
        (like: "Failed to pull image", "OOMKilled - ran out of memory")
            |
            v
Step 4: LogCollector gets the last 20 lines of logs from each container
        (like: "Error: Cannot connect to database at 10.0.0.5:5432")
            |
            v
Step 5: BedrockDiagnoser sends all this info to the AI brain
        The AI says: "Root cause: The database pod is not running.
                       Suggested fix: Check if the database deployment exists
                       in the same namespace."
            |
            v
Step 6: Report is generated with diagnosis and fix suggestions
```

**Real-life example:** Imagine your car engine light turns on. This tool is like a mechanic who plugs into the car's computer, reads the error codes, and tells you exactly what is wrong and how to fix it.

---

## The Shared Brain (shared/ folder)

All 3 tools share the same AI brain. This is the `shared/` folder.

```
shared/
  |
  +-- bedrock_client.py    <-- The AI brain
  |     Talks to either:
  |     - Ollama (free, runs on your computer)
  |     - AWS Bedrock (paid, runs in the cloud)
  |
  +-- config.py            <-- Settings
  |     Stores: which AI model to use, AWS region, timeouts
  |
  +-- report_generator.py  <-- Report writer
        Creates the .txt report files with
        "What is implemented correctly" and
        "Improvements needed" sections
```

**How the AI brain decides which model to use:**

```
You say: "Use ollama-deepseek"
            |
            v
BedrockClient checks: Is this model in the Ollama list?
            |
     YES -> Talk to Ollama at localhost:11434 (free, local)
            |
     NO  -> Talk to AWS Bedrock in the cloud (paid, more powerful)
```

---

## The Factory Assembly Line (CI/CD Pipeline)

This is how code goes from your computer to the cloud automatically.

### Part 1: CI Pipeline (ci.yml) - Build and Test

```
Developer pushes code to GitHub
            |
            v
    +-------------------+
    |  JOB 1: LINT      |  <-- Checks for code style mistakes
    |  ruff check        |      (like spell check for code)
    +-------------------+
            |
            v
    +-------------------+
    |  JOB 2: TEST      |  <-- Runs test scripts
    |  pytest            |      (like a checklist that must pass)
    +-------------------+
            |
            v
    +-------------------+
    |  JOB 3: SECURITY  |  <-- Scans for known vulnerabilities
    |  trivy + bandit    |      (like checking if any locks are broken)
    +-------------------+
            |
            v
    +-------------------+
    |  JOB 4: REPORTS   |  <-- Runs all 3 scanners on the code itself
    |  generate reports  |      and saves .txt report files
    +-------------------+
            |
            v
    +-------------------+
    |  JOB 5: BUILD     |  <-- Creates 3 Docker containers in parallel
    |  docker build      |      and pushes them to AWS ECR (image storage)
    +-------------------+
```

### Part 2: CD Pipeline (deploy.yml) - Deploy to Cloud

```
CI pipeline finished successfully
            |
            v
    +-------------------+
    |  JOB 1: DEPLOY    |  <-- Creates Kubernetes pods on EKS Fargate
    |  kubectl apply     |      (one pod per tool)
    +-------------------+
            |
            v
    +-------------------+
    |  JOB 2: REPORTS   |  <-- Generates deployment reports
    |  generate reports  |      (what was deployed, what can improve)
    +-------------------+
            |
            v
    +-------------------+
    |  JOB 3: VERIFY    |  <-- Checks if all pods are running
    |  kubectl get pods  |      (like a final inspection)
    +-------------------+
            |
            v
    3 services are now running on AWS!
    Access them via LoadBalancer URLs
```

---

## How Docker Containers Are Built

Each tool gets its own Docker container. Think of Docker containers like **lunch boxes** - they contain everything the tool needs to run.

```
Base: Python 3.14 image (like an empty lunch box)
            |
            v
Add: curl and kubectl (like adding utensils)
            |
            v
Add: shared/ folder (like adding a recipe book)
            |
            v
Add: Python requirements (like adding ingredients)
            |
            v
Add: Tool code (like adding the actual food)
            |
            v
Set: Expose port 8001/8002/8003 (like putting a label on the box)
            |
            v
Start: uvicorn server (like putting the lunch box in the fridge,
       ready to eat when someone opens it)
```

---

## How AWS Services Work Together

```
    +-------+     +-------+     +-------+
    | ECR   |     | EKS   |     | ALB   |
    | (Store|     | (Run  |     | (Route|
    | images|     | pods) |     | traffic|
    +---+---+     +---+---+     +---+---+
        |             |             |
        | Push        | Deploy      | Route
        | images      | pods        | users
        v             v             v
    +-------------------------------+
    |         3 Containers          |
    |                               |
    | terraform-review-agent :8001  |
    | infrastructure-auditor :8002  |
    | k8s-debugger          :8003  |
    +-------------------------------+
                    |
                    v
            +---------------+
            | Users access  |
            | via browser   |
            | or API calls  |
            +---------------+
```

---

## The Complete Journey of a Code Change

Here is what happens from start to finish when a developer changes code:

```
1. Developer writes code on their computer
   (Example: Adds a new security check to K8sScanner)

2. Developer pushes code to GitHub
   git push origin main

3. GitHub Actions CI pipeline starts automatically
   - Lint checks pass (no code style errors)
   - Tests pass (new code works)
   - Security scan passes (no vulnerabilities)

4. Reports are generated
   - infrastructure-auditor report says:
     "WHAT IS IMPLEMENTED CORRECTLY:
      - The Kubernetes YAML scanner can now detect 7 types of security misconfigurations"
     "IMPROVEMENTS NEEDED:
      - None"

5. Docker images are built for all 3 tools
   Each image contains the latest code

6. Images are pushed to AWS ECR
   (AWS stores the images safely in the cloud)

7. CD pipeline starts automatically
   - Old pods are replaced with new pods
   - Fargate starts the containers serverlessly

8. Deployment is verified
   - kubectl get pods shows all pods are Running
   - Health checks pass

9. Users can now access the updated tools
   - terraform-review-agent at port 8001
   - infrastructure-auditor at port 8002
   - k8s-debugger at port 8003

10. Reports are saved as downloadable artifacts
    - Users can download scan reports from GitHub Actions
```

---

## Summary Table

| Component | What It Is | What It Does | How It Connects |
|-----------|-----------|--------------|-----------------|
| terraform-review-agent | Python tool on port 8001 | Scans Terraform code for security issues | Uses shared AI brain, reports to shared reports folder |
| infrastructure-auditor | Python tool on port 8002 | Scans K8s YAML, Docker Compose, Terraform | Uses shared AI brain, reports to shared reports folder |
| k8s-debugger | Python tool on port 8003 | Diagnoses broken Kubernetes pods | Uses shared AI brain, reports to shared reports folder |
| shared/bedrock_client.py | AI abstraction layer | Talks to Ollama or AWS Bedrock | Used by all 3 tools for AI analysis |
| shared/report_generator.py | Report writer | Creates .txt report files | Used by all 3 tools and CI/CD |
| CI pipeline (ci.yml) | GitHub Actions workflow | Builds, tests, scans, and packages | Produces Docker images and reports |
| CD pipeline (deploy.yml) | GitHub Actions workflow | Deploys to AWS EKS Fargate | Runs the 3 tools in the cloud |
| ECR | AWS image storage | Stores Docker images | CI pushes here, CD pulls from here |
| EKS | AWS Kubernetes | Runs the 3 containers | CD deploys here |
| ALB | AWS load balancer | Routes user traffic to the right tool | Created automatically by Kubernetes Service |

---

## Key Takeaway

Everything is connected like a chain:

**Code** -> **GitHub** -> **CI Pipeline** -> **Docker Images** -> **ECR** -> **CD Pipeline** -> **EKS/Fargate** -> **Running Services**

And all 3 tools share the same **AI brain** and **report system**, so they work as one unified platform.
