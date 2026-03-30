# 🐦 Design Twitter — System Design Interview

> **Source:** [Design Twitter w/ a Staff Engineer](https://www.youtube.com/watch?v=Nfa-uUHuFHg)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: The Core Problem — Fan-Out Strategies](#4-deep-dive-1-the-core-problem--fan-out-strategies)
5. [Deep Dive 2: The Celebrity Problem & Hybrid Approach](#5-deep-dive-2-the-celebrity-problem--hybrid-approach)
6. [Deep Dive 3: Feed Ranking & Personalization](#6-deep-dive-3-feed-ranking--personalization)
7. [Deep Dive 4: Trending Topics (Top-K)](#7-deep-dive-4-trending-topics-top-k)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Post Tweet** | Users create tweets (280 chars + media) |
| **Follow/Unfollow** | Follow other users to see their tweets |
| **Home Timeline** | Personalized feed of followed users' tweets |
| **Search** | Full-text search across all public tweets |

### Non-Functional Requirements
| Requirement | Target | Reasoning |
|-------------|--------|-----------|
| **Read-Heavy** | 10:1 reads vs writes | Users read far more than tweet |
| **Low Latency** | Timeline load < 500ms | User experience |
| **Availability** | 99.99%+ | Global social platform |
| **Eventual Consistency** | OK for timeline (seconds delay acceptable) | Trade-off for scale |

### Back-of-Envelope
```
Users: 500M monthly, 200M daily
Tweets: 500M tweets/day → ~6000 writes/sec
Timeline reads: 200M × 5 reads/day = 1B → ~12K reads/sec
Average followers: 200
Median followers: ~50 (power law distribution)
Max followers: 100M+ (celebrities)
```

---

## 2. Core Entities & API Design

### Entities
```
User     → id, username, display_name, followers_count, following_count
Tweet    → id, user_id, text, media_urls[], timestamps, like_count, retweet_count
Follow   → follower_id, followee_id
Timeline → user_id, tweet_ids[] (materialized view)
```

### API
```
POST   /v1/tweets              → { text, media_ids? } → tweet_id
GET    /v1/timeline/home        → Personalized feed (paginated)
GET    /v1/timeline/{userId}    → User's own tweets
POST   /v1/follows              → { target_user_id }
GET    /v1/search?q=            → Full-text tweet search
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌─────────────────┐
│  Client   │───│  API Gateway  │───│  Tweet Service    │
└──────────┘    └──────┬───────┘    └────────┬────────┘
                       │                     │
              ┌────────┼──────────┐   ┌──────┴────────┐
              │        │          │   │  Tweets DB      │
     ┌────────┴──┐  ┌──┴──────┐  │   │ (Cassandra)     │
     │ Timeline   │  │ Follow  │  │   └─────────────────┘
     │ Service    │  │ Service │  │
     └─────┬─────┘  └────┬────┘  │
           │              │      │
     ┌─────┴─────┐  ┌────┴──────┴──┐
     │ Redis      │  │ Graph DB      │
     │ (Timeline  │  │ (Follow       │
     │  cache)    │  │  relationships)│
     └───────────┘  └──────────────┘
```

---

## 4. Deep Dive 1: The Core Problem — Fan-Out Strategies

When User A tweets, 200 followers need to see it. How?

### Strategy 1: Fan-Out on READ (Pull Model)

```
When User B loads home timeline:
  1. Fetch list of all users B follows: [A, C, D, E, ...]
  2. For each followed user, fetch their recent tweets
  3. Merge all tweets → sort by timestamp → return top 50

SQL equivalent:
  SELECT * FROM tweets 
  WHERE user_id IN (SELECT followee FROM follows WHERE follower = B)
  ORDER BY created_at DESC
  LIMIT 50
```

| Pros | Cons |
|------|------|
| ✅ No extra work on tweet creation | ❌ Slow: merge N lists on every read |
| ✅ Simple data model | ❌ Latency: O(followers × fetch_time) |
| ✅ No storage overhead | ❌ Every timeline load = many DB queries |
| ✅ Always up-to-date | ❌ Doesn't scale for 12K reads/sec |

### Strategy 2: Fan-Out on WRITE (Push Model)

```
When User A tweets:
  1. Fetch all of A's followers: [B, C, D, E, ...]
  2. For each follower → PUSH tweet into their timeline cache:
     LPUSH timeline:B tweet_data
     LPUSH timeline:C tweet_data
     LPUSH timeline:D tweet_data

When User B loads home timeline:
  → Simply read from timeline:B (already pre-computed!)
  → LRANGE timeline:B 0 49 → done in O(1)
```

| Pros | Cons |
|------|------|
| ✅ Timeline reads are instant (O(1)) | ❌ Write amplification: 1 tweet → N writes |
| ✅ Data is pre-computed | ❌ Celebrity with 100M followers = 100M writes |
| ✅ Scales reads infinitely | ❌ Delay: tweet appears in followers' feeds async |
| ✅ Heavy lifting is async (background workers) | ❌ Storage: N copies of every tweet |

---

## 5. Deep Dive 2: The Celebrity Problem & Hybrid Approach

### The Problem
```
Lady Gaga has 84M followers.
She tweets → fan-out = 84M Redis writes.
  At 500 tweets/day from celebrities = 42 BILLION writes/day
  → Impossible. System would be constantly doing fan-out.
```

### ✅✅ Hybrid Solution (What Twitter Actually Uses)

```
RULE: 
  "Normal" users (< 10K followers) → Fan-out on WRITE (push)
  "Celebrity" users (> 10K followers) → Fan-out on READ (pull)

Timeline assembly for User B:
  1. Read pre-computed timeline from Redis (pushed tweets): O(1)
  2. Fetch recent tweets from celebrities B follows: 
     SELECT * FROM tweets WHERE user_id IN (celebrity_1, celebrity_2, ...)
  3. Merge + rank + return

Celebrity count per user: typically < 20 ← manageable number of queries
Normal tweets: already in cache ← instant

This is the exact approach described in the video!
```

### Who is a "Celebrity"?
```
Threshold: > 10K followers? > 100K? > 1M?
  → Configuration parameter, tune based on system capacity
  → Monitor: if fan-out workers have high lag → lower the threshold
  → Can be asymmetric: some users "opt in" to pull model
```

---

## 6. Deep Dive 3: Feed Ranking & Personalization

### Beyond Chronological: Relevance Ranking
```
Raw timeline (chronological):
  tweet_1 (1 min ago, from acquaintance)
  tweet_2 (2 min ago, from close friend)
  tweet_3 (5 min ago, celebrity tweet, 50K likes)

Ranked timeline:
  tweet_3 (5 min ago, celebrity, high engagement) ← top because engagement
  tweet_2 (2 min ago, close friend) ← high because relationship
  tweet_1 (1 min ago, acquaintance) ← lower despite recency
```

### Ranking Signals
```
Score = w1*recency + w2*engagement + w3*relationship + w4*content_type

engagement = like_count × 1.0 + retweet_count × 2.0 + reply_count × 3.0
relationship = interaction_frequency(you, author)
content_type = media_boost if has_image/video
recency = exponential_decay(age_in_minutes)
```

---

## 7. Deep Dive 4: Trending Topics (Top-K)

```
Trending = words/hashtags with abnormally HIGH recent frequency

Pipeline:
  1. Stream processor (Flink) consumes all tweets in real-time
  2. Extract hashtags and significant words
  3. Count frequency in sliding windows (5m, 1h, 24h)
  4. Compare current frequency vs baseline → anomaly = trending
  5. Store top-K in Redis sorted set:
     ZADD trending score "#worldcup"

Why anomaly detection, not just "most frequent"?
  → "the" is the most frequent word but never trending
  → "#worldcup" is trending because it's 500x its normal rate
```

---

## 8. Interview Tips & Common Questions

### Q: Why not just use fan-out on write for everyone?
> Lady Gaga tweeting = 84M Redis operations. At 10ms per op = 233 hours of work for ONE tweet. The hybrid approach limits fan-out to <10K followers, keeping the 99th percentile write time under 1 second.

### Q: How do you handle a new follow?
> Backfill: when B follows A, fetch A's recent 100 tweets and merge into B's timeline cache. This is a one-time operation. Going forward, A's tweets are fan-out'd to B normally.

### Q: How do retweets work in the timeline?
> A retweet is treated as a new tweet with a reference to the original. Fan-out happens the same way. When rendering, the client shows "User A retweeted" with the original content.

### Q: How do you handle tweet deletions?
> Mark as deleted in the DB (soft delete). Async: remove from all timeline caches where it was pushed. Accept that some users may briefly see a deleted tweet (eventual consistency).

### Q: Why Cassandra for tweets?
> Write-heavy (500M tweets/day). Cassandra excels at sequential writes (LSM-tree). Partition by user_id for efficient user timeline queries. Time-sorted clustering for chronological order.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
