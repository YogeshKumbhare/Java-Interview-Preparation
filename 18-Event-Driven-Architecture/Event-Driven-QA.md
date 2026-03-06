# 📡 Event-Driven Architecture — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Event-Driven Architecture (EDA)?

**Event-Driven Architecture** is a software design pattern where the flow of the program is determined by **events** — significant changes in state. Instead of services directly calling each other (request-response), they communicate by **producing and consuming events**.

**Analogy:** Instead of a manager walking to each employee's desk telling them what to do (synchronous), the manager posts announcements on a bulletin board (events). Interested employees check the board and act accordingly (asynchronous).

### Synchronous vs Event-Driven:
```
Synchronous (REST):
  Order Service → (HTTP POST) → Payment Service → (HTTP POST) → Inventory Service
  Problem: If Inventory Service is down → entire chain fails!
  Problem: Order Service waits for ALL services to respond (slow)

Event-Driven:
  Order Service → publishes "OrderCreated" event to Kafka
  Payment Service → subscribes, processes payment, publishes "PaymentCompleted"
  Inventory Service → subscribes, reserves stock → publishes "StockReserved"
  Each service is INDEPENDENT — if one is down, events wait in queue
```

### Benefits:
- **Loose coupling** — services don't know about each other
- **Scalability** — each service scales independently
- **Resilience** — services can fail and recover without losing events
- **Audit trail** — every event is a record of what happened

### Drawbacks:
- **Complexity** — harder to trace the flow (distributed tracing needed)
- **Eventual consistency** — data is not immediately consistent
- **Debugging** — harder to reproduce issues
- **Event ordering** — ensuring correct order across partitions

---

## 📖 CQRS — Command Query Responsibility Segregation

### Theory:
**CQRS** separates the **write model** (commands) from the **read model** (queries) into different services, potentially using different databases optimized for each purpose.

**Why?** Because reads and writes have fundamentally different requirements:
- **Writes** need ACID transactions, data validation, business rules
- **Reads** need fast queries, denormalized data, complex filtering

```
Traditional (single model):
┌─────────────────────────┐
│     OrderService        │
│  - createOrder()  (W)   │
│  - getOrder()     (R)   │
│  - searchOrders() (R)   │
│  - cancelOrder()  (W)   │
│         ↕                │
│    PostgreSQL           │
│  (normalized tables)    │
└─────────────────────────┘
Problem: Complex search queries slow down writes (shared DB)
Problem: Normalized schema = expensive JOINs for reads

CQRS:
┌──────────────────┐         ┌──────────────────┐
│  Command Service │         │  Query Service    │
│  createOrder()   │         │  getOrder()       │
│  cancelOrder()   │         │  searchOrders()   │
│       ↕          │         │       ↕           │
│  PostgreSQL      │ ─events→│  Elasticsearch    │
│  (normalized)    │ (Kafka) │  (denormalized)   │
│  ACID writes     │         │  Fast reads       │
└──────────────────┘         └──────────────────┘
```

### Implementation:
```java
// ═══ COMMAND SIDE ═══
@Service
@Transactional
public class OrderCommandService {

    public OrderId createOrder(CreateOrderCommand cmd) {
        // Validation
        if (cmd.getItems().isEmpty()) throw new ValidationException("No items");

        // Business logic → save to write DB (PostgreSQL)
        Order order = Order.create(cmd);
        orderRepository.save(order);

        // Publish event → syncs read model
        eventPublisher.publish(new OrderCreatedEvent(
            order.getId(),
            order.getUserId(),
            order.getItems(),
            order.getTotal(),
            order.getStatus(),
            Instant.now()
        ));

        return order.getId();
    }

    public void cancelOrder(String orderId) {
        Order order = orderRepository.findById(orderId).orElseThrow();
        order.cancel(); // Business rules: can only cancel if PENDING
        orderRepository.save(order);

        eventPublisher.publish(new OrderCancelledEvent(orderId, Instant.now()));
    }
}

// ═══ QUERY SIDE ═══
@Service
@Transactional(readOnly = true)
public class OrderQueryService {

    private final ElasticsearchOperations es;

    public OrderView getOrder(String orderId) {
        return orderReadRepository.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
    }

    public Page<OrderSummary> searchOrders(OrderSearchCriteria criteria, Pageable pageable) {
        // Complex search on Elasticsearch — fast and flexible
        NativeQuery query = NativeQuery.builder()
            .withQuery(q -> q.bool(b -> {
                if (criteria.getUserId() != null)
                    b.must(m -> m.term(t -> t.field("userId").value(criteria.getUserId())));
                if (criteria.getStatus() != null)
                    b.must(m -> m.term(t -> t.field("status").value(criteria.getStatus())));
                if (criteria.getMinAmount() != null)
                    b.must(m -> m.range(r -> r.field("total").gte(JsonData.of(criteria.getMinAmount()))));
                return b;
            }))
            .withPageable(pageable)
            .build();
        return es.search(query, OrderSummary.class);
    }
}

// ═══ EVENT HANDLER: Syncs command → query ═══
@Service
public class OrderEventHandler {

    @KafkaListener(topics = "order-events")
    @Transactional
    public void handle(OrderEvent event) {
        switch (event) {
            case OrderCreatedEvent e -> {
                OrderView view = new OrderView();
                view.setId(e.getOrderId());
                view.setUserId(e.getUserId());
                view.setItems(e.getItems());
                view.setTotal(e.getTotal());
                view.setStatus("CREATED");
                view.setCreatedAt(e.getTimestamp());
                orderReadRepository.save(view); // Save to Elasticsearch
            }
            case OrderCancelledEvent e -> {
                orderReadRepository.updateStatus(e.getOrderId(), "CANCELLED");
            }
        }
    }
}
```

