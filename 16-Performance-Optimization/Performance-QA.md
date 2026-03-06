# ⚡ Performance & Optimization — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Performance Optimization?

Performance optimization is the process of **making your application faster, more efficient, and more responsive** while using fewer resources (CPU, memory, network). For a 12-year senior, this means understanding the JVM internals, profiling tools, and how to systematically identify and fix bottlenecks.

### Key Performance Metrics:
- **Throughput**: Requests per second (RPS) — how many requests the system handles
- **Latency**: Response time per request (p50, p95, p99) — how fast each request completes
- **Resource Utilization**: CPU, memory, disk I/O, network I/O usage
- **Scalability**: How performance changes as load increases

---

## 📖 Garbage Collection (GC) — Deep Dive

### Theory: What is Garbage Collection?
GC is the **automatic memory management** process in the JVM. It identifies and reclaims memory occupied by objects that are no longer reachable (no references pointing to them). Without GC, developers would have to manually free memory (like C/C++), leading to memory leaks and crashes.

### How GC works (Mark-Sweep-Compact):
```
Phase 1: MARK
  - Start from GC Roots (local variables, static fields, active threads)
  - Traverse object graph
  - Mark every reachable object as "alive"

Phase 2: SWEEP
  - Scan the heap
  - Remove all unmarked (unreachable) objects
  - Free their memory

Phase 3: COMPACT (optional)
  - Move surviving objects together
  - Eliminate memory fragmentation
  - Update all references to new locations
```

### GC Root Types:
```
What keeps an object alive?
1. Local variables on thread stacks
2. Static variables in loaded classes
3. JNI references (native code)
4. Active threads themselves
5. Synchronized monitors (locked objects)
6. Class objects loaded by classloaders
```

### GC Algorithms Available:

| GC | Best For | Pause Time | Throughput | Java Version |
|----|---------|-----------|-----------|-------------|
| **Serial** | Small apps, single core | Long (STW) | Low | All |
| **Parallel** | Batch processing, throughput | Medium | High | All |
| **G1** | General purpose (balanced) | Low-Medium | Medium-High | 7+ (default 9+) |
| **ZGC** | Ultra-low latency | Sub-ms | High | 15+ (prod: 21) |
| **Shenandoah** | Low latency (Red Hat) | Sub-ms | High | 12+ |

### G1 GC Internals (Most important for interviews):
```
G1 divides heap into ~2000 equally-sized REGIONS:
┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
│Eden │Eden │Surv.│ Old │Empty│ Old │Eden │Humu.│
│     │     │     │     │     │     │     │(big)│
└─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘

- Eden: new objects
- Survivor: survived 1+ minor GC
- Old: survived many GCs (promoted)
- Humongous: objects > 50% of region size

G1 collects regions with MOST garbage first (Garbage-First → name origin)
```

### JVM GC Tuning Examples:
```bash
# G1 GC (recommended for most apps)
-XX:+UseG1GC
-Xms4g -Xmx4g                     # Set equal (avoid resizing pauses)
-XX:MaxGCPauseMillis=200           # Target max pause
-XX:G1HeapRegionSize=16m           # Region size (1-32MB, power of 2)
-XX:InitiatingHeapOccupancyPercent=45  # Start mixed GC at 45% heap
-XX:G1NewSizePercent=20            # Young gen 20-60% of heap
-XX:G1MaxNewSizePercent=60
-XX:G1MixedGCCountTarget=8        # Spread mixed GC over 8 cycles
-XX:ParallelGCThreads=8           # GC threads (set to CPU cores)

# ZGC (Java 21+ for ultra-low latency)
-XX:+UseZGC
-XX:+ZGenerational                 # Java 21+ generational ZGC
-Xms4g -Xmx4g
# ZGC guarantees < 1ms pauses regardless of heap size!

# GC Logging (essential for diagnosis)
-Xlog:gc*:file=gc.log:tags,time,uptime,level:filecount=5,filesize=20m
```

---

## 📖 Profiling Tools

