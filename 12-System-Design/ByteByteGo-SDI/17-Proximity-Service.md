# Chapter 17: Proximity Service

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/proximity-service)

Design a proximity service (like Yelp) that discovers nearby places — restaurants, hotels, gas stations, etc.

---

## Step 1 - Understand the problem and establish design scope

**Functional:** Return businesses based on user's location and radius. Business owners can add/delete/update business info (reflected next day). Customers can view detailed info.

**Non-functional:** Low latency, high availability, scalable to handle spike during peak hours.

**Estimations:** 100M daily active users, 200M businesses.

---

## Step 2 - High-level design

### API Design

- `GET /v1/search/nearby` — params: latitude, longitude, radius
- Business CRUD APIs: `GET/POST/PUT/DELETE /v1/businesses/{id}`

### Data model

**Business table**: business_id, name, address, city, state, country, latitude, longitude

**Geo index table**: Efficiently index businesses by location

### Algorithms for nearby search

#### Option 1: Two-dimensional search (naive)
SQL query with `latitude BETWEEN x AND y AND longitude BETWEEN a AND b` — not efficient (doesn't use indexes well).

#### Option 2: Evenly divided grid
Divide the world into small grids. Problem: uneven distribution (ocean vs city).

#### Option 3: Geohash ⭐
Converts 2D coordinates into a 1D string by recursively dividing the world into quadrants. Nearby locations share common prefixes.

| Geohash length | Grid width | Grid height |
|---------------|------------|-------------|
| 4 | 39.1 km | 19.5 km |
| 5 | 4.9 km | 4.9 km |
| 6 | 1.2 km | 0.61 km |

#### Option 4: Quadtree
A tree data structure — recursively subdivide 2D space into four quadrants until each leaf contains fewer than N businesses.

#### Option 5: Google S2
Maps sphere to 1D index using Hilbert curve. Used internally at Google.

### Java Example – Geohash-based Proximity Search

```java
import java.util.*;
import java.util.stream.*;

public class ProximityService {

    record Business(String id, String name, double lat, double lng) {}

    // Simplified geohash encoding
    private final Map<String, List<Business>> geohashIndex = new HashMap<>();

    public String encodeGeohash(double lat, double lng, int precision) {
        String base32 = "0123456789bcdefghjkmnpqrstuvwxyz";
        double[] latRange = {-90, 90}, lngRange = {-180, 180};
        StringBuilder hash = new StringBuilder();
        boolean isLng = true;
        int bit = 0, ch = 0;
        while (hash.length() < precision) {
            double mid;
            if (isLng) {
                mid = (lngRange[0] + lngRange[1]) / 2;
                if (lng > mid) { ch |= (1 << (4 - bit)); lngRange[0] = mid; }
                else { lngRange[1] = mid; }
            } else {
                mid = (latRange[0] + latRange[1]) / 2;
                if (lat > mid) { ch |= (1 << (4 - bit)); latRange[0] = mid; }
                else { latRange[1] = mid; }
            }
            isLng = !isLng;
            if (++bit == 5) { hash.append(base32.charAt(ch)); bit = 0; ch = 0; }
        }
        return hash.toString();
    }

    public void addBusiness(Business biz) {
        String hash = encodeGeohash(biz.lat(), biz.lng(), 5);
        geohashIndex.computeIfAbsent(hash, k -> new ArrayList<>()).add(biz);
    }

    public List<Business> searchNearby(double lat, double lng, int precision) {
        String userHash = encodeGeohash(lat, lng, precision);
        // Search current cell + neighboring cells (simplified)
        return geohashIndex.entrySet().stream()
            .filter(e -> e.getKey().startsWith(userHash.substring(0, precision - 1)))
            .flatMap(e -> e.getValue().stream())
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        ProximityService service = new ProximityService();
        service.addBusiness(new Business("b1", "Pizza Palace", 37.7749, -122.4194));
        service.addBusiness(new Business("b2", "Sushi Express", 37.7751, -122.4180));
        service.addBusiness(new Business("b3", "Coffee Hub", 37.7760, -122.4170));
        service.addBusiness(new Business("b4", "Far Away Diner", 40.7128, -74.0060));

        var results = service.searchNearby(37.7750, -122.4190, 5);
        System.out.println("=== Nearby Businesses ===");
        results.forEach(b -> System.out.printf("  %s (%s)%n", b.name(), b.id()));
    }
}
```

---

## Step 3 - Design deep dive

### Geohash vs Quadtree

| Feature | Geohash | Quadtree |
|---------|---------|----------|
| Storage | Easy to store in DB | In-memory tree, harder to persist |
| Query | Simple prefix matching | Tree traversal |
| Update | Easy | Need to rebuild portions |
| Boundary issue | Need to check neighbors | Natural handling |

### Caching
- Cache businesses by geohash prefix in Redis
- Cache is refreshed periodically (business data changes slowly)

### Database
- Read-heavy workload → primary-secondary DB setup
- Business table + geospatial index table

---

## Step 4 - Wrap up

Additional talking points:
- **Filtering by business type, rating, price range**
- **Real-time business hours**
- **Dynamic radius expansion** if not enough results
