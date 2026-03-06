# 🗄️ Hibernate / JPA Deep Dive — ACID, Internals & Interview Questions
## Target: 12+ Years | FAANG / JP Morgan / Goldman Sachs

---

## 📖 1. ACID Properties in Hibernate — Complete Theory

### What is ACID?
ACID is an acronym for **4 properties** that guarantee every database transaction is processed reliably — even in the face of system failures, concurrent access, or errors.

```
A — Atomicity    → All or Nothing
C — Consistency  → Valid State to Valid State
I — Isolation    → Transactions don't interfere
D — Durability   → Committed = Permanent
```

---

### 🅰️ ATOMICITY — "All or Nothing"

**What it means:** Every operation in a transaction either ALL succeed, or if ANY one fails, ALL changes are rolled back. There is NO partial success.

**Real-world analogy:** ATM withdrawal — the bank debits your account AND dispenses cash. If the machine jams after debiting but before dispensing, atomicity guarantees the debit is reversed. You don't lose money.

**How Hibernate implements it:**

```java
@Transactional  // Spring manages transaction — starts at method entry
public void transferMoney(Long fromId, Long toId, BigDecimal amount) {
    Account from = accountRepo.findById(fromId).orElseThrow();
    Account to   = accountRepo.findById(toId).orElseThrow();

    from.debit(amount);   // Step 1: Debit ₹10,000 from Account A
    accountRepo.save(from);

    // Simulate failure after debit — WITHOUT @Transactional this would be catastrophic!
    if (amount.compareTo(new BigDecimal("100000")) > 0) {
        throw new InsufficientLimitException("Transfer limit exceeded");
    }

    to.credit(amount);    // Step 2: Credit ₹10,000 to Account B
    accountRepo.save(to);

    // @Transactional guarantees: If InsufficientLimitException is thrown,
    // the debit to Account A is ROLLED BACK automatically.
    // Both accounts are unchanged — atomicity preserved!
}

// ⚠️ TRAP: @Transactional does NOT rollback on checked exceptions by default!
// For checked exceptions, use:
@Transactional(rollbackFor = Exception.class)
// OR configure specific rollback:
@Transactional(rollbackFor = {SQLException.class, BusinessException.class})
```

**What AOP does behind the scenes:**
```java
// Spring creates a PROXY around your class at startup.
// When you call transferMoney(), you're actually calling this proxy:
try {
    transactionManager.beginTransaction();   // Open TX
    transferMoney(fromId, toId, amount);     // Your actual code
    transactionManager.commit();             // Flush + commit to DB
} catch (RuntimeException ex) {
    transactionManager.rollback();           // UNDO everything!
    throw ex;
}
```

---

### 🅲 CONSISTENCY — "Valid State to Valid State"

**What it means:** A transaction must bring the database from ONE valid state to ANOTHER valid state. All data integrity rules (constraints, triggers, cascades) are maintained.

**Consistency in your code = DB constraints + application validation:**

```java
@Entity
@Table(name = "accounts",
    uniqueConstraints = @UniqueConstraint(columnNames = "account_number") // DB-level constraint
)
public class Account {
    @Id @GeneratedValue
    private Long id;

    @Column(nullable = false)
    private String accountNumber;

    @Min(value = 0, message = "Balance cannot be negative") // App-level constraint
    @Column(nullable = false)
    private BigDecimal balance;

    @Version // Optimistic locking version — prevents inconsistent concurrent updates
    private Long version;

    public void debit(BigDecimal amount) {
        if (this.balance.compareTo(amount) < 0) {
            throw new InsufficientFundsException("Balance ₹" + balance + " < debit ₹" + amount);
        }
        this.balance = this.balance.subtract(amount);
        // Invariant: balance >= 0 always maintained
    }
}
```

**How Hibernate flush order relates to consistency:**
```java
// Hibernate has a specific ACTION ORDER when flushing:
// 1. All EntityInsertAction (INSERTs)
// 2. All EntityUpdateAction (UPDATEs)
// 3. All CollectionRemoveAction (collection removals)
// 4. All CollectionUpdateAction (collection updates)
// 5. All EntityDeleteAction (DELETEs)
// This order respects FK constraints! Child inserts happen before parent deletes, etc.
```

---

### 🅸 ISOLATION — "Transactions Don't See Each Other's Work"

**What it means:** Concurrent transactions execute as if they were the only transaction. Each transaction sees a consistent view of data.

**4 Isolation Problems (read in increasing severity):**

| Problem | Description | Example |
|---------|-------------|---------|
| **Dirty Read** | Read uncommitted data from another TX | TX2 reads TX1's update before TX1 commits. TX1 rolls back → TX2 has phantom data |
| **Non-Repeatable Read** | Same row read twice gives different values | TX1 reads balance=₹1000. TX2 updates to ₹500 and commits. TX1 reads again → ₹500 |
| **Phantom Read** | Same query returns different ROWS | TX1 counts orders=10. TX2 inserts an order. TX1 counts again → 11 |
| **Lost Update** | Two TXs both update same row, one update is overwritten | Both read balance=₹1000, both add ₹100, last write wins → ₹1100 not ₹1200 |

**4 Isolation Levels (increasing strictness, decreasing concurrency):**

```java
// Set via @Transactional
@Transactional(isolation = Isolation.READ_UNCOMMITTED)  // Prevents: nothing
@Transactional(isolation = Isolation.READ_COMMITTED)    // Prevents: dirty reads (Most common default!)
@Transactional(isolation = Isolation.REPEATABLE_READ)   // Prevents: dirty + non-repeatable reads
@Transactional(isolation = Isolation.SERIALIZABLE)      // Prevents: all 3 + phantoms (slowest!)

// ⚡ Production rule: Use READ_COMMITTED for most services.
// Use SERIALIZABLE only for critical financial operations like account creation.
```

**Optimistic vs Pessimistic Locking:**

```java
// ═══ OPTIMISTIC LOCKING ═══
// Assumes conflicts are RARE. No DB lock acquired on read.
// Checks version at update time — throws if version changed.

@Entity
public class Product {
    @Id @GeneratedValue
    private Long id;

    private int stock;

    @Version  // Magic annotation! Hibernate adds WHERE version=X to every UPDATE
    private Long version;
}

// What Hibernate generates under the hood:
// UPDATE products SET stock=?, version=? WHERE id=? AND version=?
//                                              ^^^^^^^^^^^^^^^^^^^^
//                                              If version changed → 0 rows updated
//                                              → StaleObjectStateException thrown!

// Handling optimistic lock failure (retry logic):
@Retryable(value = OptimisticLockingFailureException.class, maxAttempts = 3)
@Transactional
public void reduceStock(Long productId, int quantity) {
    Product product = productRepo.findById(productId).orElseThrow();
    product.setStock(product.getStock() - quantity);
    productRepo.save(product); // Might throw OptimisticLockingFailureException
}

// ═══ PESSIMISTIC LOCKING ═══
// Assumes conflicts are FREQUENT. Acquires DB lock on SELECT.
// Other transactions BLOCK until lock is released.

@Transactional
public void bookTicket(Long seatId) {
    // For UPDATE → SQL: SELECT * FROM seats WHERE id=? FOR UPDATE
    Seat seat = seatRepo.findById(seatId, LockModeType.PESSIMISTIC_WRITE);

    if (!seat.isAvailable()) throw new SeatNotAvailableException();
    seat.book();
    seatRepo.save(seat);
    // Lock released when transaction commits
}

// When to use which:
// Optimistic  → High-read, low-conflict (product catalog updates, user profiles)
// Pessimistic → High-conflict, critical (seat booking, inventory, ticket sales)
```

---

### 🅳 DURABILITY — "Committed = Permanent"

**What it means:** Once a transaction is committed, its changes survive any system failure (crash, power outage, disk failure).

**How it works at DB level:**

```
Write-Ahead Logging (WAL):
1. DB writes transaction to the WAL (disk log) BEFORE updating actual data pages
2. Transaction is marked "committed" in the WAL
3. DB confirms commit to the application
4. At some point later, dirty pages are written from RAM to actual data files
5. If crash happens between 2 and 4 → WAL is replayed on restart → data recovered!

PostgreSQL WAL:    pg_wal directory
MySQL Binary Log:  binlog files
Oracle Redo Log:   redo log files
```

