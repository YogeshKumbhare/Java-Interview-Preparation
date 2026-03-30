# 🔗 Design Bitly (URL Shortener) — System Design Interview

> **Source:** [Design Bitly w/ a Staff Engineer](https://www.youtube.com/watch?v=iUU4O1sWtJA)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: How Do We Generate Short URLs?](#4-deep-dive-1-how-do-we-generate-short-urls)
5. [Deep Dive 2: Read-Heavy System — Scaling Redirects](#5-deep-dive-2-read-heavy-system--scaling-redirects)
6. [Deep Dive 3: 301 vs 302 Redirects](#6-deep-dive-3-301-vs-302-redirects)
7. [Deep Dive 4: Analytics & Click Tracking](#7-deep-dive-4-analytics--click-tracking)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Shorten URL** | Given a long URL, generate a unique short URL |
| **Redirect** | Short URL redirects to original long URL |
| **Custom Aliases** | Users can specify a custom short code |
| **Analytics** | Track click count, referrer, geography |
| **Expiration** | Optional TTL on shortened URLs |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Read-Heavy** | 100:1 read-to-write ratio | Millions click, few create |
| **Low Latency** | < 50ms redirect | Must feel instant |
| **Availability** | 99.99% | Every click matters |
| **Scalability** | 100K reads/second | Viral links |

### Back-of-Envelope
```
Writes: 100M new URLs/month → ~40 writes/sec
Reads:  100:1 ratio → 10B redirects/month → ~4000 reads/sec
URL stored: 7-char code → 62^7 = 3.5 trillion possible URLs (plenty)
Storage: 100M/month × 12 months × 500 bytes = ~600GB/year (small)
```

---

## 2. Core Entities & API Design

### Entities
```
ShortUrl → id, short_code (7 chars), long_url, user_id, created_at, expires_at
Click    → id, short_code, timestamp, referrer, user_agent, ip, country
```

### API
```
POST   /v1/urls                     → { long_url, custom_alias?, ttl? }
                                     → { short_url: "https://bit.ly/abc1234" }
GET    /v1/{short_code}              → 301/302 redirect to original URL
GET    /v1/urls/{short_code}/stats   → Click analytics
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌─────────────────┐
│  Client   │───│  API Gateway  │───│  URL Service      │
└──────────┘    └──────┬───────┘    └────────┬────────┘
                       │                     │
                ┌──────┴───────┐    ┌────────┴────────┐
                │   Redis       │    │  PostgreSQL      │
                │  (Cache)      │    │ (URL mappings)   │
                └──────────────┘    └─────────────────┘
                       │
                ┌──────┴───────┐    ┌──────────────────┐
                │ Kafka (async) │───│ Analytics Workers  │
                └──────────────┘    │ → ClickHouse       │
                                    └──────────────────┘
```

---

## 4. Deep Dive 1: How Do We Generate Short URLs?

### Option 1: MD5/SHA-256 Hash + Truncation
```
hash = MD5("https://example.com/very/long/url")
short_code = base62(hash[:7])

Problem: Collisions
  → Different URLs may produce same 7-char code
  → Must check DB for collision → retry with salt
  → Adds read before write
```

### Option 2: Auto-Incrementing Counter
```
counter = next_id()  → 1, 2, 3, 4, ...
short_code = base62(counter)

1 → "1"
62 → "10"
238,328 → "zz"
3,521,614,606,208 → "zzzzzzz"

Pros: Guaranteed unique (no collisions), simple
Cons: Predictable → sequential codes are guessable
      Security concern: enumeration attack
```

### Option 3: Pre-Generated Key Service (Best for Interviews)
```
Key Generation Service (KGS):
  1. Pre-compute millions of random 7-char base62 codes
  2. Store in DB with used/unused flag
  3. On URL creation request:
     a. Pop an unused key from KGS (atomic operation)
     b. Insert: { short_code, long_url } into URL table
  
Benefits:
  ✅ No collision checks needed
  ✅ Zero compute on hot path
  ✅ Non-sequential (not guessable)
  ✅ Pre-generation is async, no latency impact
  
Implementation:
  Two tables: keys_unused (pre-generated pool) and keys_used
  Worker thread continuously generates new keys into keys_unused
  URL Service atomically moves key from unused → used
```

### Option 4: Snowflake-like ID + Base62 (Very Common)
```
Distributed ID: datacenter_id + worker_id + timestamp + sequence
→ Globally unique 64-bit number → base62 encode → 7 chars

No coordination needed between nodes
Each node generates independently
```

---

## 5. Deep Dive 2: Read-Heavy System — Scaling Redirects

```
Redirect flow (hot path):
  1. Client hits GET /abc1234
  2. Check Redis cache first:
     → HIT: return 301/302 redirect to cached long_url
     → MISS: query PostgreSQL → populate cache → redirect
  
Cache strategy:
  → Size: top 20% of URLs get 80% of traffic (Pareto)
  → Eviction: LRU (Least Recently Used)
  → TTL: 24 hours (most clicks happen within first day)
  
  Expected cache hit rate: > 90%
  → 4000 reads/sec × 90% = 3600 served from Redis
  → Only 400 reads/sec hit PostgreSQL → easily manageable
```

### Multi-Layer Caching
```
Layer 1: CDN (Cloudflare, CloudFront)
  → Edge caching for globally popular links
  → Only with 301 (permanent) redirects

Layer 2: Redis (Application Cache)
  → In-memory, sub-millisecond lookups
  → LRU eviction, 24h TTL

Layer 3: PostgreSQL with Read Replicas
  → Primary for writes
  → Multiple replicas for reads
```

---

## 6. Deep Dive 3: 301 vs 302 Redirects

| Aspect | 301 (Permanent) | 302 (Temporary) |
|--------|-----------------|-----------------|
| **Browser Behavior** | Caches redirect locally → never hits your server again | Every visit hits your server |
| **Good For** | Reducing server load | Analytics tracking |
| **Analytics** | LOSE click data (browser handles redirect) | CAPTURE every click |
| **SEO** | Passes link juice to destination | Link juice stays with short URL |
| **Best For** | High-traffic, no analytics needed | Bit.ly-style with click counting |

> **The video recommends:** Use **302** if analytics matter (the default). Offer 301 as an option for users who prioritize performance over tracking.

---

## 7. Deep Dive 4: Analytics & Click Tracking

```
Async click tracking (don't block the redirect):
  1. User clicks short URL
  2. Redirect immediately (302) ← fast path, no delay
  3. Async: publish click event to Kafka:
     { short_code, timestamp, ip, referrer, user_agent }
  4. Analytics workers consume from Kafka:
     - Resolve IP → country, city (MaxMind GeoIP)
     - Parse user_agent → browser, device, OS
     - Write to ClickHouse/Druid (OLAP) for efficient aggregation
  5. Dashboard queries ClickHouse:
     "How many clicks per day for link X from US mobile?"
```

---

## 8. Interview Tips & Common Questions

### Q: How do you handle a URL that goes viral (millions of clicks)?
> Redis absorbs the read traffic. The short_code → long_url mapping is a tiny key-value pair. Redis handles 100K+ reads/sec. CDN edge caching removes load from your infrastructure entirely for static redirects.

### Q: What if the KGS runs out of keys?
> 62^7 = 3.5 trillion possible codes. At 100M new URLs/month, that's 35,000 years of supply. Not a practical concern. If it ever is, extend to 8 characters: 62^8 = 218 trillion.

### Q: How do you prevent abuse (malicious URLs)?
> Scan long_url against blacklists (Google Safe Browsing API) before creating short URL. Rate limit creation per IP/user. Flag URLs that get sudden traffic spikes for review.

### Q: Why not just use UUIDs?
> UUID v4 = 128 bits = 36 characters (with dashes). Way too long for a "short" URL. Even base62-encoded: 22 characters. The whole point is brevity. 7 characters is the sweet spot.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
