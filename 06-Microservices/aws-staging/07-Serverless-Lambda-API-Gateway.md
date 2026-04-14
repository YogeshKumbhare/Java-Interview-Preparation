# AWS SAA Exam - Serverless (Lambda, API Gateway, Step Functions)

> **Domain Coverage:** Design High-Performing Architectures, Design Cost-Optimized Architectures
> **Services:** Lambda, API Gateway, Step Functions, AppSync, EventBridge, SAM, Amplify

---

## Questions & Answers

### Question 1
A company wants to build a REST API that automatically scales based on demand. The backend logic performs simple CRUD operations on a DynamoDB table. The company wants to minimize operational overhead.

Which architecture should the Solutions Architect recommend?

- A. EC2 instances behind an ALB with Auto Scaling
- B. Amazon API Gateway with AWS Lambda and DynamoDB
- C. Amazon ECS with Fargate behind an ALB
- D. Amazon EC2 with a custom API framework

**Correct Answer: B**

**Explanation:** API Gateway + Lambda + DynamoDB is the fully serverless architecture that auto-scales, requires zero server management, and uses a pay-per-request pricing model. API Gateway handles HTTP routing, Lambda executes the business logic, and DynamoDB stores the data. EC2 and ECS require managing infrastructure. This is the most operationally efficient solution.

---

### Question 2
A Lambda function needs to process images uploaded to an S3 bucket. Each image takes 10-14 minutes to process. Some images fail processing and need to be retried.

What should the Solutions Architect configure?

- A. S3 Event Notification → Lambda (with 15-minute timeout)
- B. S3 Event Notification → SQS → Lambda (with 15-minute timeout and DLQ)
- C. S3 Event Notification → SNS → Lambda
- D. S3 Event Notification → EventBridge → Lambda

**Correct Answer: B**

**Explanation:** Lambda has a maximum timeout of 15 minutes, which covers the 10-14 minute processing. Using SQS between S3 and Lambda provides: (1) buffering during traffic spikes, (2) automatic retries via visibility timeout, (3) Dead Letter Queue (DLQ) for failed messages after max retries. Direct S3→Lambda invocation doesn't provide retry/DLQ capabilities as cleanly. SQS ensures no image is lost.

---

### Question 3
A company has a Lambda function that is invoked 10 million times per month with an average execution time of 200ms and uses 256 MB of memory. They want to reduce costs.

Which approach should the Solutions Architect consider?

- A. Increase memory to 512 MB (may reduce execution time)
- B. Use Provisioned Concurrency
- C. Use ARM-based (Graviton2) Lambda functions
- D. Both A and C

**Correct Answer: D**

**Explanation:** Increasing memory may reduce execution time (Lambda CPU scales linearly with memory), potentially reducing overall cost despite higher per-ms cost. ARM/Graviton2 functions cost 20% less and can provide up to 34% better price-performance. Combining both optimizations maximizes cost savings. Provisioned Concurrency adds cost and is for reducing cold starts, not general cost optimization.

---

### Question 4
A company has a workflow that involves multiple Lambda functions executed in sequence. If one step fails, the entire workflow should stop. The company needs to track the state of each step.

Which service should the Solutions Architect use to orchestrate this workflow?

- A. Amazon SQS with chained Lambda functions
- B. AWS Step Functions
- C. Amazon EventBridge with Lambda targets
- D. Amazon SNS with Lambda subscribers

**Correct Answer: B**

**Explanation:** AWS Step Functions provides visual workflow orchestration for Lambda functions (and other AWS services). It tracks the state of each step, supports error handling, retries, parallel execution, and conditional branching. Step Functions maintains the state machine, so you can see exactly where a workflow failed. SQS provides decoupling but not workflow orchestration. EventBridge is for event routing.

---

### Question 5
A company needs to create a WebSocket API that maintains persistent connections with clients for real-time chat functionality. The backend is serverless.

Which service should the Solutions Architect use?

- A. Application Load Balancer with Lambda targets
- B. Amazon API Gateway WebSocket API with Lambda
- C. Amazon CloudFront with Lambda@Edge
- D. Amazon AppSync with subscriptions

**Correct Answer: B**

