# Chapter 18: Nearby Friends

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/nearby-friends)

In this chapter, we design a scalable backend system for a new mobile app feature called "Nearby Friends". For an opt-in user who grants permission to access their location, the mobile client presents a list of friends who are geographically nearby.

The key difference from **Proximity Service** (Chapter 17): proximity service has static business locations, while "nearby friends" uses **dynamic** user locations that change frequently.

---

## Step 1 - Understand the Problem and Establish Design Scope

**Candidate**: How geographically close is considered to be "nearby"?
**Interviewer**: 5 miles. This number should be configurable.

**Candidate**: Can I assume 1 billion users and 10% use the nearby friends feature?
**Interviewer**: Yes, that's reasonable.

**Candidate**: Do we need to store location history?
**Interviewer**: Yes, location history can be valuable for machine learning.

**Candidate**: Could we assume if a friend is inactive for more than 10 minutes, that friend will disappear from nearby list?
**Interviewer**: Yes, inactive friends will no longer be shown.

**Functional requirements:**
- See nearby friends on mobile app. Each entry shows distance and timestamp of last update.
- Nearby friend lists updated every few seconds.

**Non-functional requirements:**
- Low latency: receive location updates without too much delay.
- Reliability: overall reliable; occasional data point loss is acceptable.
- Eventual consistency: a few seconds delay in different replicas is acceptable.

**Back-of-the-envelope estimation:**
- 100 million DAU use the feature. Concurrent users: 10% = 10 million.
- Location refresh interval: 30 seconds (human walking speed ~3-4 mph).
- Average user has 400 friends.
- Location update QPS = 10 million / 30 = ~334,000
- With 400 friends, 10% online and nearby: 334K * 400 * 10% = **14 million location updates/second** to forward.

---

## Step 2 - Propose High-Level Design and Get Buy-In

The problem calls for a design with **efficient message passing**.

### Communication options

**Peer-to-peer**: Not practical for mobile with flaky connections and battery drain.

**Shared backend**: More practical design.

![Figure 3 – Shared Backend](images/ch18/figure-3.png)

Backend responsibilities:
- Receive location updates from all active users.
- Find active friends who should receive each update and forward it.
- If distance exceeds threshold, do not forward.

### Proposed design

![Figure 4 – High-level Design](images/ch18/figure-4.png)

**Load balancer**: Distributes traffic across RESTful API servers and stateful WebSocket servers.

**RESTful API servers**: Stateless HTTP servers for tasks like adding/removing friends, updating user profiles.

**WebSocket servers**: Stateful servers handling near real-time location updates. Each client maintains **one persistent WebSocket connection**. Also handles client initialization (seed mobile client with locations of all nearby online friends).

**Redis location cache**: Stores most recent location data per active user. TTL expires inactive users.

**User database**: User data and friendship data (relational or NoSQL, sharded by user_id).

**Location history database**: Stores historical location data (not directly related to "nearby friends" feature).

**Redis pub/sub server**: Very lightweight message bus. A modern Redis server can hold millions of channels.

---

## Step 3 - Design Deep Dive

### Periodic location update flow

![Figure 7 – Periodic Location Update](images/ch18/figure-7.png)

