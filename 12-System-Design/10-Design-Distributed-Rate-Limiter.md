# ⏱️ Design Distributed Rate Limiter — System Design Interview

> **Source:** [Design Rate Limiter w/ a Staff Engineer](https://www.youtube.com/watch?v=MIJFyUPG4Z4)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [Where Does the Rate Limiter Live?](#3-where-does-the-rate-limiter-live)
4. [Deep Dive 1: Rate Limiting Algorithms](#4-deep-dive-1-rate-limiting-algorithms)
5. [Deep Dive 2: Distributed Rate Limiting with Redis](#5-deep-dive-2-distributed-rate-limiting-with-redis)
6. [Deep Dive 3: Race Conditions & Atomicity](#6-deep-dive-3-race-conditions--atomicity)
7. [Deep Dive 4: Rules Configuration & Multi-Tier Limiting](#7-deep-dive-4-rules-configuration--multi-tier-limiting)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Limit Requests** | Allow N requests per user/IP per time window |
| **Multi-Granularity** | Per-second, per-minute, per-hour limits |
| **Response Headers** | Return remaining quota + retry-after time |
| **Configurable Rules** | Different limits per endpoint, user tier |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Low Latency** | < 1ms decision | Must not slow down API calls |
| **Eventually Consistent** | Brief over-limit OK (not critical) | Distributed systems can't be perfect |
| **Highly Available** | Rate limiter failure ≠ API failure | Open > closed on failure |
| **Scalable** | Support millions of unique rate limit keys | Global platform |

---

## 2. Core Entities & API Design

```
Rate Limit Rule:
  { endpoint: "/api/search", max_requests: 100, window: "1 minute", applies_to: "user_id" }

Rate Limit Response Headers (industry standard):
  X-RateLimit-Limit: 100            ← max requests allowed
  X-RateLimit-Remaining: 42         ← remaining in this window
  X-RateLimit-Reset: 1711814400     ← when window resets (epoch)
  Retry-After: 30                   ← seconds until retry (when limited)

HTTP Status:
  200 OK          ← request allowed
  429 Too Many Requests ← rate limited
```

---

## 3. Where Does the Rate Limiter Live?

```
Option 1: CLIENT-SIDE
  → Client limits its own requests
  → Easy to bypass → not reliable for enforcement
  → Useful only as a courtesy throttle

Option 2: APPLICATION SERVER (middleware)
  → Rate limit check in every API handler
  → Tightly coupled → hard to maintain

Option 3: API GATEWAY (recommended) ✅
  → Centralized gateway (Kong, Envoy, AWS API Gateway)
  → Rate limiting happens BEFORE request reaches backend
  → One place to configure rules
  → All services protected automatically
```

---

## 4. Deep Dive 1: Rate Limiting Algorithms

### Algorithm 1: Fixed Window Counter

```
Window: 12:00:00 - 12:00:59 → counter = 0
Each request: counter++
If counter > limit → reject

Key: rate_limit:{userId}:{window_start}
Examples:
  12:00:05 → INCR rate_limit:user123:1200 → 1 (allow)
  12:00:30 → INCR rate_limit:user123:1200 → 50 (allow)
  12:00:45 → INCR rate_limit:user123:1200 → 101 (REJECT)

Problem: Edge burst
  59 requests at 12:00:59
  59 requests at 12:01:00
  → 118 requests in 2 seconds but each window sees only 59 → both allowed!
```

### Algorithm 2: Sliding Window Log

```
Store timestamp of every request in a sorted set:
  ZADD requests:{userId} {timestamp} {requestId}  

On each request:
  1. Remove entries older than window: ZREMRANGEBYSCORE requests:{userId} 0 (now - window)
  2. Count remaining: ZCARD requests:{userId}
  3. If count ≥ limit → reject; else → ZADD new request

Pros: Precise, no edge burst issue
Cons: Memory-expensive (stores every timestamp)
      100 req/min × 1M users = 100M entries
```

### Algorithm 3: Sliding Window Counter (Best Hybrid)

```
Combine two fixed windows with weighted overlap:

Current window count × weight + Previous window count × (1 - weight)

Example: limit = 100/minute, current time = 12:01:15
  Previous window (12:00): 80 requests
  Current window (12:01): 30 requests
  Elapsed in current window: 15s / 60s = 25%
  
  Estimated = 30 + 80 × (1 - 0.25) = 30 + 60 = 90 → under 100 → allow

Pros: Smooth, no burst at boundaries, low memory
Cons: Approximate (acceptable)
```

### Algorithm 4: Token Bucket (Most Popular)

```
Concept:
  - Bucket holds tokens (capacity = max_tokens)
  - Tokens added at fixed rate (refill_rate per second)
  - Each request consumes one token
  - If bucket empty → reject request
  
Example: 10 tokens, refill 1/second
  t=0:  10 tokens → request → 9 tokens
  t=0:  9 tokens → request → 8 tokens (burst!)
  t=0:  8 tokens → ... → 0 tokens → REJECT
  t=1:  1 token (refilled) → request → 0 tokens
  t=2:  1 token → request → 0 tokens

Redis implementation:
  Key: bucket:{userId}
  Fields: tokens (float), last_refill (timestamp)

  On request:
    1. Calculate tokens added since last_refill
    2. tokens = min(max_tokens, tokens + elapsed × refill_rate)
    3. If tokens ≥ 1: tokens -= 1 → ALLOW
    4. Else: REJECT (return retry_after = (1 - tokens) / refill_rate)

Pros: 
  ✅ Allows short bursts (up to bucket size)
  ✅ Smooths out traffic over time
  ✅ Only 2 values stored per key (very memory-efficient)
  ✅ Most intuitive for API consumers
```

### Algorithm 5: Leaky Bucket

```
Like token bucket, but requests are QUEUED and processed at fixed rate.
  → Bucket = queue with fixed capacity
  → Requests drain at constant rate
  → If queue full → reject (429)

Difference from token bucket:
  Token bucket: allows bursts, then refills
  Leaky bucket: constant output rate, smooths bursts completely

Use case: when you need guaranteed smooth processing rate
  → Payment processing (exactly N transactions/second)
```

### Comparison
| Algorithm | Memory | Accuracy | Burst | Complexity |
|-----------|--------|----------|-------|------------|
| Fixed Window | Low | Edge burst issue | Yes | Simple |
| Sliding Log | High | Exact | No | Medium |
| Sliding Counter | Low | Approximate | Smoothed | Medium |
| Token Bucket | Low | Good | Controlled | Medium |
| Leaky Bucket | Medium | Good | None | Medium |

---

## 5. Deep Dive 2: Distributed Rate Limiting with Redis

```
Multi-server environment:
  API Server 1 ──┐
  API Server 2 ──┤── Redis (centralized counter)
  API Server 3 ──┘

Each server checks Redis before processing request:
  1. EVAL token_bucket_script {userId} → ALLOW or REJECT
  2. Redis handles concurrency (single-threaded execution)
  3. All servers share the same counter → globally consistent

Redis Lua Script (Token Bucket — Atomic):
  local key = KEYS[1]
  local max_tokens = tonumber(ARGV[1])
  local refill_rate = tonumber(ARGV[2])
  local now = tonumber(ARGV[3])
  
  local data = redis.call('HMGET', key, 'tokens', 'last_refill')
  local tokens = tonumber(data[1]) or max_tokens
  local last_refill = tonumber(data[2]) or now
  
  -- Refill tokens
  local elapsed = now - last_refill
  tokens = math.min(max_tokens, tokens + elapsed * refill_rate)
  
  if tokens >= 1 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 3600)  -- TTL for cleanup
    return {1, tokens}  -- ALLOW, remaining
  else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    return {0, tokens}  -- REJECT, no tokens
  end
```

---

## 6. Deep Dive 3: Race Conditions & Atomicity

### The Race Condition
```
Without atomic operations:
  Thread A: GET tokens → 1
  Thread B: GET tokens → 1
  Thread A: tokens > 0 → ALLOW → SET tokens = 0
  Thread B: tokens > 0 → ALLOW → SET tokens = 0
  
Both requests allowed, but limit was 1! Over-limit by 100%.
```

### Solution: Redis Lua Scripts
```
Redis executes Lua scripts ATOMICALLY:
  → No interleaving between concurrent script executions
  → GET + CHECK + SET happens as one operation
  → No race condition possible

Alternative: Redis MULTI/EXEC transactions
  → Also atomic, but less flexible than Lua
```

---

## 7. Deep Dive 4: Rules Configuration & Multi-Tier Limiting

```
Rate limit rules stored in config (YAML, DB, or API):

rules:
  - endpoint: "/api/search"
    limits:
      - { window: "1s", max: 5 }      # burst protection
      - { window: "1m", max: 100 }     # sustained rate
      - { window: "1h", max: 1000 }    # hourly cap
    apply_by: "user_id"
    
  - endpoint: "/api/login"
    limits:
      - { window: "1m", max: 5 }       # brute force protection  
    apply_by: "ip"

  - endpoint: "/api/*"
    limits:
      - { window: "1s", max: 50 }      # global per-user rate
    apply_by: "api_key"
    tier_overrides:
      premium: { window: "1s", max: 500 }  # 10x for paying users

Request must pass ALL matching rules.
```

---

## 8. Interview Tips & Common Questions

### Q: What happens when Redis is down?
> **Fail open** (allow all requests). Rate limiter is a PROTECTION mechanism, not a core feature. Blocking all traffic when rate limiter is unavailable = worse than allowing some over-limit traffic. Log the failure for monitoring.

### Q: How do you handle multiple data centers?
> Option 1: Local Redis per DC → eventually consistent (may briefly exceed global limit). Option 2: Global Redis → adds cross-DC latency (~50ms). Trade-off: most APIs choose local Redis + relaxed global limits.

### Q: How do you rate limit by IP for unauthenticated requests?
> Use source IP as the rate limit key. Caveat: NAT/proxies → thousands of users behind one IP (corporate networks). Combine IP + device fingerprint + JA3 hash for better granularity.

### Q: Token bucket vs sliding window — which should I choose?
> Token bucket if you want to allow controlled bursts (API rate limiting). Sliding window if you want strictly smooth rate (payment processing). In an interview, present token bucket as your primary choice and mention alternatives.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
