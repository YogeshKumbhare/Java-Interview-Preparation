# 🏗️ System Design — Deep Dive Interview Q&A
## Target: 12+ Years Experience

---

## Q1: Design a Payment System (Like Google Pay / PhonePe)

### Requirements:
```
Functional:
- User can send money to another user
- User can check transaction history
- Merchants can receive payments
- Support UPI, Cards, Wallets

Non-functional:
- 99.99% uptime (≤52 minutes downtime/year)
- < 2 second transaction completion
- 100,000 TPS peak load
- Zero data loss
- Idempotent (duplicate protection)
```

### High-Level Architecture:
```
Mobile/Web Client
      ↓ HTTPS
API Gateway (Kong/AWS API GW)
  ├── Rate limiting (1000 req/min per user)
  ├── JWT validation
  ├── SSL termination
  └── DDoS protection
      ↓
Load Balancer (AWS ALB)
      ↓
Microservices:
├── User Service (user profiles, authentication)
├── Account Service (wallet balance, bank accounts)
├── Transaction Service (core payment processing)
├── Notification Service (SMS, email, push)
└── Fraud Detection Service (ML-based real-time)
      ↓
Async Layer (Kafka):
├── payment-initiated
├── payment-completed
├── payment-failed
└── fraud-alerts
      ↓
Databases:
├── User DB: PostgreSQL (ACID, consistency)
├── Transaction DB: PostgreSQL + Read Replicas
├── Cache: Redis Cluster (sessions, idempotency keys)
└── Analytics: ClickHouse (reporting, dashboards)
```

### Core Transaction Flow:
```java
@Service
@Transactional(isolation = Isolation.SERIALIZABLE)
public class PaymentTransactionService {

    public PaymentResult initiatePayment(PaymentRequest request) {
        // 1. Idempotency check (Redis)
        String idempotencyKey = request.getIdempotencyKey();
        Optional<PaymentResult> existing = idempotencyCache.get(idempotencyKey);
        if (existing.isPresent()) return existing.get();

        // 2. Fraud check (synchronous, < 100ms SLA)
        FraudCheckResult fraud = fraudDetectionService.check(request);
        if (fraud.isBlocked()) throw new FraudDetectedException(fraud.getReason());

        // 3. Debit sender (pessimistic lock)
        Account sender = accountRepo.findByIdWithLock(request.getSenderId());
        sender.debit(request.getAmount()); // Throws InsufficientFundsException if low

        // 4. Create pending transaction
        Transaction tx = transactionRepo.save(Transaction.pending(request));

        // 5. Publish to async processor (non-blocking)
        kafkaTemplate.send("payment-initiated", tx.getId(), PaymentInitiatedEvent.from(tx));

        // 6. Store idempotency result
        PaymentResult result = PaymentResult.pending(tx.getId());
        idempotencyCache.put(idempotencyKey, result, Duration.ofHours(24));

        return result;
    }
}

// Async second step — actual money movement
@KafkaListener(topics = "payment-initiated")
public void processPayment(PaymentInitiatedEvent event) {
    try {
        Account receiver = accountRepo.findByIdWithLock(event.getReceiverId());
        receiver.credit(event.getAmount());

        Transaction tx = transactionRepo.findById(event.getTransactionId());
        tx.markCompleted();
        transactionRepo.save(tx);

        kafkaTemplate.send("payment-completed", PaymentCompletedEvent.from(tx));

    } catch (Exception ex) {
        // Compensation — reverse debit
        Account sender = accountRepo.findByIdWithLock(event.getSenderId());
        sender.credit(event.getAmount()); // Refund

        Transaction tx = transactionRepo.findById(event.getTransactionId());
        tx.markFailed(ex.getMessage());
        transactionRepo.save(tx);

        kafkaTemplate.send("payment-failed", PaymentFailedEvent.from(tx));
    }
}
```

---

## Q2: Design URL Shortener (like bit.ly) — 100M URLs/day

### Capacity Estimation:
```
100M URLs created/day → 1,157 writes/second
Read:Write ratio = 100:1 → 115,700 reads/second
Average URL length = 100 bytes
Storage: 100M × 100 bytes × 365 days × 5 years = ~18 TB
```

### Architecture:
```java
@Service
public class UrlShortenerService {

    private static final String BASE62 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";

    @Autowired
    private RedisTemplate<String, String> redis;

    @Autowired
    private UrlRepository urlRepo;

    public String shorten(String longUrl, String userId) {
        // Check if URL already shortened (dedup)
        Optional<String> existing = urlRepo.findShortCodeByLongUrl(longUrl);
        if (existing.isPresent()) return buildShortUrl(existing.get());

        // Generate unique short code
        String shortCode = generateShortCode();

        // Store in DB
        UrlMapping mapping = new UrlMapping();
        mapping.setShortCode(shortCode);
        mapping.setLongUrl(longUrl);
        mapping.setCreatedBy(userId);
        mapping.setCreatedAt(Instant.now());
        mapping.setExpiresAt(Instant.now().plus(365, ChronoUnit.DAYS));
        urlRepo.save(mapping);

        // Cache for fast reads
        redis.opsForValue().set("url:" + shortCode, longUrl, Duration.ofHours(24));

        return buildShortUrl(shortCode);
    }

    @Cacheable(value = "urls", key = "#shortCode")
    public String expand(String shortCode) {
        // Redis first
        String cached = redis.opsForValue().get("url:" + shortCode);
        if (cached != null) {
            // Async analytics
            analyticsQueue.add(new ClickEvent(shortCode));
            return cached;
        }

        // DB fallback
        return urlRepo.findByShortCode(shortCode)
            .map(UrlMapping::getLongUrl)
            .orElseThrow(() -> new UrlNotFoundException(shortCode));
    }

    private String generateShortCode() {
        // Distributed ID generation — Snowflake algorithm
        long id = snowflakeIdGenerator.nextId();
        return encode(id);
    }

    private String encode(long num) {
        StringBuilder sb = new StringBuilder();
        while (num > 0) {
            sb.append(BASE62.charAt((int)(num % 62)));
            num /= 62;
        }
        return sb.reverse().toString();
    }
}
```

