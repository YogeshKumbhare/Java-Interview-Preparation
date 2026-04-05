# Chapter 17: Proximity Service

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/proximity-service)

In this chapter, we design a proximity service. A proximity service is used to discover nearby places such as restaurants, hotels, theaters, museums, etc., and is a core component that powers features like finding the best restaurants nearby on Yelp or finding k-nearest gas stations on Google Maps.

---

## Step 1 - Understand the Problem and Establish Design Scope

**Candidate**: Can a user specify the search radius? If there are not enough businesses within the search radius, does the system expand the search?
**Interviewer**: Let's assume we only care about businesses within a specified radius.

**Candidate**: What's the maximal radius allowed? Can I assume it's 20 km?
**Interviewer**: That's a reasonable assumption.

**Candidate**: Can a user change the search radius on the UI?
**Interviewer**: Yes, we have the following options: 0.5km, 1km, 2km, 5km, and 20km.

**Candidate**: How does business information get added, deleted, or updated? Do we need to reflect these in real-time?
**Interviewer**: Business owners can add, delete or update a business. Newly added/updated businesses will be effective the next day.

**Functional requirements:**
- Return all businesses based on user's location (latitude/longitude) and radius.
- Business owners can add, delete or update a business (not real-time).
- Customers can view detailed information about a business.

**Non-functional requirements:**
- Low latency: Users should see nearby businesses quickly.
- Data privacy: Comply with GDPR and CCPA.
- High availability and scalability.

**Back-of-the-envelope estimation:**
- 100 million daily active users, 200 million businesses.
- Search QPS = 100M * 5 searches / 10^5 seconds = 5,000

---

## Step 2 - Propose High-Level Design and Get Buy-In

### API Design

**Search nearby:**
```
GET /v1/search/nearby
Request Parameters:
  latitude (decimal), longitude (decimal), radius (int, default 5000m)

Response Body:
{
  "total": 10,
  "businesses": [{business object}]
}
```

**Business APIs:**

| API | Detail |
|-----|--------|
| GET /v1/businesses/{:id} | Return detailed information about a business |
| POST /v1/businesses | Add a business |
| PUT /v1/businesses/{:id} | Update details of a business |
| DELETE /v1/businesses/{:id} | Delete a business |

### Data model

Read volume is high (search for nearby businesses, view business details). Write volume is low. A relational database such as MySQL is a good fit.

**Business table (primary key: business_id):**
Contains business_id, name, address, latitude, longitude, etc.

**Geo index table:**
Used for efficient processing of spatial operations (discussed in deep dive).

### High-level design

![Figure 2 – High-level Design](images/ch17/figure-2.png)

Two parts: **location-based service (LBS)** and **business-related service**.

**Load balancer:**
Distributes incoming traffic across multiple services.

**Location-based service (LBS):**
- Core part of the system — finds nearby businesses.
- Read-heavy, no write requests.
- High QPS, especially during peak hours in dense areas.
- Stateless → easy to scale horizontally.

**Business service:**
- Write: Business owners create/update/delete businesses. Low QPS.
- Read: Customers view business details. High QPS during peak hours.

**Database cluster:**
Primary-secondary setup. Primary handles writes, replicas handle reads. Some data discrepancy acceptable because business info doesn't need real-time updates.

### Algorithms to fetch nearby businesses

#### Option 1: Two-dimensional search (Naive)

```sql
SELECT business_id, latitude, longitude,
FROM business
WHERE (latitude BETWEEN {:my_lat} - radius AND {:my_lat} + radius) AND
      (longitude BETWEEN {:my_long} - radius AND {:my_long} + radius)
```

Not efficient — must scan the whole table. Database index only improves search in one dimension.

#### Option 2: Evenly divided grid

Divide the world into small grids. Issues: uneven data distribution (dense areas vs sparse areas).

#### Option 3: Geohash ⭐ Recommended

Geohash reduces 2D data (longitude, latitude) into a 1D string of letters and digits. Works by recursively dividing the world into smaller grids.

![Figure 7 – Geohash](images/ch17/figure-7.png)

Base32 representation examples:
- Google HQ: `9q9hvu`
- Facebook HQ: `9q9jhr`

**Geohash precision table:**

| Geohash length | Grid width x height |
|----------------|---------------------|
| 1 | 5,009.4km x 4,992.6km |
| 4 | 39.1km x 19.5km |
| 5 | 4.9km x 4.9km |
| 6 | 1.2km x 609.4m |
| 7 | 152.9m x 152.4m |

**Radius to geohash mapping:**

| Radius | Geohash length |
|--------|----------------|
| 0.5 km | 6 |
| 1 km | 5 |
| 2 km | 5 |
| 5 km | 4 |
| 20 km | 4 |

**Boundary issues:**
1. Two locations can be very close but have no shared prefix (e.g., locations on either side of the equator).
2. Two positions can have a long shared prefix but belong to different geohashes.

**Solution**: Fetch businesses from the current grid AND its 8 neighboring grids.

**Not enough businesses**: Remove the last digit of the geohash to expand search radius iteratively.

#### Option 4: Quadtree

A **quadtree** recursively subdivides 2D space into 4 quadrants until each grid has ≤100 businesses.

![Figure 13 – Quadtree](images/ch17/figure-13.png)

