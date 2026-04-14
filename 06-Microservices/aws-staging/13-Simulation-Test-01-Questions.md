# SAA-C01 Simulation Test 01 — Extracted Questions (64 Questions)

> **Source:** CertoMeter — AWS Certified Solutions Architect Associate (SAA-C01) Simulation Test 01
> **Total Questions:** 64

---

### Question 1 (ID: 956293)
A medical office has a requirement to store data for seven years. The data is stored in Amazon S3, but they do not have a large budget for storing this data and do not plan on accessing the data unless audited.

What is the MOST cost-efficient, secure, and redundant solution for this scenario?

- A. Copy the data to an Amazon EFS volume and mount it to six instances in a VPC
- B. Export the data from Amazon S3 with AWS Snowball and store the data on a local RAID 1 Array
- C. Use Amazon S3 Lifecycle policies to transition the data to S3-IA and then to Amazon Glacier
- D. Periodically download the data to an Amazon EBS volume and archive the data to Amazon Glacier

**Correct Answer: C**

**Explanation:** S3 Lifecycle policies can automatically transition data from S3 Standard → S3-IA → Glacier. For 7-year retention with rare access, Glacier provides the lowest cost at $0.004/GB/month. It's durable (11 9s), secure (encrypted), and fully managed. EFS and EBS are significantly more expensive. Snowball to local RAID loses cloud durability.

---

### Question 2 (ID: 956272)
A Solutions Architect is designing a web application that contains an Auto Scaling group with Amazon EC2 instances behind an Elastic Load Balancing load balancer. The EC2 instances access static content within an Amazon S3 bucket. When application load reaches a specified threshold, the Auto Scaling group will scale up and deploy new EC2 instances to handle the additional load.

When new EC2 instances are deployed using the Auto Scaling group, what should the Architect do to ensure that the instances can access static content within the S3 bucket?

- A. Configure the Auto Scaling group to launch instances with an AWS IAM role with read-only permissions to the S3 bucket
- B. Create a security group that grants Amazon S3 read-only permissions for instances behind the load balancer and apply it to the S3 bucket
- C. Apply an AWS IAM policy to the S3 bucket that permits read-only access the folder 'static-content' from the EC2 instances
- D. Create an AWS IAM user with a policy that grants the permissions to read the S3 bucket. Configure the load balancer to store the user's Public/Private key.

**Correct Answer: A**

**Explanation:** IAM roles attached to EC2 instances via instance profiles provide temporary credentials automatically. The Auto Scaling launch configuration/template specifies the IAM role, so all new instances automatically get S3 read permissions. Security groups don't control S3 access. IAM users with keys are less secure and don't auto-distribute to new instances.

---

### Question 3 (ID: 725571)
A customer has a legacy application with a large amount of data. The files accessed by the application are approximately 10 GB each, but are rarely accessed. However, when files are accessed, they are retrieved sequentially. The customer is migrating the application to AWS and would like to use Amazon EC2 and Amazon EBS.

What is the LEAST expensive EBS volume type for this use case?

- A. Cold HDD (sc1)
- B. Provisioned IOPS SSD (io1)
- C. General Purpose SSD (gp2)
- D. Throughput Optimized HDD (st1)

**Correct Answer: A**

**Explanation:** Cold HDD (sc1) is the cheapest EBS volume type at ~$0.015/GB/month. It's designed for infrequently accessed, sequential workloads — exactly this use case. Throughput Optimized HDD (st1) is for frequently accessed sequential data. SSD types (gp2, io1) are for random I/O and much more expensive.

---

### Question 4 (ID: 956275)
A company runs a web application on Amazon EC2 instances in an Auto Scaling group. The application uses Amazon RDS MySQL with Multi-AZ. During a major traffic spike, the database becomes the bottleneck due to read-heavy queries.

What should the Solutions Architect do to improve read performance?

- A. Enable RDS read replicas and direct read traffic to the replica endpoint
- B. Increase the RDS instance size
- C. Enable Multi-AZ with read replicas
- D. Move to Amazon Aurora

**Correct Answer: A**

**Explanation:** RDS Read Replicas offload read queries from the primary instance. The application directs read-heavy queries to the replica endpoint, reducing load on the primary. This is the most targeted and cost-effective solution for read bottlenecks. Simply scaling up adds cost. Aurora migration is an over-engineering for this specific problem.

---

### Question 5 (ID: 956277)
A company stores confidential data in an S3 bucket. The company must ensure that data is encrypted at rest using keys that the company fully manages, including the ability to rotate keys on demand.

Which encryption approach meets these requirements?

- A. SSE-S3
- B. SSE-KMS with AWS-managed keys
- C. SSE-KMS with customer-managed CMK
- D. SSE-C

**Correct Answer: C**

**Explanation:** SSE-KMS with customer-managed CMK provides full control over encryption keys. The company can create, rotate, disable, and audit keys via CloudTrail. SSE-S3 uses AWS-managed keys with no customer control. AWS-managed KMS keys don't allow on-demand rotation. SSE-C requires the customer to manage keys outside AWS and pass them with every request.

---

### Question 6 (ID: 956279)
A Solutions Architect is designing a highly available architecture for a web application. The application runs on EC2 instances and uses an Application Load Balancer. The architecture must withstand the loss of an entire Availability Zone.

What is the MINIMUM number of Availability Zones required?

- A. 1
- B. 2
- C. 3
- D. 4

**Correct Answer: B**

**Explanation:** To withstand the loss of one AZ, you need at least 2 AZs. With instances in 2 AZs behind an ALB, if one AZ fails, the other continues serving traffic. However, 3 AZs is recommended for production to maintain capacity during AZ failure. The minimum requirement is 2.

---

### Question 7 (ID: 956281)
A company has a mobile application that generates millions of events per second. The events must be captured, processed in real-time, and stored for future analysis.

Which architecture should the Solutions Architect recommend?

