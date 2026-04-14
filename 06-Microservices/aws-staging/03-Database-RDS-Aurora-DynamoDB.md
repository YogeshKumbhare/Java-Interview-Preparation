# AWS SAA Exam - Database Services (RDS, Aurora, DynamoDB, ElastiCache, Redshift)

> **Domain Coverage:** Design High-Performing Architectures, Design Resilient Architectures, Design Cost-Optimized Architectures
> **Services:** RDS, Aurora, DynamoDB, ElastiCache, Redshift, Neptune, DocumentDB, Keyspaces, QLDB

---

## Questions & Answers

### Question 1
A Solutions Architect is creating a new relational database. The compliance team will use the database, and mandates that data content must be stored across three different Availability Zones.

Which of the following options should the Architect use?

- A. Amazon Aurora
- B. Amazon RDS MySQL with Multi-AZ enabled
- C. Amazon DynamoDB
- D. Amazon ElastiCache

**Correct Answer: A**

**Explanation:** Amazon Aurora automatically replicates data across 3 AZs with 6 copies of your data. Aurora's storage is distributed across 3 AZs with 2 copies in each AZ. RDS Multi-AZ maintains a standby replica in one other AZ (2 AZs only). DynamoDB is a NoSQL database, not relational. ElastiCache is an in-memory caching service, not a database for compliance data.

---

### Question 2
A company runs an e-commerce application with a backend database on Amazon RDS MySQL. During peak shopping events, the database experiences heavy read traffic that degrades write performance.

Which solution should the Solutions Architect implement to improve read performance?

- A. Enable Multi-AZ deployment
- B. Create Read Replicas and direct read traffic to them
- C. Increase the RDS instance size
- D. Enable RDS Proxy

**Correct Answer: B**

**Explanation:** Read Replicas offload read traffic from the primary database, improving overall performance. Read traffic is directed to replicas, leaving the primary instance free for write operations. Multi-AZ is for HA/failover, not read scaling. Increasing instance size (vertical scaling) has limits and is more expensive. RDS Proxy improves connection management but doesn't offload reads.

---

### Question 3
A company needs a database for their application that requires single-digit millisecond read latency for millions of requests per second. The data model uses key-value and document patterns. The application needs automatic scaling.

Which database service should the Solutions Architect recommend?

- A. Amazon RDS with Read Replicas
- B. Amazon DynamoDB
- C. Amazon Aurora
- D. Amazon Redshift

**Correct Answer: B**

**Explanation:** DynamoDB is a fully managed NoSQL database that provides single-digit millisecond performance at any scale. It supports key-value and document data models with automatic scaling through on-demand or provisioned capacity modes. RDS and Aurora are relational databases. Redshift is for analytics/data warehousing.

---

### Question 4
A company's application needs a relational database that can handle 5x the throughput of MySQL with automatic failover in under 30 seconds. The database must be compatible with MySQL.

Which service should the Solutions Architect recommend?

- A. Amazon RDS MySQL Multi-AZ
- B. Amazon Aurora MySQL
- C. Amazon RDS MySQL with Read Replicas
- D. Amazon RDS MariaDB

**Correct Answer: B**

**Explanation:** Amazon Aurora provides up to 5x the throughput of standard MySQL. Aurora supports automatic failover with typically less than 30 seconds of downtime. Aurora is MySQL and PostgreSQL compatible. RDS MySQL Multi-AZ provides failover but at standard MySQL performance. RDS Read Replicas provide read scaling but not the same write performance.

---

### Question 5
A company is building a real-time leaderboard for an online gaming application. The leaderboard needs sub-millisecond response times for reading sorted data.

Which solution should the Solutions Architect use?

- A. Amazon DynamoDB with Global Secondary Indexes
- B. Amazon ElastiCache for Redis with Sorted Sets
- C. Amazon RDS with indexed queries
- D. Amazon Aurora with read replicas

**Correct Answer: B**

