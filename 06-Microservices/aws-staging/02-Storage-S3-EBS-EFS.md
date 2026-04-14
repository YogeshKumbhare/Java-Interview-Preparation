# AWS SAA Exam - Storage Services (S3, EBS, EFS, FSx)

> **Domain Coverage:** Design High-Performing Architectures, Design Cost-Optimized Architectures, Design Resilient Architectures
> **Services:** S3, S3 Glacier, EBS, EFS, FSx, Storage Gateway, Snow Family, AWS Transfer Family

---

## Questions & Answers

### Question 1
A company stores critical application data in Amazon S3. The data must be protected against accidental deletion by any user, including the root account.

Which S3 feature should the Solutions Architect enable?

- A. S3 Versioning
- B. S3 Object Lock with Governance Mode
- C. S3 Object Lock with Compliance Mode
- D. S3 Cross-Region Replication

**Correct Answer: C**

**Explanation:** S3 Object Lock in Compliance Mode provides the highest level of protection. Once set, the retention period cannot be shortened and the mode cannot be changed by anyone, including the root user. Governance Mode allows users with special permissions to delete objects. Versioning alone doesn't prevent deletion of versions. MFA Delete can add protection but doesn't fully protect against the root account.

---

### Question 2
A company has a data lake on Amazon S3. The data is accessed frequently for the first 30 days, then rarely accessed for the next 60 days, and after 90 days it must be archived for compliance for 7 years.

Which lifecycle configuration is MOST cost-effective?

- A. S3 Standard → S3 Standard-IA after 30 days → S3 Glacier Deep Archive after 90 days
- B. S3 Standard → S3 One Zone-IA after 30 days → S3 Glacier after 90 days
- C. S3 Standard → S3 Intelligent-Tiering
- D. Keep all data in S3 Standard

**Correct Answer: A**

**Explanation:** S3 Standard for frequent access (first 30 days), S3 Standard-IA for infrequent access (30-90 days) at lower cost, and S3 Glacier Deep Archive for long-term archival (cheapest archival option, ideal for 7+ year retention). One Zone-IA is cheaper but less resilient (single AZ). Glacier Deep Archive costs ~$1/TB/month vs Glacier at ~$4/TB/month for data that doesn't need fast retrieval.

---

### Question 3
A customer has a legacy application with a large amount of data. The files accessed by the application are approximately 10 GB each, but are rarely accessed. However, when files are accessed, they are retrieved sequentially. The customer is migrating to AWS and would like to use Amazon EC2 and Amazon EBS.

What is the LEAST expensive EBS volume type for this use case?

- A. Cold HDD (sc1)
- B. Provisioned IOPS SSD (io1)
- C. General Purpose SSD (gp2)
- D. Throughput Optimized HDD (st1)

**Correct Answer: A**

**Explanation:** Cold HDD (sc1) is the least expensive EBS volume type and is ideal for infrequent, sequential access patterns. It provides the lowest cost per GB. Throughput Optimized HDD (st1) is for frequently accessed, throughput-intensive workloads. SSD volumes (gp2, io1) are more expensive and designed for random I/O patterns.

---

### Question 4
A company needs to store files that are accessed by multiple EC2 instances simultaneously across multiple Availability Zones. The files must be accessible via standard file system protocols.

Which storage service should the Solutions Architect use?

- A. Amazon EBS Multi-Attach
- B. Amazon EFS
- C. Amazon S3
- D. Amazon FSx for Windows File Server

**Correct Answer: B**

**Explanation:** Amazon EFS provides a scalable, fully managed NFS file system that can be mounted simultaneously by thousands of EC2 instances across multiple AZs. EBS Multi-Attach is limited to io1/io2 volumes in a single AZ and supports up to 16 instances. S3 is object storage, not a file system. FSx for Windows uses SMB protocol, not standard NFS.

---

### Question 5
A company is archiving compliance data that must be retained for 10 years. The data will never be accessed unless there is an audit, in which case the data must be retrievable within 12 hours.

Which storage solution is MOST cost-effective?

- A. Amazon S3 Standard-IA
- B. Amazon S3 Glacier
- C. Amazon S3 Glacier Deep Archive
- D. Amazon EBS Cold HDD (sc1)

**Correct Answer: C**