---

## Q3: Design a Rate Limiter

### Algorithms:
```
1. Token Bucket (recommended):
   - Bucket holds N tokens
   - Request consumes 1 token
   - Tokens refill at rate R per second
   - Burst allowed up to bucket size

2. Sliding Window Log:
   - Log each request timestamp
   - Count requests in last N seconds
   - More accurate, more memory

3. Fixed Window Counter:
   - Simple counter per window
   - Problem: boundary burst (100 at 11:59 + 100 at 12:00 = 200 in 2 sec)
```

```java
@Component
public class RedisRateLimiter {

    private final RedisTemplate<String, String> redis;

    // Token Bucket in Redis (Lua script for atomicity)
    private static final String LUA_SCRIPT = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])

        local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
        local tokens = tonumber(bucket[1]) or capacity
        local last_refill = tonumber(bucket[2]) or now

        -- Calculate tokens to add since last refill
        local elapsed = now - last_refill
        local new_tokens = math.min(capacity, tokens + (elapsed * refill_rate / 1000))

        if new_tokens < 1 then
            return 0  -- Rate limited
        end

        -- Consume 1 token
        redis.call('HMSET', key, 'tokens', new_tokens - 1, 'last_refill', now)
        redis.call('EXPIRE', key, 3600)
        return 1  -- Allowed
        """;

    public boolean isAllowed(String userId, int capacity, int refillRate) {
        String key = "rate_limit:" + userId;
        Long result = redis.execute(
            new DefaultRedisScript<>(LUA_SCRIPT, Long.class),
            Collections.singletonList(key),
            String.valueOf(capacity),
            String.valueOf(refillRate),
            String.valueOf(System.currentTimeMillis())
        );
        return result != null && result == 1L;
    }
}

// Spring Filter
@Component
public class RateLimitingFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws IOException, ServletException {
        String userId = extractUserId(req);
        if (!rateLimiter.isAllowed(userId, 100, 10)) { // 100 capacity, 10/sec refill
            res.setStatus(429);
            res.setHeader("Retry-After", "1");
            res.getWriter().write("{\"error\":\"Too many requests\"}");
            return;
        }
        chain.doFilter(req, res);
    }
}
```

---

## Q4: Caching Strategy — Cache Patterns

> **💡 Note:** For a comprehensive deep dive into caching, refer to the [Caching Strategies Module](../26-Caching-Strategies/Caching-QA.md).

```
Cache-Aside (Lazy Loading) — most common:
  Read: Check cache → miss → read DB → populate cache
  Write: Update DB → invalidate cache

Write-Through:
  Write: Update DB + update cache synchronously
  Pro: Cache always fresh
  Con: Write latency increases

Write-Behind (Write-Back):
  Write: Update cache → async DB write later
  Pro: Very fast writes
  Con: Data loss risk if cache fails

Read-Through:
  Read: Cache responsibility to pull from DB on miss

Cache-Aside Implementation:
```

```java
@Service
public class ProductCachingService {

    private final RedisTemplate<String, Product> redis;
    private final ProductRepository productRepo;

    public Product getProduct(Long id) {
        String key = "product:" + id;

        // Cache-aside: check cache first
        Product cached = redis.opsForValue().get(key);
        if (cached != null) {
            return cached;
        }

        // Cache miss — fetch from DB
        Product product = productRepo.findById(id)
            .orElseThrow(() -> new ProductNotFoundException(id));

        // Cache with TTL
        redis.opsForValue().set(key, product, Duration.ofMinutes(30));

        return product;
    }

    @Transactional
    public Product updateProduct(Long id, ProductUpdateRequest request) {
        Product product = productRepo.findById(id).orElseThrow();
        product.updateFrom(request);
        Product saved = productRepo.save(product);

        // Invalidate cache — NOT update (to avoid stale data race)
        redis.delete("product:" + id);

        return saved;
    }
}
```

---

## Q5: High Availability — Zero-Downtime Deployment

```
Blue-Green Deployment:
  Blue: Current production (100% traffic)
  Green: New version (0% traffic)
  Switch: Route traffic from Blue to Green
  Rollback: Instantly switch back if issues

Canary Release:
  Release to 1% → 5% → 25% → 100% of users
  Monitor error rates at each stage
  Automatic rollback if error rate exceeds threshold

Rolling Update (Kubernetes):
  Replace pods one by one
  Always maintain N replicas
```

```yaml
# Kubernetes Rolling Update Strategy
apiVersion: apps/v1
kind: Deployment
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 2   # Max 2 pods down at a time
      maxSurge: 2         # Max 2 extra pods during update
  template:
    spec:
      containers:
      - name: payment-service
        image: payment-service:v2.0
        readinessProbe:   # Traffic only when ready
          httpGet:
            path: /actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        livenessProbe:    # Restart if unhealthy
          httpGet:
            path: /actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
```
