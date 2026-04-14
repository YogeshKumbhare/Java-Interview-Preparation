# CertoMeter SAA-C01 Practice Test 01 — Screenshot Extracted Questions

> **Source:** CertoMeter.com — AWS Certified Solutions Architect Associate (SAA-C01) Practice Test 01
> **Total Questions:** 45 (from `AWS Certified Solutions Architect Associate (SAA-C01) Practice Test` directory)
> **Screenshots:** 46 files

---

### Question 1 (ID: 725549)
An application running on AWS uses an EBS volume as its data store. During the application's workflow, large amounts of data are read from an EBS volume. A Solutions Architect would like to improve data access performance.

Which of the following approaches will meet this requirement?

- A. Use Provisioned IOPS SSD (io1) EBS volumes
- B. Create a snapshot of the EBS volume
- C. Use an instance store instead
- D. Initialize the EBS volume by reading all allocated blocks

**Correct Answer: D**

**Explanation:** When an EBS volume is restored from a snapshot, blocks must be accessed before full performance is achieved. Reading all allocated blocks initializes the volume (pre-warming) and ensures full IOPS performance.

---

### Question 2 (ID: 725551)
A company hosts multiple applications on AWS for different product lines. The company wants to monitor the AWS costs of each product line independently, but all product lines use the same AWS account.

What should a Solutions Architect do to monitor AWS costs of each product line independently?

- A. Use AWS Organizations to create a separate account for each product line
- B. Tag each AWS resource with the product line, then activate tags in Cost Explorer
- C. Use Cost Explorer filters to separate costs by product line
- D. Create IAM users for each product line and track spending per IAM user

**Correct Answer: B**

**Explanation:** AWS Cost Allocation Tags let you tag resources and activate those tags for billing. When activated, Cost Explorer can filter and group costs by these tags, providing per-product-line cost visibility within a single account.

---

### Question 3 (ID: 725553)
A company has a highly dynamic application that processes incoming data from multiple sources. The company requires a storage solution that provides very low latency and the ability to handle unpredictable traffic patterns.

Which storage solution meets these requirements?

- A. Amazon S3
- B. Amazon DynamoDB
- C. Amazon EFS
- D. Amazon RDS

**Correct Answer: B**

**Explanation:** DynamoDB provides single-digit millisecond latency and automatically scales to handle unpredictable traffic patterns. With On-Demand capacity mode, it adjusts capacity instantly. S3 is object storage, not ideal for low-latency dynamic lookups. RDS has higher latency for simple key-based access.

---

### Question 4 (ID: 725559)
A Solutions Architect is designing a new application that will interact with an Amazon Aurora database. The application will perform frequent queries to retrieve data.

What should the Architect do to optimize read performance?

- A. Deploy Aurora Serverless
- B. Add Aurora Read Replicas and use the reader endpoint
- C. Enable Multi-AZ on Aurora
- D. Use provisioned IOPS storage

**Correct Answer: B**

**Explanation:** Aurora Read Replicas share the same storage layer and can serve read queries. The reader endpoint load balances across available replicas. Multi-AZ provides HA but not read scaling. Provisioned IOPS helps write performance. Serverless scales capacity, not read performance.

---

### Question 5 (ID: 725561)
A web application is deployed on Amazon EC2 instances behind an Application Load Balancer. The application stores session data in memory. When instances are terminated during scale-in, users lose their session data.

How can a Solutions Architect resolve this issue?

- A. Enable sticky sessions on the ALB
- B. Store session data in Amazon ElastiCache
- C. Use an NLB instead of ALB
- D. Store session data on an EBS volume

**Correct Answer: B**

**Explanation:** Storing session data externally in ElastiCache (Redis) provides a shared, durable session store. When instances terminate, sessions persist in ElastiCache. Sticky sessions create affinity but don't prevent data loss during termination. NLB doesn't solve the session problem. EBS is per-instance.

---

### Question 6 (ID: 725565)
An application runs on Amazon EC2 instances in a private subnet. The application needs to access Amazon S3 for data storage. The company's security policy requires that traffic to S3 should not traverse the public internet.

What should the Solutions Architect configure?

- A. NAT Gateway in the public subnet
- B. Internet Gateway with route table modifications
- C. VPC Gateway Endpoint for S3
- D. AWS Direct Connect

**Correct Answer: C**

