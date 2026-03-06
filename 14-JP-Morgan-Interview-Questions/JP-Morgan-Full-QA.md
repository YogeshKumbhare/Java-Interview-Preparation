# 🏦 JP Morgan Chase — Java Backend / Spring Boot Interview Q&A
## (Recently Appeared — Real Interview Questions with Deep-Dive Answers)
**Target Experience: 12+ Years | Senior Java Backend Engineer**

---

## Question 1: How can we make an existing HashMap thread-safe WITHOUT using ConcurrentHashMap?

### ✅ Answer (Senior Level)

There are **4 approaches** to make a HashMap thread-safe without ConcurrentHashMap:

---

### Approach 1: `Collections.synchronizedMap()`
```java
Map<String, String> map = new HashMap<>();
Map<String, String> syncMap = Collections.synchronizedMap(map);

// USAGE — always synchronized on the map object
synchronized (syncMap) {
    for (Map.Entry<String, String> entry : syncMap.entrySet()) {
        System.out.println(entry.getKey() + " = " + entry.getValue());
    }
}
```
**How it works internally:**
- Wraps every method (get, put, remove) with `synchronized` on the map object
- Only ONE thread can access ANY method at a time → **lower throughput**
- ⚠️ Iteration MUST be manually synchronized — not automatic!

---

### Approach 2: Manual `synchronized` blocks
```java
public class ThreadSafeCache {
    private final Map<String, String> map = new HashMap<>();
    private final Object lock = new Object();

    public void put(String key, String value) {
        synchronized (lock) {
            map.put(key, value);
        }
    }

    public String get(String key) {
        synchronized (lock) {
            return map.get(key);
        }
    }
}
```

---

### Approach 3: `ReadWriteLock` (Best for Read-Heavy scenarios)
```java
public class ReadHeavyCache {
    private final Map<String, String> map = new HashMap<>();
    private final ReadWriteLock rwLock = new ReentrantReadWriteLock();

    public String get(String key) {
        rwLock.readLock().lock();
        try {
            return map.get(key);
        } finally {
            rwLock.readLock().unlock();
        }
    }

    public void put(String key, String value) {
        rwLock.writeLock().lock();
        try {
            map.put(key, value);
        } finally {
            rwLock.writeLock().unlock();
        }
    }
}
```
**Why this is better:** Multiple threads can READ simultaneously. Only WRITES are exclusive.
- At JP Morgan scale with millions of reads/second → THIS is the preferred answer.

---

### Approach 4: `StampedLock` (Java 8+ — Optimistic locking)
```java
public class OptimisticCache {
    private final Map<String, Object> map = new HashMap<>();
    private final StampedLock lock = new StampedLock();

    public Object get(String key) {
        long stamp = lock.tryOptimisticRead(); // No actual lock acquired
        Object value = map.get(key);
        if (!lock.validate(stamp)) { // Check if write happened
            stamp = lock.readLock();
            try {
                value = map.get(key);
            } finally {
                lock.unlockRead(stamp);
            }
        }
        return value;
    }

    public void put(String key, Object value) {
        long stamp = lock.writeLock();
        try {
            map.put(key, value);
        } finally {
            lock.unlockWrite(stamp);
        }
    }
}
```

### 🔑 When to Use What:
| Approach | Use Case |
|----------|----------|
| `synchronizedMap` | Simple use case, legacy code |
| Manual sync | Full control needed |
| `ReadWriteLock` | 80%+ reads, few writes (e.g., config cache) |
| `StampedLock` | Ultra-high performance, optimistic reads |

---

## Question 2: How do you ensure consistent data across multiple JVM instances (App1/JVM1 updated value reflected in App2/JVM2)?

### ✅ Answer (Senior Level — Distributed Systems)

This is a **distributed cache consistency** problem. In a JVM, local heap is private — JVM1's `ConcurrentHashMap` update is NEVER visible to JVM2.

