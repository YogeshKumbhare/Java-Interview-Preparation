# AWS SAA Exam - Migration & Transfer Services

> **Domain Coverage:** All Domains
> **Services:** AWS Migration Hub, Server Migration Service, Database Migration Service, DataSync, Transfer Family, Snow Family, Application Discovery Service, CloudEndure, MGN

---

## Questions & Answers

### Question 1
A company has 500 on-premises servers running various workloads. They want to plan a large-scale migration to AWS and need to discover server dependencies, performance data, and utilization patterns.

Which service should the Solutions Architect use for the discovery phase?

- A. AWS Migration Hub
- B. AWS Application Discovery Service
- C. AWS Server Migration Service
- D. AWS CloudFormation

**Correct Answer: B**

**Explanation:** AWS Application Discovery Service helps plan migration by collecting information about on-premises data centers. It discovers server configuration, usage data, and dependency mapping. The agentless discovery (via VMware vCenter connector) or agent-based discovery provides data needed for migration planning. Migration Hub aggregates this data but doesn't perform discovery itself.

---

### Question 2
A company wants to migrate a large Oracle database (10 TB) to Amazon Aurora PostgreSQL. The migration must have minimal downtime.

Which combination of AWS services should the Solutions Architect use?

- A. AWS DMS with CDC (Change Data Capture) + AWS SCT (Schema Conversion Tool)
- B. AWS DataSync
- C. AWS Snowball Edge
- D. pgloader

**Correct Answer: A**

**Explanation:** For heterogeneous database migration (Oracle → PostgreSQL): AWS SCT converts the schema from Oracle to PostgreSQL. AWS DMS performs the initial full data load and then uses CDC for continuous replication during the migration period, enabling near-zero downtime cutover. DataSync is for file-based transfers. Snowball is for bulk data movement to S3.

---

### Question 3
A company has 200 TB of data on-premises. Their internet connection is 1 Gbps. They need to migrate all data to S3 within 2 weeks.

Which migration method should the Solutions Architect recommend?

- A. Direct internet transfer to S3
- B. AWS Snowball Edge devices (multiple)
- C. AWS Direct Connect
- D. AWS DataSync

**Correct Answer: B**

**Explanation:** At 1 Gbps, transferring 200 TB would take approximately 18.5 days (exceeding the 2-week deadline). Each Snowball Edge device holds 80 TB. Using 3 devices in parallel, the data can be loaded and shipped within the 2-week window. Direct Connect takes weeks to provision. DataSync over 1 Gbps cannot meet the deadline.

---

### Question 4
A company is performing a "lift and shift" migration of virtual machines from VMware to AWS. They want an automated, agent-based solution that provides continuous replication and testing before cutover.

Which service should the Solutions Architect use?

- A. AWS Server Migration Service (SMS)
- B. AWS Application Migration Service (MGN)
- C. AWS DataSync
- D. AWS CloudEndure Migration

**Correct Answer: B**

**Explanation:** AWS Application Migration Service (MGN) is the primary recommended service for lift-and-shift migrations. It provides continuous block-level replication, non-disruptive testing, and automated cutover. MGN replaced CloudEndure Migration and AWS SMS for most rehost migration scenarios. It supports physical, virtual, and cloud servers.

---

### Question 5
A company has an on-premises MySQL database that needs to be migrated to Amazon RDS MySQL. The database is 500 GB, and the company can accept a 4-hour maintenance window.

Which is the SIMPLEST migration approach?

- A. AWS DMS full load migration during the maintenance window
- B. mysqldump and restore to RDS
- C. AWS DMS with CDC for continuous replication
- D. AWS Snowball with manual database restore

**Correct Answer: A**

**Explanation:** For a same-engine migration (MySQL → MySQL) with an acceptable maintenance window, AWS DMS full load is the simplest approach. It handles the complete data migration in one operation. mysqldump also works but DMS is fully managed and handles edge cases better. CDC isn't needed since a maintenance window is acceptable. Snowball is for S3, not direct database migration.

---

### Question 6
A company transfers files daily from on-premises to S3 using SFTP. They want to maintain the same workflow while migrating their SFTP server to AWS.

Which service should the Solutions Architect use?

