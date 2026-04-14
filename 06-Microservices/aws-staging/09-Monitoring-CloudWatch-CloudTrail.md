# AWS SAA Exam - Monitoring & Logging (CloudWatch, CloudTrail, X-Ray)

> **Domain Coverage:** Design Secure Architectures, Design Resilient Architectures
> **Services:** CloudWatch (Metrics, Alarms, Logs, Dashboards), CloudTrail, AWS X-Ray, VPC Flow Logs, AWS Config, AWS Health Dashboard, Trusted Advisor

---

## Questions & Answers

### Question 1
A company needs to monitor the CPU utilization of their EC2 instances and automatically trigger an alarm when CPU exceeds 80% for 5 consecutive minutes.

Which service and configuration should the Solutions Architect use?

- A. AWS CloudTrail with event notifications
- B. Amazon CloudWatch Alarm with CPUUtilization metric, period 60s, evaluation periods 5, threshold 80%
- C. AWS Config Rule for CPU utilization
- D. Amazon Inspector with CPU monitoring

**Correct Answer: B**

**Explanation:** CloudWatch Alarms monitor metrics and trigger actions. Configuring an alarm on the `CPUUtilization` metric with a 60-second period and 5 evaluation periods (5 minutes total) at 80% threshold provides the exact monitoring needed. CloudTrail logs API calls. Config tracks configurations. Inspector scans for vulnerabilities.

---

### Question 2
A company wants to track all API calls made in their AWS account for security auditing and compliance. The logs must be stored permanently and be tamper-proof.

Which configuration should the Solutions Architect implement?

- A. CloudWatch Logs with unlimited retention
- B. CloudTrail with S3 storage, log file validation, and S3 Object Lock
- C. VPC Flow Logs
- D. AWS Config recording

**Correct Answer: B**

**Explanation:** CloudTrail logs all AWS API calls. Storing logs in S3 provides permanent storage. Log file validation ensures integrity (tamper detection via SHA-256 hashing). S3 Object Lock (Compliance Mode) prevents deletion by anyone. This combination provides permanent, tamper-proof API audit logs. CloudWatch Logs doesn't capture API calls. VPC Flow Logs capture network traffic.

---

### Question 3
A company has a distributed microservices application. They need to trace requests as they flow through multiple services to identify performance bottlenecks.

Which service should the Solutions Architect use?

- A. Amazon CloudWatch Logs
- B. AWS X-Ray
- C. AWS CloudTrail
- D. Amazon CloudWatch Metrics

**Correct Answer: B**

**Explanation:** AWS X-Ray provides distributed tracing for microservices. It traces requests as they travel through the application, creating a service map that visualizes the call chain and identifies latency bottlenecks. X-Ray integrates with Lambda, API Gateway, ECS, EC2, and Elastic Beanstalk. CloudWatch Logs/Metrics provide monitoring but not request-level tracing.

---

### Question 4
A company runs EC2 instances in a VPC. They need to monitor and log all network traffic flowing through their network interfaces for security analysis.

Which feature should the Solutions Architect enable?

- A. CloudTrail Data Events
- B. VPC Flow Logs
- C. CloudWatch Network metrics
- D. AWS Config

**Correct Answer: B**

**Explanation:** VPC Flow Logs capture information about IP traffic going to and from network interfaces in the VPC. They can be published to CloudWatch Logs, S3, or Kinesis Data Firehose. Flow logs capture source/destination IPs, ports, protocol, action (ACCEPT/REJECT), and packet/byte counts. This is essential for security analysis, troubleshooting, and compliance.

---

### Question 5
A company wants to be notified when their AWS resources are not configured according to company security policies. For example, they want to detect S3 buckets with public access or EC2 instances without required tags.

Which service should the Solutions Architect use?

- A. Amazon GuardDuty
- B. AWS Config with Config Rules
- C. AWS CloudTrail
- D. Amazon Inspector

**Correct Answer: B**

**Explanation:** AWS Config continuously monitors and records AWS resource configurations. Config Rules evaluate whether resources comply with desired configurations (e.g., no public S3 buckets, required tags). Non-compliant resources trigger notifications via SNS. GuardDuty detects threats. CloudTrail logs API calls. Inspector scans for vulnerabilities in EC2.

