# 🚀 Caching Strategies & Types — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 1. What is Caching & Why Do We Need It?

Caching is the process of storing copies of frequently accessed data in a temporary, high-speed storage layer (usually RAM) so that future requests for that data can be served much faster than accessing the primary storage (like a relational database, API, or disk).

### Why use caching?
1. **Reduce Latency**: In-memory access (<1ms) vs DB disk access (10ms+).
2. **Reduce Load on Primary Database**: Prevent DB overload during traffic surges.
3. **Save Compute**: Avoid recalculating complex aggregations repeatedly.

---

## 📖 2. Types of Caching (Where Cache Resides)

### 2.1 Local Cache (In-Memory Cache)
The cache resides in the same JVM memory/application space as the application.
- **Pros**: Fastest possible access (no network hop).
- **Cons**: High memory consumption per node. Cache inconsistency across clustered nodes. Data is lost on app restart.
- **Examples**: `ConcurrentHashMap`, **Caffeine** (Spring Boot Default), Guava Cache, Ehcache.

#### Real-time Example Code: Local Caching with Caffeine (Spring Boot)
```java
@Configuration
@EnableCaching
public class CaffeineCacheConfig {
    @Bean
    public CacheManager cacheManager() {
        CaffeineCacheManager cacheManager = new CaffeineCacheManager("productCache", "userCache");
        cacheManager.setCaffeine(Caffeine.newBuilder()
                .expireAfterWrite(10, TimeUnit.MINUTES) // TTL
                .maximumSize(1000) // LRU Eviction mostly
                .recordStats());
        return cacheManager;
    }
}

@Service
public class ProductService {
    @Cacheable(value = "productCache", key = "#productId")
    public Product getProductDetails(String productId) {
        // Slow DB call simulated
        return productRepository.findById(productId)
                 .orElseThrow(() -> new ResourceNotFoundException("Product not found"));
    }
    
    @CachePut(value = "productCache", key = "#product.id")
    public Product updateProduct(Product product) {
        return productRepository.save(product);
    }
    
    @CacheEvict(value = "productCache", key = "#productId")
    public void deleteProduct(String productId) {
        productRepository.deleteById(productId);
    }
}
```

### 2.2 Distributed Cache
An independent cache cluster shared across all application instances.
- **Pros**: Consistent data across all microservices/instances. Scales independently. Survives application restarts.
- **Cons**: Network call latency (~1ms). Serialization/Deserialization overhead.
- **Examples**: **Redis**, Memcached, Hazelcast, Amazon ElastiCache.

#### Real-time Example Code: Distributed Cache with Redis (Spring Boot)
```java
@Configuration
@EnableCaching
public class RedisCacheConfig {
    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory connectionFactory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofHours(1)) // Global TTL
            .serializeKeysWith(RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer()));

        return RedisCacheManager.builder(connectionFactory)
            .cacheDefaults(config)
            .build();
    }
}

@Service
public class InventoryService {
    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    public void updateStockAtomic(String productId, int quantity) {
        // Atomic decrement in Redis (Real-time prevention of overselling)
        Long currentStock = redisTemplate.opsForValue().decrement("stock:" + productId, quantity);
        if (currentStock < 0) {
            redisTemplate.opsForValue().increment("stock:" + productId, quantity); // Rollback
            throw new InsufficientStockException("Out of stock!");
        }
    }
}
```

### 2.3 CDN (Content Delivery Network) / Edge Caching
Caches static assets (images, JS, CSS, videos) or whole HTML pages at proxy servers located geographically near the users.
- **Examples**: Cloudflare, AWS CloudFront, Akamai.

---

## 📖 3. Caching Strategies (Read/Write Patterns)

Your chosen pattern heavily impacts data consistency.

### 3.1 Cache-Aside (Lazy Loading)
The application is responsible for reading from and writing to the cache.
*   **Read**: App checks cache. If miss, app reads from DB, writes to cache, and returns data.
*   **Write**: App updates DB, then invalidates or updates the cache.
*   **Best for**: Read-heavy workloads.
*   **Real-time Example**: Product details page in E-commerce.

```java
// Cache-Aside Example
public User getUser(Long id) {
    User user = cache.get("user:" + id); // 1. Check Cache
    if (user == null) {                  // 2. Cache Miss
        user = db.findUserById(id);      // 3. Read from DB
        if (user != null) {
            cache.put("user:" + id, user, TTL); // 4. Populate Cache
        }
    }
    return user;
}
```

