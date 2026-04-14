# AWS SAA Exam - EC2 & Compute Services

> **Domain Coverage:** Design High-Performing Architectures, Design Resilient Architectures, Design Cost-Optimized Architectures
> **Services:** EC2, Auto Scaling, Elastic Beanstalk, ECS, EKS, Placement Groups, AMI, Launch Templates

---

## Questions & Answers

### Question 1
A company is launching a new web application on Amazon EC2 instances. The application requires consistent, low-latency communication between the instances. The instances are in the same AWS Region.

Which placement group strategy should the Solutions Architect recommend?

- A. Partition placement group
- B. Spread placement group
- C. Cluster placement group
- D. Default placement group

**Correct Answer: C**

**Explanation:** Cluster placement groups pack instances close together inside an Availability Zone. This strategy enables workloads to achieve the low-latency network performance necessary for tightly-coupled node-to-node communication. Spread placement groups place instances across distinct underlying hardware to reduce correlated failures. Partition placement groups spread instances across logical partitions to limit the impact of hardware failure.

---

### Question 2
A company runs a stateless web application on Amazon EC2 instances behind an Application Load Balancer. The application experiences variable traffic patterns with unpredictable spikes.

Which approach provides the MOST cost-effective solution while maintaining availability?

- A. Use Reserved Instances for baseline capacity and On-Demand Instances for peak traffic
- B. Use On-Demand Instances with Auto Scaling
- C. Use Reserved Instances for baseline capacity and Spot Instances with Auto Scaling for peak traffic
- D. Use Dedicated Hosts for all instances

**Correct Answer: C**

**Explanation:** Reserved Instances provide significant cost savings (up to 72%) for predictable baseline capacity. Spot Instances can save up to 90% compared to On-Demand and are ideal for stateless, fault-tolerant workloads that can handle interruptions. Auto Scaling ensures the application scales to meet demand. This combination provides the best cost-optimization.

---

### Question 3
An application is running on Amazon EC2 instances behind an Application Load Balancer. The instances run in an Auto Scaling group across multiple Availability Zones. Four instances are required to handle a predictable traffic load. The Solutions Architect wants to ensure that the operation is fault-tolerant up to the loss of one Availability Zone.

Which is the MOST cost-efficient way to meet these requirements?

- A. Deploy two instances in each of three Availability Zones.
- B. Deploy two instances in each of two Availability Zones.
- C. Deploy four instances in each of two Availability Zones.
- D. Deploy one instance in each of three Availability Zones.

**Correct Answer: A**

**Explanation:** With 2 instances in each of 3 AZs (6 total), if one AZ is lost, 4 instances remain across the other 2 AZs — exactly meeting the requirement. Option B (4 total) would leave only 2 instances if an AZ fails. Option C (8 total) is over-provisioned and not cost-efficient. Option D (3 total) doesn't meet the 4-instance requirement even without failure.

---

### Question 4
A Solutions Architect needs to design a solution for a legacy application that runs on a single EC2 instance. The application stores session data locally. The company wants to improve availability without modifying the application.

What should the Solutions Architect recommend?

- A. Deploy the application across multiple AZs with an ALB and store sessions in Amazon ElastiCache
- B. Create an AMI of the instance and use it in a launch template with Auto Scaling (min=1, max=1, desired=1)
- C. Use a Spot Instance with a Spot Fleet
- D. Deploy the application on AWS Lambda

**Correct Answer: B**

**Explanation:** Since the application cannot be modified and stores session data locally, the best approach is to create an AMI and use Auto Scaling with min/max/desired of 1. If the instance fails, Auto Scaling will automatically launch a replacement. Options A/D require application modification. Option C with Spot Instances could cause interruptions.

---

### Question 5
A company is migrating a monolithic application to AWS. The application runs on Windows and requires specific hardware-bound licenses tied to physical cores.

Which EC2 option should the Solutions Architect recommend?

- A. Dedicated Instances
- B. Dedicated Hosts
- C. Reserved Instances
- D. Spot Instances

**Correct Answer: B**

**Explanation:** Dedicated Hosts provide visibility and control over the physical server, including socket and core counts. This allows the use of per-core, per-socket, or per-VM software licenses such as Windows Server, SQL Server, and SUSE Linux Enterprise Server. Dedicated Instances run on hardware dedicated to your account but don't provide the same visibility into underlying hardware for licensing purposes.

