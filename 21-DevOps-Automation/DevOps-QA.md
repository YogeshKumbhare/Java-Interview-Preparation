# 🔧 DevOps & Automation — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is DevOps?

**DevOps** is a set of practices that combines **software Development (Dev)** and **IT Operations (Ops)**. The goal is to shorten the development lifecycle and deliver high-quality software continuously.

**Before DevOps:** Developers write code → throw it over the wall to Ops → Ops deploys (weeks later) → things break → blame game.

**With DevOps:** Developers and Ops collaborate from day one. Code is automatically built, tested, and deployed continuously. Infrastructure is defined as code. Everything is automated.

### DevOps Lifecycle:
```
PLAN → CODE → BUILD → TEST → RELEASE → DEPLOY → OPERATE → MONITOR
  ↑                                                              │
  └──────────────────────── FEEDBACK ──────────────────────────────┘

Tools at each stage:
PLAN:    Jira, Confluence, Notion
CODE:    Git, GitHub, GitLab, Bitbucket
BUILD:   Maven, Gradle, npm
TEST:    JUnit, Selenium, SonarQube
RELEASE: Jenkins, GitHub Actions, GitLab CI
DEPLOY:  Docker, Kubernetes, Ansible, Terraform
OPERATE: Prometheus, Grafana, PagerDuty
MONITOR: ELK Stack, Datadog, New Relic
```

---

## 📖 Infrastructure as Code (IaC) — Terraform

### Theory:
**Infrastructure as Code** treats infrastructure (servers, databases, load balancers) as **code** that can be versioned, reviewed, and automated — instead of manually clicking in AWS Console.

```hcl
# terraform/main.tf — Define AWS infrastructure as code

provider "aws" {
  region = "ap-south-1"  # Mumbai region
}

# VPC
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "payment-vpc" }
}

# EKS Cluster (Managed Kubernetes)
resource "aws_eks_cluster" "payment_cluster" {
  name     = "payment-cluster"
  role_arn = aws_iam_role.eks_role.arn
  version  = "1.28"

  vpc_config {
    subnet_ids = aws_subnet.private[*].id
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "payment_db" {
  engine               = "postgres"
  engine_version       = "15.4"
  instance_class       = "db.r6g.xlarge"
  allocated_storage    = 100
  db_name              = "payment_db"
  username             = var.db_username
  password             = var.db_password
  multi_az             = true           # High availability
  backup_retention_period = 7            # 7 days of backups
  deletion_protection  = true
  storage_encrypted    = true
  skip_final_snapshot  = false
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "payment_cache" {
  replication_group_id = "payment-cache"
  description          = "Payment service Redis cluster"
  engine               = "redis"
  node_type            = "cache.r6g.large"
  num_cache_clusters   = 3
  automatic_failover_enabled = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

# Application Load Balancer
resource "aws_lb" "payment_alb" {
  name               = "payment-alb"
  internal           = false
  load_balancer_type = "application"
  subnets            = aws_subnet.public[*].id
}
```

### Terraform Commands:
```bash
terraform init      # Initialize providers (download AWS plugin)
terraform plan      # Preview changes (what will be created/modified/destroyed)
terraform apply     # Apply changes (create infrastructure)
terraform destroy   # Tear down everything (use in non-prod only!)
terraform state list  # See current infrastructure
```

---

## 📖 GitOps — Git as the Single Source of Truth

### Theory:
**GitOps** is a deployment strategy where the **desired state** of your infrastructure and applications is stored in a **Git repository**. A GitOps operator (ArgoCD, Flux) continuously monitors Git and ensures the actual cluster state matches the Git state.

```
Developer pushes to Git:
  main branch → Kubernetes manifests updated

ArgoCD (GitOps operator) detects change:
  Git state: replicas=5, image=v2.1
  Cluster state: replicas=3, image=v2.0
  → ArgoCD automatically syncs cluster to match Git!

Benefits:
- Full audit trail (Git history = deployment history)
- Easy rollback (git revert = rollback deployment)
- No manual kubectl commands → everything through PRs
- Consistent environments (staging = production manifests)
```

### ArgoCD Application:
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: payment-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-manifests.git
    targetRevision: main
    path: services/payment-service
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true        # Remove resources not in Git
      selfHeal: true     # Revert manual changes to match Git
    syncOptions:
      - CreateNamespace=true
```

---

## 📖 GitHub Actions (CI/CD)

```yaml
# .github/workflows/ci-cd.yml
name: Build, Test, Deploy

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  DOCKER_REGISTRY: ghcr.io/company
  IMAGE_NAME: payment-service

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: testdb
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
          cache: maven

      - name: Build
        run: mvn clean compile

      - name: Unit Tests
        run: mvn test

      - name: Integration Tests
        run: mvn verify -P integration
        env:
          SPRING_DATASOURCE_URL: jdbc:postgresql://localhost:5432/testdb

      - name: SonarQube Analysis
        run: mvn sonar:sonar
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}

      - name: Build Docker Image
        run: docker build -t $DOCKER_REGISTRY/$IMAGE_NAME:${{ github.sha }} .

      - name: Push to Registry
        run: |
          echo ${{ secrets.GITHUB_TOKEN }} | docker login ghcr.io -u ${{ github.actor }} --password-stdin
          docker push $DOCKER_REGISTRY/$IMAGE_NAME:${{ github.sha }}

  deploy-staging:
    needs: build-and-test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          kubectl set image deployment/payment-service \
            payment-service=$DOCKER_REGISTRY/$IMAGE_NAME:${{ github.sha }} \
            -n staging

  deploy-production:
    needs: build-and-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    steps:
      - name: Deploy to Production
        run: |
          kubectl set image deployment/payment-service \
            payment-service=$DOCKER_REGISTRY/$IMAGE_NAME:${{ github.sha }} \
            -n production
```

---

## Common Interview Questions:

### "What is the difference between Terraform and Ansible?"
```
Terraform (Declarative — "What I want"):
  - Define desired state → Terraform figures out HOW to reach it
  - Focus: Infrastructure provisioning (create servers, databases, networks)
  - State file tracks current state → knows what to add/change/remove
  - Idempotent by nature

Ansible (Procedural — "How to do it"):
  - Write step-by-step playbooks (instructions)
  - Focus: Configuration management (install Java, configure Nginx)
  - Agentless — connects via SSH
  - Great for: app deployment, server configuration

Often used TOGETHER:
  Terraform → create EC2 instances + RDS + load balancer
  Ansible → install Java, deploy JAR, configure logging on those instances
```