---

### Question 6
A company needs to aggregate CloudWatch metrics from EC2 instances running a custom application across multiple Regions into a single dashboard.

Which CloudWatch feature supports this?

- A. CloudWatch Agent with custom metrics
- B. CloudWatch Cross-Account Observability
- C. CloudWatch Dashboards with cross-Region widgets
- D. Both B and C

**Correct Answer: D**

**Explanation:** CloudWatch Cross-Account Observability enables viewing and monitoring metrics across multiple accounts. CloudWatch Dashboards support cross-Region data sources, allowing you to add widgets from different Regions on a single dashboard. Together, they provide a unified view of metrics across Regions and accounts.

---

### Question 7
A company wants to monitor custom application metrics such as the number of active users and request queue depth. These metrics are not available as default CloudWatch metrics.

What should the Solutions Architect do?

- A. Enable detailed monitoring on EC2 instances
- B. Install the CloudWatch Agent and publish custom metrics using the PutMetricData API
- C. Use AWS X-Ray for custom metrics
- D. Use VPC Flow Logs

**Correct Answer: B**

**Explanation:** The CloudWatch Agent runs on EC2 instances and can publish custom metrics to CloudWatch using the PutMetricData API. You can define application-specific metrics (active users, queue depth, etc.). Detailed monitoring only increases the frequency of default EC2 metrics (1-minute vs 5-minute). X-Ray provides tracing, not custom metrics. Flow Logs capture network data.

---

### Question 8
A company has a CloudWatch Alarm set on CPU utilization. The alarm should automatically scale the Auto Scaling group AND send an email notification when triggered.

How many alarm actions should be configured?

- A. One action — either scaling or notification, not both
- B. Two actions — one for Auto Scaling, one for SNS notification
- C. Configure two separate alarms for the same metric
- D. Use Step Functions to orchestrate both actions

**Correct Answer: B**

**Explanation:** CloudWatch Alarms support multiple actions. You can configure both an Auto Scaling action (to scale the ASG) and an SNS notification action (to send email) on the same alarm. When the alarm transitions to ALARM state, both actions execute. No need for separate alarms or orchestration.

---

### Question 9
A company needs to retain CloudWatch Logs for 1 year for compliance. Currently, logs are retained indefinitely, consuming significant storage.

What should the Solutions Architect do to optimize costs while meeting the retention requirement?

- A. Set log group retention to 365 days
- B. Export logs to S3 daily using a scheduled Lambda function
- C. Set retention to 365 days AND export older logs to S3 Glacier for long-term archiving
- D. Delete logs manually every year

**Correct Answer: C**

**Explanation:** Setting the log group retention to 365 days automatically removes logs older than 1 year from CloudWatch. For cost optimization, exporting logs to S3 (with lifecycle to Glacier) before the retention period expires provides cheapest long-term storage. CloudWatch Logs storage is more expensive than S3/Glacier. Simple 365-day retention works but is more expensive than S3 archival.

---

### Question 10
A company needs to detect and respond to EC2 instance terminations in near-real-time to trigger automated remediation.

Which approach should the Solutions Architect implement?

- A. CloudWatch Alarm on InstanceCount metric
- B. EventBridge rule for EC2 instance state change events
- C. CloudTrail with SNS notification on TerminateInstances
- D. AWS Config Rule for running instances

**Correct Answer: B**

**Explanation:** EventBridge captures EC2 instance state-change events in near-real-time. A rule can filter for "terminated" state and trigger a Lambda function for automated remediation. This provides the fastest detection and response. CloudTrail with SNS has higher latency. CloudWatch metrics have 5-minute delays. Config captures configuration changes, not events.

---

### Question 11
A company runs a multi-account AWS environment. They need centralized logging of all API activities across all accounts.

Which architecture should the Solutions Architect implement?

- A. CloudTrail trail in each account writing to a central S3 bucket
- B. CloudTrail Organization trail writing to a central S3 bucket
- C. CloudWatch Logs with cross-account log group sharing
- D. VPC Flow Logs from all accounts to a central location

**Correct Answer: B**

**Explanation:** CloudTrail Organization trail automatically logs API activity from all accounts in the AWS Organization to a central S3 bucket. This is managed from the management account and doesn't require individual trail configuration in each account. Individual trails per account work but require manual setup and maintenance.