**How Hibernate's flush/commit relates to durability:**

```java
@Transactional
public void saveOrder(Order order) {
    orderRepo.save(order); // Does NOT write to DB yet! Just adds to Session's dirty map.

    // Hibernate batches writes and FLUSHES at:
    // 1. Before query execution (FlushMode.AUTO — default)
    // 2. At transaction commit
    // 3. When Session.flush() is called explicitly

    // Session.flush() → sends SQL to DB (but NOT committed yet)
    // Transaction.commit() → DB commits → WAL written → DURABLE ✅
}

// FlushModeType settings:
// ALWAYS: Flush before every query (safest, but slow — many DB round trips)
// AUTO:   Flush before queries that might be affected by pending changes (default)
// COMMIT: Only flush at commit (fastest, but read-your-writes issues)
// MANUAL: Never flush automatically (you call session.flush() explicitly)
```

---

## 📖 2. Hibernate Session & Entity Lifecycle — Deep Dive

### Entity States (4 States You MUST Know):

```
┌──────────┐   new MyEntity()   ┌──────────┐
│  TRANSIENT│ ─────────────────▶ │  MANAGED │
│(not known  │   session.save()  │(in session│
│ to session) │   session.persist()│ 1st-level │
└──────────┘                   │  cache)  │
                                └──────────┘
                                     │ session.evict(e)
                                     │ session.close()
                                     ▼
                               ┌──────────┐
                               │ DETACHED │ session.merge(e) ──▶ MANAGED
                               │(was managed│
                               │ now not) │
                               └──────────┘
                                     │ session.delete(e) or
                                     │ @OneToMany cascade = DELETE
                                     ▼
                               ┌──────────┐
                               │ REMOVED  │ ──▶ (after commit) deleted from DB
                               └──────────┘
```

```java
// TRANSIENT — just a new Java object, Hibernate doesn't know about it
Product product = new Product("iPhone", 99999.0); // Not in session

// PERSISTENT / MANAGED — session tracks every change
Session session = sessionFactory.openSession();
session.beginTransaction();
session.save(product);              // Now MANAGED — session tracks it
product.setPrice(89999.0);          // No save() needed! Hibernate detects dirty state
session.getTransaction().commit();  // Hibernate auto-generates UPDATE! (dirty checking)

// DETACHED — was managed, session closed
session.close();                    // product is now DETACHED
product.setPrice(79999.0);          // Hibernate doesn't KNOW about this change!

// Merge detached entity (attach to new session)
Session session2 = sessionFactory.openSession();
Product managed = (Product) session2.merge(product); // NOW tracked again with latest state
session2.getTransaction().commit(); // UPDATE fired

// REMOVED
session.delete(product);            // Schedules DELETE — still in memory until commit
```

### How Dirty Checking Works Internally:

```
At session.flush() time, Hibernate:
1. Iterates all MANAGED entities in the session (1st-level cache)
2. Compares current field values vs snapshot taken when entity was loaded
3. For every field that CHANGED → generates UPDATE SQL for that entity
4. This is why you DON'T always need to call save() on managed entities!

Snapshot is stored in EntityEntry inside the Hibernate PersistenceContext.

⚠️ Performance warning: If your session has 10,000 managed entities,
   Hibernate checks ALL 10,000 at flush time! This is why:
   - Use StatelessSession for batch processing (no dirty checking, no 1st-level cache)
   - Or clear the session periodically: session.flush(); session.clear();
```

---

## 📖 3. Hibernate N+1 Problem — 3 Solutions

### The Problem:
```java
// Loading 100 orders and accessing their items → 1 + 100 = 101 queries! ❌
List<Order> orders = orderRepo.findAll();  // Query 1: SELECT * FROM orders
for (Order o : orders) {
    List<Item> items = o.getItems();       // Query 2-101: SELECT * FROM items WHERE order_id=?
    System.out.println(items.size());
}
```

### Solution 1: JOIN FETCH (JPQL)
```java
// Single query with JOIN — loads everything at once ✅
@Query("SELECT o FROM Order o JOIN FETCH o.items WHERE o.status = :status")
List<Order> findWithItems(@Param("status") String status);
// SQL: SELECT o.*, i.* FROM orders o JOIN items i ON o.id=i.order_id WHERE o.status=?

// ⚠️ Limitation: Produces a CARTESIAN PRODUCT for multiple collections!
// If Order has items AND payments, JOIN FETCH both explodes the result set!
// Solution for multiple collections → use @EntityGraph or SUBSELECT
```

### Solution 2: @EntityGraph
```java
@EntityGraph(attributePaths = {"items", "items.product", "shipment"})
@Query("SELECT o FROM Order o WHERE o.userId = :userId")
List<Order> findOrdersWithDetails(@Param("userId") Long userId);
// Hibernate generates a single query with all JOINs for the specified paths
// Best for: Multiple nested associations without cartesian product issues
```

### Solution 3: @BatchSize (Lazy Loading with batching)
```java
@Entity
public class Order {
    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)
    @BatchSize(size = 20)  // Load items for 20 orders at once instead of 1 by 1
    private List<Item> items;
}
// When you access items of 100 orders, Hibernate fires:
// SELECT * FROM items WHERE order_id IN (1,2,3,...,20)  → 5 queries instead of 100!
// Best for: When you can't always predict which associations will be accessed
```

---

## 📖 4. Hibernate Caching — L1, L2, Query Cache

### First-Level Cache (L1) — Session Cache:
```java
// Enabled by default, scoped to Session (= one transaction)
// Same session, same ID → SAME OBJECT, no DB query!

try (Session session = sessionFactory.openSession()) {
    User u1 = session.get(User.class, 1L); // SELECT from DB
    User u2 = session.get(User.class, 1L); // SAME OBJECT from L1 cache — NO DB query!
    System.out.println(u1 == u2); // TRUE — identical reference!

    // L1 is cleared when:
    session.evict(u1);  // Remove specific entity
    session.clear();    // Clear entire L1 cache
    session.close();    // Session closed — L1 dies with it
}
// After session closes → L1 is gone. New session = empty cache.
```

### Second-Level Cache (L2) — Shared Across Sessions:
```java
// Must be explicitly configured. Shared across all sessions in the application.
// Popular providers: Ehcache, Hazelcast, Redis (via Redisson)

// application.properties:
// spring.jpa.properties.hibernate.cache.use_second_level_cache=true
// spring.jpa.properties.hibernate.cache.region.factory_class=org.hibernate.cache.ehcache.EhCacheRegionFactory
// spring.jpa.properties.hibernate.cache.use_query_cache=true

@Entity
@Cacheable                              // Enable L2 caching for this entity
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE) // Cache strategy
public class Country {
    @Id
    private Long id;
    private String name;
    // Countries rarely change — perfect for L2 cache!
}

// CacheConcurrencyStrategy options:
// READ_ONLY        → Only for immutable entities (fastest). Exception on update attempt.
// NONSTRICT_READ_WRITE → Small window of stale data possible. No locking overhead.
// READ_WRITE       → Actual locking — safe for read/write. Good default.
// TRANSACTIONAL    → Full transaction support (requires JTA transaction manager)
```

### Query Cache:
```java
// Cache the RESULT of a specific JPQL query (not just entities)
@Repository
public class CountryRepository {

    @QueryHints(@QueryHint(name = HINT_CACHEABLE, value = "true"))
    @Query("SELECT c FROM Country c ORDER BY c.name")
    List<Country> findAllCached();
    // The list of country IDs is cached. Hibernate re-fetches entities by ID from L2 or DB.

    // ⚠️ Query cache invalidated when ANY country entity changes!
    // Avoid query cache for frequently-updated entities.
}
```

---

## 📖 5. Common Hibernate Interview Questions with Answers

### Q1: What is the difference between `save()`, `persist()`, `merge()`, `saveOrUpdate()`?