**Explanation:** S3 Glacier Deep Archive is the cheapest storage class (~$0.00099/GB/month) and supports retrieval within 12 hours (Standard retrieval takes up to 12 hours). This matches the requirement perfectly. Regular Glacier is more expensive. S3 Standard-IA is too expensive for data that's almost never accessed. EBS is not designed for long-term archival.

---

### Question 6
A company's application generates log files that are written once and read frequently for the first week. After that, the logs are rarely read but must be kept for 5 years. The company wants to minimize costs while allowing quick access to recent logs.

Which S3 storage strategy should the Solutions Architect recommend?

- A. Store all logs in S3 Standard
- B. Use S3 Intelligent-Tiering for all logs
- C. S3 Standard with lifecycle policy to transition to S3 Glacier after 7 days
- D. S3 Standard with lifecycle policy to S3 Standard-IA after 7 days, then S3 Glacier after 30 days

**Correct Answer: D**

**Explanation:** This approach optimizes cost at each stage: S3 Standard for the first week of frequent access, S3 Standard-IA for occasional access (cheaper, minimum 30 days), then S3 Glacier for long-term archival at the lowest cost. Going directly to Glacier after 7 days would require paying for the 30-day minimum storage in IA anyway. Intelligent-Tiering has monitoring fees that may not be cost-effective here.

---

### Question 7
A Solutions Architect needs to design an S3 bucket policy that allows public read access to objects but denies all PUT operations unless the request includes server-side encryption with AWS KMS.

Which policy condition should be used for the encryption requirement?

- A. `"s3:x-amz-server-side-encryption": "aws:kms"`
- B. `"s3:x-amz-server-side-encryption": "AES256"`
- C. `Condition: {"StringNotEquals": {"s3:x-amz-server-side-encryption": "aws:kms"}}`
- D. `Condition: {"Null": {"s3:x-amz-server-side-encryption": "true"}}`

**Correct Answer: C**

**Explanation:** Using a Deny policy with `StringNotEquals` condition for `s3:x-amz-server-side-encryption: aws:kms` will deny any PUT request that doesn't include KMS encryption. This is the standard pattern to enforce encryption. You can also combine with a `Null` condition to deny requests that don't include the header at all.

---

### Question 8
A company wants to replicate S3 objects from a bucket in us-east-1 to a bucket in eu-west-1 for disaster recovery. Only objects uploaded after enabling replication should be copied. Existing objects should not be replicated.

Which feature should the Solutions Architect configure?

- A. S3 Cross-Region Replication (CRR)
- B. S3 Same-Region Replication (SRR)
- C. S3 Batch Replication
- D. AWS DataSync

**Correct Answer: A**

**Explanation:** S3 Cross-Region Replication (CRR) automatically replicates new objects (uploaded after enabling) from a source bucket to a destination bucket in a different Region. By default, CRR only replicates new objects — not existing ones. Versioning must be enabled on both buckets. S3 Batch Replication would be needed to replicate existing objects.

---

### Question 9
A company has an on-premises NFS file server with 50 TB of data. They want to migrate to AWS while maintaining NFS access for on-premises users during the migration. The migration must be completed within 2 weeks.

Which service should the Solutions Architect use?

- A. AWS Snowball Edge
- B. AWS DataSync with VPN/Direct Connect
- C. AWS Storage Gateway - File Gateway
- D. AWS Transfer Family

**Correct Answer: B**

**Explanation:** AWS DataSync can transfer data over the network at up to 10 Gbps through a VPN or Direct Connect. It supports NFS as a source location. For 50 TB with a reasonable connection, this can complete within 2 weeks. Storage Gateway provides ongoing hybrid access but isn't optimized for bulk migration. Snowball could work but involves shipping time overhead. Transfer Family is for SFTP/FTPS/FTP, not NFS.

---

### Question 10
An application running on Amazon EC2 needs to access an S3 bucket. The company's security policy requires that the data never traverse the public internet.

Which solution should the Solutions Architect implement?

- A. S3 bucket policy restricting to the VPC's IP range
- B. S3 Gateway Endpoint
- C. NAT Gateway with S3 access
- D. AWS PrivateLink for S3

**Correct Answer: B**

**Explanation:** An S3 Gateway Endpoint provides private connectivity from a VPC to S3 without traversing the internet. Traffic stays within the AWS network. Gateway Endpoints are free for S3 and DynamoDB. NAT Gateway routes through the internet. PrivateLink (Interface Endpoint) also works for S3 but has associated costs and is typically used for more complex access patterns.

