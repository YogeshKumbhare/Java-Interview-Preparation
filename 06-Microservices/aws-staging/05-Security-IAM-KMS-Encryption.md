# AWS SAA Exam - Security, IAM & Encryption

> **Domain Coverage:** Design Secure Architectures (30% of exam)
> **Services:** IAM, KMS, CloudHSM, AWS Organizations, SCP, Secrets Manager, Systems Manager Parameter Store, Cognito, STS, GuardDuty, Inspector, Macie, Shield, WAF, Security Hub, ACM, Config

---

## Questions & Answers

### Question 1
A Solution Architect is developing software on AWS that requires access to multiple AWS services, including an Amazon EC2 instance. This is a security sensitive application, and AWS credentials such as Access Key ID and Secret Access Key need to be protected and cannot be exposed anywhere in the system.

What security measure would satisfy these requirements?

- A. Store the AWS Access Key ID/Secret Access Key combination in software comments
- B. Assign an IAM user to the Amazon EC2 instance.
- C. Assign an IAM role to the Amazon EC2 instance.
- D. Enable multi-factor authentication for the AWS root account

**Correct Answer: C**

**Explanation:** IAM roles allow EC2 instances to obtain temporary security credentials automatically without embedding long-term credentials in code. The EC2 instance assumes the role and receives temporary credentials via the instance metadata service. IAM users require access keys (which could be exposed). MFA protects the root account but doesn't solve the credential management issue.

---

### Question 2
A company wants to enforce that all data stored in Amazon S3 is encrypted at rest. They need to use their own encryption keys managed within AWS.

Which encryption option should the Solutions Architect use?

- A. SSE-S3 (Server-Side Encryption with Amazon S3 managed keys)
- B. SSE-KMS (Server-Side Encryption with AWS KMS keys)
- C. SSE-C (Server-Side Encryption with Customer-Provided keys)
- D. Client-Side Encryption

**Correct Answer: B**

**Explanation:** SSE-KMS uses customer-managed keys (CMKs) in AWS KMS. KeyMS provides audit trails (via CloudTrail), key rotation, and fine-grained access control. SSE-S3 uses Amazon-managed keys with no customer control. SSE-C requires customers to manage keys outside AWS. Client-side encryption is done before upload and managed entirely by the customer.

---

### Question 3
A company has multiple AWS accounts and wants to enforce a policy that no user in any account can create S3 buckets with public access enabled.

Which approach should the Solutions Architect use?

- A. IAM policies in each account denying public S3 bucket creation
- B. AWS Organizations Service Control Policy (SCP) denying public S3 access
- C. S3 Block Public Access at the account level in each account
- D. Both B and C

**Correct Answer: D**

**Explanation:** SCPs in AWS Organizations set permission guardrails across all accounts (even if individual accounts try to allow public access). S3 Block Public Access at the account level prevents any bucket from being made public. Using both provides defense-in-depth. SCPs are preventive controls at the organization level, and Block Public Access is a service-level control.

---

### Question 4
A company stores sensitive customer data in Amazon S3. The company needs to ensure that every access to this data is logged, including who accessed it, when, and what operation was performed.

Which combination of features should the Solutions Architect enable? (Select TWO)

- A. S3 Server Access Logging
- B. AWS CloudTrail Data Events for S3
- C. AWS Config Rules for S3
- D. Amazon Macie
- E. VPC Flow Logs

**Correct Answer: A, B**

**Explanation:** S3 Server Access Logging provides detailed records of requests made to the bucket. CloudTrail Data Events for S3 log all API calls to S3 objects (GetObject, PutObject, DeleteObject). Together they provide comprehensive access auditing. Config tracks configuration changes, not access. Macie discovers sensitive data. VPC Flow Logs capture network traffic, not S3 access.

---

### Question 5
A company needs to store database credentials that an application on EC2 can retrieve securely. The credentials must be rotated automatically every 30 days.

Which service should the Solutions Architect use?

- A. AWS Systems Manager Parameter Store with SecureString
- B. AWS Secrets Manager
- C. AWS KMS
- D. IAM User Access Keys

**Correct Answer: B**

