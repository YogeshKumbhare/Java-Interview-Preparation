# 🏛️ SOLID Principles — Deep Dive (Theory + Code + Cross-Questions)
## Target: 12+ Years Experience

---

## 📖 What are the SOLID Principles?

**SOLID** is an acronym coined by Robert C. Martin ("Uncle Bob") for five object-oriented design principles that, when applied together, help build software that is:
- **Maintainable:** Easy to change in one place without breaking others
- **Testable:** Units can be tested in isolation
- **Extensible:** New features added without modifying working code
- **Readable:** Clear responsibilities at every level

At the 12-year level, interviewers don't just ask if you know SOLID — they ask you to **identify violations in code they show you**, explain *why* it's a violation, and *how* it cascades into real production problems.

| Letter | Principle | Core Idea |
|--------|-----------|-----------|
| **S** | Single Responsibility Principle | A class should have only ONE reason to change |
| **O** | Open/Closed Principle | Open for extension, Closed for modification |
| **L** | Liskov Substitution Principle | Subtypes must be replaceable for their base types |
| **I** | Interface Segregation Principle | Clients should not depend on interfaces they don't use |
| **D** | Dependency Inversion Principle | Depend on abstractions, not concrete implementations |

---

## S — Single Responsibility Principle (SRP)

### 📖 Theory:
**What it means:** A class should have **one reason to change** — meaning it should be responsible for one logical unit of behavior. "Reason to change" means a change in business requirements that forces this specific class to be edited.

**Why it matters:** When a class handles multiple concerns (validation, persistence, email, logging), each concern's change mandate touches the same class. A schema change, email template update, and log format change all collide in one file, creating merge conflicts, unexpected breakages, and massive classes that are impossible to unit-test.

**Real-world impact:** Classes violating SRP tend to grow to 1000+ lines, become the "God Class" that every developer fears changing, and have near-zero unit test coverage because mocking 10+ collaborators is too complex.

**Analogy:** A Chef who also cleans the restaurant, manages payroll, and fixes plumbing. When the kitchen gets a new stove, the Chef who does everything needs to adapt. The health inspector, manager, AND plumber are also affected. Singleresponsibility: hire a separate cleaner, accountant, and plumber.

### ❌ Violation:
```java
// This class has FOUR reasons to change:
// 1. Validation rules change (new password policy)
// 2. Database schema changes
// 3. Email template/provider changes (Sendgrid → SES)
// 4. Log format changes (plain text → JSON)
public class UserService {
    public void registerUser(User user) {
        // 1. Validate — UserService concern? Maybe
        if (user.getEmail() == null) throw new ValidationException("Email required");
        if (user.getPassword().length() < 8) throw new ValidationException("Weak password");

        // 2. Save to DB — UserService concern? Yes
        userRepo.save(user);

        // 3. Send welcome email — ❌ Not UserService's job!
        // When email provider changes from SMTP to SES, this class breaks
        emailSender.send(user.getEmail(), "Welcome!", buildWelcomeBody(user));

        // 4. Log to file — ❌ Also not UserService's job!
        // When log format changes to JSON, this class breaks
        logger.writeToFile("User registered: " + user.getId());
    }
}
```

### ✅ Correct — Each class has one job:
```java
// UserService: ONLY orchestrates user registration
@Service
public class UserService {
    private final UserRepository userRepo;
    private final UserValidator validator;
    private final ApplicationEventPublisher publisher;

    public User registerUser(User user) {
        validator.validate(user);                 // Delegate to dedicated validator
        User saved = userRepo.save(user);          // DB is UserService's concern
        publisher.publishEvent(new UserRegisteredEvent(this, saved)); // Decouple notifications
        return saved;
    }
}

// UserValidator: ONLY handles validation rules
@Component
public class UserValidator {
    public void validate(User user) {
        if (user.getEmail() == null) throw new ValidationException("Email required");
        if (user.getPassword().length() < 8) throw new ValidationException("Weak password");
        // When password policy changes, ONLY this class changes
    }
}

// WelcomeEmailListener: ONLY sends welcome email (triggered by event)
@Component
public class WelcomeEmailListener {
    private final EmailService emailService;

    @EventListener
    @Async  // Doesn't block main registration flow
    public void onUserRegistered(UserRegisteredEvent event) {
        emailService.sendWelcome(event.getUser());
        // When email provider changes, ONLY this class changes
    }
}
```