### 3.2 Read-Through Cache
The application always asks the *cache provider* for data. If it's a miss, the *cache provider* (not the app code) fetches data from the DB, stores it, and returns it.
*   **Best for**: Read-heavy workloads where the cache library natively supports DB hydration (e.g., Guava CacheLoader, Hazelcast MapLoader).

```java
// Read-Through Example (Guava CacheLoader)
LoadingCache<String, User> userCache = CacheBuilder.newBuilder()
    .maximumSize(1000)
    .build(
        new CacheLoader<String, User>() {
            public User load(String id) {
                return userRepository.findById(id); // Cache auto-loads on miss!
            }
        });

// App code merely calls:
User u = userCache.get("123"); 
```

### 3.3 Write-Through Cache
When writing data, the app writes to the cache, and the app/cache *synchronously* writes to the DB before returning success to the user.
*   **Pros**: 100% Data consistency between Cache and DB.
*   **Cons**: High write penalty (writes take longer because they hit both systems sequentially).
*   **Best for**: Systems that cannot tolerate stale data but read the same data frequently immediately after writing (e.g., banking/wallet balance updates).

```java
// Write-Through Example
@Transactional
public User updateUserBalance(Long id, BigDecimal newBalance) {
    // 1. Update Database synchronously
    User user = db.updateUserBalance(id, newBalance);
    
    // 2. Update Cache synchronously
    // The method doesn't return until BOTH DB and Cache are updated.
    cache.put("user:balance:" + id, newBalance);
    
    return user;
}
```

### 3.4 Write-Behind (Write-Back) Cache
App writes data *only* to the cache and gets immediate success. The system *asynchronously* bulk-writes (flushes) the data from the cache to the DB in the background at regular intervals.
*   **Pros**: Blazing fast write throughput. Absorbs database overload (DB batch inserts/updates).
*   **Cons**: Data loss risk if the cache instance crashes before the background write-to-DB occurs.
*   **Best for**: High-frequency, low-criticality writes (e.g., YouTube view counters, likes, analytic event tracking).

```java
// Write-Behind Example
public void recordVideoView(String videoId) {
    // 1. FAST: Only update Redis counter (Immediate return)
    redisTemplate.opsForValue().increment("video:views:" + videoId);
    
    // Note: DB is NOT updated here!
}

// Background worker running asynchronously (e.g., every 5 minutes)
@Scheduled(fixedDelay = 300000)
public void syncViewsToDatabase() {
    // 2. Scan Redis for updated view counts
    Map<String, Long> viewsToSync = fetchAllViewsFromRedis();
    
    // 3. Perform bulk batch update to DB
    db.batchUpdateVideoViews(viewsToSync);
    
    // 4. Optionally clear the synced keys from Redis
}
```

---

## 📖 4. Cache Eviction Policies

When the cache memory limit is reached, which item do we kick out?

1.  **LRU (Least Recently Used)**: Kicks out the item accessed furthest in the past. (Most common & practical default).
2.  **LFU (Least Frequently Used)**: Kicks out the item with the lowest overall access count. Better than LRU if you have consistent "hot" items over time.
3.  **FIFO (First In First Out)**: Kicks out the oldest item in the cache, regardless of access patterns.
4.  **TTL (Time To Live)**: Kicks out items automatically after a specific time duration expires. Ensures data doesn't remain stale forever.

#### Code Example: Configuring Eviction in Redis
```properties
# Redis configuration (redis.conf) for eviction
maxmemory 2gb
# Evict keys using LRU among keys that have an expire set
maxmemory-policy volatile-lru

# Other options:
# allkeys-lru -> Evict any key using LRU (useful if Redis is purely a cache)
# allkeys-lfu -> Evict any key using LFU
# noeviction  -> Return errors when memory limit reached (DO NOT USE for caching)
```

#### Code Example: Configuring Eviction in Caffeine (Local Cache)
```java
Caffeine.newBuilder()
    .maximumSize(10_000) // LRU-based size eviction
    .expireAfterWrite(10, TimeUnit.MINUTES) // TTL eviction
    .expireAfterAccess(5, TimeUnit.MINUTES) // Evict if unused for 5 mins
    .build();
```

---

## 📖 5. Common Cache Anomalies & Fixes (Interview Favorites!)

