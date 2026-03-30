# 💬 Design WhatsApp — System Design Interview

> **Source:** [Design WhatsApp w/ a Senior Manager](https://www.youtube.com/watch?v=cr6p0n0N-VA)
> **Full Answer Key:** [hellointerview.com/whatsapp](https://www.hellointerview.com/learn/system-design/answer-keys/whatsapp)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: How Do We Scale to Billions of Users?](#4-deep-dive-1-how-do-we-scale-to-billions-of-users)
5. [Deep Dive 2: Message Delivery Flow (Online & Offline)](#5-deep-dive-2-message-delivery-flow-online--offline)
6. [Deep Dive 3: Handling Multiple Clients Per User](#6-deep-dive-3-handling-multiple-clients-per-user)
7. [Deep Dive 4: Detecting Disconnected Clients](#7-deep-dive-4-detecting-disconnected-clients)
8. [Deep Dive 5: Message Ordering & Gap Detection](#8-deep-dive-5-message-ordering--gap-detection)
9. [Deep Dive 6: Group Messaging Scaling](#9-deep-dive-6-group-messaging-scaling)
10. [What is Expected at Each Level?](#10-what-is-expected-at-each-level)
11. [Interview Tips & Common Questions](#11-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **1:1 Messaging** | Real-time text messaging between two users |
| **Group Chat** | Multi-user chats (limit 100 participants) |
| **Send/Receive While Offline** | Messages stored for up to 30 days |
| **Delivery Receipts** | ✓ sent, ✓✓ delivered, ✓✓ read (blue) |
| **Media Sharing** | Images, videos, documents |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Low Latency** | < 500ms delivery when online | Real-time feel |
| **Reliability** | Zero message loss | Messages are critical |
| **Scalability** | 2B+ users, 100B+ messages/day | Global platform |
| **Privacy** | End-to-end encryption | User trust |

---

## 2. Core Entities & API Design

### Entities
```
User        → id, phone, public_key, last_seen
Chat        → id, type (1:1|group), participants[], created_at
Message     → id, chat_id, sender_id, content, type, timestamp, sequence_num
Inbox       → user_id, message_id, delivered (bool)
Client      → id, user_id, device_type, last_active, websocket_server_id
```

### Protocol Choice: WebSocket
```
Why NOT REST:
  REST = request-response → server can't push messages
  Polling = wasteful (90% of polls return empty)
  Long-polling = okay but connection overhead per message
  
WebSocket = persistent, bi-directional, full-duplex
  → Server pushes messages instantly
  → Low overhead (no HTTP headers per message)
  → Connection persists across multiple messages
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌──────────────────┐
│ Client A  │◄─WS─│ Chat Server 1 │──│    Pub/Sub         │
└──────────┘    └──────┬───────┘    │ (Redis Pub/Sub or  │
                       │            │  Google Cloud Pub/Sub)│
┌──────────┐    ┌──────┴───────┐    └──────────┬─────────┘
│ Client B  │◄─WS─│ Chat Server 2 │             │
└──────────┘    └──────┬───────┘    ┌──────────┴─────────┐
                       │            │   Message DB         │
                       │            │   (Cassandra)        │
                ┌──────┴───────┐    └──────────┬─────────┘
                │  Inbox DB     │              │
                │  (Cassandra)  │    ┌─────────┴──────────┐
                └──────────────┘    │  Push Notification   │
                                    │  Service (APNs/FCM)  │
                                    └────────────────────┘
```

---

## 4. Deep Dive 1: How Do We Scale to Billions of Users?

Each Chat Server holds ~50K WebSocket connections. With 2B users (even 200M concurrent), that's **4,000+ Chat Server instances.**

The problem: User A sends a message to User B. They're on DIFFERENT Chat Servers. How does the message get routed?

### ❌ Bad Solution: Naively Horizontally Scale

```
Each Chat Server knows about all other servers
→ O(N²) connections between servers
→ At 4000 servers, that's 16M inter-server connections
→ Completely unmanageable
```

### ❌ Bad Solution: Kafka Topic Per User

```
Create a Kafka topic for each of 2B users
→ Kafka handles millions of topics poorly
→ Topic creation/deletion overhead
→ Low utilization (most users offline most of the time)
```

### ✅ Good Solution: Consistent Hashing of Chat Servers

```
Hash(user_id) → assigned Chat Server
ZooKeeper maintains the mapping
When user connects → routed to their assigned server
When sending to user B → lookup B's server → direct forward

Challenge: User reconnects → may get different server
→ Need re-routing, session migration
```

### ✅✅ Great Solution: Pub/Sub for Message Routing

```
Architecture:
  1. When User A connects to Chat Server 1:
     → Chat Server 1 subscribes to Pub/Sub topic "user:A"
     
  2. When User C sends a message TO User A:
     → Chat Server (wherever C is) publishes to topic "user:A"
     → Pub/Sub delivers to Chat Server 1 (subscriber)
     → Chat Server 1 pushes to User A via WebSocket

Why this works:
  - Decouples Chat Servers completely
  - No server needs to know about other servers
  - Pub/Sub handles routing transparently
  - Servers can scale independently
```

**Should we partition by chat or by user?**

| Scenario | By Chat | By User |
|----------|---------|---------|
| **1:1 chats (250 chats/user)** | 250 subscriptions per user | 1 subscription per user ✅ |
| **Group (100 participants)** | 1 subscription per user ✅ | Publish to 99 topics per message |

> **Recommendation from the video:** Partition by USER. For 1:1 messaging (the dominant case), each user subscribes to just 1 topic. For groups, the server publishes to each participant's topic.

### The Write Path (Sending a Message)
```
1. Write message to Message Table + create Inbox entries (DURABLE)
2. Return "sent" ACK to sender → ✓
3. Publish to Pub/Sub for real-time delivery (BEST-EFFORT)

Key: Step 1 ensures no message loss. Step 3 is for speed.
If Pub/Sub fails → message is still in Inbox → delivered on next sync.
```

---

## 5. Deep Dive 2: Message Delivery Flow (Online & Offline)

### Online Delivery
```
User A sends "Hi" to User B:
  1. Client A → WebSocket → Chat Server 1
  2. Chat Server 1:
     a. Generate message_id + timestamp + sequence_number
     b. Write to Message table (Cassandra)
     c. Write to Inbox:{User B} (delivery tracking)
     d. ACK to User A → ✓ (sent)
  3. Chat Server 1 → Publish to Pub/Sub topic "user:B"
  4. Chat Server 2 (subscribed to "user:B"):
     → Receives message → pushes via WebSocket to Client B
  5. Client B → ACK back to Chat Server 2 → ✓✓ (delivered)
  6. Chat Server 2 → Update Inbox entry: delivered = true
  7. Forward ✓✓ receipt to User A via Pub/Sub
```

### Offline Delivery
```
User B is OFFLINE (no WebSocket connection):
  1-3: Same as above
  4. No Chat Server has Pub/Sub subscription for "user:B"
     → Message stays in Inbox:{User B}
  5. Push notification sent via APNs/FCM (lightweight alert)
  
When User B comes back online:
  6. Connects to Chat Server → subscribes to "user:B"
  7. Fetches undelivered messages: 
     SELECT * FROM inbox WHERE user_id = B AND delivered = false
  8. Delivers all missed messages → marks as delivered
  9. Sends ✓✓ receipts back for each
```

---

## 6. Deep Dive 3: Handling Multiple Clients Per User

User A has a phone, tablet, and web client. All three need to receive messages.

```
Solution:
  1. Create a Clients table: { client_id, user_id, device_type, last_active }
  2. Inbox becomes per-CLIENT, not per-user:
     inbox:{client_1} → [msg_1, msg_2, ...]
     inbox:{client_2} → [msg_1, msg_2, ...]
  3. When sending message TO User A:
     → Write to Inbox for EACH of A's active clients
  4. Pub/Sub topic stays as "user:A" (unchanged)
     → All Chat Servers with any of A's clients are subscribed
     → All devices receive the push
```

---

## 7. Deep Dive 4: Detecting Disconnected Clients

### ❌ Bad Solution: Rely on TCP Timeouts

```
TCP timeout can take 30+ minutes to detect a dead connection
→ Chat Server thinks client is online for way too long
→ Messages go to Pub/Sub instead of Inbox → lost
```

### ✅ Good Solution: ACK Timeouts with Server-Side Retry

```
Server sends message → waits 5s for ACK
If no ACK → retry once
If still no ACK → assume disconnected → switch to offline mode
```

### ✅✅ Great Solution: Application-Level Heartbeats

```
Client sends heartbeat every 30 seconds:
  → "I'm alive" ping to Chat Server

If Chat Server misses 2 consecutive heartbeats (60s):
  → Mark client as DISCONNECTED
  → Unsubscribe from Pub/Sub
  → Switch to offline delivery (Inbox + push notification)

When client reconnects:
  → Re-subscribe to Pub/Sub
  → Sync missed messages from Inbox
```

---

## 8. Deep Dive 5: Message Ordering & Gap Detection

### The Problem
```
Messages arrive out of order due to network jitter:
  Client receives: msg_3, msg_1, msg_5, msg_2, msg_4
  Should display: msg_1, msg_2, msg_3, msg_4, msg_5
```

### Solution: Sequence Numbers per Chat
```
Each chat has a monotonically increasing sequence counter:
  chat:123 → sequence: 47

When message sent in chat 123:
  sequence = INCR chat:123:sequence → 48
  message.sequence_num = 48

Client-side rendering:
  → Buffer messages in memory
  → Sort by sequence_num before displaying
  → If gap detected (received 46, 48 but not 47):
    → Wait briefly for 47
    → If still missing → request from server: GET /messages?chat=123&seq=47
```

### ✅✅ Great: Piggyback Sequence on Heartbeats
```
Client heartbeat includes: "last received sequence_num for each chat"
Server responds with any messages the client is missing
→ Self-healing gap detection without explicit requests
```

---

## 9. Deep Dive 6: Group Messaging Scaling

### Small Groups (< 100 participants)
```
Fan-out on write:
  User A sends message to group G (50 members):
  1. Persist message once (chat_id = group_G, sender = A)
  2. Write to Inbox for each of 50 members (or their clients)
  3. Publish to Pub/Sub for each member: topic "user:B", "user:C", ...
  
Cost: O(N) per message, where N = group size
  50 members × 100B messages/day = manageable
```

### Why 100 is the limit?
```
At 100 members:
  1 message → 100 Pub/Sub publishes + 100 Inbox writes
  Active group with 1000 msg/day → 100K operations/day per group
  Scales linearly with group size

At 10,000 members (Telegram-scale):
  Need a different model: "channels" with fan-out-on-read
  → Members pull messages when they open the channel
```

---

## 10. What is Expected at Each Level?

### Mid-Level
- WebSocket for real-time messaging
- Basic message storage in database
- Online/offline delivery distinction

### Senior
- Pub/Sub routing between Chat Servers
- Inbox pattern for offline delivery
- Delivery/read receipts flow
- Heartbeat-based disconnect detection
- Group messaging fan-out

### Staff+
- Pub/Sub partition strategy (by user vs by chat)
- Multi-client handling with per-client Inbox
- Sequence number-based ordering with gap detection
- Back-of-envelope: messages/sec, Chat Server capacity
- End-to-end encryption (Signal Protocol mention)
- Consistent hashing alternatives discussion

---

## 11. Interview Tips & Common Questions

### Q: Why Cassandra for messages?
> Write-heavy: 100B+ messages/day. Cassandra: high write throughput, linear scaling, built for time-series/append-only data. Partition by chat_id → all messages for a chat on one node → efficient range scans by timestamp.

### Q: How does end-to-end encryption work?
> Signal Protocol: each user has public-private key pair. Sender encrypts with recipient's public key. Server is a relay — never sees plaintext. Key exchange happens once per conversation. Mention this conceptually but don't deep-dive unless asked.

### Q: How do you handle "typing" indicators?
> Ephemeral — NOT persisted. Send via WebSocket/Pub/Sub to online participants only. Throttle to max once per 3 seconds. If recipient is offline → don't send.

### Q: How do you handle last-seen / online status?
> Update `last_seen` timestamp on heartbeat. Other users query: "is User B's last_seen within 5 minutes?" → show as "online". This is eventually consistent and that's fine.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
