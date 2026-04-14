# AWS Certified Solutions Architect Associate (SAA-C01) - Simulation Test 02

This file contains questions from the "Simulation Test 02" set. 
*(Note: Questions 1 to 58 are pending transcription and will be added here once located or re-extracted.)*

---

## Q59. Handling Sudden Traffic Surges
**Question:** A company is running a series of national TV campaigns. These 30 seconds advertisements will introduce sudden traffic peaks targeted at a Node.js application. The company expects traffic to increase from live requests each minute to more than 5000 requests each minute. Which AWS service should a Solutions Architect use to ensure traffic surges can be handled?
- A. Amazon Elasticache
- B. AWS Lambda
- C. Size EC2 instances to handle peak load
- D. An Auto scaling group for EC2 instances

**Correct Answer: D**

**Explanation:** An Auto Scaling group for EC2 instances can automatically adjust the number of instances in response to the sudden traffic peaks, ensuring that the application can handle the surges created by the TV campaigns.

---

## Q60. Ensuring High Availability with RDS
**Question:** A team has an application that detects new objects being uploaded into an AmazonS3 bucket. The uploads trigger a Lambda function to write object metadata into an Amazon DynamoDB table and RDS PostgreSQL database. Which action should the team take to ensure high availability? 
- A. Enable cross-region application in the AmazonS3 bucket
- B. Create a Lambda function for each Availability Zone the application is deployed.
- C. Enable multi-AZ on the RDS PostgreSQL database
- D. Create a Dynamo DB stream for the Dynamo DB table

**Correct Answer: C**

**Explanation:** Amazon S3 and DynamoDB are inherently highly available and fault-tolerant. AWS Lambda automatically runs your code across multiple Availability Zones. To ensure the RDS PostgreSQL database matches this level of high availability, Multi-AZ deployment must be enabled.

---

## Q61. Maintaining Order in a Waiting List
**Question:** A restaurant reservation application needs the ability to maintain a waiting list. When a customer tries to reserve a table, and none are available, the customer must be put on the waiting list, and the application must notify the customer when a table becomes free. What service should the Solution Architect recommend to ensure that the system respects the order in which the customer requests are put onto the waiting list?
- A. Amazon SNS
- B. AWS Lambda with sequential dispatch
- C. A FIFO queue in Amazon SQS
- D. A standard queue in Amazon SQS

**Correct Answer: C**

**Explanation:** Amazon SQS FIFO (First-In-First-Out) queues are designed to enhance messaging between applications when the order of operations and events is critical, or where duplicates can't be tolerated, such as maintaining a strict order in a waiting list.

---

## Q62. Improving Application Performance from Database Latency
**Question:** A company wants to improve the performance of their web application after receiving customer complaints. An analysis conducted that the same complex database queries were causing increased latency. What should a Solutions Architect recommend to improve the application's performance?
- A. Use Amazon Redshift to analyse the queries
- B. Migrate the database to MySQL
- C. Integrate Amazon Elasticache into the application
- D. Use a Lambda-triggered request to the backend database

**Correct Answer: A** (Note: As per the practice test portal screenshot. However, integrating Amazon ElastiCache (C) is the standard architectural best practice to cache the results of the same complex queries and improve application latency directly. Redshift is used for OLAP analytics rather than online application performance caching.)

**Explanation:** The portal answer marks Redshift (A). However, in a real-world scenario, to reduce database latency caused by repeated complex queries, caching the results using Amazon ElastiCache (such as Redis or Memcached) is typically the recommended and most effective approach.

---

## Q63. Restricting Content Delivery to Specific Countries
**Question:** An organization uses Amazon S3 to store video content served via its website. It only has rights to deliver this content to users within its own country and needs to restrict access. How can the organization ensure that these files are only accessible from within its country?
- A. Use a custom Amazon S3 bucket policy to allow access only to users inside the organizations country
- B. Use Amazon Cloud Front and Geo Restriction to allow access only to users inside the organization's country
- C. Use an Amazon S3 bucket ACL to allow access only to users inside the organization's country
- D. Use file-based ACL permissions on each video tile to allow access only to users inside the organization's country.

**Correct Answer: B**

**Explanation:** Amazon CloudFront provides a Geo Restriction (geo-blocking) feature that allows you to easily restrict access to your content based on the geographic location of your viewers, ensuring compliance with delivery rights.

---

## Q64. Minimizing Performance Degradation in ElastiCache
**Question:** A gaming application is heavily dependent on caching and uses Amazon ElastiCache for Redis. The application performance was recently degraded due to failure of the cache node. What should a Solutions Architect recommend to minimize performance degradation in the future?
- A. Migrate from ElastiCache to Amazon RDS.
- B. Configure automatic backup to save cache data.
- C. Configure ElastiCache Multi-AZ with automatic failover
- D. Use Auto Scaling to provision cache nodes based on CPU usage

**Correct Answer: C**

**Explanation:** Enabling Multi-AZ with Automatic Failover for ElastiCache for Redis ensures high availability by automatically detecting a primary node failure and promoting a replica to be the new primary, with minimal interruption to application performance.

---

## Q65. Cross-Region File Replication
**Question:** A company needs to quickly ensure that all files created in an Amazon S3 bucket in us-east-1 are also available in another bucket in ap-southeast-2. Which option represents the simplest way to implement this design?
- A. enable versioning and configure cross-region replication from the bucket in us-east-1 to the bucket in ap-southeast-2
- B. Add an S3 lifecycle rule to move any new files from the bucket in us-east-1b to the bucket in ap-southeast-2
- C. Create a Lambda function to be triggered for every new file in us-east-1 that copies the file to the bucket in ap-southeast-2
- D. Use SNS to notify the bucket in ap-southeast-2 to create a file whenever a file is created in the bucket in us-east-1

**Correct Answer: A**

**Explanation:** Cross-Region Replication (CRR) is an S3 feature that automatically and asynchronously copies objects across buckets in different AWS Regions. It provides the simplest managed way to achieve this. CRR requires versioning to be enabled on both the source and destination buckets.

---

## Summary
This file tracks questions from the SAA-C01 Simulation Test 02. Q59-Q65 from the extracted screenshot set are documented above.