**Explanation:** API Gateway supports WebSocket APIs that maintain persistent, two-way connections with clients. Lambda functions handle the $connect, $disconnect, and $default routes. API Gateway manages the WebSocket connections. AppSync subscriptions also work for real-time but require GraphQL. ALB supports WebSocket but requires EC2/ECS, not serverless Lambda. CloudFront doesn't support WebSocket natively.

---

### Question 6
A Lambda function needs to connect to an Amazon RDS database. Under heavy load, the database runs out of connections.

Which service should the Solutions Architect implement to solve this?

- A. Increase the RDS instance size
- B. Amazon RDS Proxy
- C. Amazon ElastiCache
- D. Lambda Provisioned Concurrency

**Correct Answer: B**

**Explanation:** Amazon RDS Proxy pools and shares database connections, reducing the connection overhead. Lambda functions create new connections on each invocation, which can overwhelm RDS. RDS Proxy maintains a warm connection pool, improving database efficiency and reducing connection-related errors. ElastiCache caches data but doesn't solve the connection problem. Provisioned Concurrency reduces cold starts, not connection pooling.

---

### Question 7
A company wants to run a Lambda function on a predictable schedule — every day at 6 AM UTC to generate daily reports.

Which service should trigger the Lambda function?

- A. Amazon SQS
- B. Amazon CloudWatch Events / EventBridge scheduled rule
- C. API Gateway
- D. AWS Step Functions

**Correct Answer: B**

**Explanation:** Amazon EventBridge (formerly CloudWatch Events) supports cron expressions and rate expressions to invoke Lambda functions on a schedule. A rule like `cron(0 6 * * ? *)` triggers Lambda at 6 AM UTC daily. SQS requires messages in the queue. API Gateway requires HTTP requests. Step Functions orchestrate workflows but don't schedule standalone triggers.

---

### Question 8
A company is building a serverless application. They need to serve static assets (HTML, CSS, JS) and route API calls to Lambda functions through API Gateway.

Which architecture minimizes costs and latency?

- A. S3 static website hosting + API Gateway + Lambda
- B. CloudFront distribution with S3 origin for static assets + API Gateway origin for APIs
- C. EC2 instances for both static and API
- D. ECS Fargate for both static and API

**Correct Answer: B**

**Explanation:** CloudFront serves as a single entry point with two origins: S3 for static assets (cached at edge locations for low latency) and API Gateway for API calls. This provides global low latency for static content and serverless APIs. S3 static hosting alone doesn't provide edge caching. EC2/ECS requires server management.

---

### Question 9
A Lambda function processes records from a Kinesis Data Stream. The function occasionally fails due to a poison pill (bad record). This causes the entire batch to be retried indefinitely, stopping all processing.

Which feature should the Solutions Architect configure?

- A. Lambda Dead Letter Queue (DLQ)
- B. Lambda event source mapping with BisectBatchOnFunctionError and MaximumRetryAttempts
- C. Lambda Destinations for failures
- D. Increase Lambda memory

**Correct Answer: B**

**Explanation:** `BisectBatchOnFunctionError` splits the failing batch in half on each retry to isolate the poison pill record. `MaximumRetryAttempts` limits retries to prevent infinite loops. Combined with `DestinationConfig` for failures (to send bad records to SQS/SNS), this approach handles poison pills without blocking the stream. DLQ works with async invocations, not stream-based triggers.

---

### Question 10
A company needs to build a GraphQL API that provides real-time subscriptions and offline data synchronization for a mobile application.

Which AWS service is MOST appropriate?

- A. Amazon API Gateway REST API
- B. Amazon API Gateway HTTP API
- C. AWS AppSync
- D. Amazon CloudFront

**Correct Answer: C**

**Explanation:** AWS AppSync is a managed GraphQL API service that supports real-time subscriptions via WebSocket and offline data synchronization for mobile apps. It integrates with DynamoDB, Lambda, and other data sources. API Gateway (REST/HTTP) supports REST APIs but not native GraphQL with subscriptions and offline sync.

---

### Question 11
A company runs a Lambda function that processes files from S3. The function needs access to a shared file system to store intermediate results that must persist between invocations and be accessible by multiple concurrent Lambda executions.

Which storage option should the Solutions Architect use?