### Solution 1: **Distributed Cache (Redis)**
```java
// Spring Boot + Redis
@Service
public class UserService {
    @Autowired
    private RedisTemplate<String, User> redisTemplate;

    public void updateUser(String userId, User user) {
        // Update DB
        userRepository.save(user);
        // Update Redis — now BOTH JVMs see latest data
        redisTemplate.opsForValue().set("user:" + userId, user, 30, TimeUnit.MINUTES);
    }

    public User getUser(String userId) {
        User cached = redisTemplate.opsForValue().get("user:" + userId);
        if (cached == null) {
            cached = userRepository.findById(userId).orElseThrow();
            redisTemplate.opsForValue().set("user:" + userId, cached);
        }
        return cached;
    }
}
```

### Solution 2: **Event-Driven Cache Invalidation via Kafka**
```java
// App1 publishes cache invalidation event
@Service
public class App1Service {
    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    public void updateValue(String key, String value) {
        localCache.put(key, value);
        db.update(key, value);
        kafkaTemplate.send("cache-invalidation", key); // Notify App2
    }
}

// App2 listens and invalidates its local cache
@KafkaListener(topics = "cache-invalidation")
public void onCacheInvalidated(String key) {
    localCache.remove(key); // App2 cache cleared
    // Next read fetches from DB — consistency restored
}
```

### Solution 3: **Database as the single source of truth** (simplest)
- Both JVMs always read from DB, no local cache
- Use DB read replicas to handle scale

### ⚙️ JP Morgan Context:
> In JP Morgan's real-time trading systems, they use Redis Cluster + Kafka for sub-millisecond consistency across nodes. The pattern is: **Write to DB → Publish event → All nodes invalidate local cache.**

---

## Question 3: Can we use @Transactional on protected or private methods?

### ✅ Answer

**Short answer: NO — and yes, but there's a nuance.**

### Why it doesn't work on `private` methods:
```java
@Service
public class PaymentService {

    // ❌ This @Transactional has NO EFFECT
    @Transactional
    private void processPaymentInternal(Payment p) {
        // Spring's AOP proxy CANNOT intercept private methods
        // because Java proxies work via method override
        paymentRepo.save(p);
    }

    // ✅ This works — public method is proxied
    @Transactional
    public void processPayment(Payment p) {
        paymentRepo.save(p);
    }
}
```

### Why it doesn't work on `protected` methods (with standard proxy):
```java
// Spring uses JDK Dynamic Proxy (interface-based) by default
// JDK Proxy can only intercept PUBLIC methods via interface
// protected methods are NOT part of the interface → NOT intercepted
```

### When does `protected` work?
```java
// With CGLIB proxy (class-based), protected CAN be intercepted
// Spring Boot auto-configures CGLIB when no interface is present
// BUT — Spring team still recommends only public @Transactional methods

@SpringBootApplication
// CGLIB is default in Spring Boot — class-based subclassing
```

### Internal mechanism:
```
Client Code
    ↓
Spring Proxy (wraps target bean)
    ↓ (intercepts only PUBLIC methods)
TransactionInterceptor.invoke()
    ↓
Opens transaction → calls real method → commits/rollbacks
    ↓
Returns to client
```

### 🔑 Rule for Interviews:
> `@Transactional` works **only on public methods** in Spring's standard proxy-based AOP. On private methods — silently ignored. On protected — depends on CGLIB, but avoid it for clarity and testability.

---

## Question 4: What is the internal implementation of the @Transactional annotation?

### ✅ Answer — Deep Dive

`@Transactional` is implemented via **Spring AOP + Proxy Pattern + TransactionInterceptor**.

### Step-by-step flow:
```
1. Bean is registered in ApplicationContext
2. BeanPostProcessor detects @Transactional → wraps bean in a Proxy
3. On method call → Proxy intercepts
4. TransactionInterceptor.invoke() is called
5. Looks up TransactionManager (JPA, JDBC, etc.)
6. Checks @Transactional attributes (propagation, isolation, rollbackFor)
7. Opens/joins/suspends transaction per propagation rule
8. Calls real method
9. On success → commit; On exception → rollback
```

### Pseudo Code of TransactionInterceptor:
```java
// This is what Spring does internally (simplified)
public Object invoke(MethodInvocation invocation) throws Throwable {
    TransactionAttribute txAttr = getTransactionAttribute(invocation.getMethod());
    PlatformTransactionManager tm = getTransactionManager();

    TransactionStatus status = tm.getTransaction(txAttr); // BEGIN
    try {
        Object result = invocation.proceed(); // Call actual method
        tm.commit(status); // COMMIT
        return result;
    } catch (Throwable ex) {
        if (shouldRollback(txAttr, ex)) {
            tm.rollback(status); // ROLLBACK
        } else {
            tm.commit(status);
        }
        throw ex;
    }
}
```