- A. Amazon SQS → Lambda → S3
- B. Amazon Kinesis Data Streams → Lambda → S3/Redshift
- C. Amazon SNS → SQS → EC2
- D. API Gateway → Lambda → DynamoDB

**Correct Answer: B**

**Explanation:** Kinesis Data Streams is designed for real-time ingestion of millions of events per second. Lambda consumers process events in real-time, and results are stored in S3 for data lake or Redshift for analytics. SQS has lower throughput limits and doesn't support real-time streaming. SNS is for notifications, not event capture.

---

### Question 8 (ID: 956283)
A company has an application that stores session state on EC2 instances. When an instance fails, users lose their session data. The company wants to decouple session state from the instances.

Which solution provides the LOWEST latency for session management?

- A. Amazon S3
- B. Amazon DynamoDB
- C. Amazon ElastiCache Redis
- D. Amazon RDS

**Correct Answer: C**

**Explanation:** ElastiCache Redis provides sub-millisecond latency for key-value lookups, making it ideal for session management. It supports data persistence, replication, and Multi-AZ failover. DynamoDB offers single-digit ms latency (higher). S3 and RDS have much higher latency for session-style access patterns.

---

### Question 9 (ID: 956285)
A company operates an e-commerce platform. During flash sales, the order processing system becomes overwhelmed, causing orders to be lost.

Which architecture improvement prevents order loss during traffic spikes?

- A. Deploy larger EC2 instances for the order processors
- B. Place an SQS queue between the web tier and order processing tier
- C. Add more order processing instances permanently
- D. Use CloudFront to cache order requests

**Correct Answer: B**

**Explanation:** SQS decouples the web tier from the order processors. During traffic spikes, orders are queued in SQS and processed at a sustainable rate. No orders are lost because SQS durably stores messages. Larger instances don't prevent loss during extreme spikes. CloudFront caches content, not transactional orders. Permanent over-provisioning wastes money.

---

### Question 10 (ID: 956287)
A company runs a containerized application that needs to scale automatically based on CPU utilization. The company does not want to manage the underlying infrastructure.

Which AWS service should the Solutions Architect recommend?

- A. Amazon ECS on EC2
- B. Amazon ECS on AWS Fargate
- C. Amazon EKS on EC2
- D. EC2 with Docker installed

**Correct Answer: B**

**Explanation:** ECS on Fargate is serverless — AWS manages the underlying infrastructure. Auto Scaling policies scale containers based on CPU utilization. No EC2 instance management needed. ECS on EC2 and EKS on EC2 require managing EC2 instances. EC2 with Docker is fully self-managed.

---

### Question 11 (ID: 956289)
A Solutions Architect must design a solution for an application that requires 15,000 IOPS consistently. The application uses a single EC2 instance with one EBS volume.

Which EBS volume type should be used?

- A. General Purpose SSD (gp2)
- B. General Purpose SSD (gp3)
- C. Provisioned IOPS SSD (io1)
- D. Throughput Optimized HDD (st1)

**Correct Answer: C**

**Explanation:** io1/io2 Provisioned IOPS SSD supports up to 64,000 IOPS and allows specifying exact IOPS requirements. gp2 provides up to 16,000 IOPS but is burst-based. gp3 provides 3,000 baseline and up to 16,000 IOPS. For consistently requiring 15,000 IOPS, io1 provides guaranteed performance. gp3 could also work but io1 guarantees consistency.

---

### Question 12 (ID: 956291)
A company has deployed a web application across two AWS Regions for disaster recovery. The primary Region is us-east-1 and the DR Region is eu-west-1. The company needs DNS failover when the primary Region becomes unhealthy.

Which Route 53 routing policy should be configured?

- A. Weighted routing
- B. Latency-based routing
- C. Failover routing
- D. Geolocation routing

**Correct Answer: C**

**Explanation:** Failover routing policy defines a primary and secondary (DR) endpoint. Route 53 health checks monitor the primary. If the primary fails health checks, Route 53 automatically routes traffic to the secondary (DR) endpoint. Weighted routing splits traffic. Latency-based routes to lowest latency, not failover. Geolocation routes by user location.

---

### Question 13 (ID: 956293)
A company has a three-tier web application. The data tier uses Amazon RDS PostgreSQL. The company needs the database to automatically failover to a standby in another AZ with minimal downtime.

Which RDS feature provides this?

- A. Read Replicas
- B. Multi-AZ deployment
- C. Cross-Region Replication
- D. Automated Backups

**Correct Answer: B**

**Explanation:** Multi-AZ maintains a synchronous standby replica in another AZ. During failure, RDS automatically fails over to the standby with minimal downtime (typically 60-120 seconds). Read Replicas are asynchronous and require manual promotion. Cross-Region Replication is for DR across Regions. Automated Backups provide recovery, not failover.

---

### Question 14 (ID: 956295)
A company needs to run a high-performance computing (HPC) workload on AWS. The workload requires low-latency, high-throughput network communication between nodes.

Which EC2 feature should the Solutions Architect use?

- A. Enhanced Networking
- B. Placement Groups (Cluster)
- C. Dedicated Hosts
- D. Elastic Fabric Adapter (EFA)

**Correct Answer: D**

**Explanation:** Elastic Fabric Adapter (EFA) provides the lowest latency and highest throughput for HPC workloads with OS-bypass capabilities. It supports MPI (Message Passing Interface) for tightly-coupled HPC applications. Cluster placement groups reduce latency but EFA goes further. Enhanced Networking provides better networking but not HPC-grade. Dedicated Hosts are for licensing.

---

### Question 15 (ID: 956297)
A company collects log data from multiple AWS services. The company wants to centralize and analyze logs using SQL queries in a serverless manner.

Which combination of services should be used?

- A. CloudWatch Logs → S3 → Athena
- B. CloudWatch Logs → Elasticsearch
- C. CloudTrail → RDS → SQL queries
- D. CloudWatch Logs → Redshift

**Correct Answer: A**

