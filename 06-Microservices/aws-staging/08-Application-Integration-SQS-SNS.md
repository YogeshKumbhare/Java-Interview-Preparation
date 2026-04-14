# AWS SAA Exam - Application Integration (SQS, SNS, Kinesis, EventBridge)

> **Domain Coverage:** Design High-Performing Architectures, Design Resilient Architectures
> **Services:** SQS, SNS, Kinesis Data Streams, Kinesis Data Firehose, Amazon MQ, EventBridge, AppFlow

---

## Questions & Answers

### Question 1
A company has a web application that needs to process customer orders. The order processing takes several minutes. The company wants to decouple the web tier from the processing tier to improve fault tolerance.

Which architecture should the Solutions Architect implement?

- A. Web tier writes to a shared EBS volume, processing tier reads from it
- B. Web tier sends messages to an SQS queue, processing tier polls the queue
- C. Web tier directly invokes the processing tier Lambda functions
- D. Web tier uses shared database table for task coordination

**Correct Answer: B**

**Explanation:** SQS provides reliable, asynchronous message queuing that decouples the web tier from the processing tier. If the processing tier fails, messages remain in the queue and are processed when it recovers. Direct invocation creates tight coupling. Shared storage or database creates dependencies and doesn't provide queue semantics.

---

### Question 2
A company needs to send a single notification that triggers multiple downstream systems: email, SMS, mobile push notifications, and an SQS queue for order processing.

Which service should the Solutions Architect use?

- A. Amazon SQS with multiple consumers
- B. Amazon SNS with multiple subscription types
- C. Amazon EventBridge
- D. AWS Step Functions

**Correct Answer: B**

**Explanation:** Amazon SNS supports multiple subscription protocols (Email, SMS, HTTP/HTTPS, Lambda, SQS, mobile push) from a single topic. Publishing one message to the SNS topic delivers it to all subscribers simultaneously. SQS delivers messages to only one consumer. EventBridge is event-driven but doesn't natively support all these notification protocols directly.

---

### Question 3
A company collects IoT sensor data from thousands of devices. The data arrives at a rate of 10,000 records per second and must be processed in real-time with the ability to replay the data stream.

Which service should the Solutions Architect use?

- A. Amazon SQS
- B. Amazon SNS
- C. Amazon Kinesis Data Streams
- D. Amazon MQ

**Correct Answer: C**

**Explanation:** Kinesis Data Streams handles real-time ingestion at massive scale (thousands of records per second per shard). It supports data replay (consumers can re-read data within the retention period of 24 hours to 365 days). Multiple consumers can read the same data independently. SQS doesn't support replay or real-time streaming. SNS is pub/sub, not stream processing.

---

### Question 4
A company needs to deliver real-time streaming data directly to Amazon S3, Amazon Redshift, and Amazon Elasticsearch. The company wants a fully managed solution with minimal custom code.

Which service should the Solutions Architect use?

- A. Amazon Kinesis Data Streams with custom Lambda consumers
- B. Amazon Kinesis Data Firehose
- C. AWS Glue streaming
- D. Amazon MSK (Managed Streaming for Apache Kafka)

**Correct Answer: B**

**Explanation:** Kinesis Data Firehose is a fully managed service that delivers streaming data to S3, Redshift, Elasticsearch (OpenSearch), and Splunk. It handles batching, compression, encryption, and delivery automatically — no custom consumer code needed. Kinesis Data Streams requires custom consumers. Glue is for ETL. MSK requires managing Kafka infrastructure.

---

### Question 5
A company is migrating from on-premises ActiveMQ to AWS. They need a managed message broker that supports JMS, AMQP, MQTT, and STOMP protocols to maintain compatibility with existing applications.

Which service should the Solutions Architect use?

- A. Amazon SQS
- B. Amazon SNS
- C. Amazon MQ
- D. Amazon Kinesis

**Correct Answer: C**

**Explanation:** Amazon MQ is a managed message broker service for Apache ActiveMQ and RabbitMQ that supports industry-standard protocols (JMS, AMQP, MQTT, STOMP, OpenWire). It provides seamless migration from on-premises ActiveMQ without code changes. SQS and SNS use AWS-proprietary APIs. Kinesis is for streaming data, not traditional message brokering.

