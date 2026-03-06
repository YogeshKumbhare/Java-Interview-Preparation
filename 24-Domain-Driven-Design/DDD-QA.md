# 🏛️ Domain-Driven Design (DDD) — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Domain-Driven Design?

**Domain-Driven Design (DDD)** is a software design approach coined by Eric Evans in his 2003 book. It focuses on creating software that deeply reflects the **business domain** (the problem space). Instead of designing around technical concerns (database tables, REST endpoints), you design around **business concepts**.

**Why DDD matters for seniors:** When a system grows beyond 10 services, without DDD, you get a **Big Ball of Mud** — services are tightly coupled, boundaries are wrong, and every change requires coordinating 5 teams. DDD gives you tools to define clean boundaries.

### DDD Building Blocks:

```
STRATEGIC DDD (high-level, system design):
├── Bounded Context — boundary where a model applies
├── Ubiquitous Language — shared vocabulary between devs and business
├── Context Map — how bounded contexts relate to each other
└── Subdomains — Core, Supporting, Generic

TACTICAL DDD (low-level, code design):
├── Entity — object with identity
├── Value Object — object defined by attributes (no identity)
├── Aggregate — cluster of entities with consistency rules
├── Aggregate Root — the entry point to an aggregate
├── Repository — data access abstraction
├── Domain Service — logic that doesn't belong to single entity
├── Domain Event — something that happened in the domain
└── Factory — complex object creation
```

---

## 📖 Bounded Context — The Most Important DDD Concept

### Theory:
A **Bounded Context** is a **clear boundary** within which a specific domain model is defined and applicable. The same real-world concept can have **different meanings** in different contexts.

```
Example: "Account"

Banking Context:
  Account = { accountNumber, balance, overdraftLimit, transactions[] }
  Operations: deposit(), withdraw(), transfer()

Authentication Context:
  Account = { username, passwordHash, roles[], lastLogin }
  Operations: login(), changePassword(), enable2FA()

Marketing Context:
  Account = { email, preferences, communicationOptIn }
  Operations: subscribe(), unsubscribe(), sendPromotion()

Each context has its OWN "Account" model!
They are NOT the same entity. Don't try to create ONE Account class for all!
```

### Context Map:
```
┌─────────────────────┐        ┌─────────────────────┐
│   ORDER CONTEXT     │        │  PAYMENT CONTEXT     │
│                     │        │                      │
│  Order              │        │  Payment             │
│  OrderItem          │ ─────→ │  Transaction         │
│  OrderService       │ Events │  PaymentGateway      │
│                     │ (Kafka)│                      │
│  Ubiquitous Lang:   │        │  Ubiquitous Lang:    │
│  "Place order"      │        │  "Process payment"   │
│  "Cancel order"     │        │  "Refund"            │
└─────────────────────┘        └─────────────────────┘
         │
         │ REST API
         ↓
┌─────────────────────┐
│  INVENTORY CONTEXT  │
│                     │
│  Product            │
│  StockLevel         │
│  Warehouse          │
│                     │
│  Ubiquitous Lang:   │
│  "Reserve stock"    │
│  "Restock"          │
└─────────────────────┘
```

---

## 📖 Entity vs Value Object

### Theory:
**Entity**: An object with a **unique identity** that persists over time. Even if all its attributes change, it's still the same entity. Example: A person changes their name, address, phone — but they're still the same person (identified by SSN or ID).

**Value Object**: An object defined entirely by its **attributes**. Two value objects with the same attributes are considered equal. They have **no identity**. Example: Money — $100 USD is the same as another $100 USD. Address — "123 Main St" is the same as another "123 Main St".