---

### Question 11
A company needs to serve static content (images, CSS, JavaScript) for a global web application with low latency.

Which architecture provides the BEST performance?

- A. S3 bucket in a single Region with Transfer Acceleration
- B. S3 bucket with CloudFront distribution
- C. EC2 instances in each Region serving static content
- D. S3 buckets in each Region with Route 53 latency-based routing

**Correct Answer: B**

**Explanation:** CloudFront is a CDN that caches content at edge locations worldwide, providing low-latency access to static content. S3 serves as the origin, and CloudFront distributes the content globally. Transfer Acceleration speeds uploads to S3 but doesn't cache at edge locations. EC2 in each Region is expensive and complex. Multiple S3 buckets require managing replication.

---

### Question 12
A company has 100 TB of data stored on-premises. They need to transfer this data to Amazon S3. Their internet connection is 100 Mbps.

Which migration method should they use to complete the transfer in the SHORTEST time?

- A. AWS Direct Connect
- B. AWS Snowball Edge devices
- C. S3 Transfer Acceleration over the internet
- D. AWS DataSync over VPN

**Correct Answer: B**

**Explanation:** At 100 Mbps, transferring 100 TB would take approximately 92 days. AWS Snowball Edge devices (each holding 80 TB) can be shipped and returned within 1-2 weeks. Using 2 Snowball Edge devices in parallel would complete the transfer much faster than any network-based method. Direct Connect takes weeks to provision. DataSync and Transfer Acceleration are limited by the 100 Mbps bandwidth.

---

### Question 13
A company requires that all objects uploaded to their S3 bucket are encrypted using SSE-KMS with a specific customer-managed CMK. If an object is uploaded without the correct encryption, the upload should be denied.

How should the Solutions Architect enforce this?

- A. Enable default encryption on the S3 bucket with the CMK
- B. Create a bucket policy that denies PutObject without the correct encryption header
- C. Use S3 Object Lock
- D. Both A and B

**Correct Answer: D**

**Explanation:** Enabling default encryption ensures objects uploaded without an encryption header are automatically encrypted with the specified CMK. However, to prevent uploads using a different encryption method (e.g., SSE-S3), you also need a bucket policy that explicitly denies PutObject requests that don't specify the correct CMK. Both together provide complete enforcement.

---

### Question 14
A company runs a Windows-based application that requires SMB protocol access to a shared file system. The file system needs to be highly available across multiple AZs.

Which AWS service should the Solutions Architect recommend?

- A. Amazon EFS
- B. Amazon FSx for Windows File Server (Multi-AZ)
- C. Amazon FSx for Lustre
- D. Amazon EBS with Windows file sharing

**Correct Answer: B**

**Explanation:** Amazon FSx for Windows File Server provides a fully managed Windows file system with native SMB protocol support, Active Directory integration, and Multi-AZ deployment for high availability. EFS uses NFS protocol (Linux). FSx for Lustre is for high-performance computing (Linux). EBS doesn't support multi-instance access easily.

---

### Question 15
A company uses S3 to store application data. The company discovers that occasionally older versions of objects need to be restored. The IT team wants to protect against accidental deletion while minimizing storage costs.

Which combination of features should be enabled?

- A. S3 Versioning + S3 Lifecycle Policies to expire old versions after 90 days
- B. S3 Versioning + MFA Delete
- C. S3 Object Lock + S3 Versioning
- D. S3 Cross-Region Replication

**Correct Answer: A**

**Explanation:** Versioning preserves, retrieves, and restores every version of every object. Combined with lifecycle policies to expire old versions after 90 days, this provides protection against accidental deletion while controlling costs. MFA Delete adds extra protection but doesn't minimize costs. Object Lock may be too restrictive. CRR helps with DR but is more expensive.

---

### Question 16
A company is running a media processing workflow. Large video files (up to 100 GB) are uploaded by users and stored in S3 before processing. Users complain about slow upload times.

Which feature should the Solutions Architect enable to improve upload performance?

- A. S3 Transfer Acceleration
- B. S3 Multipart Upload
- C. CloudFront with S3 origin
- D. Both A and B

**Correct Answer: D**

