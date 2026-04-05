# Chapter 24: Distributed Email Service

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/distributed-email-service)

In this chapter we design a large-scale email service, such as Gmail, Outlook, or Yahoo Mail. The growth of the internet has led to an explosion in the volume of emails. In 2020, Gmail had over 1.8 billion active users and Outlook had over 400 million users worldwide.

---

## Step 1 - Understand the Problem and Establish Design Scope

**Candidate**: How many people use the product?
**Interviewer**: One billion users.

**Candidate**: I think the following features are important: Authentication, Send and receive emails, Fetch all emails, Filter emails by read and unread status, Search emails by subject, sender, and body, Anti-spam and anti-virus.
**Interviewer**: We don't need to worry about authentication. Let's focus on the other features.

**Candidate**: How do users connect with mail servers?
**Interviewer**: For this interview, let's assume HTTP is used for client and server communication.

**Candidate**: Can emails have attachments?
**Interviewer**: Yes.

**Non-functional requirements:**
- **Reliability**: We should not lose email data.
- **Availability**: Email and user data automatically replicated across multiple nodes.
- **Scalability**: System must handle increasing number of users and emails.
- **Flexibility and extensibility**: A flexible/extensible system allows us to add new features easily.

**Back-of-the-envelope estimation:**
- 1 billion users
- QPS for sending emails: 10^9 × 10 / 10^5 = **100,000**
- Average emails received per day: 40, average metadata size: 50KB
- Metadata storage for 1 year: 1B × 40 × 365 × 50KB = **730 PB**
- 20% emails contain attachments (avg 500KB)
- Attachment storage for 1 year: 1B × 40 × 365 × 20% × 500KB = **1,460 PB**

Need a distributed database solution.

---

## Step 2 - Propose High-Level Design

### Email Knowledge 101

**Email protocols:**
- **SMTP** (Simple Mail Transfer Protocol): Standard for sending emails between servers.
- **POP** (Post Office Protocol): Downloads emails, then deletes from server. Single device access.
- **IMAP** (Internet Mail Access Protocol): Read email from server, remains on server. Multi-device access.
- **HTTPS**: Used for web-based email (Microsoft ActiveSync, webmail).

**DNS MX records**: Used to look up mail exchanger records for recipient's domain. Lower priority number = more preferred.

**Email attachments**: Sent with Base64 encoding. MIME (Multipurpose Internet Mail Extension) allows attachments to be sent over the internet.

### Traditional Mail Servers

1. Alice logs in to Outlook, composes email, presses "send" — sent to Outlook SMTP server
2. Outlook mail server queries DNS for Gmail's SMTP server address
3. Transfers email to Gmail SMTP server
4. Gmail stores email, makes it available to Bob via IMAP/POP

**Storage limitation**: Traditional servers stored emails in local file directories (Maildir format). Disk I/O bottleneck, no high availability.

### Distributed Mail Servers

**Email APIs (RESTful HTTP):**

| Endpoint | Description |
|----------|-------------|
| `POST /v1/messages` | Sends a message to recipients in To, Cc, Bcc |
| `GET /v1/folders` | Returns all folders of an email account |
| `GET /v1/folders/{:folder_id}/messages` | Returns all messages under a folder |
| `GET /v1/messages/{:message_id}` | Gets all info about a specific message |

**Message object response:**
```json
{
  "user_id": "string",
  "from": {"name": "string", "email": "string"},
  "to": [{"name": "string", "email": "string"}],
  "subject": "string",
  "body": "string",
  "is_read": false
}
```

**High-level architecture:**

![Figure 5 – High-level Design](images/ch24/figure-5.png)

Key components:
- **Webmail**: Users use web browsers to receive and send emails.
- **Web servers**: Public-facing services for login, signup, user profile, email operations.
- **Real-time servers**: WebSocket servers for pushing new emails to clients in real-time. Falls back to long polling if WebSocket not available.
- **Metadata database**: Stores email metadata (subject, body, sender, recipients). Cassandra-like.
- **Attachment store**: Amazon S3 (up to 25MB per email).
- **Distributed cache**: Redis for caching recent emails.
- **Search store**: Distributed document store with inverted index for full-text search.

