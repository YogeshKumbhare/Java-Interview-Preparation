# AWS SAA Exam - High Availability & Disaster Recovery

> **Domain Coverage:** Design Resilient Architectures (26% of exam)
> **Concepts:** Multi-AZ, Multi-Region, RPO, RTO, Backup Strategies, Auto Scaling, Failover Patterns

---

## Questions & Answers

### Question 1
A company runs a critical application on Amazon EC2 behind an Application Load Balancer. The application stores data in Amazon RDS MySQL Multi-AZ. The company's RPO is 1 hour and RTO is 15 minutes.

Which disaster recovery strategy meets these requirements?

- A. Backup and Restore
- B. Pilot Light
- C. Warm Standby
- D. Multi-Site Active-Active

**Correct Answer: C**

**Explanation:** Warm Standby maintains a scaled-down but fully functional version of the application in a secondary Region. It can be scaled up quickly (within minutes) to handle full production traffic. RPO is low (continuous replication) and RTO is ~15 minutes. Backup & Restore has high RTO (hours). Pilot Light requires more time to scale up. Multi-Site Active-Active is overkill and most expensive.

---

### Question 2
A company needs to design an architecture where the application can survive the failure of an entire AWS Region. The application serves global users and requires RPO of 0 (zero data loss) for the database.

Which architecture meets these requirements?

- A. Multi-AZ deployment within a single Region
- B. Amazon Aurora Global Database with cross-Region replicas
- C. Amazon DynamoDB Global Tables
- D. RDS with cross-Region Read Replicas

**Correct Answer: C**

**Explanation:** DynamoDB Global Tables use multi-Region, multi-active replication with last-writer-wins conflict resolution. Writes in any Region are replicated to all other Regions (typically within a second). This provides RPO near 0 with active-active capability. Aurora Global Database has a write Region and read-only secondary Regions (not active-active). RDS Cross-Region Read Replicas involve asynchronous replication with potential data loss.

---

### Question 3
A company runs a web application in us-east-1. They want a disaster recovery site in us-west-2. The company can tolerate a 4-hour RTO but wants to minimize costs.

Which DR strategy should the Solutions Architect implement?

- A. Multi-Site Active-Active
- B. Warm Standby
- C. Pilot Light
- D. Backup and Restore

**Correct Answer: C**

**Explanation:** Pilot Light keeps the minimum critical components running in the DR Region (e.g., database replication) but doesn't run full application infrastructure. When a disaster occurs, you scale out the remaining components (takes 1-4 hours). This is cost-effective while meeting the 4-hour RTO. Backup & Restore may exceed 4 hours. Warm Standby and Multi-Site are more expensive than needed.

---

### Question 4
An organization is planning a migration from on-premises to AWS, and needs a design that will provide greater operational transparency. Which service should be built into the architecture to automate the capture and publishing of custom metrics that will provide this required transparency?

- A. Amazon CloudWatch
- B. AWS CloudTrail
- C. AWS Developer Tools
- D. AWS X-Ray

**Correct Answer: A**

**Explanation:** Amazon CloudWatch is the monitoring and observability service that captures, publishes, and tracks custom metrics. CloudWatch supports publishing custom metrics, setting alarms, creating dashboards, and automated actions. CloudTrail is for API call logging. AWS X-Ray is for tracing requests through distributed applications. AWS Developer Tools is a suite for CI/CD.

---

### Question 5
A company has an Auto Scaling group with Health Check type set to EC2. The instances are behind an ALB. An instance passes EC2 health checks but fails the ALB health checks.

What happens to the instance?

- A. Auto Scaling terminates the instance and launches a replacement
- B. The instance continues to run and receives traffic
- C. The instance continues to run but the ALB stops sending traffic to it
- D. Both A and C

**Correct Answer: C**

**Explanation:** When Auto Scaling health check type is set to EC2, it only considers EC2 status checks. Since the EC2 check passes, Auto Scaling keeps the instance. However, the ALB independently performs health checks and stops routing traffic to unhealthy targets. To have Auto Scaling also respond to ALB health check failures, set the health check type to "ELB".