**Explanation:** S3 Transfer Acceleration routes uploads through CloudFront edge locations for faster transfers over long distances. Multipart Upload enables parallel upload of parts for large files (required for files >5 GB, recommended for >100 MB), improving throughput and allowing retry of individual parts. Together, they maximize upload performance.

---

### Question 17
A company has enabled S3 Versioning on a bucket. A developer accidentally deletes an important file. The file no longer appears in the S3 console.

How can the file be recovered?

- A. Contact AWS Support to restore the file
- B. Delete the delete marker on the object
- C. Restore from S3 Glacier
- D. The file is permanently lost

**Correct Answer: B**

**Explanation:** When versioning is enabled and an object is "deleted," S3 adds a delete marker (a special version). The previous versions still exist. To recover the object, simply delete the delete marker, which makes the most recent version visible again. The underlying object versions are not deleted.

---

### Question 18
A company needs a highly durable storage solution for storing database backups. The backups range from 1 GB to 5 TB in size. The backups must be available for immediate retrieval for 30 days, then archived for 7 years.

Which solution meets the requirements at the LOWEST cost?

- A. EBS snapshots with lifecycle policy
- B. S3 Standard with lifecycle to S3 Glacier Deep Archive after 30 days
- C. S3 Standard-IA with lifecycle to S3 Glacier after 30 days
- D. Amazon FSx for backup storage

**Correct Answer: B**

**Explanation:** S3 Standard provides 99.999999999% (11 nines) durability and immediate access for the first 30 days. After 30 days, lifecycle transitions to Glacier Deep Archive (~$1/TB/month) for the cheapest long-term archival. S3 Standard-IA has a 30-day minimum storage requirement, making it unnecessary for the first stage since Standard provides what's needed. Glacier Deep Archive is the cheapest archival tier.

---

### Question 19
A company uses Amazon EBS volumes for its EC2 instances. The company needs to create point-in-time backups of the volumes and retain them for disaster recovery in another Region.

What should the Solutions Architect do?

- A. Create EBS snapshots and copy them to another Region
- B. Use EBS Multi-Attach to replicate the volume
- C. Use AWS Backup with cross-Region copy
- D. Both A and C

**Correct Answer: D**

**Explanation:** Both approaches work: EBS snapshots can be manually copied to another Region for DR. AWS Backup provides an automated, policy-based approach to create and manage backups with cross-Region copy rules. AWS Backup is the recommended approach for its automation and lifecycle management capabilities.

---

### Question 20
A file processing application uses Amazon EFS. The application reads files once when they are uploaded, then rarely accesses them. Over 80% of the data in EFS is infrequently accessed.

How can the Solutions Architect reduce storage costs?

- A. Migrate data to Amazon S3
- B. Enable EFS Lifecycle Management with Infrequent Access (IA) storage class
- C. Use a smaller EFS file system
- D. Move to Amazon EBS

**Correct Answer: B**

**Explanation:** EFS Lifecycle Management automatically moves files to the EFS Infrequent Access (IA) storage class based on access patterns. EFS IA costs up to 92% less than EFS Standard. Files are automatically moved back to Standard on the next access. This provides transparent cost savings without changing the application.

---

### Question 21
An organization runs an online media site. An employee posted a product review that contained videos and pictures. The review went viral and the organization needs to handle the resulting spike in website traffic.

What action would provide an immediate solution?

- A. Redesign the website to use Amazon API Gateway, and use AWS Lambda to deliver content
- B. Add server instances using Amazon EC2 and use Amazon Route 53 with a failover routing policy
- C. Serve the images and videos via an Amazon CloudFront distribution created using the news site as the origin
- D. Use Amazon ElastiCache for Redis for caching and reducing the load requests from the origin

**Correct Answer: C**

**Explanation:** CloudFront provides an immediate solution by caching and distributing the viral content at edge locations worldwide. It can handle massive traffic spikes without modifications to the origin. Setting up a CloudFront distribution is quick and immediately offloads traffic. Options A, B would take longer to implement. ElastiCache helps with database caching, not serving static media content.

---

### Question 22
A company has a hybrid environment with an on-premises data center and AWS. They need to provide their on-premises applications with low-latency access to a subset of frequently used data stored in S3, while maintaining all data in S3.

Which solution should the Solutions Architect use?