**Explanation:** AWS Secrets Manager stores secrets (database credentials, API keys) and supports built-in automatic rotation for RDS, DocumentDB, and Redshift databases. Parameter Store SecureString can store secrets but requires custom Lambda functions for rotation. KMS manages encryption keys, not passwords/credentials. IAM keys are for AWS API access.

---

### Question 6
A company wants to grant temporary access to an S3 bucket to a third-party auditor for 24 hours. The auditor does not have an AWS account.

Which approach should the Solutions Architect use?

- A. Create an IAM user with time-limited credentials
- B. Generate S3 presigned URLs for the required objects
- C. Create a cross-account IAM role
- D. Make the S3 bucket public temporarily

**Correct Answer: B**

**Explanation:** S3 presigned URLs grant time-limited access to specific objects without requiring the recipient to have AWS credentials. You can set the expiration time (e.g., 24 hours). The URL includes the permissions of the IAM entity that generated it. Cross-account roles require an AWS account. Making the bucket public is a security risk. IAM users shouldn't be created for temporary access.

---

### Question 7
A company uses AWS Organizations with multiple OUs (Organizational Units). The security team wants to ensure that no one in the development OU can terminate EC2 instances in production accounts.

Which approach should the Solutions Architect implement?

- A. IAM policies in each development account
- B. SCP attached to the development OU denying ec2:TerminateInstances for production resources
- C. Resource-based policies on production EC2 instances
- D. AWS Config rules to detect termination

**Correct Answer: B**

**Explanation:** Service Control Policies (SCPs) set the maximum permissions for member accounts in an OU. By attaching an SCP to the development OU that denies `ec2:TerminateInstances` for production resources, you prevent any action regardless of IAM permissions within those accounts. SCPs cannot be overridden by individual account IAM policies.

---

### Question 8
A company has a web application that authenticates users with a username and password stored in Amazon Cognito User Pools. The company wants to add social sign-in (Google, Facebook) without modifying the backend.

Which service should the Solutions Architect configure?

- A. Amazon Cognito Identity Pools (Federated Identities)
- B. Amazon Cognito User Pools with social identity providers
- C. AWS IAM Identity Center (SSO)
- D. AWS STS with SAML federation

**Correct Answer: B**

**Explanation:** Cognito User Pools support adding social identity providers (Google, Facebook, Apple, Amazon) as federated sign-in options. Users can sign in with social accounts, and Cognito handles the federation transparently. Identity Pools provide temporary AWS credentials for authenticated users. IAM Identity Center is for enterprise SSO. STS with SAML is for enterprise identity federation.

---

### Question 9
A company needs to encrypt all data in transit between their application and an Amazon RDS database.

Which approach should the Solutions Architect implement?

- A. Enable SSL/TLS on the RDS instance and require SSL connections
- B. Use a VPN connection between the application and RDS
- C. Enable SSE-KMS encryption on the RDS database
- D. Use AWS PrivateLink

**Correct Answer: A**

**Explanation:** Enabling SSL/TLS on RDS and requiring SSL connections (using `rds.force_ssl=1` parameter for PostgreSQL or `require_secure_transport=ON` for MySQL) encrypts data in transit. The application connects using the RDS CA certificate. SSE-KMS encrypts data at rest, not in transit. VPN and PrivateLink provide network-level privacy but don't inherently encrypt database connections.

---

### Question 10
A company wants to detect unauthorized use of their AWS credentials, suspicious API calls, and potential security threats in their AWS environment.

Which service should the Solutions Architect enable?

- A. AWS CloudTrail
- B. Amazon GuardDuty
- C. AWS Config
- D. Amazon Inspector

**Correct Answer: B**

**Explanation:** Amazon GuardDuty is a threat detection service that continuously monitors for malicious activity and unauthorized behavior. It analyzes CloudTrail logs, VPC Flow Logs, and DNS logs using machine learning. CloudTrail logs API calls but doesn't detect threats. Config tracks configuration changes. Inspector scans EC2 instances for vulnerabilities.

---

### Question 11
A company needs to implement the principle of least privilege for IAM access. A developer needs to read objects from a specific S3 bucket named "app-data-prod" and nothing else.