---

### Question 6
A company processes financial transactions. Each transaction must be processed exactly once and in the exact order they were received.

Which SQS feature ensures this?

- A. SQS Standard Queue with visibility timeout
- B. SQS FIFO Queue with MessageGroupId
- C. SQS Standard Queue with DLQ
- D. SQS FIFO Queue with ContentBasedDeduplication

**Correct Answer: B**

**Explanation:** SQS FIFO queues guarantee exactly-once processing and strict ordering within a MessageGroupId. All messages with the same MessageGroupId are processed in exact order. FIFO queues are limited to 300 messages/second (3,000 with batching). Standard queues provide best-effort ordering and at-least-once delivery. ContentBasedDeduplication is for automatic dedup but doesn't handle ordering alone.

---

### Question 7
A company has created a new application that sends 50 messages per second to an SQS FIFO queue. Messages are processed by a fleet of EC2 instances. The company discovers that messages from different customers are being blocked by each other.

How can the Solutions Architect improve parallelism while maintaining per-customer ordering?

- A. Switch to SQS Standard Queue
- B. Use MessageGroupId set to customer ID
- C. Create separate FIFO queues for each customer
- D. Increase the number of EC2 instances

**Correct Answer: B**

**Explanation:** Setting MessageGroupId to the customer ID ensures that messages within the same customer are processed in order, while messages for different customers can be processed in parallel. FIFO queues support up to 20,000 message groups. Standard Queue would lose ordering. Separate queues per customer doesn't scale. More instances alone doesn't fix the ordering contention.

---

### Question 8
A company has a Lambda function processing messages from an SQS queue. Some messages consistently fail processing. After multiple retries, the failed messages block new messages from being processed.

What should the Solutions Architect configure?

- A. Increase the visibility timeout
- B. Configure a Dead Letter Queue (DLQ) with maxReceiveCount
- C. Delete the failed messages manually
- D. Increase Lambda memory

**Correct Answer: B**

**Explanation:** A Dead Letter Queue (DLQ) receives messages that exceed the maxReceiveCount (maximum retries). After N failed processing attempts, the message is moved to the DLQ for investigation, unblocking the main queue. You can then analyze and reprocess DLQ messages. Increasing visibility timeout delays retries but doesn't solve the fundamental problem.

---

### Question 9
A company has an event-driven architecture. When a user signs up, they need to: (1) send a welcome email, (2) create a user profile in DynamoDB, (3) trigger a marketing workflow. These actions should be loosely coupled.

Which architecture provides the BEST decoupling?

- A. Lambda function that performs all three actions sequentially
- B. SNS topic with three Lambda subscribers
- C. EventBridge event bus with three rules targeting different Lambda functions
- D. Step Functions with parallel states

**Correct Answer: C**

**Explanation:** EventBridge provides the best decoupling through event-driven architecture. Custom events are published to the event bus, and rules independently route events to different targets. Each target is completely independent — adding or removing actions doesn't affect others. SNS also works for fan-out but EventBridge provides richer filtering, schema registry, and event replay.

---

### Question 10
A company needs to stream large volumes of clickstream data to S3 for batch analytics. The data should arrive in S3 in near-real-time (within 60 seconds) and be automatically converted from JSON to Parquet format.

Which service should the Solutions Architect use?

- A. Kinesis Data Streams with Lambda consumer
- B. Kinesis Data Firehose with format conversion
- C. AWS Glue streaming ETL
- D. Amazon MSK with S3 connector

**Correct Answer: B**

**Explanation:** Kinesis Data Firehose supports delivery to S3 with a minimum buffer interval of 60 seconds. It natively supports format conversion from JSON to Parquet (or ORC) using an AWS Glue table schema. This is fully managed with no custom code. Kinesis Data Streams with Lambda requires custom consumer code. Glue streaming is more complex and expensive.

---

### Question 11
A company has a distributed application where microservices communicate via messages. One service produces events, and multiple services need to consume the SAME event independently, each at their own pace.

Which architecture should the Solutions Architect use?

