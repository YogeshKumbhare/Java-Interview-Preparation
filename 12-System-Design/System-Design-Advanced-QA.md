# 🏗️ System Design — Advanced Interview Q&A (Part 2)
## Target: 12+ Years Experience | ByteByteGo / Grokking Inspired

> **Note:** This extends System-Design-QA.md with more system designs and foundational concepts.

---

## 📖 System Design Foundations — Must Know Before Any Interview

### CAP Theorem
```
You can only guarantee TWO of three properties in a distributed system:

C - Consistency: Every read returns the most recent write
A - Availability: Every request receives a response (no errors)
P - Partition Tolerance: System works despite network partitions

         C
        / \
       /   \
   CP /     \ CA
     /       \
    P ─────── A
        AP

Real-world choices:
  CP: MongoDB, HBase, Redis (reject writes during partition)
  AP: Cassandra, DynamoDB, CouchDB (serve stale data during partition)
  CA: Traditional RDBMS (single node — no partition to tolerate)

In practice: Partition tolerance is NON-NEGOTIABLE in distributed systems.
So the real choice is: CP vs AP.
```

### Consistent Hashing
```
Problem: Simple hash (key % N servers) breaks when you add/remove servers
         (ALL keys get redistributed!)

Consistent Hashing Solution:
  1. Map servers onto a hash ring (0 to 2³² - 1)
  2. Hash each key → find next server clockwise
  3. Add/remove server? Only K/N keys move (K=total keys, N=servers)

     0
    / \
   S1   S3  ← Servers placed on ring using hash(server_ip)
   |     |
   K1  K2   ← Keys routed to next clockwise server
    \  /
     S2
    360°

Virtual Nodes: Each server gets multiple positions on the ring
               → better load distribution
               → S1 has 150 virtual nodes spread around the ring

Used by: Cassandra, DynamoDB, Redis Cluster, CDNs (Akamai)
```

### Load Balancing Algorithms
```
1. Round Robin: Requests distributed sequentially (S1→S2→S3→S1...)
2. Weighted Round Robin: More requests to powerful servers
3. Least Connections: Route to server with fewest active connections
4. IP Hash: Same client always goes to same server (sticky sessions)
5. Consistent Hashing: For distributed caches (Redis, Memcached)

Layer 4 (TCP): HAProxy, AWS NLB — fast, no content inspection
Layer 7 (HTTP): Nginx, AWS ALB — can route based on URL, headers, cookies
```

### Database Scaling Patterns
```
Vertical Scaling: Bigger machine (more CPU, RAM, SSD)
  + Simple         - Has limits   - Single point of failure

Horizontal Scaling:
  1. Read Replicas: Master → multiple read replicas
     + Easy setup   - Eventually consistent   - Only scales reads

  2. Sharding: Split data across multiple DB instances
     Key-based: hash(user_id) % N → determines which shard
     Range-based: A-M → Shard 1, N-Z → Shard 2
     + Scales writes   - Cross-shard queries are expensive
                       - Hotspot if bad shard key

  3. Database Federation: Split by function
     Users DB, Products DB, Orders DB → different servers
     + Clear boundaries   - Cross-function joins impossible
```

---

## Q6: Design a Chat System (WhatsApp / Slack)

### Requirements:
```
Functional:
- 1:1 messaging with delivery status (sent/delivered/read)
- Group chat (up to 500 members)
- Online/offline presence indicator
- Media sharing (images, files)
- Message history and search

Non-Functional:
- Low latency (<100ms message delivery)
- 500M daily active users
- Messages ordered and never lost
```

### High-Level Architecture:
```
Client (Mobile/Web)
    ↕ WebSocket (persistent connection)
Chat Gateway (manages WebSocket connections)
    ↓
Message Service → Kafka (message queue) → Message Store (Cassandra)
    ↓
Presence Service (Redis) — tracks online/offline
    ↓
Push Notification Service (FCM/APNs) — for offline users
    ↓
Media Service (S3 + CDN) — for images/files
```

### Key Design Decisions:

