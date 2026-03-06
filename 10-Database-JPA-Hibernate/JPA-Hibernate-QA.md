# 🗄️ Database, JPA & Hibernate — Deep Dive Interview Q&A
## Target: 12+ Years Experience

---

## Q1: JPA N+1 Problem — Detection and Solution

### The Problem:
```java
// N+1 Problem — each Order loads associated User in a SEPARATE query
List<Order> orders = orderRepo.findAll();
// Query 1: SELECT * FROM orders (returns 100 orders)

for (Order order : orders) {
    System.out.println(order.getUser().getName()); // Query 2-101!
    // Each getUser() fires: SELECT * FROM users WHERE id = ?
}
// TOTAL: 101 queries! Performance disaster.
```

### Solutions:

**Solution 1: JPQL JOIN FETCH**
```java
// Single query with JOIN
@Query("SELECT o FROM Order o JOIN FETCH o.user JOIN FETCH o.items WHERE o.status = :status")
List<Order> findByStatusWithUserAndItems(@Param("status") String status);

// Result: SELECT o.*, u.*, i.* FROM orders o
//         JOIN users u ON o.user_id = u.id
//         JOIN order_items i ON o.id = i.order_id
//         WHERE o.status = ?
// Only 1 query!
```

**Solution 2: @EntityGraph**
```java
@EntityGraph(attributePaths = {"user", "items", "items.product"})
List<Order> findAll(); // JOIN FETCH auto-generated
```

**Solution 3: Batch fetching (Hibernate-specific)**
```java
@Entity
public class Order {
    @OneToMany(fetch = FetchType.LAZY)
    @BatchSize(size = 20) // Load 20 orders' items in one query
    private List<OrderItem> items;
}
```

**Solution 4: DTO Projection with JPQL**
```java
@Query("""
    SELECT new com.company.dto.OrderSummaryDto(
        o.id, o.total, o.status, u.name, u.email
    )
    FROM Order o JOIN o.user u
    WHERE o.status = :status
    """)
List<OrderSummaryDto> findOrderSummaries(@Param("status") String status);
```

---

## Q2: Hibernate Caching Levels

> **💡 Note:** For a comprehensive deep dive into caching strategies, including redis, refer to the [Caching Strategies Module](../26-Caching-Strategies/Caching-QA.md).

```
Level 1 Cache (Session Cache):
  - Per SessionFactory session scope
  - ALWAYS enabled, cannot disable
  - Objects cached per session
  - Cleared when session closes

Level 2 Cache (SessionFactory Cache):
  - Shared across sessions
  - Requires explicit configuration (Ehcache, Redis)
  - Cache per entity class or query

Query Cache:
  - Caches query results (not entities)
  - Works with L2 cache
```

```java
// L2 Cache configuration
@Entity
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE)
public class Product {
    @Id private Long id;
    private String name;

    @OneToMany
    @Cache(usage = CacheConcurrencyStrategy.READ_WRITE) // Also cache collection
    private List<Category> categories;
}

// application.yml
spring:
  jpa:
    properties:
      hibernate:
        cache:
          use_second_level_cache: true
          use_query_cache: true
          region:
            factory_class: org.hibernate.cache.jcache.internal.JCacheRegionFactory

// Repository with caching
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {
    @QueryHints(@QueryHint(name = HINT_CACHEABLE, value = "true"))
    @Query("SELECT p FROM Product p WHERE p.category = :cat")
    List<Product> findByCategory(@Param("cat") String category);
}
```

---

## Q3: Transaction Isolation Levels

```sql
-- Isolation issues:
-- Dirty Read: Reading uncommitted data from another transaction
-- Non-repeatable Read: Same row returns different value in same transaction
-- Phantom Read: Same query returns different ROWS in same transaction

-- Isolation Levels (increasing isolation = decreasing performance):
-- READ_UNCOMMITTED: Sees uncommitted changes (all problems possible)
-- READ_COMMITTED: Only committed data (prevents dirty reads) [PostgreSQL default]
-- REPEATABLE_READ: Same row always same value (prevents non-repeatable reads) [MySQL default]
-- SERIALIZABLE: Full isolation (prevents all, including phantoms)
```