---

### Question 6
A web application requires instances that can handle sudden, unpredictable traffic bursts followed by periods of steady traffic. The application can tolerate occasional instance terminations.

Which EC2 purchasing option combination provides the MOST cost-effective solution?

- A. All On-Demand Instances
- B. All Spot Instances
- C. On-Demand Instances for stable baseline with Spot Instances for burst capacity
- D. Reserved Instances for everything

**Correct Answer: C**

**Explanation:** On-Demand provides reliable baseline capacity, while Spot Instances (up to 90% cheaper) handle burst traffic cost-effectively. Since the application tolerates interruptions, Spot is suitable for the variable portion. All Spot would risk availability during Spot interruptions. All On-Demand would be expensive. All Reserved doesn't handle variable traffic well.

---

### Question 7
A company is running an application on EC2 instances in a private subnet. The instances need to download software patches from the internet but should NOT be accessible from the internet.

Which solution should the Solutions Architect implement?

- A. Internet Gateway attached to the VPC
- B. NAT Gateway in a public subnet
- C. VPC Endpoint for S3
- D. Bastion host in a public subnet

**Correct Answer: B**

**Explanation:** A NAT Gateway in a public subnet allows instances in private subnets to initiate outbound connections to the internet (e.g., download patches) while preventing inbound connections from the internet. Internet Gateway alone doesn't help private subnet instances. VPC Endpoint is for AWS services only. Bastion host is for SSH access, not internet access for the instances.

---

### Question 8
An organization wants to migrate a legacy Ruby-on-Rails application to AWS. The application is not used frequently, but it must be scalable during peak use. The organization requires minimal code changes.

Which solution will meet the requirements?

- A. Migrate the application to AWS Lambda.
- B. Deploy the application to an EC2 instance.
- C. Host the application on Amazon S3, and use Amazon CloudFront to cache static assets.
- D. Create an AWS Elastic Beanstalk deployment for the application with satisfactory scaling criteria.

**Correct Answer: D**

**Explanation:** Elastic Beanstalk supports Ruby and handles deployment, capacity provisioning, load balancing, and auto-scaling with minimal code changes. Lambda would require significant application restructuring. A single EC2 instance doesn't auto-scale. S3/CloudFront is for static sites only, not Ruby-on-Rails applications.

---

### Question 9
A company needs to run a batch processing workload that can be interrupted. The workload consists of thousands of independent, short-running tasks. The results are stored in Amazon S3.

Which compute option is the MOST cost-effective?

- A. EC2 On-Demand Instances
- B. EC2 Spot Instances with Spot Fleet
- C. AWS Lambda functions
- D. EC2 Reserved Instances

**Correct Answer: B**

**Explanation:** Spot Instances are up to 90% cheaper than On-Demand and ideal for batch processing workloads that are fault-tolerant and can be interrupted. Spot Fleet allows you to define instance pools and manage a fleet of Spot Instances automatically. Lambda has execution time limits (15 min). Reserved Instances are for steady-state workloads.

---

### Question 10
A company has deployed an application on EC2 instances with an Auto Scaling group. The application stores session state in memory. Users report losing their session when instances are terminated during a scale-in event.

What should the Solutions Architect do to resolve this issue?

- A. Use sticky sessions on the ALB
- B. Store session data in Amazon DynamoDB or ElastiCache
- C. Increase the minimum number of instances in the Auto Scaling group
- D. Use a Network Load Balancer instead

**Correct Answer: B**

**Explanation:** Storing session data in an external store (DynamoDB or ElastiCache) decouples the session from the instance. This way, when instances terminate, sessions persist. Sticky sessions can help but don't solve the problem when instances are terminated. Increasing minimum instances adds cost without solving the root issue.

---

### Question 11
A Solutions Architect needs to deploy an application that requires a minimum of 4 EC2 instances. The instances must be placed on separate underlying hardware to minimize the impact of hardware failure.

Which placement group type meets this requirement?

- A. Cluster placement group
- B. Partition placement group
- C. Spread placement group
- D. Default placement group

**Correct Answer: C**