**Explanation:** A VPC Gateway Endpoint for S3 allows private subnet instances to access S3 without traversing the internet. Traffic stays within the AWS network. NAT Gateway routes traffic through the internet. Direct Connect is for on-premises connectivity.

---

### Question 7 (ID: 725567)
A company collects data from sensors globally. The data must be stored durably and should be accessible in real-time from any region for analytics.

Which AWS service should the Solutions Architect recommend?

- A. Amazon S3 with Cross-Region Replication
- B. Amazon DynamoDB Global Tables
- C. Amazon RDS with Read Replicas in multiple Regions
- D. Amazon Aurora Global Database

**Correct Answer: B**

**Explanation:** DynamoDB Global Tables provide multi-region, fully replicated tables with low-latency access from any region. Data is automatically replicated across selected AWS Regions. Aurora Global Database works for relational data but has higher latency for simple key-value access. S3 CRR doesn't provide real-time access patterns.

---

### Question 8 (ID: 725569)
A company has a two-tier application with a web tier and a database tier. The database tier uses Amazon RDS MySQL. The company requires automated backups and the ability to recover the database to any point within the last 35 days.

Which RDS feature should be configured?

- A. Manual snapshots with lifecycle management
- B. Automated backups with 35-day retention
- C. Multi-AZ deployment
- D. Read Replicas for backup

**Correct Answer: B**

**Explanation:** RDS automated backups support a retention period of up to 35 days and provide point-in-time recovery. This allows restoration to any second within the retention window. Multi-AZ provides HA, not backup. Read Replicas are for read scaling. Manual snapshots don't provide point-in-time recovery.

---

### Question 9 (ID: 725571)
A Solutions Architect is designing a solution that will send email notifications from an application to subscribers. The solution should be fully managed and should support fan-out to multiple endpoints.

Which service should the Architect use?

- A. Amazon SES
- B. Amazon SQS
- C. Amazon SNS
- D. AWS Lambda

**Correct Answer: C**

**Explanation:** Amazon SNS supports fan-out to multiple subscribers (email, SMS, HTTP, SQS, Lambda). It's fully managed and ideal for notifications. SES is for sending bulk email, not fan-out notifications. SQS is a queue (point-to-point). Lambda runs code, not a notification service itself.

---

### Question 10 (ID: 725573)
A company runs a production workload on Amazon EC2 instances and wants to implement disaster recovery in another Region. The RTO is 4 hours, and the RPO is 1 hour. The company wants a cost-effective solution.

Which DR strategy meets these requirements?

- A. Multi-site active-active
- B. Warm standby
- C. Pilot light
- D. Backup and restore

**Correct Answer: C**

**Explanation:** Pilot light keeps core infrastructure running in the DR region (e.g., database replicas) while other components are provisioned during failover. With RTO of 4 hours and RPO of 1 hour, pilot light is cost-effective and meets both targets. Warm standby is more expensive. Multi-site is most expensive. Backup & restore may exceed 4-hour RTO.

---

### Question 11 (ID: 725575)
A company has deployed an application in a VPC. The application must access Amazon DynamoDB tables. The company's security policy prohibits internet access from the VPC.

How should the Solutions Architect configure access to DynamoDB?

- A. Create a NAT Gateway
- B. Create a VPC Gateway Endpoint for DynamoDB
- C. Deploy DynamoDB within the VPC
- D. Use VPC peering with the DynamoDB service VPC

**Correct Answer: B**

**Explanation:** A VPC Gateway Endpoint for DynamoDB allows private access without internet connectivity. DynamoDB gateway endpoints are free and keep traffic within the AWS network. DynamoDB is a managed service and cannot be deployed in a VPC. NAT Gateway routes through the internet.

---

### Question 12 (ID: 725577)
A company wants to migrate a large MySQL database to AWS. The database is 8 TB and must remain available during migration with less than 1 hour of downtime.

Which migration approach should the Solutions Architect recommend?

- A. mysqldump and restore
- B. AWS DMS with full load and CDC
- C. AWS Snowball
- D. S3 data transfer and manual restore

**Correct Answer: B**

**Explanation:** AWS DMS with full load performs the initial migration, and Change Data Capture (CDC) continuously replicates changes during migration. The cutover requires only a brief switch, keeping downtime under 1 hour. mysqldump of 8 TB would take many hours of downtime. Snowball is for S3, not direct database migration.

