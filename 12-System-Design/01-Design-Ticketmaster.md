# 🎫 Design Ticketmaster — System Design Interview

> **Source:** [Design Ticketmaster w/ a]Staff Engineer](https://www.youtube.com/watch?v=fhdPyoO6aXI)
> **Full Answer Key:** [hellointerview.com/ticketmaster](https://www.hellointerview.com/learn/system-design/answer-keys/ticketmaster)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities](#2-core-entities)
3. [API Design](#3-api-design)
4. [High-Level Architecture](#4-high-level-architecture)
5. [Deep Dive 1: How Do We Handle Seat Reservations Without Double-Booking?](#5-deep-dive-1-how-do-we-handle-seat-reservations-without-double-booking)
6. [Deep Dive 2: How Do We Scale the View API to 10s of Millions?](#6-deep-dive-2-how-do-we-scale-the-view-api-to-10s-of-millions)
7. [Deep Dive 3: Virtual Waiting Queue for Extremely Popular Events](#7-deep-dive-3-virtual-waiting-queue-for-extremely-popular-events)
8. [Deep Dive 4: How Can We Optimize Search?](#8-deep-dive-4-how-can-we-optimize-search)
9. [Deep Dive 5: Payment Flow with Stripe](#9-deep-dive-5-payment-flow-with-stripe)
10. [What is Expected at Each Level?](#10-what-is-expected-at-each-level)
11. [Interview Tips & Common Questions](#11-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **View Events** | Users browse and view event details, venue info |
| **Search Events** | Search by keyword, location, date, genre |
| **Interactive Seat Map** | Real-time seat map showing Available / Held / Booked |
| **Book Tickets** | Reserve seats, complete payment, receive confirmation |
| **Temporary Hold** | Held seats auto-expire after ~10 minutes |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Strong Consistency** | No double-booking at all | A user who paid MUST get their exact seat |
| **Scalability** | 10M+ concurrent users on popular drops | Taylor Swift, BTS, etc. |
| **Low Latency** | <200ms browsing, <500ms reservation | Good UX |
| **High Availability** | 99.9%+ uptime | Revenue-critical |

> **Key Insight from the video:** Consistency is MORE important than availability for this system. Double-selling a seat is unacceptable. We sacrifice some availability (via waiting rooms) to maintain strict consistency during checkout.

---

## 2. Core Entities

```
User         → id, name, email, auth_details
Event        → id, name, venue_id, date, performer, description, category
Venue        → id, name, location, sections[], capacity
Ticket       → id, event_id, venue_id, section, row, number, status, price
              status: AVAILABLE | RESERVED | BOOKED
Booking      → id, user_id, event_id, ticket_ids[], total_amount, status, created_at
              status: IN_PROGRESS | CONFIRMED | CANCELLED
```

> **Important:** In the video, the ticket status is the central piece. The transitions are: `AVAILABLE → RESERVED → BOOKED` (happy path) or `AVAILABLE → RESERVED → AVAILABLE` (timeout/cancel).

---

## 3. API Design

```
GET    /v1/events?keyword={}&city={}&date={}       → Search events
GET    /v1/events/{eventId}                        → Event details
GET    /v1/events/{eventId}/seats                  → Interactive seat map
POST   /v1/bookings                                → { ticketId } → Reserve seat (returns bookingId)
POST   /v1/bookings/{bookingId}/payment             → Process payment with Stripe token
DELETE /v1/bookings/{bookingId}                     → Cancel reservation
```

---

## 4. High-Level Architecture

```
                                 ┌──────────────┐
                                 │ Elasticsearch │ ← Full-text event search
                                 └───────┬──────┘
┌────────┐    ┌─────────────┐    ┌───────┴──────┐    ┌──────────────┐
│ Client  │───│ API Gateway │───│ Event Service │    │  Redis Cache  │
└────────┘    │ (Rate Limit)│    └──────────────┘    │ (Event data,  │
              └──────┬──────┘                        │  seat state)  │
                     │           ┌──────────────┐    └───────┬──────┘
                     ├──────────│Booking Service│────────────┤
                     │           └───────┬──────┘            │
                     │                   │           ┌───────┴──────┐
                     │           ┌───────┴──────┐    │ Redis         │
                     │           │ Stripe        │    │ Distributed   │
                     │           │ (Webhooks)    │    │ Lock (TTL)    │
                     │           └──────────────┘    └──────────────┘
                     │                                       │
                     │                               ┌───────┴──────┐
                     │                               │ PostgreSQL    │
                     │                               │ (Source of    │
              ┌──────┴──────┐                        │  Truth)       │
              │ Message Queue│                        └──────────────┘
              │  (Kafka)     │
              └──────┬──────┘
                     │
              ┌──────┴──────┐
              │ Notification │
              │ Worker       │
              └─────────────┘
```

---

## 5. Deep Dive 1: How Do We Handle Seat Reservations Without Double-Booking?

This is the **#1 deep dive** the interviewer expects. Two users click "Book" on the same seat simultaneously.

### ❌ Bad Solution: Long-Running Database Locks

```sql
BEGIN;
SELECT * FROM tickets WHERE id = 123 FOR UPDATE;  -- Lock the row
-- User fills payment form (5-10 minutes)...
UPDATE tickets SET status = 'BOOKED' WHERE id = 123;
COMMIT;
```

**Why it's bad:**
- Row locked for 5-10 minutes while user fills payment details
- Other users CAN'T even check if the seat is available
- If user abandons session, lock may never release
- Database connection pool exhaustion under load

### ✅ Good Solution: Status + Expiration Time with Cron

```sql
-- On seat selection:
UPDATE tickets SET status = 'RESERVED', expires_at = NOW() + '10 min'
WHERE id = 123 AND status = 'AVAILABLE';

-- Cron job runs every 30 seconds:
UPDATE tickets SET status = 'AVAILABLE'
WHERE status = 'RESERVED' AND expires_at < NOW();
```

**Why it's good but not great:**
- ✅ Short DB transaction (milliseconds, not minutes)
- ❌ **Delay between expiry and cron execution** — seat stays "reserved" even after expiry until cron runs
- ❌ If cron fails or lags, tickets stuck as "reserved"
- ❌ For high-demand events (Taylor Swift), even 30 seconds delay = lost sales

### ✅✅ Great Solution: Implicit Status with Expiration Time

```sql
-- Instead of checking: status = 'AVAILABLE'
-- Check: status = 'AVAILABLE' OR (status = 'RESERVED' AND expires_at < NOW())

BEGIN;
UPDATE tickets 
SET status = 'RESERVED', expires_at = NOW() + INTERVAL '10 min', held_by = ?
WHERE id = 123 
  AND (status = 'AVAILABLE' OR (status = 'RESERVED' AND expires_at < NOW()));

-- Check rows_affected
IF rows_affected == 0 THEN
  -- Seat is genuinely reserved by another user
  RETURN "Seat unavailable"
END IF;
COMMIT;
```

**Why it's great:**
- ✅ No cron job needed — expired seats are **implicitly available**
- ✅ Atomic check: no race conditions
- ✅ Zero delay between expiry and availability
- ❌ Still relies on DB for hot-path concurrency

### ✅✅✅ Great Solution: Distributed Lock with TTL (Redis)

```
Step 1: User selects seat → POST /bookings { ticketId: 123 }
Step 2: Booking Service acquires Redis lock:
        SET lock:ticket:123 {userId} EX 600 NX
        (NX = only if key doesn't exist, EX = 600 seconds TTL)
Step 3: If lock acquired → Create booking in DB (status: IN_PROGRESS)
        If NOT acquired → "Seat unavailable, try another"
Step 4: Return bookingId to client → redirect to payment page
Step 5: If user doesn't pay within 10 min → Redis auto-releases lock (TTL expires)
Step 6: If payment succeeds → Update ticket status to BOOKED, delete Redis lock
```

**Why it's the best:**
- ✅ Sub-millisecond lock acquisition
- ✅ **Auto-expiration** — no cron, no implicit checks, Redis TTL handles it
- ✅ Scales independently from the database
- ✅ DB only used for durable persistence after payment
- ❌ Need to handle Redis failure (fallback to DB-level check)

> **Interview Tip:** Present the JOURNEY from Bad → Good → Great. This shows depth of thinking and is exactly what the video demonstrates.

---

## 6. Deep Dive 2: How Do We Scale the View API to 10s of Millions?

When Taylor Swift tickets drop, the event page gets 10M+ concurrent requests.

### Caching Strategy
```
HIGH CACHE TTL (hours/days):
  - Event details (name, date, venue, performer)
  - Venue info (location, capacity, sections)
  → This data rarely changes → cache aggressively

LOW CACHE TTL (seconds):
  - Seat availability map
  → Changes frequently during booking
  → Use Redis with 5-10s TTL
  → Acceptable to show slightly stale seat map

CACHE KEY PATTERN:
  event:{eventId}:details → event metadata (TTL: 1 hour)
  event:{eventId}:seats   → seat availability bitmask (TTL: 5 seconds)
```

### Read-Through Cache Pattern
```
Client requests event → API checks Redis
  → CACHE HIT  → return immediately
  → CACHE MISS → query PostgreSQL → populate Redis → return
```

### SSE (Server-Sent Events) for Real-Time Seat Updates
```
Client subscribes: GET /v1/events/{id}/seats/stream (SSE)
  → Server pushes seat status changes in real-time
  → When a seat is reserved/released → push update
  → Client updates UI without polling

Why SSE over WebSocket?
  → One-directional (server → client only)
  → Simpler implementation
  → Auto-reconnect built into EventSource API
```

### Horizontal Scaling
```
Event Service is STATELESS:
  → Spin up 100+ instances behind load balancer
  → Each instance reads from Redis cache
  → Zero shared state between instances
  → Auto-scale based on CPU/request count
```

---

## 7. Deep Dive 3: Virtual Waiting Queue for Extremely Popular Events

For events with millions of concurrent buyers, even caching isn't enough.

### How It Works
```
Step 1: User requests booking page → placed in Redis sorted set queue
        ZADD waiting_queue:{eventId} {timestamp} {userId}

Step 2: Server maintains SSE/WebSocket connection with each queued user
        → Periodically sends position updates: "You are #4,523 in line"

Step 3: When capacity opens (someone completes or abandons):
        → Dequeue next N users from the sorted set
        → Mark them as "admitted" in Redis SET:
          SADD admitted:{eventId} {userId/sessionId} [with TTL]

Step 4: Admitted users proceed to seat selection & booking
        → Booking Service checks: SISMEMBER admitted:{eventId} {userId}
        → If not in admitted set → reject with "Please wait in queue"

Step 5: Limit concurrent booking users to, say, 500 at a time
        → Once one completes/times out, next in queue is admitted
```

### Why This Works
```
Without queue: 1M users hit booking simultaneously → system crashes
With queue:    1M users in queue, 500 in booking flow at a time → system stable
               Fair FIFO ordering → users feel it's fair
```

---

## 8. Deep Dive 4: How Can We Optimize Search?

### Bad → Good → Great Solutions

| Level | Approach | Latency |
|-------|----------|---------|
| **Bad** | `SELECT * FROM events WHERE name LIKE '%keyword%'` | Full table scan, seconds |
| **Good** | SQL full-text index: `CREATE INDEX idx_event_search ON events USING GIN (to_tsvector('english', name))` | Better, but limited |
| **Great** | Elasticsearch: dedicated full-text search engine with inverted index, fuzzy matching, faceted search | Sub-100ms on billions of docs |

### Elasticsearch Integration
```
Event Service → on event create/update → publish to Kafka
  → Elasticsearch indexer consumes → updates search index

Search query → API Gateway → Elasticsearch (search)
  → Returns event IDs → Fetch full details from Redis/PostgreSQL
```

---

## 9. Deep Dive 5: Payment Flow with Stripe

This is the exact flow described in the video:

```
Step 1: Client  → fills payment form (Stripe.js tokenizes card)
        → Our server NEVER sees raw card numbers (PCI compliance)

Step 2: Client  → sends { bookingId, paymentToken } to our server
Step 3: Server  → creates Stripe PaymentIntent using the token
Step 4: Stripe  → processes payment async → sends webhook to our server

Step 5: Webhook handler (MUST be idempotent):
        a. Extract bookingId from Stripe metadata
        b. Begin DB transaction:
           - UPDATE tickets SET status = 'BOOKED' WHERE booking_id = ?
           - UPDATE bookings SET status = 'CONFIRMED' WHERE id = ?
        c. Delete Redis lock for the ticket
        d. Send confirmation notification via Kafka

Idempotency: Stripe may retry webhooks on failure
  → Check booking status before updating
  → If already CONFIRMED → skip (no duplicate processing)
  → Use bookingId as idempotency key
```

---

## 10. What is Expected at Each Level?

### Mid-Level
- Understand functional requirements
- Design basic seat booking flow with database
- Identify the double-booking problem

### Senior
- Propose distributed locking (Redis) with TTL
- Design caching strategy for high-read scenarios
- Explain payment integration (Stripe webhooks, idempotency)
- Discuss trade-offs (consistency vs availability)

### Staff+
- Virtual waiting queue design with admission control
- Deep understanding of why consistency > availability here
- SSE for real-time seat updates
- Elasticsearch for search optimization
- Back-of-envelope calculations for queue sizing
- Discuss PCI compliance, anti-bot measures (CAPTCHA, rate limiting)

---

## 11. Interview Tips & Common Questions

### Q: Why not just use a simple DB transaction for the entire checkout?
> DB row locks create contention under massive concurrent access. The checkout flow takes 5-10 minutes (user filling payment), and holding a DB lock that long is a non-starter. Redis lock with TTL decouples the "hold" from the "payment" flow.

### Q: How do you handle seat hold expiration?
> Redis key TTL (e.g., 600 seconds). When the key expires, the seat automatically becomes available. No cron jobs, no background workers — Redis handles it natively.

### Q: What if payment fails after seat is held?
> Release the seat: delete the Redis lock. Update booking status to CANCELLED. The seat is immediately available for others. The state machine: `AVAILABLE → RESERVED → BOOKED` or `AVAILABLE → RESERVED → AVAILABLE`.

### Q: Why strong consistency over availability?
> Double-booking = two people pay for the same physical seat. This is not a "soft" problem — it causes refunds, legal issues, and brand damage. Use virtual waiting rooms to reduce load rather than relaxing consistency.

### Q: How do you prevent bots from buying all tickets?
> Rate limiting per IP/session. CAPTCHA before entering the waiting queue. Device fingerprinting. Bot detection (behavioral analysis). Limit tickets per user/account.

### Q: How do you handle the "seat map" at scale?
> Compress seat state as a bitmask (2 bits per seat: available/reserved/booked). For a 50,000-seat venue, that's ~12KB. Serve via CDN. Client renders locally. Much smaller than sending individual seat objects.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