```java
// WebSocket for real-time bidirectional communication
// NOT HTTP polling — too many wasted requests for 500M users

// Message Storage: Cassandra (not PostgreSQL)
// WHY? Optimized for high write throughput, data is partitioned by chat_id
// Schema:
// PRIMARY KEY (chat_id, message_id)
// message_id = Snowflake ID (timestamp-based, naturally ordered)

// Message Delivery Flow:
// 1. User A sends message → WebSocket → Chat Gateway
// 2. Gateway → Kafka topic (messages)
// 3. Consumer stores in Cassandra
// 4. Consumer checks: Is User B online? (Redis presence)
//    YES → Push via WebSocket to User B's Chat Gateway
//    NO  → Send push notification (FCM/APNs)

// Group Chat Optimization:
// For group of 500 members, DON'T fan-out to 500 Kafka messages
// Instead: Write ONCE to group message table
// Each member's device pulls from group on connect (lazy fan-out)
```

### Presence Service:
```
Redis with key expiry:
  SET user:123:online true EX 30  (expires in 30 seconds)
  Client sends heartbeat every 20 seconds to renew

Online check: EXISTS user:123:online
  true  → green dot
  false → gray dot

For group presence (who's online in a group):
  Redis SET: group:456:online → {user:123, user:789, ...}
```

---

## Q7: Design a Notification System

### Requirements:
```
- Support: Push (mobile), SMS, Email, In-app
- 100M notifications/day
- Personalized templates
- Rate limiting (no spam)
- Delivery tracking + analytics
```

### Architecture:
```
Trigger Sources (Order placed, Payment received, Promo campaign)
    ↓
Notification Service (validates, deduplicates, applies preferences)
    ↓
Priority Queue (Kafka) → High/Medium/Low priority topics
    ↓
Workers (per channel):
├── Push Worker → FCM/APNs
├── SMS Worker → Twilio/AWS SNS
├── Email Worker → SendGrid/SES
└── In-App Worker → WebSocket/SSE

Stores:
├── Template Store (MongoDB) — email/sms templates with {{variables}}
├── User Preferences (PostgreSQL) — opt-in/opt-out per channel
├── Delivery Log (Cassandra) — every notification status
└── Rate Limiter (Redis) — max 3 SMS/hour per user
```

### Key Design Decisions:
```
1. DEDUPLICATION: Hash(event_type + user_id + content) stored in Redis
   with TTL. Prevents sending same notification twice.

2. USER PREFERENCES: User chooses which notifications on which channel
   Marketing emails: opt-in only
   Security alerts: always send, can't opt out

3. RATE LIMITING per user per channel:
   Redis: INCR user:123:sms:count EX 3600
   If count > 3 → queue for later, don't drop

4. RETRY with exponential backoff:
   Attempt 1: immediate
   Attempt 2: 1 minute
   Attempt 3: 5 minutes
   Attempt 4: 30 minutes → move to DLQ

5. TEMPLATE ENGINE:
   "Hi {{user.name}}, your order {{order.id}} has been shipped!"
   Stored in MongoDB, versioned, A/B testable
```

---

## Q8: Design a News Feed (Facebook / Twitter / LinkedIn)

### Architecture:
```
Two approaches:

1. PULL Model (Fan-out on Read):
   User opens feed → system queries all friends' posts → merge + rank → display
   + Simple, works well for users who follow millions
   - Slow for the reader (must query many tables)

2. PUSH Model (Fan-out on Write):
   User posts → system pushes to ALL followers' feed caches
   + Fast reads (pre-computed feed)
   - Celebrity problem: Elon Musk has 100M followers = 100M writes per post!

3. HYBRID (Used by Twitter/Facebook):
   Celebrities (>10K followers): PULL model (query on read)
   Normal users (<10K followers): PUSH model (fan-out on write)
```

### Feed Ranking:
```
Score = f(affinity, recency, content_type, engagement)

Affinity: How close are you to the author?
  - Liked 50 of their posts → high affinity
  - Never interacted → low affinity

Recency: How old is the post?
  - 5 minutes ago → high score
  - 3 days ago → low score

Content Type: Video > Image > Text (engagement-based weighting)

Engagement: Trending posts get boosted
  - 1000 likes in 1 hour → high score

Final feed = Top-K posts by score + pagination (cursor-based, not offset)
```

---

## Q9: Design a Search Autocomplete / Typeahead System

### Architecture:
```
User types "inter" →
  Client sends after 2+ characters, debounce 200ms
    ↓
  API Gateway → Autocomplete Service
    ↓
  Trie (prefix tree) in Redis or in-memory
    ↓
  Returns top 10 suggestions sorted by frequency/recency

Data Pipeline:
  Search logs → Kafka → Analytics → Update Trie hourly

Trie Structure:
  root
   ├── i
   │   └── n
   │       └── t
   │           ├── e
   │           │   ├── r [interview: 50K, internet: 45K, internal: 30K]
   │           │   └── l [intel: 20K, intelligent: 15K]
   │           └── o → [into: 25K]
   └── j
       └── a → v → a [java: 100K, javascript: 80K]
```

