# 🔥 Design Tinder — System Design Interview

> **Source:** [Design Tinder w/ a Staff Engineer](https://www.youtube.com/watch?v=18Fg5Akhkqw)
> **Full Answer Key:** [hellointerview.com/tinder](https://www.hellointerview.com/learn/system-design/answer-keys/tinder)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: How Do We Ensure Swiping Is Consistent & Low Latency?](#4-deep-dive-1-how-do-we-ensure-swiping-is-consistent--low-latency)
5. [Deep Dive 2: How Do We Generate the Feed/Stack With Low Latency?](#5-deep-dive-2-how-do-we-generate-the-feedstack-with-low-latency)
6. [Deep Dive 3: How Do We Avoid Showing Already-Swiped Profiles?](#6-deep-dive-3-how-do-we-avoid-showing-already-swiped-profiles)
7. [What is Expected at Each Level?](#7-what-is-expected-at-each-level)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Profile** | Create/edit profile with photos, bio, preferences (age, distance) |
| **Discovery Feed** | See a stack of nearby potential matches |
| **Swiping** | Swipe right (yes) or left (no) on profiles one-by-one |
| **Match Notification** | Mutual right-swipes = match + instant notification |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Low Latency** | Swipe: <200ms | UX feels instant |
| **Consistency** | Strong for match detection | Two right-swipes MUST create a match |
| **Scalability** | Billions of swipes/day | Massive DAU |
| **Availability** | High for feed, strong consistency for matching | Feed staleness OK, missed matches NOT OK |

---

## 2. Core Entities & API Design

### Entities
```
User       → id, name, age, gender, bio, photos[], 
             preferences { gender, age_min, age_max, max_distance_km }
             location { lat, lng, updated_at }
Swipe      → id, from_user, to_user, direction (left|right), timestamp
Match      → id, user_a_id, user_b_id, created_at
```

### API
```
POST   /v1/profiles              → Create/update profile
PUT    /v1/location              → Update GPS location
GET    /v1/feed                  → Get discovery stack (batch of profiles)
POST   /v1/swipes                → { target_id, direction } → { is_match? }
GET    /v1/matches               → List of matches
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌─────────────────┐
│  Client   │───│  API Gateway  │───│ Profile Service   │
└──────────┘    └──────┬───────┘    └─────────────────┘
                       │
              ┌────────┼──────────────┐
              │        │              │
     ┌────────┴──┐  ┌──┴──────┐   ┌──┴───────────────┐
     │ Location   │  │ Swipe   │   │ Feed Generation   │
     │ Service    │  │ Service │   │ Service            │
     └─────┬─────┘  └────┬────┘   └────────┬──────────┘
           │              │                 │
     ┌─────┴─────┐  ┌────┴────┐    ┌───────┴────────┐
     │ Redis GEO  │  │ Redis   │    │ Cassandra       │
     │ (proximity)│  │ (Lua    │    │ (Swipe history  │
     └───────────┘  │ scripts)│    │  + user data)   │
                     └────┬────┘    └────────────────┘
                          │
                    ┌─────┴─────┐
                    │ Match      │
                    │ Service    │
                    │ (notify)   │
                    └───────────┘
```

---

## 4. Deep Dive 1: How Do We Ensure Swiping Is Consistent & Low Latency?

This is the **core deep dive**. The race condition:
```
Person A swipes right on B → server checks for B→A swipe → nothing yet
Person B swipes right on A → server checks for A→B swipe → nothing yet  
Person A's swipe saved
Person B's swipe saved
→ BOTH right-swiped but NO MATCH was detected! 😱
```

### ❌ Bad Solution: Database Polling for Matches

```
Save swipe → separate cron job scans for mutual swipes
```
**Problems:** Delay in match notification. High DB load. Race conditions between scan and new swipes.

### ✅ Good Solution: Database Transactions

```sql
BEGIN;
  INSERT INTO swipes (from_user, to_user, direction) VALUES (A, B, 'right');
  SELECT direction FROM swipes WHERE from_user = B AND to_user = A;
  -- If other direction = 'right' → CREATE MATCH
COMMIT;
```
**Better**, but at high scale with distributed/sharded databases, cross-shard transactions are expensive.

### ✅✅ Great Solution: Sharded Cassandra with Single-Partition Transactions

The key insight: **store both swipes in the SAME partition** so the check is atomic.

```sql
-- Partition key: sorted user pair (always consistent regardless of who swipes)
CREATE TABLE swipes (
  user_pair TEXT,        -- partition key: "smaller_id:larger_id"
  from_user UUID,        -- clustering key
  to_user UUID,          -- clustering key
  direction TEXT,
  created_at TIMESTAMP,
  PRIMARY KEY ((user_pair), from_user, to_user)
);
```

```python
def get_user_pair(user_a, user_b):
    # Sort IDs → A→B and B→A map to SAME partition
    sorted_ids = sorted([user_a, user_b])
    return f"{sorted_ids[0]}:{sorted_ids[1]}"

def handle_swipe(from_user, to_user, direction):
    user_pair = get_user_pair(from_user, to_user)
    
    # Both operations happen atomically within SAME partition
    batch = """
    BEGIN BATCH
      INSERT INTO swipes (user_pair, from_user, to_user, direction, created_at)
      VALUES (?, ?, ?, ?, ?);
    APPLY BATCH;
    """
    # Then check for inverse swipe in same partition (local read)
    other = SELECT direction FROM swipes 
            WHERE user_pair = ? AND from_user = to_user AND to_user = from_user;
    
    if direction == 'right' and other == 'right':
        create_match(from_user, to_user)  # 🎉 IT'S A MATCH!
```

**Why it works:** Cassandra guarantees atomic batch operations within a single partition. No cross-partition coordination needed.

### ✅✅ Great Solution: Redis for Atomic Operations (Lua Script)

```python
def get_key(user_a, user_b):
    sorted_ids = sorted([user_a, user_b])
    return f"swipes:{sorted_ids[0]}:{sorted_ids[1]}"

def handle_swipe(from_user, to_user, direction):
    key = get_key(from_user, to_user)
    
    # Redis Lua script — runs ATOMICALLY (no interleaving)
    script = """
    redis.call('HSET', KEYS[1], ARGV[1], ARGV[2])
    return redis.call('HGET', KEYS[1], ARGV[3])
    """
    
    other_swipe = redis.eval(
        script,
        keys=[key],
        args=[
            f"{from_user}_swipe",   # field to set
            direction,              # our swipe direction
            f"{to_user}_swipe"      # field to check
        ]
    )
    
    # Atomically: set our swipe AND check their swipe
    if direction == 'right' and other_swipe == b'right':
        create_match(from_user, to_user)  # 🎉 MATCH!
```

**Redis Lua advantages:**
- ✅ Entire script runs atomically — no race condition possible
- ✅ Sub-millisecond latency
- ✅ Key partitioning with sorted IDs → consistent hashing distributes load
- ❌ Need to persist swipes to Cassandra async (Redis is not durable enough for permanent data)

---

## 5. Deep Dive 2: How Do We Generate the Feed/Stack With Low Latency?

The feed query is complex:
```sql
SELECT * FROM users 
WHERE age BETWEEN 18 AND 35
  AND gender = 'female'
  AND distance(lat, lng) < max_distance
  AND user_id NOT IN (already_swiped_users)
ORDER BY ranking_score
LIMIT 50;
```

### ✅ Good Solution: Indexed Database for Real-Time Querying

```
Use geospatial index for distance filtering
+ composite index on (gender, age)
→ Filter → Rank → Return

Challenge: "NOT IN (already_swiped)" is expensive when user has swiped on 100K+ profiles
```

### ✅ Good Solution: Pre-computation and Caching

```
Background job runs periodically:
  1. For each user, pre-compute candidate list
  2. Store in Redis cache: feed:{userId} → [profile_ids...]
  3. When user opens app → serve from cache instantly

Challenge: Pre-computed feed can go stale (user changed preferences, profiles moved)
```

### ✅✅ Great Solution: Hybrid (Pre-computation + Indexed DB)

```
1. Pre-compute candidate list during low-traffic hours → store in cache
2. When user opens app → serve pre-computed feed
3. When cache runs out → fall back to real-time indexed DB query
4. Invalidate cache when:
   - User changes preferences → full recompute
   - User moves significantly → recompute
   - Candidate profiles change → lazy invalidation
```

---

## 6. Deep Dive 3: How Do We Avoid Showing Already-Swiped Profiles?

If a user has swiped on 50,000 profiles, we need an efficient "already seen" check.

### ❌ Bad Solution: DB Query + `NOT IN` Check

```sql
SELECT * FROM candidates WHERE user_id NOT IN (
  SELECT to_user FROM swipes WHERE from_user = ?
)
```
**Problem:** The subquery returns 50K+ IDs → massive `NOT IN` list → extremely slow.

### ✅ Good Solution: Cache Swipe History in Redis SET

```
SADD swiped:{userId} profile_1 profile_2 ... profile_50000
SISMEMBER swiped:{userId} candidate_id  → O(1) check
```
**Better:** O(1) per check, but storing 50K entries per user × millions of users = significant memory.

### ✅✅ Great Solution: Bloom Filter

```
Per-user Bloom filter in Redis:
  BF.ADD swiped_filter:{userId} profile_1
  BF.ADD swiped_filter:{userId} profile_2
  ...
  
  BF.EXISTS swiped_filter:{userId} candidate_X
  → "definitely NOT swiped" (guaranteed) → show in feed
  → "probably swiped" (small false positive rate ~1%) → skip

Memory: Bloom filter for 100K items with 1% FP rate = ~120KB per user
vs SET: 100K × 50 bytes = 5MB per user → 40x memory savings
```

**Why false positives are acceptable:**
- False positive = "user might have seen this profile" → skip it
- Cost: miss showing ONE profile they haven't seen → very low cost
- False negative = "user definitely hasn't seen this" → guaranteed accurate
- This is the perfect use case for Bloom filters

---

## 7. What is Expected at Each Level?

### Mid-Level
- Basic swipe + match flow
- Location-based filtering
- Database-backed matching

### Senior
- Race condition awareness for mutual swipes
- Cassandra or Redis atomic matching (sorted user pair key)
- Geospatial indexing for proximity queries
- Feed caching for low latency

### Staff+
- Bloom filter for "already swiped" deduplication
- Hybrid feed generation (pre-computed + indexed fallback)
- Content-Defined CDC for feed invalidation
- Lua scripts for atomic Redis operations
- Back-of-envelope: swipes/day, Bloom filter sizing
- Recommendation engine discussion (ranking, cold-start)

---

## 8. Interview Tips & Common Questions

### Q: Why the sorted user_pair key?
> `get_key("A", "B")` = `get_key("B", "A")` = `"swipes:A:B"`. This ensures both users' swipe data lands in the same partition/key, enabling atomic check-and-set without distributed coordination.

### Q: Why Cassandra for swipes?
> Billions of swipes/day = write-heavy workload. Cassandra's LSM-tree architecture is optimized for high write throughput with linear horizontal scaling. No complex joins needed — just point lookups by user_pair.

### Q: How do you handle the "Super Like" feature?
> Super likes bypass normal ranking and appear at the TOP of the target user's stack. Stored with a `direction = 'super_right'` in the swipe table. When generating feed, check a separate "super_like_inbox" first.

### Q: How do you handle the cold-start problem?
> New user with no swipe history → use demographic-based recommendations (popular profiles in their age/location range). As swipe data accumulates, personalize using collaborative filtering (users who swiped similarly to you also liked X).

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