---

### Question 6
A company needs to ensure that their application data stored in Amazon S3 survives the loss of 2 Availability Zones simultaneously.

Does S3 Standard meet this requirement by default?

- A. No, S3 Standard only replicates within a single AZ
- B. No, you need to enable Cross-Region Replication
- C. Yes, S3 Standard automatically stores data across at least 3 AZs
- D. Yes, but only with S3 Versioning enabled

**Correct Answer: C**

**Explanation:** S3 Standard automatically stores data redundantly across a minimum of 3 AZs within a Region. It's designed for 99.999999999% (11 nines) durability and can sustain the concurrent loss of 2 AZs. No additional configuration is needed. S3 One Zone-IA is the class that stores data in a single AZ.

---

### Question 7
A company has the following DR requirements: RPO = 5 minutes, RTO = 1 hour. They use Amazon Aurora MySQL as their database.

Which Aurora feature helps meet the RPO requirement across Regions?

- A. Aurora Automated Backups (retained for 35 days)
- B. Aurora Global Database (replication lag typically < 1 second)
- C. Aurora Multi-AZ (standby in another AZ)
- D. Manual Aurora snapshots copied to another Region

**Correct Answer: B**

**Explanation:** Aurora Global Database provides cross-Region replication with typical lag of under 1 second, far exceeding the 5-minute RPO requirement. The secondary Region can be promoted in under 1 minute. Automated backups have at most 5-minute granularity but restoring takes time. Multi-AZ protects within a Region only. Manual snapshots don't meet the 5-minute RPO.

---

### Question 8
A company has an application that uses an Amazon RDS database. The database experiences failures approximately once a month. The company wants automatic recovery.

What is the MOST effective solution?

- A. Increase the RDS instance size
- B. Enable Multi-AZ deployment
- C. Create a Read Replica and promote it manually
- D. Take frequent manual snapshots

**Correct Answer: B**

**Explanation:** RDS Multi-AZ provides automatic failover to a standby instance in another AZ. When the primary instance fails, RDS automatically promotes the standby (within 1-2 minutes). No manual intervention is needed. Read Replicas require manual promotion. Snapshots require manual restore. Larger instances don't prevent failures.

---

### Question 9
A company needs to design a solution where the application can scale horizontally. The application stores user session data. Which approach ensures the application remains stateless for horizontal scaling?

- A. Use sticky sessions on the load balancer
- B. Store session data in Amazon ElastiCache Redis
- C. Store session data on EBS volumes
- D. Use larger EC2 instances

**Correct Answer: B**

**Explanation:** To make an application stateless (enabling horizontal scaling), externalize the session state to a shared store like ElastiCache Redis or DynamoDB. This way, any instance can serve any user. Sticky sessions tie users to specific instances (not truly stateless). EBS volumes are instance-specific. Larger instances are vertical scaling, not horizontal.

---

### Question 10
A company has a multi-AZ architecture. During a disaster, they need to redirect traffic from the primary Region to a secondary Region within 30 seconds.

Which service should the Solutions Architect use for traffic management?

- A. Amazon Route 53 with failover routing and health checks
- B. AWS Global Accelerator with endpoint groups
- C. Amazon CloudFront with origin failover
- D. All of the above can work

**Correct Answer: D**

**Explanation:** All three services can handle Region-level failover: Route 53 failover routing (DNS-based, TTL-based propagation). Global Accelerator (near-instant failover, uses AWS network). CloudFront origin failover (for CDN-served content). Global Accelerator provides the fastest failover (~30 seconds or less) since it doesn't depend on DNS TTL propagation.

---

### Question 11
A company runs a payments processing application that requires exactly-once processing of messages. If the application server crashes, the message should not be lost and should not be processed twice.

Which messaging architecture should the Solutions Architect use?

- A. Amazon SNS with Lambda subscriber
- B. Amazon SQS Standard Queue with visibility timeout
- C. Amazon SQS FIFO Queue with deduplication
- D. Amazon Kinesis Data Streams

**Correct Answer: C**