**Explanation:** ElastiCache for Redis provides sub-millisecond response times and natively supports Sorted Sets, which are ideal for leaderboard implementations. Redis can sort members by score automatically. DynamoDB provides single-digit millisecond (not sub-millisecond). RDS and Aurora are too slow for real-time leaderboard requirements.

---

### Question 6
A company is migrating an on-premises Oracle database to AWS. The company wants to reduce licensing costs and minimize changes to the application code.

Which migration approach should the Solutions Architect recommend?

- A. Amazon RDS for Oracle with License Included
- B. Amazon RDS for Oracle with Bring Your Own License (BYOL)
- C. Amazon Aurora PostgreSQL with AWS Schema Conversion Tool (SCT)
- D. Amazon DynamoDB

**Correct Answer: C**

**Explanation:** Migrating to Aurora PostgreSQL eliminates Oracle licensing costs entirely. AWS SCT helps convert the database schema, and AWS DMS helps migrate the data. While application changes may be needed, this provides the best long-term cost reduction. RDS for Oracle still requires Oracle licenses. DynamoDB would require significant application redesign.

---

### Question 7
A company runs an OLTP (Online Transaction Processing) workload on an RDS database. The database is becoming a bottleneck. The company wants to improve database response time for frequently repeated read queries.

Which caching strategy should the Solutions Architect implement?

- A. Amazon DAX
- B. Amazon ElastiCache for Redis with lazy loading
- C. Amazon CloudFront
- D. Host-based caching on EC2

**Correct Answer: B**

**Explanation:** ElastiCache for Redis with lazy loading (cache-aside pattern) caches frequently read query results, reducing load on the RDS database. Lazy loading only caches data that is actually requested, which is efficient. DAX is specifically for DynamoDB, not RDS. CloudFront caches HTTP responses, not database queries. Host-based caching doesn't share cache across instances.

---

### Question 8
A company needs a database that provides ACID transactions, is fully managed, and can handle up to 10x the write throughput of standard MySQL.

Which database should the Solutions Architect recommend?

- A. Amazon DynamoDB with Transactions
- B. Amazon Aurora MySQL
- C. Amazon RDS MySQL
- D. Amazon Redshift

**Correct Answer: B**

**Explanation:** Amazon Aurora MySQL provides ACID compliance, is fully managed, and delivers up to 5x the throughput of standard MySQL (with Aurora optimized reads providing additional performance gains). Note: The question says "10x" which doesn't exactly match Aurora's claimed 5x, but Aurora is still the best answer among the options. DynamoDB supports transactions but is NoSQL. Redshift is for analytics.

---

### Question 9
A company has a DynamoDB table that receives millions of writes per second during peak hours but very few writes during off-peak hours. The company wants to minimize costs while maintaining performance.

Which capacity mode should the Solutions Architect choose?

- A. Provisioned capacity with Auto Scaling
- B. On-demand capacity mode
- C. Provisioned capacity with reserved capacity
- D. Provisioned capacity with manual scaling

**Correct Answer: B**

**Explanation:** DynamoDB On-Demand capacity mode automatically scales to accommodate workload demands. You pay per request, which is ideal for unpredictable or spiky traffic patterns. Provisioned with Auto Scaling could work but may not scale fast enough for sudden spikes. Reserved capacity requires upfront commitment. On-Demand is best for highly variable workloads.

---

### Question 10
A company is designing a social media application. The application needs to store and query complex relationships between users (friends, followers, interests). Queries like "find friends of friends who like XYZ" are common.

Which database service should the Solutions Architect recommend?

- A. Amazon DynamoDB with Global Secondary Indexes
- B. Amazon Aurora MySQL with complex JOINs
- C. Amazon Neptune
- D. Amazon DocumentDB

**Correct Answer: C**

**Explanation:** Amazon Neptune is a fully managed graph database service that is optimized for storing and querying highly connected data. Graph databases excel at traversing relationships (like social networks, recommendation engines). DynamoDB and Aurora can handle relationships but not as efficiently for graph traversal patterns. DocumentDB is for JSON document workloads.

---

