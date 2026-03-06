# 🎨 Design Patterns — Deep Dive (Theory + Code + Cross-Questions)
## Target: 12+ Years Experience

---

## 📖 What are Design Patterns?

Design Patterns are **reusable, proven solutions to commonly occurring problems** in software design. They are not frameworks or libraries — they are **templates** and **best practices** captured from experienced developers, introduced formally by the "Gang of Four" (GoF) in 1994.

### Why they matter at the 12-year level:
At a senior level, you are expected to recognize *when* a pattern is applicable, *why* it's better than the alternative, and *what trade-offs* it introduces. Saying "I used the Factory Pattern here" is not enough — you must explain **why you chose it over a direct constructor**, and **what problem it solves**.

### Three Categories:
| Category | Purpose | Patterns |
|----------|---------|----------|
| **Creational** | How objects are **created** | Singleton, Builder, Factory, Abstract Factory, Prototype |
| **Structural** | How objects are **composed** | Adapter, Decorator, Proxy, Facade, Composite, Bridge, Flyweight |
| **Behavioral** | How objects **communicate** | Observer, Strategy, Template Method, Chain of Responsibility, Command, Iterator, State |

---

## CATEGORY 1: CREATIONAL PATTERNS

---

### 1. Singleton Pattern

#### 📖 Theory:
**What:** Ensures a class has **exactly one instance** and provides a **global access point** to it.

**Why it exists:** Some resources are expensive to create and should exist only once — database connection pools, configuration managers, logging services, thread pools. Creating multiple instances would be wasteful (memory) or incorrect (inconsistent state).

**How it works:** The constructor is made `private`. A static method/field holds the one instance. All calls to get it return the same object.

**The Thread-Safety Problem:** In multi-threaded apps, two threads can both enter the constructor simultaneously (double-checked locking issue before Java 5). The **Enum approach** is the gold standard — the JVM guarantees enums are instantiated once, making it intrinsically thread-safe.

**When to use:**
- ✅ Shared resource: DB connection pool, Redis client, config manager
- ✅ Stateless utility services (but prefer Spring `@Bean` singleton instead)
- ❌ Avoid in domain objects (creates tight coupling and hard-to-test code)

```java
// ✅ APPROACH 1: Enum Singleton (Best — Thread-safe, Serialization-safe)
// The JVM guarantees an enum type is instantiated exactly once.
// This is the approach Joshua Bloch (Effective Java) recommends.
public enum DatabaseConnectionPool {
    INSTANCE;

    private final DataSource dataSource;

    DatabaseConnectionPool() {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:postgresql://localhost/prod");
        config.setMaximumPoolSize(50);
        this.dataSource = new HikariDataSource(config);
    }

    public Connection getConnection() throws SQLException {
        return dataSource.getConnection();
    }
}

// Usage
DatabaseConnectionPool.INSTANCE.getConnection();

// ✅ APPROACH 2: Double-Checked Locking (Classic, verbose)
// The 'volatile' keyword prevents CPU instruction reordering,
// which caused subtle bugs in Java 4 and earlier.
public class ConfigManager {
    private static volatile ConfigManager instance; // volatile is CRITICAL

    private ConfigManager() { /* Load config */ }

    public static ConfigManager getInstance() {
        if (instance == null) {                        // First check (no lock)
            synchronized (ConfigManager.class) {
                if (instance == null) {                // Second check (in lock)
                    instance = new ConfigManager();
                }
            }
        }
        return instance;
    }
}

// ✅ APPROACH 3: Initialization-on-Demand Holder (Elegant, lazy, thread-safe)
// Only creates instance when getInstance() is FIRST called.
// The class loader guarantees the static inner class is loaded once.
public class Singleton {
    private Singleton() {}

    private static class Holder {
        static final Singleton INSTANCE = new Singleton();
    }

    public static Singleton getInstance() {
        return Holder.INSTANCE; // Thread-safe, no synchronization overhead
    }
}
```

**Interview Cross-Questions:**
> **Q: "Why is the Enum Singleton safe against reflection attacks?"**
> A: "Java explicitly prohibits creating a second instance of an Enum via reflection. If you call `constructor.newInstance()` on an Enum, the JVM throws `IllegalArgumentException: Cannot reflectively create enum objects`. With a standard Singleton class, reflection can invoke the private constructor, creating a second instance."

---

### 2. Builder Pattern

#### 📖 Theory:
**What:** Constructs a **complex object step by step**, returning the fully built object only when `build()` is called.

**Why it exists:** Consider a class with 10 fields, some optional. You could have 10 different constructors (telescoping constructor anti-pattern). This makes reading of call-sites impossible: `new Request("url", null, null, "POST", 5000, true, null, null)`. The Builder separates the construction logic from the object's representation.

**How it works:** A static inner `Builder` class mirrors the target object's fields. Each setter on the Builder returns `this` (fluent API / method chaining). The target class's constructor is `private` and accepts only the `Builder` object.

**When to use:**
- Object has 4+ optional parameters
- Object must be immutable after creation (no setters on the final object)
- The construction process must happen step-by-step or be readable

**Real-world Java examples:** `StringBuilder`, `HttpClient.Builder`, `@Builder` from Lombok, `BeanDefinitionBuilder` in Spring.

