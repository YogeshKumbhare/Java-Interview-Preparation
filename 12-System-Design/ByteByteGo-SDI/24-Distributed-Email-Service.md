# Chapter 24: Distributed Email Service

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/distributed-email-service)

Design a distributed email service like Gmail, Outlook, or Yahoo Mail.

---

## Step 1 - Understand the problem and establish design scope

**Features:** Send/receive emails, search emails, mark as read/unread, anti-spam/virus filtering, support attachments.

**Non-functional:** Reliability (no lost emails), availability, scalability (1 billion users), low latency (email listing < 1s).

**Estimations:** 1 billion users, average 40 emails/day received, average email size 50 KB, metadata per email: 200 bytes, storage/day: 1B * 40 * 50KB = 2 PB/day.

---

## Step 2 - High-level design

### Email protocols

| Protocol | Direction | Description |
|----------|-----------|-------------|
| SMTP | Sending | Simple Mail Transfer Protocol, standard for sending |
| IMAP | Receiving | Internet Message Access Protocol, sync across devices |
| POP3 | Receiving | Post Office Protocol, downloads and deletes from server |

### Send email flow
1. User composes email via web/mobile client
2. Client sends to web server via HTTP
3. Web server validates and forwards to outgoing queue
4. SMTP outgoing workers pick up and send via SMTP
5. Recipient's mail server receives and stores

### Receive email flow
1. External sender's SMTP server connects to our SMTP incoming server
2. Email goes through spam/virus filter
3. If passes, stored in mail storage
4. Real-time notification pushed to recipient's client (WebSocket)
5. Client fetches via IMAP or web API

### Java Example – Email Service Core

```java
import java.util.*;
import java.util.concurrent.*;
import java.time.*;

public class EmailService {
    record Email(String id, String from, String to, String subject,
                 String body, Instant timestamp, boolean read, String folder) {}

    private final Map<String, List<Email>> mailboxes = new ConcurrentHashMap<>();
    private final Queue<Email> outgoingQueue = new ConcurrentLinkedQueue<>();

    public void sendEmail(String from, String to, String subject, String body) {
        String id = UUID.randomUUID().toString().substring(0, 8);
        Email email = new Email(id, from, to, subject, body, Instant.now(), false, "INBOX");

        // Add to sender's SENT folder
        mailboxes.computeIfAbsent(from, k -> new CopyOnWriteArrayList<>())
                 .add(new Email(id, from, to, subject, body, Instant.now(), true, "SENT"));

        // Queue for delivery
        outgoingQueue.offer(email);
        processOutgoing();

        System.out.printf("📧 Email sent: %s → %s [%s]%n", from, to, subject);
    }

    private void processOutgoing() {
        Email email;
        while ((email = outgoingQueue.poll()) != null) {
            // Spam filter (simplified)
            if (!isSpam(email)) {
                mailboxes.computeIfAbsent(email.to(), k -> new CopyOnWriteArrayList<>())
                         .add(email);
            }
        }
    }

    private boolean isSpam(Email email) {
        return email.subject().toLowerCase().contains("free money");
    }

    public List<Email> getInbox(String userId) {
        return mailboxes.getOrDefault(userId, List.of()).stream()
            .filter(e -> "INBOX".equals(e.folder()))
            .sorted(Comparator.comparing(Email::timestamp).reversed())
            .toList();
    }

    public List<Email> searchEmails(String userId, String keyword) {
        return mailboxes.getOrDefault(userId, List.of()).stream()
            .filter(e -> e.subject().toLowerCase().contains(keyword.toLowerCase())
                      || e.body().toLowerCase().contains(keyword.toLowerCase()))
            .toList();
    }

    public static void main(String[] args) {
        EmailService service = new EmailService();
        service.sendEmail("alice@mail.com", "bob@mail.com", "Meeting Tomorrow", "Let's meet at 10am");
        service.sendEmail("charlie@mail.com", "bob@mail.com", "Project Update", "Phase 2 is complete");
        service.sendEmail("spam@evil.com", "bob@mail.com", "Free Money!!!", "Click here!");

        System.out.println("\nBob's Inbox:");
        service.getInbox("bob@mail.com").forEach(e ->
            System.out.printf("  From: %s | Subject: %s%n", e.from(), e.subject()));
    }
}
```

---

## Step 3 - Design deep dive

### Email storage
- Previously: local file-per-email on disk, accessed via IMAP
- Modern: Distributed storage systems (BlobStore for attachments, NoSQL for metadata)
- Search index (Elasticsearch) for full-text email search

### Conversation threading
- Group emails by `In-Reply-To` and `References` headers
- Display as conversation threads

### Search
- Build an inverted index on email body, subject, sender, labels
- Near real-time indexing pipeline: new email → Kafka → index builder → Elasticsearch

### Deliverability
- **SPF, DKIM, DMARC**: Authentication mechanisms to prevent spoofing
- **IP warm-up**: Gradually increase sending volume from new IPs
- **Bounce handling**: Remove invalid addresses
- **Dedicated IP**: Separate IPs for transactional vs marketing emails

---

## Step 4 - Wrap up

Additional talking points:
- **PGP / S/MIME encryption**
- **Calendar integration**
- **Offline support**
- **Email threading and labels**