**Interview Cross-Questions:**
> **Q: "SRP says one reason to change. But UserService now orchestrates validation, saving, and event publishing. Isn't that three responsibilities?"**
> A: "The key is the abstraction level. `UserService.registerUser()` has exactly one responsibility at the business layer: **coordinating the user registration workflow**. It doesn't implement validation, it doesn't implement email sending — it delegates to dedicated classes. A manager who delegates to specialists still has one job: coordinate the team. The 'reason to change' test applies: if the email provider changes, does `UserService` change? No — only `WelcomeEmailListener`. That's the proof."

---

## O — Open/Closed Principle (OCP)

### 📖 Theory:
**What it means:** Software entities should be **open for extension** (new behavior can be added) but **closed for modification** (existing, tested code is not touched).

**Why it matters:** Every time you modify a working, tested class to add a new case, you risk breaking existing behavior. In production systems processing hundreds of thousands of transactions, a bug introduced by an edit to a core class can be catastrophic. OCP says: don't touch the core. Add new classes instead.

**How to achieve it:** Through abstractions (interfaces, abstract classes) and the Strategy or Decorator pattern. New cases are new implementations of the interface, not new if-else branches.

**Real-world trigger:** "We need to support a new payment method" / "We need a new report format" / "We have a new customer tier". If adding this requires modifying the core engine — OCP is violated. If it only requires adding new classes — OCP is upheld.

**Analogy:** A plug socket. You can plug in any new device (extension) without rewiring the socket (modification). The socket's API (3-pin standard) is closed. The number of devices you can plug in is open.

### ❌ Violation — adding new type requires MODIFYING existing class:
```java
// Adding a new customer tier (e.g., "PLATINUM") requires:
// 1. Finding this class (risk of introducing regression)
// 2. Editing the if-else chain
// 3. Re-testing ALL existing cases
// 4. Hoping no other developer touched this file simultaneously
public class DiscountCalculator {
    public BigDecimal calculate(Order order) {
        if (order.getType().equals("REGULAR")) {
            return order.getTotal().multiply(BigDecimal.valueOf(0.95));
        } else if (order.getType().equals("PREMIUM")) {
            return order.getTotal().multiply(BigDecimal.valueOf(0.80));
        } else if (order.getType().equals("VIP")) {
            return order.getTotal().multiply(BigDecimal.valueOf(0.70));
            // Adding "PLATINUM" means editing HERE — dangerous!
        }
        return order.getTotal();
    }
}
```

### ✅ Correct — Add new types by adding new CLASSES, not modifying existing:
```java
// The contract — never changes
public interface DiscountStrategy {
    BigDecimal calculate(Order order);
    boolean appliesTo(String orderType);
}

// Existing strategies — NEVER TOUCHED when adding new ones
@Component
public class RegularDiscount implements DiscountStrategy {
    @Override public BigDecimal calculate(Order order) { return order.getTotal().multiply(BigDecimal.valueOf(0.95)); }
    @Override public boolean appliesTo(String type) { return "REGULAR".equals(type); }
}

@Component
public class PremiumDiscount implements DiscountStrategy {
    @Override public BigDecimal calculate(Order order) { return order.getTotal().multiply(BigDecimal.valueOf(0.80)); }
    @Override public boolean appliesTo(String type) { return "PREMIUM".equals(type); }
}

// ✅ NEW REQUIREMENT: just add a new class! Zero changes to existing code!
@Component
public class PlatinumDiscount implements DiscountStrategy {
    @Override public BigDecimal calculate(Order order) { return order.getTotal().multiply(BigDecimal.valueOf(0.60)); }
    @Override public boolean appliesTo(String type) { return "PLATINUM".equals(type); }
}

// DiscountCalculator: Never changes — Spring DI auto-discovers all implementations
@Service
public class DiscountCalculator {
    private final List<DiscountStrategy> strategies; // Spring injects ALL DiscountStrategy beans

    public DiscountCalculator(List<DiscountStrategy> strategies) {
        this.strategies = strategies;
    }

    public BigDecimal calculate(Order order) {
        return strategies.stream()
            .filter(s -> s.appliesTo(order.getType()))
            .findFirst()
            .map(s -> s.calculate(order))
            .orElse(order.getTotal()); // No discount if type unrecognized
    }
}
```

---

## L — Liskov Substitution Principle (LSP)

### 📖 Theory:
**What it means:** If `S` is a subtype of `T`, then objects of type `T` may be **replaced** with objects of type `S` without altering any of the desirable properties of the program. In plain English: a subclass must be **usable anywhere its parent class is used**, without the calling code knowing or breaking.

