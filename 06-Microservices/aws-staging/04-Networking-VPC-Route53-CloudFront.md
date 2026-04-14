# AWS SAA Exam - Networking (VPC, Route 53, CloudFront, ELB)

> **Domain Coverage:** Design Secure Architectures, Design High-Performing Architectures, Design Resilient Architectures
> **Services:** VPC, Subnets, Route Tables, Security Groups, NACLs, NAT Gateway, Internet Gateway, VPN, Direct Connect, Route 53, CloudFront, ALB, NLB, GLB, API Gateway, Transit Gateway, VPC Peering, PrivateLink

---

## Questions & Answers

### Question 1
A company with an existing AWS VPC is experiencing an increasing number of malicious attacks from a particular IP address range. The company wants to block all access from these IP addresses while the abuse patterns are being investigated.

How can access from the specified IPs be denied quickly and temporarily?

- A. Use an AWS Marketplace solution to block access from the specified IP range.
- B. Leverage NAT gateway on each instance to block access from the specified IP range.
- C. Use network ACLs to block access from the specified IP range.
- D. Create a rule in the security groups to block access from the specified IP range.

**Correct Answer: C**

**Explanation:** Network ACLs (NACLs) support both ALLOW and DENY rules and are applied at the subnet level. They can be updated quickly to block specific IP ranges. Security Groups only support ALLOW rules — they cannot explicitly deny traffic. NAT Gateways don't block IP addresses. NACLs are the fastest way to implement temporary IP-based blocking.

---

### Question 2
A company has a three-tier web application running in a VPC. The web tier is in a public subnet, the application tier is in a private subnet, and the database tier is in another private subnet. The application tier needs to download patches from the internet.

Which solution allows the application tier to access the internet while remaining inaccessible from the internet?

- A. Attach an Internet Gateway to the private subnet
- B. Deploy a NAT Gateway in the public subnet and update the private subnet route table
- C. Use a bastion host in the public subnet
- D. Move the application tier to the public subnet

**Correct Answer: B**

**Explanation:** A NAT Gateway in the public subnet allows instances in private subnets to initiate outbound internet connections (e.g., for patches) while preventing inbound connections from the internet. The private subnet route table needs a route to 0.0.0.0/0 pointing to the NAT Gateway. Internet Gateways provide bidirectional internet access. Bastion hosts are for SSH access.

---

### Question 3
A company runs a web application that serves customers globally. The application is hosted in us-east-1. Users in Asia-Pacific experience high latency.

Which combination of services should the Solutions Architect use to reduce latency? (Select TWO)

- A. Amazon CloudFront with the ALB as origin
- B. Amazon Route 53 with simple routing
- C. AWS Global Accelerator
- D. VPC Peering between Regions
- E. S3 Cross-Region Replication

**Correct Answer: A, C**

**Explanation:** CloudFront caches static content at edge locations globally, reducing latency. Global Accelerator routes dynamic traffic through the AWS global network (instead of the public internet) to the optimal endpoint, reducing latency for dynamic content. Route 53 simple routing doesn't solve latency. VPC Peering connects VPCs, not end users. S3 CRR only helps with S3 data.

---

### Question 4
A company needs to connect their on-premises data center to their AWS VPC with a dedicated, private connection that provides consistent network performance. The connection must be encrypted.

Which solution meets these requirements?

- A. AWS Site-to-Site VPN
- B. AWS Direct Connect
- C. AWS Direct Connect with VPN overlay
- D. VPC Peering

**Correct Answer: C**

**Explanation:** Direct Connect provides a dedicated, private connection with consistent performance (not encrypted by default). Adding a VPN overlay on top of Direct Connect provides encryption (IPsec). Direct Connect alone is not encrypted. Site-to-Site VPN goes over the public internet (not dedicated). VPC Peering is for connecting VPCs within AWS.

---

### Question 5
A company must host an application that uses a domain name. The company wants to route traffic based on the geographic location of the user to comply with data sovereignty requirements.

Which Route 53 routing policy should the Solutions Architect use?

- A. Latency-based routing
- B. Geolocation routing
- C. Weighted routing
- D. Failover routing

**Correct Answer: B**