**Explanation:** Spread placement groups place each instance on distinct underlying hardware, reducing the risk of simultaneous failures. This is ideal for small numbers of critical instances. Note: Spread placement groups are limited to 7 running instances per AZ per group. Cluster groups are for low-latency, not fault tolerance. Partition groups are for large distributed workloads like HDFS/Cassandra.

---

### Question 12
A company is deploying a containerized microservices application. The company wants to use AWS-managed infrastructure and does not want to manage the underlying servers.

Which service should the Solutions Architect recommend?

- A. Amazon ECS on EC2
- B. Amazon ECS on AWS Fargate
- C. Amazon EC2 with Docker installed
- D. Amazon EKS on EC2

**Correct Answer: B**

**Explanation:** AWS Fargate is a serverless compute engine for containers that works with Amazon ECS (and EKS). It removes the need to provision, configure, or scale clusters of virtual machines to run containers. ECS on EC2 and EKS on EC2 both require managing EC2 instances. Docker on EC2 requires even more management overhead.

---

### Question 13
A company runs a compute-intensive scientific modeling application on EC2. The application runs for 6 hours daily, 5 days a week. The company wants to minimize costs.

Which purchasing option is MOST cost-effective?

- A. On-Demand Instances started and stopped daily
- B. Reserved Instances (1-year term)
- C. Spot Instances
- D. Scheduled Reserved Instances

**Correct Answer: A**

**Explanation:** For workloads that run on a predictable but non-continuous schedule (30 hours/week vs 168 hours/week), On-Demand Instances that are started and stopped per schedule are the most cost-effective. Reserved Instances charge for the full 24/7 period regardless of usage. Spot Instances risk interruption for a 6-hour scientific computation. Scheduled Reserved Instances have been deprecated in most regions.

---

### Question 14
A Solutions Architect is designing an application that needs to process images uploaded by users. The processing takes between 5-20 minutes per image. The workload is unpredictable.

Which architecture provides the MOST scalable and cost-effective solution?

- A. EC2 instances polling an SQS queue for new images
- B. AWS Lambda triggered by S3 upload events
- C. EC2 instances with Auto Scaling based on SQS queue depth
- D. A single large EC2 instance

**Correct Answer: C**

**Explanation:** Lambda has a 15-minute execution limit, so images that take up to 20 minutes can't reliably be processed. EC2 instances with Auto Scaling based on SQS queue depth provide scalability and cost optimization — scaling out when the queue is deep and scaling in when idle. A single EC2 instance doesn't scale and is a single point of failure.

---

### Question 15
A company wants to launch Amazon EC2 instances and needs the instances to have the lowest possible latency between them. The instances will communicate using a custom UDP-based protocol.

Which configuration should the Solutions Architect use?

- A. Launch instances in a spread placement group in multiple AZs
- B. Launch instances in a cluster placement group in a single AZ
- C. Launch instances with enhanced networking in multiple AZs
- D. Launch instances with Elastic Fabric Adapter (EFA) in multiple AZs

**Correct Answer: B**

**Explanation:** Cluster placement groups provide the lowest possible inter-instance latency by packing instances close together within a single AZ. Enhanced networking and EFA improve network performance but don't minimize inter-instance latency like cluster placement. Spread placement groups and multiple AZs introduce higher latency.

---

### Question 16
A development team needs to share a custom AMI with another AWS account in the same Region. The AMI was created from an instance with an encrypted EBS volume using a customer-managed AWS KMS key.

What steps must be completed to share the AMI? (Select TWO)

- A. Share the AMI with the target account
- B. Share the KMS key with the target account by modifying the key policy
- C. Copy the AMI to the target account's Region
- D. Decrypt the EBS volume before creating the AMI
- E. Make the AMI public

**Correct Answer: A, B**

**Explanation:** To share an AMI with encrypted snapshots: (1) Share the AMI with the target account by modifying the launch permissions. (2) Share the KMS key used to encrypt the snapshot by updating the key policy to grant the target account access. You cannot share AMIs encrypted with the default AWS-managed key. Making the AMI public is not necessary for sharing with specific accounts.

---

### Question 17
A company has an application that generates large amounts of data. The data must be processed within 1 second of being generated. The data processing is compute-intensive and requires GPU acceleration.