Which IAM policy provides the MINIMUM required permissions?

- A. `s3:*` on `arn:aws:s3:::app-data-prod/*`
- B. `s3:GetObject` on `arn:aws:s3:::app-data-prod/*`
- C. `s3:GetObject` on `arn:aws:s3:::*`
- D. AmazonS3ReadOnlyAccess managed policy

**Correct Answer: B**

**Explanation:** `s3:GetObject` grants only read access to objects, and restricting the resource to `arn:aws:s3:::app-data-prod/*` limits it to the specific bucket. This follows the principle of least privilege — granting only the minimum permissions needed. Option A grants all S3 actions. Option C grants read to all buckets. The managed policy grants read access to all S3 resources.

---

### Question 12
A company needs to manage SSH keys for hundreds of EC2 instances across multiple accounts. They want to eliminate the need for SSH key management and enable audit logging of all shell commands.

Which service should the Solutions Architect use?

- A. EC2 Instance Connect
- B. AWS Systems Manager Session Manager
- C. Bastion Host with SSH
- D. AWS Secrets Manager for SSH keys

**Correct Answer: B**

**Explanation:** Systems Manager Session Manager provides secure, auditable instance access without SSH keys, bastion hosts, or open inbound ports. All session activity can be logged to S3 and CloudWatch Logs for audit purposes. It uses IAM for access control. EC2 Instance Connect simplifies SSH but still uses keys. Bastion hosts require key management.

---

### Question 13
A company stores encryption keys using AWS KMS. A compliance requirement states that encryption keys must never leave the hardware security module (HSM) and the company must have exclusive access to the HSM.

Which service should the Solutions Architect use?

- A. AWS KMS with customer-managed CMK
- B. AWS KMS with AWS-managed CMK
- C. AWS CloudHSM
- D. AWS KMS with imported key material

**Correct Answer: C**

**Explanation:** AWS CloudHSM provides dedicated hardware security modules that are single-tenant. You have exclusive access to the HSM, and keys never leave the HSM. AWS KMS uses shared HSMs managed by AWS (regardless of whether you use customer-managed or AWS-managed CMKs). For compliance requiring exclusive HSM access, CloudHSM is the only option.

---

### Question 14
A company needs to protect their web application from DDoS attacks. They want both infrastructure-level protection (Layer 3/4) and application-level protection (Layer 7), along with 24/7 access to the AWS DDoS Response Team.

Which services should the Solutions Architect enable? (Select TWO)

- A. AWS Shield Standard
- B. AWS Shield Advanced
- C. AWS WAF
- D. Amazon GuardDuty
- E. AWS Firewall Manager

**Correct Answer: B, C**

**Explanation:** Shield Advanced provides enhanced DDoS protection at Layers 3, 4, and 7, plus 24/7 access to the AWS DDoS Response Team (DRT), cost protection, and advanced reporting. WAF provides Layer 7 application-level protection against web exploits (SQL injection, XSS). Together they provide comprehensive DDoS and application-layer protection. Shield Standard is automatic and free but doesn't include DRT access.

---

### Question 15
A company uses multiple AWS accounts. The security team needs a centralized view of all security findings across all accounts, including findings from GuardDuty, Inspector, Macie, and IAM Access Analyzer.

Which service provides this capability?

- A. AWS CloudTrail
- B. AWS Security Hub
- C. Amazon CloudWatch
- D. AWS Config

**Correct Answer: B**

**Explanation:** AWS Security Hub provides a centralized security dashboard that aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Firewall Manager, and third-party tools. It checks against security best practices (CIS AWS Foundations Benchmark). CloudTrail logs API calls. CloudWatch monitors metrics. Config tracks configuration changes.

---

### Question 16
A company needs to classify and protect sensitive data (such as PII, credit card numbers) stored in their S3 buckets across multiple accounts.

Which service should the Solutions Architect use?

- A. Amazon GuardDuty
- B. Amazon Macie
- C. AWS Config
- D. Amazon Inspector

**Correct Answer: B**

**Explanation:** Amazon Macie uses machine learning and pattern matching to discover, classify, and protect sensitive data in Amazon S3. It can identify PII, financial data, and other sensitive information. Macie supports multi-account deployment through AWS Organizations. GuardDuty is for threat detection. Config is for configuration compliance. Inspector is for EC2 vulnerability scanning.