```java
// ═══ ENTITY — has identity, mutable ═══
@Entity
public class Customer {
    @Id   // IDENTITY — this makes it an Entity
    @GeneratedValue(strategy = GenerationType.UUID)
    private String customerId;

    private String name;         // Can change
    private String email;        // Can change
    private String phone;        // Can change

    // Two customers with same name/email are NOT the same customer!
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Customer c)) return false;
        return customerId.equals(c.customerId); // Compare by ID, not attributes
    }

    @Override
    public int hashCode() {
        return Objects.hash(customerId);
    }
}

// ═══ VALUE OBJECT — no identity, immutable ═══
@Embeddable
public record Money(BigDecimal amount, Currency currency) {
    // Compact constructor for validation
    public Money {
        Objects.requireNonNull(amount, "Amount required");
        Objects.requireNonNull(currency, "Currency required");
        if (amount.scale() > 2) throw new IllegalArgumentException("Max 2 decimal places");
    }

    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new CurrencyMismatchException(this.currency, other.currency);
        }
        return new Money(this.amount.add(other.amount), this.currency); // Returns NEW object!
    }

    public Money subtract(Money other) {
        if (this.amount.compareTo(other.amount) < 0) {
            throw new InsufficientFundsException();
        }
        return new Money(this.amount.subtract(other.amount), this.currency);
    }
    // equals() and hashCode() auto-generated by record — compares ALL fields
}

@Embeddable
public record Address(
    String street,
    String city,
    String state,
    String zipCode,
    String country
) {
    // Two addresses with same fields ARE the same address
    // No ID needed
}
```

---

## 📖 Aggregate — The Consistency Boundary

### Theory:
An **Aggregate** is a cluster of **related entities and value objects** that are treated as a **single unit** for data changes. Every aggregate has an **Aggregate Root** — the only entity through which external code can access the aggregate.