Memory usage:
- Leaf nodes: ~2 million, 832 bytes each
- Internal nodes: ~0.67 million, 64 bytes each
- Total: ~1.71 GB — fits easily in one server.

Building time: O((N/100) * log(N/100)) — a few minutes for 200M businesses.

Use **blue/green deployment** or incremental rollout to minimize downtime.

#### Option 5: Google S2

Google S2 is an in-memory solution mapping a sphere to a 1D index based on the Hilbert curve. Used by Google Maps, Tinder.

| Geo Index | Companies |
|-----------|-----------|
| Geohash | Bing map, Redis, MongoDB, Lyft |
| Quadtree | Yext |
| Both | Elasticsearch |
| S2 | Google Maps, Tinder |

**Recommendation**: Choose geohash or quadtree for interviews (S2 is more complex).

---

## Step 3 - Design Deep Dive

### Scale the database

**Business table**: Shard by business_id (even load distribution).

**Geospatial index table**: Use read replicas (data fits in working set of one server, sharding unnecessary).

**Two options for geospatial index table:**
- Option 1: JSON array of business IDs per geohash row
- Option 2: Multiple rows, one per business per geohash ⭐ Recommended

Option 2 is better because addition/removal is simple with compound key `(geohash, business_id)`.

### Caching

Not immediately obvious that caching is a win for this workload:
- Read-heavy, small dataset that fits in modern DB server.
- Adding DB read replicas can improve throughput.

**If caching is warranted:**
- Cache key: geohash (not raw location — GPS coordinates are imprecise)
- Two types of cached data:

| Key | Value |
|-----|-------|
| geohash | List of business IDs in the grid |
| business_id | Business object |

**Memory usage:**
- Storage for Redis values: 8 bytes × 200M businesses × 3 precisions = ~5 GB
- Fits in one modern Redis server; deploy globally for HA.

```java
public List<String> getNearbyBusinessIds(String geohash) {
    String cacheKey = hash(geohash);
    List<String> listOfBusinessIds = Redis.get(cacheKey);
    if (listOfBusinessIds == null) {
        listOfBusinessIds = runSelectSQLQuery(geohash);
        Cache.set(cacheKey, listOfBusinessIds, "1d");
    }
    return listOfBusinessIds;
}
```

### Region and availability zones

Deploy LBS to multiple regions and availability zones:
- Users physically closer to the system.
- Spread traffic evenly across population.
- Comply with privacy laws (data stored locally in some countries).

### Java Example – Proximity Service with Geohash

```java
import java.util.*;

public class ProximityService {

    // Simulated geo index: geohash -> list of business IDs
    private final Map<String, List<String>> geoIndex = new HashMap<>();
    // Simulated business cache: id -> name
    private final Map<String, String> businessCache = new HashMap<>();

    public void addBusiness(String businessId, String name, String geohash) {
        geoIndex.computeIfAbsent(geohash, k -> new ArrayList<>()).add(businessId);
        businessCache.put(businessId, name);
        System.out.println("Added business: " + name + " at geohash: " + geohash);
    }

    public List<String> getNearbyBusinesses(String userGeohash, int radius) {
        // In real implementation: compute geohash from lat/lng
        // and fetch from geohash + 8 neighbors
        List<String> businessIds = geoIndex.getOrDefault(userGeohash, List.of());
        List<String> result = new ArrayList<>();
        for (String id : businessIds) {
            result.add(businessCache.get(id));
        }
        return result;
    }

    // Simulate geohash encoding (simplified)
    public static String encodeGeohash(double lat, double lng, int precision) {
        // Real implementation uses base32 encoding recursively
        return String.format("%.6f,%.6f", lat, lng).substring(0, precision);
    }

    public static void main(String[] args) {
        ProximityService service = new ProximityService();
        service.addBusiness("b1", "Pizza Palace", "9q8zn");
        service.addBusiness("b2", "Coffee House", "9q8zn");
        service.addBusiness("b3", "Burger Joint", "9q8zm");

        List<String> nearby = service.getNearbyBusinesses("9q8zn", 500);
        System.out.println("Nearby businesses: " + nearby);
    }
}
```

### Step 4 - Wrap Up

Geospatial indexing options discussed:
- Two-dimensional search
- Evenly divided grid
- **Geohash** ⭐ (chosen example)
- Quadtree
- Google S2

Key insights:
- Geohash is effective for reducing 2D to 1D search.
- Use neighbors to handle boundary issues.
- Scale with read replicas, not sharding for geospatial index.
- Deploy globally across regions and availability zones.

---

## Reference materials

[1] GDPR: https://en.wikipedia.org/wiki/General_Data_Protection_Regulation
[2] CCPA: https://en.wikipedia.org/wiki/California_Consumer_Privacy_Act
[3] Redis GEOHASH: https://redis.io/commands/GEOHASH
[4] POSTGIS: https://postgis.net/
[5] Geohash: https://www.movable-type.co.uk/scripts/geohash.html
[6] Quadtree: https://en.wikipedia.org/wiki/Quadtree
[7] S2: http://s2geometry.io/
[8] Geospatial Indexing: The 10 Million QPS Redis Architecture Powering Lyft: https://www.youtube.com/watch?v=cSFWlF96Sds