**Why it matters:** LSP violations break polymorphism. Code that appears to work via an abstract base class breaks at runtime when a specific subtype is injected. These bugs are notoriously hard to find because the issue is in the contract — not syntax or compile-time.

**Warning signs of LSP violation:**
- A subclass throws `UnsupportedOperationException` for a method it was forced to inherit
- A subclass overrides a method by making it do nothing (empty method body)
- A subclass strengthens preconditions (requires MORE of the caller) or weakens postconditions (promises LESS)

**Analogy:** You can substitute a rechargeable battery for a regular AA battery in a TV remote. Both fulfill the "Battery" contract of providing power. A USB power bank that only works when plugged into a wall violates the substitution — it's a different kind of power source, not a true battery.

### ❌ Violation — classic Rectangle/Square:
```java
class Rectangle {
    protected int width, height;
    public void setWidth(int w) { this.width = w; }
    public void setHeight(int h) { this.height = h; }
    public int area() { return width * height; }
}

class Square extends Rectangle {
    // A Square has equal sides — forces both dimensions to stay equal
    @Override
    public void setWidth(int w) {
        this.width = w;
        this.height = w; // ❌ BREAKS LSP — callers don't expect this!
    }
    @Override
    public void setHeight(int h) {
        this.width = h;
        this.height = h; // ❌ Same — changes width when setting height!
    }
}

// LSP VIOLATION: Code expecting Rectangle breaks with Square subtype
void testRectangle(Rectangle rect) {
    rect.setWidth(5);
    rect.setHeight(10);
    assert rect.area() == 50; // ✅ Passes for Rectangle
    // ❌ FAILS for Square: setHeight(10) also sets width=10, area=100, not 50!
}

testRectangle(new Rectangle()); // ✅ Passes
testRectangle(new Square());    // ❌ AssertionError — LSP violated!
```

### ✅ Correct — Banking example where all subtypes are safely substitutable:
```java
public abstract class BankAccount {
    protected BigDecimal balance;

    public BigDecimal getBalance() { return balance; }

    // Precondition: amount > 0 (documented in abstract class contract)
    public void deposit(BigDecimal amount) {
        if (amount.compareTo(BigDecimal.ZERO) <= 0)
            throw new IllegalArgumentException("Deposit must be positive");
        this.balance = this.balance.add(amount);
    }

    public abstract void withdraw(BigDecimal amount);
}

public class SavingsAccount extends BankAccount {
    @Override
    public void withdraw(BigDecimal amount) {
        // Precondition same as parent's contract
        if (amount.compareTo(balance) > 0) throw new InsufficientFundsException();
        this.balance = this.balance.subtract(amount);
    }
}

public class OverdraftAccount extends BankAccount {
    private final BigDecimal overdraftLimit;

    @Override
    public void withdraw(BigDecimal amount) {
        // Weakens precondition safely: allows more scenarios than SavingsAccount
        // but still fulfills the parent's original contract (amount > 0 required)
        BigDecimal availableFunds = balance.add(overdraftLimit);
        if (amount.compareTo(availableFunds) > 0) throw new InsufficientFundsException("Exceeds limit");
        this.balance = this.balance.subtract(amount);
    }
}

// ✅ LSP compliant: any subtype of BankAccount works correctly here
// The calling code doesn't care if it's a Savings or Overdraft account
public void processRefund(BankAccount account, BigDecimal amount) {
    account.deposit(amount); // Works correctly for ANY BankAccount subtype
}
```

**Interview Cross-Questions:**
> **Q: "LSP says subtypes must satisfy parent contracts. But what if business requirements FORCE a subtype to behave differently?"**
> A: "That's a strong signal that inheritance is the wrong relationship. If a subtype cannot honestly fulfill its parent's contract, they are NOT in a true IS-A relationship. The fix is to **break the inheritance** and use composition or a different abstraction. In the Square/Rectangle case: Extract a common `Shape` interface with an `area()` method but NO `setWidth()`/`setHeight()`. Rectangle implements Shape. Square implements Shape. Neither IS-A the other. They are siblings sharing a common interface — not parent/child."

---

## I — Interface Segregation Principle (ISP)

### 📖 Theory:
**What it means:** Clients should not be forced to depend on interface methods they do not use. Split large interfaces into smaller, **role-specific** ones that define only the operations the specific client needs.

**Why it matters:** When a class is forced to implement meaningless interface methods (throwing `UnsupportedOperationException` or leaving empty bodies), the interface contract is a lie. Callers receive an object claiming it can "eat" and "sleep" but those methods crash at runtime.