- A. Lambda /tmp directory (512 MB - 10 GB)
- B. Amazon EFS mounted to Lambda
- C. Amazon S3 for intermediate storage
- D. Amazon DynamoDB for intermediate storage

**Correct Answer: B**

**Explanation:** Lambda supports mounting Amazon EFS as a shared file system. Multiple concurrent Lambda executions can read/write to the same EFS file system. Data persists across invocations. The /tmp directory is ephemeral and not shared between invocations. S3 works but has higher latency for file system operations. DynamoDB is for structured data, not file storage.

---

### Question 12
A company wants to reduce Lambda cold start times for a latency-sensitive Java function that handles API requests.

Which approach should the Solutions Architect use?

- A. Increase Lambda memory allocation
- B. Use Lambda Provisioned Concurrency
- C. Use Lambda SnapStart
- D. All of the above help reduce cold starts

**Correct Answer: D**

**Explanation:** All three help: More memory = more CPU = faster initialization. Provisioned Concurrency keeps instances warm (eliminates cold starts). SnapStart (for Java 11+) caches a snapshot of the initialized execution environment, dramatically reducing cold starts for Java functions. The best approach depends on cost tolerance and requirements.

---

### Question 13
A company has an API Gateway REST API. They want to restrict the API to return only 100 requests per second per client, while allowing burst traffic up to 200 requests per second.

Which API Gateway feature should the Solutions Architect configure?

- A. API Gateway usage plans with API keys
- B. API Gateway resource policies
- C. AWS WAF rate-limiting rule
- D. Lambda concurrency limits

**Correct Answer: A**

**Explanation:** API Gateway usage plans with API keys allow you to set throttling limits (rate and burst) per client (API key). You can configure a steady-state rate (100 req/s) and burst limit (200 req/s). Resource policies control access based on IP/VPC. WAF rate limiting blocks excessive requests but doesn't provide per-client throttling. Lambda concurrency limits affect all invocations, not per-client.

---

### Question 14
A company is building an event-driven architecture. When an order is placed, multiple downstream services need to be notified simultaneously: inventory service, payment service, and notification service. Each service processes the event independently.

Which architecture pattern should the Solutions Architect use?

- A. SQS queue with multiple consumers
- B. SNS topic with SQS queue subscriptions (fan-out pattern)
- C. Step Functions parallel state
- D. Lambda function that calls each service

**Correct Answer: B**

**Explanation:** The SNS fan-out pattern: An SNS topic publishes to multiple SQS queues (one per service). Each service processes its queue independently. This provides decoupling, independent scaling, and independent failure handling. SQS alone delivers each message to only one consumer. Step Functions create tight coupling. Direct Lambda calls create dependencies and retry complexity.

---

### Question 15
A company wants to deploy a Lambda function that requires specific Linux libraries and custom binary dependencies not available in the standard Lambda runtimes.

Which approach should the Solutions Architect use?

- A. Install dependencies at runtime using `pip install`
- B. Use Lambda Layers for shared libraries
- C. Package the function as a container image
- D. Both B and C work

**Correct Answer: D**

**Explanation:** Lambda Layers allow packaging libraries and dependencies separately (up to 250 MB unzipped). Container images allow packaging Lambda functions as Docker containers (up to 10 GB), including any custom binaries and libraries. Both approaches support custom dependencies. Installing at runtime adds latency and may fail.

---

### Question 16
A company needs to execute long-running workflows (up to 1 year) that involve human approval steps and waiting periods. The workflow must maintain state.

Which service should the Solutions Architect use?

- A. AWS Lambda with SQS
- B. AWS Step Functions Standard Workflows
- C. AWS Step Functions Express Workflows
- D. Amazon SWF

**Correct Answer: B**

**Explanation:** Step Functions Standard Workflows support executions up to 1 year, with built-in support for human approval tasks (using Task Tokens with callback patterns), waiting states, and state management. Express Workflows are limited to 5 minutes. Lambda has a 15-minute limit. SWF is a legacy service being replaced by Step Functions.

---

### Question 17
A company has a Lambda function that needs to process messages from an SQS queue. The messages must be processed exactly once and in order.

Which SQS queue type and Lambda configuration should be used?

