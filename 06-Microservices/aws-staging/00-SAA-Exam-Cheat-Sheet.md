# AWS SAA Exam - Ultimate Cheat Sheet & Exam Tips

> **Exam:** AWS Certified Solutions Architect – Associate (SAA-C03)
> **Questions:** 65 (50 scored + 15 unscored)
> **Time:** 130 minutes
> **Passing Score:** 720/1000
> **Format:** Multiple choice and multiple response

---

## Exam Domain Breakdown

| Domain | Weight | Focus |
|--------|--------|-------|
| 1. Design Secure Architectures | **30%** | IAM, encryption, VPC security |
| 2. Design Resilient Architectures | **26%** | Multi-AZ, DR, Auto Scaling, decoupling |
| 3. Design High-Performing Architectures | **24%** | Compute, storage, DB, networking optimization |
| 4. Design Cost-Optimized Architectures | **20%** | Pricing models, right-sizing, storage classes |

---

## 🔐 Domain 1: Security - Key Patterns (30%)

### IAM Decision Tree
```
Need AWS API access from EC2? → IAM Role (NEVER access keys)
Need cross-account access? → IAM Role with STS:AssumeRole
Need temporary credentials? → STS (AssumeRole / GetSessionToken)
Need user auth for web/mobile? → Cognito User Pools
Need AWS credentials after auth? → Cognito Identity Pools
Need enterprise SSO? → IAM Identity Center (AWS SSO)
```

### Encryption Decision Tree
```
Encrypt S3 at rest (simple)? → SSE-S3
Encrypt S3 at rest (audit/control)? → SSE-KMS
Encrypt S3 at rest (own keys)? → SSE-C
Encrypt in transit? → SSL/TLS (enforce via bucket policy)
Need dedicated HSM? → CloudHSM
Need key rotation? → KMS (automatic or manual)
```

### Security Service Selector
```
Block specific IPs? → NACLs (NOT Security Groups)
Protect against DDoS? → Shield (Standard=free, Advanced=paid)
Block SQL injection/XSS? → WAF
Detect threats (ML)? → GuardDuty
Scan EC2 vulnerabilities? → Inspector
Find sensitive data in S3? → Macie
Centralize findings? → Security Hub
Track API calls? → CloudTrail
Track config changes? → Config
Manage secrets? → Secrets Manager (auto-rotation) or Parameter Store (simpler)
```

---

## 🏗️ Domain 2: Resilience - Key Patterns (26%)

### Multi-AZ vs Multi-Region
```
AZ failure protection → Multi-AZ (RDS, Aurora, EFS, ALB automatically)
Region failure protection → Multi-Region (Aurora Global DB, DynamoDB Global Tables)
```

### DR Strategy Quick Select
```
RTO: Hours, Budget: Low    → Backup & Restore
RTO: 10s min, Budget: Med  → Pilot Light
RTO: Minutes, Budget: High → Warm Standby
RTO: Near zero, Budget: Max → Multi-Site Active-Active
```

### Auto Scaling Key Concepts
```
Target Tracking → Set target metric (easiest, recommended)
Step Scaling → Define scaling steps (for complex scenarios)
Simple Scaling → One alarm = one action (legacy, avoid)
Scheduled Scaling → Time-based (predictable patterns)
Predictive Scaling → ML-based forecasting
```

### Decoupling Patterns
```
Async processing → SQS Queue
Fan-out (1 to many) → SNS Topic
Fan-out + durability → SNS + SQS per consumer
Ordered processing → SQS FIFO
Exactly-once → SQS FIFO + deduplication
Event-driven → EventBridge
Real-time streaming → Kinesis Data Streams
Streaming to S3/Redshift → Kinesis Data Firehose
```

---

## ⚡ Domain 3: Performance - Key Patterns (24%)

### Compute Selection
```
Predictable web workload → EC2 with ALB
Containers (managed infra) → ECS on EC2
Containers (serverless) → ECS on Fargate
Short tasks (<15 min) → Lambda
Quick deployment, no servers → Elastic Beanstalk
HPC with MPI → EC2 Cluster placement + EFA
```