**Explanation:** Geolocation routing lets you route traffic based on the geographic location of the user (continent, country, or state). This is ideal for data sovereignty requirements where users in specific regions must be routed to servers in those regions. Latency-based routing picks the lowest latency endpoint, which may not comply with data sovereignty. Weighted routing distributes traffic by ratio. Failover is for DR.

---

### Question 6
A company has a VPC with a public subnet and a private subnet. An EC2 instance in the public subnet needs to communicate with an RDS instance in the private subnet on port 3306.

What is the MINIMUM change required to allow this communication?

- A. Create a VPC Peering connection between the subnets
- B. Update the RDS Security Group to allow inbound port 3306 from the EC2 instance's Security Group
- C. Create a new NACL allowing port 3306
- D. Add a NAT Gateway

**Correct Answer: B**

**Explanation:** Security Groups are stateful — you only need to allow the inbound rule. Allowing inbound on port 3306 from the EC2 security group is the minimum change. VPC Peering is for connecting different VPCs, not subnets in the same VPC. NACLs have default rules that allow all traffic within the VPC. NAT Gateway is for outbound internet access from private subnets.

---

### Question 7
A company runs an application behind an Application Load Balancer (ALB). The application is deployed in a single Availability Zone. The company wants to ensure the application remains available if that AZ fails.

Which steps should the Solutions Architect take? (Select TWO)

- A. Enable cross-zone load balancing on the ALB
- B. Deploy EC2 instances in multiple AZs
- C. Use Route 53 failover routing
- D. Register the new AZ subnets with the ALB
- E. Use a Network Load Balancer instead

**Correct Answer: B, D**

**Explanation:** To survive AZ failures: (1) Deploy instances in multiple AZs so there are healthy targets if one AZ fails. (2) Register subnets from those AZs with the ALB so it can route traffic to all AZs. Cross-zone load balancing distributes traffic evenly but doesn't help if instances only exist in one AZ. Route 53 failover helps but doesn't solve the single AZ issue.

---

### Question 8
A company needs to expose an internal REST API to specific partner companies without making it publicly accessible. The partners have AWS accounts.

Which approach should the Solutions Architect use?

- A. API Gateway with IAM authentication
- B. AWS PrivateLink with VPC Endpoint Service
- C. VPC Peering with the partner accounts
- D. API Gateway with a public endpoint and IP whitelisting

**Correct Answer: B**

**Explanation:** AWS PrivateLink allows you to expose services privately to other AWS accounts through VPC endpoints. Traffic stays within the AWS network and never traverses the internet. This is the most secure way to share services between accounts. VPC Peering exposes the entire VPC. API Gateway with public endpoint is less secure. PrivateLink provides granular control.

---

### Question 9
A company is designing a multi-VPC architecture. They have 10 VPCs that need to communicate with each other and with their on-premises network.

Which networking solution provides the SIMPLEST architecture?

- A. VPC Peering between all VPCs (full mesh)
- B. AWS Transit Gateway
- C. VPN connections between all VPCs
- D. AWS Direct Connect to each VPC

**Correct Answer: B**

**Explanation:** AWS Transit Gateway acts as a hub-and-spoke network, connecting multiple VPCs and on-premises networks through a single gateway. With 10 VPCs, full-mesh VPC Peering would require 45 connections (n*(n-1)/2). Transit Gateway simplifies this to 10 attachments. It also supports VPN and Direct Connect attachments for on-premises connectivity.

---

### Question 10
A company needs to distribute incoming application traffic across targets in multiple Availability Zones. The application uses HTTP and requires path-based routing to route requests to different microservices.

Which load balancer should the Solutions Architect use?

- A. Classic Load Balancer
- B. Application Load Balancer (ALB)
- C. Network Load Balancer (NLB)
- D. Gateway Load Balancer (GWLB)

**Correct Answer: B**