- A. Amazon S3 with direct upload
- B. AWS Transfer Family (SFTP endpoint)
- C. AWS DataSync
- D. Amazon FSx

**Correct Answer: B**

**Explanation:** AWS Transfer Family provides fully managed SFTP, FTPS, and FTP endpoints for transferring files into and out of Amazon S3 or EFS. Existing SFTP clients and workflows continue to work without changes. DataSync is for scheduled/one-time bulk transfers. Direct S3 upload requires application changes. FSx is a file system, not a transfer service.

---

### Question 7
A company needs to continuously synchronize an on-premises NFS file share with Amazon S3. Changes must be synced every hour.

Which service should the Solutions Architect use?

- A. AWS Storage Gateway File Gateway
- B. AWS DataSync with scheduled tasks
- C. S3 Cross-Region Replication
- D. AWS Transfer Family

**Correct Answer: B**

**Explanation:** AWS DataSync supports scheduled tasks that can run at regular intervals (every hour). It efficiently transfers only changed data (incremental sync), supports NFS as a source, and delivers to S3. Storage Gateway provides continuous cache-based access but isn't designed for scheduled sync. S3 CRR replicates between S3 buckets, not on-premises. Transfer Family is for SFTP workflows.

---

### Question 8
A company has identified 6 migration strategies (the "6 R's"). For an application that will be re-deployed on AWS using cloud-native features, which migration strategy applies?

- A. Rehost (Lift and Shift)
- B. Replatform (Lift, Tinker, and Shift)
- C. Refactor/Re-architect
- D. Retire

**Correct Answer: C**

**Explanation:** Refactor/Re-architect involves redesigning the application to take advantage of cloud-native features (serverless, microservices, etc.). Rehost is moving as-is with no changes. Replatform makes small optimizations (e.g., moving to RDS without schema changes). Retire means decommissioning. Repurchase means moving to a SaaS. Retain means keeping on-premises.

---

### Question 9
A company has an on-premises tape backup system. They want to migrate their tape-based backup workflow to AWS without changing their existing backup application.

Which service should the Solutions Architect use?

- A. AWS Storage Gateway - File Gateway
- B. AWS Storage Gateway - Volume Gateway
- C. AWS Storage Gateway - Tape Gateway
- D. AWS Backup

**Correct Answer: C**

**Explanation:** Storage Gateway Tape Gateway presents virtual tape library (VTL) interfaces to existing backup applications. The backup application sees virtual tapes and uses them just like physical tapes. Data is stored in S3 and S3 Glacier. No changes needed to the backup workflow. File Gateway is for NFS/SMB file access. Volume Gateway provides iSCSI block storage. AWS Backup is cloud-native.

---

### Question 10
A company is migrating a multi-tier application from on-premises to AWS. They want to migrate in phases, starting with the database, then the application tier, and finally the web tier.

Which service helps coordinate and track the progress of this multi-phase migration?

- A. AWS CloudFormation
- B. AWS Migration Hub
- C. AWS Systems Manager
- D. AWS Service Catalog

**Correct Answer: B**

**Explanation:** AWS Migration Hub provides a single place to discover, assess, and track the status of application migrations to AWS. It integrates with AWS migration tools (MGN, DMS, SMS) and partner tools to provide a unified view of migration progress across multiple applications and phases. CloudFormation deploys infrastructure. Systems Manager manages resources. Service Catalog manages approved products.

---

### Question 11
A company wants to migrate a PostgreSQL database from RDS in one Region to RDS in another Region with minimal downtime.

Which approach should the Solutions Architect use?

- A. Create a cross-Region Read Replica and promote it
- B. Take a snapshot, copy to the other Region, and restore
- C. Use AWS DMS with CDC
- D. Both A and C work; A is simpler

**Correct Answer: D**

**Explanation:** Cross-Region Read Replica replication is continuous and asynchronous. When ready, promote the replica to become the primary in the new Region (minimal downtime during promotion). DMS with CDC also works by continuously replicating changes. The Read Replica approach is simpler for same-engine migrations within RDS.

---

### Question 12
A company needs to transfer 1 PB of data from their data center to AWS S3 Glacier. Their internet connection is 10 Gbps.

Which migration service should the Solutions Architect use?

- A. AWS Snowball Edge (multiple devices)
- B. AWS Snowmobile
- C. AWS DataSync over Direct Connect
- D. S3 Transfer Acceleration

