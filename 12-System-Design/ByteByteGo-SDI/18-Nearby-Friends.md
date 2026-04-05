# Chapter 18: Nearby Friends

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/nearby-friends)

Design a feature like Facebook Nearby Friends — show friends who are geographically close to you in real-time.

---

## Step 1 - Understand the problem and establish design scope

**Functional:** Show nearby friends within a configurable radius (default 5 miles). Distance and last-known location update displayed. Location updated every 30 seconds.

**Non-functional:** Low latency, reliability, eventual consistency (slight location delay OK).

**Estimations:** 100M DAU, 10% feature enabled = 10M concurrent users, 30-sec update → ~334K updates/sec.

---

## Step 2 - High-level design

### Communication protocol

Need bi-directional, real-time communication → **WebSocket**

### High-level components

1. **Load Balancer**: Distribute WebSocket connections
2. **WebSocket Servers**: Handle persistent connections, stateful
3. **Redis Pub/Sub**: Channel per user for location updates broadcast
4. **Location Cache (Redis)**: Store latest location per user (TTL-based)
5. **Location History DB**: Persist location history (Cassandra)
6. **API Servers**: Handle non-real-time requests (add/remove friends, update profile)

### Flow: Location update

1. User sends location update via WebSocket
2. WebSocket server saves to Location Cache + Location History DB
3. WebSocket server publishes update to user's Redis Pub/Sub channel
4. All friends subscribed to this channel receive the update
5. Friends' WebSocket servers calculate distance and push to client if within radius

### Java Example – Nearby Friends with Pub/Sub

```java
import java.util.*;
import java.util.concurrent.*;

public class NearbyFriendsService {

    record Location(double lat, double lng, long timestamp) {}

    private final Map<String, Location> locationCache = new ConcurrentHashMap<>();
    private final Map<String, Set<String>> friendsGraph = new ConcurrentHashMap<>();
    private final Map<String, List<String>> subscriptions = new ConcurrentHashMap<>();
    private final double RADIUS_KM = 8.0; // ~5 miles

    public void updateLocation(String userId, double lat, double lng) {
        locationCache.put(userId, new Location(lat, lng, System.currentTimeMillis()));
        // Notify friends
        Set<String> friends = friendsGraph.getOrDefault(userId, Set.of());
        for (String friendId : friends) {
            Location friendLoc = locationCache.get(friendId);
            if (friendLoc != null) {
                double dist = haversine(lat, lng, friendLoc.lat(), friendLoc.lng());
                if (dist <= RADIUS_KM) {
                    System.out.printf("  📍 %s is %.1f km from %s%n", userId, dist, friendId);
                }
            }
        }
    }

    public List<String> getNearbyFriends(String userId) {
        Location userLoc = locationCache.get(userId);
        if (userLoc == null) return List.of();
        List<String> nearby = new ArrayList<>();
        for (String friendId : friendsGraph.getOrDefault(userId, Set.of())) {
            Location fLoc = locationCache.get(friendId);
            if (fLoc != null && haversine(userLoc.lat(), userLoc.lng(), 
                                           fLoc.lat(), fLoc.lng()) <= RADIUS_KM) {
                nearby.add(friendId);
            }
        }
        return nearby;
    }

    private double haversine(double lat1, double lng1, double lat2, double lng2) {
        double R = 6371; // Earth radius km
        double dLat = Math.toRadians(lat2 - lat1);
        double dLng = Math.toRadians(lng2 - lng1);
        double a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                   Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
                   Math.sin(dLng/2) * Math.sin(dLng/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    public static void main(String[] args) {
        NearbyFriendsService service = new NearbyFriendsService();
        service.friendsGraph.put("alice", Set.of("bob", "charlie", "dave"));
        service.friendsGraph.put("bob", Set.of("alice"));

        // All in San Francisco area
        service.updateLocation("alice", 37.7749, -122.4194);
        service.updateLocation("bob", 37.7751, -122.4180);   // ~0.1 km away
        service.updateLocation("charlie", 37.7849, -122.4094); // ~1.3 km
        service.updateLocation("dave", 40.7128, -74.0060);     // NYC, far away

        System.out.println("\nAlice's nearby friends: " + 
            service.getNearbyFriends("alice"));
    }
}
```

---

## Step 3 - Design deep dive

### Redis Pub/Sub for location updates
- Each user has a channel: `user:{userId}:location`
- When user A updates location, publish to A's channel
- All online friends of A are subscribed to A's channel
- Each WebSocket server manages subscriptions for its connected users

### Scaling WebSocket servers
- Use consistent hashing to assign users to WebSocket servers
- Service discovery (ZooKeeper) manages server registry
- On server failure, clients reconnect to a different server

### Scaling Redis Pub/Sub
- Shard Redis Pub/Sub by user_id hash
- Use Redis Cluster for horizontal scaling
- Consider replacing with distributed message queue for very large scale

---

## Step 4 - Wrap up

Additional talking points:
- **Privacy**: Users can turn off location sharing for specific friends
- **Nearby random people** (different from nearby friends)
- **Power consumption optimization on mobile**