Which EC2 instance type is MOST appropriate?

- A. C5 (Compute Optimized)
- B. P3 (Accelerated Computing / GPU)
- C. R5 (Memory Optimized)
- D. M5 (General Purpose)

**Correct Answer: B**

**Explanation:** P3 instances provide GPU acceleration for compute-intensive workloads such as machine learning, computational fluid dynamics, genomics, and financial analysis. C5 instances are CPU-optimized but don't provide GPUs. R5 instances are for memory-intensive workloads. M5 is general purpose.

---

### Question 18
An application running on EC2 needs to store temporary data that requires high IOPS. The data does not need to persist after the instance is stopped.

Which storage option is MOST cost-effective?

- A. Amazon EBS Provisioned IOPS SSD (io1)
- B. Amazon EBS General Purpose SSD (gp3)
- C. Instance Store (ephemeral storage)
- D. Amazon EFS

**Correct Answer: C**

**Explanation:** Instance Store provides temporary block-level storage that is physically attached to the host computer. It provides very high IOPS at no additional cost (included in the instance price). Since the data doesn't need to persist after instance stop, Instance Store is the most cost-effective option. EBS volumes persist independently and cost extra.

---

### Question 19
A company runs Windows workloads on Amazon EC2 and wants to ensure instances are automatically replaced within minutes if they become unhealthy.

Which feature should the Solutions Architect use?

- A. EC2 Auto Recovery
- B. Auto Scaling group with health checks
- C. CloudWatch alarm with EC2 reboot action
- D. AWS Systems Manager maintenance window

**Correct Answer: B**