**Explanation:** ALB operates at Layer 7 (HTTP/HTTPS) and supports path-based routing (e.g., /api/* → Service A, /images/* → Service B). It also supports host-based routing, HTTP header routing, and query string routing. NLB is Layer 4 (TCP/UDP) and doesn't support path-based routing. GWLB is for third-party virtual appliances.

---

### Question 11
A company needs to set up DNS failover so that if the primary web application becomes unhealthy, traffic is automatically routed to a static S3-hosted maintenance page.

Which Route 53 configuration should the Solutions Architect use?

- A. Weighted routing with health checks
- B. Failover routing with health checks
- C. Simple routing with health checks
- D. Latency-based routing with health checks

**Correct Answer: B**

**Explanation:** Route 53 failover routing allows you to configure a primary and secondary (failover) record. Health checks monitor the primary endpoint. If the primary fails the health check, Route 53 automatically routes traffic to the secondary (the S3 maintenance page). This is the standard active-passive failover pattern.

---

### Question 12
A financial services company needs to process millions of TCP connections per second with ultra-low latency. The company also needs to preserve the source IP address of clients.

Which load balancer should the Solutions Architect use?

- A. Application Load Balancer
- B. Network Load Balancer
- C. Classic Load Balancer
- D. Gateway Load Balancer

**Correct Answer: B**

**Explanation:** NLB operates at Layer 4 (TCP/UDP) and can handle millions of requests per second with ultra-low latency (~100 microseconds). NLB preserves the source IP address by default. ALB adds its own IP (source IP is in X-Forwarded-For header). NLB supports static IP addresses and Elastic IPs, which is important for financial services with allowlists.

---

### Question 13
A company has a VPC with CIDR block 10.0.0.0/16. The company wants to connect this VPC to another VPC with CIDR block 10.0.0.0/16 in a different account.

Can VPC Peering be used?

- A. Yes, VPC Peering supports overlapping CIDR blocks
- B. No, VPC Peering does not support overlapping CIDR blocks
- C. Yes, but only with Transit Gateway
- D. Yes, but only if they are in different Regions

**Correct Answer: B**

**Explanation:** VPC Peering does not support overlapping CIDR blocks. If two VPCs have identical or overlapping CIDR ranges, peering cannot be established. The solution would be to restructure one VPC's CIDR or use other connectivity options like PrivateLink for specific services.

---

### Question 14
A company wants to serve a static website from an S3 bucket. The website should be accessible via HTTPS with a custom domain name. The company wants the LOWEST cost solution.

Which architecture should the Solutions Architect use?

- A. S3 bucket with website hosting enabled + Route 53 alias record
- B. S3 bucket + CloudFront distribution with ACM certificate + Route 53 alias record
- C. S3 bucket + ALB + EC2 instance with SSL certificate
- D. S3 bucket + API Gateway with custom domain

**Correct Answer: B**

**Explanation:** S3 static website hosting doesn't support HTTPS natively. CloudFront provides HTTPS with a free ACM (AWS Certificate Manager) certificate. Route 53 alias record points the custom domain to CloudFront. This is the lowest cost approach for static websites with HTTPS. ALB + EC2 is more expensive. S3 alone can't serve HTTPS with custom domains.

---

### Question 15
A company has two VPCs: VPC-A peered with VPC-B, and VPC-B peered with VPC-C. Resources in VPC-A need to access resources in VPC-C.

What should the Solutions Architect do?

- A. VPC Peering supports transitive routing, no changes needed
- B. Create a direct VPC Peering connection between VPC-A and VPC-C
- C. Use Transit Gateway to connect all three VPCs
- D. Both B and C work

**Correct Answer: D**

**Explanation:** VPC Peering does NOT support transitive routing. Traffic from VPC-A cannot reach VPC-C through VPC-B. Two solutions: (1) Create a direct peering between VPC-A and VPC-C. (2) Use Transit Gateway which acts as a hub for all VPCs. Both options work. Transit Gateway is better for many VPCs; direct peering is simpler for a few.

---

### Question 16
A Solutions Architect needs to design a VPC architecture where web servers are accessible from the internet but database servers are not. Both tiers need to communicate with each other.

Which architecture should be implemented?

- A. Web servers and database servers in a public subnet with Security Groups
- B. Web servers in a public subnet, database servers in a private subnet
- C. All servers in a private subnet with a NAT Gateway
- D. All servers in a public subnet with NACLs to restrict database access

**Correct Answer: B**

**Explanation:** This is the standard multi-tier VPC architecture: web servers in a public subnet (with Internet Gateway access) and database servers in a private subnet (no direct internet access). Security Groups allow communication between tiers. Placing databases in a public subnet is a security risk. NACLs alone are insufficient for proper network segregation.

---

### Question 17
A company is using Amazon CloudFront to serve a web application. They want to restrict access to the S3 origin so that users can only access content through CloudFront, not directly from S3.

Which feature should the Solutions Architect configure?

- A. S3 bucket policy with IP restriction
- B. CloudFront Origin Access Control (OAC)
- C. S3 presigned URLs
- D. CloudFront signed URLs

**Correct Answer: B**

**Explanation:** Origin Access Control (OAC) restricts access to the S3 origin so that content can only be retrieved through the CloudFront distribution. OAC replaces the legacy Origin Access Identity (OAI). The S3 bucket policy is updated to only allow the CloudFront distribution to access the objects. Presigned URLs and signed URLs serve different purposes (time-limited access to specific objects).

---

### Question 18
A company needs to register a new domain name and configure DNS for their application. The application runs on EC2 instances behind an ALB.

Which Route 53 record type should the Solutions Architect create to point the domain to the ALB?

- A. A record (Alias) pointing to the ALB
- B. CNAME record pointing to the ALB DNS name
- C. MX record pointing to the ALB
- D. A record with the ALB's IP address

**Correct Answer: A**

**Explanation:** An Alias A record points a domain name directly to an AWS resource (like an ALB). Alias records are free for Route 53 queries and resolve at the DNS level. CNAME records work but cannot be used at the zone apex (root domain) and incur DNS lookup charges. ALBs don't have static IP addresses, so a regular A record won't work.

---

### Question 19
A company needs a connection between their on-premises data center and AWS VPC. The connection must be established quickly (within days) and encrypted. Bandwidth requirements are moderate.

Which solution should the Solutions Architect recommend?

- A. AWS Direct Connect
- B. AWS Site-to-Site VPN
- C. AWS VPN CloudHub
- D. AWS Transit Gateway with VPN

**Correct Answer: B**

**Explanation:** AWS Site-to-Site VPN can be set up within minutes to hours — much faster than Direct Connect (which takes weeks to months to provision). VPN traffic is encrypted using IPsec. For moderate bandwidth needs, VPN provides a cost-effective and quick solution. Direct Connect provides better performance but takes much longer to establish.

---

### Question 20
A company has an application that receives traffic from mobile clients worldwide. The application requires static IP addresses for client whitelisting purposes. The application backend runs on EC2 instances in multiple AZs.

Which load balancer should the Solutions Architect use?

- A. Application Load Balancer with Elastic IP
- B. Network Load Balancer with Elastic IPs
- C. Classic Load Balancer
- D. Application Load Balancer with Global Accelerator

**Correct Answer: B**

**Explanation:** NLB supports static IP addresses (one per AZ) and can be assigned Elastic IPs. This is essential for client whitelisting. ALB doesn't support static IPs natively. While Global Accelerator provides static IPs, NLB directly satisfies the requirement. Also, NLB is ideal for high-performance TCP traffic from mobile clients.

---

### Question 21
A company needs to connect 50 branch offices to their AWS VPC. Each branch has its own VPN connection. The company wants centralized management of these VPN connections.

Which service should the Solutions Architect use?

- A. AWS VPN CloudHub
- B. AWS Transit Gateway with VPN attachments
- C. Direct Connect Gateway
- D. VPC Peering with each branch

**Correct Answer: B**

**Explanation:** Transit Gateway supports multiple VPN attachments and provides centralized management. With 50 branches, Transit Gateway scales well and provides a hub-and-spoke architecture. VPN CloudHub allows branch-to-branch communication but is limited in scale. Direct Connect requires physical infrastructure at each branch. VPC Peering doesn't support VPN connections.

---

### Question 22
An application needs to communicate with AWS services (S3, DynamoDB, SNS) from within a VPC without using the internet. The company wants to minimize data transfer costs.

Which combination of VPC endpoints should the Solutions Architect create? (Select TWO)

- A. Gateway Endpoint for S3
- B. Gateway Endpoint for DynamoDB
- C. Interface Endpoint for S3
- D. Interface Endpoint for SNS
- E. NAT Gateway for all services

**Correct Answer: A, B, D**

**Explanation:** Gateway Endpoints are available (and free) for S3 and DynamoDB. Interface Endpoints (powered by PrivateLink) are needed for SNS and other AWS services. Gateway Endpoints are preferable for S3 and DynamoDB as they are free. NAT Gateway routes traffic through the internet and incurs data processing charges.

---

### Question 23
A company is deploying a web application behind an ALB. The ALB must only accept HTTPS traffic (port 443) and redirect any HTTP (port 80) requests to HTTPS.

Which ALB configuration accomplishes this?

- A. Create two listeners: HTTPS on 443 forwarding to target group, HTTP on 80 with redirect action to HTTPS
- B. Only create an HTTPS listener on 443 and block all HTTP traffic
- C. Use Security Groups to block HTTP and allow HTTPS
- D. Configure a WAF rule to redirect HTTP to HTTPS

**Correct Answer: A**

**Explanation:** ALB supports redirect actions on listeners. Create an HTTP listener on port 80 with a redirect action that sends users to the HTTPS version of the URL (port 443). The HTTPS listener on 443 forwards traffic to the target group. Blocking HTTP would cause connection errors for users who type http://. Security Groups can't redirect traffic.

---

### Question 24
A company needs to protect their web application running behind an ALB from common web exploits such as SQL injection and cross-site scripting (XSS).

Which service should the Solutions Architect use?

- A. Amazon GuardDuty
- B. AWS Shield Standard
- C. AWS WAF (Web Application Firewall)
- D. Amazon Inspector

**Correct Answer: C**

**Explanation:** AWS WAF protects web applications from common web exploits including SQL injection, XSS, and other OWASP Top 10 vulnerabilities. WAF can be attached to ALB, CloudFront, and API Gateway. GuardDuty monitors for threats at the account level. Shield protects against DDoS attacks. Inspector scans for vulnerabilities in EC2 instances.

---

### Question 25
A company needs to route traffic to the AWS Region with the lowest latency for the end user. The application is deployed in us-east-1, eu-west-1, and ap-southeast-1.

Which Route 53 routing policy should the Solutions Architect use?

- A. Geolocation routing
- B. Latency-based routing
- C. Weighted routing
- D. Multivalue answer routing

**Correct Answer: B**

**Explanation:** Latency-based routing evaluates the network latency between the end user and each AWS Region, then routes traffic to the Region with the lowest latency. Geolocation routes based on geographic location (continent/country), which doesn't necessarily correspond to lowest latency. Weighted routing distributes by ratio. Multivalue returns multiple values randomly.

---

## Quick Reference: Security Groups vs NACLs

| Feature | Security Groups | NACLs |
|---------|----------------|-------|
| Level | Instance (ENI) | Subnet |
| Rules | Allow only | Allow & Deny |
| State | Stateful | Stateless |
| Processing | All rules evaluated | Rules processed in order |
| Default | Deny all inbound, Allow all outbound | Allow all |
| IP Blocking | Cannot explicitly deny | Can deny specific IPs |

## Quick Reference: Load Balancer Types

| Feature | ALB | NLB | GWLB |
|---------|-----|-----|------|
| Layer | 7 (HTTP/HTTPS) | 4 (TCP/UDP/TLS) | 3 (IP) |
| Path Routing | Yes | No | No |
| WebSocket | Yes | Yes | No |
| Static IP | No (use Global Accelerator) | Yes (Elastic IP) | No |
| Latency | Moderate | Ultra-low (~100µs) | Low |
| Use Case | Web apps, microservices | Gaming, IoT, financial | 3rd party appliances |

## Quick Reference: Route 53 Routing Policies

| Policy | Use Case |
|--------|----------|
| Simple | Single resource, no health checks |
| Weighted | A/B testing, gradual deployment |
| Latency | Best performance for global users |
| Failover | Active-passive DR |
| Geolocation | Data sovereignty, localization |
| Geoproximity | Route to nearest resource with bias |
| Multivalue | Return multiple healthy records |

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