**Explanation:** Export CloudWatch Logs to S3, then use Athena for serverless SQL queries. Athena is pay-per-query with no infrastructure to manage. Elasticsearch requires cluster management. Redshift requires provisioned clusters. RDS requires database management. The S3 + Athena combination is fully serverless.

---

### Question 16 (ID: 956299)
A company has implemented AWS Organizations with multiple accounts. The security team wants to ensure that no IAM user in any member account can disable CloudTrail.

How should this be accomplished?

- A. Create an IAM policy in each account denying CloudTrail actions
- B. Use a Service Control Policy (SCP) to deny cloudtrail:StopLogging
- C. Enable CloudTrail with log file integrity validation
- D. Use AWS Config to detect CloudTrail changes

**Correct Answer: B**

**Explanation:** SCPs in AWS Organizations apply guardrails across all member accounts. An SCP denying `cloudtrail:StopLogging` and `cloudtrail:DeleteTrail` prevents anyone (even root) in member accounts from disabling CloudTrail. IAM policies can be modified by account admins. Config detects but doesn't prevent. Log file integrity validates logs but doesn't prevent disabling.

---

### Question 17 (ID: 956301)
A company wants to deploy a WordPress website that can scale horizontally. The media assets (images, videos) need to be shared across all instances.

Which storage solution should be used for shared media?

- A. Amazon EBS with snapshots shared across instances
- B. Amazon EFS mounted to all instances
- C. Instance store volumes
- D. Amazon S3 with CloudFront

**Correct Answer: D**

**Explanation:** S3 stores media objects (images, videos) and CloudFront caches them at edge locations for fast delivery. S3 is accessible from all instances without mounting. EFS could work but is more expensive for large media files. EBS is single-instance. Instance store is ephemeral. S3 + CloudFront is the most scalable and cost-effective for media assets.

---

### Question 18 (ID: 956303)
An application uses Amazon API Gateway and AWS Lambda. The Lambda function queries an Amazon RDS database. During peak traffic, the database runs out of connections.

What should the Solutions Architect do?

- A. Increase the database connection limit
- B. Use Amazon RDS Proxy
- C. Increase Lambda memory
- D. Use DynamoDB instead

**Correct Answer: B**

**Explanation:** RDS Proxy pools and shares database connections across Lambda invocations. Instead of each Lambda invocation opening a new connection, RDS Proxy maintains a warm connection pool. This prevents exhausting the database connection limit. Increasing the limit is temporary. More Lambda memory doesn't reduce connections. DynamoDB changes the architecture.

---

### Question 19 (ID: 956305)
A company stores compliance documents that cannot be modified or deleted for 5 years after creation. The documents are stored in Amazon S3.

Which S3 feature should be enabled?

- A. S3 Versioning
- B. S3 Object Lock in Compliance mode
- C. S3 MFA Delete
- D. S3 Lifecycle policies

**Correct Answer: B**

**Explanation:** S3 Object Lock in Compliance mode prevents any user (including root) from deleting or modifying objects for the specified retention period. This meets regulatory requirements for immutable records. Governance mode allows some users to override. Versioning preserves versions but doesn't prevent deletion. MFA Delete adds protection but can still be overridden.

---

### Question 20 (ID: 956307)
A company needs to transfer 100 TB of data from on-premises to AWS S3 within 2 weeks. Their internet connection is 1 Gbps.

Which transfer method is MOST efficient?

- A. AWS DataSync over Direct Connect
- B. S3 Transfer Acceleration
- C. AWS Snowball Edge
- D. Multi-part upload over the internet

**Correct Answer: C**

**Explanation:** At 1 Gbps, transferring 100 TB takes ~9 days theoretically, but real-world throughput is lower. Snowball Edge devices (80 TB each) can be loaded locally and shipped to AWS, completing within 2 weeks reliably. DataSync over Direct Connect could work but requires existing DC provisioning. Transfer Acceleration helps but is limited by bandwidth.

---

### Question 21 (ID: 956309)
A Solutions Architect needs to ensure that EC2 instances in a private subnet can download software patches from the internet but cannot be accessed from the internet.

Which configuration should be used?

- A. Internet Gateway with private IP
- B. NAT Gateway in a public subnet with route from private subnet
- C. VPC Endpoint for patch service
- D. Elastic IP on each instance

**Correct Answer: B**

**Explanation:** NAT Gateway enables outbound internet access for private subnet instances while preventing inbound connections from the internet. The private subnet route table routes 0.0.0.0/0 to the NAT Gateway. Internet Gateway requires public IPs. VPC Endpoints only work for AWS services. Elastic IPs make instances publicly accessible.

---

### Question 22 (ID: 956311)
A company's application needs to process messages from an SQS queue. Each message requires exactly 10 minutes to process. Some messages are being processed multiple times.

What should the Solutions Architect do to prevent duplicate processing?

- A. Use a FIFO queue
- B. Increase the visibility timeout to greater than 10 minutes
- C. Enable long polling
- D. Use a dead letter queue

**Correct Answer: B**

**Explanation:** If the visibility timeout is less than processing time, the message becomes visible again and another consumer processes it (duplicate). Setting visibility timeout greater than processing time (e.g., 15 minutes) prevents this. FIFO queues prevent duplicates differently (deduplication ID). Long polling reduces empty receives. Dead letter queues capture failed messages.

---

### Question 23 (ID: 956313)
A company has a data lake in Amazon S3 with petabytes of data. The company wants to run SQL queries on this data without loading it into a traditional database.

Which service should be used?

- A. Amazon Redshift
- B. Amazon RDS
- C. Amazon Athena
- D. AWS Glue

**Correct Answer: C**

**Explanation:** Amazon Athena queries data directly in S3 using standard SQL. It's serverless — no infrastructure to manage, and you pay per query. For a data lake pattern, Athena is the primary query engine. Redshift requires loading data. RDS is a relational database. Glue is for ETL, not interactive querying.

---