| Method | Context | Returns | Immediate SQL? | Detached entities? |
|--------|---------|---------|----------------|--------------------|
| `save()` | Hibernate API | Serializable (ID) | Not always | ❌ No |
| `persist()` | JPA standard | void | Not immediately | ❌ No |
| `merge()` | JPA standard | Managed copy | Not immediately | ✅ Yes |
| `saveOrUpdate()` | Hibernate API | void | Not always | ✅ Yes |

```java
// PERSIST: Must be used within a transaction. Does NOT accept detached entities.
Product p = new Product("Laptop", 50000.0);
em.persist(p);                    // p must be TRANSIENT or MANAGED

// MERGE: Returns a NEW managed copy. Original object stays DETACHED.
Product detached = getDetachedProduct();
Product managed = em.merge(detached);  // managed = new managed copy
// DON'T USE detached after this → use managed!

// SAVE vs PERSIST: save() returns ID immediately (useful in Hibernate); persist() doesn't.
```

---

### Q2: Why does Hibernate throw LazyInitializationException?
```java
// ❌ CLASSIC TRAP: Session closed before accessing lazy collection
@Transactional
public Order getOrder(Long id) {
    return orderRepo.findById(id).get();
}
// → Session closes when @Transactional method returns

// In Controller:
Order order = orderService.getOrder(1L);
order.getItems().size(); // 💥 LazyInitializationException! Session is closed!

// FIXES:
// 1. Access within @Transactional
// 2. Use JOIN FETCH in query
// 3. Use @EntityGraph
// 4. Use DTO projection (SELECT new OrderDTO(o.id, o.total) ...)
// 5. Use OpenSessionInView (anti-pattern in production!)
```

---

### Q3: What is the difference between `get()` and `load()`?
```java
// get() → immediate DB hit, returns null if not found
User user = session.get(User.class, 999L); // SELECT fired immediately
if (user == null) System.out.println("Not found"); // Safe!

// load() → returns PROXY (lazy), DB hit deferred until proxy is accessed
User proxy = session.load(User.class, 999L); // NO SELECT yet!
System.out.println(proxy.getId()); // Still no SELECT (already in proxy)
System.out.println(proxy.getName()); // NOW SELECT fires → ObjectNotFoundException if missing!

// Use get() → when you're not sure the entity exists
// Use load() → when you need an entity reference for a relationship (e.g., setting FK without loading full entity)
Order order = new Order();
order.setUser(session.load(User.class, userId)); // Efficient! Only sets FK column, no full User load
```

---

### Q4: Explain `@OneToMany` cascade types:
```java
@Entity
public class Order {
    @OneToMany(
        mappedBy = "order",
        cascade = CascadeType.ALL,     // All operations cascade to items
        orphanRemoval = true           // Remove items when removed from the list
    )
    private List<Item> items = new ArrayList<>();
}

// CascadeType options:
// PERSIST  → session.persist(order) also persists all items
// MERGE    → session.merge(order) also merges all items
// REMOVE   → session.delete(order) also deletes all items
// DETACH   → session.detach(order) also detaches all items
// REFRESH  → session.refresh(order) also refreshes items from DB
// ALL      → All of the above

// orphanRemoval = true:
order.getItems().remove(item); // ← This DELETE will be fired for the removed item!
// vs cascade = REMOVE: Only fires when ORDER is deleted, not when item removed from list.
```

---

### Q5: What is the Open Session in View (OSIV) anti-pattern?
```java
// OSIV: Keeps the Hibernate session open for the ENTIRE HTTP request duration
// Including the view rendering phase (Thymeleaf, REST serialization)

// Controlled by:
spring.jpa.open-in-view=true  // Spring Boot DEFAULT — enables OSIV!
// This is WHY Spring Boot doesn't throw LazyInitializationException in simple apps!
// But it's dangerous:

// Problems with OSIV in production:
// 1. DB connections held open for the full request duration (including network time!)
// 2. In a 200ms request: 5ms DB + 195ms network + view rendering = connection held 200ms
// 3. Under load: thread pool exhausted → all requests queue waiting for connections!
// 4. Lazy queries happen in the view layer → hard to detect N+1 problems

// For production microservices:
spring.jpa.open-in-view=false  // Turn off! Use DTOs or @EntityGraph instead.
```

---

### Q6: What is HikariCP and how do you tune it?
```java
// HikariCP = Ultra-fast JDBC connection pool (Spring Boot default since 2.0)

// application.properties tuning:
spring.datasource.hikari.maximum-pool-size=20       // Max DB connections (default 10) — tune carefully!
spring.datasource.hikari.minimum-idle=5             // Keep 5 connections warm always
spring.datasource.hikari.connection-timeout=30000   // Wait max 30s for connection before throwing
spring.datasource.hikari.idle-timeout=600000        // Close idle connections after 10 min
spring.datasource.hikari.max-lifetime=1800000       // Max connection lifetime = 30 min (< DB timeout)
spring.datasource.hikari.keepalive-time=60000       // Ping DB every 60s to keep connections alive
spring.datasource.hikari.leak-detection-threshold=30000 // Warn if connection held > 30s (find leaks!)

// Sizing formula:
// Max pool size = (Core count × 2) + effective spindle count
// For 4-core app server: ~10 connections is often optimal
// More connections ≠ faster! DB has its own thread limits.

// ⚠️ HikariCP Connection Leak — how to detect:
// Set leak-detection-threshold=30000 → Hikari logs a WARNING with stack trace
// if a connection is held for > 30 seconds without being returned to pool!
```

---

## 🎯 Hibernate Cross-Questioning Scenarios

**Q: "@Transactional works on the method in Service but not when I call it from another method within the same class. Why?"**
> **Answer:** "This is the Spring **self-invocation problem**. Spring AOP wraps your class in a proxy. When you call a method from OUTSIDE the class, the call goes through the proxy (which handles the transaction). But when method A calls method B **within the same class**, it calls `this.methodB()` — which bypasses the proxy entirely. No transaction is started.
>
> The fix is to either: (1) inject the service into itself using `@Autowired` (breaks encapsulation), (2) move the method to a separate service bean, or (3) use AspectJ weaving instead of Spring JDK/CGLIB proxies (compiles AOP aspects directly into bytecode — no proxy needed). Option 2 is the cleanest approach."

---

**Q: "How does Hibernate know which fields changed without us calling save()?"**
> **Answer:** "Hibernate implements **Automatic Dirty Checking** through its `PersistenceContext`. When an entity is first loaded in a session, Hibernate takes a **snapshot** of all its field values and stores it in an `EntityEntry` alongside the actual object. At flush time (before a query or at commit), Hibernate iterates all managed entities and compares current field values against the stored snapshots using a field-by-field comparison. Any changed field triggers a corresponding UPDATE SQL. This is why Hibernate is powerful but also why large sessions with many entities can be slow at flush time — it's O(n × fields) comparison work."

---

**Q: "Your application is growing and Hibernate L2 cache is showing stale data. How do you handle cache invalidation?"**
> **Answer:** "Cache invalidation is the classic 'hard problem' in computing. For Hibernate L2 cache in a clustered environment (multiple app instances), each instance has its own local L2 cache. When one instance updates an entity, the other instances' caches become stale immediately.
>
> Solutions: (1) Use a **distributed L2 cache** — Hazelcast or Redis as the cache provider. All instances share the same cache store and receive invalidation events. (2) Set `CacheConcurrencyStrategy.READ_WRITE` which uses a 'soft lock' mechanism during updates to temporarily invalidate the cache entry across nodes. (3) For critical data, disable L2 caching and rely on DB queries with HikariCP connection pooling and DB-level read replicas for scaling. (4) Use event-driven cache invalidation — publish a cache eviction event to a Kafka topic; all instances consume it and evict the specific key."

---

# ═══════════════════════════════════════════════════
# 🚀 SECTION 2: Performance Tuning & Optimization
# ═══════════════════════════════════════════════════

## 📖 6. Fetching Strategies — Lazy vs Eager (Complete Guide)