**Consequence:** A fat interface creates unnecessary coupling. When an interface's method changes, ALL classes implementing it must be updated — even those that never use that method.

**Analogy:** A TV remote with 50 buttons vs a remote with only the 5 buttons needed for a smart TV. An elderly user (the "client") forced to use the 50-button remote must navigate 45 buttons they will never press. ISP says: only expose the buttons the user actually needs.

### ❌ Violation:
```java
public interface Worker {
    void work();
    void eat();       // ❌ Machines don't eat! This forces Robots to implement it.
    void sleepNight(); // ❌ Machines don't sleep! Forced onto Robots.
}

public class Robot implements Worker {
    @Override public void work() { /* Efficient, 24/7 */ }
    @Override public void eat() {
        throw new UnsupportedOperationException("Robots don't eat!"); // ❌ Lie in the contract
    }
    @Override public void sleepNight() {
        throw new UnsupportedOperationException("Robots don't sleep!"); // ❌ Lie
    }
}
```

### ✅ Correct — Segregated role-based interfaces:
```java
// Three small, focused interfaces
public interface Workable {
    void work();
}

public interface Eatable {
    void eat();
    void takeLunchBreak();
}

public interface Restable {
    void sleepNight();
    void takeVacation();
}

// Human implements all three (it IS-A all three role types)
public class HumanEmployee implements Workable, Eatable, Restable {
    @Override public void work() { /* works 8 hours */ }
    @Override public void eat() { /* eats lunch */ }
    @Override public void takeLunchBreak() { /* 30-min break */ }
    @Override public void sleepNight() { /* sleeps 7 hours */ }
    @Override public void takeVacation() { /* annual leave */ }
}

// Robot ONLY implements what it uses — no forced empty methods!
public class Robot implements Workable {
    @Override public void work() { /* works 24/7 without breaks! */ }
}
```

### Real-world: Repository pattern with ISP
```java
// Segregated by operation type (READ vs WRITE)
public interface ReadRepository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    Page<T> findAll(Pageable pageable);
}

public interface WriteRepository<T> {
    T save(T entity);
    void delete(T entity);
    void deleteById(Long id);
}

// CQRS Command side: only needs writes (cannot accidentally read stale data)
@Repository
public class OrderCommandRepository implements WriteRepository<Order> {
    // Only save/delete operations available
}

// CQRS Query side: only needs reads (no risk of writes from analytics code)
@Repository
public class OrderQueryRepository implements ReadRepository<OrderView, String> {
    // Only findById/findAll operations available
}

// Full CRUD: Standard service needing both (explicitly declares both roles)
public interface OrderRepository extends ReadRepository<Order, Long>, WriteRepository<Order> {}
```

---

## D — Dependency Inversion Principle (DIP)

### 📖 Theory:
**What it means:** Two rules:
1. **High-level modules** (business logic) should NOT depend on **low-level modules** (implementations). Both should depend on **abstractions** (interfaces).
2. **Abstractions** should not depend on details. **Details** (concrete implementations) should depend on abstractions.

**Why it matters:** When a high-level business service (`OrderService`) directly instantiates a concrete class (`new MySQLOrderRepository()`), they are tightly coupled. Changing the database (PostgreSQL → MongoDB) → change `OrderService`. Running a unit test without a database → impossible. Deploying to a test environment with an in-memory DB → requires code changes.

**DIP is the foundation of Dependency Injection (DI).** Spring's entire `@Autowired` / `@Bean` system exists to implement DIP at the framework level. You program to interfaces; Spring wires the concrete implementation at runtime.

**Analogy:** A lamp is designed to use electricity via a standardized plug (the abstraction). It doesn't care if the electricity comes from a nuclear plant, solar panels, or a wind turbine (the implementations). The lamp depends on the "electricity plug" abstraction, not on any specific power source.

### ❌ Violation — tightly coupled to concrete classes:
```java
public class OrderService {
    // Directly depends on concrete classes — tightly coupled!
    // If you need to switch from MySQL to PostgreSQL, you modify THIS BUSINESS CLASS
    private MySQLOrderRepository orderRepository = new MySQLOrderRepository("jdbc:mysql://...");
    private StripePaymentGateway paymentGateway = new StripePaymentGateway("sk_prod_...");

    public void processOrder(Order order) {
        orderRepository.save(order);
        paymentGateway.charge(order);
        // Unit testing this without a MySQL DB and Stripe account = impossible!
    }
}
```