### Question 24 (ID: 956315)
A company uses Amazon CloudFront to serve content from an S3 bucket. The company wants to restrict access so that users can ONLY access S3 content through CloudFront, not directly via S3 URLs.

How should this be configured?

- A. S3 bucket policy allowing only CloudFront IP ranges
- B. Origin Access Control (OAC) with CloudFront
- C. VPC endpoint for S3
- D. IAM role for CloudFront

**Correct Answer: B**

**Explanation:** Origin Access Control (OAC) replaces the legacy OAI (Origin Access Identity). It allows CloudFront to access S3 while the bucket policy denies all other access. Users must go through CloudFront. IP-based policies are fragile and change. VPC endpoints are for VPC access. IAM roles don't restrict S3 direct access.

---

### Question 25 (ID: 956317)
A company needs an in-memory caching solution for frequently accessed database queries. The cache must support complex data structures like sorted sets and geospatial data.

Which service should be used?

- A. Amazon ElastiCache Memcached
- B. Amazon ElastiCache Redis
- C. Amazon DynamoDB DAX
- D. Amazon CloudFront

**Correct Answer: B**

**Explanation:** ElastiCache Redis supports advanced data structures: sorted sets, hashes, lists, geospatial indexes, HyperLogLog, and streams. Memcached is simpler (key-value only, no persistence). DAX is specifically for DynamoDB caching. CloudFront caches HTTP responses, not database queries.

---

### Question 26 (ID: 956319)
A company runs a production database on Amazon RDS MySQL. A developer accidentally drops a critical table. The company needs to restore the table to the state 30 minutes before the incident.

What should the DBA do?

- A. Restore from the latest automated backup
- B. Use point-in-time recovery to restore to a new instance 30 minutes before the drop
- C. Promote a Read Replica
- D. Restore from a manual snapshot

**Correct Answer: B**

**Explanation:** Point-in-time recovery (PITR) allows restoring to any second within the backup retention period. The DBA restores to a new RDS instance at the timestamp 30 minutes before the DROP TABLE, then extracts the table data. The latest backup may be hours old. Manual snapshots may not be recent enough. Read Replicas would have replicated the DROP.

---

### Question 27 (ID: 956321)
An application needs to store and retrieve objects at massive scale. Objects range from 1 KB to 5 GB. The application needs millisecond retrieval and the ability to handle millions of requests per second.

Which storage should the Architect choose?

- A. Amazon EBS io2
- B. Amazon S3 Standard
- C. Amazon DynamoDB
- D. Amazon EFS

**Correct Answer: B**

**Explanation:** S3 Standard provides 11 9s of durability, supports objects up to 5 TB, and handles thousands of requests per second per prefix. With prefix partitioning, it scales to millions of requests/second. DynamoDB has a 400 KB item limit. EBS is block storage for single instances. EFS is network file storage with higher latency at scale.

---

### Question 28 (ID: 956323)
A company has an application that receives spike traffic patterns — 100 requests per minute normally, but up to 10,000 during spikes lasting 5 minutes. The backend is AWS Lambda with DynamoDB.

How should the DynamoDB table be configured to handle these spikes cost-effectively?

- A. Provisioned capacity with Auto Scaling
- B. On-Demand capacity mode
- C. Provisioned capacity sized for peak load
- D. DynamoDB Accelerator (DAX)

**Correct Answer: B**

**Explanation:** DynamoDB On-Demand mode instantly accommodates any traffic volume without capacity planning. You pay per request. For spiky workloads with unpredictable peaks, On-Demand is ideal — no throttling, no over-provisioning. Auto Scaling reacts slowly to sudden spikes. Provisioned for peak wastes money during normal traffic. DAX is for caching, not capacity.

---

### Question 29 (ID: 956325)
A company is designing a microservices architecture. Services need to communicate asynchronously, and some services publish events that multiple downstream services need to process.

Which architecture pattern should be used?

- A. Direct HTTP/REST calls between services
- B. Amazon SNS topics with SQS queue subscriptions (fan-out)
- C. Shared database for inter-service communication
- D. AWS Step Functions

**Correct Answer: B**

**Explanation:** SNS + SQS fan-out pattern: the publisher sends to an SNS topic, and each downstream service has its own SQS queue subscribed to the topic. Messages are durably delivered to all subscribers asynchronously. Direct HTTP calls create tight coupling. Shared databases create a single point of failure. Step Functions orchestrate workflows, not pub/sub.

---

### Question 30 (ID: 956327)
A company needs to host a static website with a custom domain and HTTPS. The website should have low latency globally.

Which services should the Solutions Architect use?

- A. EC2 + ALB + ACM
- B. S3 static hosting + CloudFront + ACM + Route 53
- C. Lightsail + Route 53
- D. Elastic Beanstalk + Route 53

**Correct Answer: B**

**Explanation:** S3 hosts the static files, CloudFront provides CDN for global low latency, ACM provides free SSL/TLS certificates for HTTPS, and Route 53 manages the custom domain. This is serverless, fully managed, and highly scalable. EC2/ALB is over-engineered for static content. Lightsail lacks global CDN.

---

### Question 31 (ID: 956329)
A company runs a real-time dashboard that displays IoT sensor data. Thousands of sensors send data every second. The dashboard must show the last 24 hours of data.

Which architecture should be used?

- A. Sensors → API Gateway → Lambda → RDS → Dashboard
- B. Sensors → Kinesis Data Streams → Lambda → DynamoDB (with TTL) → Dashboard
- C. Sensors → SQS → EC2 → S3 → Dashboard
- D. Sensors → SNS → Lambda → ElastiCache → Dashboard

**Correct Answer: B**

**Explanation:** Kinesis Data Streams ingests high-velocity IoT data in real-time. Lambda processes and stores data in DynamoDB with TTL set to 24 hours (auto-delete old data). The dashboard reads from DynamoDB. SQS isn't designed for real-time streaming. RDS may struggle with thousands of writes per second. SNS is for notifications, not data streaming.