### 🚨 5.1 Cache Penetration
**Problem**: A malicious user constantly queries for an ID that **does not exist** in the DB (like `id=-999`). Cache always misses, DB always queried, causing DB overload.
**Fix**:
1.  **Cache the Null/Empty value** with a short TTL.
2.  **Use a Bloom Filter**: Placed before the cache. It quickly tells you if an ID *definitely does not exist*. If Bloom filter says it doesn't exist, block the request immediately.

```java
// 1. Caching Null value example
public Product getProduct(Long id) {
    String cacheKey = "prod:" + id;
    Product p = redis.get(cacheKey);
    
    if (p != null) {
        if (p.isNullStub()) return null; // We cached the "not found" state!
        return p;
    }
    
    p = db.getProduct(id);
    if (p == null) {
        redis.set(cacheKey, new ProductNullStub(), Duration.ofMinutes(5)); // Cache the miss
    } else {
        redis.set(cacheKey, p, Duration.ofHours(1));
    }
    return p;
}
```

### 🚨 5.2 Cache Breakdown (Dogpile Effect / Thundering Herd)
**Problem**: A highly popular "Hot Key" (e.g., iPhone launch price) expires (TTL ends). Suddenly, 10,000 concurrent requests hit the cache, see a miss, and all 10,000 requests hit the DB simultaneously to recalculate the same data, crashing the DB.
**Fix**: **Mutex Lock** (Distributed Lock). Only allow *one* thread to query the DB and repopulate the cache, while others wait.

```java
// Cache Breakdown Fix (Redis Distributed Lock)
public Product getHotProduct(String id) {
    Product p = redis.get("prod:" + id);
    if (p != null) return p;

    // Cache Miss! Acquire Lock to prevent Thundering Herd
    RLock lock = redissonClient.getLock("lock:prod:" + id);
    try {
        if (lock.tryLock(10, 10, TimeUnit.SECONDS)) {
            // Double-check cache inside lock!
            p = redis.get("prod:" + id);
            if (p == null) {
                p = db.getProduct(id);        // 1 DB call only!
                redis.set("prod:" + id, p);   // Update Cache
            }
        } else {
            // Didn't get lock, wait a bit and retry cache
            Thread.sleep(100);
            return getHotProduct(id);
        }
    } finally {
        if(lock.isHeldByCurrentThread()){
            lock.unlock();
        }
    }
    return p;
}
```

### 🚨 5.3 Cache Avalanche
**Problem**: Thousands of distinct cache keys happen to **expire at the exact same exact timestamp** (e.g., batch job loaded them all at exactly midnight with 24hr TTL). The cache suddenly drops all of them, sending all subsequent traffic straight to the DB.
**Fix**: Add **jitter (randomness)** to the TTLs.

```java
// Cache Avalanche Fix: Add random jitter to TTL (e.g., 24 hours +/- 60 mins)
long baseTTL = 24 * 60 * 60; // 24 hours
long jitter = new Random().nextInt(3600); // 0 to 60 mins random
redis.set("key", value, Duration.ofSeconds(baseTTL + jitter));
```

---

## 📖 6. Real-Time Scenarios (Architecture Questions)

### Q: "How would you design the cache for a live sports score app?"
**A:** Since data changes constantly and is read-heavy:
1.  **Cache Type**: Distributed Cache like Redis.
2.  **Pattern**: **Write-Through** or **Write-Behind**. When a score updates, the background worker immediately overwrites the Redis key (`match:123:score`).
3.  **Clients**: Apps connect via WebSockets. We don't wait for DB inserts; Redis Pub/Sub pushes the score update instantly to API servers, which push to client websockets.

### Q: "How would you handle caching user session data?"
**A:** Use **Redis** as a centralized session store (Spring Session Redis).
1.  **Why?** Ensures that if server A crashes, User is not implicitly logged out, because Server B can fetch the session from Redis.
2.  **TTL**: Tie the TTL to the session timeout (e.g., 30 mins, renewed on every access).

### Q: "We have an expensive Search Query that returns paginated results. How to cache?"
**A:** Caching paginated search results directly by URL/params is highly inefficient because filters create millions of permutations, causing low hit ratios.
**Better approach**:
1. Cache the *underlying objects* (e.g., `Product:Id`).
2. Run the search query on Elasticsearch/DB to get purely a list of `Product IDs` (which is fast).
3. Then do a `Redis MGET` (multi-get) to fetch the full product details for those IDs from the cache.