### Theory:
Hibernate has two strategies for loading associated entities/collections:
- **EAGER** — load the associated data **immediately** when the parent is loaded (JOIN or separate query)
- **LAZY** — load the associated data **only when first accessed** (proxy placeholder until then)

```java
// ═══ DEFAULT FETCH TYPES (know these by heart!) ═══
@OneToOne   → default: EAGER   ← surprisingly eager!
@ManyToOne  → default: EAGER   ← also eager by default!
@OneToMany  → default: LAZY    ← always lazy
@ManyToMany → default: LAZY    ← always lazy

// PROBLEM with EAGER defaults:
@Entity
public class Order {
    @ManyToOne(fetch = FetchType.EAGER)  // DEFAULT — dangerous!
    private User user;

    @OneToOne(fetch = FetchType.EAGER)   // DEFAULT — dangerous!
    private Address billingAddress;
}
// Simple: SELECT * FROM orders → triggers:
// SELECT * FROM users WHERE id=?
// SELECT * FROM addresses WHERE id=?
// Because BOTH are EAGER — 3 queries for a single order load!
// If loading 100 orders → 1 + 100 + 100 = 201 queries!
```

### Always Override to LAZY for @ManyToOne and @OneToOne:
```java
@Entity
public class Order {
    @ManyToOne(fetch = FetchType.LAZY)   // ← ALWAYS do this!
    @JoinColumn(name = "user_id")
    private User user;

    @OneToOne(fetch = FetchType.LAZY)    // ← ALWAYS do this!
    @JoinColumn(name = "address_id")
    private Address billingAddress;

    @OneToMany(mappedBy = "order", fetch = FetchType.LAZY)  // Already lazy by default, keep it
    private List<Item> items;
}
// Now: SELECT * FROM orders → just 1 query!
// User/Address loaded only when you explicitly access them.
```

### Dynamic Fetching at Runtime (Best of Both Worlds):
```java
// Use LAZY everywhere by default in @Entity definition.
// At query time, CHOOSE what to eagerly load based on the use case:

// Use Case 1: List page — only needs order summary, no items
List<Order> summaries = orderRepo.findAll(); // Only orders loaded

// Use Case 2: Order detail page — needs items and user
@EntityGraph(attributePaths = {"items", "user", "billingAddress"})
@Query("SELECT o FROM Order o WHERE o.id = :id")
Optional<Order> findDetailById(@Param("id") Long id); // Everything loaded in 1 join query

// Use Case 3: Report — needs items but not user
@Query("SELECT o FROM Order o JOIN FETCH o.items WHERE o.createdAt > :date")
List<Order> findRecentWithItems(@Param("date") LocalDate date);
```

### Named Entity Graph (reusable):
```java
@Entity
@NamedEntityGraph(
    name = "Order.withItemsAndUser",
    attributeNodes = {
        @NamedAttributeNode("items"),
        @NamedAttributeNode(value = "items", subgraph = "items.product"),
        @NamedAttributeNode("user")
    },
    subgraphs = {
        @NamedSubgraph(name = "items.product",
                       attributeNodes = @NamedAttributeNode("product"))
    }
)
public class Order { ... }

// Use the named graph:
@EntityGraph("Order.withItemsAndUser")
Optional<Order> findById(Long id);
```

---

## 📖 7. Batching & Bulk Operations — StatelessSession

### JDBC Batch Size — Bulk Inserts/Updates:
```java
// application.properties:
spring.jpa.properties.hibernate.jdbc.batch_size=50   // Send 50 SQLs in 1 DB roundtrip
spring.jpa.properties.hibernate.order_inserts=true   // Group inserts by entity type
spring.jpa.properties.hibernate.order_updates=true   // Group updates by entity type
spring.jpa.properties.hibernate.jdbc.batch_versioned_data=true  // Required for @Version

// Without batching: 10,000 inserts = 10,000 DB round trips = SLOW
// With batch_size=50: 10,000 inserts = 200 DB round trips = 50x faster!

@Transactional
public void bulkInsert(List<Product> products) {
    for (int i = 0; i < products.size(); i++) {
        entityManager.persist(products.get(i));

        if (i % 50 == 0) { // Matches batch_size
            entityManager.flush();   // Send accumulated batch to DB
            entityManager.clear();   // Clear L1 cache to avoid OOM!
        }
    }
}

// ⚠️ GenerationType.IDENTITY breaks batching!
// IDENTITY requires immediate INSERT to get the ID → can't batch!
// Use SEQUENCE instead:
@Id
@GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "product_seq")
@SequenceGenerator(name = "product_seq", sequenceName = "product_seq", allocationSize = 50)
// allocationSize=50 matches batch_size → Hibernate pre-allocates 50 IDs in memory
private Long id;
```

### StatelessSession — High-Volume Processing Without PersistenceContext:
```java
// StatelessSession bypasses:
// ✅ No First-Level cache (dirty checking skipped → MUCH faster for batch ops)
// ✅ No dirty checking overhead
// ✅ No cascading
// ✅ No collection management
// ✅ No interceptors/event listeners

// Perfect for: ETL jobs, data migration, reporting, bulk processing

@Service
public class BulkMigrationService {

    @Autowired
    private SessionFactory sessionFactory;

    public void migrateMillionRows() {
        // NOT @Transactional — StatelessSession manages its own transactions
        StatelessSession statelessSession = sessionFactory.openStatelessSession();

        try {
            Transaction tx = statelessSession.beginTransaction();

            // Stream results to avoid loading all into memory:
            Stream<LegacyOrder> orders = statelessSession
                .createQuery("SELECT o FROM LegacyOrder o", LegacyOrder.class)
                .stream(); // Returns lazily-fetched stream

            orders.map(legacy -> transformToNewOrder(legacy))
                  .forEach(newOrder -> {
                      statelessSession.insert(newOrder); // Direct INSERT, no L1 cache!
                  });

            tx.commit();
        } catch (Exception e) {
            statelessSession.getTransaction().rollback();
            throw e;
        } finally {
            statelessSession.close();
        }
    }
}

// StatelessSession limitations:
// ❌ No cascading (must save parent and child explicitly)
// ❌ No lazy loading (everything is immediate)
// ❌ No @Version optimistic locking (no entity state tracked)
// Use it only when performance > safety and you control all writes explicitly
```

---

# ═══════════════════════════════════════════════════
# 🗺️ SECTION 3: Advanced Mappings & Design
# ═══════════════════════════════════════════════════

## 📖 8. Inheritance Strategies — Trade-offs Comparison

### Strategy 1: SINGLE_TABLE (Default)
```java
// All classes in hierarchy → ONE database table
// Discriminator column tells Hibernate which type each row is

@Entity
@Table(name = "payments")
@Inheritance(strategy = InheritanceType.SINGLE_TABLE)
@DiscriminatorColumn(name = "payment_type", discriminatorType = DiscriminatorType.STRING)
public abstract class Payment {
    @Id @GeneratedValue private Long id;
    private BigDecimal amount;
    private LocalDateTime createdAt;
}

@Entity
@DiscriminatorValue("CREDIT_CARD")
public class CreditCardPayment extends Payment {
    private String cardNumber;   // Only used for this subtype
    private String cvv;
}

@Entity
@DiscriminatorValue("UPI")
public class UpiPayment extends Payment {
    private String upiId;        // Only used for this subtype
}

// Generated table:
// payments: id, amount, created_at, payment_type, card_number, cvv, upi_id
// card_number, cvv → NULL for UPI rows
// upi_id → NULL for credit card rows

// ✅ Pros: Fastest queries (no JOINs), simple structure
// ❌ Cons: Many nullable columns, can't apply NOT NULL constraints on subtype fields
// Use when: Many subtypes, frequent polymorphic queries, denormalization OK
```