- A. SQS queue shared by all consumers
- B. SNS topic with SQS queue per consumer (fan-out)
- C. Direct HTTP calls between services
- D. Shared database table for events

**Correct Answer: B**

**Explanation:** The SNS+SQS fan-out pattern allows each consumer to have its own SQS queue subscribed to the SNS topic. Each consumer processes messages independently at its own rate without affecting others. If a consumer is slow or offline, its queue accumulates messages until it catches up. A shared SQS queue would deliver each message to only one consumer.

---

### Question 12
A company has a legacy application that uses RabbitMQ for message queuing. They want to migrate to AWS with minimal application changes.

Which AWS service should the Solutions Architect recommend?

- A. Amazon SQS
- B. Amazon MQ for RabbitMQ
- C. Amazon Kinesis Data Streams
- D. Amazon EventBridge

**Correct Answer: B**

**Explanation:** Amazon MQ for RabbitMQ is a fully managed RabbitMQ broker. Applications using RabbitMQ protocols (AMQP 0-9-1) can migrate with minimal code changes. SQS uses a different API that would require application changes. Kinesis is for streaming, not message queuing with RabbitMQ protocol. EventBridge is event-driven, not a message broker.

---

### Question 13
A company has an SQS queue with a visibility timeout of 30 seconds. The processing Lambda function sometimes takes 5 minutes to complete. Messages are being processed multiple times.

What should the Solutions Architect do?

- A. Increase the visibility timeout to at least 5 minutes (300 seconds)
- B. Increase Lambda memory to process faster
- C. Switch to SNS instead of SQS
- D. Enable long polling

**Correct Answer: A**

**Explanation:** When the visibility timeout is shorter than the processing time, the message becomes visible to other consumers before processing completes, causing duplicate processing. The visibility timeout must be at least as long as the maximum processing time plus a buffer. Set it to 360 seconds (6 minutes) to account for the 5-minute processing time.

---

### Question 14
A company needs to process stock market data with sub-second latency. The data arrives as a continuous stream from multiple sources. The processing requires ordered records from each source.

Which combination should the Solutions Architect use?

- A. SQS FIFO Queue with Lambda
- B. Kinesis Data Streams with partition key set to source ID
- C. SNS with Lambda subscribers
- D. EventBridge with SQS targets

**Correct Answer: B**

**Explanation:** Kinesis Data Streams provides sub-second latency for stream processing. Using the source ID as the partition key ensures all records from the same source go to the same shard, maintaining order per source. Multiple shards enable parallel processing of different sources. SQS FIFO has a 300 msg/s limit. SNS doesn't support streams. EventBridge adds latency.

---

### Question 15
A company wants to integrate SaaS applications (Salesforce, ServiceNow) with AWS services to transfer data on a schedule.

Which service should the Solutions Architect use?

- A. AWS DataSync
- B. Amazon AppFlow
- C. AWS Transfer Family
- D. Custom Lambda functions with API calls

**Correct Answer: B**

**Explanation:** Amazon AppFlow is a fully managed integration service that enables secure data transfer between SaaS applications (Salesforce, SAP, Zendesk, ServiceNow, etc.) and AWS services (S3, Redshift). It supports scheduled and event-driven transfers with data transformation. DataSync is for file-based data transfer. Transfer Family is for SFTP/FTPS. Custom Lambda requires significant development.

---

### Question 16
A company has an SNS topic that sends notifications to SQS queues in different AWS accounts. Some messages are being lost because the SQS queues in other accounts don't have the correct access policy.

What should the Solutions Architect configure on each SQS queue?

- A. IAM policy in the queue owner's account
- B. SQS queue access policy allowing the SNS topic to send messages
- C. Cross-account IAM role
- D. SNS endpoint subscription with protocol confirmation

**Correct Answer: B**

**Explanation:** Each SQS queue must have a queue policy (resource-based policy) that allows the SNS topic (identified by its ARN) to perform `sqs:SendMessage`. Without this policy, SNS cannot deliver messages to the queue in another account. Additionally, the subscription must be confirmed. IAM policies alone can't grant cross-service, cross-account access; resource-based policies are needed.