```java
// Real-world: HTTP Request Builder
// ❌ BEFORE Builder — unreadable!
// new HttpRequest("https://api.com", "POST", headers, body, 3000, true, null, "gzip");
//   What does the 6th boolean mean? The 7th null?

// ✅ AFTER Builder — completely self-documenting
public class HttpRequest {
    private final String url;
    private final String method;
    private final Map<String, String> headers;
    private final String body;
    private final int timeoutMs;

    // Private constructor — only the Builder can call this
    private HttpRequest(Builder builder) {
        this.url = builder.url;
        this.method = builder.method;
        this.headers = Collections.unmodifiableMap(builder.headers);
        this.body = builder.body;
        this.timeoutMs = builder.timeoutMs;
    }

    public static class Builder {
        private String url;                          // Required
        private String method = "GET";               // Optional, has default
        private final Map<String, String> headers = new HashMap<>(); // Optional
        private String body;                         // Optional
        private int timeoutMs = 5000;               // Optional, has default

        // Each method returns 'this' enabling fluent chaining
        public Builder url(String url) { this.url = url; return this; }
        public Builder post(String body) { this.method = "POST"; this.body = body; return this; }
        public Builder header(String key, String value) { headers.put(key, value); return this; }
        public Builder timeout(int ms) { this.timeoutMs = ms; return this; }

        public HttpRequest build() {
            // Validate required fields here (fail-fast before object creation)
            Objects.requireNonNull(url, "URL is required");
            return new HttpRequest(this);
        }
    }
}

// Perfectly readable usage
HttpRequest request = new HttpRequest.Builder()
    .url("https://api.payment.com/charge")
    .post("{\"amount\": 100}")
    .header("Authorization", "Bearer " + token)
    .header("Content-Type", "application/json")
    .timeout(3000)
    .build();
```

**Interview Cross-Questions:**
> **Q: "The Builder pattern creates a separate Builder class. Lombok's `@Builder` annotation reduces this boilerplate. Would you always use Lombok in production code?"**
> A: "Lombok's `@Builder` is excellent for reducing boilerplate and I'd use it in most cases. However, I would **not** use it when I need custom validation inside `build()` (since Lombok generates a generic builder), or when the construction order matters (Lombok has no enforced step ordering). In libraries or open-source APIs, I'd avoid Lombok to avoid forcing a compile-time dependency on consumers."

---

### 3. Factory Method Pattern

#### 📖 Theory:
**What:** Defines an interface for creating an object but lets **subclasses (or implementations) decide which class to instantiate**. The creator defers instantiation to a factory method.

**Why it exists:** Without a factory, the calling code is tightly coupled to a concrete class: `new StripePaymentProcessor()`. If you need to swap to a different payment gateway, you must find every single `new` statement in your codebase. The Factory abstracts object creation, making the code depend only on abstractions.

**How it works:** A single factory class/method takes a parameter (like a string, enum, or context) and returns the correct implementation of an interface.

**Factory vs Abstract Factory:** Factory creates **one type of object** (one product). Abstract Factory creates **families of related objects** (a product suite).

**When to use:**
- You don't know ahead of time which class to instantiate (strategy/plugin based on config or runtime data)
- Adding new implementations should not require modifying existing code (OCP principle)

```java
// Real-world: Payment Processor Factory
// Interface defines the contract
public interface PaymentProcessor {
    PaymentResult process(Payment payment);
    boolean supports(String paymentMethod); // Self-selection
}

@Component
public class CreditCardProcessor implements PaymentProcessor {
    @Override
    public PaymentResult process(Payment payment) {
        // Delegates to Stripe or a card gateway
        return stripeClient.charge(payment);
    }
    @Override
    public boolean supports(String method) { return "CREDIT_CARD".equals(method); }
}

@Component
public class UPIProcessor implements PaymentProcessor {
    @Override
    public PaymentResult process(Payment payment) {
        return upiGateway.initiate(payment);
    }
    @Override
    public boolean supports(String method) { return "UPI".equals(method); }
}

// The Factory — Spring auto-injects all PaymentProcessor beans into the list
// Adding a new processor (e.g., "BNPL") just requires a new class — NO factory changes!
@Service
public class PaymentProcessorFactory {
    private final List<PaymentProcessor> processors; // Spring DI

    public PaymentProcessorFactory(List<PaymentProcessor> processors) {
        this.processors = processors;
    }

    public PaymentProcessor getProcessor(String paymentMethod) {
        return processors.stream()
            .filter(p -> p.supports(paymentMethod))
            .findFirst()
            .orElseThrow(() -> new UnsupportedPaymentMethodException(paymentMethod));
    }
}

// Usage at the service layer
PaymentProcessor processor = factory.getProcessor("UPI"); // UPIProcessor returned
PaymentResult result = processor.process(payment);
```

---

### 4. Abstract Factory Pattern

#### 📖 Theory:
**What:** Provides an interface for creating **families of related objects** without specifying their concrete classes. The Abstract Factory is a factory of factories.

**Why it exists:** Imagine an e-commerce UI that needs to render on both Mobile and Desktop. Both platforms need Buttons, TextFields, and Dialogs, but they look different. The Abstract Factory ensures that you never accidentally mix a Mobile Button with a Desktop Dialog — they always come from the same factory.