---

### Question 32 (ID: 956331)
A company wants to ensure that all EC2 instances are launched with encrypted EBS volumes. This must be enforced across all users in the account.

What is the simplest way to enforce this?

- A. Create an IAM policy denying ec2:RunInstances without encrypted volumes
- B. Enable EBS encryption by default in the account settings
- C. Use AWS Config to detect unencrypted volumes
- D. Use CloudFormation for all instance launches

**Correct Answer: B**

**Explanation:** EBS encryption by default is an account-level setting. Once enabled, all new EBS volumes and snapshots are automatically encrypted using the default CMK. No IAM policy needed. AWS Config detects but doesn't prevent. CloudFormation can enforce but doesn't cover console launches. Account-level default is the simplest solution.

---

### Question 33 (ID: 956333)
A Solutions Architect is designing a multi-account strategy using AWS Organizations. The company wants to consolidate billing and apply security guardrails across all accounts.

Which combination of features should be used?

- A. Consolidated billing only
- B. All features enabled with SCPs
- C. Separate AWS accounts with cross-account roles
- D. AWS Control Tower without Organizations

**Correct Answer: B**

**Explanation:** AWS Organizations with 'All features' enables both consolidated billing and SCPs for security guardrails. SCPs restrict permissions across all member accounts, enforcing security policies centrally. 'Consolidated billing only' doesn't support SCPs. Cross-account roles don't provide centralized guardrails. Control Tower requires Organizations.

---

### Question 34 (ID: 956335)
A company has a batch processing application that reads input files from S3, processes them, and writes output files back to S3. The processing takes 2-4 hours per batch.

Which EC2 purchasing option provides the BEST cost savings for fault-tolerant batch processing?

- A. On-Demand Instances
- B. Spot Instances
- C. Reserved Instances (1-year)
- D. Dedicated Instances

**Correct Answer: B**

**Explanation:** Spot Instances provide up to 90% savings over On-Demand. For fault-tolerant batch processing (can be restarted), Spot is ideal. If an instance is reclaimed, the batch can restart from the last checkpoint. Reserved Instances require a 1-year commitment for batch that may not run continuously. On-Demand is full price.

---

### Question 35 (ID: 956337)
An application uses Amazon Aurora PostgreSQL. The company needs to generate weekly reports that involve complex queries running for 2-3 hours. These report queries are impacting production performance.

What should the Solutions Architect do?

- A. Run the reports during off-peak hours
- B. Create an Aurora Read Replica and run reports against it
- C. Increase the Aurora instance size
- D. Export data to S3 and use Athena

**Correct Answer: B**

**Explanation:** Aurora Read Replicas share the same storage cluster but have separate compute. Directing complex, long-running report queries to a Read Replica eliminates the impact on the production primary instance. Scaling up adds cost and doesn't isolate workloads. Off-peak hours may not coincide with reporting needs. S3/Athena adds pipeline complexity.

---

### Question 36 (ID: 956339)
A company has an on-premises application that needs to access an S3 bucket. The network team requires that the traffic not traverse the public internet.

What should the Solutions Architect configure?

- A. VPN connection + VPC Gateway Endpoint for S3
- B. Direct Connect + VPC Gateway Endpoint for S3
- C. VPN connection + NAT Gateway
- D. Direct Connect public VIF

**Correct Answer: B**

**Explanation:** Direct Connect provides a dedicated private connection from on-premises to AWS. Combined with a VPC Gateway Endpoint for S3, traffic flows privately: on-premises → Direct Connect → VPC → S3 endpoint. VPN over the internet still partially uses the public internet. NAT Gateway routes through the internet. Direct Connect public VIF accesses S3 over the public routing path.

---

### Question 37 (ID: 956341)
A company runs a photo-sharing application. Users upload photos that must be resized into multiple sizes (thumbnail, medium, large). The processing should happen automatically upon upload.

Which architecture should be used?

- A. EC2 instance polling S3 for new objects
- B. S3 event notification → Lambda function for resizing
- C. CloudWatch scheduled event → Lambda
- D. Step Functions with EC2 workers

**Correct Answer: B**

**Explanation:** S3 event notifications trigger Lambda automatically when objects are uploaded. Lambda resizes the image into multiple sizes and writes them back to S3. This is serverless, event-driven, and scales automatically. EC2 polling wastes resources. Scheduled events add delays. Step Functions are over-engineered for simple image processing.

---

### Question 38 (ID: 956343)
A company has a VPC with public and private subnets. The company wants to allow SSH access to EC2 instances in the private subnet from the corporate network (10.0.0.0/8) via a VPN connection.

Which security group configuration should be applied to the private instances?

- A. Allow SSH (port 22) from 0.0.0.0/0
- B. Allow SSH (port 22) from 10.0.0.0/8
- C. Allow all traffic from the VPN gateway
- D. Allow SSH (port 22) from the public subnet CIDR

**Correct Answer: B**

**Explanation:** The security group should allow SSH (port 22) from the corporate network CIDR (10.0.0.0/8). The VPN connection extends the corporate network to the VPC, so corporate IPs can reach private instances. Allowing 0.0.0.0/0 is overly permissive. Allowing from public subnet CIDR doesn't include corporate IPs. Allowing all traffic is too broad.

---

### Question 39 (ID: 956345)
A company has multiple AWS accounts and needs a centralized logging solution. All CloudTrail logs from every account must be stored in a single S3 bucket.

How should this be configured?

- A. Enable CloudTrail in each account pointing to the central bucket with a cross-account bucket policy
- B. Use AWS Config to aggregate logs
- C. Create a Lambda function to copy logs between accounts
- D. Use VPC Flow Logs instead

**Correct Answer: A**

**Explanation:** Create an Organization Trail or enable CloudTrail in each member account, configuring it to deliver logs to a central S3 bucket in the security/logging account. The central bucket has a cross-account bucket policy allowing CloudTrail from all accounts to write. AWS Config is for compliance, not log aggregation. Lambda introduces complexity.

