# 🎯 Cross-Questioning Deep Dives — Part 2
## Target: 12+ Years Experience | Senior/Lead/Architect

> **Note:** This extends Cross-Questioning-QA.md with additional scenarios across all domains.

---

## 6. Java Core Cross-Questions

### Scenario: You explained that String is immutable.
**Q: "If String is immutable, why does `str.replace('a', 'b')` seem to change it?"**
> **Answer:** "`replace()` does NOT modify the original String. It creates and returns a **new** String object with the replacements. The original `str` is unchanged. This is why you must do `str = str.replace('a', 'b')` — reassigning the reference to the new object. This immutability is why Strings are safe as HashMap keys and can be cached in the String Pool."

### Scenario: You said HashMap is O(1) for get/put.
**Q: "In the worst case, all keys hash to the same bucket. Doesn't that make HashMap O(n)?"**
> **Answer:** "Correct, with a pathological hash function, all keys land in one bucket creating a linked list — O(n) lookup. However, since Java 8, when a bucket exceeds **8 entries**, the linked list is **treeified** into a Red-Black Tree, making worst-case O(log n) instead of O(n). The threshold drops back to 6 to un-treeify. Also, a good `hashCode()` implementation (using Objects.hash()) distributes keys evenly, making collisions rare."

### Scenario: You used `volatile` keyword.
**Q: "How is `volatile` different from `synchronized`? When would `volatile` NOT be enough?"**
> **Answer:** "`volatile` guarantees **visibility** — all threads see the latest value written to the variable. But it does NOT guarantee **atomicity** of compound operations. Example: `counter++` involves read, increment, write — three steps. `volatile` ensures each thread reads the latest `counter` value, but two threads can still read the same value, increment, and write back the same result — losing one increment. For compound operations, use `AtomicInteger.incrementAndGet()` or `synchronized`. Use `volatile` only for simple flags (like `volatile boolean running = true`)."

---

## 7. Collections & Generics Cross-Questions

### Scenario: You used ConcurrentHashMap for a shared cache.
**Q: "ConcurrentHashMap is thread-safe for individual operations. But is this code thread-safe?"**
```java
if (!cache.containsKey(key)) {
    cache.put(key, expensiveComputation(key));
}
```
> **Answer:** "No, this is a classic **check-then-act** race condition. Between `containsKey()` and `put()`, another thread could insert the same key. Two threads run `expensiveComputation()` simultaneously. The fix is `cache.computeIfAbsent(key, k -> expensiveComputation(k))` — this is atomic in ConcurrentHashMap. It checks AND inserts in a single locked operation."

### Scenario: You chose ArrayList over LinkedList.
**Q: "LinkedList has O(1) insert at head, ArrayList has O(n). Why not use LinkedList?"**
> **Answer:** "In practice, ArrayList almost ALWAYS wins, even for insertions. LinkedList has terrible **cache locality** — each node is a separate object on the heap, scattered in memory. CPU cache misses destroy performance. ArrayList's internal array is contiguous memory — the CPU prefetcher loads nearby elements automatically. Joshua Bloch (Java Collections architect) said: 'Does anyone actually use LinkedList? I wrote it, and I never use it.' The only valid use case is a true Deque with many add/remove at both ends."

---

## 8. Database & Hibernate Cross-Questions

### Scenario: You used @OneToMany with FetchType.EAGER.
**Q: "You have 1000 orders, each with 50 items. You load Order list. What happens?"**
> **Answer:** "Disaster. With EAGER fetching, Hibernate generates a JOIN that returns 1000 × 50 = 50,000 rows. Worse, with multiple EAGER collections on the same entity, you get a **Cartesian product** — multiplying rows exponentially. And the `MultipleBagFetchException` crashes the app if two List collections are EAGER. Rule: **ALL collections should be LAZY**. Load them explicitly with `JOIN FETCH` or `@EntityGraph` only when needed."

### Scenario: You explained optimistic locking with @Version.
**Q: "Two users edit the same product simultaneously. User A saves first (version 0→1). User B tries to save (still has version 0). What exception is thrown and how do you handle it gracefully?"**
> **Answer:** "Hibernate throws `OptimisticLockException` (wrapped in Spring's `ObjectOptimisticLockingFailureException`). In the `@RestControllerAdvice`, I catch it and return HTTP 409 Conflict with a message: 'This record was modified by another user. Please refresh and try again.' The frontend shows the latest data and lets the user re-apply their changes. This is better than pessimistic locking (SELECT FOR UPDATE) which blocks other users."

---

## 9. DevOps & Kubernetes Cross-Questions