**Explanation:** An Auto Scaling group with health checks (EC2 status checks or ELB health checks) automatically terminates unhealthy instances and launches replacements using a launch template or launch configuration. EC2 Auto Recovery only recovers the same instance on new hardware (doesn't replace). CloudWatch reboot action only reboots, doesn't replace.

---

### Question 20
A company needs to run an application that requires a specific operating system configuration and custom kernel modules. The application needs to run on dedicated physical servers for compliance requirements.

Which EC2 option should be used?

- A. Dedicated Instances
- B. Dedicated Hosts
- C. Bare Metal Instances
- D. Reserved Instances

**Correct Answer: C**

**Explanation:** EC2 Bare Metal instances provide direct access to the underlying server hardware, allowing custom kernel modules, hypervisors, and OS configurations. Dedicated Hosts provide dedicated physical servers but still run on AWS's hypervisor. Dedicated Instances run on dedicated hardware but don't provide direct hardware access.

---

### Question 21
An Auto Scaling group has the following configuration: Min=2, Max=10, Desired=4. A scaling policy with a cooldown period of 300 seconds is configured. A CloudWatch alarm triggers a scale-out event. Two instances are being launched.

What happens if another alarm triggers during the cooldown period?

- A. Two more instances are launched immediately
- B. The scaling activity is ignored until the cooldown period expires
- C. The alarm is queued and processed after cooldown
- D. The Auto Scaling group is set to Max capacity

**Correct Answer: B**

**Explanation:** During the cooldown period, Auto Scaling ignores additional scaling activities. This prevents excessive scaling. The cooldown period gives newly launched instances time to start handling traffic, after which accurate metrics can trigger appropriate scaling decisions.

---

### Question 22
A media company has deployed a multi-tier architecture on AWS. Web servers are deployed in two Availability Zones using an Auto Scaling group with a default Auto Scaling termination policy. The web servers' Auto Scaling group currently has 15 instances running.

Which instance will be terminated first during a scale-in operation?

- A. The instance with the oldest launch configuration
- B. The instance in the Availability Zone that has most instances
- C. The instance closest to the next billing hour
- D. The oldest instance in the group

**Correct Answer: B**

**Explanation:** The default termination policy first selects the AZ with the most instances to maintain balance. Within that AZ, it selects the instance with the oldest launch configuration/template. If there's still a tie, it selects the instance closest to the next billing hour.

---

### Question 23
A company needs to run a Windows-based application that requires .NET Framework 4.8. The company wants minimal infrastructure management.

Which service should the Solutions Architect recommend?

- A. AWS Lambda with .NET runtime
- B. Amazon ECS with Windows containers
- C. AWS Elastic Beanstalk with Windows Server platform
- D. Amazon EC2 with Windows Server AMI

**Correct Answer: C**

**Explanation:** Elastic Beanstalk supports Windows Server with .NET Framework and handles infrastructure provisioning, load balancing, auto-scaling, and monitoring. This provides minimal management overhead. Lambda supports .NET Core but not .NET Framework 4.8. EC2 requires more management. ECS with Windows containers adds container management complexity.

---

### Question 24
A Solutions Architect needs to design a solution where an application must maintain a persistent connection to an EC2 instance for several hours. The application uses WebSocket protocol.

Which load balancer type should be used?

- A. Classic Load Balancer
- B. Application Load Balancer
- C. Network Load Balancer
- D. Gateway Load Balancer

**Correct Answer: B**

**Explanation:** Application Load Balancer (ALB) natively supports WebSocket connections, which are long-lived, full duplex connections. ALB handles the WebSocket upgrade from HTTP/HTTPS automatically. NLB works at Layer 4 and can also handle WebSocket connections, but ALB is the more appropriate choice as WebSocket is an application-layer protocol.

---

### Question 25
A company wants to ensure that all EC2 instances launched in their account have specific tags applied for cost allocation. The company wants to prevent instances from being launched without the required tags.

Which solution meets this requirement?

- A. Use AWS Config rules to check for tags after launch
- B. Use IAM policies with tag-based conditions using `aws:RequestTag`
- C. Use AWS CloudFormation to launch all instances
- D. Use AWS Organizations SCP to deny launching without tags

**Correct Answer: B**

**Explanation:** IAM policies with `aws:RequestTag` condition keys can enforce that specific tags must be provided when creating resources. If the tags are missing, the API call is denied. This is proactive enforcement. AWS Config rules detect non-compliance after the fact (reactive). SCPs can also work but are applied at the organization level.

---

### Question 26
A company has an Auto Scaling group with instances in 3 AZs. The desired capacity is 6. An AZ experiences an outage.

What does Auto Scaling do?

- A. Does nothing until the AZ recovers
- B. Launches 2 new instances spread across the remaining 2 AZs
- C. Launches 6 new instances in the remaining 2 AZs
- D. Reduces the desired capacity to 4

**Correct Answer: B**

**Explanation:** Auto Scaling detects unhealthy instances in the failed AZ and launches replacement instances in the remaining healthy AZs to maintain the desired capacity of 6. It distributes instances evenly across available AZs. So if 2 instances were in the failed AZ, it launches 2 new ones across the remaining AZs.

---

### Question 27
A company is running a High Performance Computing (HPC) workload on EC2. The application requires high throughput, low latency communication between instances using MPI (Message Passing Interface).

Which combination of features should the Solutions Architect use?

- A. Cluster placement group + Elastic Fabric Adapter (EFA)
- B. Spread placement group + Enhanced Networking
- C. Partition placement group + EFA
- D. Cluster placement group + Elastic Network Adapter (ENA)

**Correct Answer: A**

**Explanation:** For HPC workloads using MPI: Cluster placement groups minimize inter-instance latency, and EFA (Elastic Fabric Adapter) provides OS-bypass capabilities for high-throughput, low-latency inter-instance communication. EFA supports MPI applications. ENA provides enhanced networking but not the OS-bypass capability needed for HPC/MPI workloads.

---

### Question 28
A company runs a legacy application on a single m4.large EC2 instance. Monitoring shows the instance CPU utilization averages 5% but spikes to 90% for 3 minutes every hour.

Which instance type change would be MOST cost-effective?

- A. t3.large with unlimited mode
- B. t3.large with standard mode
- C. m5.large
- D. c5.large

**Correct Answer: A**

**Explanation:** T3 instances provide a baseline CPU performance with the ability to burst. With "unlimited" mode, the instance can burst above baseline for as long as needed (paying for surplus credits). Since the workload has low average utilization with brief periodic spikes, T3 with unlimited mode is ideal. Standard mode risks throttling if CPU credits are exhausted. M5/C5 would be more expensive for a workload averaging 5% CPU.

---

### Question 29
A company is using Amazon EC2 On-Demand Instances for a production workload that runs 24/7 and is expected to run for the next 3 years. The workload has steady-state resource requirements.

Which purchasing option would provide the GREATEST cost savings?

- A. 1-year Standard Reserved Instance with All Upfront payment
- B. 3-year Standard Reserved Instance with All Upfront payment
- C. 3-year Convertible Reserved Instance with All Upfront payment
- D. Compute Savings Plan with 3-year commitment

**Correct Answer: B**

**Explanation:** A 3-year Standard Reserved Instance with All Upfront payment provides the maximum discount (up to 72% compared to On-Demand). The longer term and full upfront payment maximize savings. If the workload is steady-state and guaranteed for 3 years, this is ideal. Convertible RIs cost more but offer flexibility to change instance types. Savings Plans are slightly more flexible but may not provide the absolute maximum savings for a specific instance.

---

### Question 30
A company needs to share an Amazon Machine Image (AMI) that is stored in Region us-east-1 with a development team in Region eu-west-1.

What should the Solutions Architect do?

- A. Share the AMI directly — AMIs are global resources
- B. Copy the AMI to eu-west-1, then share with the development team
- C. Create a new AMI in eu-west-1 from a snapshot copied from us-east-1
- D. Export the AMI and import it in eu-west-1

**Correct Answer: B**

**Explanation:** AMIs are regional resources. To use an AMI in a different Region, you must copy it to that Region first. After copying, you can share it with other accounts or use it directly. AMIs cannot be shared cross-Region without copying.

---

## Quick Reference: EC2 Instance Types

| Family | Optimized For | Use Case |
|--------|--------------|----------|
| M | General Purpose | Web servers, small databases |
| C | Compute | Batch processing, ML inference, gaming |
| R | Memory | In-memory databases, real-time analytics |
| P/G | GPU/Accelerated | ML training, video encoding, HPC |
| T | Burstable | Dev/test, small workloads |
| I | Storage | NoSQL databases, data warehousing |
| D | Dense Storage | Distributed file systems, data lakes |

## Quick Reference: EC2 Purchasing Options

| Option | Best For | Savings |
|--------|----------|---------|
| On-Demand | Short-term, unpredictable workloads | None (baseline) |
| Reserved (Standard) | Steady-state, predictable workloads | Up to 72% |
| Reserved (Convertible) | Steady-state with flexibility needs | Up to 66% |
| Spot | Fault-tolerant, flexible workloads | Up to 90% |
| Dedicated Hosts | Licensing, compliance requirements | Varies |
| Savings Plans | Flexible compute commitment | Up to 72% |

---

## Global Web Sourced Questions - SAA-C03

### Q-Global-1. Optimizing Cost for Fault-Tolerant Batch Processing
**Question:** A company runs a nightly batch processing job on Amazon EC2 instances. The job is highly fault-tolerant, stateless, and can be interrupted and resumed without any issues. The job takes approximately 4 hours to complete each night. The company mandates that the cost of this workload must be minimized as much as possible. Which EC2 pricing option should a Solutions Architect choose?
- A. EC2 On-Demand Instances
- B. EC2 Dedicated Hosts
- C. EC2 Reserved Instances
- D. EC2 Spot Instances

**Correct Answer: D**

**Explanation:** Spot Instances allow you to request spare Amazon EC2 computing capacity for up to 90% off the On-Demand price. Since the batch processing job is fault-tolerant and stateless, it can handle interruptions if AWS reclaims the Spot Instances. This makes it the most cost-effective solution for this specific workload.

### Q-Global-2. Enabling High-Performance Computing
**Question:** A research team needs to deploy an application on AWS that requires high levels of inter-node communication for tightly coupled, high-performance computing (HPC) workloads. Which architectural decision should a Solutions Architect make to achieve the lowest possible network latency and highest packet per second performance?
- A. Deploy EC2 instances in a Spread Placement Group.
- B. Deploy EC2 instances in a Cluster Placement Group.
- C. Deploy EC2 instances across multiple Availability Zones.
- D. Deploy EC2 instances attached to an Auto Scaling group with a Network Load Balancer.

**Correct Answer: B**

**Explanation:** A Cluster Placement Group packs instances close together inside an Availability Zone. This strategy enables workloads to achieve the low latency network performance necessary for tightly coupled node-to-node communication that is typical of HPC applications.
