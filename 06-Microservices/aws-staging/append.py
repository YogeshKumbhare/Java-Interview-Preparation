import os

s3_file = r"C:\My Data\Yogesh AWS ExamPreparation\Topic-Wise-Questions\02-Storage-S3-EBS-EFS.md"
net_file = r"C:\My Data\Yogesh AWS ExamPreparation\Topic-Wise-Questions\04-Networking-VPC-Route53-CloudFront.md"

with open(s3_file, 'a', encoding='utf-8') as f:
    f.write("""
---

## Global Web Sourced Questions - SAA-C03

### Q-Global-1. Ensuring Data Durability Across Regions Cost-Effectively
**Question:** A company stores its application backup data in an Amazon S3 Standard bucket in the us-east-1 region. Due to a new compliance requirement, the company must ensure these backups are also stored in the eu-west-1 region. The backups are rarely accessed but must be retrieved within 12 hours if needed for an audit. What is the MOST cost-effective way to meet these requirements?
- A. Enable AWS Backup to automatically copy the backups to an S3 Standard bucket in eu-west-1.
- B. Enable S3 Cross-Region Replication (CRR) to copy the backups to an S3 Glacier Flexible Retrieval bucket in eu-west-1.
- C. Create a Lambda function to copy the objects to an S3 One Zone-IA bucket in eu-west-1.
- D. Enable S3 Cross-Region Replication (CRR) to copy the backups to an S3 Standard-IA bucket in eu-west-1 and set a lifecycle policy to move them to Glacier Deep Archive.

**Correct Answer: B**

**Explanation:** S3 Cross-Region Replication allows automatic asynchronous copying of objects across buckets in different regions. Since the data in EU is rarely accessed and a retrieval time of 12 hours is acceptable, S3 Glacier Flexible Retrieval is highly cost-effective and meets the retrieval constraint (Standard retrievals take 3-5 hours, Bulk takes 5-12 hours).

### Q-Global-2. Migrating File Data for Legacy Applications
**Question:** An enterprise is migrating its on-premises infrastructure to AWS. It has numerous legacy Linux applications that require shared access to a centralized file system. These applications cannot be rewritten to use object storage APIs. Which AWS service should a Solutions Architect recommend?
- A. Amazon S3 mapped via Storage Gateway
- B. Amazon Elastic Block Store (EBS) Multi-Attach
- C. Amazon Elastic File System (EFS)
- D. Amazon FSx for Windows File Server

**Correct Answer: C**

**Explanation:** Amazon EFS provides simple, scalable, fully managed elastic NFS file storage for use with AWS Cloud services and on-premises resources. It is built to scale on demand to petabytes without disrupting applications, growing and shrinking automatically. It natively supports Linux applications requiring a standard file system interface.
""")

with open(net_file, 'a', encoding='utf-8') as f:
    f.write("""
---

## Global Web Sourced Questions - SAA-C03

### Q-Global-1. Blocking Malicious IP Addresses
**Question:** A company's web application deployed in a VPC is facing an ongoing DDoS attack from a known set of malicious IP addresses. A Solutions Architect needs to quickly block traffic from these specific IPs at the subnet level. Which action should be taken?
- A. Update the Security Groups associated with the web tier instances to deny the malicious IPs.
- B. Update the Network Access Control List (Network ACL) associated with the public subnet to deny the malicious IPs.
- C. Use AWS Shield Advanced to automatically block the specified IP addresses.
- D. Modify the Route table of the VPC to route the malicious IPs to a blackhole.

**Correct Answer: B**

**Explanation:** Network ACLs operate at the subnet level and support explicit DENY rules, making them the correct tool to quickly block malicious IP ranges from reaching any instances in the subnet. Security groups only support ALLOW rules, so they cannot be used to explicitly deny traffic.

### Q-Global-2. Improving Global Application Availability and Performance
**Question:** A company has a globally distributed user base that interacts with an API hosted on AWS in a single region. Users in locations geographically distant from the AWS region are reporting high latency. Which service should a Solutions Architect use to improve the global performance and availability of the API?
- A. Amazon CloudFront
- B. AWS Global Accelerator
- C. Amazon Route 53 with latency-based routing
- D. Application Load Balancer with Cross-Zone Load Balancing

**Correct Answer: B**

**Explanation:** AWS Global Accelerator uses the robust Amazon global network to route traffic to the optimal endpoint, bypassing public internet congestion. It provides static IP addresses that act as a fixed entry point to your application globally, reducing latency and dramatically improving performance for users across the world.
""")