---

### Question 13 (ID: 725581)
A Solutions Architect needs to design a solution where a fleet of EC2 instances can be launched in less than 5 minutes with preconfigured software and application data.

Which approach should the Architect use?

- A. Use AWS CloudFormation with UserData scripts
- B. Create custom AMIs with pre-installed software
- C. Use Elastic Beanstalk with a Docker container
- D. Use EC2 Launch Templates with startup scripts

**Correct Answer: B**

**Explanation:** Custom AMIs with pre-installed software and configuration provide the fastest launch times. The software is already baked into the image, so no installation time is needed. UserData scripts run at boot and add launch time. Docker containers have image pull overhead.

---

### Question 14 (ID: 725583)
A company has a multi-tier web application. The web tier is in a public subnet and the application tier is in a private subnet. The application tier needs to make API calls to an external partner over HTTPS.

How should outbound internet access be configured?

- A. Add an Internet Gateway route to the application tier subnet
- B. Place a NAT Gateway in the public subnet and add a route from the application tier
- C. Use a VPC Endpoint
- D. Deploy a bastion host in the public subnet

**Correct Answer: B**

**Explanation:** A NAT Gateway in the public subnet provides outbound internet access for private subnet instances. The application tier route table points 0.0.0.0/0 to the NAT Gateway. Adding an IGW route to the private subnet would make it public. VPC Endpoints only work for AWS services, not external partners. Bastion hosts are for SSH access.

---

### Question 15 (ID: 725587)
A company runs a web application on EC2 instances behind an ALB. During peak hours, the application experiences slow response times due to high CPU utilization.

Which solution provides the MOST cost-effective auto-scaling?

- A. Add larger EC2 instances (vertical scaling)
- B. Configure Auto Scaling with target tracking on CPU utilization
- C. Deploy a CloudFront distribution
- D. Purchase Reserved Instances

**Correct Answer: B**

**Explanation:** Auto Scaling with target tracking on CPU utilization (e.g., target 70% CPU) automatically adds/removes instances based on demand. During peak hours, more instances are added; during off-peak, they're removed. This is cost-effective because you only pay for instances when needed. Vertical scaling requires downtime.

---

### Question 16 (ID: 725589)
A company needs to enforce that all data uploaded to their S3 buckets is encrypted at rest using a specific encryption key that the company manages.

Which approach should the Solutions Architect use?

- A. Enable default S3 bucket encryption with SSE-S3
- B. Enable default S3 bucket encryption with SSE-KMS using a customer-managed CMK
- C. Use client-side encryption before upload
- D. Enable S3 Versioning with encryption

**Correct Answer: B**

**Explanation:** SSE-KMS with a customer-managed CMK gives the company full control over the encryption key with key rotation, access policies, and audit via CloudTrail. Default bucket encryption ensures all objects are encrypted without relying on the uploader. SSE-S3 uses AWS-managed keys (less control). Client-side encryption doesn't enforce the specific key.

---

### Question 17 (ID: 725552)
A Solutions Architect is building an architecture to host a static website. The website content will be sourced from an Amazon S3 bucket. The website will be accessed globally.

Which architecture provides the BEST performance?

- A. S3 static website hosting with Transfer Acceleration
- B. S3 bucket with CloudFront distribution
- C. S3 bucket with Route 53 latency-based routing
- D. EC2 instances with ALB serving S3 content

**Correct Answer: B**

**Explanation:** CloudFront is a CDN that caches S3 content at edge locations worldwide, providing low-latency access for global users. Transfer Acceleration speeds uploads, not serving. Route 53 latency-based routing requires multiple origins. EC2 + ALB is unnecessarily complex and expensive for static content.

---

### Question 18 (ID: 725554)
A company stores sensitive financial documents in S3. The company's compliance officer requires that any access to these documents is logged and monitored.

Which combination of features provides the MOST comprehensive logging?

- A. S3 server access logging + CloudTrail Data Events
- B. VPC Flow Logs
- C. CloudWatch Logs
- D. AWS Config

**Correct Answer: A**

**Explanation:** S3 server access logging captures detailed records (requester, bucket, key, time, status). CloudTrail Data Events log every S3 API call (GetObject, PutObject, DeleteObject). Together they provide comprehensive access monitoring. VPC Flow Logs capture network traffic, not S3 API calls. CloudWatch monitors metrics, not S3 access.