### Propagation Types:
```java
@Transactional(propagation = Propagation.REQUIRED)      // Use existing or create new
@Transactional(propagation = Propagation.REQUIRES_NEW)  // Always new tx, suspends outer
@Transactional(propagation = Propagation.NESTED)        // Savepoint within outer tx
@Transactional(propagation = Propagation.SUPPORTS)      // Join if exists, else no tx
@Transactional(propagation = Propagation.NEVER)         // Throw if tx exists
@Transactional(propagation = Propagation.MANDATORY)     // Throw if no tx exists
```

---

## Question 5: Application deployed to production with high traffic — how to handle? What scaling strategies?

### ✅ Answer — Production Architecture (12-year level)

### Immediate (< 5 minutes):
```
1. Check metrics → JVM heap, CPU, DB connection pool
2. Enable rate limiting immediately
3. Scale horizontally → Add more instances (Kubernetes: kubectl scale deployment app --replicas=10)
```

### Scaling Strategies:
```
Horizontal Scaling (Scale Out):
  └── Add more instances behind load balancer
  └── Stateless apps → easy to scale
  └── Session data → move to Redis

Vertical Scaling (Scale Up):
  └── Increase CPU/RAM of existing instance
  └── Quick fix but has limits

Database Scaling:
  └── Read Replicas → offload SELECT queries
  └── Connection pooling (HikariCP) → tune pool size
  └── Database sharding for very large datasets
  └── Caching layer (Redis) → reduce DB hits

Application Optimizations:
  └── Async processing → CompletableFuture, @Async
  └── Circuit breakers → Resilience4j
  └── Bulkhead pattern → limit concurrent requests per service
```

### Kubernetes auto-scaling example:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: payment-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: payment-service
  minReplicas: 3
  maxReplicas: 50
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Spring Boot Production Tuning:
```properties
# HikariCP connection pool
spring.datasource.hikari.maximum-pool-size=50
spring.datasource.hikari.minimum-idle=10
spring.datasource.hikari.connection-timeout=30000

# JVM tuning (in Dockerfile or startup script)
# -Xms512m -Xmx2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

---

## Question 6: How do you get alerts for 500 Internal Server Errors occurring every 5 minutes?

### ✅ Answer — Observability Stack

### Solution: Prometheus + Grafana + Alertmanager

```yaml
# Prometheus Alert Rule
groups:
  - name: application-alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_server_requests_seconds_count{status="500"}[5m])) > 0
        for: 1m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: "500 errors detected in last 5 minutes"
          description: "{{ $value }} errors per second on {{ $labels.instance }}"
```

### Spring Boot Actuator + Micrometer:
```xml
<!-- pom.xml -->
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-registry-prometheus</artifactId>
</dependency>
```

```properties
management.endpoints.web.exposure.include=health,metrics,prometheus
management.metrics.tags.application=payment-service
```

### Custom Alert in Spring Boot:
```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    private final MeterRegistry meterRegistry;
    private final Counter errorCounter;

    public GlobalExceptionHandler(MeterRegistry meterRegistry) {
        this.meterRegistry = meterRegistry;
        this.errorCounter = Counter.builder("app.errors.500")
            .description("Count of 500 errors")
            .register(meterRegistry);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception ex) {
        errorCounter.increment(); // Prometheus picks this up
        log.error("Internal Server Error", ex);
        return ResponseEntity.status(500)
            .body(new ErrorResponse("INTERNAL_ERROR", ex.getMessage()));
    }
}
```

### PagerDuty / Slack Alert Integration:
```yaml
# Alertmanager config
receivers:
  - name: slack-notifications
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR_WEBHOOK'
        channel: '#prod-alerts'
        text: '{{ .CommonAnnotations.description }}'
```

---

## Question 7: How do you handle partial failures in microservices architecture?

### ✅ Answer — Resilience Patterns

### Pattern 1: Circuit Breaker (Resilience4j)
```java
@Service
public class OrderService {