### Strategy 2: JOINED (Normalized)
```java
@Entity
@Table(name = "payments")
@Inheritance(strategy = InheritanceType.JOINED)
public abstract class Payment {
    @Id @GeneratedValue private Long id;
    private BigDecimal amount;
}

@Entity
@Table(name = "credit_card_payments")  // Separate table!
public class CreditCardPayment extends Payment {
    // id here is FK to payments.id (shared PK)
    private String cardNumber;
    private String cvv;
}

// Tables:
// payments: id, amount
// credit_card_payments: id (FK → payments.id), card_number, cvv
// upi_payments: id (FK → payments.id), upi_id

// SQL for CreditCardPayment:
// SELECT p.*, c.* FROM payments p
// INNER JOIN credit_card_payments c ON p.id = c.id
// WHERE p.id = ?

// ✅ Pros: Fully normalized, NOT NULL constraints on subtype fields, clean schema
// ❌ Cons: JOINs for every query → slower, complex SQL
// Use when: Data integrity critical, infrequent polymorphic queries, normalization required
```

### Strategy 3: TABLE_PER_CLASS
```java
@Entity
@Inheritance(strategy = InheritanceType.TABLE_PER_CLASS)
public abstract class Payment {
    @Id @GeneratedValue(strategy = GenerationType.SEQUENCE)  // Must use SEQUENCE, not IDENTITY!
    private Long id;
    private BigDecimal amount;
}

@Entity
@Table(name = "credit_card_payments")
public class CreditCardPayment extends Payment {
    private String cardNumber; // amount is DUPLICATED in this table
}

// Tables:
// credit_card_payments: id, amount, card_number, cvv  ← amount duplicated!
// upi_payments: id, amount, upi_id                    ← amount duplicated!

// Polymorphic query (find all payments) → UNION ALL of all tables:
// SELECT * FROM credit_card_payments UNION ALL SELECT * FROM upi_payments

// ✅ Pros: Each table fully self-contained, good for queries on single type
// ❌ Cons: UNION ALL for polymorphic queries (very slow), data duplication
// Use when: Rarely do polymorphic queries, each type accessed independently
```

### Inheritance Strategy Comparison:
| Aspect | SINGLE_TABLE | JOINED | TABLE_PER_CLASS |
|--------|-------------|--------|-----------------|
| **DB Tables** | 1 | 1 + N subtypes | N subtypes only |
| **Query Performance** | ✅ Fastest (no JOIN) | ⚠️ JOIN per load | ❌ UNION for poly |
| **Normalization** | ❌ Nullable columns | ✅ Fully normalized | ⚠️ Duplication |
| **Schema clarity** | ❌ Mixed columns | ✅ Clean | ✅ Clean per type |
| **Best for** | Simple hierarchy | Complex, integrity-critical | Independent types |

---

## 📖 9. Composite Keys & Embeddables

### @EmbeddedId (Preferred approach):
```java
// Composite primary key: order_id + product_id → OrderItemId

@Embeddable  // Must be Embeddable; must implement Serializable and equals/hashCode!
public class OrderItemId implements Serializable {
    private Long orderId;
    private Long productId;

    // Required: equals() and hashCode() based on ALL fields
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderItemId)) return false;
        OrderItemId that = (OrderItemId) o;
        return Objects.equals(orderId, that.orderId) &&
               Objects.equals(productId, that.productId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(orderId, productId);
    }
}

@Entity
@Table(name = "order_items")
public class OrderItem {
    @EmbeddedId
    private OrderItemId id;  // Composite PK

    private int quantity;
    private BigDecimal price;

    @ManyToOne
    @MapsId("orderId")          // Maps orderId field of EmbeddedId to order FK
    @JoinColumn(name = "order_id")
    private Order order;

    @ManyToOne
    @MapsId("productId")        // Maps productId field of EmbeddedId to product FK
    @JoinColumn(name = "product_id")
    private Product product;
}

// Querying:
OrderItemId pk = new OrderItemId(orderId, productId);
OrderItem item = em.find(OrderItem.class, pk);
```

### @IdClass (Alternative, JPA spec):
```java
// IdClass — the composite key is a separate class but fields are repeated in entity

public class EmployeeProjectId implements Serializable {
    private Long employeeId;
    private Long projectId;
    // equals, hashCode required!
}

@Entity
@IdClass(EmployeeProjectId.class)
public class EmployeeProject {
    @Id private Long employeeId;  // Repeated from IdClass
    @Id private Long projectId;   // Repeated from IdClass

    private String role;

    @ManyToOne
    @JoinColumn(name = "employeeId", insertable = false, updatable = false)
    private Employee employee;
}

// @EmbeddedId vs @IdClass:
// @EmbeddedId: Cleaner (PK is one field), better with @MapsId
// @IdClass: Less boilerplate for simple cases, but fields duplicated
```

### @Embeddable for Value Objects (non-PK):
```java
@Embeddable
public class Address {
    private String street;
    private String city;
    @Column(name = "zip_code")
    private String zipCode;
    private String country;
}

@Entity
public class Customer {
    @Id @GeneratedValue private Long id;
    private String name;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street",  column = @Column(name = "billing_street")),
        @AttributeOverride(name = "city",    column = @Column(name = "billing_city")),
        @AttributeOverride(name = "zipCode", column = @Column(name = "billing_zip"))
    })
    private Address billingAddress;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street",  column = @Column(name = "shipping_street")),
        @AttributeOverride(name = "city",    column = @Column(name = "shipping_city")),
        @AttributeOverride(name = "zipCode", column = @Column(name = "shipping_zip"))
    })
    private Address shippingAddress;
    // ↑ Both map to same table with different column names!
}
```

---

## 📖 10. Custom Types — @UserType & @Formula

### @Formula — Derived/Calculated Properties:
```java
@Entity
public class Product {
    @Id @GeneratedValue private Long id;

    @Column(name = "price")
    private BigDecimal price;

    @Column(name = "tax_rate")
    private BigDecimal taxRate;

    // @Formula: Calculated by DB at query time — NO column in DB!
    @Formula("price * (1 + tax_rate)")
    private BigDecimal priceWithTax;

    // Subquery formula — count from related table:
    @Formula("(SELECT COUNT(*) FROM reviews r WHERE r.product_id = id)")
    private Long reviewCount;

    // ⚠️ Formula uses NATIVE SQL — not JPQL! Be DB-aware.
    // Not updatable — always computed from DB formula
}
```

### Custom UserType — Mapping Java types to DB types:
```java
// Use case: Map a Java enum List → stored as comma-separated DB VARCHAR

public class StringListType implements UserType<List<String>> {

    @Override
    public int getSqlType() {
        return Types.VARCHAR;
    }

    @Override
    public Class<List<String>> returnedClass() {
        return (Class) List.class;
    }

    @Override
    public List<String> nullSafeGet(ResultSet rs, int position,
                                    SharedSessionContractImplementor session, Object owner)
                                    throws SQLException {
        String value = rs.getString(position);
        if (value == null) return Collections.emptyList();
        return Arrays.asList(value.split(","));
    }

    @Override
    public void nullSafeSet(PreparedStatement st, List<String> value, int index,
                            SharedSessionContractImplementor session) throws SQLException {
        if (value == null || value.isEmpty()) {
            st.setNull(index, Types.VARCHAR);
        } else {
            st.setString(index, String.join(",", value));
        }
    }

    @Override
    public boolean equals(List<String> x, List<String> y) { return Objects.equals(x, y); }

    @Override
    public boolean isMutable() { return true; }

    // ... other methods with default implementations
}

// Register and use:
@Entity
public class Article {
    @Id @GeneratedValue private Long id;

    @Type(StringListType.class)
    @Column(name = "tags")  // DB column is VARCHAR("java,spring,hibernate")
    private List<String> tags; // Java side is List<String>
}

// Simpler alternative for JSON columns (PostgreSQL):
@Type(JsonType.class) // Using Hypersistence Utils library
@Column(columnDefinition = "jsonb")
private Map<String, Object> metadata;
```

---

# ═══════════════════════════════════════════════════
# 🔒 SECTION 4: Transaction & Concurrency — Complete
# ═══════════════════════════════════════════════════

## 📖 11. Transaction Propagation — All 6 Levels Explained