```java
// Spring @Transactional with isolation
@Transactional(isolation = Isolation.REPEATABLE_READ)
public BigDecimal getAccountBalance(String accountId) {
    // Multiple reads in this tx will see consistent data
    Account account = accountRepo.findById(accountId).orElseThrow();
    // ... business logic ...
    return account.getBalance();
}

// For financial operations — SERIALIZABLE
@Transactional(isolation = Isolation.SERIALIZABLE)
public void transferMoney(String fromId, String toId, BigDecimal amount) {
    Account from = accountRepo.findById(fromId).orElseThrow();
    Account to = accountRepo.findById(toId).orElseThrow();

    if (from.getBalance().compareTo(amount) < 0) {
        throw new InsufficientFundsException();
    }

    from.setBalance(from.getBalance().subtract(amount));
    to.setBalance(to.getBalance().add(amount));

    accountRepo.save(from);
    accountRepo.save(to);
}
```

---

## Q4: Optimistic vs Pessimistic Locking

### Optimistic Locking (no DB lock — uses version column):
```java
@Entity
public class BankAccount {
    @Id
    private Long id;

    private BigDecimal balance;

    @Version  // Hibernate manages automatically
    private Long version; // 0, 1, 2, 3...
}

// Hibernate generates: UPDATE bank_accounts SET balance=?, version=2 WHERE id=? AND version=1
// If version mismatch → OptimisticLockException → retry

@Service
public class AccountService {
    @Retryable(value = OptimisticLockingFailureException.class, maxAttempts = 3)
    @Transactional
    public void updateBalance(Long id, BigDecimal amount) {
        BankAccount account = accountRepo.findById(id).orElseThrow();
        account.setBalance(account.getBalance().add(amount));
        accountRepo.save(account);
        // If concurrent update happened, OptimisticLockException thrown
        // @Retryable will retry up to 3 times
    }
}
```

### Pessimistic Locking (DB-level lock):
```java
public interface AccountRepository extends JpaRepository<BankAccount, Long> {
    // SELECT ... FOR UPDATE — row is locked until transaction commits
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT a FROM BankAccount a WHERE a.id = :id")
    Optional<BankAccount> findByIdWithLock(@Param("id") Long id);

    // SELECT ... FOR SHARE — multiple reads allowed, no writes
    @Lock(LockModeType.PESSIMISTIC_READ)
    Optional<BankAccount> findById(Long id);
}

@Transactional
public void transferWithPessimisticLock(Long fromId, Long toId, BigDecimal amount) {
    // Lock both accounts to prevent concurrent modification
    BankAccount from = accountRepo.findByIdWithLock(fromId).orElseThrow();
    BankAccount to = accountRepo.findByIdWithLock(toId).orElseThrow();

    // Safe to modify — no other transaction can touch these rows
    from.debit(amount);
    to.credit(amount);

    accountRepo.save(from);
    accountRepo.save(to);
}
```

---

## Q5: Database Indexing — Practical Knowledge

```sql
-- Composite index — column order matters!
-- Good for: WHERE status = ? AND created_at > ?
CREATE INDEX idx_orders_status_date ON orders(status, created_at DESC);

-- Covering index — query satisfied entirely from index
-- SELECT id, status, total doesn't need to touch main table
CREATE INDEX idx_orders_covering ON orders(status) INCLUDE (id, total, created_at);

-- Partial index — index only subset of rows
CREATE INDEX idx_active_users ON users(email) WHERE is_active = true;

-- Expression index — index on computed column
CREATE INDEX idx_lower_email ON users(LOWER(email));
-- Supports: WHERE LOWER(email) = 'john@example.com'

-- Check index usage
EXPLAIN ANALYZE SELECT * FROM orders WHERE user_id = 123 AND status = 'PAID';
```

### JPA and Indexes:
```java
@Entity
@Table(name = "orders", indexes = {
    @Index(name = "idx_orders_user", columnList = "user_id"),
    @Index(name = "idx_orders_status_date", columnList = "status, created_at DESC"),
    @Index(name = "idx_orders_idempotency", columnList = "idempotency_key", unique = true)
})
public class Order {
    @Id
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(nullable = false)
    private String status;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @Column(name = "idempotency_key", unique = true)
    private String idempotencyKey;
}
```

