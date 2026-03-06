# 🔴 Real-Time Production Scenarios — Interview Q&A
## Target: 12+ Years Experience

---

## Scenario 1: "Production is down — Customer reports payment stuck"

### How to approach in 5 minutes:

```
Step 1: Observe (2 min)
├── Check Grafana dashboard
│   ├── Error Rate → spiked to 40%? Normal (1%)?
│   ├── Response Time → p99 latency?
│   └── JVM metrics → heap, GC pause?
├── Check Kibana logs → ERROR/EXCEPTION count last 10 min
└── Check Kafka → consumer lag spiking?

Step 2: Identify (1 min)
├── OutOfMemoryError → memory leak, JVM restart
├── Connection pool exhausted → DB is bottleneck
├── Kafka consumer lag → slow processing
└── Downstream service timeout → circuit breaker should fire

Step 3: Mitigate (1 min)
├── Rolling restart of affected pods
├── Increase replicas for capacity
├── Enable feature flag to bypass problematic feature
└── Return to previous deployment (rollback)

Step 4: Fix (remaining time)
├── Root cause analysis
├── Hotfix
└── Post-mortem document
```

### Code: Emergency feature toggle
```java
@Service
public class PaymentService {

    @Autowired
    private FeatureToggleService featureToggle;

    public PaymentResult processPayment(PaymentRequest request) {
        // Emergency bypass — toggle in LaunchDarkly/ConfigServer live
        if (featureToggle.isEnabled("use-legacy-payment-processor")) {
            return legacyPaymentProcessor.process(request);
        }
        return newPaymentProcessor.process(request);
    }
}
```

---

## Scenario 2: "Memory leak detected — heap keeps growing until OOM"

### Diagnosis:
```bash
# Take heap dump
jmap -dump:format=b,file=heapdump.hprof <pid>

# JVM flags (add to startup)
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/logs/heapdump.hprof

# GC log analysis
-XX:+PrintGCDetails -XX:+PrintGCDateStamps -Xloggc:/logs/gc.log

# Analyze with Eclipse MAT or JProfiler
# Look for:
# 1. Objects with highest retained heap
# 2. Shortest path to GC roots (classloaders, static fields, thread stack)
```

### Common Memory Leaks in Java:

**Leak 1: Static collections growing unbounded**
```java
// ❌ LEAK: Static List grows forever
public class EventProcessor {
    private static List<Event> processedEvents = new ArrayList<>();

    public void process(Event event) {
        processedEvents.add(event); // Never cleared!
    }
}

// ✅ Fix: Bounded cache
private static final int MAX_EVENTS = 1000;
private static final Deque<Event> processedEvents = new ArrayDeque<>();

public void process(Event event) {
    synchronized (processedEvents) {
        if (processedEvents.size() >= MAX_EVENTS) {
            processedEvents.pollFirst(); // Remove oldest
        }
        processedEvents.addLast(event);
    }
}
```

**Leak 2: ThreadLocal not cleaned up**
```java
// ❌ LEAK: ThreadLocal in thread pool — threads reused, old data persists
public class RequestContext {
    static ThreadLocal<User> currentUser = new ThreadLocal<>();
    // If never removed, grows with each request!!
}

// ✅ Fix: Always remove in finally
@Component
public class RequestFilter extends OncePerRequestFilter {
    protected void doFilterInternal(...) {
        try {
            RequestContext.currentUser.set(extractUser(request));
            chain.doFilter(request, response);
        } finally {
            RequestContext.currentUser.remove(); // CRITICAL
        }
    }
}
```

**Leak 3: Listener / Observer not deregistered**
```java
// ❌ LEAK: Event listeners accumulate if subscribers not removed
eventBus.register(new PaymentEventListener());
// If PaymentEventListener added every request → memory grows

// ✅ Fix: Register once, or deregister when done
@Component
@EventListener
public class PaymentEventListener { // Spring manages lifecycle
    @EventListener(PaymentEvent.class)
    public void handle(PaymentEvent event) { /* */ }
}
```

---

## Scenario 3: "Database is the bottleneck — high CPU on DB server"

### Investigation:
```sql
-- Find slow queries PostgreSQL
SELECT pid, query, state, wait_event_type, wait_event,
       age(clock_timestamp(), query_start) as query_age
FROM pg_stat_activity
WHERE state != 'idle'
  AND age(clock_timestamp(), query_start) > interval '1 second'
ORDER BY query_age DESC;

-- Find missing indexes
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'orders';

-- Find lock contention
SELECT blocked_locks.pid, blocked_activity.query as blocked_query,
       blocking_locks.pid as blocking_pid, blocking_activity.query as blocking_query
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.granted
JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;
```

### Solutions:
```java
// 1. Read from replica (Spring Boot)
@Configuration
public class DataSourceConfig {
    @Bean
    @Primary
    public DataSource writeDataSource() { return masterDataSource(); }

    @Bean
    public DataSource readDataSource() { return replicaDataSource(); }
}

@Service
public class OrderQueryService {
    @Transactional(readOnly = true) // Routes to read replica
    public Page<Order> findOrders(Pageable pageable) {
        return orderRepo.findAll(pageable);
    }
}

// 2. Caching hot queries
@Cacheable(value = "order-stats", key = "#userId")
public OrderStats getOrderStats(Long userId) {
    return orderRepo.computeStats(userId); // Expensive aggregation — cached
}

// 3. Async batch processing instead of sync queries
@Async
@Scheduled(fixedDelay = 60000)
public void precomputeDashboardStats() {
    // Pre-compute and cache — don't compute on user request
    List<Region> regions = regionService.getAllRegions();
    for (Region region : regions) {
        DashboardStats stats = computeStats(region);
        redis.opsForValue().set("stats:" + region.getId(), stats, Duration.ofHours(1));
    }
}
```