- A. Standard Queue with Lambda event source mapping
- B. FIFO Queue with Lambda event source mapping
- C. Standard Queue with Lambda polling in a loop
- D. FIFO Queue with Lambda triggered by CloudWatch Events

**Correct Answer: B**

**Explanation:** SQS FIFO queues guarantee exactly-once processing and maintain strict message ordering. Lambda event source mapping with FIFO queues automatically processes messages in order and handles deduplication. Standard queues provide at-least-once delivery (possible duplicates) and best-effort ordering. CloudWatch Events doesn't trigger Lambda based on SQS messages.

---

### Question 18
A company wants to run custom code at CloudFront edge locations to customize content based on the user's device type and location.

Which feature should the Solutions Architect use?

- A. Lambda@Edge
- B. CloudFront Functions
- C. API Gateway with Lambda
- D. Both A and B can work, depending on requirements

**Correct Answer: D**

**Explanation:** Both work at edge locations: CloudFront Functions are lightweight (< 1ms), support viewer request/response events, and are ideal for simple transformations (header manipulation, URL rewrites). Lambda@Edge supports all CloudFront events, runs up to 30 seconds, and handles complex logic (device detection, A/B testing). Choose based on complexity and execution time requirements.

---

### Question 19
A company has an API Gateway REST API with Lambda backend. During peak hours, some requests receive 429 (Too Many Requests) errors.

What could be causing this and how should it be resolved?

- A. Lambda concurrency limit reached; request a concurrency limit increase
- B. API Gateway default throttling limit reached; increase the throttle settings
- C. DynamoDB throughput exceeded; enable auto-scaling
- D. All of the above could cause 429 errors

**Correct Answer: D**

**Explanation:** 429 errors can be caused by: (1) Lambda reaching its account-level concurrency limit (1,000 by default). (2) API Gateway throttling at the method, stage, or account level. (3) DynamoDB returning ProvisionedThroughputExceededException (which Lambda may surface as 429). Each needs to be investigated and addressed independently.

---

### Question 20
A company is deploying a serverless application using AWS SAM (Serverless Application Model). They want to gradually shift traffic from the old Lambda version to the new version.

Which deployment preference should the Solutions Architect configure?

- A. AllAtOnce
- B. Canary10Percent5Minutes
- C. Linear10PercentEvery10Minutes
- D. Blue/Green with manual switch

**Correct Answer: B**

**Explanation:** Canary deployment sends a small percentage of traffic (10%) to the new version for a watchdog period (5 minutes). If CloudWatch alarms are healthy, it shifts all remaining traffic. This provides safe, gradual deployment with automatic rollback if issues are detected. Linear shifts traffic in equal increments over time (slower). AllAtOnce has no protection. SAM supports all these through `DeploymentPreference`.

---

## Quick Reference: Lambda Limits

| Limit | Value |
|-------|-------|
| Timeout | 15 minutes max |
| Memory | 128 MB - 10,240 MB |
| Package Size (zip) | 50 MB compressed, 250 MB unzipped |
| Container Image Size | 10 GB |
| /tmp Storage | 512 MB - 10,240 MB |
| Concurrency (default) | 1,000 per Region |
| Environment Variables | 4 KB total |
| Layers | 5 per function |

## Quick Reference: API Gateway Types

| Feature | REST API | HTTP API | WebSocket API |
|---------|----------|----------|--------------|
| Cost | Higher | Lower (up to 71% less) | Per message/connection |
| Features | Full (caching, WAF, usage plans) | Basic (faster) | Real-time bidirectional |
| Auth | IAM, Cognito, Lambda, API Key | IAM, Cognito, JWT | IAM, Cognito, Lambda |
| Protocol | HTTP/HTTPS | HTTP/HTTPS | WebSocket |

## Quick Reference: When to Use What?

| Requirement | Service |
|-------------|---------|
| REST/HTTP API | API Gateway + Lambda |
| GraphQL API | AppSync |
| Event-driven processing | EventBridge + Lambda |
| Schedule-based tasks | EventBridge Rules + Lambda |
| Complex workflows | Step Functions |
| Message queuing | SQS + Lambda |
| Fan-out notifications | SNS + SQS |
| Stream processing | Kinesis + Lambda |
| Edge computing | Lambda@Edge / CloudFront Functions |