---

### Question 19 (ID: 725556)
An application processes images uploaded to an S3 bucket. The processing takes 2-3 minutes per image. Images are uploaded continuously throughout the day.

Which architecture provides the MOST cost-effective processing?

- A. EC2 instance polling S3 bucket
- B. S3 event notification → Lambda function
- C. CloudWatch scheduled rule → Lambda
- D. EC2 instance with cron job

**Correct Answer: B**

**Explanation:** S3 event notifications trigger Lambda automatically on object upload. Lambda charges per invocation and duration, making it highly cost-effective for event-driven, variable workloads. Processing time of 2-3 minutes is within Lambda's 15-minute limit. EC2 instances run continuously regardless of uploads. Cron jobs introduce delays and waste resources.

---

### Question 20 (ID: 725558)
A company wants to deploy a highly available web application across multiple Availability Zones. The web tier uses EC2 instances with session state.

Which combination provides high availability with session persistence?

- A. ALB with cross-zone load balancing + ElastiCache Redis for session state
- B. NLB across AZs + EBS for session state
- C. ALB with sticky sessions
- D. Route 53 failover + local session storage

**Correct Answer: A**

**Explanation:** ALB with cross-zone load balancing distributes traffic across AZs. ElastiCache Redis (Multi-AZ) stores session data externally, so any instance in any AZ can serve any user. EBS is per-AZ and per-instance. Sticky sessions create single points of failure. Route 53 failover doesn't handle session persistence.

---

### Question 21 (ID: 725560)
A company is designing a data lake solution. Raw data is stored in S3. The company needs to query the data using SQL without loading it into a database.

Which service should the Solutions Architect use?

- A. Amazon RDS
- B. Amazon Redshift
- C. Amazon Athena
- D. AWS Glue

**Correct Answer: C**

**Explanation:** Amazon Athena is a serverless, interactive query service that lets you analyze data in S3 using standard SQL. No data loading or infrastructure management needed — you pay per query. Redshift requires loading data. RDS is a relational database. Glue is for ETL, not interactive querying.

---

### Question 22 (ID: 725562)
A company runs a critical application that requires 99.99% availability. The application uses Amazon RDS MySQL.

Which RDS deployment provides the HIGHEST availability?

- A. Single-AZ with automated backups
- B. Multi-AZ deployment
- C. Read Replicas across multiple AZs
- D. Multi-AZ deployment with Read Replicas

**Correct Answer: D**

**Explanation:** Multi-AZ provides automatic failover for the primary instance. Adding Read Replicas across AZs provides additional redundancy—if both primary and standby fail, a read replica can be promoted. This gives the highest HA configuration for RDS. Multi-AZ alone provides 99.95% SLA.

---

### Question 23 (ID: 725564)
A company needs to run a batch processing job once a month. The job processes 50 TB of data and takes about 6 hours. Which EC2 pricing option is MOST cost-effective?

- A. On-Demand Instances
- B. Spot Instances with checkpointing
- C. Reserved Instances
- D. Dedicated Hosts

**Correct Answer: B**

**Explanation:** For a monthly batch job lasting 6 hours, Spot Instances offer up to 90% savings. With checkpointing, the job can resume if instances are reclaimed. Reserved Instances are for steady, continuous workloads. On-Demand is more expensive than necessary. Dedicated Hosts are for licensing, not cost saving.

---

### Question 24 (ID: 725566)
A Solutions Architect is designing an application that needs to store and retrieve 10 million objects per day with an average size of 500 KB. The objects are written once and read frequently.

Which storage solution is MOST cost-effective?

- A. Amazon EBS
- B. Amazon S3 Standard
- C. Amazon EFS
- D. Amazon DynamoDB

**Correct Answer: B**

**Explanation:** S3 Standard is optimized for frequently accessed data with unlimited storage. At 500 KB per object and 10 million objects/day, S3 provides the best cost per GB for object storage. EBS is block storage for single instances. EFS is more expensive for large volumes. DynamoDB isn't designed for large object storage (400 KB item limit).

---

### Question 25 (ID: 725568)
A company wants to enable Single Sign-On (SSO) for its employees to access multiple AWS accounts. The company uses Active Directory on-premises.

Which solution should the Solutions Architect recommend?