### Key Design Decisions:
```
1. TRIE vs Elasticsearch:
   Trie: O(prefix_length) lookup, ultra-fast, fits in memory for top queries
   ES: Full-text search, fuzzy matching, better for long-tail queries
   → Use both: Trie for hot queries, ES fallback for rare queries

2. UPDATE FREQUENCY: Don't update in real-time (too expensive)
   Batch update trie every 15 minutes from search analytics
   Keep top 1000 suggestions per prefix (prune low-frequency)

3. PERSONALIZATION: Blend global popularity with user's search history
   Score = 0.7 × global_freq + 0.3 × user_freq

4. MULTI-LANGUAGE: Separate tries per language
   Detect language from user locale
```

---

## Q10: Design a Distributed Job Scheduler

### Requirements:
```
- Schedule jobs (cron and one-time)
- Exactly-once execution guarantee
- Handle 1M+ scheduled jobs
- Retry failed jobs with backoff
- Monitor job status
```

### Architecture:
```
API Layer → Job definitions stored in PostgreSQL
    ↓
Scheduler Service (Leader election via ZooKeeper/Redis)
    ↓
Job Queue (Redis Sorted Set — score = next_run_timestamp)
    ↓
Worker Pool (Kubernetes pods, auto-scaled)
    ↓
Result Store + Dead Letter Queue

Key: Exactly-once via distributed lock:
  1. Worker tries: SET job:123:lock NX EX 300 (Redis lock)
  2. Only one worker gets the lock → executes the job
  3. On completion: DELETE lock, update status
  4. On timeout: lock expires, another worker can retry
```

---

## 📊 System Design Estimation Cheat Sheet

### Numbers Every Engineer Must Know:
```
L1 cache reference:                    0.5 ns
Main memory reference:                 100 ns
SSD random read:                       16 μs
HDD seek:                             4 ms
Round trip within datacenter:          0.5 ms
Round trip CA → Netherlands:           150 ms

Read 1 MB sequentially:
  Memory:   250 μs
  SSD:      1 ms
  HDD:      20 ms
  Network (1Gbps): 10 ms

1 day = 86,400 seconds ≈ 100K seconds
1M requests/day ≈ 12 requests/second
1B requests/day ≈ 12,000 requests/second

Storage:
  1 byte = 8 bits
  1 char (ASCII) = 1 byte
  1 char (Unicode) = 2-4 bytes
  1 tweet (140 chars + metadata) ≈ 250 bytes
  1 image (compressed) ≈ 300 KB
  1 minute of video (HD) ≈ 50 MB
```

### Back-of-Envelope Template:
```
1. DAU (Daily Active Users): ___
2. Requests per user per day: ___
3. Total requests/day = DAU × requests = ___
4. QPS (Queries Per Second) = total / 86400
5. Peak QPS = QPS × 3 (typically 3x average)
6. Storage per record: ___ bytes
7. Storage per day = records/day × bytes
8. Storage for 5 years = daily × 365 × 5
9. Bandwidth = QPS × record_size
```

---

## 🎯 System Design Cross-Questioning

### Q: "You chose Kafka for messaging. Why not RabbitMQ?"
> **Answer:** "Kafka is a distributed log — messages are retained (days/weeks) and consumers can replay. RabbitMQ is a traditional message broker — messages are deleted after consumption. I chose Kafka because: (1) Event sourcing — we need to replay events for rebuilding read models. (2) Multiple consumer groups can read the same topic independently. (3) Kafka handles 100K+ messages/sec on a single partition. RabbitMQ is better for: task queues with complex routing, lower latency requirements, and when you need message acknowledgment per-message."

### Q: "Your design has a single point of failure at the database. How do you ensure high availability?"
> **Answer:** "Multi-layer HA: (1) Database: Primary + synchronous standby (zero data loss failover). Read replicas for scaling reads. Managed service (AWS RDS Multi-AZ) handles automatic failover. (2) Application: Multiple instances behind a load balancer. Kubernetes ensures pod restart on failure. (3) Cache: Redis Sentinel or Cluster mode — automatic master failover. (4) Message Queue: Kafka with replication factor 3 — survives 2 broker failures. (5) CDN: Content served from edge locations — survives origin failure."
