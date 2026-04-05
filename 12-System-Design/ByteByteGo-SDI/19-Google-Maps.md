# Chapter 19: Google Maps

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/google-maps)

Design a simplified version of Google Maps — covering map rendering, location tracking, and navigation (ETA/route planning).

---

## Step 1 - Understand the problem and establish design scope

**Features:** User location update, navigation (ETA + routes), map rendering.

**Non-functional:** Accuracy for navigation, smooth rendering, low data usage, available in areas with weak network, High availability and scalability.

**Estimations:** 1 billion DAU, 5 million users daily navigation, GPS updated every second during navigation.

---

## Step 2 - High-level design

### Map 101

- **Positioning system**: GPS for location
- **Map rendering**: Use pre-rendered map tiles at various zoom levels
- **Routing**: Graph-based shortest path (Dijkstra's / A*)
- **Geocoding**: Convert address to lat/lng and vice versa

### Routing algorithms

- The road network is modeled as a **graph** where intersections are nodes and roads are edges
- Weights = time/distance
- Use **Dijkstra's algorithm** or **A*** for shortest path
- **Routing tiles**: Pre-partition the world into tiles at different resolution levels (local roads, arterial roads, highway) for hierarchical routing

### High-level components

1. **Location Service**: Receives and stores user GPS data (write-heavy, Kafka → DB)
2. **Map Tile Service**: Serves pre-rendered map tiles from CDN
3. **Navigation Service**: Computes optimal routes using routing tiles
4. **Ranking Service**: Ranks multiple routes (fastest, shortest, no tolls)

### Java Example – Shortest Path Navigation

```java
import java.util.*;

public class NavigationService {

    record Edge(String to, double weight) {} // weight = travel time in minutes

    private final Map<String, List<Edge>> graph = new HashMap<>();

    public void addRoad(String from, String to, double travelTime) {
        graph.computeIfAbsent(from, k -> new ArrayList<>()).add(new Edge(to, travelTime));
        graph.computeIfAbsent(to, k -> new ArrayList<>()).add(new Edge(from, travelTime));
    }

    // Dijkstra's shortest path
    public List<String> findRoute(String start, String end) {
        Map<String, Double> dist = new HashMap<>();
        Map<String, String> prev = new HashMap<>();
        PriorityQueue<String> pq = new PriorityQueue<>(Comparator.comparing(n -> dist.getOrDefault(n, Double.MAX_VALUE)));

        dist.put(start, 0.0);
        pq.add(start);

        while (!pq.isEmpty()) {
            String current = pq.poll();
            if (current.equals(end)) break;

            for (Edge edge : graph.getOrDefault(current, List.of())) {
                double newDist = dist.get(current) + edge.weight();
                if (newDist < dist.getOrDefault(edge.to(), Double.MAX_VALUE)) {
                    dist.put(edge.to(), newDist);
                    prev.put(edge.to(), current);
                    pq.add(edge.to());
                }
            }
        }

        // Reconstruct path
        List<String> path = new ArrayList<>();
        for (String at = end; at != null; at = prev.get(at)) path.add(0, at);
        return path.get(0).equals(start) ? path : List.of();
    }

    public static void main(String[] args) {
        NavigationService nav = new NavigationService();
        nav.addRoad("Home", "Gas Station", 5);
        nav.addRoad("Home", "Park", 3);
        nav.addRoad("Park", "Mall", 4);
        nav.addRoad("Gas Station", "Mall", 2);
        nav.addRoad("Mall", "Office", 6);
        nav.addRoad("Gas Station", "Office", 10);

        List<String> route = nav.findRoute("Home", "Office");
        System.out.println("Route: " + String.join(" → ", route));
        System.out.println("ETA: ~" + route.size() * 3 + " minutes"); // simplified
    }
}
```

---

## Step 3 - Design deep dive

### Map rendering
- Map tiles pre-rendered at 21+ zoom levels
- Stored in CDN for fast delivery
- Client downloads only visible tiles based on viewport

### Location service
- High write volume → use Kafka to buffer GPS data
- Store location history in Cassandra (write-optimized)
- Used for ETA prediction, traffic analysis

### Navigation service - Routing tiles
- Divide world into hierarchical routing tiles (3 levels):
  - **Local**: Small roads within a city block
  - **Regional**: Arterial roads connecting neighborhoods
  - **Highway**: Interstate/highway-level connections
- Route calculation spans multiple tile levels for long-distance routes

### Adaptive ETA
- Use real-time traffic data + historical patterns
- Machine learning models predict travel time

---

## Step 4 - Wrap up

Additional talking points:
- **Delivery routes optimization** (multi-stop TSP)
- **Transit/walking/cycling directions**
- **3D/satellite view**
- **Offline maps**: Download tiles for areas ahead of time