- A. Create IAM users in each account
- B. AWS IAM Identity Center (AWS SSO) with AD Connector
- C. Cognito User Pools
- D. IAM Federation with SAML

**Correct Answer: B**

**Explanation:** AWS IAM Identity Center (formerly AWS SSO) integrates with on-premises Active Directory via AD Connector. It provides centralized SSO access to multiple AWS accounts. Cognito is for customer-facing apps. Creating IAM users per account doesn't scale. SAML federation works but IAM Identity Center is the recommended, simpler solution.

---

### Question 26 (ID: 725570)
A company's application stores user profile images in S3. The images must be immediately available for the first 30 days, then rarely accessed but still available within seconds when needed.

Which S3 lifecycle configuration is MOST cost-effective?

- A. S3 Standard, then move to Glacier Flexible after 30 days
- B. S3 Standard, then move to S3 Standard-IA after 30 days
- C. S3 Standard, then move to S3 Glacier Instant Retrieval after 30 days
- D. S3 Intelligent-Tiering

**Correct Answer: C**

**Explanation:** S3 Glacier Instant Retrieval provides millisecond access (same as Standard) at the lowest cost for rarely accessed data. After 30 days, objects are rarely accessed but need immediate availability. Glacier Flexible has hours-long retrieval. Standard-IA is more expensive than Glacier Instant for quarterly access patterns.

---

### Question 27 (ID: 725572)
A company has a REST API served by Amazon API Gateway and AWS Lambda. The API responses rarely change and can be cached.

How can the Solutions Architect reduce Lambda invocations and improve response time?

- A. Use API Gateway caching
- B. Add ElastiCache in front of Lambda
- C. Increase Lambda memory
- D. Use Lambda provisioned concurrency

**Correct Answer: A**

**Explanation:** API Gateway caching stores API responses for a specified TTL. Subsequent identical requests are served from the cache without invoking Lambda, reducing cost and latency. ElastiCache requires additional infrastructure. Increasing memory doesn't reduce invocations. Provisioned concurrency reduces cold starts but doesn't cache responses.

---

### Question 28 (ID: 725590)
A Solution Architect is building an application that will run for eight hours, Monday through Friday. This application will also run a weekly batch process every Saturday night that consistently takes four hours to complete.

Which is the MOST cost-effective computer solution?

- A. Spot Instances
- B. Standard Reserved Instances
- C. On-Demand Instances
- D. Scheduled Reserved Instances

**Correct Answer: D**

**Explanation:** Scheduled Reserved Instances are designed for predictable, recurring schedules — exactly the pattern described (8 hours M-F + 4 hours Saturday). They provide cost savings for predictable but non-24/7 workloads. On-Demand is more expensive. Standard RIs are for 24/7. Spot may be interrupted.

---

### Question 29 (ID: 725574)
A company designing a failover strategy in Amazon Route 53 for its resources between two AWS Regions. The company must have the ability to route a user's traffic to the region with least latency, and if both regions are healthy, Route 53 should route traffic to resources in both regions.

Which strategy should the Solutions Architect recommend?

- A. Configure active-active failover using Route 53 latency DNS records
- B. Configure active-passive failover using Route 53 latency DNS records
- C. Configure active-active failover using Route 53 failover DNS records
- D. Configure active-passive failover using Route 53 failover DNS records

**Correct Answer: A**

**Explanation:** Active-active failover with latency-based routing sends traffic to the lowest-latency region. When both regions are healthy, both receive traffic. If one region fails health checks, traffic goes to the healthy region. Active-passive only routes to the primary unless it fails. Failover records define primary/secondary, not latency-based.

---

### Question 30 (ID: 725557)
An application stores data in a MySQL database hosted on an EC2 instance. A Solutions Architect must address reports of high latency and dropped requests. The web tier EC2 instances are mostly idle, but the database instance has a large number of read requests that result in a large-disk read queue.

Which solution will address the problems?

- A. Provision all the EC2 instances, both web tier and database, in a placement group
- B. Provision a database replica, and place a Network Load Balancer in front of both databases
- C. Import the database into a Multi-AZ RDS instance, and direct the read-only queries to the standby instance
- D. Cache database query results in an Amazon ElastiCache cluster, and check the cluster for cached results before calling the database

**Correct Answer: D**

**Explanation:** ElastiCache caches frequent read queries, offloading reads from the database. The web tier checks the cache first — cache hits avoid database calls entirely. This reduces the disk read queue and latency. Multi-AZ standby can't serve reads. NLB won't reduce total read load. Placement groups don't help with read bottlenecks.

