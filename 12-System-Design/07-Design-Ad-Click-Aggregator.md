# 📊 Design Ad Click Aggregator — System Design Interview

> **Source:** [Design Ad Click Aggregator w/ a Senior Engineer](https://www.youtube.com/watch?v=Zcv_899yqhI)
> **Full Answer Key:** [hellointerview.com/ad-click-aggregator](https://www.hellointerview.com/learn/system-design/answer-keys/ad-click-aggregator)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Data Flow & System Interface](#2-data-flow--system-interface)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Click Tracking — Client vs Server Redirect](#4-deep-dive-1-click-tracking--client-vs-server-redirect)
5. [Deep Dive 2: Real-Time Aggregation Pipeline](#5-deep-dive-2-real-time-aggregation-pipeline)
6. [Deep Dive 3: Scaling to 10K Clicks/Second](#6-deep-dive-3-scaling-to-10k-clickssecond)
7. [Deep Dive 4: Ensuring No Click Data Is Lost](#7-deep-dive-4-ensuring-no-click-data-is-lost)
8. [Deep Dive 5: Click Fraud Detection & Deduplication](#8-deep-dive-5-click-fraud-detection--deduplication)
9. [Interview Tips & Common Questions](#9-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Click Tracking** | Record every ad click with ad_id, timestamp, user metadata |
| **Real-Time Aggregation** | Aggregate clicks per ad_id in 1-min and 1-hour windows |
| **Analytics Dashboard** | Advertisers view click counts, CTR, spend in real-time |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Accuracy** | Near-exact (eventual reconciliation to exact) | Billing depends on click counts |
| **Latency** | Aggregated data available within 1 minute | Real-time dashboards |
| **Throughput** | 10K+ clicks/second sustained | Super Bowl ads, viral campaigns |
| **No Data Loss** | Zero tolerance | Advertisers pay per click; losing clicks = losing revenue |

---

## 2. Data Flow & System Interface

```
This is a DATA PIPELINE problem, not a traditional CRUD API.

Data Flow:
  User clicks ad → Click event captured → Stream → Aggregate → Store → Query

Click Event:
  { ad_id, impression_id, timestamp, user_id (hashed), ip, referrer }

Query API:
  GET /v1/ads/{adId}/clicks?window=1h   → Click count in last hour
  GET /v1/ads/{adId}/analytics            → CTR, spend, impressions
```

---

## 3. High-Level Architecture

```
┌──────────────┐    ┌────────────────┐    ┌──────────────────┐
│ Ad Placement  │───│ Click Processor │───│ Kafka / Kinesis    │
│ Service (ads) │    │ Service (HTTP)  │    │ (Click Events)    │
└──────────────┘    └────────────────┘    └────────┬─────────┘
                                                   │
                                         ┌─────────┴─────────┐
                           ┌─────────────│  Stream Processor   │
                           │             │ (Flink/Spark)       │
                           │             │ → Windowed Agg       │
                           │             └─────────┬───────────┘
                           │                       │
                    ┌──────┴───────┐      ┌───────┴────────┐
                    │   S3 (Raw     │      │ OLAP DB          │
                    │   Click Logs) │      │ (ClickHouse/     │
                    │   → Batch     │      │  Snowflake)      │
                    │   Reconciliation│    └───────┬────────┘
                    └──────────────┘              │
                                          ┌───────┴────────┐
                                          │ Dashboard API   │
                                          └────────────────┘
```

---

## 4. Deep Dive 1: Click Tracking — Client vs Server Redirect

### ✅ Good Solution: Client-Side Redirect
```
Ad link: <a href="/click?adId=123&dest=https://advertiser.com">
  1. Browser hits /click → server logs click → returns 302 to dest
  2. Browser follows redirect to advertiser.com

Problem: Client-side ad blockers can prevent the /click call
```

### ✅✅ Great Solution: Server-Side Redirect (Hidden from Client)
```
Ad link: <a href="https://ads.example.com/r/abc123">
  1. Server intercepts ALL ad clicks
  2. Decodes impression metadata from URL token
  3. Logs click event to Kafka synchronously
  4. Returns 302 redirect to advertiser URL
  
Benefits:
  → Click capture is transparent (harder to block)
  → No client-side JavaScript needed
  → Server controls the entire flow
```

---

## 5. Deep Dive 2: Real-Time Aggregation Pipeline

### ❌ Bad Solution: Store & Query from Same DB

```
INSERT INTO clicks (ad_id, timestamp, ...) VALUES (?, ?, ...);
SELECT COUNT(*) FROM clicks WHERE ad_id = ? AND timestamp > NOW() - 1 HOUR;
```
**Problem:** At 10K writes/sec, the COUNT query scans millions of rows → slow, blocks writes.

### ✅ Good Solution: Separate Analytics DB with Batch Processing

```
Write raw clicks → S3 (append-only log)
Batch job (hourly): Spark reads S3 → aggregates → writes to OLAP DB
```
**Problem:** 1-hour delay. Not real-time.

### ✅✅ Great Solution: Stream Processing (Flink/Kafka Streams)

```
Kafka → Flink Job:
  1. Read click events from Kafka
  2. Key by ad_id
  3. Tumbling windows: 1-minute aggregation
     for each window: { ad_id, window_start, click_count, unique_users }
  4. Write aggregated results to OLAP DB (ClickHouse)
  5. Larger windows (1h, 24h) = materialized from 1-min windows

Flink Windowed Aggregation:
  clickStream
    .keyBy(event -> event.adId)
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .aggregate(new ClickCountAggregator())
    .addSink(clickhouseSink);
```

### ✅✅ Exactly-Once Semantics: Critical for Billing Accuracy

> This is the **#1 correctness guarantee** needed — advertiser billing depends on click counts being exact.

```
How Flink achieves Exactly-Once (2-Phase Commit):

Phase 1: CHECKPOINT (Flink's internal commit)
  - Flink takes periodic state snapshots (checkpoints) to durable storage (S3/HDFS)
  - Checkpoint includes: Kafka consumer offset + aggregation state + output buffers
  
Phase 2: COMMIT (Kafka Transactional Producer)
  - Flink uses Kafka's transactional API to write results atomically
  - Only committed AFTER the checkpoint is confirmed durable
  
Recovery after crash:
  - Flink restarts from the last successful checkpoint
  - Replays Kafka events from the saved offset
  - Re-applies UNcommitted events → produces same aggregate
  - Outputs the result → commits → exactly-once guaranteed

Without this: at-least-once (may over-count clicks → over-bill advertisers)
```

---

## 6. Deep Dive 3: Scaling to 10K Clicks/Second

### Component-by-Component Scaling

```
1. Click Processor Service:
   → Stateless HTTP service
   → Horizontally scale + load balancer
   → Auto-scale based on CPU/request rate

2. Kafka/Kinesis:
   → Sharding by ad_id (natural choice)
   → Kinesis: 1MB/s or 1000 records/s per shard
   → 10K clicks/s × 100 bytes = 1MB/s → need ~10 shards
   → All events for same ad_id → same shard → correct aggregation

3. Flink (Stream Processor):
   → Separate job per shard → horizontal scaling
   → Each job aggregates its subset of ad_ids
   → Auto-scale based on Kafka consumer lag

4. OLAP DB (ClickHouse/Snowflake):
   → Pre-aggregated data: ~600 writes/min (10K ads × 1 row/min)
   → This is a TINY write load → single node handles it
   → Read queries: point queries by ad_id → indexed, fast
```

### Hot Shards Problem
```
Super Bowl ad: 1 ad gets 50% of all clicks → hot shard!

Solution:
  → Shard by ad_id + random salt:
    Key: "ad_123:0", "ad_123:1", "ad_123:2" (3 sub-shards)
  → Each sub-shard processes independently
  → Merge in OLAP DB: SUM(click_count) WHERE ad_id = 123
```

---

## 7. Deep Dive 4: Ensuring No Click Data Is Lost

### Lambda Architecture (Fast + Slow Path)

```
FAST PATH (Real-Time):
  Kafka → Flink → ClickHouse (approximate, low latency)
  → Available within seconds
  → May have minor inaccuracies (late events, system hiccups)

SLOW PATH (Batch Reconciliation):
  Kafka → S3 (raw logs, all events, durable)
  → Spark batch job runs every hour
  → Scans ALL raw events → produces exact aggregate counts
  → Overwrites ClickHouse with "ground truth" numbers

Why both?
  → Real-time: advertisers see trends as they happen
  → Batch: billing is based on EXACT reconciled numbers
  → Discrepancy? Batch always wins (source of truth)
```

---

## 8. Deep Dive 5: Click Fraud Detection & Deduplication

### ❌ Bad Solution: Add userId to Click Payload
```
Assume user is logged in → use userId to dedup
Problem: most ad clicks are from anonymous users (no userId)
```

### ✅✅ Great Solution: Impression-Based Deduplication

```
Step 1: Ad Placement Service generates unique impression_id per ad shown
        impression_id = UUID + signature (signed with server secret key)

Step 2: When ad is shown → impression_id sent to browser with the ad

Step 3: User clicks ad → browser sends impression_id with click event

Step 4: Click Processor:
  a. Verify signature of impression_id (prevents fabricated clicks)
  b. Check Redis/cache: has this impression_id been seen?
     → EXISTS: duplicate click → ignore
     → NOT EXISTS: write to Kafka (stream) FIRST → then add to cache

Why write to stream BEFORE cache?
  → If cache update fails → we might see the impression again (duplicate)
  → BUT duplicates are caught later by batch reconciliation
  → If stream write fails → we LOSE the click forever
  → Lost clicks CANNOT be recovered
  → Occasional duplicates CAN be reconciled → safer ordering
```

---

## 9. Interview Tips & Common Questions

### Q: Why not just use a counter in Redis?
> INCR operations in Redis are fast but NOT durable. Redis crash = lost counts. Kafka + S3 provide durability. Redis can be used for real-time approximate counters, but billing requires the durable batch reconciliation path.

### Q: How do you handle late-arriving events?
> Flink supports watermarks for event-time processing. Late events (within a grace period) are handled by updating the existing window. Very late events fall to the batch reconciliation path.

### Q: Why an OLAP database (ClickHouse) instead of PostgreSQL?
> ClickHouse is columnar → aggregation queries (SUM, COUNT by ad_id) are 100x faster than row-oriented PostgreSQL. It's optimized for append-heavy, query-heavy analytical workloads.

### Q: How does click-through rate (CTR) work?
> CTR = clicks / impressions. The Ad Placement Service tracks impressions. The Click Processor tracks clicks. Join both datasets in the OLAP DB: `SELECT clicks/impressions FROM ad_stats WHERE ad_id = ?`.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