---

### Question 17
A web application allows users to upload files to S3. The Solutions Architect needs to ensure that only authenticated users can upload files and that uploads go directly to S3 without passing through the application server.

Which approach should the Solutions Architect use?

- A. IAM user credentials embedded in the client application
- B. S3 presigned POST URLs generated by the application backend
- C. Public S3 bucket with CORS enabled
- D. CloudFront signed URLs with S3 origin

**Correct Answer: B**

**Explanation:** Presigned POST URLs allow the backend to generate a time-limited URL that clients use to upload files directly to S3 without passing through the application server. The URL includes IAM permissions and conditions (file type, size limits). Embedding credentials in clients is insecure. Public buckets are insecure. CloudFront signed URLs are for downloads, not uploads to S3.

---

### Question 18
A company needs to enable cross-account access so that an application in Account A can read from a DynamoDB table in Account B.

Which approach should the Solutions Architect use?

- A. Share IAM user credentials from Account B with Account A
- B. Create an IAM role in Account B with DynamoDB read permissions and allow Account A to assume it
- C. Create a VPC Peering connection between the accounts
- D. Copy the DynamoDB table to Account A using DMS

**Correct Answer: B**

**Explanation:** Cross-account IAM roles are the standard way to grant cross-account access. Account B creates a role with DynamoDB read permissions and a trust policy allowing Account A to assume it. The application in Account A uses STS AssumeRole to get temporary credentials. Sharing credentials is insecure. VPC Peering doesn't grant resource-level permissions. Copying data is not access management.

---

### Question 19
A company wants to ensure that all EBS volumes across all Regions in their account are encrypted by default.

What should the Solutions Architect do?

- A. Create an SCP to deny creating unencrypted EBS volumes
- B. Enable EBS encryption by default in each Region via the EC2 settings
- C. Use AWS Config to detect unencrypted volumes
- D. Both A and B

**Correct Answer: D**

**Explanation:** Enabling EBS encryption by default ensures all new EBS volumes are automatically encrypted (preventive control in each Region). Adding an SCP provides an organizational guardrail that prevents anyone from disabling the setting or bypassing it. AWS Config can detect but not prevent unencrypted volumes. Using both provides defense-in-depth.

---

### Question 20
A company needs to manage TLS/SSL certificates for their applications running behind ALBs across multiple Regions. The certificates should be automatically renewed.

Which service should the Solutions Architect use?

- A. AWS Certificate Manager (ACM)
- B. IAM SSL Certificate Store
- C. Self-managed certificates on EC2 instances
- D. Third-party certificate authority only

**Correct Answer: A**

**Explanation:** AWS Certificate Manager (ACM) provides free, automatically renewed SSL/TLS certificates that integrate with ALB, CloudFront, and API Gateway. ACM handles certificate provisioning, deployment, and renewal automatically. The IAM certificate store is legacy and doesn't auto-renew. Self-managed certificates require manual renewal.

---

### Question 21
A company needs to implement a solution where API calls can only be made from within the corporate network. The APIs are hosted on API Gateway.

Which approach provides the MOST secure solution?

- A. API Gateway with API keys
- B. API Gateway with resource policy restricting to VPC endpoint
- C. API Gateway with IAM authentication and IP condition
- D. API Gateway with Lambda authorizer checking source IP

**Correct Answer: B**