**Explanation:** SQS FIFO queues guarantee exactly-once processing and maintain message order. Content-based deduplication prevents duplicate message delivery. If processing fails, the message becomes visible again after the visibility timeout. Standard SQS provides at-least-once delivery (possible duplicates). SNS doesn't guarantee exactly-once. Kinesis requires checkpoint management.

---

### Question 12
A company wants to achieve high availability for their single-instance RDS database without the additional cost of Multi-AZ.

Which approaches provide basic HA? (Select TWO)

- A. Enable automated backups with point-in-time recovery
- B. Enable Multi-AZ (this is the only option)
- C. Create a read replica for manual failover
- D. Use Amazon Aurora Serverless (has built-in HA)
- E. Take frequent manual snapshots

**Correct Answer: A, C**

**Explanation:** Automated backups with PITR allow recovery to any point in time (within the retention window). A read replica can be manually promoted to primary if the main instance fails. These provide basic HA at lower cost than Multi-AZ. However, both involve manual intervention and downtime. Aurora Serverless has built-in HA but is a different service/cost model.

---

### Question 13
A company has an Auto Scaling group with a minimum of 2 instances and a maximum of 10. The application experiences a gradual traffic increase over 15 minutes.

Which scaling policy is MOST appropriate?

- A. Simple Scaling
- B. Step Scaling
- C. Target Tracking Scaling
- D. Scheduled Scaling

**Correct Answer: C**

**Explanation:** Target Tracking Scaling automatically adjusts capacity to maintain a target metric value (e.g., average CPU at 50%). It continuously adapts to changing traffic patterns. Step Scaling requires manual definition of scaling steps. Simple Scaling has a cooldown period that prevents rapid response. Scheduled Scaling works for predictable patterns, not gradual increases.

---

### Question 14
A company uses Amazon S3 for storing application backups. They need to ensure they can recover from accidental deletion of any object within the last 30 days.

Which combination of features provides this capability?

- A. S3 Versioning + Lifecycle policy to delete old versions after 30 days
- B. S3 Versioning + MFA Delete
- C. S3 Cross-Region Replication
- D. S3 Object Lock with 30-day retention

**Correct Answer: A**

**Explanation:** S3 Versioning retains all versions of objects, including delete markers. If an object is deleted, the previous version is preserved. A lifecycle policy to expire old versions after 30 days controls costs. This provides a 30-day window for recovery. MFA Delete is an additional safeguard but doesn't help with recovery. Object Lock prevents deletion entirely.

---

### Question 15
A company has an application deployed in a single Region using an Auto Scaling group behind an ALB. The company wants to expand to a second Region for disaster recovery with minimum RTO.

Which architecture should the Solutions Architect implement?

- A. Deploy a copy of the application in the second Region, use Route 53 failover routing
- B. Keep AMIs in the second Region and deploy on demand
- C. Use AWS Backup to replicate resources to the second Region
- D. Use CloudFormation StackSets to deploy on demand

**Correct Answer: A**

**Explanation:** Deploying the full application stack in the secondary Region (Warm Standby or Multi-Site) with Route 53 failover routing provides the minimum RTO. Route 53 health checks detect primary Region failures and automatically route traffic to the secondary. Deploying on demand (Pilot Light) increases RTO. CloudFormation deployment takes time.

---

### Question 16
A company needs to ensure their application can handle sudden spikes in traffic, increasing from 100 to 10,000 requests per second in under 2 minutes. The current Auto Scaling group takes 5 minutes to scale.

Which improvement should the Solutions Architect propose?

- A. Use Predictive Scaling with Auto Scaling
- B. Pre-warm the ALB and use a combination of warm pool + step scaling
- C. Increase the minimum capacity
- D. Use larger instance types

**Correct Answer: B**

**Explanation:** Auto Scaling Warm Pool keeps pre-initialized instances stopped/running that can be rapidly launched. This reduces the scaling time from minutes to seconds. Step scaling with aggressive thresholds provides quick response. Pre-warming the ALB prepares it for sudden traffic increases. Increasing minimum capacity wastes resources during low traffic. Predictive scaling needs historical data.

---