---

### Question 17
A company needs to implement a reliable message delivery system where each message is processed by one of many consumers. If a consumer fails, the message should be available for another consumer.

Which service provides this pattern NATIVELY?

- A. Amazon SNS
- B. Amazon SQS Standard Queue
- C. Amazon Kinesis Data Streams
- D. Amazon EventBridge

**Correct Answer: B**

**Explanation:** SQS Standard Queue provides the competing consumers pattern. Messages are distributed to consumers, and the visibility timeout ensures that if a consumer fails, the message becomes visible again for another consumer. Only one consumer processes each message. SNS is pub/sub (one-to-many). Kinesis supports multiple consumers but each reads all records. EventBridge routes events, not queued processing.

---

### Question 18
A company has a Kinesis Data Stream with 4 shards. They need to increase throughput for a growing workload.

What should the Solutions Architect do?

- A. Increase the retention period
- B. Split shards to increase capacity (resharding)
- C. Merge shards to increase capacity
- D. Add enhanced fan-out consumers

**Correct Answer: B**

**Explanation:** Each shard provides 1 MB/s input and 2 MB/s output. Splitting shards increases the number of shards, increasing total throughput. Merging reduces shards (decreases throughput). Increasing retention period keeps data longer but doesn't increase throughput. Enhanced fan-out provides dedicated throughput per consumer but doesn't increase overall ingestion capacity.

---

### Question 19
A company needs to ensure that email notifications are sent when specific AWS resource changes occur (e.g., EC2 instance state changes, S3 bucket policy modifications).

Which solution provides the MOST comprehensive coverage?

- A. CloudWatch Events with SNS
- B. Amazon EventBridge with SNS integration
- C. AWS Config Rules with SNS
- D. CloudTrail with Lambda

**Correct Answer: B**

**Explanation:** Amazon EventBridge (evolution of CloudWatch Events) provides comprehensive coverage of AWS service events. It supports all AWS service events, custom events, and SaaS partner events. Rules can filter specific events and route them to SNS for email notifications. EventBridge provides richer event filtering than CloudWatch Events and is the recommended service.

---

### Question 20
A company is processing messages from an SQS queue. They want to process messages in batches of 10, but also want the Lambda function to wait up to 20 seconds for a full batch before processing.

Which SQS feature should the Solutions Architect configure?

- A. Short polling with batch size of 10
- B. Long polling with batch size of 10
- C. Message timer with batch size of 10
- D. Visibility timeout of 20 seconds

**Correct Answer: B**

**Explanation:** Long polling (WaitTimeSeconds up to 20 seconds) keeps the connection open and waits for messages to arrive, reducing empty responses and API costs. Combined with a batch size of 10, Lambda receives up to 10 messages per invocation. Short polling returns immediately (potentially empty). Message timer delays message availability. Visibility timeout affects processing time, not batching.

---

## Quick Reference: SQS vs SNS vs Kinesis vs EventBridge

| Feature | SQS | SNS | Kinesis | EventBridge |
|---------|-----|-----|---------|------------|
| Pattern | Queue (pull) | Pub/Sub (push) | Stream (pull/push) | Event bus (push) |
| Consumers | One consumer/msg | Many subscribers | Many consumers | Many targets |
| Ordering | FIFO only | No | Per shard | No |
| Replay | No (consumed = deleted) | No | Yes (retention) | Yes (archive) |
| Throughput | Nearly unlimited | Nearly unlimited | Per shard (1 MB/s in) | Nearly unlimited |
| Retention | 4-14 days | None (immediate) | 24hr - 365 days | None / Archive |
| Use Case | Decoupling, buffering | Notifications, fan-out | Real-time analytics | Event-driven arch |

## Quick Reference: SQS Standard vs FIFO

| Feature | Standard | FIFO |
|---------|----------|------|
| Throughput | Unlimited | 300 msg/s (3,000 with batching) |
| Ordering | Best-effort | Strict (per MessageGroupId) |
| Delivery | At-least-once | Exactly-once |
| Deduplication | No | Yes (5-min window) |
| Name Suffix | Any | Must end with .fifo |