### Question 11
A company runs a data warehouse workload that performs complex analytical queries across petabytes of structured data. The queries need to run on historical data older than 6 months.

Which service should the Solutions Architect use?

- A. Amazon RDS for PostgreSQL
- B. Amazon Redshift
- C. Amazon DynamoDB
- D. Amazon Aurora

**Correct Answer: B**

**Explanation:** Amazon Redshift is a fully managed data warehouse service designed for OLAP (Online Analytical Processing) workloads. It uses columnar storage and massively parallel processing (MPP) to run complex analytical queries against petabytes of data efficiently. RDS/Aurora are for OLTP. DynamoDB is NoSQL and not designed for complex analytical queries.

---

### Question 12
A company wants to implement a caching layer for their DynamoDB table to reduce response time from single-digit milliseconds to microseconds.

Which caching service should the Solutions Architect use?

- A. Amazon ElastiCache for Redis
- B. Amazon ElastiCache for Memcached
- C. Amazon DynamoDB Accelerator (DAX)
- D. Amazon CloudFront

**Correct Answer: C**

**Explanation:** DAX (DynamoDB Accelerator) is a fully managed, in-memory cache specifically designed for DynamoDB. It reduces DynamoDB response times from single-digit milliseconds to microseconds. DAX is fully compatible with DynamoDB API calls — no application code changes needed. ElastiCache works but requires application code changes and is a more general-purpose cache.

---

### Question 13
A company needs to migrate an on-premises PostgreSQL database with 500 GB of data to Amazon RDS PostgreSQL. The migration must have minimal downtime.

Which migration approach should the Solutions Architect use?

- A. AWS Database Migration Service (DMS) with continuous replication
- B. pg_dump and pg_restore to RDS
- C. Copy the database files to S3 and import to RDS
- D. AWS Snowball

**Correct Answer: A**

**Explanation:** AWS DMS supports continuous replication (CDC - Change Data Capture) which allows minimal downtime migration. DMS replicates the initial data and then continuously replicates changes until the cutover. pg_dump/pg_restore requires downtime during the export/import process. S3 import is not a supported method for RDS. Snowball is for large data transfers to S3.

---

### Question 14
An application needs a database that provides millisecond latency, automatic multi-Region replication, and 99.999% availability.

Which DynamoDB feature should the Solutions Architect enable?

- A. DynamoDB Streams
- B. DynamoDB Global Tables
- C. DynamoDB Point-in-Time Recovery
- D. DynamoDB Transactions

**Correct Answer: B**

**Explanation:** DynamoDB Global Tables provide fully managed, multi-Region, multi-active replication. Data is automatically replicated across AWS Regions with millisecond latency for local reads/writes. Global Tables provide 99.999% availability SLA. DynamoDB Streams is a change data capture feature. PITR is for backups. Transactions are for ACID operations.

---

### Question 15
A company is building an application that requires a database capable of handling reads of 100,000 requests per second with low latency. Read traffic is 90% of total traffic. The application uses a relational data model.

Which architecture should the Solutions Architect design?

- A. Amazon Aurora with Aurora Replicas and read endpoint
- B. Amazon RDS with a single large instance
- C. Amazon DynamoDB with DAX
- D. Amazon Redshift with Concurrency Scaling

**Correct Answer: A**

**Explanation:** Aurora supports up to 15 Aurora Replicas with automatic load balancing through the reader endpoint. Aurora Replicas share the same storage volume as the primary, so replication lag is minimal (usually <10ms). This architecture can handle extremely high read throughput. A single RDS instance cannot handle 100K reads/second. DynamoDB is NoSQL, not relational.

---

### Question 16
A company needs a database solution that can automatically scale storage from 10 GB to 128 TB without downtime, and supports up to 15 read replicas.

Which database service meets these requirements?

- A. Amazon RDS MySQL
- B. Amazon Aurora
- C. Amazon DynamoDB
- D. Amazon RDS PostgreSQL

**Correct Answer: B**