    @CircuitBreaker(name = "paymentService", fallbackMethod = "paymentFallback")
    @TimeLimiter(name = "paymentService")
    @Retry(name = "paymentService")
    public CompletableFuture<PaymentResponse> processPayment(Order order) {
        return CompletableFuture.supplyAsync(() ->
            paymentClient.processPayment(order.getPaymentDetails())
        );
    }

    // Fallback — executed when circuit is OPEN
    public CompletableFuture<PaymentResponse> paymentFallback(Order order, Exception ex) {
        log.warn("Payment service unavailable, queuing for retry: {}", order.getId());
        // Publish to Kafka for async retry
        kafkaTemplate.send("payment-retry-queue", order);
        return CompletableFuture.completedFuture(
            PaymentResponse.pending(order.getId())
        );
    }
}
```

### application.yml:
```yaml
resilience4j:
  circuitbreaker:
    instances:
      paymentService:
        failure-rate-threshold: 50      # Open when 50% requests fail
        wait-duration-in-open-state: 10s
        sliding-window-size: 10
        minimum-number-of-calls: 5
  retry:
    instances:
      paymentService:
        max-attempts: 3
        wait-duration: 500ms
        retry-exceptions:
          - java.net.ConnectException
```

### Pattern 2: Saga Pattern for distributed transactions
```
Order Service → creates order (PENDING)
    ↓ publishes OrderCreated event
Payment Service → charges card
    ↓ publishes PaymentProcessed event
Inventory Service → reserves stock
    ↓ publishes StockReserved event
Order Service → updates order to CONFIRMED

On Failure:
    Payment fails → publish PaymentFailed
    Order Service → compensate → cancel order
```

---

## Question 8: How would you log all methods annotated with @Transactional? (Pseudo code)

### ✅ Answer — Spring AOP

```java
@Aspect
@Component
@Slf4j
public class TransactionalLoggingAspect {

    // Pointcut: all methods annotated with @Transactional
    @Pointcut("@annotation(org.springframework.transaction.annotation.Transactional)")
    public void transactionalMethods() {}

    @Around("transactionalMethods()")
    public Object logTransactionalMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        String threadName = Thread.currentThread().getName();
        long startTime = System.currentTimeMillis();

        log.info("[TX-START] Method: {} | Thread: {}", methodName, threadName);
        log.info("[TX-ARGS] {}", Arrays.toString(joinPoint.getArgs()));

        try {
            Object result = joinPoint.proceed();
            long duration = System.currentTimeMillis() - startTime;
            log.info("[TX-COMMIT] Method: {} | Duration: {}ms", methodName, duration);
            return result;
        } catch (Exception ex) {
            long duration = System.currentTimeMillis() - startTime;
            log.error("[TX-ROLLBACK] Method: {} | Duration: {}ms | Error: {}",
                methodName, duration, ex.getMessage());
            throw ex;
        }
    }

    // Also capture method-level @Transactional attributes
    @Before("@annotation(transactional)")
    public void logTransactionalAttributes(
            JoinPoint jp,
            Transactional transactional) {
        log.debug("[TX-CONFIG] Method: {} | Propagation: {} | Isolation: {} | ReadOnly: {}",
            jp.getSignature().getName(),
            transactional.propagation(),
            transactional.isolation(),
            transactional.readOnly());
    }
}
```

---

## Question 9: Kafka with multiple consumer instances — how to ensure only ONE processes a message from a topic?

### ✅ Answer — Kafka Consumer Groups & Partitions

### Core Concept:
> In Kafka, **one partition is consumed by exactly ONE consumer within a consumer group**. This is the built-in guarantee.

```java
// application.yml
spring:
  kafka:
    consumer:
      group-id: payment-processor-group  # ALL instances share same group-id!
      auto-offset-reset: earliest
      key-deserializer: org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
```

```java
@Service
public class PaymentConsumer {