### ✅ Correct — Depend on abstractions, let the framework wire implementations:
```java
// ABSTRACTIONS (interfaces) — defined in the domain/core layer
public interface OrderRepository {
    Order save(Order order);
    Optional<Order> findById(String id);
}

public interface PaymentGateway {
    PaymentResult charge(Payment payment);
}

// HIGH-LEVEL MODULE — depends ONLY on interfaces, not implementations
@Service
public class OrderService {
    private final OrderRepository orderRepository; // Interface!
    private final PaymentGateway paymentGateway;   // Interface!

    // Spring (or a test) injects the concrete implementation via this constructor
    public OrderService(OrderRepository repo, PaymentGateway gateway) {
        this.orderRepository = repo;
        this.paymentGateway = gateway;
    }

    public OrderResult processOrder(Order order) {
        Order saved = orderRepository.save(order);
        PaymentResult payment = paymentGateway.charge(saved.getPayment());
        return new OrderResult(saved, payment);
    }
}

// LOW-LEVEL MODULES — concrete implementations of the abstractions
// Swap DB engine without touching OrderService:
@Repository
@Profile("!test")  // Production: use JPA
public class JpaOrderRepository implements OrderRepository { /* PostgreSQL via JPA */ }

@Repository
@Profile("test")   // Test: use in-memory mock
public class InMemoryOrderRepository implements OrderRepository {
    private final Map<String, Order> store = new ConcurrentHashMap<>();
    @Override public Order save(Order o) { store.put(o.getId(), o); return o; }
    @Override public Optional<Order> findById(String id) { return Optional.ofNullable(store.get(id)); }
}

// Swap payment gateway via config:
@Service
@ConditionalOnProperty(name = "payment.gateway", havingValue = "stripe")
public class StripePaymentGateway implements PaymentGateway { /* Stripe API */ }

@Service
@ConditionalOnProperty(name = "payment.gateway", havingValue = "razorpay")
public class RazorpayPaymentGateway implements PaymentGateway { /* Razorpay API */ }
```

**Interview Cross-Questions:**
> **Q: "Spring's @Autowired already handles DIP automatically. So do we even need to think about DIP if we use Spring?"**
> A: "Spring handles the wiring, but DIP is about HOW we write our code, not what framework we use. If we `@Autowired private JpaOrderRepository repo` (the concrete class instead of the interface), we've violated DIP even inside a Spring app. Spring can still inject it, but now `OrderService` is tightly coupled to JPA. We cannot swap it for an in-memory store in tests or a MongoDB store in production without changing `OrderService`. DIP requires that the field declarations are `private final OrderRepository repo` (interface). Spring is the DI container that makes DIP enforcement practical at scale."

---

## Interview Q: "How have you applied SOLID in your real projects?"

### Sample STAR-format answer for a 12-year senior:

```
Situation:
"Our legacy payment microservice had a single PaymentService class with 1,200 lines.
It handled validation, processing, fraud detection, notification, and reporting.
Every change needed 3 developers reviewing 1200-line diffs. Test coverage was 18%."

Task:
"I led the refactoring as part of a 3-sprint technical debt reduction initiative."

Action:
"Applying SRP: Split into PaymentValidationService, PaymentProcessingService,
NotificationOrchestrationService, and FraudDetectionService.

Applying OCP: Replaced 15-case if-else payment method chain with PaymentProcessor
interface. New methods (UPI, BNPL) became new classes. Existing code zero-touch.

Applying DIP: Introduced PaymentGateway interface, allowing Stripe Europe and
Razorpay India deployments to swap without touching business logic.

Applying ISP: Split the monolithic PaymentRepository into ReadablePaymentRepository
and WritablePaymentRepository, enabling read-replicas for analytics queries."

Result:
"Test coverage went from 18% to 79%. Time to add a new payment method dropped from
3 weeks to 2 days. Production incidents from this module dropped by 60% in 6 months."
```

---

## SOLID Quick Reference Table

| Principle | One-Liner | Violation Warning Signs | Fix |
|-----------|-----------|------------------------|-----|
| **S**RP | One reason to change | Class > 200 lines, multiple dependencies | Extract into focused classes |
| **O**CP | Add, don't edit | `if (type.equals("X"))` chains | Interface + Strategy pattern |
| **L**SP | Subtypes must substitute | `UnsupportedOperationException` in subclass | Break inheritance, use composition |
| **I**SP | Don't force unused methods | Empty or UnsupportedOperation impls | Split large interface into roles |
| **D**IP | Depend on abstractions | `new ConcreteClass()` in business logic | Inject interfaces, not concrete |