---

## 📖 Event Sourcing — Store Every State Change

### Theory:
Instead of storing only the **current state** of an entity, **Event Sourcing** stores the **complete sequence of events** that led to the current state. The current state is derived by **replaying** all events.

**Analogy:** A bank statement. The current balance is not stored directly — it's calculated by replaying all deposits and withdrawals from the beginning.

```
Traditional (state-based):
  Account: { id: 1, balance: 1000 }
  → You know the current balance but NOT how it got there

Event Sourcing (event-based):
  Event 1: AccountCreated(id=1, initialBalance=0)
  Event 2: MoneyDeposited(id=1, amount=500)
  Event 3: MoneyDeposited(id=1, amount=700)
  Event 4: MoneyWithdrawn(id=1, amount=200)
  → Current balance = 0 + 500 + 700 - 200 = 1000
  → You know EVERY change and can audit the full history
```

### Implementation:
```java
// Events (immutable records)
public sealed interface AccountEvent {
    record AccountCreated(String accountId, String owner, Instant at) implements AccountEvent {}
    record MoneyDeposited(String accountId, BigDecimal amount, String source, Instant at) implements AccountEvent {}
    record MoneyWithdrawn(String accountId, BigDecimal amount, String reason, Instant at) implements AccountEvent {}
}

// Aggregate — rebuilds state from events
public class BankAccount {
    private String accountId;
    private BigDecimal balance = BigDecimal.ZERO;
    private String status = "ACTIVE";
    private final List<AccountEvent> uncommittedEvents = new ArrayList<>();

    // Rebuild from event history
    public static BankAccount fromEvents(List<AccountEvent> eventHistory) {
        BankAccount account = new BankAccount();
        for (AccountEvent event : eventHistory) {
            account.apply(event); // Replay each event
        }
        return account;
    }

    // Command: deposit money
    public void deposit(BigDecimal amount, String source) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0) throw new IllegalArgumentException();
        MoneyDeposited event = new MoneyDeposited(accountId, amount, source, Instant.now());
        apply(event);
        uncommittedEvents.add(event); // Queued for persistence
    }

    // Command: withdraw money
    public void withdraw(BigDecimal amount, String reason) {
        if (amount.compareTo(balance) > 0) throw new InsufficientFundsException();
        MoneyWithdrawn event = new MoneyWithdrawn(accountId, amount, reason, Instant.now());
        apply(event);
        uncommittedEvents.add(event);
    }

    // Apply event to state (used for both replay and new events)
    private void apply(AccountEvent event) {
        switch (event) {
            case AccountCreated e -> { this.accountId = e.accountId(); this.balance = BigDecimal.ZERO; }
            case MoneyDeposited e -> { this.balance = this.balance.add(e.amount()); }
            case MoneyWithdrawn e -> { this.balance = this.balance.subtract(e.amount()); }
        }
    }
}

// Event Store
@Repository
public class EventStore {
    public void save(String aggregateId, List<AccountEvent> events) {
        for (AccountEvent event : events) {
            eventTable.insert(aggregateId, event.getClass().getSimpleName(),
                objectMapper.writeValueAsString(event), Instant.now());
        }
    }

    public List<AccountEvent> getEvents(String aggregateId) {
        return eventTable.findByAggregateIdOrderBySequence(aggregateId)
            .stream()
            .map(row -> deserialize(row.getEventType(), row.getPayload()))
            .collect(Collectors.toList());
    }
}
```

---

## 📖 Saga Pattern — Distributed Transaction Alternative

