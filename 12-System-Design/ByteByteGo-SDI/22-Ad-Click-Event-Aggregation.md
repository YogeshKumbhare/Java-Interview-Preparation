# Chapter 22: Ad Click Event Aggregation

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/ad-click-event-aggregation)

Design a system that aggregates ad click events in real-time for reporting, billing, and analytics.

---

## Step 1 - Understand the problem and establish design scope

**Functional:** Aggregate ad click events over the last M minutes, return top N most clicked ads in the last M minutes, support aggregation filtering by different attributes, data accuracy for billing.

**Non-functional:** Correctness (affects billing revenue), handle delayed or duplicate events, robustness and fault tolerance, low latency for queries.

**Estimations:** 1 billion ad clicks/day, 2 million ads, ~10,000 clicks/sec (peak: 50K/sec)

---

## Step 2 - High-level design

### Query API

- `GET /v1/ads/{ad_id}/aggregated_count` — params: from, to, filter
- Returns aggregated click count for an ad within a time range

### Data model

**Raw data (ad_click_event):** ad_id, click_timestamp, user_id, ip, country

**Aggregated data:** ad_id, window_start, window_end, click_count, filter_id

### Architecture

1. **Ad click events** → **Message Queue (Kafka)** → **Aggregation Service** → **Aggregated Data DB**
2. Raw data also stored in a cold storage for reconciliation
3. **Query Service** reads from aggregated DB

### Aggregation strategies

| Strategy | Description |
|----------|-------------|
| MapReduce | Map nodes distribute, Reduce nodes aggregate |
| Stream processing | Apache Flink/Spark Streaming for real-time |

### Java Example – Sliding Window Aggregation

```java
import java.util.*;
import java.util.concurrent.*;

public class AdClickAggregator {
    record ClickEvent(String adId, long timestamp, String userId, String country) {}
    record AggregatedResult(String adId, long windowStart, long windowEnd, long count) {}

    private final Map<String, Map<Long, Long>> aggregations = new ConcurrentHashMap<>();
    private final long WINDOW_SIZE_MS = 60_000; // 1-minute windows

    public void processClick(ClickEvent event) {
        long windowStart = (event.timestamp() / WINDOW_SIZE_MS) * WINDOW_SIZE_MS;
        String key = event.adId();
        aggregations.computeIfAbsent(key, k -> new ConcurrentHashMap<>())
                    .merge(windowStart, 1L, Long::sum);
    }

    public AggregatedResult getAggregated(String adId, long from, long to) {
        Map<Long, Long> windows = aggregations.getOrDefault(adId, Map.of());
        long total = windows.entrySet().stream()
            .filter(e -> e.getKey() >= from && e.getKey() < to)
            .mapToLong(Map.Entry::getValue).sum();
        return new AggregatedResult(adId, from, to, total);
    }

    public List<Map.Entry<String, Long>> getTopN(int n, long windowStart) {
        Map<String, Long> counts = new HashMap<>();
        aggregations.forEach((adId, windows) -> {
            Long c = windows.get(windowStart);
            if (c != null) counts.put(adId, c);
        });
        return counts.entrySet().stream()
            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
            .limit(n).toList();
    }

    public static void main(String[] args) {
        AdClickAggregator agg = new AdClickAggregator();
        long now = System.currentTimeMillis();
        agg.processClick(new ClickEvent("ad_001", now, "u1", "US"));
        agg.processClick(new ClickEvent("ad_001", now + 100, "u2", "US"));
        agg.processClick(new ClickEvent("ad_002", now, "u3", "UK"));
        agg.processClick(new ClickEvent("ad_001", now + 200, "u4", "IN"));

        long windowStart = (now / 60000) * 60000;
        var result = agg.getAggregated("ad_001", windowStart, windowStart + 60000);
        System.out.println("ad_001 clicks: " + result.count());
        System.out.println("Top 2: " + agg.getTopN(2, windowStart));
    }
}
```

---

## Step 3 - Design deep dive

### Time and aggregation window
- **Tumbling window**: Fixed-size, non-overlapping (every 1 min)
- **Sliding window**: Fixed-size, overlapping (last 5 min, refreshed every 1 min)
- **Session window**: Variable length, bounded by inactivity gap

### Handling late/duplicate events
- **Watermark**: Allow a grace period for late events (e.g., 15 min)
- **Exactly-once processing**: Use Kafka + Flink with checkpointing
- **Deduplication**: Use (ad_id, event_timestamp, user_id) as dedup key

### Reconciliation
- Compare real-time aggregated data with batch-processed raw data periodically
- Lambda architecture: real-time (speed layer) + batch (batch layer) + merged (serving layer)

### Fault tolerance
- Use Kafka as a persistent log → replay events on failure
- Flink checkpointing for stateful recovery

---

## Step 4 - Wrap up

Additional talking points:
- **Alternative: store raw events and aggregate on read** (slower but more flexible)
- **Data recalculation**: If aggregation bug found, reprocess from Kafka
- **Multi-tenancy**: Aggregate per advertiser