### Email Sending Flow

![Figure 6 – Email Sending Flow](images/ch24/figure-6.png)

1. User writes email → request to load balancer
2. Load balancer rate limits → routes to web servers
3. Web servers validate email (size limit, same-domain check)
4. Email passes validation → put in outgoing queue (in attachment store if attachment too large)
5. Email fails validation → put in error queue
6. SMTP outgoing workers pull from outgoing queue → check spam/virus
7. Email stored in "Sent Folder"
8. SMTP outgoing workers send to recipient mail server

Monitor outgoing queue size. If stuck:
- Recipient mail server unavailable → retry with exponential backoff
- Not enough consumers → add more consumers

### Email Receiving Flow

![Figure 7 – Email Receiving Flow](images/ch24/figure-7.png)

1. Incoming emails arrive at SMTP load balancer
2. Load balancer distributes traffic; bounces invalid emails
3. Large attachments → stored in S3 first
4. Emails put in incoming email queue
5. Mail processing workers filter spam, check viruses
6. Email stored in mail storage, cache, and object data store
7. If receiver online → email pushed to real-time WebSocket servers
8. For offline users → email stored in storage layer

---

## Step 3 - Design Deep Dive

### Metadata Database

**Characteristics of email metadata:**
- Email headers: small and frequently accessed
- Email body: can be large, infrequently accessed
- Operations isolated to individual users
- 82% of read queries for data younger than 16 days
- Data has high-reliability requirements

**Database choice considerations:**
- Relational DB (MySQL/PostgreSQL): Not ideal for large unstructured BLOB data
- Distributed object storage (S3): Hard to support mark-as-read, threading, search
- NoSQL (Bigtable, Cassandra): Google Bigtable used by Gmail

**Database characteristics required:**
- Single column can be single-digit MB
- Strong data consistency
- Designed to reduce disk I/O
- Highly available and fault-tolerant
- Easy incremental backups

**Data model:**
- Partition key: `user_id` (all user data on single shard)
- Clustering key: `email_id` (TIMEUUID — sorts chronologically)

**Key queries:**

Query 1: Get all folders for a user
```sql
-- Table: folders_by_user (partition key: user_id)
```

Query 2: Display all emails for a specific folder
```sql
-- Table: emails_by_folder (partition key: <user_id, folder_id>, clustering key: email_id TIMEUUID)
```

Query 3: Create/delete/get specific email
```sql
SELECT * FROM emails_by_user WHERE email_id = 123;
```

Query 4: Fetch read/unread emails
- Denormalize into two tables: `read_emails` and `unread_emails`
- Moving UNREAD → READ: delete from `unread_emails`, insert into `read_emails`

**Bonus: Conversation threads** using JWZ algorithm:
```json
{
  "headers": {
    "Message-Id": "<7BA04B2A-430C-4D12-8B57-862103C34501@gmail.com>",
    "In-Reply-To": "<CAEWTXuPfN=LzECjDJtgY9Vu03kgFvJnJUSHTt6TW@gmail.com>",
    "References": ["<7BA04B2A-430C-4D12-8B57-862103C34501@gmail.com>"]
  }
}
```

**Consistency trade-off**: Single primary per mailbox. During failover, mailbox inaccessible. Trades availability for consistency.

### Email Deliverability

Over 50% of all emails sent are spam. Key techniques:

- **Dedicated IPs**: New IP addresses have no history; email providers are less likely to accept.
- **Classify emails**: Send marketing and transactional emails from different IPs.
- **Warm up IPs**: Takes 2-6 weeks to build reputation (Amazon SES).
- **Ban spammers quickly**: Prevent reputation damage.
- **Feedback processing**:
  - **Hard bounce**: Recipient email address invalid → don't retry
  - **Soft bounce**: Temporary failure (ISP busy) → retry
  - **Complaint**: User clicks "report spam"

