# AWS SAA Exam - Cost Optimization

> **Domain Coverage:** Design Cost-Optimized Architectures (20% of exam)
> **Concepts:** Reserved Instances, Savings Plans, Spot Instances, Right-sizing, Storage Tiers, Data Transfer Costs, Cost Explorer, Budgets, Compute Optimizer

---

## Questions & Answers

### Question 1
A company runs a production web application 24/7 on EC2 instances. The instance type has been stable for the past year and is expected to remain the same for the next 3 years.

Which purchasing option provides the MAXIMUM cost savings?

- A. On-Demand Instances
- B. 1-year Standard Reserved Instance (Partial Upfront)
- C. 3-year Standard Reserved Instance (All Upfront)
- D. 3-year Convertible Reserved Instance (All Upfront)

**Correct Answer: C**

**Explanation:** 3-year Standard Reserved Instance with All Upfront payment provides the maximum discount (up to 72% compared to On-Demand). For stable, predictable workloads with a known instance type, Standard RIs offer the best savings. Convertible RIs provide flexibility to change instance types but offer lower discounts (~54%). All Upfront maximizes the discount.

---

### Question 2
A company runs multiple applications across various EC2 instance types and Regions. They want a flexible pricing model that provides savings without being locked to specific instance types.

Which option should the Solutions Architect recommend?

- A. Standard Reserved Instances
- B. Convertible Reserved Instances
- C. Compute Savings Plans
- D. EC2 Instance Savings Plans

**Correct Answer: C**

**Explanation:** Compute Savings Plans provide the most flexibility — savings apply across any EC2 instance type, Region, OS, or tenancy. They also apply to Fargate and Lambda. EC2 Instance Savings Plans are locked to a specific instance family in a specific Region. Standard RIs are locked to specific instance types within an AZ.

---

### Question 3
A company's data analytics team runs large Hadoop jobs that process data in parallel. The jobs can handle interruptions and resubmit failed tasks. The jobs typically run for 2-6 hours.

Which EC2 purchasing option should the Solutions Architect recommend?

- A. On-Demand Instances
- B. Spot Instances
- C. Reserved Instances
- D. Dedicated Instances

**Correct Answer: B**

**Explanation:** Spot Instances provide up to 90% savings compared to On-Demand and are ideal for fault-tolerant, interruptible workloads like Hadoop jobs. The 2-minute termination notice gives the application time to check-point and redistribute tasks. Hadoop's distributed nature means it can handle node failures gracefully. On-Demand and Reserved are unnecessarily expensive for this use case.

---

### Question 4
A company stores 100 TB of log data in S3 Standard. Analysis shows that only 5% of the data is accessed in any given month, and the access patterns are unpredictable.

Which S3 storage class should the Solutions Architect recommend to minimize costs?

- A. S3 Standard-IA
- B. S3 One Zone-IA
- C. S3 Intelligent-Tiering
- D. S3 Glacier

**Correct Answer: C**

**Explanation:** S3 Intelligent-Tiering automatically moves data between access tiers based on actual usage patterns. With only 5% accessed monthly but unpredictable access patterns, Intelligent-Tiering optimizes costs automatically without retrieval fees. Standard-IA charges retrieval fees for each access. One Zone-IA has lower durability. Glacier introduces retrieval delays.

---

### Question 5
A company has a development environment that runs from 8 AM to 6 PM, Monday through Friday. The environment is completely idle outside these hours.

Which approach minimizes costs for the development environment?

- A. Reserved Instances for all development instances
- B. On-Demand Instances with automated start/stop using EventBridge + Lambda
- C. Spot Instances with Auto Scaling
- D. Always-on On-Demand Instances

**Correct Answer: B**

**Explanation:** Scheduling instance start/stop with EventBridge rules and Lambda functions means you only pay for 10 hours/day, 5 days/week (50 hours vs 168 hours/week — 70% savings). Reserved Instances charge for 24/7 regardless of usage. Spot Instances might not always be available when needed. Always-on instances waste money during idle hours.

---

### Question 6
A company runs an application that stores session data in ElastiCache Redis. The data is recreatable from the database if lost. The company wants to reduce ElastiCache costs.

Which approach should the Solutions Architect use?