```java
// PROPAGATION defines: What happens to the transaction when a @Transactional method
// is called from WITHIN another @Transactional method?

// ━━━ REQUIRED (Default) ━━━
@Transactional(propagation = Propagation.REQUIRED)
public void methodA() {
    methodB(); // B joins A's transaction — same transaction
}
// If A's TX exists → B joins it. If not → B creates a new one.
// If B throws → ENTIRE transaction (A+B) rolls back.

// ━━━ REQUIRES_NEW ━━━
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void auditLog(String event) {
    // ALWAYS creates a NEW transaction, suspending the outer one.
    // If outer TX rolls back → audit log is NOT rolled back!
    // Use for: Audit logging, notifications that should always be saved
}

@Transactional                      // Main business TX
public void processOrder(Order o) {
    orderRepo.save(o);              // Main TX
    auditLogService.log("ORDER CREATED"); // auditLog runs in SEPARATE TX!
    throw new RuntimeException("Something wrong");
    // Main TX rolls back → order NOT saved
    // Audit TX already committed → audit log IS saved! ✅
}

// ━━━ NESTED ━━━
@Transactional(propagation = Propagation.NESTED)
public void saveDraft(Draft d) {
    // Creates a SAVEPOINT inside the outer transaction.
    // If NESTED rolls back → only rolls back to the savepoint, not entire TX.
    // If outer TX rolls back → nested also rolls back.
    // Not all DB/JPA providers support NESTED (PostgreSQL does via savepoints).
}

// ━━━ SUPPORTS ━━━
// Runs within existing TX if present; runs non-transactionally if none.
// Use for: Read-only operations that can work both ways.
@Transactional(propagation = Propagation.SUPPORTS)

// ━━━ NOT_SUPPORTED ━━━
// Suspends any existing TX, runs without a transaction.
// Use for: Non-transactional legacy code that must not participate in TX.
@Transactional(propagation = Propagation.NOT_SUPPORTED)

// ━━━ NEVER ━━━
// Throws IllegalTransactionStateException if a TX exists.
// Use for: Methods that must NEVER run in a transaction (strict enforcement).
@Transactional(propagation = Propagation.NEVER)

// ━━━ MANDATORY ━━━
// Throws if NO existing transaction. Must be called within an active TX.
// Use for: Internal helper methods that should only be called from @Transactional methods.
@Transactional(propagation = Propagation.MANDATORY)
```

---

## 📖 12. Flush Modes — Deep Dive

```java
// FlushMode controls WHEN Hibernate sends pending SQL to the database.
// Flushing ≠ Committing. Flush = SQL sent to DB. Commit = DB confirms persistence.

// ━━━ FlushMode.AUTO (Default) ━━━
// Hibernate flushes before executing a query IF the query might be affected
// by pending (unflushed) changes in the session.

@Transactional(flushMode = FlushModeType.AUTO)
public void processAndQuery() {
    // pending change:
    product.setPrice(new BigDecimal("999")); // not yet flushed

    // Hibernate checks: "Does this query select from 'products'?"
    // YES → flushes first so the query sees the pending price change!
    List<Product> products = em.createQuery(
        "SELECT p FROM Product p WHERE p.price < 1000", Product.class
    ).getResultList(); // ← Hibernate auto-flushes before this!
}

// ━━━ FlushMode.COMMIT ━━━
// Only flushes at transaction commit. Faster for read-heavy operations.
// ⚠️ Risk: Queries within the TX may NOT see uncommitted pending changes!

@Transactional
public void readHeavy() {
    em.setFlushMode(FlushModeType.COMMIT); // Override for this session

    product.setPrice(new BigDecimal("999")); // changed but NOT flushed yet

    // This query does NOT see the price change (still shows old price from DB)!
    List<Product> products = em.createQuery(...).getResultList();

    // At commit → THEN price is flushed and saved.
    // Use COMMIT mode for: read-only-ish operations with many queries, batch reads
}

// ━━━ FlushMode.MANUAL ━━━
// Never auto-flushes. You control flush completely.
Session session = sessionFactory.openSession();
session.setHibernateFlushMode(FlushMode.MANUAL);
session.beginTransaction();

for (int i = 0; i < 10000; i++) {
    session.persist(new DataRecord(i));
    if (i % 200 == 0) {
        session.flush();  // Manually flush every 200 records
        session.clear();  // Clear L1 cache to keep memory low
    }
}
session.getTransaction().commit();

// ━━━ FlushMode.ALWAYS ━━━ (Hibernate-specific, not JPA standard)
// Flushes before EVERY query — even if the query doesn't touch those tables.
// Most aggressive, most expensive. Use only when you need absolute consistency
// for native SQL queries that Hibernate can't analyze.
```

---

## 📖 13. Pessimistic Locking — Deadlock Prevention

```java
// PESSIMISTIC_READ: Shared lock — others can read but NOT write
// PESSIMISTIC_WRITE: Exclusive lock — no other read OR write allowed

// ─── Deadlock scenario ───
// Thread 1: Locks Account A (write), then tries to lock Account B
// Thread 2: Locks Account B (write), then tries to lock Account A
// → DEADLOCK! Both wait for each other forever.

// ─── Prevention: Always acquire locks in the SAME ORDER ───
@Transactional(timeout = 5) // TX timeout = 5 seconds (auto-rollback if exceeded)
public void transfer(Long fromId, Long toId, BigDecimal amount) {
    // ALWAYS lock in ascending ID order — prevents deadlocks!
    Long firstId = Math.min(fromId, toId);
    Long secondId = Math.max(fromId, toId);

    Account first  = accountRepo.findByIdWithPessimisticLock(firstId);   // Lock first
    Account second = accountRepo.findByIdWithPessimisticLock(secondId);  // Then second

    Account from = fromId.equals(firstId) ? first : second;
    Account to   = toId.equals(firstId) ? first : second;

    from.debit(amount);
    to.credit(amount);
}

@Repository
public interface AccountRepository extends JpaRepository<Account, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)   // FOR UPDATE
    @Query("SELECT a FROM Account a WHERE a.id = :id")
    Account findByIdWithPessimisticLock(@Param("id") Long id);

    @Lock(LockModeType.PESSIMISTIC_READ)    // FOR SHARE / LOCK IN SHARE MODE
    @Query("SELECT a FROM Account a WHERE a.id = :id")
    Account findByIdWithSharedLock(@Param("id") Long id);
}

// Lock scope with timeout (PostgreSQL/Oracle):
@Lock(LockModeType.PESSIMISTIC_WRITE)
@QueryHints({
    @QueryHint(name = "javax.persistence.lock.timeout", value = "3000") // 3 second lock wait
})
Account findByIdWithLockTimeout(@Param("id") Long id);
// If lock not acquired within 3s → LockTimeoutException instead of waiting indefinitely!
```

---

# ═══════════════════════════════════════════════════
# 🌐 SECTION 5: Modern Ecosystem & Integration
# ═══════════════════════════════════════════════════

## 📖 14. JPA vs Native Hibernate — When to Use Each

### Hibernate-Specific Features (not in JPA standard):

```java
// ━━━ @Filter — Dynamic WHERE clause on queries ━━━
@Entity
@FilterDef(
    name = "activeFilter",
    parameters = @ParamDef(name = "isActive", type = Boolean.class)
)
@Filter(name = "activeFilter", condition = "active = :isActive")
public class User {
    private boolean active;
}

// Enable the filter per session:
Session session = entityManager.unwrap(Session.class);
session.enableFilter("activeFilter").setParameter("isActive", true);

// Now ALL queries on User automatically add: WHERE active = true
// Perfect for: Soft deletes, multi-tenant row-level filtering, draft vs published
List<User> activeUsers = userRepo.findAll(); // Automatically filtered!

// ━━━ @Immutable — Read-only entities (no dirty checking!) ━━━
@Entity
@Immutable // Hibernate never checks for dirty state → huge performance boost!
public class ExchangeRate {
    @Id private Long id;
    private String fromCurrency;
    private String toCurrency;
    private BigDecimal rate;
    private LocalDate date;
    // Exchange rates from external system — never updated via our app
}
// ✅ Skip dirty checking entirely for read-only reference data → performance win

// ━━━ @NaturalId — Business key lookup ━━━
@Entity
public class Employee {
    @Id @GeneratedValue private Long id; // Surrogate PK

    @NaturalId(mutable = false) // Business identifier
    @Column(unique = true, nullable = false)
    private String employeeNumber; // "EMP-2024-001"

    @NaturalId
    @Column(unique = true)
    private String email;
}

// Hibernate caches NaturalId → DB lookups for natural IDs use L2 cache!
session.byNaturalId(Employee.class)
       .using("employeeNumber", "EMP-2024-001")
       .load(); // Checks L2 cache first — no DB hit if cached!

// ━━━ @Where — Permanent WHERE on entity ━━━
@Entity
@Where(clause = "deleted_at IS NULL")  // Auto-appended to ALL queries on this entity
public class Product {
    private LocalDateTime deletedAt; // Soft-delete column
}
// SELECT * FROM products WHERE deleted_at IS NULL ← always added!
// Soft delete without changing any query code!
```