**Rules of Aggregates:**
1. Only the Aggregate Root is referenced from outside
2. All changes go through the Aggregate Root (it enforces business rules)
3. One transaction = one aggregate (don't modify two aggregates in one transaction)
4. Reference other aggregates by ID, not by direct object reference

```java
// ═══ ORDER AGGREGATE ═══
// Order is the Aggregate Root
// OrderItem and ShippingAddress are part of the aggregate

@Entity
public class Order { // ← AGGREGATE ROOT
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String orderId;

    @Embedded
    private CustomerId customerId; // Reference to Customer aggregate by ID (not object!)

    @OneToMany(cascade = CascadeType.ALL, orphanRemoval = true)
    private List<OrderItem> items = new ArrayList<>(); // Part of this aggregate

    @Embedded
    private Address shippingAddress;  // Value Object

    @Embedded
    private Money totalAmount;

    private OrderStatus status;

    @Version
    private Long version; // Optimistic locking

    // ═══ Business methods on Aggregate Root ═══
    // External code CANNOT directly modify OrderItem — must go through Order

    public void addItem(ProductId productId, String productName, Money price, int quantity) {
        if (status != OrderStatus.DRAFT) {
            throw new OrderNotModifiableException("Cannot add items to " + status + " order");
        }
        // Business rule: max 50 items per order
        if (items.size() >= 50) {
            throw new OrderLimitExceededException("Maximum 50 items per order");
        }

        OrderItem item = new OrderItem(productId, productName, price, quantity);
        items.add(item);
        recalculateTotal();
    }

    public void removeItem(String itemId) {
        if (status != OrderStatus.DRAFT) {
            throw new OrderNotModifiableException("Cannot remove items from " + status + " order");
        }
        items.removeIf(item -> item.getItemId().equals(itemId));
        recalculateTotal();
    }

    public void submit() {
        if (items.isEmpty()) {
            throw new EmptyOrderException("Cannot submit empty order");
        }
        this.status = OrderStatus.SUBMITTED;
        // Raise domain event
        registerEvent(new OrderSubmittedEvent(this.orderId, this.customerId, this.totalAmount));
    }

    public void cancel(String reason) {
        if (status == OrderStatus.SHIPPED || status == OrderStatus.DELIVERED) {
            throw new OrderNotCancellableException("Cannot cancel " + status + " order");
        }
        this.status = OrderStatus.CANCELLED;
        registerEvent(new OrderCancelledEvent(this.orderId, reason));
    }

    private void recalculateTotal() {
        this.totalAmount = items.stream()
            .map(OrderItem::getSubtotal)
            .reduce(Money.ZERO, Money::add);
    }
}

// OrderItem is NOT an aggregate root — cannot be accessed directly
@Entity
public class OrderItem {
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private String itemId;

    @Embedded
    private ProductId productId; // Reference by ID

    private String productName;

    @Embedded
    private Money price;

    private int quantity;

    public Money getSubtotal() {
        return new Money(
            price.amount().multiply(BigDecimal.valueOf(quantity)),
            price.currency()
        );
    }
}
```

---

## 📖 Hexagonal Architecture (Ports & Adapters)

### Theory:
Hexagonal architecture places the **domain logic at the center** and uses **ports** (interfaces) and **adapters** (implementations) to connect to external systems. The domain doesn't depend on frameworks, databases, or APIs — they depend on the domain.

```
                    ┌─────────────────────────────────┐
  REST API ───→     │         APPLICATION LAYER        │
  GraphQL ───→     │  ┌───────────────────────────┐  │     ───→ PostgreSQL
  gRPC ───→        │  │      DOMAIN LAYER          │  │     ───→ Redis
                    │  │                            │  │     ───→ Kafka
  Web UI ───→      │  │  Entities, Value Objects   │  │     ───→ External APIs
                    │  │  Domain Services           │  │
  Scheduled ───→   │  │  Domain Events             │  │
  Jobs             │  │  Business Rules            │  │
                    │  │                            │  │
                    │  └───────────────────────────┘  │
  Input Ports      │         Output Ports              │   Output Adapters
  (Interfaces)     └─────────────────────────────────┘   (Implementations)
```

### Code Structure:
```
src/
├── domain/                          # 🏛️ CORE — zero framework dependencies!
│   ├── model/
│   │   ├── Order.java               # Aggregate Root
│   │   ├── OrderItem.java           # Entity
│   │   ├── Money.java               # Value Object
│   │   └── OrderStatus.java         # Enum
│   ├── event/
│   │   └── OrderSubmittedEvent.java  # Domain Event
│   ├── port/
│   │   ├── in/
│   │   │   └── CreateOrderUseCase.java    # Input Port (interface)
│   │   └── out/
│   │       ├── OrderRepository.java       # Output Port (interface)
│   │       └── PaymentPort.java           # Output Port (interface)
│   └── service/
│       └── OrderDomainService.java  # Logic that spans entities
│
├── application/                     # 📋 USE CASES — orchestration
│   └── CreateOrderService.java      # Implements CreateOrderUseCase
│
├── adapter/                         # 🔌 ADAPTERS — framework-specific
│   ├── in/
│   │   └── web/
│   │       └── OrderController.java # REST endpoint (Input Adapter)
│   └── out/
│       ├── persistence/
│       │   └── JpaOrderRepository.java  # PostgreSQL (Output Adapter)
│       └── messaging/
│           └── KafkaEventPublisher.java # Kafka (Output Adapter)
```

```java
// INPUT PORT (Interface — domain layer)
public interface CreateOrderUseCase {
    OrderId createOrder(CreateOrderCommand command);
}

// APPLICATION SERVICE (implements use case)
@Service
@Transactional
public class CreateOrderService implements CreateOrderUseCase {

    private final OrderRepository orderRepo;    // Output port
    private final PaymentPort paymentPort;      // Output port

    @Override
    public OrderId createOrder(CreateOrderCommand cmd) {
        // Pure business logic — no framework code!
        Order order = Order.create(cmd.getCustomerId(), cmd.getShippingAddress());
        cmd.getItems().forEach(item ->
            order.addItem(item.productId(), item.name(), item.price(), item.quantity()));
        order.submit();

        orderRepo.save(order); // Calls port — doesn't know it's PostgreSQL

        return order.getOrderId();
    }
}

// OUTPUT PORT (Interface — domain layer)
public interface OrderRepository {
    void save(Order order);
    Optional<Order> findById(OrderId id);
}

// OUTPUT ADAPTER (Implementation — adapter layer)
@Repository
public class JpaOrderRepository implements OrderRepository {
    @Autowired
    private JpaOrderEntityRepository jpaRepo; // Spring Data JPA

    @Override
    public void save(Order order) {
        OrderEntity entity = OrderMapper.toEntity(order);
        jpaRepo.save(entity);
    }

    @Override
    public Optional<Order> findById(OrderId id) {
        return jpaRepo.findById(id.value())
            .map(OrderMapper::toDomain);
    }
}
```

**Benefits of Hexagonal Architecture:**
- **Testability**: Test domain logic without database, Kafka, HTTP
- **Flexibility**: Swap PostgreSQL for MongoDB by changing only the adapter
- **Clean boundaries**: Domain code never imports `org.springframework.*`