- A. Use Reserved Nodes for ElastiCache
- B. Use smaller node types
- C. Disable Multi-AZ for the development environment
- D. All of the above

**Correct Answer: D**

**Explanation:** All approaches reduce costs: Reserved Nodes provide up to 55% savings for production. Smaller nodes (right-sizing) reduce hourly costs if current nodes are oversized. Disabling Multi-AZ for non-production saves the standby node cost. Since the data is recreatable, reduced HA is acceptable for dev. Apply all optimizations where appropriate.

---

### Question 7
A company has 50 TB of data in S3 Standard. The data has not been accessed in the past 90 days but regulation requires it be kept for 7 years. The data must be retrievable within 5 minutes if needed.

Which S3 storage class minimizes costs while meeting the retrieval requirement?

- A. S3 Glacier Flexible Retrieval
- B. S3 Glacier Instant Retrieval
- C. S3 Glacier Deep Archive
- D. S3 Standard-IA

**Correct Answer: B**

**Explanation:** S3 Glacier Instant Retrieval provides millisecond access (within seconds, well under 5 minutes) at a lower cost than Standard-IA. It's designed for rarely accessed data that needs immediate retrieval. Glacier Flexible Retrieval can take 1-12 hours. Deep Archive takes 12-48 hours. Standard-IA is more expensive than Glacier Instant Retrieval for data accessed less than once per quarter.

---

### Question 8
A company transferring data between an S3 bucket and EC2 instances in the same Region notices high data transfer costs on their AWS bill.

What is causing the high data transfer costs?

- A. Data transfer between S3 and EC2 in the same Region is always charged
- B. The EC2 instances are accessing S3 through a NAT Gateway
- C. The S3 bucket is in a different AZ
- D. S3 Transfer Acceleration is enabled

**Correct Answer: B**

**Explanation:** Data transfer between S3 and EC2 in the same Region is free when accessed through a VPC endpoint (Gateway Endpoint) or the internet. However, if EC2 instances in a private subnet access S3 through a NAT Gateway, data processing charges apply (~$0.045/GB). Using an S3 Gateway Endpoint (free) eliminates this cost. This is a common cost optimization on the exam.

---

### Question 9
A company has multiple AWS accounts and wants to receive alerts when any single account's monthly spending exceeds $5,000.

Which service should the Solutions Architect use?

- A. AWS Cost Explorer
- B. AWS Budgets
- C. AWS Trusted Advisor
- D. AWS Cost and Usage Report

**Correct Answer: B**

**Explanation:** AWS Budgets allows you to set custom cost budgets and receive alerts when actual or forecasted spending exceeds the threshold. You can configure email and SNS notifications. Cost Explorer visualizes spending but doesn't alert. Trusted Advisor provides recommendations but not budget alerts. Cost and Usage Report provides detailed billing data but no alerting.

---

### Question 10
A company runs several EC2 instances of varying types. AWS Compute Optimizer shows that many instances are over-provisioned. The company wants to optimize instance types.

What should the Solutions Architect do?

- A. Replace all instances with the smallest available type
- B. Follow AWS Compute Optimizer right-sizing recommendations
- C. Use Spot Instances for everything
- D. Consolidate all workloads onto fewer large instances

**Correct Answer: B**

**Explanation:** AWS Compute Optimizer analyzes CloudWatch metrics (CPU, memory, network) and provides specific right-sizing recommendations for each instance. It recommends appropriate instance types based on actual utilization patterns. Simply using the smallest type might under-provision. Spot Instances aren't appropriate for all workloads. Consolidation may not optimize individual workload needs.

---

### Question 11
A company uses Amazon RDS Multi-AZ for their development database. The development team only uses the database during business hours.

Which changes would reduce costs? (Select TWO)

- A. Disable Multi-AZ for the development database
- B. Use RDS Reserved Instances for the development database
- C. Stop the RDS instance during non-business hours
- D. Switch to a smaller instance type
- E. Delete the database

**Correct Answer: A, C**