### Storage Selection
```
Object storage → S3
Block storage (single instance) → EBS
Shared file system (Linux/NFS) → EFS
Shared file system (Windows/SMB) → FSx for Windows
High-performance file system → FSx for Lustre
Temporary high-IOPS → Instance Store
```

### Database Selection
```
Relational (MySQL/PostgreSQL) → Aurora (5x perf, auto-scale storage)
Relational (Oracle/SQL Server) → RDS
Key-value / Document → DynamoDB
DynamoDB caching (μs latency) → DAX
General caching (ms latency) → ElastiCache
Data warehouse / Analytics → Redshift
Graph relationships → Neptune
Search → OpenSearch
MongoDB compatible → DocumentDB
Cassandra compatible → Keyspaces
Immutable ledger → QLDB
```

### Caching Strategy
```
Cache DB queries → ElastiCache (Redis/Memcached)
Cache DynamoDB → DAX (transparent, microsecond)
Cache static content → CloudFront (global CDN)
Cache API responses → API Gateway caching
```

### Load Balancer Selection
```
HTTP/HTTPS + path routing → ALB (Layer 7)
TCP/UDP + ultra-low latency → NLB (Layer 4)
Static IPs needed → NLB (supports EIP)
WebSocket → ALB or NLB
3rd party appliances → GWLB (Layer 3)
```

---

## 💰 Domain 4: Cost Optimization - Key Patterns (20%)

### EC2 Pricing Decision Tree
```
Short-term / unpredictable → On-Demand
Steady 24/7 / known type → Reserved Instance (Standard)
Steady 24/7 / flexible type → Savings Plan (Compute)
Fault-tolerant / interruptible → Spot Instance (up to 90% off)
Licensing compliance → Dedicated Host
Dev/test with burst → T3/T3a (burstable)
```

### S3 Cost Optimization
```
Frequent access → Standard
Infrequent, known pattern → Standard-IA
Infrequent, unknown pattern → Intelligent-Tiering
Rarely accessed, instant retrieval → Glacier Instant Retrieval
Archive (hours retrieval OK) → Glacier Flexible
Long-term archive → Glacier Deep Archive (cheapest)
Non-critical, infrequent → One Zone-IA
```

### Common Cost Traps on the Exam
```
NAT Gateway data processing → Use VPC endpoints instead (free for S3/DynamoDB)
Cross-AZ data transfer → Keep resources in same AZ when possible
Cross-Region transfer → Keep resources in same Region
Idle resources → Use Trusted Advisor / Compute Optimizer
Over-provisioned instances → Right-size with Compute Optimizer
EIP not attached → Release unused Elastic IPs
```

---

## 🔑 Critical Exam Concepts

### VPC Essentials
- **Security Groups:** Stateful, ALLOW only, instance level
- **NACLs:** Stateless, ALLOW + DENY, subnet level
- **NAT Gateway:** Outbound internet for private subnets, managed service
- **Internet Gateway:** Bidirectional internet access for public subnets
- **VPC Endpoint (Gateway):** S3 + DynamoDB (free)
- **VPC Endpoint (Interface/PrivateLink):** Other AWS services (paid)

### S3 Essentials
- **Durability:** 99.999999999% (11 nines) for all classes
- **Versioning:** Preserves all versions, enables MFA Delete
- **Object Lock:** WORM (Governance mode vs Compliance mode)
- **Transfer Acceleration:** Fast long-distance S3 uploads
- **Event Notifications:** Trigger Lambda/SQS/SNS on object events
- **Max object size:** 5 TB (use multipart upload for >100 MB)

### RDS vs Aurora
- **RDS:** Up to 5 read replicas, 64 TB storage, 1-2 min failover
- **Aurora:** Up to 15 read replicas, 128 TB storage, <30s failover
- **Aurora:** 6 copies across 3 AZs, auto-scaling storage
- **Aurora Serverless:** Auto-scale compute, pay per ACU-second
- **Aurora Global DB:** Cross-Region, <1s replication, <1 min failover

