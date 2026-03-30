# 📰 Design Facebook News Feed — System Design Interview

> **Source:** [Design FB News Feed w/ a Senior Manager](https://www.youtube.com/watch?v=Qj4-GruzyDU)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Feed Generation — Pull vs Push vs Hybrid](#4-deep-dive-1-feed-generation--pull-vs-push-vs-hybrid)
5. [Deep Dive 2: Feed Ranking (EdgeRank / ML)](#5-deep-dive-2-feed-ranking-edgerank--ml)
6. [Deep Dive 3: Feed Storage & Caching](#6-deep-dive-3-feed-storage--caching)
7. [Deep Dive 4: Handling Non-Friend Content (Suggested Posts)](#7-deep-dive-4-handling-non-friend-content-suggested-posts)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Create Posts** | Users create text/image/video posts |
| **News Feed** | Personalized feed of friends' and suggested content |
| **Interactions** | Like, comment, share on posts |
| **Infinite Scroll** | Paginated feed loading on demand |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Low Latency** | Feed loads < 500ms | User retention |
| **Scalability** | 2B+ users, median ~500 friends | Facebook scale |
| **Eventual Consistency** | OK (seconds delay) | Not financial data |
| **Personalization** | ML-ranked, not chronological | Engagement optimization |

---

## 2. Core Entities & API Design

### Entities
```
User     → id, name, friends[], interests
Post     → id, user_id, text, media_urls[], created_at, like_count, comment_count
Feed     → user_id, feed_items[{ post_id, score, source }] (materialized)
Friendship → user_a, user_b, created_at
```

### API
```
POST   /v1/posts                    → { text, media_ids } → post_id
GET    /v1/feed?cursor=&page_size=  → Personalized feed page
POST   /v1/posts/{id}/like          → Like/unlike a post
POST   /v1/posts/{id}/comment       → Add a comment
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌─────────────────┐
│  Client   │───│  API Gateway  │───│  Post Service     │
└──────────┘    └──────┬───────┘    └────────┬────────┘
                       │                     │
              ┌────────┴───────┐    ┌────────┴────────┐
              │  Feed Service   │    │   Posts DB       │
              │ (Ranking +     │    │  (Cassandra)      │
              │  Assembly)     │    └─────────────────┘
              └────────┬───────┘
                       │
              ┌────────┼──────────┐
              │        │          │
     ┌────────┴──┐  ┌──┴──────┐  ┌──┴───────────┐
     │ Redis      │  │ Fan-Out  │  │ ML Ranking    │
     │ (Pre-computed│  │ Workers  │  │ Service       │
     │  feed cache)│  │ (Kafka)  │  └──────────────┘
     └───────────┘  └──────────┘
```

---

## 4. Deep Dive 1: Feed Generation — Pull vs Push vs Hybrid

### Pull Model (Fan-Out on Read)
```
When User A opens feed:
  1. Fetch A's friend list: [B, C, D, E, ...]  (500 friends avg)
  2. For each friend: fetch recent posts
  3. Merge all posts → rank by ML model → return top 50

Pros: No pre-computation, always fresh
Cons: SLOW (500 DB calls per feed load at 200M DAU = disaster)
```

### Push Model (Fan-Out on Write)
```
When User B creates a post:
  1. Fetch B's friend list: [A, C, D, ...]
  2. For each friend: push post into their pre-computed feed cache
     LPUSH feed:A post_data
     LPUSH feed:C post_data

When User A opens feed:
  → LRANGE feed:A 0 49 → instant read from cache

Pros: Feed reads are O(1) — instant
Cons: Celebrity with 10M friends → 10M writes per post → expensive
```

### ✅✅ Hybrid Model (What Facebook Uses)
```
Normal users (< 5K friends) → PUSH model
  → Their posts are pushed to friends' feeds on write
  → Fast, pre-computed, cached

Celebrity/Pages (> 5K friends) → PULL model
  → Their posts are NOT pushed — too expensive
  → On feed load: pull celebrity posts + merge with cached friend posts

Feed Assembly (on read):
  1. Read pre-computed feed from Redis: [post_1, post_2, ...post_40]
  2. Fetch recent posts from followed celebrities/pages: [post_A, post_B]
  3. Merge → ML Ranking Service scores all candidates → return top 50
```

---

## 5. Deep Dive 2: Feed Ranking (EdgeRank / ML)

Facebook's ranking is the MOST important differentiator from a simple timeline.

### EdgeRank (Original Algorithm)
```
Score = Σ(Affinity × Weight × Decay)

Affinity: How close is the viewer to the poster?
  → Based on: messages sent, profile views, interaction frequency
  → Higher affinity for family, close friends → their posts rank first

Weight: What type of content is it?
  → Video > Photo > Link > Text (video = highest engagement)
  → Live video > pre-recorded

Decay: How old is the post?
  → Exponential decay: e^(-λ × age_minutes)
  → Recent posts score higher
  → But viral old posts with high engagement can overcome decay
```

### Modern ML Ranking (3-Pass Pipeline — Meta's Real System)

> **EdgeRank was deprecated by Facebook in 2012.** Modern Facebook uses a three-pass deep learning pipeline. Don't just mention EdgeRank in interviews — pivot to this modern explanation.

```
PASS 0 — CANDIDATE RETRIEVAL (milliseconds, cheap):
  Input: 1 billion+ posts from friends, groups, pages, recommendations
  → Simple logistic regression or embedding-based lookup
  → Hard filters: already-seen posts? blocked user? privacy violation?
  → Output: ~10,000 rough candidates

PASS 1 — MAIN RANKING (heavy DNN, ~50ms):
  Input: 10,000 candidates
  → Deep Neural Network predicts multiple objectives PER post:
    P(click_like)         → will user like?
    P(comment)            → will user write a comment?
    P(share)              → will user share?
    P(dwell_time > 30s)   → will user actually READ this?
    P(hide)               → will user hide this post? (← NEGATIVE signal)
    P(report)             → will user report as spam? (← VERY NEGATIVE)
  → Composite score = Σ(weight_i × P(action_i))
    weights tuned to maximize "meaningful social interactions"
  → Output: Top 500 scored candidates

PASS 2 — RE-RANKING / BUSINESS RULES (context-aware):
  Input: 500 top-scored candidates
  Apply hard rules the DNN doesn't handle:
  → DIVERSITY: no more than 3 consecutive posts from same author
  → FRESHNESS: inject recent breaking news even if slightly lower score
  → INTEGRITY: harm/spam classifier → demote or remove dangerous content
  → ADS: insert paid content at fixed positions (every 5th-6th post)
  → FORMAT BALANCE: mix video/photo/text/link (avoid all-video feeds)
  → Output: 50-150 posts → user's next scroll

Why 3 passes?
  → Can't run DNN on 1 billion posts (1 billion × 50ms = impossible)
  → Can't apply business rules in DNN weights (rules change daily)
  → Pass 0 reduces the problem by 100,000x before expensive models run
```

---

## 6. Deep Dive 3: Feed Storage & Caching

### Pre-Computed Feed in Redis
```
Key: feed:{userId}
Value: Sorted set or list of post references

ZADD feed:user123 score "post_456"
ZADD feed:user123 score "post_789"

Max feed size: 500 posts per user (LRU eviction)
TTL: 7 days (if user hasn't logged in, rebuild on next visit)
```

### Post Content Caching
```
Feed stores post REFERENCES (IDs), not full content.
Hydration: Fetch full post content from Posts DB or Post Cache.

Post cache (Redis):
  Key: post:{postId}
  Value: { text, media_urls, user_name, like_count, ... }
  TTL: 24 hours

Two-layer read:
  1. Get post IDs from feed cache → [456, 789, ...]
  2. MGET post:456 post:789 ... from post cache
  3. Cache misses → batch query Cassandra → populate cache
```

### Fan-Out Worker Pipeline
```
User B posts → Kafka topic "new_posts"
  → Fan-Out Workers consume:
    1. Fetch B's friend list
    2. For each friend:
       ZADD feed:{friend_id} score post_id
    3. If friend is online (has WebSocket):
       Push notification: "New post from B"

Workers are horizontally scaled:
  → Auto-scale based on Kafka consumer lag
  → During peak hours (8-10pm): scale up
```

---

## 7. Deep Dive 4: Handling Non-Friend Content (Suggested Posts)

```
Modern feeds include ~30% non-friend content:
  → Suggested posts from Pages you follow
  → "Suggested for you" from recommendation engine
  → Ads (separate ad placement system)
  → Group posts from joined groups

Integration:
  Stage 1 candidates =  friend posts (push) 
                       + followed page posts (pull)
                       + recommendation engine posts (pull)
                       + ads (from ad server)
  
  Stage 2 ranking: ML model treats ALL candidates equally
    → Friend posts might rank LOWER than a viral suggested post
    → Ads are inserted at fixed intervals (every 5th post)
```

---

## 8. Interview Tips & Common Questions

### Q: How does Facebook handle 2B users with ~500 friends each?
> Hybrid fan-out is key. 99% of users have < 5K friends → push model handles them efficiently. Only ~1% are high-follower accounts → pull model for those. Pre-computed feed in Redis makes reads instant.

### Q: How do you handle post deletions?
> Remove from source DB (soft delete). Async: remove from all friend feed caches. Next feed load: filter out deleted posts. Accept brief delay (seconds) — user may see a deleted post briefly.

### Q: How do you prevent echo chambers / filter bubbles?
> Diversity injection: ML model includes diversity as a ranking signal. Periodically inject content from outside the user's usual circle. Show "trending" content regardless of social graph. This is a product decision, not a pure engineering one.

### Q: What's the difference between News Feed and Twitter Timeline?
> Twitter = mostly chronological with some ranking. Facebook = heavily ML-ranked. Twitter uses fan-out-on-write with hybrid for celebrities. Facebook uses the same fan-out hybrid but with much heavier ranking.

### Q: How do you handle the "cold start" problem?
> New user with no friends → serve globally popular content + content based on signup interests. As user adds friends and interacts → personalization improves. Bootstrap period: ~1 week of usage data.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