### 1. Java Flight Recorder (JFR) — Built into JDK
```bash
# Start recording (zero overhead in prod)
-XX:StartFlightRecording=duration=300s,filename=recording.jfr

# Or attach to running process
jcmd <pid> JFR.start duration=120s filename=/tmp/myapp.jfr

# OR programmatically
Recording recording = new Recording();
recording.start();
// ... do work ...
recording.stop();
recording.dump(Path.of("myapp.jfr"));
```

### 2. VisualVM — GUI Profiler
```
Features:
- Real-time CPU and memory monitoring
- Thread dump analysis
- Heap dump analysis
- Method-level CPU profiling (which methods are slow?)
- Memory allocation tracking (which objects created most?)

How to connect:
1. Start app with: -Dcom.sun.management.jmxremote=true
2. Open VisualVM → File → Add JMX Connection → localhost:PID
```

### 3. Async Profiler — Low-overhead sampling
```bash
# CPU profiling (which methods consume CPU?)
./profiler.sh -d 30 -f flamegraph.html <pid>

# Allocation profiling (which code creates objects?)
./profiler.sh -e alloc -d 30 -f alloc-flame.html <pid>

# Lock profiling (where is contention?)
./profiler.sh -e lock -d 30 -f lock-flame.html <pid>
```

---

## 📖 Common Performance Problems & Solutions

### Problem 1: Memory Leak
```java
// ═══ DIAGNOSIS ═══
// Symptoms: Heap grows steadily, full GC frequency increases, eventually OOM

// Step 1: Take heap dumps at intervals
jmap -dump:live,format=b,file=heap1.hprof <pid>
// Wait 10 minutes
jmap -dump:live,format=b,file=heap2.hprof <pid>

// Step 2: Compare in Eclipse MAT → find objects that grew between dumps
// Step 3: Check "shortest path to GC root" → find who's holding reference

// ═══ COMMON LEAK: Static collection growing without bound ═══
public class MetricsCollector {
    // ❌ LEAK: This list grows forever, never cleared!
    private static final List<Metric> allMetrics = new ArrayList<>();

    public void collect(Metric m) {
        allMetrics.add(m); // Called 1000 times/sec → OOM in hours
    }
}

// ✅ FIX: Use bounded structure
private static final int MAX_SIZE = 10000;
private static final Deque<Metric> recentMetrics = new ArrayDeque<>(MAX_SIZE);

public void collect(Metric m) {
    if (recentMetrics.size() >= MAX_SIZE) {
        recentMetrics.pollFirst(); // Remove oldest
    }
    recentMetrics.addLast(m);
}

// ═══ COMMON LEAK: ThreadLocal in thread pool ═══
// Thread pool reuses threads → ThreadLocal value persists → leak!
// ALWAYS call ThreadLocal.remove() in finally block

// ═══ COMMON LEAK: Connection/stream not closed ═══
// ❌ If exception occurs before close(), resource leaks
InputStream stream = new FileInputStream("large-file.csv");
process(stream);
stream.close(); // Never reached if process() throws!

// ✅ try-with-resources — auto-close guaranteed
try (InputStream stream = new FileInputStream("large-file.csv")) {
    process(stream);
} // close() called automatically, even on exception
```

### Problem 2: Slow Database Queries (most common in production)
```java
// ═══ DIAGNOSIS ═══
// Step 1: Enable SQL logging
// spring.jpa.show-sql=true
// logging.level.org.hibernate.SQL=DEBUG
// logging.level.org.hibernate.type.descriptor.sql.BasicBinder=TRACE

// Step 2: Check for N+1 queries
// Look for pattern: 1 query + N identical queries with different IDs

// Step 3: Run EXPLAIN ANALYZE on slow queries
// EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123 AND status = 'PAID';
// Check: Seq Scan (bad) vs. Index Scan (good)

// ═══ FIX: Add proper indexes ═══
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_user_status", columnList = "user_id, status"),
    @Index(name = "idx_created_at", columnList = "created_at DESC")
})
public class Order { /* ... */ }

// ═══ FIX: Use JOIN FETCH to prevent N+1 ═══
@Query("SELECT o FROM Order o JOIN FETCH o.user JOIN FETCH o.items WHERE o.status = :status")
List<Order> findActiveOrders(@Param("status") String status);

// ═══ FIX: Use projections — don't fetch entire entity ═══
@Query("SELECT new com.company.dto.OrderSummary(o.id, o.status, o.total) FROM Order o WHERE o.userId = :uid")
List<OrderSummary> findSummaryByUser(@Param("uid") Long userId);
```