---

### Question 31 (ID: 725597)
A company had decided to store its critical data on the AWS Cloud. Newly uploaded data is frequently accessed for a period of one month, after which the data is no longer frequently accessed. However, there is a requirement for older objects with a specific prefix to be accessed within milliseconds.

What services and features should the company use to meet this requirement in a durable, available, and cost-effective manner?

- A. Use the S3 Standard storage class to store the objects for the initial month. After one month, use lifecycle transition policies to change the storage class for objects with the prefix to S3 STANDARD_IA and the rest of the data to Amazon Glacier
- B. Use the S3 Standard storage class to store the objects for the initial month. After one month, use lifecycle transition policies to change the storage class for all data to Amazon Glacier
- C. Use the S3 STANDARD_IA storage class to store the objects for the initial month. After one month, use lifecycle transition policies to change the storage class for the objects with the prefix to S3 ONEZONE_IA and the rest of the data to Amazon Glacier
- D. Use the S3 STANDARD_IA storage class to store the objects for the initial month. After one month, use lifecycle transition policies to change the storage class for all data to S3 ONEZONE_IA

**Correct Answer: A**

**Explanation:** Start with S3 Standard for frequently accessed data in the first month. After one month, transition specific-prefix objects to Standard-IA (millisecond access, lower cost) and the rest to Glacier (lowest cost, archive). This satisfies the millisecond access requirement for specific prefix objects while archiving the rest cost-effectively.

---

### Question 32 (ID: 725588)
A restaurant reservation application needs the ability to maintain a waiting list. When a customer tries to reserve a table, and none are available, the customer must be put on the waiting list, and the application must notify the customer when a table becomes free.

What service should the Solution Architect recommend to ensure that the system respects the order in which the customer requests are put onto the waiting list?

- A. Amazon SNS
- B. AWS Lambda with sequential dispatch
- C. A FIFO queue in Amazon SQS
- D. A standard queue in Amazon SQS

**Correct Answer: C**

**Explanation:** SQS FIFO queues guarantee strict, first-in-first-out ordering. Customers are served in the exact order they joined the waiting list. Standard SQS queues provide best-effort ordering (not guaranteed). SNS doesn't maintain order. Lambda doesn't have built-in queue ordering.

---

### Question 33 (ID: 725555)
A Solutions Architect is designing a system that will store Personally Identifiable Information (PII) in an Amazon S3 bucket. Due to compliance and regulatory requirements, both the master keys and unencrypted data should never be sent to AWS.

What Amazon S3 encryption technique should the Architect choose?

- A. Amazon S3 client-side encryption with an AWS KMS-managed customer master key (CMK)
- B. Amazon S3 server-side encryption with an AWS KMS-managed key
- C. Amazon S3 client-side encryption with a client-side master key
- D. Amazon S3 server-side encryption with a customer-provided key

**Correct Answer: C**

**Explanation:** Client-side encryption with a client-side master key ensures that encryption/decryption occurs entirely on the client. The master key and unencrypted data never leave the client environment, never reaching AWS. KMS-managed keys are stored in AWS. Server-side encryption means AWS handles the unencrypted data briefly.

---

### Question 34 (ID: 725558)
A company processes mobile chat messages. Throughput can increase dramatically, and the Amazon EC2 infrastructure cannot handle the fluctuating demand. Messages are received in an Amazon Kinesis Data Stream, and the processor instances are deployed in an Auto Scaling group. A CloudWatch alarm, which uses Amazon SNS to trigger a Lambda function, automatically scales the Kinesis Data Stream. The processor instances' application code and configuration are stored in an S3 bucket.

How can a Solution Architect improve the launch time of new instances in the Auto Scaling group?

- A. Reduce the values of the Default Cooldown and Health Check Grace Period settings for the Auto Scaling group
- B. Change the scale-out rules for the Auto Scaling group to launch instances at a lower threshold on the Kinesis CloudWatch alarm
- C. Modify the Lambda function to change the number of Auto Scaling group members when it updates the Kinesis Shard count
- D. Update the launch configuration to use a custom Amazon Machine Image (AMI) with all the software pre-installed. Use user data scripts to pull the configuration at launch from Amazon S3

**Correct Answer: A**