### Theory:
The Saga pattern manages **distributed transactions** across microservices WITHOUT using 2PC. It breaks a transaction into **local transactions**, each publishing an event that triggers the next step. If any step fails, **compensating transactions** undo previous steps.

### Two approaches:

### 1. Choreography (event-based, no central coordinator):
```
Order Service → publishes OrderCreated
    ↓
Payment Service → listens → charges card → publishes PaymentCompleted
    ↓
Inventory Service → listens → reserves stock → publishes StockReserved
    ↓
Order Service → listens → marks order CONFIRMED

FAILURE:
Payment Service → charge fails → publishes PaymentFailed
    ↓
Order Service → listens → marks order CANCELLED (compensating action)
```

### 2. Orchestration (central Saga coordinator):
```java
@Service
public class OrderSagaOrchestrator {

    public void createOrderSaga(CreateOrderCommand cmd) {
        // Step 1: Create order
        OrderId orderId = orderService.createPendingOrder(cmd);

        try {
            // Step 2: Reserve payment
            paymentService.reserve(orderId, cmd.getAmount());

            // Step 3: Reserve inventory
            inventoryService.reserve(orderId, cmd.getItems());

            // Step 4: Confirm order
            orderService.confirmOrder(orderId);

        } catch (PaymentReservationException ex) {
            // Compensate Step 1
            orderService.cancelOrder(orderId);
            throw new OrderCreationFailedException("Payment failed", ex);

        } catch (InventoryReservationException ex) {
            // Compensate Step 2 + Step 1
            paymentService.cancelReservation(orderId);
            orderService.cancelOrder(orderId);
            throw new OrderCreationFailedException("Inventory not available", ex);
        }
    }
}
```

---

## 📖 Outbox Pattern — Reliable Event Publishing

### 📖 Theory (Deep Dive):

#### The Dual-Write Problem:
In a microservices architecture, a very common requirement is: **save data to the database AND publish an event to Kafka/RabbitMQ**. This sounds simple, but it has a fatal flaw — there is no way to make a database write and a Kafka write **atomic** in a single transaction. They are independent systems.

```
❌ PROBLEM 1: DB succeeds, Kafka fails
--------------------------------------------
1. orderRepo.save(order);      ✅ DB committed
2. kafkaTemplate.send(event);  ❌ Kafka broker unavailable
→ Order exists in DB, but NO event → Payment/Inventory services never notified
→ Order is stuck forever in PENDING state

❌ PROBLEM 2: Kafka succeeds, DB rolls back
--------------------------------------------
1. kafkaTemplate.send(event);  ✅ Event published to Kafka
2. orderRepo.save(order);      ❌ DB constraint violation → transaction rolls back
→ Event published, but NO order in DB → downstream services try to process a ghost order

❌ PROBLEM 3: App crashes between the two writes
-------------------------------------------------
→ No recovery mechanism. The state is split between the two systems.
```

#### How the Outbox Pattern Solves This:
Write the event to an **OUTBOX table** in the **same database** as the business data, **in the same transaction**. This reduces two unreliable writes to **one reliable DB write**. A separate background process then reads the outbox and publishes to Kafka.

```
✅ SOLUTION: Transactional Outbox
┌─────────────────────────────────────┐
│         Single DB Transaction        │
│  INSERT INTO orders VALUES (...)     │ ← Business data
│  INSERT INTO outbox VALUES (...)     │ ← Event stored atomically
└─────────────────────────────────────┘
            ↓ Later (async)
┌─────────────────────────────────────┐
│        Outbox Relay / Poller        │
│  SELECT * FROM outbox               │
│  WHERE published = false            │
│  → kafkaTemplate.send(event)        │
│  → UPDATE outbox SET published=true │
└─────────────────────────────────────┘

Key guarantee: Event is NEVER lost. At worst, it's delivered TWICE (at-least-once).
Consumer must be IDEMPOTENT to handle duplicate delivery.
```

---

### Full Implementation:

#### Step 1: Outbox Entity (DB Table)
```java
@Entity
@Table(name = "outbox_events",
    indexes = {
        @Index(name = "idx_outbox_published", columnList = "published, createdAt"), // Query index
        @Index(name = "idx_outbox_aggregate", columnList = "aggregateType, aggregateId")
    }
)
@Data
public class OutboxEvent {
    @Id
    @GeneratedValue
    private UUID id;                   // UUID for idempotency key on the consumer side

    @Column(nullable = false)
    private String aggregateType;      // e.g., "Order", "Payment"

    @Column(nullable = false)
    private String aggregateId;        // e.g., "order-uuid-123" (used as Kafka partition key!)

    @Column(nullable = false)
    private String eventType;          // e.g., "ORDER_CREATED", "PAYMENT_FAILED"

    @Column(columnDefinition = "jsonb", nullable = false)
    private String payload;            // Full event body as JSON

    @Column(nullable = false)
    private Instant createdAt = Instant.now();

    @Column(nullable = false)
    private boolean published = false; // Has this been sent to Kafka?

    private Instant publishedAt;       // When was it published? (for auditing)

    private int retryCount = 0;        // How many times has publishing been attempted?

    private String lastError;          // Last error message (for debugging stuck events)
}
```