    // With same group-id, Kafka ensures partition-level exclusivity
    @KafkaListener(
        topics = "payment-events",
        groupId = "payment-processor-group",
        concurrency = "3"  // 3 threads = can handle 3 partitions simultaneously
    )
    public void processPayment(
            ConsumerRecord<String, PaymentEvent> record,
            Acknowledgment ack) {
        try {
            log.info("Processing partition: {}, offset: {}, key: {}",
                record.partition(), record.offset(), record.key());

            paymentService.process(record.value());

            ack.acknowledge(); // Manual commit after successful processing
        } catch (Exception ex) {
            // Send to DLQ
            dlqTemplate.send("payment-events-dlq", record.value());
            ack.acknowledge(); // Still commit to avoid reprocessing
        }
    }
}
```

### Key Configuration:
```yaml
spring:
  kafka:
    listener:
      ack-mode: MANUAL_IMMEDIATE  # Commit only after processing
    consumer:
      enable-auto-commit: false   # Critical — manual commit
      max-poll-records: 100       # Batch size
      fetch-max-wait: 500ms
```

### Partition Assignment Visualization:
```
Topic: payment-events (6 partitions)
Consumer Group: payment-processor-group

Instance 1: [Partition 0, Partition 1]
Instance 2: [Partition 2, Partition 3]
Instance 3: [Partition 4, Partition 5]

If Instance 2 dies → Kafka rebalances:
Instance 1: [Partition 0, Partition 1, Partition 2]
Instance 3: [Partition 3, Partition 4, Partition 5]
```

---

## Question 10: How do you handle failures during Kafka message consumption in microservices?

### ✅ Answer — Dead Letter Queue + Retry Pattern

```java
@Configuration
public class KafkaConfig {

    @Bean
    public ConsumerFactory<String, PaymentEvent> consumerFactory() {
        return new DefaultKafkaConsumerFactory<>(consumerProps());
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, PaymentEvent> kafkaListenerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, PaymentEvent> factory =
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());

        // Retry policy: 3 attempts with exponential backoff
        factory.setCommonErrorHandler(new DefaultErrorHandler(
            new DeadLetterPublishingRecoverer(kafkaTemplate,
                (record, ex) -> new TopicPartition(
                    record.topic() + "-DLQ", record.partition())),
            new FixedBackOff(1000L, 3) // 1 second interval, 3 retries
        ));

        return factory;
    }
}

// DLQ Consumer — Process failed messages
@KafkaListener(topics = "payment-events-DLQ", groupId = "dlq-processor")
public void processDlq(ConsumerRecord<String, PaymentEvent> record) {
    log.error("Processing DLQ: {}", record.value());
    // Alert ops team, store in DB, manual review
    alertingService.notifyDlqMessage(record);
    failedMessageRepository.save(new FailedMessage(record));
}
```

---

## Question 11: Duplicate payment — customer clicks "Pay" multiple times. How to handle? How to identify and inform client?

### ✅ Answer — Idempotency Pattern (Critical for FinTech)

```java
@Service
@Transactional
public class PaymentService {

    @Autowired
    private PaymentRepository paymentRepo;

    @Autowired
    private IdempotencyKeyRepository idempotencyRepo;

    public PaymentResponse processPayment(PaymentRequest request) {
        String idempotencyKey = request.getIdempotencyKey(); // UUID from client

        // Step 1: Check if this key was already processed
        Optional<IdempotencyRecord> existing =
            idempotencyRepo.findByKey(idempotencyKey);

        if (existing.isPresent()) {
            // Duplicate detected — return SAME previous response
            log.warn("Duplicate payment request: key={}", idempotencyKey);
            return PaymentResponse.builder()
                .status("DUPLICATE")
                .transactionId(existing.get().getTransactionId())
                .message("Payment already processed. TransactionId: "
                    + existing.get().getTransactionId())
                .build();
        }

        // Step 2: Lock to prevent concurrent duplicate processing
        // Database-level lock
        try {
            Payment payment = new Payment();
            payment.setAmount(request.getAmount());
            payment.setStatus("PROCESSING");
            paymentRepo.save(payment);

            // Step 3: Call payment gateway
            GatewayResponse response = paymentGateway.charge(payment);

            // Step 4: Save idempotency record ATOMICALLY
            IdempotencyRecord record = new IdempotencyRecord();
            record.setKey(idempotencyKey);
            record.setTransactionId(response.getTransactionId());
            record.setCreatedAt(Instant.now());
            record.setExpiresAt(Instant.now().plus(24, ChronoUnit.HOURS));
            idempotencyRepo.save(record);

            return PaymentResponse.success(response.getTransactionId());

        } catch (DuplicateKeyException ex) {
            // Race condition — another thread already processed it
            IdempotencyRecord saved = idempotencyRepo.findByKey(idempotencyKey).get();
            return PaymentResponse.duplicate(saved.getTransactionId());
        }
    }
}
```

### Client-side implementation:
```javascript
// Frontend generates UUID once per payment session
const idempotencyKey = crypto.randomUUID();