- A. AWS Storage Gateway - File Gateway
- B. AWS DataSync
- C. AWS Direct Connect
- D. S3 Cross-Region Replication

**Correct Answer: A**

**Explanation:** AWS Storage Gateway File Gateway provides on-premises applications with NFS/SMB access to data stored in S3. It caches frequently used data locally for low-latency access while storing all data durably in S3. DataSync is for one-time or scheduled data transfers. Direct Connect provides network connectivity but doesn't cache data. CRR is for replication between S3 buckets.

---

### Question 23
A company needs to store 500 TB of genomics data. The data will be analyzed using high-performance computing (HPC) workloads that require sub-millisecond latency and high throughput.

Which storage solution should the Solutions Architect recommend?

- A. Amazon EFS
- B. Amazon FSx for Lustre linked to S3
- C. Amazon S3 with Transfer Acceleration
- D. Amazon EBS Provisioned IOPS (io2)

**Correct Answer: B**

**Explanation:** Amazon FSx for Lustre is a high-performance file system designed for HPC workloads. It provides sub-millisecond latency, up to hundreds of GB/s throughput, and millions of IOPS. It can be linked to S3 to transparently access and process S3 data. EFS doesn't provide the same level of performance. EBS is limited to single instances. S3 alone doesn't provide file system semantics.

---

### Question 24
A company is running a database on an EC2 instance. The database requires 64,000 IOPS for optimal performance.

Which EBS volume type should the Solutions Architect choose?

- A. General Purpose SSD (gp3)
- B. Provisioned IOPS SSD (io2)
- C. Provisioned IOPS SSD (io1)
- D. Throughput Optimized HDD (st1)

**Correct Answer: B**

**Explanation:** io2 volumes support up to 64,000 IOPS, making them ideal for I/O-intensive databases. io2 also provides 99.999% durability (100x more than gp2/gp3/io1). gp3 supports up to 16,000 IOPS. io1 supports 64,000 IOPS too but io2 provides better durability at the same price. HDD volumes don't support high IOPS.

---

### Question 25
A company wants to transition 10 PB of cold data from an on-premises data center to Amazon S3 Glacier. The company has a 1 Gbps internet connection.

Which migration method is MOST practical?

- A. AWS Snowmobile
- B. Multiple AWS Snowball Edge devices
- C. AWS DataSync over Direct Connect
- D. S3 Transfer Acceleration

**Correct Answer: A**

**Explanation:** AWS Snowmobile is designed for exabyte-scale data transfers and can carry up to 100 PB per Snowmobile. For 10 PB of data, Snowmobile is the most practical option. At 1 Gbps, network transfer would take approximately 926 days. Multiple Snowball Edge devices (80 TB each) would require 125+ devices, which is possible but logistically complex. Snowmobile handles this scale more efficiently.

---

## Quick Reference: S3 Storage Classes

| Storage Class | Durability | Availability | Min Duration | Retrieval | Cost (per GB/month) |
|---------------|-----------|-------------|-------------|-----------|-------------------|
| Standard | 99.999999999% | 99.99% | None | Immediate | ~$0.023 |
| Standard-IA | 99.999999999% | 99.9% | 30 days | Immediate | ~$0.0125 |
| One Zone-IA | 99.999999999% | 99.5% | 30 days | Immediate | ~$0.01 |
| Intelligent-Tiering | 99.999999999% | 99.9% | None | Immediate | ~$0.023-$0.0025 |
| Glacier Instant | 99.999999999% | 99.9% | 90 days | Milliseconds | ~$0.004 |
| Glacier Flexible | 99.999999999% | 99.99% | 90 days | 1-12 hours | ~$0.0036 |
| Glacier Deep Archive | 99.999999999% | 99.99% | 180 days | 12-48 hours | ~$0.00099 |

## Quick Reference: EBS Volume Types

| Type | Use Case | Max IOPS | Max Throughput |
|------|----------|----------|---------------|
| gp3 | General purpose | 16,000 | 1,000 MB/s |
| gp2 | General purpose | 16,000 | 250 MB/s |
| io2 | Critical databases | 64,000 | 1,000 MB/s |
| io2 Block Express | Largest databases | 256,000 | 4,000 MB/s |
| st1 | Big data, logs | 500 | 500 MB/s |
| sc1 | Cold archives | 250 | 250 MB/s |

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
