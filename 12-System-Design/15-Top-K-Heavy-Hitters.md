# 🏆 Top-K / Heavy Hitters — System Design Interview

> **Source:** [Top-K System Design Interview w/ Ex-Meta Senior Manager](https://www.youtube.com/watch?v=y-tA2NW4LNY)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Why Naive Solutions Fail](#4-deep-dive-1-why-naive-solutions-fail)
5. [Deep Dive 2: Count-Min Sketch (Frequency Estimation)](#5-deep-dive-2-count-min-sketch-frequency-estimation)
6. [Deep Dive 3: Space-Saving Algorithm (Direct Top-K Tracking)](#6-deep-dive-3-space-saving-algorithm-direct-top-k-tracking)
7. [Deep Dive 4: Multi-Layer Streaming Aggregation](#7-deep-dive-4-multi-layer-streaming-aggregation)
8. [Deep Dive 5: Windowed Aggregation & Time Decay](#8-deep-dive-5-windowed-aggregation--time-decay)
9. [Deep Dive 6: Fast Path + Slow Path Architecture](#9-deep-dive-6-fast-path--slow-path-architecture)
10. [Interview Tips & Common Questions](#10-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Top-K Items** | Return the K most frequent items in a given time window |
| **Real-Time** | Updates within seconds as new events arrive |
| **Configurable Windows** | Last 1 min, 5 min, 1 hour, 24 hours |
| **Query API** | API to fetch current top-K for any supported window |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Throughput** | Millions of events/second | High-scale platforms |
| **Latency** | Query response < 100ms | Dashboard/real-time use |
| **Accuracy** | Approximate OK (bounded error) | Exact counting is too expensive |
| **Scalability** | Horizontal scaling with data volume | Event volume grows |

### Use Cases
```
- Trending Hashtags (Twitter/X)
- Top Searched Queries (Google Autocomplete)
- Most Viewed Videos (YouTube)
- Most Sold Products (Amazon)
- Most Active Error Codes (Monitoring)
```

---

## 2. Core Entities & API Design

### API
```
GET /v1/topk?k=10&window=5m    → Top 10 items in last 5 minutes
GET /v1/topk?k=50&window=1h    → Top 50 items in last 1 hour
GET /v1/frequency/{itemId}      → Estimated frequency of a specific item
```

---

## 3. High-Level Architecture

```
┌──────────────┐    ┌──────────────┐    ┌─────────────────────┐
│ Event Sources │───│    Kafka       │───│ Stream Processor     │
│ (clicks, views│    │ (Partitioned) │    │ (Flink/Kafka Streams)│
│  searches)    │    │               │    │                     │
└──────────────┘    └──────────────┘    │ ┌─────────────────┐ │
                                        │ │ Count-Min Sketch │ │
                                        │ │ or Space-Saving  │ │
                                        │ └─────────────────┘ │
                                        └─────────┬───────────┘
                                                  │
                                        ┌─────────┴───────────┐
                                        │   Redis Sorted Set    │
                                        │  (Top-K results)      │
                                        └─────────┬───────────┘
                                                  │
                                        ┌─────────┴───────────┐
                                        │   API / Query Layer   │
                                        └─────────────────────┘
```

---

## 4. Deep Dive 1: Why Naive Solutions Fail

### Naive: HashMap + Min Heap
```python
# Track count for every item:
counts = {}              # item_id → count
min_heap = MinHeap(K)    # maintains top K items

def process_event(item_id):
    counts[item_id] = counts.get(item_id, 0) + 1
    # Update heap with new count...
```

**Why this fails at scale:**
```
1 billion unique items × 50 bytes per entry = 50 GB of RAM
→ Doesn't fit in memory of one machine
→ Distributed HashMap = complex, slow
→ Most items are in the "long tail" — counted once and never again
→ We're wasting memory tracking items we'll never report
```

**Key insight from the video:** We want the top 10 items out of 1 billion. We don't need to track all 1 billion. We need **approximate data structures** that use bounded memory.

---

## 5. Deep Dive 2: Count-Min Sketch (Frequency Estimation)

### How It Works
```
A 2D matrix of counters: d rows × w columns
d = number of hash functions (typically 5)
w = number of columns (typically 10,000)

For each event (item_id):
  hash_1(item_id) mod w → increment counter[0][h1]
  hash_2(item_id) mod w → increment counter[1][h2]
  hash_3(item_id) mod w → increment counter[2][h3]
  hash_4(item_id) mod w → increment counter[3][h4]
  hash_5(item_id) mod w → increment counter[4][h5]

To QUERY frequency of item X:
  return MIN(
    counter[0][hash_1(X) mod w],
    counter[1][hash_2(X) mod w],
    counter[2][hash_3(X) mod w],
    counter[3][hash_4(X) mod w],
    counter[4][hash_5(X) mod w]
  )
  
Why MIN? Each counter may have COLLISIONS (other items hashing to same cell).
Collisions only ADD, never subtract → overestimates.
Taking MIN across independent hash functions minimizes overestimate.
```

### Properties
```
✅ Fixed memory: O(d × w) regardless of unique items
   5 × 10,000 = 50,000 counters × 8 bytes = 400KB
   → Tracks frequency of BILLIONS of items in 400KB!

✅ O(d) update and query time (5 hash computations)

❌ OVERESTIMATES counts (due to hash collisions)
❌ Never underestimates
❌ Can't enumerate items (can only query specific items)

Error bound:
  ε = e / w   (e = Euler's number ≈ 2.718)
  With w = 10,000: ε = 0.027%
  Overcount per item ≤ ε × total_events
  With 1M events: max overcount ≤ 270
```

### For Top-K: CMS + Min Heap
```
Maintain a Min Heap of size K alongside the CMS:
  1. For each event → update CMS
  2. Get estimated count from CMS
  3. If estimated count > min(heap):
     → Replace heap minimum with this item + new count
  4. Heap always contains approximate top-K
```

---

## 6. Deep Dive 3: Space-Saving Algorithm (Direct Top-K Tracking)

### How It Works
```
Fixed-size table of K entries: { item_id, count, error_bound }

For each event:
  IF item_id exists in table:
    → increment its count ← easy

  IF item_id NOT in table:
    → Find the entry with SMALLEST count (min_count)
    → Replace it: { item_id = new_item, count = min_count + 1, error = min_count }
    → Key insight: the new item's count is AT LEAST min_count + 1
       because if it weren't, it would have been evicted earlier

Properties:
  ✅ Directly maintains top-K (no separate heap needed)
  ✅ Better accuracy for actual top items than CMS
  ✅ Fixed memory: O(K) entries
  ✅ Error bound per item is KNOWN (stored in error field)
  ❌ Slightly more complex
```

### Comparison
| Feature | Count-Min Sketch | Space-Saving |
|---------|-----------------|--------------|
| **Memory** | Fixed (d × w counters) | Fixed (K entries) |
| **Best For** | Frequency estimation of ANY item | Tracking ONLY the top-K |
| **Error Type** | Overestimates all queries | Bounded error for top items |
| **Can Enumerate** | No (need external heap) | Yes (table IS the top-K) |
| **Use Case** | "How many times was X seen?" | "What are the top 10?" |

> **Interview Tip:** Space-Saving is simpler to explain and directly answers the Top-K question. CMS is more versatile (supports arbitrary frequency queries). Present Space-Saving as your primary, mention CMS as an alternative.

---

## 7. Deep Dive 4: Multi-Layer Streaming Aggregation

```
With 100 Flink workers, each sees a SUBSET of events.
No single worker sees ALL events. How do we get global top-K?

LAYER 1: LOCAL aggregation (per Flink worker)
  → Each worker maintains its own CMS or Space-Saving
  → Processes events from its assigned Kafka partition
  → Periodically (every 5 sec) emits local top-K candidates:
    { item: "hashtag_worldcup", count: 47,293 }
    { item: "hashtag_superbowl", count: 31,107 }

LAYER 2: GLOBAL merge (centralized or few nodes)
  → Receives local top-K from ALL 100 workers
  → Merges counts per item:
    ZINCRBY topk:5min "hashtag_worldcup" 47293
    ZINCRBY topk:5min "hashtag_superbowl" 31107
  → Redis sorted set maintains the global ranking
  → ZREVRANGE topk:5min 0 K-1 → final global top-K

This is a MAP → REDUCE pattern:
  Map (workers): process events locally → emit partial results
  Reduce (merger): combine partial results → emit final answer
```

---

## 8. Deep Dive 5: Windowed Aggregation & Time Decay

### Tumbling Windows (Non-Overlapping)
```
|---1min---|---1min---|---1min---|
  Window 1    Window 2    Window 3

Each window independently counts events.
At window close → emit results → reset counters.
Flink: .window(TumblingEventTimeWindows.of(Time.minutes(1)))
```

### Rolling Up Windows
```
1-minute windows are the base resolution.
Larger windows roll up from smaller ones:

5-minute window = combine last 5 one-minute windows
1-hour window = combine last 60 one-minute windows
24-hour window = combine last 24 one-hour windows

Maintain separate Redis sorted sets:
  topk:1m:{windowId}
  topk:5m:{windowId}  
  topk:1h:{windowId}
```

### Exponential Time Decay (For Trending)
```
"Trending" ≠ "Most frequent all-time"
"Trending" = "Abnormally high frequency RIGHT NOW compared to baseline"

Decayed Score = count × e^(-λ × age_in_minutes)

Example (λ = 0.01):
  Item A: 1000 counts, 1 hour ago → 1000 × e^(-0.6) = 549
  Item B: 500 counts, 5 min ago  → 500 × e^(-0.05) = 475
  
  Item A has 2x total counts but Item B is TRENDING because it's fresher.
  
  With stronger decay (λ = 0.05):
  Item A: 1000 × e^(-3.0) = 50  ← faded significantly
  Item B: 500 × e^(-0.25) = 389 ← still strong
```

---

## 9. Deep Dive 6: Fast Path + Slow Path Architecture

```
FAST PATH (Real-Time, Approximate):
  Kafka → Flink (CMS / Space-Saving) → Redis sorted set
  → Updated every 5 seconds
  → Serves dashboard queries instantly
  → Approximate (bounded error from data structures)

SLOW PATH (Batch Reconciliation, Exact):
  Kafka → S3 (raw event logs, durable)
  → Spark batch job runs hourly
  → Scans ALL events → produces EXACT counts
  → Updates "ground truth" sorted sets in Redis

Why both:
  → Fast path: stakeholders see trends as they happen
  → Slow path: reporting uses EXACT numbers (compliance, billing)
  → Discrepancy is small and temporary (within error bounds)
```

---

## 10. Interview Tips & Common Questions

### Q: Why not just use a HashMap in Redis?
> HashMap with HGET/HSET doesn't maintain sorted order. You'd need to scan all keys to find top-K → O(N). Redis sorted set (ZADD/ZREVRANGE) maintains order at O(log N) insert, O(K) for top-K. At billions of unique items, even Redis can't hold a full HashMap — bounded data structures (CMS) are essential.

### Q: How do you handle data skew (hot items)?
> Hot items create "hot partitions" in Kafka. Solution: random partition key suffix: `item_123:shard_0`, `item_123:shard_1`. Distributes load across partitions. The global merge layer sums across shards.

### Q: How accurate is Count-Min Sketch?
> Error bounded by ε = e/w. With w = 10,000 and d = 5 hash functions, overcount per item ≤ 0.027% × total events. For top items with millions of counts, the error is negligible (< 1%). Good enough for trending.

### Q: How do you support multiple time windows?
> 1-minute windows are the base. Roll up into 5m, 1h, 24h by combining base windows. Maintain separate Redis sorted sets per window granularity.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