---

## Q6: Spring Data JPA — Advanced Repository Patterns

```java
// Custom repository methods
public interface OrderRepository extends JpaRepository<Order, Long>,
        JpaSpecificationExecutor<Order> {

    // Derived query from method name
    List<Order> findByStatusAndUserIdOrderByCreatedAtDesc(String status, Long userId);

    // Pagination
    Page<Order> findByStatusAndCreatedAtAfter(String status, Instant after, Pageable page);

    // Projection — only fetch needed columns
    List<OrderSummaryProjection> findByUserId(Long userId);

    // Native query
    @Query(value = """
        SELECT DATE(created_at) as date, COUNT(*) as count, SUM(total) as revenue
        FROM orders
        WHERE status = 'PAID' AND created_at >= :start AND created_at <= :end
        GROUP BY DATE(created_at)
        ORDER BY date
        """, nativeQuery = true)
    List<DailyRevenueDto> findDailyRevenue(
        @Param("start") Instant start,
        @Param("end") Instant end
    );

    // Bulk update
    @Modifying
    @Transactional
    @Query("UPDATE Order o SET o.status = 'EXPIRED' WHERE o.status = 'PENDING' AND o.createdAt < :cutoff")
    int expireOldOrders(@Param("cutoff") Instant cutoff);
}

// Projection interface — only fetch what you need
public interface OrderSummaryProjection {
    Long getId();
    String getStatus();
    BigDecimal getTotal();
    String getUserName(); // Nested: user.name — Spring resolves via JOIN
}

// Specification for dynamic queries
public class OrderSpecifications {
    public static Specification<Order> hasStatus(String status) {
        return (root, query, cb) ->
            status == null ? cb.conjunction() : cb.equal(root.get("status"), status);
    }

    public static Specification<Order> createdAfter(Instant date) {
        return (root, query, cb) ->
            date == null ? cb.conjunction() : cb.greaterThan(root.get("createdAt"), date);
    }

    public static Specification<Order> belongsToUser(Long userId) {
        return (root, query, cb) -> cb.equal(root.get("userId"), userId);
    }
}

// Dynamic query building
List<Order> findOrders(String status, Instant from, Long userId) {
    return orderRepo.findAll(
        where(hasStatus(status))
            .and(createdAfter(from))
            .and(belongsToUser(userId)),
        PageRequest.of(0, 20, Sort.by("createdAt").descending())
    );
}
```

---

## Q7: Database Sharding and Partitioning

```
Vertical Partitioning:
  Split table columns into multiple tables
  orders_core (id, status, total)
  orders_shipping (order_id, address, tracking_number)

Horizontal Partitioning (Sharding):
  Split rows across multiple databases/tables

Sharding Strategies:
1. Hash-based: shard = hash(user_id) % num_shards
   + Even distribution
   - Resharding is hard

2. Range-based: users 1-1M → Shard1, 1M-2M → Shard2
   + Easy range queries
   - Hot spots (recent users all on same shard)

3. Directory-based: lookup table maps userId → shardId
   + Flexible
   - Lookup table is single point of failure
```

---

## Q8: Database connection pool tuning (HikariCP)

```properties
# application.properties
spring.datasource.hikari.minimum-idle=5
spring.datasource.hikari.maximum-pool-size=20
spring.datasource.hikari.idle-timeout=300000          # 5 min
spring.datasource.hikari.connection-timeout=20000     # 20 sec wait for conn
spring.datasource.hikari.max-lifetime=1200000         # 20 min max conn life
spring.datasource.hikari.keepalive-time=60000         # Keep alive ping
spring.datasource.hikari.leak-detection-threshold=60000 # Alert if conn held > 1 min

# Pool size formula (rough guide):
# pool_size = ((core_count * 2) + effective_spindle_count)
# e.g., 4 cores, SSD (1 spindle) = ((4*2)+1) = 9 connections per service
```