---

### Question 12
A company wants to monitor the memory utilization and disk space of their EC2 instances. These metrics are not available in the default CloudWatch metrics.

What should the Solutions Architect do?

- A. Enable detailed monitoring on EC2
- B. Install the CloudWatch Unified Agent on the instances
- C. Use AWS Systems Manager inventory
- D. Configure EC2 Enhanced Monitoring

**Correct Answer: B**

**Explanation:** The CloudWatch Unified Agent collects both system-level metrics (memory, disk, swap) and application log data from EC2 instances. Default CloudWatch metrics don't include memory or disk utilization. Detailed monitoring only changes the frequency of existing metrics. SSM inventory collects software/configuration data. Enhanced Monitoring is for RDS, not EC2.

---

### Question 13
A company wants to receive notifications about AWS service disruptions, scheduled maintenance events, and account-specific issues affecting their resources.

Which service provides this information?

- A. AWS CloudTrail
- B. AWS Personal Health Dashboard (AWS Health)
- C. AWS Trusted Advisor
- D. Amazon CloudWatch

**Correct Answer: B**

**Explanation:** AWS Personal Health Dashboard (AWS Health) provides personalized alerts about AWS service disruptions, scheduled maintenance, and account-specific issues. It shows events relevant to your specific resources. Trusted Advisor provides best practice recommendations. CloudTrail logs API calls. CloudWatch monitors metrics.

---

### Question 14
A company wants to establish AWS best practice recommendations for cost optimization, security, fault tolerance, performance, and service limits.

Which service provides these recommendations?

- A. AWS Config
- B. AWS Trusted Advisor
- C. Amazon Inspector
- D. AWS Security Hub

**Correct Answer: B**

**Explanation:** AWS Trusted Advisor provides automated checks against best practices in five categories: cost optimization, security, fault tolerance, performance, and service limits. It recommends actions to improve your AWS environment. Business/Enterprise Support plans provide access to all checks. Config tracks compliance. Inspector scans vulnerabilities. Security Hub aggregates security findings.

---

### Question 15
A company has a Lambda function that occasionally experiences high latency. They need to identify which downstream service call is causing the slowdown.

Which tool should the Solutions Architect use?

- A. CloudWatch Logs Insights
- B. AWS X-Ray with service map
- C. CloudWatch Contributor Insights
- D. Lambda function logs

**Correct Answer: B**

**Explanation:** AWS X-Ray creates a service map showing all downstream calls from the Lambda function with latency data. You can identify exactly which service call (DynamoDB, S3, external API, etc.) is causing the slowdown. X-Ray traces show the time spent in each segment. CloudWatch Logs can show timing data but requires manual analysis. X-Ray provides visual, automated latency analysis.

---

### Question 16
A company uses CloudTrail to log API calls. They want to trigger automated responses when specific high-risk API calls are made (e.g., DeleteTrail, StopLogging, CreateUser).

Which solution provides near-real-time detection and response?

- A. CloudTrail with S3 event notifications
- B. CloudTrail integration with EventBridge + Lambda
- C. CloudTrail Log File Validation
- D. CloudTrail Insights

**Correct Answer: B**

**Explanation:** CloudTrail sends events to EventBridge in near-real-time. EventBridge rules can filter specific API calls (e.g., `DeleteTrail`, `CreateUser`) and trigger Lambda functions for automated response (alerting, remediation, investigation). S3 event notifications have longer delivery times. Log File Validation checks integrity. CloudTrail Insights detects unusual activity patterns.

---

### Question 17
A company needs to monitor the health and performance of their Amazon RDS database. They want to identify SQL queries that are consuming the most resources.

Which feature should the Solutions Architect enable?

- A. RDS Enhanced Monitoring
- B. RDS Performance Insights
- C. CloudWatch RDS metrics
- D. AWS X-Ray

**Correct Answer: B**

**Explanation:** RDS Performance Insights provides a dashboard that helps identify resource-consuming SQL queries. It shows database load by query, wait events, and top SQL statements. Enhanced Monitoring provides OS-level metrics (CPU, memory, I/O at process level). CloudWatch provides database-level metrics (CPU, connections, IOPS). X-Ray traces application requests, not database queries.