### Question 17
A company uses RDS MySQL with Multi-AZ for their production database. During an AZ failure, the application experienced 2 minutes of downtime during failover.

How can the company reduce the failover time?

- A. Switch to Amazon Aurora with Multi-AZ
- B. Use RDS Proxy
- C. Increase the RDS instance size
- D. Both A and B

**Correct Answer: D**

**Explanation:** Aurora failover is typically under 30 seconds (vs 1-2 minutes for RDS). RDS Proxy maintains a pool of database connections and can reduce failover time further by keeping connections alive and redirecting them to the new primary. Together, they minimize failover impact. Instance size doesn't affect failover time.

---

### Question 18
A company has a fleet of EC2 instances running a critical application. They want to be notified immediately when any instance's CPU utilization exceeds 90% for more than 5 minutes.

Which solution should the Solutions Architect implement?

- A. CloudWatch Alarm with SNS notification
- B. AWS CloudTrail event with Lambda
- C. AWS Config Rule with SNS notification
- D. EC2 Instance status check notifications

**Correct Answer: A**

**Explanation:** CloudWatch Alarms monitor metrics and trigger actions when thresholds are breached for specified periods. An alarm watching CPUUtilization > 90% for 5 minutes can send notifications via SNS (email, SMS, Lambda, etc.). CloudTrail logs API calls, not metrics. Config tracks configuration changes. EC2 status checks are about instance health, not CPU utilization.

---

### Question 19
A company is designing a system that needs 99.99% availability. The application should automatically recover from instance and AZ failures.

Which architecture meets the 99.99% availability requirement?

- A. Single EC2 instance with Auto Recovery
- B. Auto Scaling group across 2 AZs with 2 instances minimum
- C. Auto Scaling group across 3 AZs with ALB and RDS Multi-AZ
- D. Single AZ with multiple EC2 instances

**Correct Answer: C**

**Explanation:** 99.99% availability requires: multiple AZs (minimum 3 for true HA), Auto Scaling for instance failure recovery, ALB for traffic distribution, and RDS Multi-AZ for database HA. Single instances or single-AZ architectures can't achieve 99.99%. 2 AZs may not provide sufficient redundancy for 99.99%.

---

### Question 20
A company has an application that writes data to Amazon DynamoDB. The company wants to capture all changes to the items and trigger a Lambda function for processing whenever an item changes.

Which DynamoDB feature should the Solutions Architect use?

- A. DynamoDB Queries
- B. DynamoDB Streams
- C. DynamoDB Global Tables
- D. DynamoDB Transactions

**Correct Answer: B**

**Explanation:** DynamoDB Streams captures item-level changes in near-real-time. Lambda can be configured as a trigger to automatically process stream records whenever items are created, updated, or deleted. Streams retain data for 24 hours. This is the event-driven integration pattern for DynamoDB. Global Tables provide replication. Transactions provide ACID operations. Queries read data on demand.

---

## Quick Reference: DR Strategies (Lowest to Highest Cost / Lowest to Highest Speed)

| Strategy | RTO | RPO | Cost | Description |
|----------|-----|-----|------|-------------|
| Backup & Restore | Hours | Hours | $ | Restore from backups when disaster occurs |
| Pilot Light | 10s of minutes | Minutes | $$ | Core infrastructure running, scale up on demand |
| Warm Standby | Minutes | Seconds-Minutes | $$$ | Scaled-down version running in DR Region |
| Multi-Site Active-Active | Near zero | Near zero | $$$$ | Full production in both Regions |

## Quick Reference: AWS HA Building Blocks

| Component | HA Feature |
|-----------|-----------|
| EC2 | Auto Scaling group across multiple AZs |
| RDS | Multi-AZ deployment |
| Aurora | Multi-AZ by default (6 copies across 3 AZs) |
| DynamoDB | Multi-AZ by default, Global Tables for multi-Region |
| S3 | Multi-AZ by default (11 nines durability) |
| EFS | Multi-AZ by default |
| ALB/NLB | Multi-AZ by default |
| ElastiCache | Multi-AZ with auto-failover (Redis) |
