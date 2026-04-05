# Chapter 19: Google Maps

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/google-maps)

In this chapter, we design a simple version of Google Maps. Google started Project Google Maps in 2005 and developed a web mapping service. It provides satellite imagery, street maps, real-time traffic conditions, and route planning.

Google Maps had one billion daily active users (March 2021), 99% coverage of the world, and 25 million updates daily.

---

## Map 101

### Positioning system

- **Latitude (Lat)**: denotes how far north or south we are
- **Longitude (Long)**: denotes how far east or west we are

### Going from 3D to 2D

The process of translating points from a 3D globe to a 2D plane is called **Map Projection**. Google Maps uses a modified version of Mercator projection called **Web Mercator**.

### Geocoding

Geocoding is the process of converting addresses to geographic coordinates. For example: "1600 Amphitheatre Parkway, Mountain View, CA" → (latitude 37.423021, longitude -122.083739).

Reverse geocoding: lat/lng pair → human-readable address.

### Geohashing

Geohashing encodes a geographic area into a short string of letters and digits. Earth is treated as a flattened surface and recursively divided into grids.

### Map rendering

One foundational concept in map rendering is **tiling**. Instead of rendering the entire map as one large image, the world is broken into smaller tiles. The client downloads only relevant tiles for the area the user is in and stitches them together.

### Road data processing for navigation algorithms

Most routing algorithms are variations of **Dijkstra's** or **A* pathfinding** algorithms. These operate on a graph where intersections are nodes and roads are edges.

**Routing tiles**: By employing a subdivision technique similar to geohashing, the world is divided into small grids. Roads within each grid are converted into a small graph data structure (nodes = intersections, edges = roads).

**Hierarchical routing tiles**: Three sets of routing tiles at different levels:
1. Most detail: small tiles with only local roads
2. Medium: larger tiles with arterial roads connecting districts
3. Least detail: large tiles with major highways connecting cities/states

---

## Step 1 - Understand the Problem and Establish Design Scope

**Candidate**: How many daily active users?
**Interviewer**: 1 billion DAU.

**Candidate**: Which features should we focus on?
**Interviewer**: Location update, navigation, ETA, and map rendering.

**Candidate**: How large is the road data?
**Interviewer**: Terabytes of raw data.

**Candidate**: Should our system take traffic conditions into consideration?
**Interviewer**: Yes.

**Focus features:**
- User location update
- Navigation service, including ETA service
- Map rendering

**Non-functional requirements:**
- Accuracy: Users should not be given the wrong directions.
- Smooth navigation: very smooth map rendering on client-side.
- Data and battery usage: as little data and battery as possible.
- High availability and scalability.

**Back-of-the-envelope estimation:**

*Storage usage:*
- Zoom level 21: ~4.4 trillion tiles × 100KB → 440 PB at highest zoom
- After compression (~80-90% reduction for water/terrain): ~50 PB
- Total across all zoom levels: ~100 PB

*Server throughput:*
- 1B DAU, 35 min navigation/week → 5B min/day
- GPS every 15 seconds batch: **200,000 QPS** (baseline), **1 million QPS** peak

---

## Step 2 - High-Level Design

![Figure 7 – High-level Design](images/ch19/figure-7.png)

Three main service flows:

### Location Service

Client sends location updates every `t` seconds. Location data buffered on client and sent in batch (e.g., every 15 seconds).

```
POST /v1/locations
Parameters:
  locs: JSON encoded array of (latitude, longitude, timestamp) tuples.
```

Database choice: **Cassandra** (high write volume, horizontally scalable).

Data consumed from Kafka by downstream services (live traffic, routing tile updates).

### Navigation Service

```
GET /v1/nav?origin=1355+market+street,SF&destination=Disneyland
```

Response includes distance, duration, html_instructions, polyline, travel_mode.

### Map Rendering

Pre-generated static map tiles served via CDN. Tile URL based on geohash:
```
https://cdn.map-provider.com/tiles/9q9hvu.png
```

---

## Step 3 - Design Deep Dive

### Data model

**Routing tiles**: Stored in object storage (S3), organized by geohash. Fetched on demand by routing algorithms.

**User location data (Cassandra):**

| key (user_id) | timestamp | lat | long | user_mode | navigation_mode |
|---------------|-----------|-----|------|-----------|-----------------|
| 51 | 132053000 | 21.9 | 89.8 | active | driving |

Partition key: `user_id`, clustering key: `timestamp`. Efficiently retrieves location for a user in a time range.

**Geocoding database (Redis):** Fast reads for address → lat/lng conversion.

**Precomputed map tiles:** Stored on CDN backed by Amazon S3.

### Location service (deep dive)

Location data consumed by multiple services via Kafka:
- Live traffic service → updates live traffic database
- Routing tile processing service → detects new/closed roads
- Other analytics services

![Figure 15 – Kafka Usage](images/ch19/figure-15.png)

### Map rendering (deep dive)

**Precomputed tiles at 21 zoom levels:**
- Level 0: entire world as single 256×256 pixel tile
- Each increment: number of tiles doubles in both directions (4× total)

**Optimization: Use vectors (WebGL)**
- Vector tiles compress much better than images
- Better zooming experience (no pixelation)

### Navigation service (deep dive)

Components:

**Geocoding service**: Resolves address to lat/lng (Google Geocoding API format).

**Route planner service**: Computes optimal route considering current traffic.

**Shortest-path service**: Runs A* algorithm against routing tiles in object storage.
1. Convert lat/lng to geohash → load routing tiles
2. Traverse graph, hydrate neighboring tiles on demand
3. Return top-k shortest paths

**ETA service**: Uses ML to predict ETAs based on current traffic + historical data.

**Ranker service**: Applies user filters (avoid tolls, avoid freeways) and ranks routes fastest → slowest.

**Updater services (Kafka consumers):**
- Routing tile processing service: new/closed roads → updated routing tiles
- Traffic update service: location streams → live traffic database

### Adaptive ETA and rerouting

To support real-time rerouting, the server tracks actively navigating users and their routing tiles:

```
user_1: r_1, r_2, r_3, ..., r_k
user_2: r_4, r_6, r_9, ..., r_n
```

**Optimized approach**: Store current + hierarchical parent tiles per user. To find affected users when `r_2` has a traffic incident, check if `r_2` is within a user's last routing tile entry — filters out many users quickly.

**Delivery protocols:**
- Mobile push notification: too limited (max 4KB)
- Long polling: less efficient
- **WebSocket**: preferred ✅ (bi-directional real-time communication)

![Figure 21 – Final Design](images/ch19/figure-21.png)

### Java Example – Routing with Dijkstra

```java
import java.util.*;

public class MapRouter {

    record Edge(String to, int weight) {}

    private final Map<String, List<Edge>> graph = new HashMap<>();

    public void addRoad(String from, String to, int travelTime) {
        graph.computeIfAbsent(from, k -> new ArrayList<>()).add(new Edge(to, travelTime));
        graph.computeIfAbsent(to, k -> new ArrayList<>()).add(new Edge(from, travelTime));
    }

    public Map<String, Integer> dijkstra(String start) {
        Map<String, Integer> dist = new HashMap<>();
        PriorityQueue<int[]> pq = new PriorityQueue<>(Comparator.comparingInt(a -> a[1]));

        dist.put(start, 0);
        pq.offer(new int[]{start.hashCode(), 0});

        Map<Integer, String> hashToNode = new HashMap<>();
        graph.keySet().forEach(n -> hashToNode.put(n.hashCode(), n));
        hashToNode.put(start.hashCode(), start);

        while (!pq.isEmpty()) {
            int[] curr = pq.poll();
            String node = hashToNode.get(curr[0]);
            int currDist = curr[1];
            if (currDist > dist.getOrDefault(node, Integer.MAX_VALUE)) continue;
            for (Edge edge : graph.getOrDefault(node, List.of())) {
                int newDist = currDist + edge.weight();
                if (newDist < dist.getOrDefault(edge.to(), Integer.MAX_VALUE)) {
                    dist.put(edge.to(), newDist);
                    hashToNode.put(edge.to().hashCode(), edge.to());
                    pq.offer(new int[]{edge.to().hashCode(), newDist});
                }
            }
        }
        return dist;
    }

    public static void main(String[] args) {
        MapRouter router = new MapRouter();
        router.addRoad("A", "B", 5);
        router.addRoad("B", "C", 3);
        router.addRoad("A", "C", 10);
        router.addRoad("C", "D", 2);

        Map<String, Integer> distances = router.dijkstra("A");
        System.out.println("Shortest distances from A:");
        distances.forEach((node, dist) ->
            System.out.println("  A -> " + node + ": " + dist + " minutes"));
    }
}
```

---

## Step 4 - Wrap Up

Designed a simplified Google Maps with:
- **Location service** (Cassandra + Kafka)
- **Navigation service** (geocoding, route planning, ETA, ranking)
- **Map rendering** (CDN with precomputed tiles, vector optimization)
- **Adaptive ETA** with real-time rerouting via WebSocket

**Future extension**: Multi-stop navigation — finding optimal order to visit multiple destinations (helpful for delivery services like DoorDash, Uber).

---

## Reference materials

[1] Google Maps: https://developers.google.com/maps?hl=en_US
[2] Google Maps Platform: https://cloud.google.com/maps-platform/
[3] Stamen Design: http://maps.stamen.com
[4] OpenStreetMap: https://www.openstreetmap.org
[5] Prototyping a Smoother Map: https://medium.com/google-design/google-maps-cb0326d165f5
[6-9] Map Projections (Wikipedia)
[10] Address geocoding: https://en.wikipedia.org/wiki/Address_geocoding
[11] Geohashing: https://kousiknath.medium.com/system-design-design-a-geo-spatial-index-for-real-time-location-search-10968fe62b9c
[12] HTTP keep-alive: https://en.wikipedia.org/wiki/HTTP_persistent_connection
[13] Directions API: https://developers.google.com/maps/documentation/directions/start
[14] Adjacency list: https://en.wikipedia.org/wiki/Adjacency_list
[15] CAP theorem: https://en.wikipedia.org/wiki/CAP_theorem
[16] ETAs with GNNs: https://deepmind.com/blog/article/traffic-prediction-with-advanced-graph-neural-networks
[17] Google Maps 101: https://blog.google/products/maps/google-maps-101-how-ai-helps-predict-traffic-and-determine-routes/