---

### Question 40 (ID: 956347)
A Solutions Architect is designing a solution for a video streaming platform. Videos are uploaded in high resolution and must be transcoded into multiple formats (720p, 1080p, 4K).

Which AWS service should be used for video transcoding?

- A. AWS Lambda
- B. Amazon Elastic Transcoder / AWS Elemental MediaConvert
- C. Amazon EC2 with FFmpeg
- D. Amazon Kinesis Video Streams

**Correct Answer: B**

**Explanation:** AWS Elemental MediaConvert (successor to Elastic Transcoder) is a file-based video transcoding service. It converts video files into multiple formats and resolutions for distribution. Lambda has a 15-minute limit and size constraints. EC2 with FFmpeg requires management. Kinesis Video Streams is for real-time video streaming, not transcoding.

---

### Question 41 (ID: 956349)
A company has a critical application that must achieve an RPO of near-zero and RTO of less than 1 minute. The application uses Amazon Aurora MySQL.

Which DR strategy should be implemented?

- A. Aurora with Multi-AZ
- B. Aurora Global Database
- C. Aurora with automated backups to S3
- D. Aurora Read Replicas in another Region

**Correct Answer: B**

**Explanation:** Aurora Global Database replicates data across Regions with typically less than 1-second lag (near-zero RPO). Failover to a secondary Region can complete in less than 1 minute (RTO). Multi-AZ handles AZ failures but not Regional failures. Automated backups have RPO of hours. Cross-Region Read Replicas have higher lag and manual promotion.

---

### Question 42 (ID: 956351)
A company wants to implement a CI/CD pipeline for deploying applications to EC2 instances. The pipeline should support blue/green deployments.

Which AWS service provides blue/green deployment capabilities?

- A. AWS CodePipeline
- B. AWS CodeDeploy
- C. AWS CodeBuild
- D. AWS CloudFormation

**Correct Answer: B**

**Explanation:** AWS CodeDeploy supports blue/green deployments, where a new set of instances (green) is provisioned alongside the existing instances (blue). Traffic is shifted to green after validation. If issues arise, traffic reverts to blue. CodePipeline orchestrates the pipeline. CodeBuild compiles code. CloudFormation manages infrastructure but doesn't inherently do blue/green.

---

### Question 43 (ID: 956353)
A company needs to store time-series data from IoT devices. The data must be queryable by device ID and timestamp, and old data (>90 days) should be automatically deleted.

Which service should the Solutions Architect recommend?

- A. Amazon RDS
- B. Amazon DynamoDB with TTL
- C. Amazon Timestream
- D. Amazon S3 with lifecycle policies

**Correct Answer: C**

**Explanation:** Amazon Timestream is a purpose-built time-series database optimized for IoT and operational data. It automatically moves data between memory and magnetic storage tiers and supports built-in time-based data retention. DynamoDB with TTL works but isn't optimized for time-series queries. S3 is object storage, not queryable for time-series patterns.

---

### Question 44 (ID: 956355)
A Solutions Architect needs to design an application that processes messages from multiple SQS queues. Each message type requires different processing logic. The messages must be processed in parallel.

Which approach should be used?

- A. Single Lambda function subscribing to all queues
- B. Separate Lambda functions for each queue with event source mappings
- C. EC2 instance polling all queues
- D. Step Functions orchestrating queue processing

**Correct Answer: B**

**Explanation:** Separate Lambda functions with event source mappings provide isolated processing logic per queue type. Each Lambda scales independently based on its queue depth. Lambda processes messages in parallel automatically. A single function for all queues creates maintenance complexity. EC2 polling wastes resources. Step Functions add orchestration overhead.

---

### Question 45 (ID: 956357)
A company has a web application behind an ALB. The company wants to protect against common web attacks such as SQL injection, cross-site scripting (XSS), and known bad IP addresses.

Which AWS service should be used?

- A. AWS Shield
- B. AWS WAF
- C. Security Groups
- D. Network ACLs

**Correct Answer: B**

**Explanation:** AWS WAF (Web Application Firewall) protects against common web exploits: SQL injection, XSS, and allows IP-based rules. It integrates directly with ALB, CloudFront, and API Gateway. Shield provides DDoS protection. Security groups and NACLs control network access but don't inspect application-layer attacks.

---

### Question 46 (ID: 956359)
A company stores backup data in S3 Glacier. A compliance audit requires immediate access to a specific archived file.

Which Glacier retrieval option provides the fastest access?

- A. Standard retrieval (3-5 hours)
- B. Bulk retrieval (5-12 hours)
- C. Expedited retrieval (1-5 minutes)
- D. Provisioned capacity + Expedited retrieval

**Correct Answer: D**

**Explanation:** Provisioned capacity guarantees Expedited retrieval availability. Expedited retrieval returns data within 1-5 minutes. Without provisioned capacity, Expedited requests may be rejected during peak load. Standard takes 3-5 hours. Bulk is cheapest but 5-12 hours. For guaranteed fast access during audits, Provisioned + Expedited is best.

---

### Question 47 (ID: 956361)
A company has a Lambda function that needs to access resources in a VPC (RDS database) and also needs to access the internet (external API calls).

How should the VPC be configured?

- A. Lambda in public subnet with Internet Gateway
- B. Lambda in private subnet with NAT Gateway in public subnet
- C. Lambda outside VPC with VPC peering
- D. Lambda in private subnet with VPC Endpoint only

**Correct Answer: B**

**Explanation:** VPC-attached Lambda functions run in private subnets. For internet access, a NAT Gateway in a public subnet with a route from the private subnet provides outbound internet connectivity. Lambda cannot be placed in public subnets effectively. VPC Endpoints only work for AWS services, not external APIs. Lambda outside VPC can't access VPC resources natively.

---

### Question 48 (ID: 956363)
A company runs a legacy application that uses a proprietary database on-premises. The company wants to migrate to AWS using Amazon EC2 while maintaining the same database.