**Explanation:** Aurora automatically scales storage in 10 GB increments up to 128 TB. It supports up to 15 Aurora Replicas. Storage scaling is automatic and causes no downtime. RDS MySQL/PostgreSQL supports up to 5 read replicas and has a max storage of 64 TB. DynamoDB storage scales automatically but is NoSQL.

---

### Question 17
A company runs a critical relational database on Amazon RDS. The company needs to ensure that the database can survive an AZ failure with minimal data loss and automatic failover.

Which RDS feature should the Solutions Architect enable?

- A. Read Replicas with automatic promotion
- B. Multi-AZ deployment
- C. Automated backups
- D. Cross-Region Read Replicas

**Correct Answer: B**

**Explanation:** Multi-AZ deployment maintains a synchronous standby replica in a different AZ. If the primary fails, RDS automatically promotes the standby, typically within 1-2 minutes. The synchronous replication ensures near-zero data loss. Read Replicas use asynchronous replication (possible data loss) and don't automatically promote. Automated backups help with recovery but don't provide automatic failover.

---

### Question 18
A company needs to run analytical queries on real-time data without affecting the performance of their production Aurora MySQL database.

Which feature should the Solutions Architect use?

- A. Aurora Read Replicas
- B. Aurora Parallel Query
- C. Aurora Serverless
- D. Aurora Global Database

**Correct Answer: A**

**Explanation:** Aurora Read Replicas share the same storage as the primary instance with minimal replication lag. Analytical queries can be directed to replicas, which offloads the production database. Aurora Parallel Query is for speeding up analytical queries across the entire dataset. However, for the specific goal of isolating analytical workloads from production, read replicas are the correct approach.

---

### Question 19
A company needs a serverless database that automatically scales based on actual usage and charges per second of compute time. The application has unpredictable usage patterns with occasional bursts.

Which database solution should the Solutions Architect recommend?

- A. Amazon DynamoDB On-Demand
- B. Amazon Aurora Serverless v2
- C. Amazon RDS with reserved capacity
- D. Amazon ElastiCache Serverless

**Correct Answer: B**

**Explanation:** Aurora Serverless v2 automatically scales database capacity based on application demand. It scales in fine-grained increments (0.5 ACU), starts/stops automatically, and charges per second. It's ideal for unpredictable workloads that need a relational database. DynamoDB On-Demand is serverless but NoSQL. RDS reserved capacity is for predictable workloads.

---

### Question 20
A company wants to implement a database solution for storing user session data. The data must be available with sub-millisecond latency and should automatically expire after 24 hours.

Which solution is MOST appropriate?

- A. Amazon DynamoDB with TTL (Time to Live)
- B. Amazon ElastiCache for Redis with TTL
- C. Amazon RDS with a scheduled cleanup job
- D. Amazon S3 with lifecycle policy

**Correct Answer: B**

**Explanation:** ElastiCache for Redis provides sub-millisecond latency and natively supports TTL on keys, which automatically expires session data after the specified time. DynamoDB with TTL provides millisecond latency (not sub-millisecond) and TTL deletion is eventual (can take up to 48 hours). For session data requiring sub-millisecond access, Redis is ideal.

---

### Question 21
A company is designing a multi-Region active-active application architecture. The application needs a database that supports writes in all Regions simultaneously.

Which database solution should the Solutions Architect use?

- A. Amazon Aurora Global Database
- B. Amazon DynamoDB Global Tables
- C. Amazon RDS with Cross-Region Read Replicas
- D. Amazon ElastiCache Global Datastore

**Correct Answer: B**

**Explanation:** DynamoDB Global Tables support multi-Region, multi-active (read/write) replication. All regions can accept writes simultaneously, and conflicts are resolved using a "last writer wins" approach. Aurora Global Database has a single primary Region for writes and read-only secondary Regions. RDS Cross-Region Read Replicas are read-only in secondary Regions.

---

### Question 22
A company needs to migrate a MongoDB database to AWS. They want a fully managed solution compatible with MongoDB.

Which service should the Solutions Architect recommend?