**Explanation:** A private API Gateway accessible only through a VPC endpoint, combined with a resource policy that restricts access to the VPC endpoint, ensures API calls can only be made from within the VPC (connected to the corporate network via VPN/Direct Connect). API keys are not security controls (they're for throttling). IAM with IP conditions can work but is less secure than VPC endpoint restriction.

---

### Question 22
A company wants to implement multi-factor authentication (MFA) for deleting objects from a critical S3 bucket.

Which feature should the Solutions Architect enable?

- A. S3 Object Lock
- B. MFA Delete on the S3 bucket
- C. IAM policy with MFA condition
- D. S3 bucket policy with MFA condition

**Correct Answer: B**

**Explanation:** MFA Delete requires two forms of authentication for permanently deleting object versions or changing the versioning state. When enabled, MFA Delete adds an extra layer of protection. Only the root account can enable/disable MFA Delete. Object Lock prevents deletion entirely. IAM policies with MFA conditions can enforce MFA for operations but MFA Delete is the specific S3 feature for this use case.

---

### Question 23
A company's application needs to assume an IAM role in another AWS account to access resources. The application runs on EC2 instances.

Which STS API should the application use?

- A. GetSessionToken
- B. AssumeRole
- C. GetFederationToken
- D. AssumeRoleWithWebIdentity

**Correct Answer: B**

**Explanation:** `AssumeRole` is used when an IAM entity (user, role, or service) needs to assume a role in the same or different account. It returns temporary security credentials. `GetSessionToken` is for MFA-enhanced sessions. `GetFederationToken` creates temporary credentials for federated users. `AssumeRoleWithWebIdentity` is for web identity federation (Google, Facebook, Amazon).

---

### Question 24
A company wants to ensure compliance by denying access to all AWS services except EC2, S3, and RDS in their development accounts.

Which approach should the Solutions Architect use in AWS Organizations?

- A. IAM policy in each account allowing only EC2, S3, RDS
- B. SCP with an Allow list for EC2, S3, RDS and implicit deny for everything else
- C. AWS Config Rule for detecting usage of other services
- D. AWS CloudWatch alerts for unauthorized service usage

**Correct Answer: B**

**Explanation:** SCPs can be configured as an allow list (explicitly allowing only specific services and denying everything else). This ensures that even if individual IAM policies grant broader permissions, users cannot use services not on the SCP allow list. SCPs don't grant permissions — they set the maximum possible permissions. IAM policies can be overridden by users with admin access.

---

### Question 25
A company wants to centrally manage and rotate secrets (database passwords, API keys) used by applications running in Amazon ECS containers.

Which solution should the Solutions Architect implement?

- A. Store secrets in environment variables in the task definition
- B. Store secrets in S3 and reference them in the task definition
- C. Use AWS Secrets Manager and reference secrets in the ECS task definition
- D. Use IAM roles for the container

**Correct Answer: C**

**Explanation:** AWS Secrets Manager integrates natively with ECS. Secrets can be referenced in the task definition, and ECS automatically retrieves them at container startup. Secrets Manager also provides automatic rotation. Environment variables are visible in the task definition (insecure). S3 storage requires custom retrieval logic. IAM roles manage permissions, not secrets.

---

## Quick Reference: IAM Policy Evaluation Logic

```
1. Explicit DENY → DENY (always wins)
2. SCP evaluation → Must ALLOW (if using Organizations)
3. Resource-based policy → If ALLOW, grant access
4. Identity-based policy → Must ALLOW
5. Permission boundary → Must ALLOW
6. Session policy → Must ALLOW
7. If no explicit ALLOW → DENY (implicit deny)
```

## Quick Reference: Encryption Options

| Method | Key Management | Use Case |
|--------|---------------|----------|
| SSE-S3 | AWS manages keys | Simple encryption, no audit |
| SSE-KMS | Customer manages via KMS | Audit trail, key rotation, fine-grained access |
| SSE-C | Customer provides key each request | Full key control, keys stored outside AWS |
| Client-Side | Customer encrypts before upload | Highest control, end-to-end encryption |

## Quick Reference: Security Services Cheat Sheet

| Service | Purpose |
|---------|---------|
| IAM | Authentication & Authorization |
| KMS | Encryption key management |
| CloudHSM | Dedicated HSM for crypto operations |
| Secrets Manager | Secret storage with auto-rotation |
| Parameter Store | Configuration/secret storage (simpler) |
| Cognito | User authentication for web/mobile apps |
| GuardDuty | Threat detection (ML-based) |
| Inspector | Vulnerability scanning (EC2/ECR) |
| Macie | Sensitive data discovery (S3) |
| Shield | DDoS protection |
| WAF | Web application firewall |
| Security Hub | Centralized security findings |
| ACM | TLS/SSL certificate management |
| Config | Configuration compliance tracking |
