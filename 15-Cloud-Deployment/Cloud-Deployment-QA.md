# ☁️ Cloud & Deployment — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Cloud Computing?

**Cloud Computing** is the delivery of computing services — servers, storage, databases, networking, software — **over the internet** ("the cloud") on a **pay-as-you-go** basis. Instead of buying physical hardware, you rent virtual resources from providers like AWS, Azure, or GCP.

### Three Service Models:

```
┌──────────────────────────────────────────────────────────────────┐
│     You Manage      │ IaaS        │ PaaS        │ SaaS          │
├──────────────────────┼─────────────┼─────────────┼───────────────┤
│ Application          │ ✅ YOU      │ ✅ YOU      │ ❌ Provider   │
│ Data                 │ ✅ YOU      │ ✅ YOU      │ ❌ Provider   │
│ Runtime (Java, .NET) │ ✅ YOU      │ ❌ Provider │ ❌ Provider   │
│ OS (Linux, Windows)  │ ✅ YOU      │ ❌ Provider │ ❌ Provider   │
│ Virtualization       │ ❌ Provider │ ❌ Provider │ ❌ Provider   │
│ Server/Network       │ ❌ Provider │ ❌ Provider │ ❌ Provider   │
├──────────────────────┼─────────────┼─────────────┼───────────────┤
│ Example              │ AWS EC2     │ AWS Elastic │ Salesforce    │
│                      │ Azure VM    │ Beanstalk   │ Gmail         │
│                      │ GCP Compute │ Azure App   │ Dropbox       │
│                      │             │ Service     │               │
└──────────────────────┴─────────────┴─────────────┴───────────────┘
```

---

## 📖 What is Docker?

**Docker** is a platform for building, running, and shipping applications in **containers**. A container is a lightweight, standalone, executable package that includes everything needed to run an application: code, runtime (JVM), system tools, libraries, and settings.

### Container vs VM:

```
Virtual Machine:                    Container (Docker):
┌─────────────────┐                ┌─────────────────┐
│ App A  │ App B  │                │ App A  │ App B  │
├────────┼────────┤                ├────────┼────────┤
│ Guest  │ Guest  │                │ Bins/  │ Bins/  │
│ OS     │ OS     │                │ Libs   │ Libs   │
├────────┴────────┤                ├────────┴────────┤
│   Hypervisor    │                │  Docker Engine  │
├─────────────────┤                ├─────────────────┤
│    Host OS      │                │    Host OS      │
├─────────────────┤                ├─────────────────┤
│   Hardware      │                │   Hardware      │
└─────────────────┘                └─────────────────┘
     ~GB size                           ~MB size
     Boot: minutes                      Boot: seconds
     Full OS isolation                  Process isolation
```

### Dockerfile for Spring Boot:
```dockerfile
# Multi-stage build — keeps final image small
# Stage 1: Build with Maven
FROM maven:3.9-eclipse-temurin-21 AS builder
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline          # Cache dependencies
COPY src/ src/
RUN mvn clean package -DskipTests      # Build JAR

# Stage 2: Run with minimal JRE
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/*.jar app.jar

# Non-root user (security best practice)
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# JVM settings for containerized environment
ENV JAVA_OPTS="-Xms256m -Xmx512m -XX:+UseG1GC -XX:MaxGCPauseMillis=200"

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

### Docker Compose for microservices:
```yaml
# docker-compose.yml
version: '3.8'
services:
  user-service:
    build: ./user-service
    ports:
      - "8081:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - SPRING_DATASOURCE_URL=jdbc:postgresql://postgres:5432/users
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - app-network

  payment-service:
    build: ./payment-service
    ports:
      - "8082:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=docker
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
    depends_on:
      - kafka
    networks:
      - app-network

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: users
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secret
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin"]
      interval: 10s
      timeout: 5s
      retries: 5
    volumes:
      - pgdata:/var/lib/postgresql/data
    networks:
      - app-network

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - app-network

volumes:
  pgdata:

networks:
  app-network:
    driver: bridge
```

---

## 📖 What is Kubernetes (K8s)?

**Kubernetes** is an open-source **container orchestration platform** that automates deployment, scaling, and management of containerized applications. Docker runs ONE container on ONE machine. Kubernetes manages THOUSANDS of containers across HUNDREDS of machines.

### Core Concepts:
```
Kubernetes Cluster:
├── Master Node (Control Plane)
│   ├── API Server — entry point for all K8s commands (kubectl)
│   ├── Scheduler — decides WHICH node runs each pod
│   ├── Controller Manager — ensures desired state = actual state
│   └── etcd — distributed key-value store (cluster state DB)
│
└── Worker Nodes (run your containers)
    ├── kubelet — agent that manages pods on this node
    ├── kube-proxy — handles networking between pods
    └── Container Runtime (Docker, containerd)