#### Step 2: Service — Save Order + Outbox in ONE Transaction
```java
@Service
@RequiredArgsConstructor
@Slf4j
public class OrderCommandService {
    private final OrderRepository orderRepo;
    private final OutboxEventRepository outboxRepo;
    private final ObjectMapper objectMapper;

    @Transactional // Single DB transaction — BOTH order and outbox saved atomically
    public OrderId createOrder(CreateOrderCommand cmd) {
        // Business logic
        Order order = Order.create(cmd);
        orderRepo.save(order);

        // Write event to OUTBOX (same transaction, same DB)
        OutboxEvent event = new OutboxEvent();
        event.setAggregateType("Order");
        event.setAggregateId(order.getId().toString()); // Kafka partition key
        event.setEventType("ORDER_CREATED");
        event.setPayload(toJson(new OrderCreatedEvent(
            order.getId(), order.getUserId(), order.getTotal(), Instant.now()
        )));
        outboxRepo.save(event);

        // Note: NO kafkaTemplate.send() here!
        // If DB commits → both order AND event are persisted. ✅
        // If DB rolls back → neither is persisted. ✅
        // Kafka failure → handled by the async relay. ✅

        return order.getId();
    }

    private String toJson(Object obj) {
        try { return objectMapper.writeValueAsString(obj); }
        catch (JsonProcessingException e) { throw new RuntimeException(e); }
    }
}
```

#### Step 3: Outbox Relay — Polls DB and Publishes to Kafka
```java
@Component
@RequiredArgsConstructor
@Slf4j
public class OutboxRelay {
    private final OutboxEventRepository outboxRepo;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final OutboxEventRepository outboxEventRepository;

    @Scheduled(fixedDelay = 500) // Poll every 500ms — tune based on acceptable latency
    @Transactional
    public void publishPendingEvents() {
        // Fetch batch of unpublished events (ORDER BY createdAt to maintain order per aggregate)
        List<OutboxEvent> pendingEvents = outboxRepo
            .findTop100ByPublishedFalseOrderByCreatedAtAsc(); // Batch of 100 max

        for (OutboxEvent event : pendingEvents) {
            try {
                String topic = event.getAggregateType().toLowerCase() + "-events"; // "order-events"
                String key = event.getAggregateId(); // Ensures ordering per aggregate in Kafka

                // Synchronous send with timeout — ensures we get Kafka ack before marking published
                kafkaTemplate.send(topic, key, event.getPayload())
                    .get(5, TimeUnit.SECONDS); // Wait for broker ack (RecordMetadata)

                event.setPublished(true);
                event.setPublishedAt(Instant.now());
                outboxRepo.save(event);

            } catch (Exception ex) {
                event.setRetryCount(event.getRetryCount() + 1);
                event.setLastError(ex.getMessage());
                outboxRepo.save(event);

                log.error("Failed to publish outbox event id={} type={} retry={}",
                    event.getId(), event.getEventType(), event.getRetryCount(), ex);

                // ⚠️ After max retries, alert ops — don't silently drop
                if (event.getRetryCount() >= 10) {
                    alertService.critical("Outbox event stuck: " + event.getId());
                }
            }
        }
    }
}
```

---

### Alternative: Debezium CDC (Change Data Capture) — Production Best Practice
```
Problem with polling relay:
  - It polls the DB every 500ms → additional DB load
  - If two relay instances run simultaneously → duplicate publishes (needs distributed lock)
  - Published flag update = extra write per event

Better approach: Debezium watches the PostgreSQL WAL (Write-Ahead Log)
  → Any INSERT into the outbox table is automatically streamed to Kafka
  → No polling! Near real-time (milliseconds latency)
  → No published flag needed (Debezium tracks its own offset in Kafka)

Architecture with Debezium:
┌─────────────┐    INSERT        ┌──────────────┐
│  App Service│ ──outbox_events──▶  PostgreSQL   │
└─────────────┘                  │  (WAL enabled)│
                                 └──────┬────────┘
                                        │ CDC (WAL)
                                 ┌──────▼────────┐
                                 │   Debezium    │  (Kafka Connect Connector)
                                 │   Connector   │
                                 └──────┬────────┘
                                        │ publishes
                                 ┌──────▼────────┐
                                 │     Kafka     │
                                 └───────────────┘

Debezium config (application.properties style):
  connector.class=io.debezium.connector.postgresql.PostgresConnector
  database.hostname=localhost
  database.port=5432
  database.dbname=ordersdb
  table.include.list=public.outbox_events  ← Only watch this table
  transforms=outbox
  transforms.outbox.type=io.debezium.transforms.outbox.EventRouter
  transforms.outbox.table.field.event.type=eventType
  transforms.outbox.route.by.field=aggregateType  ← Route to "order-events" topic
```