**Explanation:** Disabling Multi-AZ for development saves the cost of the standby instance (production-grade HA isn't needed for dev). Stopping the RDS instance during off-hours saves compute costs (you still pay for storage). Reserved Instances for dev that's used part-time may not save money. Smaller instance types help but aren't one of the TWO best answers here. Deleting the database isn't practical.

---

### Question 12
A company processes images uploaded to S3. Processing takes 2-3 seconds per image. The company currently uses a fleet of m5.xlarge EC2 instances running 24/7, but the average CPU utilization is only 10%.

Which architecture change provides the GREATEST cost savings?

- A. Right-size to m5.large instances
- B. Use Reserved Instances
- C. Replace EC2 with Lambda functions triggered by S3 events
- D. Use Spot Instances

**Correct Answer: C**

**Explanation:** With 10% average CPU utilization and 2-3 second processing, the workload is highly variable and event-driven — ideal for Lambda. Lambda charges per invocation and execution time (100ms granularity), so you only pay when images are actually being processed. The EC2 fleet runs 24/7 regardless of load. This switch could reduce costs by 90%+ for bursty, event-driven workloads.

---

### Question 13
A company has CloudFront distributions serving content globally. They want to analyze if all edge locations are necessary, as some regions only generate 1% of total traffic.

How can the company reduce CloudFront costs?

- A. Use CloudFront Price Class 100 (cheapest edge locations only)
- B. Use CloudFront Price Class 200 (exclude most expensive regions)
- C. Reduce the TTL on cached objects
- D. A or B depending on which regions to exclude

**Correct Answer: D**

**Explanation:** CloudFront Price Classes let you select which edge locations to use. Price Class 100 uses only the cheapest locations (US, EU). Price Class 200 excludes the most expensive locations (South America, Australia, Asia expensive). Price Class All uses all locations. Choosing the appropriate Price Class based on your user distribution reduces costs. Reducing TTL increases origin requests (higher cost).

---

### Question 14
A company uses an on-premises 10 Gbps connection to transfer data to S3. They're paying high data transfer costs. The data transfer is approximately 50 TB per month.

How can the company reduce data transfer costs?

- A. Use AWS Direct Connect instead of the internet
- B. Compress data before uploading
- C. Use S3 Transfer Acceleration
- D. Both A and B

**Correct Answer: D**

**Explanation:** Direct Connect offers lower data transfer rates compared to internet-based transfer. Compressing data reduces the volume transferred. Together, they minimize costs. Data transfer IN to S3 from the internet is free, but Direct Connect data transfer IN also has costs — however, they're lower per GB than internet egress. Compression reduces transfers regardless of connection type. Transfer Acceleration adds cost, not reduces it.

---

### Question 15
A company runs a web application on EC2 instances. They pay for Elastic IP addresses assigned to stopped instances and unused EBS volumes.

Which combination of tools helps identify and eliminate this waste? (Select TWO)

- A. AWS Trusted Advisor (cost optimization checks)
- B. AWS Cost Explorer with resource-level cost breakdown
- C. Amazon Inspector
- D. AWS Config Rules for unused resources
- E. AWS Systems Manager Inventory

**Correct Answer: A, B**

**Explanation:** Trusted Advisor checks for cost optimization issues including unassociated Elastic IP addresses, underutilized EBS volumes, and idle resources. Cost Explorer with resource-level granularity shows which resources are generating costs. Together, they identify waste for remediation. Config Rules can detect but don't specifically focus on cost. Inspector is for security vulnerabilities.

---

### Question 16
A company hosts a static website on S3. They also use CloudFront. The company realizes they're paying for S3 request costs when CloudFront serves cached content.

How can they further reduce costs?

- A. Increase CloudFront cache TTL to reduce origin requests
- B. Enable CloudFront Origin Shield
- C. Use S3 Intelligent-Tiering
- D. Both A and B

**Correct Answer: D**

**Explanation:** Increasing TTL means CloudFront serves cached content longer, reducing S3 request costs. Origin Shield adds a centralized cache layer between CloudFront and S3, further reducing origin requests (especially helpful with multiple edge locations requesting the same content). Together, they dramatically reduce S3 request costs. Intelligent-Tiering optimizes storage cost, not request cost.

---

### Question 17
A company wants to purchase Reserved Instances but is unsure which instance types to commit to.

Which tool helps analyze usage patterns and recommend Reserved Instance purchases?

- A. AWS Compute Optimizer
- B. AWS Cost Explorer Reserved Instance Recommendations
- C. AWS Trusted Advisor
- D. AWS Budgets

**Correct Answer: B**

**Explanation:** AWS Cost Explorer provides specific RI purchase recommendations based on historical usage patterns. It analyzes your past 7-30 days of usage and recommends the optimal RI type, term, and payment option to maximize savings. Compute Optimizer recommends instance types (right-sizing). Trusted Advisor shows general RI utilization. Budgets track spending.

---

### Question 18
A company is designing a new application that will use DynamoDB. The traffic pattern is highly unpredictable — some days have 10x more traffic than others.

Which DynamoDB capacity mode minimizes costs?

- A. Provisioned capacity with Auto Scaling
- B. On-demand capacity mode
- C. Reserved capacity
- D. Provisioned capacity with manual scaling

**Correct Answer: B**

**Explanation:** DynamoDB On-Demand capacity mode automatically scales to handle any level of traffic and charges per request. For highly unpredictable patterns with potentially 10x variation, On-Demand avoids the over-provisioning costs of provisioned capacity. Provisioned with Auto Scaling has scaling limits and may not react quickly enough to sudden spikes. Reserved capacity makes sense for predictable workloads.

---

### Question 19
A company uses AWS Lambda functions that each run for 100ms. The functions are invoked 1 million times per month. The company wants to reduce Lambda costs.

Which optimization should the Solutions Architect try?

- A. Reduce the memory allocation (currently 1024 MB) if the function uses less
- B. Increase the memory to reduce execution time
- C. Use Provisioned Concurrency
- D. Evaluate whether reducing memory or increasing it produces lower total cost

**Correct Answer: D**

**Explanation:** Lambda cost = number of requests × execution time × memory allocated. Reducing memory lowers per-ms cost but may increase execution time. Increasing memory adds CPU and can reduce execution time. The optimal configuration balances memory and duration for the lowest total cost. AWS Lambda Power Tuning tool can help find the optimal memory setting.

---

### Question 20
A company has a data pipeline that transfers 10 TB of data daily from EC2 instances in us-east-1 to S3 in eu-west-1. The company wants to reduce data transfer costs.

Which approach should the Solutions Architect recommend?

- A. Use S3 Transfer Acceleration
- B. Compress the data before transfer
- C. Move the S3 bucket to us-east-1 (same Region as EC2)
- D. Use CloudFront for the transfer

**Correct Answer: C**

**Explanation:** Cross-Region data transfer costs $0.02/GB (10 TB/day = ~$200/day = ~$6,000/month). Same-Region data transfer between S3 and EC2 is free. If possible, keeping S3 and EC2 in the same Region eliminates this cost entirely. Compression reduces volume but still incurs cross-Region charges. Transfer Acceleration and CloudFront add costs.

---

### Question 21
A company wants to analyze their AWS spending and visualize cost trends over the past 12 months, broken down by service and account.

Which tool should the Solutions Architect use?

- A. AWS Budgets
- B. AWS Cost Explorer
- C. AWS Cost and Usage Report (CUR)
- D. AWS Billing Dashboard

**Correct Answer: B**

**Explanation:** AWS Cost Explorer provides interactive visualization of cost and usage data. It supports filtering by service, account, tag, Region, etc., and shows trends over time (up to 13 months historical). Budgets are for alerting. CUR provides the most detailed data but requires Athena/QuickSight for visualization. The Billing Dashboard shows a simple current-month summary.

---

### Question 22
A company uses NAT Gateways for outbound internet access from private subnets. NAT Gateway data processing charges are significant (~$0.045/GB).

How can the company reduce NAT Gateway costs?

- A. Use S3 Gateway VPC Endpoints for S3 traffic
- B. Use VPC interface endpoints for frequently used AWS services
- C. Move instances to public subnets (where appropriate)
- D. All of the above

**Correct Answer: D**

**Explanation:** All approaches reduce NAT Gateway traffic and costs: Gateway VPC Endpoints for S3 (free, handles the most common traffic). Interface endpoints for other AWS services (cheaper than NAT Gateway data processing). Moving appropriate services to public subnets eliminates NAT Gateway usage entirely. NAT Gateway data processing charges are often one of the largest cost items in VPC architecture.

---

### Question 23
A company runs a multi-tier application. The data transfer between the web tier (public subnet) and application tier (private subnet) in the same AZ is appearing on their bill.

Is this data transfer charged?

- A. Yes, all data transfer between subnets is charged
- B. No, data transfer within the same AZ is free regardless of subnet
- C. It depends on whether the subnets are private or public
- D. Only if they use a NAT Gateway

**Correct Answer: B**

**Explanation:** Data transfer between EC2 instances within the same AZ is free, regardless of whether instances are in the same or different subnets (public or private). Cross-AZ data transfer costs ~$0.01/GB. Cross-Region costs more. If the bill shows data transfer charges, the instances might be in different AZs due to how the subnets are configured.

---

### Question 24
A company has over 500 EC2 instances. Many instances run at an average CPU of 5-15%. The company wants to reduce waste.

Which AWS service provides RIGHT-SIZING recommendations?

- A. AWS Trusted Advisor
- B. AWS Compute Optimizer
- C. AWS Cost Explorer
- D. All three provide some form of right-sizing recommendations

**Correct Answer: D**

**Explanation:** All three provide right-sizing input: Compute Optimizer uses ML to analyze utilization and recommend optimal instance types. Cost Explorer provides RI right-sizing recommendations. Trusted Advisor identifies idle/underutilized instances. However, Compute Optimizer provides the most detailed, ML-based right-sizing recommendations with performance risk ratings.

---

### Question 25
A company wants to implement tagging as the foundation for their cost allocation strategy. Every resource must have a "Department" and "Environment" tag.

Which combination enforces this? (Select TWO)

- A. AWS Tag Policies in AWS Organizations
- B. IAM policies with `aws:RequestTag` conditions
- C. AWS Cost Allocation Tags
- D. AWS Config Rules for required tags
- E. AWS Budgets with tag filters

**Correct Answer: A, B**

**Explanation:** Tag Policies in AWS Organizations enforce tag standards (key casing, allowed values) across all accounts. IAM policies with `aws:RequestTag` conditions prevent resource creation without required tags (proactive enforcement). Config Rules detect non-compliant resources (reactive detection). Cost Allocation Tags activate tags for billing reports but don't enforce them.

---

## Quick Reference: Cost Optimization Checklist

| Area | Action | Savings |
|------|--------|---------|
| EC2 | Right-size with Compute Optimizer | 20-40% |
| EC2 | Reserved Instances for steady workloads | Up to 72% |
| EC2 | Spot Instances for fault-tolerant workloads | Up to 90% |
| EC2 | Schedule start/stop for non-24/7 environments | Up to 70% |
| S3 | Lifecycle policies to transition storage classes | Up to 95% |
| S3 | S3 Intelligent-Tiering for unknown patterns | Variable |
| NAT Gateway | Use VPC endpoints instead | Variable |
| Data Transfer | Keep resources in the same Region/AZ | Up to 100% |
| Lambda | Optimize memory allocation | 10-40% |
| RDS | Use Aurora Serverless for variable workloads | Variable |
| CloudFront | Optimize Price Class and TTL | Variable |

## Quick Reference: Pricing Model Comparison

| Model | Commitment | Flexibility | Savings | Best For |
|-------|-----------|-------------|---------|----------|
| On-Demand | None | Full | 0% | Short-term, unpredictable |
| Savings Plans | 1-3 years $ | Moderate-High | Up to 72% | Mixed compute workloads |
| Standard RI | 1-3 years type | Low | Up to 72% | Known, steady workloads |
| Convertible RI | 1-3 years $ | Moderate | Up to 66% | Steady with flexibility |
| Spot | None | Full (interruptible) | Up to 90% | Fault-tolerant workloads |

## Quick Reference: Free Data Transfer in AWS

| Transfer Type | Cost |
|---------------|------|
| Data IN to AWS from internet | **FREE** |
| Same AZ (private IP) | **FREE** |
| S3 to EC2 (same Region) | **FREE** |
| S3 to CloudFront | **FREE** |
| VPC Gateway Endpoint to S3/DynamoDB | **FREE** |
| Cross-AZ | ~$0.01/GB |
| Cross-Region | ~$0.02/GB |
| Internet OUT | ~$0.09/GB (tiered) |
| NAT Gateway processing | ~$0.045/GB |