// Button click handler
document.getElementById('payBtn').addEventListener('click', async () => {
    document.getElementById('payBtn').disabled = true; // Disable immediately

    const response = await fetch('/api/payments', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': idempotencyKey // Same key always sent
        },
        body: JSON.stringify(paymentData)
    });

    if (response.status === 200) {
        const result = await response.json();
        if (result.status === 'DUPLICATE') {
            showMessage('Payment already processed! TransactionId: ' + result.transactionId);
        } else {
            showSuccess(result.transactionId);
        }
    }
});
```

### DB Schema:
```sql
CREATE TABLE idempotency_keys (
    id BIGSERIAL PRIMARY KEY,
    idempotency_key VARCHAR(255) UNIQUE NOT NULL,
    transaction_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL,
    expires_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_idempotency_key ON idempotency_keys(idempotency_key);
CREATE INDEX idx_expires_at ON idempotency_keys(expires_at); -- For cleanup job
```

---

## Question 12: How do you achieve zero data loss in your application?

### ✅ Answer — Multi-layer Strategy

```
LAYER 1: Database Level
├── Synchronous replication to read replicas
├── Point-in-time recovery (PITR) enabled
├── WAL (Write-Ahead Logging) shipping
└── Automated backups every hour

LAYER 2: Application Level
├── Transactional writes with proper rollback
├── Outbox Pattern (Event consistency)
└── Idempotent operations

LAYER 3: Messaging Level (Kafka)
├── acks=all (producer waits for all replicas)
├── min.insync.replicas=2
├── replication.factor=3
└── Manual acknowledgment (no auto-commit)

LAYER 4: Infrastructure Level
├── Multi-AZ deployment
├── Kubernetes PersistentVolumes with backup
└── Cross-region replication for DR
```

### Outbox Pattern (Prevents dual-write problem):
```java
@Service
@Transactional
public class OrderService {

    public Order createOrder(OrderRequest request) {
        // Step 1: Save order to DB
        Order order = orderRepo.save(new Order(request));

        // Step 2: Save event to OUTBOX table (SAME transaction!)
        OutboxEvent event = new OutboxEvent();
        event.setAggregateId(order.getId().toString());
        event.setEventType("ORDER_CREATED");
        event.setPayload(objectMapper.writeValueAsString(order));
        event.setCreatedAt(Instant.now());
        outboxRepo.save(event);

        // Both saved atomically! No dual-write problem.
        return order;
    }
}

// Separate poller publishes outbox events to Kafka
@Scheduled(fixedDelay = 1000)
public void publishOutboxEvents() {
    List<OutboxEvent> unpublished = outboxRepo.findUnpublished();
    for (OutboxEvent event : unpublished) {
        kafkaTemplate.send("order-events", event.getAggregateId(), event.getPayload());
        event.setPublished(true);
        outboxRepo.save(event);
    }
}
```

### Kafka Producer — Zero Loss Config:
```java
@Configuration
public class KafkaProducerConfig {

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.ACKS_CONFIG, "all");          // All replicas must ack
        config.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true); // No duplicates
        config.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 1);
        return new DefaultKafkaProducerFactory<>(config);
    }
}
```

---

## 🎯 JP Morgan Interview Tips

1. **Always mention trade-offs** — "ConcurrentHashMap is better for high concurrency, but ReadWriteLock gives you flexibility"
2. **Use numbers** — "We handle 50K TPS in our trading system using..."
3. **Mention monitoring** — Every system design answer should include observability
4. **Know the CAP theorem** — JP Morgan favors CP (Consistency + Partition Tolerance) systems
5. **Idempotency is king** — In financial systems, every payment API must be idempotent
6. **Think distributed-first** — Single JVM answers are wrong for production FinTech