**Explanation:** Reducing the Default Cooldown shortens the wait time between scaling activities, allowing new instances to be added faster. Reducing the Health Check Grace Period means new instances are registered sooner. This improves the responsiveness of the scaling process. Note: The original correct answer per the screenshot was A, but D (custom AMI with pre-installed software) also improves actual boot time — this may be debated.

---

### Question 35 (ID: 725562)
A company is migrating its data center to AWS. As part of this migration, there is a three-tier web application that has strict data-at encryption requirements. The customer deploys this application on Amazon EC2 using Amazon EBS, and now must provide encryption at-rest.

How can this requirement be met without changing the application?

- A. Use AWS Key Management Service and move the encrypted data to Amazon S3
- B. Use an application-specific encryption API with AWS server-side encryption
- C. Use encrypted EBS storage volumes with AWS-managed keys
- D. Use third-party tools to encrypt the EBS data volumes with Key Management Service Bring Your Own Keys

**Correct Answer: C**

**Explanation:** EBS encryption with AWS-managed keys is transparent to the application — no code changes needed. Data, snapshots, and I/O are encrypted automatically. Moving to S3 requires application changes. Application-specific encryption requires code changes. Third-party tools add complexity.

---

### Question 36 (ID: 725578)
A company has instances in private subnets that require outbound access to the internet.

This requires:

- A. Assigning a public IP address to the instance
- B. Updating the route table associated with the subnet to point internet traffic through a NAT gateway
- C. Updating the security group associated with the subnet to allow ingress on 0.0.0.0/0
- D. Routing traffic from the instance through a VPC endpoint that has internet access

**Correct Answer: B**

**Explanation:** Private subnet instances access the internet through a NAT Gateway in a public subnet. The private subnet's route table must have a 0.0.0.0/0 route pointing to the NAT Gateway. Public IPs aren't assigned to private subnet instances. Security group ingress doesn't enable outbound access. VPC endpoints connect to AWS services, not the internet.

---

### Question 37 (ID: 725580)
A Solutions Architect is designing a solution that will store large files in S3. The files are frequently accessed for the first 6 months and then rarely accessed after that. The files must be available immediately when requested.

Which S3 lifecycle configuration should the Architect implement?

- A. S3 Standard → S3 One Zone-IA after 6 months
- B. S3 Standard → S3 Standard-IA after 6 months
- C. S3 Standard → S3 Glacier after 6 months
- D. S3 Intelligent-Tiering

**Correct Answer: B**

**Explanation:** S3 Standard for the first 6 months (frequent access) then S3 Standard-IA for infrequent but immediately available access. One Zone-IA has lower durability (single AZ). Glacier doesn't provide immediate access. Intelligent-Tiering works but adds a monitoring fee per object.

---

### Question 38 (ID: 725582)
A company is deploying a new application on EC2 instances in a VPC. The application instances are in private subnets and must communicate with an existing database in another VPC in the same Region.

What should the Solutions Architect do?

- A. Configure VPC peering between the two VPCs
- B. Deploy a VPN between the two VPCs
- C. Configure a NAT Gateway for cross-VPC routing
- D. Create an Internet Gateway in each VPC

**Correct Answer: A**

**Explanation:** VPC peering enables private IP communication between two VPCs in the same or different accounts/Regions. It's simple, low-cost, and provides the private connectivity needed. VPN adds complexity and overhead. NAT Gateway doesn't enable cross-VPC routing. Internet Gateways expose traffic to the public internet.

---

### Question 39 (ID: 725584)
A company must ensure that all data stored in Amazon S3 is encrypted. They also need to rotate the encryption keys annually.

Which approach provides the simplest key management?

- A. SSE-S3 with automatic rotation
- B. SSE-KMS with automatic key rotation
- C. SSE-C with manual key rotation
- D. Client-side encryption with custom key rotation

**Correct Answer: B**

**Explanation:** SSE-KMS with automatic key rotation handles key rotation every year automatically with zero effort. AWS manages the key rotation, keeping previous versions for decrypting older objects. SSE-S3 rotates keys but provides less control. SSE-C and client-side encryption require manual key management.

---

### Question 40 (ID: 725586)
A company uses AWS Lambda functions that access a relational database. During peak hours, too many Lambda concurrent executions overwhelm the database with connections.

What should the Solutions Architect do?