---

## 📖 15. Hibernate Envers — Audit Trail & History

```java
// Envers automatically records every change to an entity in audit tables.
// Perfect for: Banking, healthcare, legal, compliance systems.

// Step 1: Add dependency
// <dependency>
//   <groupId>org.hibernate.orm</groupId>
//   <artifactId>hibernate-envers</artifactId>
// </dependency>

// Step 2: Enable auditing
spring.jpa.properties.org.hibernate.envers.audit_table_suffix=_audit
spring.jpa.properties.org.hibernate.envers.store_data_at_delete=true
spring.jpa.properties.org.hibernate.envers.global_with_modified_flag=true

// Step 3: Annotate entities
@Entity
@Audited  // ← All changes tracked automatically!
public class BankAccount {
    @Id @GeneratedValue private Long id;
    private String accountNumber;
    private BigDecimal balance;

    @NotAudited // Exclude this field from audit
    private String tempNotes;
}

// Envers creates: bank_accounts_audit table with columns:
// id, account_number, balance, REV (revision id), REVTYPE (0=ADD, 1=MOD, 2=DEL)

// Step 4: Query audit history
@Service
public class AuditService {

    @Autowired
    private EntityManager entityManager;

    public List<Object[]> getAccountHistory(Long accountId) {
        AuditReader reader = AuditReaderFactory.get(entityManager);

        // Get all revisions for this account:
        return reader.createQuery()
            .forRevisionsOfEntity(BankAccount.class, false, true)
            .add(AuditEntity.id().eq(accountId))
            .add(AuditEntity.revisionType().eq(RevisionType.MOD)) // Only MODIFICATIONS
            .addOrder(AuditEntity.revisionNumber().asc())
            .getResultList();
        // Returns: List of [BankAccount state, RevisionEntity, RevisionType]
    }

    // Get snapshot at a specific revision:
    public BankAccount getBalanceAtRevision(Long accountId, int revisionNumber) {
        AuditReader reader = AuditReaderFactory.get(entityManager);
        return reader.find(BankAccount.class, accountId, revisionNumber);
    }

    // Get list of all revisions for an entity:
    public List<Number> getRevisions(Long accountId) {
        AuditReader reader = AuditReaderFactory.get(entityManager);
        return reader.getRevisions(BankAccount.class, accountId);
    }
}
```

---

## 📖 16. Multi-Tenancy in Hibernate

### Strategy 1: Separate Schema (Most Common in Enterprise)
```java
// Each tenant gets their own DB schema.
// All tables are identical — just in different schemas.
// E.g., tenant1.orders, tenant2.orders

// application.properties:
spring.jpa.properties.hibernate.multiTenancy=SCHEMA
spring.jpa.properties.hibernate.multi_tenant_connection_provider=com.example.SchemaConnectionProvider
spring.jpa.properties.hibernate.tenant_identifier_resolver=com.example.TenantIdentifierResolver

// TenantIdentifierResolver — extracts tenant from request:
@Component
public class TenantIdentifierResolver implements CurrentTenantIdentifierResolver {

    @Override
    public String resolveCurrentTenantIdentifier() {
        // Get tenant from ThreadLocal (set by filter/interceptor):
        return TenantContext.getCurrentTenant(); // e.g., "client_abc"
    }

    @Override
    public boolean validateExistingCurrentSessions() {
        return true;
    }
}

// HTTP filter to extract tenant from header/JWT:
@Component
public class TenantFilter implements Filter {
    @Override
    public void doFilter(ServletRequest req, ...) {
        String tenantId = ((HttpServletRequest) req).getHeader("X-Tenant-Id");
        TenantContext.setCurrentTenant(tenantId); // Store in ThreadLocal
        try {
            chain.doFilter(req, res);
        } finally {
            TenantContext.clear(); // IMPORTANT! Always clean ThreadLocal!
        }
    }
}

// SchemaConnectionProvider — switches DB schema on connection checkout:
@Component
public class SchemaConnectionProvider implements MultiTenantConnectionProvider {

    @Autowired
    private DataSource dataSource;

    @Override
    public Connection getConnection(String tenantIdentifier) throws SQLException {
        Connection conn = dataSource.getConnection();
        conn.createStatement()
            .execute("SET search_path = " + tenantIdentifier); // PostgreSQL schema switch
        return conn;
    }
}
```

### Strategy 2: Discriminator Column (Single DB, Single Schema)
```java
// All tenants in ONE table with a tenant_id discriminator column.
// Simplest approach — great for SaaS with many small tenants.

@Entity
@Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
@FilterDef(name = "tenantFilter",
           parameters = @ParamDef(name = "tenantId", type = String.class))
public class Order {
    @Id @GeneratedValue private Long id;

    @Column(name = "tenant_id", nullable = false, updatable = false)
    private String tenantId; // "client_abc"

    private BigDecimal total;
}

// Enable per tenant request in filter:
session.enableFilter("tenantFilter").setParameter("tenantId", tenantContext.getId());
// Now ALL Order queries automatically include: WHERE tenant_id = 'client_abc'

// ⚠️ Risk: If filter not enabled → ALL tenant data visible! Test this carefully.
// Critical: Always add tenant_id to unique constraints! e.g., (tenant_id, order_number)
```

---

# ═══════════════════════════════════════════════════
# 🔧 SECTION 6: Troubleshooting & Best Practices
# ═══════════════════════════════════════════════════

## 📖 17. Read-Only Optimization — Avoid Dirty Checking

```java
// For read-only operations: tell Hibernate to skip dirty checking entirely!

// Option 1: @Transactional(readOnly = true) — Spring
@Transactional(readOnly = true) // ← ALWAYS use for read-only service methods!
public List<OrderSummary> getOrderSummaries() {
    // Hibernate does NOT take snapshots of loaded entities → no dirty check at commit!
    // Spring also sets FlushMode.MANUAL (never flushes) when readOnly=true
    // Result: Faster queries, no unnecessary UPDATE statements
    return orderRepo.findAll().stream()
        .map(o -> new OrderSummary(o.getId(), o.getTotal()))
        .collect(Collectors.toList());
}

// Option 2: @Immutable on entity (permanent — applies to ALL queries)
@Entity
@Immutable
public class ProductCatalogView { ... }

// Option 3: Use DTO projections (no entity loading at all!)
// Best performance — no entity object created, no proxy, no dirty checking
public interface OrderSummaryProjection {
    Long getId();
    BigDecimal getTotal();
    String getStatus();
}

// In repository:
@Query("SELECT o.id as id, o.total as total, o.status as status FROM Order o")
List<OrderSummaryProjection> findAllSummaries(); // Interface-based projection!

// Hibernate generates: SELECT o.id, o.total, o.status FROM orders o
// (Only selected columns! Not SELECT * — bandwidth efficient!)
```

---

## 📖 18. LazyInitializationException — Advanced Patterns