Which migration strategy is this?

- A. Replatform
- B. Rehost (Lift and Shift)
- C. Refactor
- D. Retain

**Correct Answer: B**

**Explanation:** Rehost (lift and shift) moves the application to AWS as-is, without changes. The same database runs on EC2 (instead of on-premises servers). Replatform makes minor optimizations (e.g., moving to RDS). Refactor involves significant code changes. Retain keeps the application on-premises.

---

### Question 49 (ID: 956365)
A company has an application that writes data to an SQS queue. A consumer Lambda function processes messages. Sometimes the Lambda function fails, and messages are retried. After 3 failures, the messages should be moved for investigation.

Which feature should be configured?

- A. SQS dead-letter queue with maxReceiveCount of 3
- B. Lambda error handling with catch blocks
- C. SQS message retention period
- D. CloudWatch Alarms for failed invocations

**Correct Answer: A**

**Explanation:** A dead-letter queue (DLQ) captures messages that fail processing after a specified number of attempts (maxReceiveCount). Setting maxReceiveCount to 3 means after 3 failed processing attempts, the message moves to the DLQ for investigation. Lambda error handling doesn't prevent reprocessing. Message retention controls how long messages stay in the queue.

---

### Question 50 (ID: 956367)
A company needs a managed database service that is compatible with Apache Cassandra for their existing Cassandra-based application.

Which AWS service should be used?

- A. Amazon DynamoDB
- B. Amazon Keyspaces (for Apache Cassandra)
- C. Amazon DocumentDB
- D. Amazon Neptune

**Correct Answer: B**

**Explanation:** Amazon Keyspaces is a fully managed, Apache Cassandra-compatible database service. Existing Cassandra applications can connect using CQL (Cassandra Query Language) with minimal code changes. DynamoDB has a different API. DocumentDB is MongoDB-compatible. Neptune is a graph database.

---

### Question 51 (ID: 956369)
A company has a data pipeline: S3 → Glue ETL → Redshift. The Glue jobs fail occasionally due to data format errors. The company wants to be notified immediately when a job fails.

How should this be set up?

- A. CloudWatch Events (EventBridge) rule for Glue job state changes → SNS notification
- B. S3 event notification → Lambda
- C. CloudWatch Logs → Alarm
- D. Glue Crawler scheduler

**Correct Answer: A**

**Explanation:** Amazon EventBridge detects Glue job state changes (FAILED, SUCCEEDED). A rule targets SNS to send email/SMS notifications when a job fails. This is real-time and event-driven. S3 events are for object-level changes. CloudWatch Logs alarms have delay. Glue Crawler scheduler is for data catalog, not job monitoring.

---

### Question 52 (ID: 956371)
A Solutions Architect needs to design a serverless REST API that performs CRUD operations on a DynamoDB table.

Which minimal architecture should be used?

- A. EC2 + Express.js + DynamoDB
- B. API Gateway + Lambda + DynamoDB
- C. ALB + ECS + DynamoDB
- D. API Gateway + EC2 + RDS

**Correct Answer: B**

**Explanation:** API Gateway → Lambda → DynamoDB is the standard serverless CRUD pattern. API Gateway handles HTTP requests, Lambda executes business logic, DynamoDB stores data. All three are serverless, pay-per-use, and auto-scaling. EC2 and ECS require infrastructure management. RDS isn't serverless by default.

---

### Question 53 (ID: 956373)
A company has EC2 instances in us-east-1 that need to replicate data to eu-west-1 for disaster recovery. The data is stored on EBS volumes.

How should cross-Region EBS replication be configured?

- A. EBS volume mirroring
- B. Create EBS snapshots and copy them to eu-west-1
- C. AWS DataSync between EBS volumes
- D. S3 Cross-Region Replication of EBS data

**Correct Answer: B**

**Explanation:** EBS snapshots can be copied across Regions. The workflow: create a snapshot of the EBS volume → copy the snapshot to eu-west-1 → restore the snapshot as a new volume in eu-west-1. This can be automated with Lambda and CloudWatch Events. EBS doesn't support native mirroring. DataSync works with NFS/SMB, not EBS. S3 CRR is for S3 objects.

---

### Question 54 (ID: 956375)
A company has a web application that serves dynamic content. Some pages are extremely popular and account for 80% of traffic. The pages change every 5 minutes.

How should the Architect optimize performance?

- A. Deploy the application in multiple Regions
- B. Use CloudFront with a TTL of 5 minutes
- C. Use ElastiCache Redis for page caching
- D. Increase EC2 instance sizes

**Correct Answer: B**

**Explanation:** CloudFront with a 5-minute TTL caches popular pages at edge locations globally. After 5 minutes, CloudFront fetches the updated content from the origin. This offloads 80% of traffic from the origin servers. ElastiCache works but only at the Region level. Multi-Region adds complexity. Larger instances have a cost ceiling.

---

### Question 55 (ID: 956377)
A company implements AWS CloudFormation to provision infrastructure. A developer accidentally changes infrastructure manually. The company wants to detect drift from the intended configuration.

Which feature should be used?

- A. CloudFormation Change Sets
- B. CloudFormation Drift Detection
- C. AWS Config
- D. CloudTrail

**Correct Answer: B**

**Explanation:** CloudFormation Drift Detection compares the actual resource configuration against the expected template configuration. It identifies resources that have been modified outside of CloudFormation. Change Sets preview changes before updating stacks. AWS Config tracks configuration changes but doesn't compare to templates. CloudTrail logs API calls but doesn't detect drift.

---

### Question 56 (ID: 956379)
A company has an application that requires a PostgreSQL-compatible database with up to 128 TB of storage, auto-scaling replicas, and 5x better throughput than standard PostgreSQL.

Which service should be used?

- A. Amazon RDS PostgreSQL
- B. Amazon Aurora PostgreSQL
- C. PostgreSQL on EC2
- D. Amazon Redshift (PostgreSQL-compatible)