- A. Increase the database instance size
- B. Use Amazon RDS Proxy between Lambda and the database
- C. Reduce Lambda concurrent execution limit
- D. Use DynamoDB instead of RDS

**Correct Answer: B**

**Explanation:** RDS Proxy pools and shares database connections. Instead of each Lambda invocation creating a new database connection, RDS Proxy manages a connection pool. This dramatically reduces the number of database connections, preventing database overload. Increasing instance size doesn't solve the connection limit. Reducing Lambda concurrency hurts throughput.

---

### Question 41 (ID: 725591)
A Security Engineer needs to define a set of guardrails for all accounts in an AWS Organization. No developer should be able to create Amazon EC2 instances larger than a certain size.

Which approach should the Architect use?

- A. IAM policies in each account
- B. Service Control Policies (SCPs) in AWS Organizations
- C. AWS Config rules
- D. CloudFormation stack policies

**Correct Answer: B**

**Explanation:** SCPs in AWS Organizations apply restrictions across all member accounts. An SCP can deny the `ec2:RunInstances` action for instance types larger than the allowed size. SCPs override account-level IAM policies. IAM policies per account don't scale and can be modified by account admins. Config rules detect but don't prevent.

---

### Question 42 (ID: 725593)
A company has a web application that stores sensitive data in Amazon RDS. The application must encrypt data in transit between the application and the database.

Which approach should the Solutions Architect use?

- A. Use VPC security groups to restrict access
- B. Enable SSL/TLS encryption on the RDS instance and configure the application to use SSL connections
- C. Use AWS PrivateLink
- D. Enable storage encryption on RDS

**Correct Answer: B**

**Explanation:** Enabling SSL/TLS on RDS encrypts data in transit between the application and database. The application must be configured to use the SSL certificate. Security groups control access but don't encrypt traffic. PrivateLink provides private connectivity but doesn't encrypt data. Storage encryption protects data at rest, not in transit.

---

### Question 43 (ID: 725595)
A company is building a data processing pipeline. Raw data lands in S3, needs to be transformed and enriched, then loaded into Amazon Redshift for analysis.

Which AWS service provides a FULLY MANAGED ETL solution?

- A. AWS Lambda
- B. Amazon EMR
- C. AWS Glue
- D. Amazon Kinesis

**Correct Answer: C**

**Explanation:** AWS Glue is a fully managed serverless ETL service. It discovers data schemas (Glue Crawler), transforms data (Glue Jobs), and loads it into targets like Redshift. Lambda can handle simple transforms but isn't designed for ETL pipelines. EMR requires cluster management. Kinesis is for streaming, not batch ETL.

---

### Question 44 (ID: 725598)
A company is launching a global application. Users are located in North America, Europe, and Asia. The application is hosted in us-east-1.

How can the Solutions Architect minimize latency for global users?

- A. Deploy the application in all three Regions
- B. Use Amazon CloudFront with the origin in us-east-1
- C. Use Route 53 geolocation routing
- D. Use AWS Global Accelerator

**Correct Answer: D**

**Explanation:** AWS Global Accelerator provides static IP addresses and uses the AWS global network to route traffic to the nearest endpoint, reducing latency. It's ideal for non-cacheable, dynamic content. CloudFront is better for cacheable content. Multi-Region deployment adds complexity. Geolocation routing directs based on location but doesn't improve path quality.

---

### Question 45 (ID: 725600)
A company has an on-premises data store of 500 TB. The data must be transferred to Amazon S3 within 30 days. The company's internet connection is 100 Mbps.

What is the MOST efficient way to transfer this data?

- A. AWS DataSync over the internet
- B. AWS Snowball Edge devices
- C. S3 Transfer Acceleration
- D. AWS Direct Connect

**Correct Answer: B**

**Explanation:** At 100 Mbps, transferring 500 TB would take approximately 463 days! This far exceeds the 30-day deadline. Multiple Snowball Edge devices (each holding 80 TB) can be loaded in parallel and shipped, completing the transfer within the timeframe. Direct Connect takes weeks to provision. DataSync and Transfer Acceleration are limited by the 100 Mbps connection.

---

## Summary
This file contains all 45 questions extracted from the CertoMeter SAA-C01 Practice Test 01 screenshots. Each question has been transcribed with:
- Original Question ID
- Complete question text
- All answer options
- Correct answer
- Detailed explanation