**Correct Answer: B**

**Explanation:** For 1 PB (1,000 TB) of data, AWS Snowmobile is the most practical option. It's an exabyte-scale data transfer service using a 45-foot shipping container that holds up to 100 PB. Using Snowball Edge would require 13+ devices. At 10 Gbps, network transfer would take ~92 days. Snowmobile can complete the job faster for this scale.

---

### Question 13
A company has migrated their application to AWS but some users still access the on-premises endpoint. The company wants to gradually shift traffic from on-premises to AWS.

Which Route 53 routing policy should the Solutions Architect use?

- A. Failover routing
- B. Weighted routing
- C. Latency-based routing
- D. Simple routing

**Correct Answer: B**

**Explanation:** Weighted routing allows gradual traffic shifting by assigning weights to different endpoints. Start with 90% to on-premises, 10% to AWS, and gradually increase the AWS weight. This provides a controlled, phased migration with the ability to roll back. Failover is for DR. Latency-based routes to the faster endpoint (not controllable). Simple routing returns a single value.

---

### Question 14
A company is using AWS DMS to migrate a database. During migration, they notice that some tables with LOB (Large Object) columns are being migrated very slowly.

What should the Solutions Architect do to improve LOB migration performance?

- A. Increase the DMS replication instance size
- B. Use "Limited LOB mode" with an appropriate max LOB size
- C. Split the migration into multiple tasks
- D. Both A and B

**Correct Answer: D**

**Explanation:** LOB columns significantly impact DMS performance. Limited LOB mode processes LOBs inline (up to the specified max size) rather than performing separate lookups for each LOB, dramatically improving performance. Increasing the replication instance size provides more memory and CPU for handling large data. Together, these optimizations improve LOB migration speed.

---

### Question 15
A company needs to migrate Windows file servers to AWS while maintaining SMB protocol access and Active Directory integration.

Which service should the Solutions Architect use as the target?

- A. Amazon EFS
- B. Amazon FSx for Windows File Server
- C. Amazon S3 with Storage Gateway
- D. Amazon FSx for Lustre

**Correct Answer: B**

**Explanation:** Amazon FSx for Windows File Server provides fully managed Windows file systems with native SMB support and Active Directory integration. This is the direct replacement for on-premises Windows file servers. EFS uses NFS (Linux). Storage Gateway adds complexity. FSx for Lustre is for HPC (Linux).

---

## Quick Reference: 6 R's of Migration

| Strategy | Description | Example |
|----------|-------------|---------|
| **Rehost** | Lift and shift (no changes) | Move VMs to EC2 using MGN |
| **Replatform** | Lift, tinker, shift (minor optimization) | Move MySQL to RDS |
| **Refactor** | Re-architect for cloud-native | Rewrite as microservices + Lambda |
| **Repurchase** | Move to a different product | On-prem CRM → Salesforce |
| **Retain** | Keep on-premises | Compliance-restricted app |
| **Retire** | Decommission application | Unused legacy system |

## Quick Reference: Migration Service Selection

| Scenario | Service |
|----------|---------|
| VM/Server migration | AWS Application Migration Service (MGN) |
| Database migration (same engine) | AWS DMS |
| Database migration (different engine) | AWS DMS + AWS SCT |
| File transfer (bulk) | AWS DataSync |
| File transfer (SFTP workflow) | AWS Transfer Family |
| Massive data transfer (TB scale) | AWS Snowball Edge |
| Massive data transfer (PB scale) | AWS Snowmobile |
| Tape backup migration | Storage Gateway (Tape Gateway) |
| Migration tracking | AWS Migration Hub |
| Discovery and planning | AWS Application Discovery Service |

## Quick Reference: Snow Family Comparison

| Device | Storage | Compute | Use Case |
|--------|---------|---------|----------|
| Snowcone | 8-14 TB | 2 vCPUs, 4 GB RAM | Edge, small transfers |
| Snowball Edge Storage | 80 TB | 40 vCPUs | Data transfer, edge storage |
| Snowball Edge Compute | 42 TB | 52 vCPUs, GPU option | Edge compute + transfer |
| Snowmobile | 100 PB | N/A | Exabyte-scale DC migration |