### Scenario: You deployed on Kubernetes with 3 replicas.
**Q: "A pod is consuming 95% memory but still responding to health checks. Kubernetes won't restart it. How do you handle this?"**
> **Answer:** "Kubernetes liveness probe only checks if the app responds. For resource-based eviction, I configure: (1) Resource limits: `resources.limits.memory: 512Mi` — Kubernetes OOM-kills the pod if exceeded. (2) Custom health checks that include memory: the `/actuator/health` endpoint can include a `DiskSpaceHealthIndicator` and custom `MemoryHealthIndicator` that returns DOWN if free memory < 10%. (3) Horizontal Pod Autoscaler (HPA) scales out based on memory metrics. (4) In the JVM: `-XX:+ExitOnOutOfMemoryError` ensures the pod crashes cleanly on OOM instead of limping."

### Scenario: You used environment variables for database passwords.
**Q: "Environment variables are visible in Kubernetes pod spec via `kubectl describe pod`. How do you secure secrets properly?"**
> **Answer:** "Plain env vars in K8s manifests are Base64-encoded (NOT encrypted). Solutions: (1) **Kubernetes Secrets** mounted as files, not env vars — files are tmpfs (in-memory), never on disk. (2) **Sealed Secrets** — encrypted in Git, only the cluster can decrypt. (3) **HashiCorp Vault** — dynamic secrets that auto-rotate. (4) **AWS Secrets Manager/GCP Secret Manager** with Spring Cloud integration — `spring.config.import=aws-secretsmanager:prod/db-credentials`. The app fetches secrets at startup, never stored in K8s manifests."

---

## 10. Performance & Scalability Cross-Questions

### Scenario: You added Redis caching for product catalog.
**Q: "What happens during a cache stampede — 10,000 concurrent requests for the same expired cache key simultaneously hit the database?"**
> **Answer:** "Cache stampede (thundering herd) is devastating. 10K requests simultaneously miss cache and hit DB. Solutions: (1) **Mutex/lock**: First request acquires a distributed lock (Redis SETNX), loads from DB, populates cache. Other 9,999 wait briefly and read from cache. (2) **Stale-while-revalidate**: Serve stale cached value while ONE background thread refreshes. (3) **Probabilistic early expiration**: Each request has a small random chance of refreshing before TTL expires, spreading the load. In production I use Caffeine's `refreshAfterWrite()` which does exactly this."

### Scenario: You have a slow API endpoint (3 second response time).
**Q: "Walk me through how you diagnose and fix this in production."**
> **Answer:** "Systematic approach: (1) **Identify**: Check APM (DataDog/New Relic) trace — is it DB, external API, or computation? (2) **Database**: Enable slow query log. Check EXPLAIN ANALYZE. Missing index? Add it. N+1? Add JOIN FETCH. (3) **External API**: Add circuit breaker timeout (3s max). Cache responses if possible. (4) **Computation**: Profile CPU — is it GC pauses? Check GC logs. (5) **Quick wins**: Add Redis cache (TTL 5 min), add database connection pool monitoring (HikariCP metrics), enable response compression. (6) **Architecture**: If fundamentally slow — make it async. Return 202 + poll for result."

---

## 11. API Design Cross-Questions

### Scenario: You designed a REST API with pagination.
**Q: "You're using offset-based pagination (page=3&size=20). A new record is inserted while the user is browsing page 2. What happens on page 3?"**
> **Answer:** "With offset pagination, the user sees a **duplicate record**. The new insert shifts all subsequent records by one position. Item 40 (last on page 2) becomes item 41 (first on page 3). The fix is **cursor-based pagination**: `GET /api/orders?after=order_id_123&limit=20`. The cursor is the last item's ID — no matter how many inserts happen, the next page starts right after that specific record. Twitter, Facebook, Slack all use cursor pagination. Offset pagination is only safe for static data."

### Scenario: You versioned your API as /api/v1/users.
**Q: "We now have v2 with breaking changes. How do you handle clients still on v1 without disrupting them?"**
> **Answer:** "Multi-version strategy: (1) **URL versioning** (/v1/users, /v2/users) — clearest, what I prefer. (2) Run both versions simultaneously for a deprecation period (6 months). (3) V1 controller delegates to V2 service with a **transformation layer** that converts V2 response to V1 format. (4) Monitor V1 usage via metrics. When traffic drops to near zero, announce sunset date with 90-day notice. (5) API gateway can route based on version header too: `Accept: application/vnd.company.v1+json`."

---

## 12. Microservices Cross-Questions

### Scenario: You use synchronous REST calls between microservices.
**Q: "Service A calls B, B calls C, C calls D. D is down. What happens to your entire system?"**
> **Answer:** "Cascading failure. A's thread is blocked waiting for B, which is blocked waiting for C, which is blocked waiting for D. With 200 Tomcat threads and 50 requests/second, all threads exhaust in 4 seconds. The entire system freezes — even endpoints that don't call D. Solutions: (1) **Circuit Breaker** (Resilience4j) on every inter-service call — fail fast instead of waiting. (2) **Timeout**: Never use default infinite timeout. Set 3s max. (3) **Bulkhead**: Isolate thread pools per downstream service — D's failure can't consume A's entire thread pool. (4) **Async**: Replace synchronous chains with event-driven (Kafka) — A publishes event, doesn't wait."