![Figure 8 – Feedback Loop](images/ch24/figure-8.png)

- **Email authentication**: SPF, DKIM, DMARC
  - SPF (Sender Policy Framework)
  - DKIM (DomainKeys Identified Mail)
  - DMARC (Domain-based Message Authentication, Reporting and Conformance)

### Search

| Feature | Google Search | Email Search |
|---------|--------------|-------------|
| Scope | Whole internet | User's own mailbox |
| Sorting | Relevance | Time, has attachment, date, read status |
| Accuracy | Eventual (indexing takes time) | Near real-time, must be accurate |

**Option 1: Elasticsearch**
- Partition by `user_id`
- Kafka used to decouple reindexing triggers from actual reindexers
- One of largest Chinese email providers (Tencent QQ Email) uses Elasticsearch

![Figure 10 – Elasticsearch](images/ch24/figure-10.png)

**Option 2: Custom search (LSM tree)**
- Log-Structured Merge-Tree (LSM) optimized for write-heavy workload
- Used by BigTable, Cassandra, RocksDB
- Separate frequently changing data (folders) from stable data (emails)

| Feature | Elasticsearch | Custom Search |
|---------|--------------|---------------|
| Scalability | Scalable to some extent | Easier to optimize for email |
| Complexity | Two systems to maintain | One system |
| Data consistency | Hard (two copies) | One copy |
| Dev effort | Easy to integrate | Significant effort |

### Scalability and Availability

- Most components horizontally scalable (user operations are independent).
- Data replicated across multiple data centers.
- Users communicate with mail server physically closer to them.

![Figure 12 – Multi-data Center](images/ch24/figure-12.png)

### Java Example – Email Service

```java
import java.util.*;
import java.util.concurrent.*;

public class EmailService {

    enum FolderType { INBOX, SENT, DRAFTS, TRASH, SPAM }

    record Email(String messageId, String from, String to, String subject,
                 String body, boolean isRead, long timestamp) {}

    // Simulated database: userId -> folder -> emails
    private final Map<String, Map<FolderType, List<Email>>> db = new ConcurrentHashMap<>();

    public void receiveEmail(String userId, Email email) {
        db.computeIfAbsent(userId, k -> new EnumMap<>(FolderType.class))
          .computeIfAbsent(FolderType.INBOX, k -> new ArrayList<>())
          .add(email);
        System.out.println("Email received for " + userId + ": " + email.subject());
    }

    public List<Email> getFolder(String userId, FolderType folder) {
        return db.getOrDefault(userId, Map.of())
                 .getOrDefault(folder, List.of());
    }

    public void markAsRead(String userId, String messageId) {
        Map<FolderType, List<Email>> userFolders = db.getOrDefault(userId, Map.of());
        for (Map.Entry<FolderType, List<Email>> entry : userFolders.entrySet()) {
            List<Email> emails = entry.getValue();
            for (int i = 0; i < emails.size(); i++) {
                if (emails.get(i).messageId().equals(messageId)) {
                    Email old = emails.get(i);
                    emails.set(i, new Email(old.messageId(), old.from(), old.to(),
                        old.subject(), old.body(), true, old.timestamp()));
                    System.out.println("Marked as read: " + messageId);
                    return;
                }
            }
        }
    }

    public List<Email> search(String userId, String keyword) {
        List<Email> results = new ArrayList<>();
        db.getOrDefault(userId, Map.of()).values().forEach(emails ->
            emails.stream()
                .filter(e -> e.subject().contains(keyword) || e.body().contains(keyword))
                .forEach(results::add));
        return results;
    }

    public static void main(String[] args) {
        EmailService service = new EmailService();
        service.receiveEmail("alice",
            new Email("m1", "bob@example.com", "alice@example.com",
                "Meeting Tomorrow", "Can we meet at 10am?", false, System.currentTimeMillis()));
        service.receiveEmail("alice",
            new Email("m2", "hr@company.com", "alice@example.com",
                "Benefits Update", "Annual benefits review.", false, System.currentTimeMillis()));

        System.out.println("Inbox: " + service.getFolder("alice", FolderType.INBOX).size() + " emails");
        service.markAsRead("alice", "m1");
        System.out.println("Search 'meeting': " + service.search("alice", "meeting").size() + " results");
        System.out.println("Search 'benefits': " + service.search("alice", "benefits").size() + " results");
    }
}
```