1. Mobile client sends location update via persistent WebSocket connection.
2. Load balancer forwards update to WebSocket server.
3. WebSocket server saves location to **location history database**.
4. WebSocket server updates location in **Redis location cache** (refreshes TTL).
5. WebSocket server publishes new location to user's channel in **Redis pub/sub**.
6. Redis pub/sub broadcasts update to all subscribers (user's online friends).
7. For each subscriber, WebSocket server computes distance.
8. If within search radius → send to subscriber's client.

### Concrete example with User 1

User 1's friends: user 2, user 3, user 4.

1. User 1's location update → their WebSocket server.
2. Published to user 1's channel in Redis pub/sub.
3. Redis pub/sub broadcasts to all subscribers (user 2, 3, 4's WebSocket handlers).
4. Each handler computes distance; if within radius → sent to client.

~40 location updates forwarded per user's location change (400 friends × 10% online and nearby).

### API design

**WebSocket APIs:**
1. Periodic location update: Client sends latitude, longitude, timestamp.
2. Client receives location updates: Friend location data and timestamp.
3. WebSocket initialization: Client sends location → receives friends' locations.
4. Subscribe to new friend: WebSocket server sends friend ID → receives friend's latest location.
5. Unsubscribe a friend: WebSocket server sends friend ID.

### Data model

**Location cache (Redis):**

| key | value |
|-----|-------|
| user_id | {latitude, longitude, timestamp} |

TTL auto-purges inactive users. If Redis goes down → replace with empty instance, cache warms as updates stream in.

**Location history database:**
```
user_id | latitude | longitude | timestamp
```
Heavy-write workload → **Cassandra** is a good candidate. Or relational DB sharded by user_id.

### Scaling

**API servers**: Stateless → auto-scale based on CPU/load/IO.

**WebSocket servers**: Stateful → care needed when removing nodes. Mark as "draining" at load balancer before removal.

**Client initialization**: On startup, WebSocket handler:
1. Updates user's location in location cache.
2. Loads all user's friends from user database.
3. Batch request to location cache for friends' locations.
4. Computes distances → returns nearby friends to client.
5. Subscribes to friend's channel in Redis pub/sub.
6. Sends user's current location to user's channel.

**Location cache scaling:**
- 10M users × 100 bytes = ~1 GB → fits in one Redis server.
- 334K updates/second → too high for single server → shard by user_id.
- Replicate each shard to standby node for HA.

**Redis pub/sub server scaling:**

Memory usage:
- 100 million channels × 20 bytes × 100 friends = **200 GB** → need ~2 servers for memory.

CPU usage:
- 14 million pushes/second, assume 100K pushes/server/second → **140 Redis pub/sub servers** needed.

CPU is the bottleneck → use a **distributed Redis pub/sub cluster**.

**Distributing channels**: Shard channels by publisher's user_id. Use **consistent hashing** (etcd or Zookeeper for service discovery).

![Figure 9 – Consistent Hashing for pub/sub](images/ch18/figure-9.png)

**Scaling operations**:
- Adding servers: Update hash ring → mass resubscription events occur.
- Replace a dead pub/sub server: Update hash ring with new server → WebSocket handlers re-subscribe to affected channels.

**Treat Redis pub/sub cluster as stateful** — scale with careful planning, over-provision for peak traffic.

### Adding/removing friends

- New friend added → callback sends message to WebSocket server → subscribe to new friend's channel → return friend's latest location.
- Friend removed → callback → unsubscribe from friend's channel.

### Alternative to Redis pub/sub: Erlang

**Erlang** (and Elixir/BEAM/OTP) is a great alternative:
- Erlang process takes ~300 bytes. Millions of processes on a single server.
- Each user modeled as an Erlang process.
- User process receives location updates and subscribes to friends' processes.
- Forms a mesh of connections efficiently routing updates.

### Nearby random person (extension)

Add a pool of pub/sub channels by **geohash** (see Chapter 17). Anyone within the same geohash grid subscribes to the same channel. Subscribe to current geohash + 8 surrounding grids for border coverage.

### Java Example – Location Update Dispatcher

```java
import java.util.*;
import java.util.concurrent.*;

public class NearbyFriendsService {

    record Location(String userId, double lat, double lng, long timestamp) {}

    // userId -> latest location
    private final Map<String, Location> locationCache = new ConcurrentHashMap<>();
    // userId -> list of friends
    private final Map<String, List<String>> friendGraph = new HashMap<>();
    // Simulated pub/sub: userId (channel) -> list of subscriber userIds
    private final Map<String, List<String>> pubSubChannels = new ConcurrentHashMap<>();

    private static final double SEARCH_RADIUS_MILES = 5.0;

    public void addFriend(String userId, String friendId) {
        friendGraph.computeIfAbsent(userId, k -> new ArrayList<>()).add(friendId);
        friendGraph.computeIfAbsent(friendId, k -> new ArrayList<>()).add(userId);
        // Subscribe each to the other's channel
        pubSubChannels.computeIfAbsent(userId, k -> new ArrayList<>()).add(friendId);
        pubSubChannels.computeIfAbsent(friendId, k -> new ArrayList<>()).add(userId);
    }

    public void updateLocation(String userId, double lat, double lng) {
        locationCache.put(userId, new Location(userId, lat, lng, System.currentTimeMillis()));
        // Publish to all friends subscribed to this user's channel
        List<String> subscribers = pubSubChannels.getOrDefault(userId, List.of());
        for (String friendId : subscribers) {
            Location friendLoc = locationCache.get(friendId);
            if (friendLoc != null) {
                double distance = haversine(lat, lng, friendLoc.lat(), friendLoc.lng());
                if (distance <= SEARCH_RADIUS_MILES) {
                    System.out.printf("Sending location update to %s: %s is %.2f miles away%n",
                        friendId, userId, distance);
                }
            }
        }
    }

    // Simplified haversine distance formula
    private double haversine(double lat1, double lng1, double lat2, double lng2) {
        double R = 3958.8; // Earth radius in miles
        double dLat = Math.toRadians(lat2 - lat1);
        double dLng = Math.toRadians(lng2 - lng1);
        double a = Math.sin(dLat / 2) * Math.sin(dLat / 2)
                + Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2))
                * Math.sin(dLng / 2) * Math.sin(dLng / 2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    public static void main(String[] args) {
        NearbyFriendsService service = new NearbyFriendsService();
        service.addFriend("alice", "bob");
        service.addFriend("alice", "carol");

        service.updateLocation("alice", 37.7749, -122.4194); // San Francisco
        service.updateLocation("bob", 37.7751, -122.4190);   // ~0.02 miles away
        service.updateLocation("carol", 40.7128, -74.0060);  // New York

        service.updateLocation("alice", 37.7752, -122.4185); // alice moved slightly
    }
}
```

---

## Step 4 - Wrap Up

Core components:
- **WebSocket**: Real-time communication between clients and server.
- **Redis**: Fast read/write of location data.
- **Redis pub/sub**: Routing layer to direct location updates from one user to online friends.

Scaling explored:
- REST API servers (stateless, easy)
- WebSocket servers (stateful, graceful draining)
- Data layer (sharding, replication)
- Redis pub/sub servers (distributed cluster with consistent hashing)

---

## Reference materials

[1] Facebook Launches "Nearby Friends": https://techcrunch.com/2014/04/17/facebook-nearby-friends/
[2] Redis Pub/Sub: https://redis.io/topics/pubsub
[3] etcd: https://etcd.io/
[4] Zookeeper: https://zookeeper.apache.org/
[5] Consistent hashing: https://www.toptal.com/big-data/consistent-hashing
[6] Erlang: https://www.erlang.org/
[7] Elixir: https://elixir-lang.org/