### DynamoDB Essentials
- **On-Demand:** Pay per request (unpredictable workloads)
- **Provisioned:** Set RCU/WCU with Auto Scaling
- **Global Tables:** Multi-Region, multi-active
- **DAX:** In-memory cache, microsecond latency
- **Streams:** Change capture for event-driven processing
- **TTL:** Auto-expire items (free automatic cleanup)

### Lambda Essentials
- **Timeout:** Max 15 minutes
- **Memory:** 128 MB - 10 GB (CPU scales linearly)
- **Concurrency:** 1,000 per Region (default, can be increased)
- **Storage:** /tmp up to 10 GB, EFS for shared persistent storage
- **Invocation:** Sync, Async, Event Source Mapping
- **Cold Start Fix:** Provisioned Concurrency or SnapStart (Java)

---

## 🎯 Exam Tips & Strategies

### Reading Questions
1. **Read the LAST line first** — it tells you exactly what's being asked
2. **Look for keywords:** "MOST cost-effective," "LEAST operational overhead," "MOST secure," "minimum downtime"
3. **Eliminate obviously wrong answers** first
4. **When two answers seem correct**, choose the one that best matches the keyword

### Common Keyword Mapping
| Keyword | Lean Toward |
|---------|-------------|
| "Serverless" / "No operational overhead" | Lambda, Fargate, Aurora Serverless, DynamoDB |
| "Cost-effective" / "Minimize cost" | Spot, Reserved, Glacier, lifecycle policies |
| "High availability" | Multi-AZ, Auto Scaling, multiple endpoints |
| "Disaster recovery" / "Multi-Region" | Aurora Global, DynamoDB Global, Route 53 |
| "Minimal code changes" | Rehost/Replatform, Elastic Beanstalk, RDS |
| "Decouple" / "Asynchronous" | SQS, SNS, EventBridge |
| "Real-time" / "Streaming" | Kinesis, DynamoDB Streams |
| "Encryption at rest" | KMS, SSE-S3, SSE-KMS |
| "Encryption in transit" | SSL/TLS, HTTPS, VPN |
| "Block IP addresses" | NACL (NOT Security Groups) |
| "Prevent data loss" | Versioning, Object Lock, Backups |
| "Sub-millisecond latency" | ElastiCache, DAX |
| "Shared file system" | EFS (Linux), FSx (Windows) |

### Answer Elimination Strategies
- **If "Dedicated Hosts" is an option** → Usually wrong unless licensing/compliance is mentioned
- **If "Snowmobile" is an option** → Only correct for 10+ PB transfers
- **If "Classic Load Balancer" is an option** → Almost always wrong (legacy)
- **If "NAT Instance" is an option** → Usually wrong (use NAT Gateway)
- **If "CloudWatch Events" is an option** → Correct but prefer "EventBridge" if both listed
- **If a managed service exists** → Prefer it over self-managed

---

## 📝 Last-Minute Review Checklist

- [ ] Know all S3 storage classes and their retrieval times
- [ ] Know the difference between Security Groups and NACLs
- [ ] Know when to use ALB vs NLB
- [ ] Know RDS Multi-AZ vs Read Replicas
- [ ] Know Aurora vs standard RDS advantages
- [ ] Know Lambda limits (15 min, memory, concurrency)
- [ ] Know all Route 53 routing policies
- [ ] Know DR strategies (Backup, Pilot Light, Warm Standby, Multi-Site)
- [ ] Know VPC Endpoint types (Gateway vs Interface)
- [ ] Know IAM role vs IAM user vs STS
- [ ] Know SQS Standard vs FIFO
- [ ] Know Kinesis Data Streams vs Firehose
- [ ] Know all EC2 purchasing options
- [ ] Know Snow Family device capacities
- [ ] Know cross-account access patterns (IAM roles + trust policies)

---

*Good luck with your AWS SAA exam! 🎓*
