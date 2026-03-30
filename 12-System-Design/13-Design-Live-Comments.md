# 💬 Design Live Comments — System Design Interview

> **Source:** [Design Live Comments w/ a Staff Engineer](https://www.youtube.com/watch?v=LjLx0fCd1k8)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Real-Time Delivery — Polling vs SSE vs WebSocket](#4-deep-dive-1-real-time-delivery--polling-vs-sse-vs-websocket)
5. [Deep Dive 2: Fan-Out at Scale (Millions of Concurrent Viewers)](#5-deep-dive-2-fan-out-at-scale-millions-of-concurrent-viewers)
6. [Deep Dive 3: Backpressure & Sampling for Viral Streams](#6-deep-dive-3-backpressure--sampling-for-viral-streams)
7. [Deep Dive 4: Comment Ordering & Consistency](#7-deep-dive-4-comment-ordering--consistency)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Post Comment** | Users post comments in real-time on a live stream/post |
| **View Live Comments** | All viewers see comments appear in near real-time |
| **High-Traffic Events** | Millions of concurrent viewers (Super Bowl, World Cup) |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Low Latency** | Comments appear within 1-2 seconds | "Live" feel |
| **Scalability** | 1M+ concurrent viewers per stream | Popular events |
| **Availability** | Graceful degradation under load | Comments can be delayed but don't crash |
| **Ordering** | Best-effort chronological (eventually consistent) | Users see roughly same order |

---

## 2. Core Entities & API Design

### Entities
```
LiveStream → id, title, status (live|ended), start_time
Comment    → id, stream_id, user_id, text, timestamp, sequence_num
```

### API
```
POST   /v1/streams/{id}/comments     → { text } → comment_id
GET    /v1/streams/{id}/comments/live → SSE/WebSocket endpoint for live feed
GET    /v1/streams/{id}/comments?cursor= → Historical comments (paginated)
```

---

## 3. High-Level Architecture

```
┌──────────┐                     ┌───────────────────┐
│ Commenter │───POST────────────│    API Gateway      │
└──────────┘                     └────────┬──────────┘
                                          │
                                 ┌────────┴──────────┐
                                 │  Comment Service    │
                                 └────────┬──────────┘
                                          │
             ┌─────────────┐     ┌────────┴──────────┐
             │ Comments DB  │◄───│    Pub/Sub (Redis   │
             │ (Cassandra)  │     │   or Kafka)        │
             └─────────────┘     └────────┬──────────┘
                                          │
                                 ┌────────┴──────────┐
                                 │ Fan-Out Servers     │
                                 │ (WebSocket/SSE      │
                                 │  connection pool)   │
                                 └────────┬──────────┘
                                          │ SSE/WS
                                 ┌────────┴──────────┐
                                 │    1M+ Viewers      │
                                 └───────────────────┘
```

---

## 4. Deep Dive 1: Real-Time Delivery — Polling vs SSE vs WebSocket

### ❌ Short Polling
```
Client polls every 1 second: GET /comments?since=last_timestamp
→ 1M viewers × 1 request/sec = 1M requests/second → overkill
→ Most polls return empty (no new comments in 1 sec)
→ 1-second worst-case delay
```

### ✅ Long Polling
```
Server holds request open until new comment arrives, then responds.
→ Reduces empty responses
→ But: connection overhead per response (HTTP handshake each time)
→ Hard to scale with persistent connections
```

### ✅✅ Server-Sent Events (SSE) — Recommended
```
Client: const eventSource = new EventSource('/streams/123/comments/live');
Server: keeps connection open, pushes new comments as they arrive

event: comment
data: {"id":"c-456","user":"Alice","text":"Goal!!","timestamp":1711814400}

event: comment
data: {"id":"c-457","user":"Bob","text":"What a finish!","timestamp":1711814401}

Why SSE over WebSocket for this use case:
  → Unidirectional: only server → client (no client input needed on this channel)
  → Built-in reconnection: browser auto-reconnects with Last-Event-ID
  → Works over HTTP/2: multiplexed, efficient
  → Simpler than WebSocket (no upgrade handshake)
  → Posting comments uses regular POST (separate)
```

### WebSocket — Also Viable
```
If bidirectional is needed (e.g., reactions, typing indicators):
  → WebSocket provides full duplex
  → More complex but more flexible
  → Use when live comments include interactive features
```

---

## 5. Deep Dive 2: Fan-Out at Scale (Millions of Concurrent Viewers)

### The Problem
```
1 comment posted → needs to reach 1M viewers → 1M pushes
This is the hardest part: the FAN-OUT.
```

### Architecture: Tiered Fan-Out

```
Tier 1: Comment Service → Pub/Sub (1 publish)
  Comment arrives → publish to channel "stream:{streamId}"

Tier 2: Pub/Sub → Fan-Out Servers (N servers subscribed)
  Each Fan-Out Server subscribes to "stream:{streamId}"
  Each server holds ~50K SSE connections

Tier 3: Fan-Out Server → Clients (50K pushes each)
  Server iterates through its SSE connections → sends comment

1M viewers ÷ 50K per server = 20 Fan-Out Servers
1 comment → 1 Pub/Sub message → 20 server receives → 50K pushes each = 1M delivered
```

### Scaling Formula
```
viewers = 1,000,000
connections_per_server = 50,000
fan_out_servers = viewers / connections_per_server = 20

comments_per_second = 1,000
total_pushes_per_second = comments_per_second × viewers = 1 BILLION
→ 20 servers × 50K connections × 1K comments = 1B pushes/sec

This is pushing the limits. Need optimizations (see Deep Dive 3).
```

---

## 6. Deep Dive 3: Backpressure & Sampling for Viral Streams

### The Problem
```
Super Bowl final: 1M viewers, 10K comments/second
Total pushes: 10K × 1M = 10 BILLION pushes/second → IMPOSSIBLE

Even at 1K comments/sec, users can't read that fast.
Showing all comments = wall of text scrolling at light speed.
```

### ✅ Client-Side Throttling
```
Client receives ALL comments but RENDERS only 5 per second.
→ Buffer comments locally → display at readable pace
→ Simple, but wastes bandwidth
```

### ✅✅ Server-Side Sampling (Better)
```
Fan-Out Server samples comments before pushing:
  - If < 10 comments/sec → push all (normal stream)
  - If 10-100/sec → push every 2nd comment (50% sample)
  - If > 100/sec → push only 5/sec (top comments by engagement)

Sampling strategies:
  1. RANDOM: pick 5 random comments per second → fair but noisy
  2. RATE-BASED: take latest 5 per second → bias toward recent
  3. ENGAGEMENT-BASED: prioritize comments with likes/replies → higher quality
  4. DIVERSITY: ensure comments from different users (avoid spam domination)
```

### ✅✅ Batch Delivery
```
Instead of pushing each comment individually:
  → Buffer for 200ms → push batch of 5-10 comments
  → Reduces network overhead (1 push instead of 10)
  → Client renders batch animation
  → Reduces WebSocket/SSE message rate 10x
```

---

## 7. Deep Dive 4: Comment Ordering & Consistency

### Eventual Consistency is Acceptable
```
User A in NY sees: comment_1, comment_2, comment_3
User B in London sees: comment_2, comment_1, comment_3
→ Different order due to network latency → acceptable for live comments
→ Not a banking transaction!
```

### Sequence Numbers for Best-Effort Ordering
```
Comment Service assigns monotonic sequence_num:
  INCR stream:{streamId}:sequence → 456

Comment payload:
  { id: "c-456", sequence: 456, text: "Goal!", timestamp: ... }

Client sorts by sequence_num:
  → If sequence gap detected (received 454, 456 but not 455):
  → Wait briefly → if still missing → skip (it'll appear later or was lost)
```

---

## 8. Interview Tips & Common Questions

### Q: Why not use Kafka for fan-out?
> Kafka is great for producer-consumer (one reader per partition). For fan-out (one message to 1M recipients), you need Pub/Sub semantics. Redis Pub/Sub or a dedicated Pub/Sub system (Google Cloud Pub/Sub) is better suited. Kafka works for the ingestion layer, not the delivery layer.

### Q: How do you handle profanity / spam moderation?
> Async pipeline: comment posted → immediately published for delivery → simultaneously sent to moderation service (ML model or keyword filter). If flagged → send a "delete" event to remove from clients already showing it. Most comments are clean → don't block on moderation for latency.

### Q: How do you store comments for replay after the live stream?
> Write all comments to Cassandra (partitioned by stream_id, sorted by timestamp). After stream ends, the SSE endpoint switches to paginated REST: `GET /comments?cursor=`. Same data, different access pattern.

### Q: What if a Fan-Out Server crashes?
> Viewers on that server lose their SSE connection. Browser's EventSource API auto-reconnects to a different server (behind load balancer). On reconnect, fetch missed comments: `Last-Event-ID: 456` → server sends comments since sequence 456.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