**Correct Answer: B**

**Explanation:** Amazon Aurora PostgreSQL is PostgreSQL-compatible, provides up to 128 TB of auto-scaling storage, up to 15 auto-scaling replicas, and delivers 3-5x better throughput than standard PostgreSQL. RDS PostgreSQL has lower storage limits and no auto-scaling storage. EC2 requires full self-management. Redshift is for data warehousing, not OLTP.

---

### Question 57 (ID: 956381)
A company needs to share a large dataset (S3 bucket) with a partner company's AWS account without making the data public.

What is the MOST secure approach?

- A. Make the bucket public and share the URL
- B. Cross-account S3 bucket policy granting access to the partner's AWS account ID
- C. Copy the data to a new bucket in the partner's account
- D. Generate pre-signed URLs for each object

**Correct Answer: B**

**Explanation:** A cross-account bucket policy grants access to a specific AWS account ID. This is secure (no public access), scalable (works for the entire bucket), and doesn't require data copying. Making the bucket public is insecure. Copying data doubles storage cost. Pre-signed URLs expire and don't scale for large datasets.

---

### Question 58 (ID: 956383)
A company wants to implement a search feature in their application. They need full-text search, faceted search, and autocomplete capabilities.

Which AWS service should be used?

- A. Amazon DynamoDB
- B. Amazon RDS with full-text indexes
- C. Amazon OpenSearch Service (Elasticsearch)
- D. Amazon S3 Select

**Correct Answer: C**

**Explanation:** Amazon OpenSearch Service (formerly Elasticsearch Service) provides full-text search, faceted search, autocomplete (suggest API), and near real-time results. DynamoDB is a key-value store without full-text search. RDS full-text indexes are limited. S3 Select queries individual objects, not search across data.

---

### Question 59 (ID: 956385)
A company runs a web application on EC2 instances. The security team wants to inspect VPC traffic for anomalous patterns and potential intrusions.

Which service provides network traffic analysis?

- A. AWS WAF
- B. Amazon GuardDuty
- C. VPC Flow Logs + Amazon Detective
- D. AWS Shield

**Correct Answer: B**

**Explanation:** Amazon GuardDuty analyzes VPC Flow Logs, CloudTrail logs, and DNS logs to detect anomalous patterns, unauthorized access, and potential intrusions using machine learning. GuardDuty is a managed threat detection service. WAF protects web apps at Layer 7. Shield defends against DDoS. VPC Flow Logs alone don't analyze patterns.

---

### Question 60 (ID: 956387)
A company uses Amazon S3 for data storage. They want to minimize costs for data that has unpredictable access patterns — sometimes frequently accessed, sometimes not accessed for months.

Which S3 storage class should be used?

- A. S3 Standard
- B. S3 Standard-IA
- C. S3 Intelligent-Tiering
- D. S3 One Zone-IA

**Correct Answer: C**

**Explanation:** S3 Intelligent-Tiering automatically moves objects between frequent and infrequent access tiers based on access patterns. No retrieval fees and no performance impact. It's ideal for unpredictable access patterns. Standard is expensive for rarely accessed data. Standard-IA charges retrieval fees. One Zone-IA has lower durability.

---

### Question 61 (ID: 956389)
A company is deploying an application that requires persistent block storage that automatically replicates within an AZ. The storage must support up to 64,000 IOPS.

Which storage should be used?

- A. Instance Store
- B. EBS io2 Block Express
- C. EBS gp3
- D. Amazon EFS

**Correct Answer: B**

**Explanation:** EBS io2 Block Express supports up to 256,000 IOPS and 4,000 MB/s throughput. It replicates within the AZ for durability. gp3 maxes out at 16,000 IOPS. Instance Store is ephemeral (not persistent). EFS is network file storage with lower per-instance IOPS. io2 Block Express is the highest-performance persistent block storage.

---

### Question 62 (ID: 956391)
A company wants to implement infrastructure as code using AWS CloudFormation. They need to parameterize templates for different environments (dev, staging, prod).

Which CloudFormation feature should be used?

- A. Nested Stacks
- B. Parameters and Conditions
- C. Stack Sets
- D. Output exports

**Correct Answer: B**

**Explanation:** CloudFormation Parameters allow users to input values at stack creation (e.g., environment name, instance size). Conditions use parameters to conditionally create resources (e.g., only create a larger instance in prod). Nested Stacks are for reusable components. Stack Sets deploy across accounts/Regions. Output exports share values between stacks.

---

### Question 63 (ID: 956393)
A company has a data processing application that runs on a fleet of EC2 instances. The application stores intermediate data on local instance store volumes. If an instance terminates unexpectedly, the intermediate data is lost.

How should the Architect improve data durability?

- A. Use larger instance store volumes
- B. Replace instance store with EBS volumes
- C. Enable termination protection
- D. Use a placement group

**Correct Answer: B**

**Explanation:** EBS volumes persist independently of the instance lifecycle. If an instance terminates, the EBS volume data remains (if not set to delete on termination). Instance store data is ephemeral — lost on termination, stop, or hardware failure. Termination protection prevents accidental termination but doesn't protect against hardware failure. Placement groups don't affect storage durability.

---

### Question 64 (ID: 956395)
A company wants to deploy a multi-Region active-active architecture for their web application. The application uses a DynamoDB table.

Which DynamoDB feature enables multi-Region active-active?

- A. DynamoDB Streams
- B. DynamoDB Global Tables
- C. DynamoDB Cross-Region Replication (manual)
- D. DynamoDB Backup and Restore

**Correct Answer: B**

**Explanation:** DynamoDB Global Tables provide fully managed, multi-Region, multi-active replication. Writes in any Region are automatically replicated to all other Regions within seconds. This enables active-active architectures. Streams enable replication but require custom Lambda functions. Backup/Restore is for DR, not active-active.

---

## Summary
This file contains all 64 questions from SAA-C01 Simulation Test 01.