---

### Outbox Pattern — Summary Table

| Concern | Polling Relay | Debezium CDC |
|---------|--------------|--------------|
| **Latency** | ~500ms (configurable) | ~50ms (near real-time) |
| **DB Load** | Polling adds queries | Reads WAL (minimal overhead) |
| **Operational complexity** | Low (just a @Scheduled bean) | High (Kafka Connect, Debezium setup) |
| **Duplicate risk** | Yes (need idempotency) | Yes (at-least-once — need idempotency) |
| **Published flag** | Required | Not needed |
| **Best for** | Smaller systems, getting started | High-throughput production systems |

---

### 🎯 Cross-Questioning Scenarios

**Q: "Your Outbox Relay runs in multiple instances behind a load balancer. Two instances pick up the same unpublished event simultaneously and both publish it to Kafka. How do you prevent duplicate events?"**
> **Answer:** "This is an important concern. Three solutions:
>
> **1. Optimistic locking in the relay:** Add a `@Version` field to the `OutboxEvent` entity. The second instance's UPDATE (setting `published=true`) will throw `OptimisticLockingFailureException` — it sees the version was already incremented by the first instance. The second instance skips this event gracefully.
>
> **2. SELECT FOR UPDATE SKIP LOCKED (Pessimistic):** The relay query uses `SELECT ... FOR UPDATE SKIP LOCKED`. This atomically locks rows being processed — other instances skip locked rows entirely, preventing double-pickup.
>
> ```java
> @Query(value = "SELECT * FROM outbox_events WHERE published = false " +
>                "ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED", nativeQuery = true)
> List<OutboxEvent> findAndLockPendingEvents();
> ```
>
> **3. Use Debezium:** As a single Kafka Connect connector reading the WAL, Debezium is inherently single-writer — no race condition possible.
>
> In all cases, the Kafka consumer must also be idempotent (use the event's UUID as an idempotency key in Redis or a deduplicated DB table) since at-least-once delivery means duplicates can still arrive even with the DB lock approach."

---

**Q: "The `published` flag approach means the outbox table grows forever. How do you handle cleanup?"**
> **Answer:** "We add a cleanup job that deletes events older than N days where `published = true`. We run this as a separate `@Scheduled` job in off-peak hours (e.g., 2 AM) with small batch deletes to avoid locking the table:
>
> ```java
> @Scheduled(cron = "0 0 2 * * *") // 2 AM daily
> @Transactional
> public void cleanupPublishedEvents() {
>     Instant cutoff = Instant.now().minus(30, ChronoUnit.DAYS);
>     int deleted;
>     do {
>         // Delete in small batches to avoid long-running transactions
>         deleted = outboxRepo.deletePublishedBefore(cutoff, PageRequest.of(0, 1000));
>     } while (deleted == 1000);
> }
> ```
>
> For very high-throughput systems, we'd use table partitioning by `created_at` in PostgreSQL — dropping an entire month's partition is near-instant (DDL) vs. deleting millions of rows (which takes hours and generates WAL pressure)."

---

**Q: "How is the Outbox Pattern different from Event Sourcing? When would you use each?"**
> **Answer:** "They solve different problems and are often used together:
>
> - **Outbox Pattern** solves the **reliability** problem: 'How do I guarantee that my event reaches Kafka after my DB write?' It's about delivery guarantees. The outbox is a temporary staging area — events are deleted after publication.
>
> - **Event Sourcing** solves the **state storage** problem: 'Instead of storing current state, I store the full history of events that produced that state.' Events are NEVER deleted — they are the source of truth.
>
> They combine naturally: In an Event Sourcing system, when you persist a new event to the Event Store, you also write it to the Outbox table in the same transaction. The Outbox relay then publishes it to Kafka for other services to consume. This way you get: full audit history (Event Sourcing) + guaranteed event delivery (Outbox) + decoupled downstream services (Kafka)."