Pod → smallest deployable unit (1+ containers)
Deployment → manages ReplicaSets (desired state: "I want 3 pods")
Service → stable network endpoint for pods (load balancing)
Ingress → external HTTP routing (like API Gateway)
ConfigMap — configuration that can be injected into pods
Secret — sensitive data (passwords, tokens) encrypted
```

### Deployment YAML:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: payment-service
  labels:
    app: payment
spec:
  replicas: 3                    # Always 3 pods running
  selector:
    matchLabels:
      app: payment
  strategy:
    type: RollingUpdate          # Zero-downtime deployments
    rollingUpdate:
      maxUnavailable: 1          # Max 1 pod down during update
      maxSurge: 1                # Max 1 extra pod during update
  template:
    metadata:
      labels:
        app: payment
    spec:
      containers:
      - name: payment
        image: payment-service:v2.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "k8s"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: password
        readinessProbe:           # Only route traffic when ready
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:            # Restart if unhealthy
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 15
---
apiVersion: v1
kind: Service
metadata:
  name: payment-service
spec:
  selector:
    app: payment
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP              # Internal only
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payment-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70   # Scale when CPU > 70%
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 📖 CI/CD Pipeline — Continuous Integration / Continuous Deployment

### Theory:
**CI (Continuous Integration):** Developers merge code frequently. Every merge triggers automated build + tests. Catches bugs early.

**CD (Continuous Deployment):** Every code change that passes tests is automatically deployed to production. No manual approval needed.

**CD (Continuous Delivery):** Same as above but with manual approval gate before production.

```
Developer pushes code → CI/CD Pipeline:
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│  Build   │ → │  Unit    │ → │Integration│ → │  Docker  │ → │  Deploy  │
│  (Maven) │   │  Tests   │   │  Tests   │   │  Image   │   │  to K8s  │
│          │   │ (JUnit5) │   │ (TestCont│   │  Build + │   │          │
│          │   │          │   │ ainers)  │   │  Push    │   │          │
└──────────┘   └──────────┘   └──────────┘   └──────────┘   └──────────┘
```

### Jenkins Pipeline:
```groovy
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'ecr.amazonaws.com/mycompany'
        IMAGE_NAME = 'payment-service'
    }

    stages {
        stage('Build') {
            steps {
                sh 'mvn clean compile'
            }
        }

        stage('Unit Tests') {
            steps {
                sh 'mvn test'
                junit '**/target/surefire-reports/*.xml'
            }
        }

        stage('Integration Tests') {
            steps {
                sh 'mvn verify -P integration-tests'
            }
        }

        stage('Sonar Analysis') {
            steps {
                sh 'mvn sonar:sonar -Dsonar.host.url=http://sonarqube:9000'
            }
        }

        stage('Docker Build & Push') {
            steps {
                sh "docker build -t ${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER} ."
                sh "docker push ${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER}"
            }
        }

        stage('Deploy to Staging') {
            steps {
                sh "kubectl set image deployment/${IMAGE_NAME} ${IMAGE_NAME}=${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER} -n staging"
                sh "kubectl rollout status deployment/${IMAGE_NAME} -n staging --timeout=300s"
            }
        }

        stage('Deploy to Production') {
            when { branch 'main' }
            input { message 'Deploy to production?' }
            steps {
                sh "kubectl set image deployment/${IMAGE_NAME} ${IMAGE_NAME}=${DOCKER_REGISTRY}/${IMAGE_NAME}:${env.BUILD_NUMBER} -n production"
            }
        }
    }

    post {
        failure {
            slackSend channel: '#prod-alerts',
                      message: "❌ Pipeline FAILED: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        success {
            slackSend channel: '#deployments',
                      message: "✅ Deployed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
```

---

## Common Interview Questions:

### "What is the difference between Docker and Kubernetes?"
| Docker | Kubernetes |
|--------|-----------|
| Runs containers on ONE machine | Orchestrates containers across MANY machines |
| Docker Compose for multi-container | Native multi-node support |
| Manual scaling | Auto-scaling (HPA) |
| No self-healing | Restarts failed containers automatically |
| Good for development | Good for production at scale |

### "Explain Blue-Green vs Canary deployment"
```
Blue-Green:
  Blue (v1) ←── 100% traffic
  Green (v2) ←── 0% traffic (testing)
  Switch: Instantly move ALL traffic to Green
  Rollback: Switch back to Blue instantly
  Pros: Simple, instant rollback
  Cons: Needs double infrastructure

Canary:
  v1 ←── 95% traffic
  v2 ←── 5% traffic (canary)
  Monitor metrics for 15 minutes
  If healthy: 5% → 25% → 50% → 100%
  If errors: Roll back canary instantly
  Pros: Low risk, gradual validation
  Cons: More complex, slower rollout
```

### "What happens when you type `kubectl apply -f deployment.yaml`?"
```
1. kubectl sends YAML to API Server (HTTP POST)
2. API Server validates YAML, stores in etcd
3. Controller Manager detects "desired state: 3 replicas, actual: 0"
4. Scheduler selects which nodes should run the pods
5. kubelet on each selected node pulls Docker image
6. Container runtime creates containers
7. readinessProbe passes → Service routes traffic to new pod
8. Old pods are terminated (rolling update)
9. Controller Manager confirms: desired state = actual state ✅
```