---

## Step 4 - Wrap Up

We designed a large-scale email service covering:
- High-level design with multiple components
- Two main flows: email sending and email receiving
- Deep dives: metadata DB design, email deliverability, search, scalability

**Additional considerations:**
- **Fault tolerance**: Handle node failures, network issues, event delays
- **Compliance**: GDPR for PII data in Europe; legal intercept
- **Security**: Phishing protections, safe browsing, confidential mode, encryption
- **Optimization**: Dedup attachments (check S3 before storing duplicates)

---

## Reference materials

[1] Number of Active Gmail Users: https://financesonline.com/number-of-active-gmail-users/
[2] Outlook: https://en.wikipedia.org/wiki/Outlook.com
[3] How Many Emails Are Sent Per Day: https://review42.com/resources/how-many-emails-are-sent-per-day/
[4] RFC 1939 - Post Office Protocol: http://www.faqs.org/rfcs/rfc1939.html
[5] ActiveSync: https://en.wikipedia.org/wiki/ActiveSync
[6] Email attachment: https://en.wikipedia.org/wiki/Email_attachment
[7] MIME: https://en.wikipedia.org/wiki/MIME
[8] Threading: https://en.wikipedia.org/wiki/Conversation_threading
[9] RFC6154: https://datatracker.ietf.org/doc/html/rfc6154
[10] Apache James: https://james.apache.org/
[11] JMAP Subprotocol for WebSocket: https://datatracker.ietf.org/doc/rfc8887/
[12] Cassandra Limitations: https://cwiki.apache.org/confluence/display/CASSANDRA2/CassandraLimitations
[13] Inverted index: https://en.wikipedia.org/wiki/Inverted_index
[14] Exponential backoff: https://en.wikipedia.org/wiki/Exponential_backoff
[15] QQ Email System: https://www.slideshare.net/areyouok/06-qq-5431919
[16] IOPS: https://en.wikipedia.org/wiki/IOPS
[17] UUID and timeuuid types: https://docs.datastax.com/en/cql-oss/3.3/cql/cql_reference/uuid_type_r.html
[18] Message threading: https://www.jwz.org/doc/threading.html
[19] Global spam volume: https://www.statista.com/statistics/420391/spam-email-traffic-share/
[20] Warming up dedicated IP addresses: https://docs.aws.amazon.com/ses/latest/dg/dedicated-ip-warming.html
[21] 2018 Data Breach Investigations Report: https://enterprise.verizon.com/resources/reports/DBIR_2018_Report.pdf
[22] Sender Policy Framework: https://en.wikipedia.org/wiki/Sender_Policy_Framework
[23] DomainKeys Identified Mail: https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail
[24] DMARC: https://dmarc.org/
[25] DB-Engines Ranking: https://db-engines.com/en/ranking/search+engine
[26] Tencent Cloud Elasticsearch: https://www.programmersought.com/article/24097547237/
[27] Log-structured merge-tree: https://en.wikipedia.org/wiki/Log-structured_merge-tree
[28] Microsoft Exchange Conference 2014 Search: https://www.youtube.com/watch?v=5EXGCSzzQak&t=2173s
[29] GDPR: https://en.wikipedia.org/wiki/General_Data_Protection_Regulation
[30] Lawful interception: https://en.wikipedia.org/wiki/Lawful_interception
[31] Email safety: https://safety.google/intl/en_us/gmail/