- A. Amazon DynamoDB
- B. Amazon DocumentDB (with MongoDB compatibility)
- C. Amazon RDS
- D. Amazon Aurora

**Correct Answer: B**

**Explanation:** Amazon DocumentDB is a fully managed document database service that is compatible with MongoDB workloads. It supports MongoDB 3.6, 4.0, and 5.0 APIs. This allows applications to use existing MongoDB drivers and tools. DynamoDB is a different NoSQL model. RDS/Aurora are relational databases.

---

### Question 23
A company has an Aurora MySQL database. They need to create a disaster recovery copy of the database in another AWS Region with a recovery time objective (RTO) of less than 1 minute.

Which feature should the Solutions Architect use?

- A. Aurora Read Replicas in another Region
- B. Aurora Global Database
- C. DMS with continuous replication to another Region
- D. Automated backups copied to another Region

**Correct Answer: B**

**Explanation:** Aurora Global Database provides cross-Region replication with typical replication lag of under 1 second. In disaster scenarios, a secondary Region can be promoted to full read/write capability in under 1 minute (RTO < 1 min). Cross-Region Read Replicas can take longer to promote. DMS involves more complexity. Automated backups require restore time.

---

### Question 24
A company wants to reduce the cost of their Amazon RDS database that runs 24/7 with predictable capacity needs for the next 3 years.

Which purchasing option provides the GREATEST savings?

- A. On-Demand pricing
- B. 1-year Reserved Instance
- C. 3-year Reserved Instance with All Upfront payment
- D. Aurora Serverless

**Correct Answer: C**

**Explanation:** RDS Reserved Instances with a 3-year term and All Upfront payment provide the maximum discount (up to 69% compared to On-Demand). For predictable, steady-state workloads running 24/7, reserved instances are the most cost-effective option. Aurora Serverless is better for variable workloads.

---

### Question 25
A company needs a database that provides immutable and cryptographically verifiable transaction logs. The database will be used for regulatory compliance to track all changes to financial records.

Which service should the Solutions Architect recommend?

- A. Amazon Aurora with audit logging
- B. Amazon QLDB (Quantum Ledger Database)
- C. Amazon DynamoDB with Streams
- D. Amazon RDS with binary logging

**Correct Answer: B**

**Explanation:** Amazon QLDB provides an immutable, transparent, and cryptographically verifiable transaction log owned by a central trusted authority. It maintains a complete and verifiable history of all changes to the data. This is ideal for regulatory compliance in financial applications. DynamoDB Streams have a 24-hour retention limit. Aurora/RDS audit logs can be modified or deleted.

---

## Quick Reference: Database Selection Guide

| Requirement | Recommended Service |
|-------------|-------------------|
| Relational + MySQL/PostgreSQL compatible | Amazon Aurora |
| Relational + Oracle/SQL Server | Amazon RDS |
| Key-value / Document (NoSQL) | Amazon DynamoDB |
| In-memory caching (sub-ms latency) | Amazon ElastiCache |
| DynamoDB caching (microsecond) | Amazon DAX |
| Graph data / relationships | Amazon Neptune |
| Data warehousing / OLAP | Amazon Redshift |
| Document DB (MongoDB compatible) | Amazon DocumentDB |
| Immutable ledger | Amazon QLDB |
| Time-series data | Amazon Timestream |
| Wide-column (Cassandra compatible) | Amazon Keyspaces |

## Quick Reference: RDS vs Aurora

| Feature | RDS | Aurora |
|---------|-----|--------|
| Max Storage | 64 TB | 128 TB |
| Read Replicas | Up to 5 | Up to 15 |
| Replication | Async | Sync (shared storage) |
| Failover Time | 1-2 min | <30 sec |
| Storage Auto-scaling | Manual/Auto (with config) | Automatic |
| Multi-AZ Data Copies | 2 AZs | 3 AZs (6 copies) |
| Serverless Option | No | Yes (Serverless v2) |
| Global Database | No (Cross-Region RR) | Yes |