---

## Scenario 4: "Kafka consumer lag is 5 million messages — how to catch up?"

```java
// Root cause assessment:
// 1. Slow processing per message (external API calls, complex logic)
// 2. Not enough consumer instances
// 3. Consumer crashing and reprocessing
// 4. Message deserializaton errors causing infinite retry

// Solution 1: Increase concurrency
@KafkaListener(
    topics = "order-events",
    groupId = "order-processor",
    concurrency = "10" // Increase from 3 to 10 (match partition count)
)
public void process(OrderEvent event) { /* */ }

// Solution 2: Scale consumer pods
// kubectl scale deployment order-consumer --replicas=10

// Solution 3: Skip slow external API — use circuit breaker
@CircuitBreaker(name = "slowApi", fallbackMethod = "fallback")
public void callSlowExternalApi(OrderEvent event) { /* */ }

// Solution 4: Parallel processing within consumer
@KafkaListener(topics = "order-events", concurrency = "6")
public void process(List<ConsumerRecord<String, OrderEvent>> records, Acknowledgment ack) {
    // Process batch in parallel
    List<CompletableFuture<Void>> futures = records.stream()
        .map(r -> CompletableFuture.runAsync(
            () -> orderService.process(r.value()),
            processingExecutor))
        .collect(Collectors.toList());

    CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();
    ack.acknowledge(); // Commit after all processed
}
```

---

## Scenario 5: "Race condition — two users buying the last item simultaneously"

```java
// Problem: Both read stock=1, both pass check, both decrement → stock=-1!

// Solution 1: Pessimistic Lock (DB level)
@Transactional
public OrderResult purchaseItem(Long productId, Long userId) {
    // Lock the product row — prevents concurrent modification
    Product product = productRepo.findByIdWithLock(productId);
    // SELECT * FROM products WHERE id=? FOR UPDATE

    if (product.getStock() <= 0) {
        throw new OutOfStockException(productId);
    }

    product.setStock(product.getStock() - 1);
    productRepo.save(product);

    Order order = orderRepo.save(new Order(product, userId));
    return new OrderResult(order);
}

// Solution 2: Optimistic Lock (uses @Version)
@Transactional
@Retry(maxAttempts = 3)
public void decrementStock(Long productId) {
    Product product = productRepo.findById(productId).orElseThrow();
    if (product.getStock() <= 0) throw new OutOfStockException(productId);
    product.setStock(product.getStock() - 1);
    productRepo.save(product); // Throws OptimisticLockException if concurrent update
    // @Retry retries the entire method
}

// Solution 3: Redis atomic decrement (Redis guarantees atomicity)
public boolean reserveStock(Long productId) {
    String key = "stock:" + productId;
    Long remaining = redis.opsForValue().decrement(key);
    if (remaining != null && remaining >= 0) {
        return true; // Successfully reserved
    }
    // Undo — restore the decrement
    redis.opsForValue().increment(key);
    return false;
}

// Solution 4: DB atomic update
@Modifying
@Query("UPDATE Product p SET p.stock = p.stock - 1 WHERE p.id = :id AND p.stock > 0")
int decrementStockAtomically(@Param("id") Long id);

// Returns 0 if stock was already 0 (no rows updated)
int updated = productRepo.decrementStockAtomically(productId);
if (updated == 0) throw new OutOfStockException(productId);
```

---

## Scenario 6: "API response time degraded from 200ms to 3000ms"

### Debug framework:
```java
// Step 1: Add distributed tracing to identify slow span
@Aspect
@Component
public class MethodTimingAspect {
    @Around("@annotation(Timed)")
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        try {
            return pjp.proceed();
        } finally {
            long duration = TimeUnit.NANOSECONDS.toMillis(System.nanoTime() - start);
            if (duration > 500) {
                log.warn("[SLOW] {} took {}ms", pjp.getSignature(), duration);
            }
            meterRegistry.timer("method.execution", "method", pjp.getSignature().toString())
                .record(duration, TimeUnit.MILLISECONDS);
        }
    }
}

// Step 2: Check for N+1 queries
// Enable SQL logging temporarily:
// spring.jpa.show-sql=true
// spring.jpa.properties.hibernate.format_sql=true
// logging.level.org.hibernate.SQL=DEBUG
// logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE

// Step 3: Profile connection pool
// HikariCP metrics
// hikaricp.connections.active: how many connections in use
// hikaricp.connections.pending: how many requests waiting for connection
// If pending > 0 → pool exhausted → increase pool size or optimize queries
```

---

## Common Behavioral Interview Questions for 12-Year Seniors

### "Tell me about a time you handled a major production incident"
```
STAR Method:
Situation: Payment service had 40% error rate during Black Friday
Task: Restore service within 15 minutes (SLA)
Action:
  1. Rolled back last deployment (suspected root cause)
  2. Scaled from 5 to 20 pods for capacity
  3. Identified Kafka consumer lag due to DB deadlocks
  4. Added DB indexes to reduce query time
  5. Implemented circuit breaker to fail fast for slow payments
Result: Service restored in 8 minutes, added runbook for future incidents
```

### "How have you improved system performance?"
```
Example: Reduced payment API p99 from 4s to 400ms
1. Identified N+1 query issue (100 extra DB hits per request)
2. Added JOIN FETCH in JPQL
3. Added Redis caching for product catalog (hit rate 95%)
4. Made external fraud check async (was blocking main thread)
5. Added DB read replica for reporting queries
Result: 10x improvement, saved $50K/month in compute costs
```