---

### Question 18
A company needs to set up anomaly detection on key CloudWatch metrics to automatically detect unusual patterns without manually setting thresholds.

Which CloudWatch feature should the Solutions Architect use?

- A. CloudWatch Alarms with static thresholds
- B. CloudWatch Anomaly Detection
- C. CloudWatch Contributor Insights
- D. CloudWatch Metric Math

**Correct Answer: B**

**Explanation:** CloudWatch Anomaly Detection uses machine learning to analyze historical metric data and create a dynamic expected value band. It automatically detects anomalies when metrics fall outside the expected range, without requiring manual threshold configuration. This is ideal for metrics with variable patterns (seasonal, day/night). Static thresholds require manual tuning.

---

### Question 19
A company runs a web application and wants to log all HTTP requests processed by their Application Load Balancer, including client IP, latency, and request paths.

Which feature should the Solutions Architect enable?

- A. ALB Access Logs
- B. VPC Flow Logs
- C. CloudTrail Data Events
- D. CloudWatch Metrics

**Correct Answer: A**

**Explanation:** ALB Access Logs capture detailed information about every request processed by the load balancer, including client IP, request URL, latency, response code, and more. Logs are stored in S3. VPC Flow Logs capture IP-level network traffic (no HTTP details). CloudTrail logs API management calls to the ALB service, not request-level data. CloudWatch provides aggregated metrics.

---

### Question 20
A company wants to receive a weekly summary of AWS cost optimization opportunities, including unused resources, idle load balancers, and underutilized EC2 instances.

Which service provides this insight?

- A. AWS Cost Explorer
- B. AWS Trusted Advisor (with Business support)
- C. AWS Budgets
- D. AWS Compute Optimizer

**Correct Answer: B**

**Explanation:** AWS Trusted Advisor (with Business or Enterprise support) provides checks for cost optimization including idle load balancers, underutilized EC2 instances, unused EBS volumes, and more. It can send weekly notifications. Cost Explorer shows spending patterns. Budgets alert on spending thresholds. Compute Optimizer provides EC2 right-sizing recommendations specifically.

---

## Quick Reference: Monitoring Services Cheat Sheet

| Service | What It Does |
|---------|-------------|
| **CloudWatch Metrics** | Monitor AWS resource metrics (CPU, network, disk) |
| **CloudWatch Alarms** | Alert when metrics cross thresholds |
| **CloudWatch Logs** | Collect, store, and analyze log data |
| **CloudWatch Dashboards** | Visual panels for metrics and logs |
| **CloudWatch Anomaly Detection** | ML-based anomaly detection |
| **CloudTrail** | Log ALL AWS API calls (who, when, what) |
| **CloudTrail Insights** | Detect unusual API activity |
| **X-Ray** | Distributed tracing for microservices |
| **VPC Flow Logs** | Network traffic logs at VPC/subnet/ENI level |
| **AWS Config** | Configuration recording and compliance |
| **GuardDuty** | Threat detection using ML |
| **Inspector** | Vulnerability scanning (EC2, ECR) |
| **Health Dashboard** | AWS service and personal health events |
| **Trusted Advisor** | Best practice recommendations |
| **Compute Optimizer** | Right-sizing recommendations |

## Quick Reference: CloudWatch Default vs Custom Metrics

| Default Metrics (Free) | Custom Metrics (Agent Required) |
|------------------------|-------------------------------|
| CPUUtilization | Memory utilization |
| NetworkIn/Out | Disk space used/available |
| DiskReadOps/WriteOps | Swap space used |
| StatusCheckFailed | Number of processes |
| EBS Read/Write operations | Custom application metrics |

## Quick Reference: Log Storage Best Practices

| Log Type | Destination | Retention |
|----------|-------------|-----------|
| Application Logs | CloudWatch Logs → S3 | Based on compliance |
| API Calls | CloudTrail → S3 | Indefinite + Object Lock |
| Network Traffic | VPC Flow Logs → S3/CloudWatch | 30-90 days typically |
| ALB Access Logs | S3 | 30-90 days typically |
| S3 Access Logs | Separate S3 bucket | Based on compliance |