**When to use:**
- System must be independent of how its products are created, composed, and represented
- System is configured with one of multiple **families** of objects
- Enforce constraints between related objects (you can't mix themes)

```java
// Interface: defines what the factory can create
public interface UIComponentFactory {
    Button createButton();
    TextField createTextField();
    Dialog createDialog();
}

// Factory 1: Material Design (Google's design system)
public class MaterialUIFactory implements UIComponentFactory {
    @Override public Button createButton() { return new MaterialButton(); }
    @Override public TextField createTextField() { return new MaterialTextField(); }
    @Override public Dialog createDialog() { return new MaterialDialog(); }
}

// Factory 2: Dark Mode Theme
public class DarkThemeUIFactory implements UIComponentFactory {
    @Override public Button createButton() { return new DarkButton(); }
    @Override public TextField createTextField() { return new DarkTextField(); }
    @Override public Dialog createDialog() { return new DarkDialog(); }
}

// The client only talks to the abstract factory interface
// Theme is determined at startup from config, never mixed
public class Application {
    private final UIComponentFactory factory;

    public Application(UIComponentFactory factory) {
        this.factory = factory; // Inject MaterialUIFactory or DarkThemeUIFactory
    }

    public void buildUI() {
        Button btn = factory.createButton();     // Always matches the theme!
        Dialog dlg = factory.createDialog();     // Same theme guaranteed
    }
}
```

---

### 5. Prototype Pattern

#### 📖 Theory:
**What:** Creates new objects by **cloning an existing object** (the prototype) instead of creating from scratch.

**Why it exists:** Some object initialization is expensive (database calls, complex computations, loading huge configurations). Once you have one valid, fully-initialized object (the prototype), you can clone it cheaply and customize the clone.

**Deep Copy vs Shallow Copy:**
- **Shallow copy** (`Object.clone()` default): Copies the object, but any object references inside point to the SAME original objects. Mutating the clone's list mutates the original.
- **Deep copy**: Creates completely independent copies of nested objects. You own this copy entirely.

**When to use:**
- Object creation is expensive (database calls, network, heavy computation)
- You need many similar objects with small differences (e.g., report templates)

```java
@Entity
public class ReportTemplate implements Cloneable {
    private String templateId;
    private List<Column> columns;         // Mutable — needs deep copy!
    private Map<String, Filter> filters;  // Mutable — needs deep copy!

    @Override
    public ReportTemplate clone() {
        try {
            ReportTemplate clone = (ReportTemplate) super.clone(); // Shallow copy first

            // Deep copy: create new independent collections
            clone.columns = columns.stream()
                .map(Column::clone)     // Each Column must also be cloned
                .collect(Collectors.toList());
            clone.filters = new HashMap<>(filters); // Shallow copy of map is fine if values are immutable

            return clone;
        } catch (CloneNotSupportedException e) {
            throw new AssertionError("Should not happen — we implement Cloneable");
        }
    }
}

// Usage: cheaply clone a pre-loaded template, customize, save as new report
ReportTemplate monthlyTemplate = templateRegistry.get("SALES_MONTHLY"); // Expensive to create
ReportTemplate customReport = monthlyTemplate.clone(); // Cheap clone!
customReport.addFilter("region", "ASIA");
customReport.setTemplateId(UUID.randomUUID().toString());
reportRepo.save(customReport);
```

---

## CATEGORY 2: STRUCTURAL PATTERNS

---

### 6. Adapter Pattern

#### 📖 Theory:
**What:** Converts the **interface of a class into another interface** that clients expect. Adapter lets classes work together that couldn't otherwise because of incompatible interfaces.

**Analogy:** A power adapter for travelling. Your Indian 3-pin device works in a European 2-pin socket via a physical adapter that converts the shape. Nothing inside your device changes.

**Why it exists:** In enterprise systems, you constantly integrate with **legacy systems** or **third-party libraries** that have an API incompatible with your modern architecture. Rewriting the legacy system is costly and risky. The Adapter wraps the old system and exposes a new compatible interface.

**Two types:**
- **Object Adapter:** Wraps an instance of the incompatible class (via composition). Preferred.
- **Class Adapter:** Uses multiple inheritance (Java doesn't support this for classes).

**When to use:**
- Integrating with a legacy system
- Using a third-party library that doesn't match your domain model
- Migrating between different API standards (REST to gRPC, legacy XML to JSON)

```java
// PROBLEM: You have a modern payment system interface (ModernPaymentGateway)
// but an old legacy system (LegacyPaymentSystem) that can't be modified (it's a JAR from 2008)

// Old legacy interface — CANNOT MODIFY THIS
public class LegacyPaymentSystem {
    public String makePayment(double amount, String currency, String cardNo) {
        // Old C++ code wrapped in Java... do not touch!
        return "LEGACY_TX_" + System.currentTimeMillis();
    }
}

// New modern interface your application code expects
public interface ModernPaymentGateway {
    PaymentResponse processPayment(PaymentRequest request);
}

// ✅ ADAPTER: Bridges the incompatible gap
// Implements the new interface, delegates internally to the old system
@Service
public class LegacyPaymentAdapter implements ModernPaymentGateway {
    private final LegacyPaymentSystem legacySystem;

    public LegacyPaymentAdapter(LegacyPaymentSystem legacySystem) {
        this.legacySystem = legacySystem; // Wrapped via composition
    }

    @Override
    public PaymentResponse processPayment(PaymentRequest request) {
        // Convert modern request → legacy parameters
        String txId = legacySystem.makePayment(
            request.getAmount().doubleValue(),  // BigDecimal → double
            request.getCurrency(),
            request.getCard().getNumber()
        );

        // Convert legacy response (just a String) → modern PaymentResponse object
        return PaymentResponse.builder()
            .transactionId(txId)
            .status("SUCCESS")
            .processedAt(Instant.now())
            .build();
    }
}
```

---

### 7. Decorator Pattern

#### 📖 Theory:
**What:** Attaches **additional responsibilities to an object dynamically** by wrapping it in decorator objects. Decorators provide a flexible alternative to subclassing for extending functionality.

**Analogy:** A coffee. Start with a plain coffee (base). Wrap it with a `MilkDecorator` (adds milk and its cost). Wrap that again with a `SugarDecorator`. The result is a Milk+Sugar coffee without a separate `MilkSugarCoffee` class.

**Why it exists:** Inheritance is static (baked in at compile time). Decoration is dynamic (applied at runtime). If you need 10 combinations of M features, inheritance requires 2^M subclasses. Decoration only requires M decorator classes.

**How it works:** The Decorator implements the same interface as the base component. It holds a reference to another object of that interface (the `delegate`). It adds behavior before or after delegating to the wrapped object.

**Real-world Java:** `InputStream` → `BufferedInputStream` → `GZIPInputStream`. Each wraps the previous, adding buffering, then decompression.

**When to use:**
- Adding cross-cutting concerns (logging, caching, security, metrics) without touching core logic
- Behavior should be added at runtime, not compile time
- When you need various combinations of optional features

```java
// The shared interface
public interface OrderRepository {
    Optional<Order> findById(String id);
    Order save(Order order);
}

// ✅ BASE: The core JPA implementation
@Repository
public class JpaOrderRepository implements OrderRepository {
    @Autowired private OrderJpaRepo jpaRepo;
    @Override public Optional<Order> findById(String id) { return jpaRepo.findById(id); }
    @Override public Order save(Order order) { return jpaRepo.save(order); }
}

// ✅ DECORATOR 1: Adds logging (wraps any OrderRepository)
public class LoggingOrderRepository implements OrderRepository {
    private final OrderRepository delegate; // The wrapped object

    public LoggingOrderRepository(OrderRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public Optional<Order> findById(String id) {
        log.info("[DB-CALL] Finding order: {}", id);
        long start = System.currentTimeMillis();
        Optional<Order> result = delegate.findById(id);
        log.info("[DB-CALL] findById took {}ms", System.currentTimeMillis() - start);
        return result;
    }
    @Override public Order save(Order order) { return delegate.save(order); }
}

// ✅ DECORATOR 2: Adds in-memory caching (wraps any OrderRepository)
public class CachingOrderRepository implements OrderRepository {
    private final OrderRepository delegate;
    private final Map<String, Order> cache = new ConcurrentHashMap<>();

    public CachingOrderRepository(OrderRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public Optional<Order> findById(String id) {
        if (cache.containsKey(id)) {
            log.debug("[CACHE-HIT] order: {}", id);
            return Optional.of(cache.get(id));
        }
        Optional<Order> result = delegate.findById(id);
        result.ifPresent(order -> cache.put(id, order)); // Populate cache
        return result;
    }

    @Override
    public Order save(Order order) {
        Order saved = delegate.save(order);
        cache.put(saved.getId(), saved); // Keep cache consistent
        return saved;
    }
}

// ✅ WIRING: Chain decorators at runtime (Spring @Bean config)
@Bean
public OrderRepository orderRepository(JpaOrderRepository jpa) {
    return new CachingOrderRepository(     // Level 3: Add caching
        new LoggingOrderRepository(         // Level 2: Add logging
            jpa                             // Level 1: Core JPA
        )
    );
}
// Now: cache check → (if miss) log → execute JPA query
```

---

### 8. Proxy Pattern

#### 📖 Theory:
**What:** Provides a **surrogate or placeholder** for another object to control access to it.

**Why it exists:** You want to add functionality around an object (access control, lazy initialization, logging, caching, remote invocation) WITHOUT the client knowing or the original object changing.

**Types of Proxies:**
- **Virtual Proxy:** Defers expensive object creation until first use (lazy loading). Hibernate does this for `@OneToMany` relationships.
- **Protection Proxy:** Controls access based on permissions.
- **Remote Proxy:** Represents an object in a different JVM or server (RMI, gRPC stubs).
- **Caching Proxy:** Caches results of expensive operations.

**The Spring Connection:** Spring's `@Transactional`, `@Cacheable`, `@Async`, `@PreAuthorize` all use **dynamic JDK or CGLIB Proxies** generated at startup. When you call `@Transactional public void save()`, you're actually calling the Proxy's `save()`, which opens a transaction, then calls your real `save()`.

```java
// EXAMPLE 1: Virtual Proxy — Lazy Loading (like Hibernate's LAZY)
public interface UserProfile {
    String getName();
    List<Post> getPosts(); // Very expensive — 10,000 posts in DB
}

public class UserProfileProxy implements UserProfile {
    private final String userId;
    private UserProfile realProfile = null; // Not loaded yet!
    private final UserProfileLoader loader;

    @Override
    public String getName() {
        // Lazy load ONLY when actually needed
        if (realProfile == null) {
            this.realProfile = loader.loadFromDatabase(userId);
        }
        return realProfile.getName();
    }

    @Override
    public List<Post> getPosts() {
        if (realProfile == null) {
            this.realProfile = loader.loadFromDatabase(userId);
        }
        return realProfile.getPosts();
    }
}

// EXAMPLE 2: Protection / Security Proxy
public class SecureDocumentProxy implements Document {
    private final RealDocument document;
    private final User currentUser;

    @Override
    public String read() {
        if (!currentUser.hasPermission("DOCUMENT_READ")) {
            throw new AccessDeniedException("User lacks DOCUMENT_READ permission");
        }
        return document.read(); // Delegate to real object only if authorized
    }
}

// EXAMPLE 3: Spring AOP IS the Proxy pattern
@Aspect @Component public class LoggingProxy {
    @Around("@annotation(org.springframework.transaction.annotation.Transactional)")
    public Object aroundTransactional(ProceedingJoinPoint pjp) throws Throwable {
        log.info("BEFORE TX: {}", pjp.getSignature());
        Object result = pjp.proceed(); // Call real method
        log.info("AFTER TX: {}", pjp.getSignature());
        return result;
    }
}
```

---

### 9. Facade Pattern

#### 📖 Theory:
**What:** Provides a **simplified interface** to a complex subsystem. The Facade doesn't add new functionality — it makes existing functionality easier to use by hiding complexity.

**Analogy:** A car's ignition key. Turning the key starts the engine, engages the fuel pump, initializes the ECU, and sets the alternator running. You just turn the key (Facade) without knowing about all 12 subsystems.

**Why it exists:** When a feature requires coordinating multiple services (user validation, inventory, pricing, payment, shipping), the calling code should not manage all these dependencies. The Facade provides a single, clean `placeOrder()` entry point.

**Difference from Adapter:** Adapter changes an interface to make it compatible. Facade creates a simplified interface on top of multiple complex ones.

**When to use:**
- Complex subsystem coordination (e.g., order processing, report generation)
- Layer boundary: exposing a clean API to the client layer while hiding service-layer complexity
- Legacy system wrapping (along with Adapter)

```java
// Without Facade — the calling code must orchestrate all 5 services (brittle, hard to test)
// userService.validate(userId);
// inventoryService.reserveItems(items);
// BigDecimal total = pricingService.calculateTotal(items, couponCode);
// paymentService.charge(userId, total, cardDetails);
// shippingService.scheduleDelivery(items, address);

// ✅ WITH Facade — single clean method hiding all complexity
@Service
public class OrderFacade {
    // Injects 5 complex services, hides them all
    private final UserService userService;
    private final InventoryService inventoryService;
    private final PricingService pricingService;
    private final PaymentService paymentService;
    private final ShippingService shippingService;

    // The Facade's single, clean API
    @Transactional
    public OrderConfirmation placeOrder(OrderRequest request) {

        // Step 1: Validate the user's identity and eligibility
        User user = userService.validateAndGet(request.getUserId());

        // Step 2: Reserve the requested items from inventory (hold them for 15 minutes)
        List<Item> reservedItems = inventoryService.reserve(request.getItems());

        // Step 3: Calculate final price with discounts, taxes, and coupons applied
        BigDecimal total = pricingService.calculate(reservedItems, request.getCouponCode());

        // Step 4: Charge the customer
        Payment payment = paymentService.charge(user, total, request.getCard());

        // Step 5: Schedule shipping
        Shipment shipment = shippingService.schedule(reservedItems, request.getShippingAddress());

        // Assemble and return the one clean confirmation object
        return OrderConfirmation.builder()
            .orderId(UUID.randomUUID().toString())
            .items(reservedItems)
            .total(total)
            .paymentId(payment.getId())
            .expectedDelivery(shipment.getExpectedDate())
            .build();
    }
}
```

---

## CATEGORY 3: BEHAVIORAL PATTERNS

---

### 10. Observer Pattern (Event-Driven)

#### 📖 Theory:
**What:** Defines a **one-to-many dependency** between objects. When one object (the **Subject/Publisher**) changes state, all its dependents (**Observers/Subscribers**) are notified and updated automatically.

**Why it exists:** Without the Observer pattern, an `OrderService` that creates an order must know about `EmailService`, `InventoryService`, and `AnalyticsService` and call each one. This is **tight coupling** — adding a new action requires modifying `OrderService`. With Observer, `OrderService` just publishes an event and never needs to know who listens.

**How it works:**
1. Publisher fires an Event
2. All registered Observers/Listeners receive the event and react independently

**Real-world usage:** Spring's `ApplicationEventPublisher`, Kafka/RabbitMQ event messaging, GUI button click listeners, MVC frameworks triggering view updates.

```java
// ✅ Spring's ApplicationEventPublisher IS an Observer implementation

// The Event (Data Transfer Object carrying state)
public class OrderCreatedEvent extends ApplicationEvent {
    private final Order order;

    public OrderCreatedEvent(Object source, Order order) {
        super(source);
        this.order = order;
    }

    public Order getOrder() { return order; }
}

// The Publisher (Subject) — knows nothing about who listens
@Service
public class OrderService {
    @Autowired private ApplicationEventPublisher publisher;
    @Autowired private OrderRepository orderRepo;

    @Transactional
    public Order createOrder(OrderRequest request) {
        Order order = orderRepo.save(new Order(request));

        // Just fire the event — we DON'T KNOW how many listeners there are!
        publisher.publishEvent(new OrderCreatedEvent(this, order));
        return order;
    }
}

// Observer 1: Email confirmation (runs asynchronously)
@Component
public class WelcomeEmailListener {
    @EventListener
    @Async // Non-blocking — doesn't slow down the order creation
    public void onOrderCreated(OrderCreatedEvent event) {
        emailService.sendConfirmation(event.getOrder());
    }
}

// Observer 2: Inventory reservation (runs synchronously, in same transaction)
@Component
public class InventoryListener {
    @EventListener
    public void onOrderCreated(OrderCreatedEvent event) {
        inventoryService.reserveStock(event.getOrder());
    }
}

// Observer 3: Analytics tracking (a new listener added without changing OrderService!)
@Component
public class AnalyticsListener {
    @EventListener
    @Async
    public void onOrderCreated(OrderCreatedEvent event) {
        analyticsService.track("ORDER_CREATED", event.getOrder());
    }
}
```

---

### 11. Strategy Pattern

#### 📖 Theory:
**What:** Defines a **family of algorithms**, encapsulates each one, and makes them **interchangeable**. The strategy lets the algorithm vary independently from the clients that use it.

**Why it exists:** Without Strategy, code that needs multiple algorithms ends up as a giant `if-else` or `switch` statement. Adding a new algorithm requires modifying existing (often risky) code. Strategy extracts each algorithm into its own class and selects the right one at runtime.

**Relationship to OCP:** Strategy is the primary way to implement the Open/Closed Principle for algorithms.

**When to use:**
- Multiple variants of an algorithm exist
- The runtime choice of algorithm depends on input data, user settings, or configuration
- You want to eliminate conditional branching on type

```java
// ✅ Real-world: Dynamic discount calculation strategy

// The contract every strategy must fulfill
@FunctionalInterface
public interface DiscountStrategy {
    BigDecimal apply(BigDecimal price, Customer customer);
}

// Strategy 1: New user — flat 20% off
@Component("newUserDiscount")
public class NewUserDiscountStrategy implements DiscountStrategy {
    @Override
    public BigDecimal apply(BigDecimal price, Customer customer) {
        // New users always get 20% off their first purchase
        return price.multiply(BigDecimal.valueOf(0.80));
    }
}

// Strategy 2: Loyalty discount — increases with years of membership
@Component("loyaltyDiscount")
public class LoyaltyDiscountStrategy implements DiscountStrategy {
    @Override
    public BigDecimal apply(BigDecimal price, Customer customer) {
        int years = customer.getMembershipYears();
        double discountRate = Math.min(0.30, years * 0.05); // 5% per year, max 30%
        return price.multiply(BigDecimal.valueOf(1 - discountRate));
    }
}

// Strategy 3: Flash sale — a new algorithm, added without changing any existing code!
@Component("flashSaleDiscount")
public class FlashSaleDiscountStrategy implements DiscountStrategy {
    @Override
    public BigDecimal apply(BigDecimal price, Customer customer) {
        return price.multiply(BigDecimal.valueOf(0.50)); // 50% off
    }
}

// Context: Selects strategy at runtime
@Service
public class PricingService {
    // Spring injects a Map<String (bean name), DiscountStrategy (bean)>
    private final Map<String, DiscountStrategy> strategies;

    public BigDecimal calculatePrice(BigDecimal basePrice, Customer customer) {
        String strategyKey = determineStrategyKey(customer);
        return strategies.get(strategyKey).apply(basePrice, customer);
    }

    private String determineStrategyKey(Customer customer) {
        if (flashSaleService.isActive()) return "flashSaleDiscount";
        if (customer.isNewUser()) return "newUserDiscount";
        return "loyaltyDiscount";
    }
}
```

---

### 12. Template Method Pattern

#### 📖 Theory:
**What:** Defines the **skeleton of an algorithm** in a base class, deferring some **specific steps to subclasses**. The algorithm structure is fixed; the implemented details vary.

**Why it exists:** When multiple classes share the same overall process but differ in specific steps, you can avoid code duplication by defining the shared skeleton once in an abstract base class and letting subclasses fill in the variable "holes".

**How it works:**
1. A `final` template method in the base class defines the step order (the algorithm skeleton).
2. Abstract methods define the "holes" that subclasses must fill.
3. Optional hook methods have default implementations that subclasses can override.

**Real-world Java:** `JdbcTemplate` (opens connection, executes your query, handles exceptions, closes connection), `AbstractController` in Spring MVC.

**Difference from Strategy:** Template Method uses **inheritance** (subclasses override steps). Strategy uses **composition** (inject different strategy objects).

```java
// ✅ Template Method: Report Generation Framework
// The final generate() defines the step order — cannot be overridden
public abstract class ReportGenerator {

    // TEMPLATE METHOD — skeleton of the algorithm
    // 'final' prevents subclasses from breaking the algorithm order
    public final Report generate(ReportCriteria criteria) {
        validateCriteria(criteria);              // Step 1: Common validation (final)
        List<Object> rawData = fetchData(criteria); // Step 2: Varies (abstract)
        List<Object> processedData = processData(rawData); // Step 3: Optional variation
        return formatReport(processedData);      // Step 4: Varies (abstract)
    }

    // Concrete step — shared by all report types, not overridable
    private void validateCriteria(ReportCriteria criteria) {
        Objects.requireNonNull(criteria.getStartDate(), "Start date is required");
        Objects.requireNonNull(criteria.getEndDate(), "End date is required");
    }

    // Abstract step — each report type fetches different data
    protected abstract List<Object> fetchData(ReportCriteria criteria);

    // Hook method — subclasses CAN override but don't have to
    protected List<Object> processData(List<Object> data) {
        return data; // Default: no transformation
    }

    // Abstract step — each report formats output differently
    protected abstract Report formatReport(List<Object> data);
}

// Subclass 1: Fills in sub-steps for Sales Reports
public class SalesReportGenerator extends ReportGenerator {
    @Override
    protected List<Object> fetchData(ReportCriteria criteria) {
        // Specific query: fetch sales data from OLAP DB
        return salesRepo.findBetween(criteria.getStartDate(), criteria.getEndDate());
    }

    @Override
    protected List<Object> processData(List<Object> data) {
        // Override hook: apply currency conversion for multi-region sales
        return currencyConverter.convertToUSD(data);
    }

    @Override
    protected Report formatReport(List<Object> data) {
        return new ExcelReport(data, "Monthly Sales Report");
    }
}

// Subclass 2: Fills in sub-steps for HR Reports
public class EmployeeReportGenerator extends ReportGenerator {
    @Override
    protected List<Object> fetchData(ReportCriteria criteria) {
        return hrRepo.findActiveEmployeesBetween(criteria.getStartDate(), criteria.getEndDate());
    }

    @Override
    protected Report formatReport(List<Object> data) {
        return new PdfReport(data, "Employee Roster Report"); // Different format!
    }
    // processData() NOT overridden — uses the base class default (no transformation)
}
```

---

### 13. Chain of Responsibility Pattern

#### 📖 Theory:
**What:** Passes a request along a **chain of handlers** where each handler decides to either process the request or pass it to the next handler in the chain.

**Why it exists:** Without this pattern, a single class with a massive `if-else` sequence handles all cases. The Chain lets you add, reorder, or remove handlers without changing the other handlers or the client that triggers the chain.

**Real-world Java:** Spring Security's `FilterChain` is a perfect example — each Security Filter (JWT check, CORS check, CSRF check, Role check) is a handler in the chain. Servlet Filters also follow this pattern.

**When to use:**
- Multiple objects may handle an event, and the handler is determined at runtime
- You want to decouple the sender from the receiver
- The set of handlers needs to be configurable (especially in pipelines and workflows)

```java
// ✅ Real-world: Payment Request Validation Chain
// Each handler validates one concern and passes to the next

// Abstract base handler defining the chain structure
public abstract class ValidationHandler {
    private ValidationHandler next; // Pointer to the next handler in the chain

    public ValidationHandler setNext(ValidationHandler next) {
        this.next = next;
        return next; // Returns next to allow fluent chaining: a.setNext(b).setNext(c)
    }

    // Each subclass must implement this
    public abstract ValidationResult handle(PaymentRequest request);

    // Helper: pass to next handler, or return valid if end of chain
    protected ValidationResult passToNext(PaymentRequest request) {
        if (next != null) return next.handle(request);
        return ValidationResult.valid(); // Reached the end — all checks passed
    }
}

// Handler 1: Checks the amount is positive
class AmountValidator extends ValidationHandler {
    @Override
    public ValidationResult handle(PaymentRequest request) {
        if (request.getAmount().compareTo(BigDecimal.ZERO) <= 0) {
            return ValidationResult.invalid("Amount must be positive"); // Short-circuit
        }
        return passToNext(request); // Amount is fine — pass to next handler
    }
}

// Handler 2: Checks currency is supported
class CurrencyValidator extends ValidationHandler {
    private static final Set<String> SUPPORTED = Set.of("USD", "EUR", "INR", "GBP");

    @Override
    public ValidationResult handle(PaymentRequest request) {
        if (!SUPPORTED.contains(request.getCurrency())) {
            return ValidationResult.invalid("Currency not supported: " + request.getCurrency());
        }
        return passToNext(request);
    }
}

// Handler 3: Validates card via Luhn algorithm
class CardValidator extends ValidationHandler {
    @Override
    public ValidationResult handle(PaymentRequest request) {
        if (!luhnCheck(request.getCardNumber())) {
            return ValidationResult.invalid("Invalid card number");
        }
        return passToNext(request);
    }
}

// Wire the chain (order can be changed anytime without changing handlers)
ValidationHandler chain = new AmountValidator();
chain.setNext(new CurrencyValidator())
     .setNext(new CardValidator())
     .setNext(new FraudDetectionValidator());

ValidationResult result = chain.handle(paymentRequest);
```

---

### 14. Command Pattern

#### 📖 Theory:
**What:** Encapsulates a **request as an object**, allowing you to parameterize clients with different requests, queue or log requests, and support **undoable operations**.

**Why it exists:** The Command pattern decouples the object that invokes the operation (Invoker) from the object that knows how to execute it (Receiver). This enables:
- **Undo/Redo** (store command history, call `undo()`)
- **Queuing** (put commands in a queue, execute asynchronously)
- **Logging** (serialize commands to disk for audit trail or crash recovery)
- **Macro recording** (record a sequence of commands, play back)

**Real-world Java:** `Runnable` is a command. `ExecutorService.submit(Runnable)` is an invoker that queues commands. Spring Batch Steps are commands. JPA's Unit of Work (session-based dirty tracking) is essentially a deferred command queue.

```java
// The Command interface — every operation is encapsulated as a Command
public interface Command {
    void execute();
    void undo(); // Reversal of execute()
    String getDescription(); // For logging/audit trail
}

// A Concrete Command: Encapsulates a money transfer action
@RequiredArgsConstructor
public class TransferMoneyCommand implements Command {
    private final BankAccount fromAccount;
    private final BankAccount toAccount;
    private final BigDecimal amount;
    private final String referenceId;

    @Override
    public void execute() {
        fromAccount.debit(amount);                            // Take money from source
        toAccount.credit(amount);                             // Give money to destination
        log.info("[CMD-EXEC] Transfer {} from {} to {} [ref={}]",
            amount, fromAccount.getId(), toAccount.getId(), referenceId);
    }

    @Override
    public void undo() {
        toAccount.debit(amount);                              // Reverse: take money back from destination
        fromAccount.credit(amount);                           // Reverse: return money to source
        log.warn("[CMD-UNDO] Reversed transfer {} [ref={}]", amount, referenceId);
    }

    @Override
    public String getDescription() {
        return String.format("Transfer %s from account %s to %s",
            amount, fromAccount.getId(), toAccount.getId());
    }
}

// Invoker: Manages a history of executed commands to support undo
@Service
public class TransactionManager {
    private final Deque<Command> history = new LinkedList<>();

    // Execute a command and store it in history
    public void execute(Command cmd) {
        cmd.execute();
        history.push(cmd);         // Push to front of deque (LIFO)
        auditLog.record(cmd.getDescription()); // Log every command
    }

    // Undo the most recent command
    public void undoLast() {
        if (!history.isEmpty()) {
            Command last = history.pop();
            last.undo();
        }
    }

    // Redo support: move to "undone" stack and re-execute
    public List<String> getAuditTrail() {
        return history.stream()
            .map(Command::getDescription)
            .collect(Collectors.toList());
    }
}
```

---

## 📋 Patterns Quick Reference — Interview Cheat Sheet

| Pattern | Category | Key Idea | Real-World Use Case |
|---------|---------|---------|---------------------|
| Singleton | Creational | One instance only | DB Connection Pool, Config Manager |
| Builder | Creational | Step-by-step construction | HttpRequest, Lombok @Builder, SQL QueryBuilder |
| Factory Method | Creational | Delegate object creation | PaymentProcessorFactory, Spring Bean creation |
| Abstract Factory | Creational | Families of objects | UI Theme factories (Material, Dark Mode) |
| Prototype | Creational | Clone instead of create | Report templates, Graphical shapes |
| Adapter | Structural | Interface conversion | Legacy integrations, Third-party SDKs |
| Decorator | Structural | Wrap to add behavior | Logging/Caching/Retry wrappers, Java I/O streams |
| Proxy | Structural | Control access | Spring @Transactional, Hibernate lazy loading |
| Facade | Structural | Simplify complex system | OrderFacade, Service orchestration layer |
| Observer | Behavioral | Notify all dependents | Spring Events, Kafka Pub/Sub |
| Strategy | Behavioral | Swappable algorithms | Discount strategies, Sort algorithms |
| Template Method | Behavioral | Define algorithm skeleton | JdbcTemplate, Spring Batch Steps |
| Chain of Responsibility | Behavioral | Pipeline of handlers | Spring Security FilterChain, Validation Pipelines |
| Command | Behavioral | Encapsulate as object | Undo/Redo, Job queues, Audit logging |

---

## 🎯 Cross-Questioning Scenarios

### Q: "You mentioned using the Factory pattern. Why not just use Spring's `@Qualifier` to inject the right bean directly?"
> **Answer:** "`@Qualifier` works only when the bean-to-inject is known at compile time. The Factory pattern solves a runtime problem: the correct processor depends on data available only at request time (e.g., the user's chosen payment method from the POST body). We can't `@Qualifier` on a runtime variable. The Factory reads that runtime value, looks up the right Spring-managed bean, and returns it."

### Q: "How does Spring's AOP Proxy relate to the Proxy Pattern, and what's its limitation?"
> **Answer:** "Spring wraps every `@Transactional`, `@Cacheable`, and `@Async` bean in a CGLIB or JDK Dynamic Proxy at startup. Calls to those methods go through the proxy, which opens transactions, manages caches, or delegates to async threads before/after calling your real method. The key limitation: this only works for calls coming FROM OUTSIDE the bean. If method A inside the same class calls method B (also `@Transactional`) on `this` directly, it bypasses the proxy entirely, so method B's transaction annotation has no effect. This is called self-invocation and requires injecting `ApplicationContext.getBean()` to self-inject the proxy, which is an anti-pattern."

### Q: "When would you use Decorator vs Inheritance to add new behavior?"
> **Answer:** "Inheritance is static — the behavior is fixed at compile time and affects all instances of the subclass. Decoration is dynamic — behavior is applied at runtime and can be mixed and matched. Use Inheritance when there is a genuine IS-A relationship and the subclass is always guaranteed to want the behavior. Use Decoration when you have multiple optional, combinable behaviors (like Logging AND Caching AND Metrics on a repository). With 3 features and inheritance, you'd need `LoggingCachingMetricsRepository` as a class. With decoration, you wrap at runtime and can pick any combination."