```java
// SCENARIO 1: Standard Service → Controller flow
// BAD pattern:
@Transactional
public Order getOrder(Long id) {
    return orderRepo.findById(id).orElseThrow(); // Session closes here
}
// In controller: order.getItems() → 💥 LazyInitializationException

// ─── Fix A: DTO projection at query level (BEST approach) ───
public record OrderDetailDTO(Long id, BigDecimal total, List<ItemDTO> items) {}

@Transactional(readOnly = true)
public OrderDetailDTO getOrderDetail(Long id) {
    Order order = orderRepo.findById(id).orElseThrow();
    // Map inside @Transactional while session is open:
    return new OrderDetailDTO(
        order.getId(),
        order.getTotal(),
        order.getItems().stream() // ← Items loaded HERE while session still open
             .map(i -> new ItemDTO(i.getProductName(), i.getQuantity(), i.getPrice()))
             .collect(Collectors.toList())
    );
    // Returns a plain Java record — NO Hibernate entity, NO proxy, NO session needed!
}

// ─── Fix B: Named JPQL with new DTO syntax ───
@Query("""
    SELECT new com.example.dto.OrderDetailDTO(
        o.id, o.total, o.status, o.createdAt
    )
    FROM Order o WHERE o.id = :id
""")
Optional<OrderDetailDTO> findDtoById(@Param("id") Long id);
// Hibernate constructs DTO directly in SQL — NO entity loaded at all!

// ─── Fix C: Hibernate.initialize() ───
@Transactional(readOnly = true)
public Order getOrderInitialized(Long id) {
    Order order = orderRepo.findById(id).orElseThrow();
    Hibernate.initialize(order.getItems()); // Force load collection in session
    return order; // Now items are initialized — no proxy anymore!
}
```

---

## 📖 19. Spring Hibernate Integration Internals

### How LocalEntityManagerFactoryBean Works:
```java
// Spring's JPA integration uses LocalContainerEntityManagerFactoryBean to:
// 1. Create EntityManagerFactory (wraps Hibernate's SessionFactory)
// 2. Integrate with Spring's transaction manager
// 3. Enable @PersistenceContext injection

@Configuration
@EnableTransactionManagement  // Enables @Transactional processing
public class JpaConfig {

    @Bean
    public LocalContainerEntityManagerFactoryBean entityManagerFactory(DataSource dataSource) {
        LocalContainerEntityManagerFactoryBean emf = new LocalContainerEntityManagerFactoryBean();
        emf.setDataSource(dataSource);
        emf.setPackagesToScan("com.example.entity"); // Scan for @Entity classes

        HibernateJpaVendorAdapter adapter = new HibernateJpaVendorAdapter();
        adapter.setGenerateDdl(false); // Never auto-generate DDL in production!
        emf.setJpaVendorAdapter(adapter);

        Map<String, Object> props = new HashMap<>();
        props.put("hibernate.dialect", "org.hibernate.dialect.PostgreSQLDialect");
        props.put("hibernate.show_sql", "false"); // Never true in production!
        props.put("hibernate.format_sql", "true");
        props.put("hibernate.jdbc.batch_size", "50");
        props.put("hibernate.order_inserts", "true");
        props.put("hibernate.order_updates", "true");
        props.put("hibernate.connection.provider_disables_autocommit", "true"); // CRITICAL for perf!
        emf.setJpaPropertyMap(props);

        return emf;
    }

    @Bean
    public PlatformTransactionManager transactionManager(EntityManagerFactory emf) {
        return new JpaTransactionManager(emf);
        // Alternatively for multi-DB: ChainedTransactionManager (soft TX across DBs)
    }
}
```

### How @Transactional Works Internally — Full Flow:
```
1. Spring scans classes at startup → finds @Transactional → creates CGLIB/JDK proxy
2. HTTP request → controller → proxy.serviceMethod()
3. TransactionInterceptor.invoke() called:
   a. TransactionManager.getTransaction(definition) → creates/joins TX
   b. Opens Hibernate Session, binds to thread-local TransactionSynchronizationManager
4. Your actual service code runs
5. Hibernate operations use the SAME session (from TransactionSynchronizationManager)
6. On method return: TransactionInterceptor.commitTransactionAfterReturning()
   a. Session.flush() → all pending SQL sent to DB
   b. Connection.commit() → DB writes committed, WAL written
   c. Session.close() → L1 cache cleared, connection returned to HikariCP pool
7. On exception: rollbackTransactionAfterThrowing() → Connection.rollback()
```

---

## 🎯 Advanced Cross-Questioning — Full Interview Scenarios

**Q: "You have a method with @Transactional(propagation = REQUIRES_NEW) called from another @Transactional method. The outer method rolls back. Does the inner method also roll back?"**
> **Answer:** "No — this is the key feature of `REQUIRES_NEW`. It:
> 1. **Suspends** the outer transaction
> 2. Creates a **completely independent** new transaction
> 3. Inner transaction commits/rolls back independently of the outer one
>
> If the inner method succeeds → it commits its own TX before returning. If the outer method then throws → ONLY the outer TX rolls back. The inner TX is already committed and **permanent**.
>
> Real use case: Audit logging with `REQUIRES_NEW` — even if the business TX rolls back, the audit log entry is committed forever. This is critical for financial systems where audit trails must be 100% complete."

---

**Q: "SINGLE_TABLE inheritance forces nullable columns. But your DBA says all columns must be NOT NULL. How do you satisfy both?"**
> **Answer:** "This is a real tension. We have 3 options:
>
> **Option 1:** Switch to `JOINED` strategy — each subtype gets its own table, so subtype-specific columns can be NOT NULL in their table. Trade-off: JOIN on every query.
>
> **Option 2:** Keep SINGLE_TABLE but use database-level CHECK constraints (not JPA constraints) to enforce that certain columns are NOT NULL only when the discriminator is a specific value:
> ```sql
> ALTER TABLE payments ADD CONSTRAINT chk_credit_card
>   CHECK (payment_type != 'CREDIT_CARD' OR card_number IS NOT NULL);
> ```
> This enforces the business rule at DB level while keeping the single table. But it's DB-specific syntax and harder to manage.
>
> **Option 3:** Use application-level validation with `@Validated` and `@Valid` on the subtype before persisting. The DB allows nulls but the application guarantees non-null through bean validation.
>
> My recommendation: For strict data integrity, use JOINED. For performance and flexibility, use SINGLE_TABLE with application validation."

---

**Q: "In Hibernate Envers, how do you track WHO made a change — the username of the logged-in user?"**
> **Answer:** "Envers supports this through a `@RevisionEntity` — a custom revision entity that you enhance with extra fields:
>
> ```java
> @RevisionEntity(AuditRevisionListener.class)
> @Entity
> public class AuditRevision extends DefaultRevisionEntity {
>     @Column(name = 'modified_by')
>     private String modifiedBy;  // Username
>
>     @Column(name = 'ip_address')
>     private String ipAddress;
> }
>
> // Listener — called for every new revision:
> public class AuditRevisionListener implements RevisionListener {
>     @Override
>     public void newRevision(Object revisionEntity) {
>         AuditRevision rev = (AuditRevision) revisionEntity;
>         // Get username from Spring Security:
>         String username = SecurityContextHolder.getContext()
>                              .getAuthentication().getName();
>         rev.setModifiedBy(username);
>     }
> }
> ```
>
> Now every audit record includes `modified_by = 'john.smith'`. This pattern is used in banking for full-compliance audit trails showing WHAT changed, WHEN, and WHO changed it."

---

**Q: "'hibernate.connection.provider_disables_autocommit=true' — what does this do and why is it important for performance?"**
> **Answer:** "By default, JDBC connections in HikariCP have `autocommit=true`. This means every SQL statement is implicitly committed. When Spring opens a `@Transactional` context, it calls `connection.setAutoCommit(false)` before the TX starts — this is a round-trip to the DB!
>
> When you set `hibernate.connection.provider_disables_autocommit=true`, you're telling Hibernate that HikariCP handles autocommit=false at the pool level. HikariCP can be configured with `spring.datasource.hikari.auto-commit=false`. This means:
> - No `setAutoCommit(false)` call needed at TX start → saves 1 DB round-trip per transaction
> - For high-throughput apps (1000+ TPS) this can save thousands of round-trips per second
>
> It's a low-level optimization but Vladimir Mihalcea (Hibernate contributor) specifically calls it out as one of the highest-ROI Hibernate performance optimizations. Always set it in production with HikariCP."

