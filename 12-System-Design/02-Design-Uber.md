# 🚗 Design Uber — System Design Interview

> **Source:** [Design Uber w/ a Staff Engineer](https://www.youtube.com/watch?v=lsKU38RKQSo)
> **Full Answer Key:** [hellointerview.com/uber](https://www.hellointerview.com/learn/system-design/answer-keys/uber)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: How Do We Handle Driver Location Updates & Proximity Searches?](#4-deep-dive-1-how-do-we-handle-driver-location-updates--proximity-searches)
5. [Deep Dive 2: How Do We Prevent Race Conditions in Ride Matching?](#5-deep-dive-2-how-do-we-prevent-race-conditions-in-ride-matching)
6. [Deep Dive 3: How Do We Handle High Request Volume at Scale?](#6-deep-dive-3-how-do-we-handle-high-request-volume-at-scale)
7. [Deep Dive 4: What If a Driver Fails to Respond?](#7-deep-dive-4-what-if-a-driver-fails-to-respond)
8. [Deep Dive 5: Geo-Sharding with Read Replicas](#8-deep-dive-5-geo-sharding-with-read-replicas)
9. [What is Expected at Each Level?](#9-what-is-expected-at-each-level)
10. [Interview Tips & Common Questions](#10-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Fare Estimation** | Rider inputs start/destination → gets estimated fare |
| **Ride Request** | Rider requests a ride based on the fare estimate |
| **Driver Matching** | System matches nearest available driver to rider |
| **Accept/Decline** | Driver can accept or decline the ride request |
| **Real-Time Tracking** | Rider tracks driver's live location on map |
| **Trip Navigation** | Driver gets navigation to pickup & dropoff |

### Non-Functional Requirements
| Requirement | Target | Reasoning |
|-------------|--------|-----------|
| **Low Latency** | Matching < 1s | Users expect instant response |
| **High Availability** | 99.99% | Ride-hailing is critical infrastructure |
| **Scalability** | 10M+ concurrent drivers sending locations every 5s | That's ~2M location updates/second |
| **Consistency** | One driver matched to one ride only | Double-matching is unacceptable |

---

## 2. Core Entities & API Design

### Entities
```
Rider    → id, name, location, payment_info
Driver   → id, name, location, status (Available|OnTrip|Offline), vehicle_info
Ride     → id, rider_id, driver_id, pickup, dropoff, status, fare, created_at
          status: REQUESTED → MATCHED → PICKUP → IN_PROGRESS → COMPLETED
Location → driver_id, lat, lng, timestamp, heading, speed
```

### API
```
POST   /v1/rides/estimate       → { pickup, dropoff } → estimated fare + ETA
POST   /v1/rides/request        → { pickup, dropoff } → ride_id
POST   /v1/rides/{id}/accept    → Driver accepts ride
POST   /v1/rides/{id}/decline   → Driver declines ride
POST   /v1/rides/{id}/start     → Begin trip
POST   /v1/rides/{id}/complete  → End trip + calculate fare
PUT    /v1/drivers/location     → Driver sends GPS: { lat, lng, timestamp }
GET    /v1/rides/{id}/status    → Ride status + driver location
```

---

## 3. High-Level Architecture

```
┌──────────┐         ┌──────────────┐
│  Rider   │◄──WS───│  WebSocket    │
│   App    │         │  Gateway      │
└────┬─────┘         └──────┬───────┘
     │                       │
┌────┴─────┐         ┌──────┴───────┐      ┌────────────────┐
│  Driver  │◄──WS───│  API Gateway   │─────│Ride Matching    │
│   App    │         │               │      │Service          │
└──────────┘         └──────┬───────┘      └────────┬───────┘
                            │                       │
                     ┌──────┴───────┐      ┌────────┴────────┐
                     │ Ride Service  │      │ Location Service │
                     └──────┬───────┘      └────────┬────────┘
                            │                       │
                     ┌──────┴───────┐      ┌────────┴────────┐
                     │ PostgreSQL   │      │   Redis GEO      │
                     │ (Ride data)  │      │ (Driver locations)│
                     └──────────────┘      └─────────────────┘
```

---

## 4. Deep Dive 1: How Do We Handle Driver Location Updates & Proximity Searches?

This is THE most important deep dive. 10M drivers × 1 update every 5s = **2 million writes/second**.

### ❌ Bad Solution: Direct Database Writes + Proximity Queries

```sql
-- Driver sends location update:
UPDATE drivers SET lat = 40.7128, lng = -74.0060 WHERE id = 123;

-- Finding nearby drivers:
SELECT * FROM drivers 
WHERE status = 'AVAILABLE'
  AND ST_Distance(location, ST_MakePoint(-74.0060, 40.7128)) < 5000;
```

**Why it's terrible:**
- 2M writes/sec → PostgreSQL/DynamoDB will either **fall over** or cost a fortune
- Without spatial index → **full table scan** across millions of rows per query
- Even with B-tree index: B-trees are terrible for 2D coordinate data
- Latency: 100-500ms per proximity query → unacceptable

### ✅ Good Solution: Batch Processing + Geospatial Database (PostGIS/Quadtree)

```
- Buffer location updates in memory, flush to PostGIS/DynamoDB every few seconds
- Use PostGIS for spatial queries (R-tree spatial index)
- Use Quadtrees for adaptive resolution
```

**Why it's better but still not great:**
- ✅ Spatial indexes make proximity queries efficient
- ❌ Still hitting persistent storage for ephemeral data
- ❌ Location data is ephemeral — drivers move every 5 seconds → no need for durability
- ❌ Batch processing introduces staleness

### ✅✅ Great Solution: Real-Time In-Memory Geospatial Store (Redis)

```
Redis GEO Commands:
  GEOADD drivers:available -73.9857 40.7484 driver_123
  GEOADD drivers:available -73.9901 40.7340 driver_456

  -- Find all available drivers within 3 km:
  GEOSEARCH drivers:available FROMLONLAT -73.9857 40.7484 BYRADIUS 3 km ASC COUNT 10

Geohashing Under the Hood:
  Redis converts (lat, lng) → 52-bit geohash → stores in sorted set
  GEOSEARCH = range query on sorted set → O(log N + M)
```

### ✅✅ Industry Reality: Uber's Actual Production System — H3 Hexagonal Grid

> **Source: Uber Engineering Blog** — Uber uses H3, a hierarchical hexagonal grid system developed and open-sourced by Uber, not plain Geohashing.

```
Why hexagons beat squares (Geohash cells):
  Square grid: corner-to-center distance ≠ edge-to-center distance
               → uneven neighbor distances → inaccurate "within N km" queries
  Hexagon grid: ALL 6 neighboring cell centers are EQUIDISTANT from each
               center cell → perfect radial symmetry → highly accurate proximity

H3 Hierarchy (15 resolution levels):
  Resolution 0  → coarsest (continent-scale)
  Resolution 7  → ~5km² per cell ≈ city block ← ideal for ride matching
  Resolution 12 → ~8,000m² per cell ← surge pricing precision
  Resolution 15 → finest (~cm precision)

Uber's Usage:
  1. Each driver's location maps to their H3 cell (mostly resolution 7)
  2. Rider requests → query driver's cell + 6 neighboring cells
  3. Surge pricing: compute demand/supply ratio per H3 cell
     → demand (ride requests) / supply (available drivers) > threshold → surge
  4. H3 cells visible in the Uber app as hexagonal price zones

Geospatial Options Compared:
  H3 (Hex grid) → Uber's choice, equal neighbor distances, hierarchical
  Geohash       → string prefix-based, simpler but rectangular cells
  Google S2     → spherical geometry cells, supports arbitrary polygon queries
  QuadTree      → recursive 2D partitioning, adaptive density, tree structure
```

**Why it's the best:**
- ✅ **Sub-millisecond** reads and writes
- ✅ Handles 2M writes/sec easily
- ✅ No durability needed — location data is ephemeral
- ✅ Geohash-based proximity queries are O(log N)
- ✅ Only store AVAILABLE drivers (not OnTrip/Offline)

**Handling Redis failures:**
- Redis Sentinel: automatic failover with replica promotion
- Redis persistence: RDB snapshots or AOF for recovery (optional — data reconstructs within seconds from live driver pings)

### ✅✅ Great Addition: Adaptive Location Update Intervals

```
Driver is idle (waiting for rides):
  → Send location every 30 seconds (low frequency)
  
Driver has a ride match pending:
  → Send location every 3 seconds (high frequency)
  
Driver is on a trip (rider tracking):
  → Send location every 1-2 seconds (highest frequency)

Why: Reduces the 2M writes/sec baseline significantly
     Most drivers are idle → 30s interval → maybe 300K writes/sec total
```

---

## 5. Deep Dive 2: How Do We Prevent Race Conditions in Ride Matching?

Two riders request rides simultaneously. Both get matched to the same driver. Only one should win.

### ❌ Bad Solution: Application-Level Locking

```python
# In the Ride Matching Service:
if driver.status == 'AVAILABLE':
    driver.status = 'MATCHED'
    # ...assign ride
```

**Problem:** With multiple service instances, there's no coordination. Two instances both read status=AVAILABLE before either writes the update. → Both riders think they're matched.

### ✅ Good Solution: Database Status Update with Atomic Check

```sql
UPDATE drivers SET status = 'MATCHED', ride_id = ?
WHERE id = ? AND status = 'AVAILABLE';

-- Check rows_affected:
-- If 1 → success, this rider got the driver
-- If 0 → driver already taken, try next candidate
```

**Why it helps:** Atomic row-level update = natural mutex. Only one transaction can succeed.
**Still imperfect:** Under extreme load, DB contention on popular driver rows.

### ✅✅ Great Solution: Distributed Lock with TTL (Redis)

```
1. Find nearest available drivers: GEOSEARCH drivers:available ...
2. For top candidate driver:
   SET lock:driver:456 {rideId} NX EX 10
   → NX: only set if key doesn't exist
   → EX 10: auto-expire after 10 seconds

3. If lock acquired → send ride request to driver via WebSocket
   If NOT acquired → try next candidate  

4. Driver accepts → update DB, remove from drivers:available set
   Driver declines or 10s timeout → Redis auto-releases lock
```

---

## 6. Deep Dive 3: How Do We Handle High Request Volume at Scale?

### ❌ Bad: Vertical Scaling
Single powerful server → single point of failure, ceiling on throughput.

### ✅✅ Great: Queue with Dynamic Scaling

```
Rider requests ride → POST /rides/request
  → API Gateway → Kafka producer → "ride_requests" topic
  → Ride Matching Workers consume from Kafka:
     - Each worker handles N ride requests
     - Auto-scale workers based on Kafka consumer lag
     - If lag > threshold → spin up more workers
     - If lag drops → scale down
```

### ✅✅ Great: Geo-Sharding

```
Partition ride requests by geographic region:
  New York rides → Kafka partition 0 → Worker pool A
  San Francisco  → Kafka partition 1 → Worker pool B
  London         → Kafka partition 2 → Worker pool C

Each region has its own Redis GEO instance:
  drivers:available:nyc
  drivers:available:sfo
  drivers:available:london

Benefits:
  - Workers only process local data
  - Redis queries only scan local drivers
  - Failures are isolated to one region
```

---

## 7. Deep Dive 4: What If a Driver Fails to Respond?

### ✅ Good Solution: Delay Queue

```
1. Send ride request to Driver A
2. Set 10-second timeout in a delay queue
3. If Driver A accepts before timeout → cancel timeout, proceed
4. If timeout fires → automatically send request to Driver B
5. Repeat until a driver accepts or all candidates exhausted
```

### ✅✅ Great Solution: Durable Execution (Temporal)

```python
# Using Temporal workflow:
@workflow.defn
class RideMatchingWorkflow:
    @workflow.run
    async def run(self, ride_request):
        drivers = await workflow.execute_activity(find_nearby_drivers, ride_request)
        
        for driver in drivers:
            accepted = await workflow.execute_activity(
                request_driver,
                driver,
                start_to_close_timeout=timedelta(seconds=10)  # auto-timeout
            )
            if accepted:
                await workflow.execute_activity(create_trip, ride_request, driver)
                return  # Success!
        
        # No driver accepted
        await workflow.execute_activity(notify_rider_no_drivers, ride_request)
```

**Why Temporal is great here:**
- ✅ Automatic retries on failure
- ✅ Durable state — survives server crashes
- ✅ Built-in timeout handling
- ✅ Complex multi-step workflow expressed as simple code
- ✅ Each step is individually logged and replayable

---

## 8. Deep Dive 5: Geo-Sharding with Read Replicas

```
PostGIS DB (Ride data) sharded by city/region:
  Shard 1: NYC  → all NYC rides, riders, drivers
  Shard 2: SFO  → all SFO data
  Shard 3: LON  → all London data

Each shard has read replicas:
  Primary: handles writes (new rides, status updates)
  Replicas: handle reads (ride history, fare estimates)

Cross-shard queries (analytics, admin):
  → Federated queries or analytics pipeline (Spark/Flink)
```

---

## 9. What is Expected at Each Level?

### Mid-Level
- Basic ride matching flow
- Simple database-backed location storage
- Identify the proximity search problem

### Senior
- Redis for real-time geospatial data (GEOADD/GEOSEARCH)
- Distributed locking for driver assignment race conditions
- WebSocket for real-time tracking
- Queue-based ride matching with auto-scaling

### Staff+
- Adaptive location update intervals
- Durable execution (Temporal) for multi-step matching workflow
- Geo-sharding strategy with read replicas
- Back-of-envelope: 10M drivers × 5s interval = 2M writes/sec
- Surge pricing (supply/demand per H3 cell)
- GPS noise handling (Kalman filter, road snapping)

---

## 10. Interview Tips & Common Questions

### Q: Why Redis instead of a database for locations?
> Location data is **ephemeral** — it changes every few seconds and doesn't need durability. Redis provides sub-millisecond writes and built-in geospatial commands. A database would be 100x slower and 10x more expensive for this workload.

### Q: How do you calculate ETA?
> Use a routing service (Google Maps API, OSRM). Pre-compute ETAs for common routes and cache them. Real-time traffic data adjusts estimates. In the interview, don't build a routing engine — just mention you'd use a service.

### Q: How do you handle surge pricing?
> Monitor supply (available drivers) vs demand (ride requests) per geographic cell (H3 hexagons). When demand/supply ratio exceeds threshold → compute surge multiplier. Process in real-time using Flink/Spark Streaming on ride request events.

### Q: What happens if WiFi/GPS drops during a trip?
> Buffer location updates on the device. When connection resumes, batch-send all buffered locations. Use dead reckoning (speed + heading) for short gaps. Trip fare is calculated from buffered waypoints, not real-time data.

### Q: How do you handle multi-region deployments?
> Each region operates independently (geo-sharded). A driver in NYC never needs to be found by an SFO rider. Cross-region: only for analytics, billing, user profiles (replicated globally).

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