### Problem 3: Thread Pool Exhaustion
```java
// ═══ SYMPTOMS ═══
// All requests hang, thread dump shows all threads WAITING
// Tomcat: "All 200 threads busy" → new requests rejected

// ═══ DIAGNOSIS: Take thread dump ═══
// jstack <pid> > threaddump.txt
// OR: kill -3 <pid> (prints to stdout)
// Look for: most threads stuck at same location

// Example: 200 threads all stuck at:
// "http-nio-8080-exec-199" WAITING
//   at sun.misc.Unsafe.park
//   at java.util.concurrent.locks.LockSupport.park
//   at com.zaxxer.hikari.pool.HikariPool.getConnection
// → DB connection pool exhausted!

// ═══ FIX: Tune HikariCP ═══
spring.datasource.hikari.maximum-pool-size=30    # Increase pool
spring.datasource.hikari.connection-timeout=5000  # Fail fast, don't wait forever
spring.datasource.hikari.leak-detection-threshold=30000 # Alert if conn held > 30s

// ═══ FIX: Make external calls async ═══
@Async
public CompletableFuture<Payment> processPaymentAsync(PaymentRequest req) {
    return CompletableFuture.completedFuture(paymentGateway.charge(req));
}
```

---

## 📖 JVM Tuning Checklist for Production

```bash
# 1. HEAP SIZING
-Xms4g -Xmx4g                     # Set equal — avoids resize pauses
# Rule: Start with container limit minus 25% for non-heap

# 2. GC SELECTION
-XX:+UseG1GC                       # Default for most apps
# OR -XX:+UseZGC for ultra-low latency

# 3. GC TUNING
-XX:MaxGCPauseMillis=200
-XX:InitiatingHeapOccupancyPercent=45

# 4. METASPACE
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m

# 5. THREAD STACK
-Xss512k                           # Reduce if many threads (default 1MB)

# 6. OOM PROTECTION
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/logs/heapdump.hprof
-XX:+ExitOnOutOfMemoryError        # Restart immediately on OOM

# 7. GC LOGGING
-Xlog:gc*:file=gc.log:tags,time,uptime,level:filecount=5,filesize=20m

# 8. JIT COMPILER
-XX:+TieredCompilation              # Default — progressive compilation
-XX:ReservedCodeCacheSize=256m      # Code cache for JIT-compiled methods

# 9. CONTAINER AWARENESS (K8s / Docker)
-XX:+UseContainerSupport             # Default in Java 10+
-XX:MaxRAMPercentage=75.0            # Use 75% of container memory for heap
```

---

## Interview Q: "How do you approach a performance issue in production?"

### Answer Framework (STAR for 12-year):
```
1. OBSERVE (don't guess — measure!)
   → Check dashboards: Grafana, Kibana, APM tool
   → Key metrics: response time p99, error rate, CPU, heap, GC pauses
   → Correlate: did anything change? (deployment, config, traffic spike)

2. HYPOTHESIZE
   → Is it CPU-bound or I/O-bound?
   → CPU-bound: thread dump → find hot methods → profile
   → I/O-bound: DB queries? External API calls? Kafka consumer lag?

3. REPRODUCE
   → Can you reproduce in staging?
   → Load test with realistic data (Gatling, JMeter, k6)

4. FIX
   → Apply the fix (add index, increase pool, fix N+1, add cache)
   → Validate with metrics — before-and-after comparison

5. PREVENT
   → Add alerts for the metric that caught this issue
   → Add load tests to CI/CD pipeline
   → Document in runbook
```
