# ☕ Java Core — Deep Dive Interview Q&A (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Java?

Java is a **platform-independent, object-oriented, high-level programming language** developed by Sun Microsystems (now Oracle) in 1995. The core philosophy is **"Write Once, Run Anywhere" (WORA)** — Java source code is compiled into **bytecode** (.class files), which runs on any machine that has a JVM (Java Virtual Machine).

### Why Java is still dominant after 29 years:
- **JVM Ecosystem** — enormous ecosystem of libraries, frameworks, and tools
- **Enterprise Stability** — banks, insurance, government run on Java (billions of transactions/day)
- **Backward Compatibility** — code written in Java 5 still compiles on Java 22
- **Strong Typing + Garbage Collection** — developer productivity with safety
- **Concurrency Support** — from threads to virtual threads (Project Loom)
- **Community** — 12+ million developers worldwide

---

## 📖 What is Object-Oriented Programming (OOP)?

OOP is a programming paradigm that organizes software design around **objects** (data + behavior) rather than functions and logic. Java is fundamentally an OOP language.

### The 4 Pillars of OOP:

### 1. Encapsulation
**Theory:** Encapsulation is the bundling of data (fields) and methods that operate on that data into a single unit (class), and restricting direct access to some components. It's like a **capsule** — the medicine is inside, you only interact with the capsule surface.

**Why it matters:** It protects internal state from unintended modification. If you change internal implementation, external code doesn't break.

```java
// ❌ Without Encapsulation — anyone can corrupt data
public class BankAccount {
    public double balance; // Anyone can set balance = -1000!
}

// ✅ With Encapsulation — data is protected
public class BankAccount {
    private double balance; // Hidden from outside

    public void deposit(double amount) {
        if (amount <= 0) throw new IllegalArgumentException("Amount must be positive");
        this.balance += amount;
    }

    public void withdraw(double amount) {
        if (amount > balance) throw new InsufficientFundsException();
        this.balance -= amount;
    }

    public double getBalance() { return balance; } // Read-only access
}
```

**Real-world analogy:** An ATM machine. You interact with the screen buttons (public methods), but you can't directly access the cash vault (private fields). The ATM validates your request (withdrawal amount ≤ balance) before giving cash.

---

### 2. Inheritance
**Theory:** Inheritance allows a class to **inherit** (reuse) properties and methods from another class. The child class (subclass) extends the parent class (superclass). It establishes an **"IS-A" relationship**.

**Why it matters:** Code reuse, polymorphism foundation, and establishing type hierarchies.

```java
// Parent (Superclass)
public class Employee {
    protected String name;
    protected double baseSalary;

    public Employee(String name, double baseSalary) {
        this.name = name;
        this.baseSalary = baseSalary;
    }

    public double calculatePay() {
        return baseSalary;
    }
}

// Child (Subclass) — inherits all fields and methods
public class Manager extends Employee {
    private double bonus;

    public Manager(String name, double baseSalary, double bonus) {
        super(name, baseSalary); // Call parent constructor
        this.bonus = bonus;
    }

    @Override
    public double calculatePay() {
        return baseSalary + bonus; // Override parent method
    }
}

// Manager IS-A Employee
Employee emp = new Manager("John", 100000, 20000); // Polymorphism
System.out.println(emp.calculatePay()); // 120000 — Manager's method called
```

---

### 3. Polymorphism
**Theory:** Polymorphism means **"many forms"**. The same method call can exhibit different behaviors depending on the actual object type. There are two types:

- **Compile-time (Static)**: Method overloading — same method name, different parameters
- **Runtime (Dynamic)**: Method overriding — child class provides its own implementation

```java
// COMPILE-TIME: Method Overloading
public class Calculator {
    public int add(int a, int b) { return a + b; }
    public double add(double a, double b) { return a + b; }
    public int add(int a, int b, int c) { return a + b + c; }
    // Compiler decides which to call based on argument types
}

// RUNTIME: Method Overriding
public class NotificationService {
    public void send(String message) {
        System.out.println("Generic notification: " + message);
    }
}

public class EmailService extends NotificationService {
    @Override
    public void send(String message) {
        System.out.println("Email: " + message); // Different behavior!
    }
}

public class SMSService extends NotificationService {
    @Override
    public void send(String message) {
        System.out.println("SMS: " + message); // Different behavior!
    }
}

// Polymorphism in action — same method call, different behavior
List<NotificationService> services = List.of(
    new EmailService(), new SMSService()
);

for (NotificationService svc : services) {
    svc.send("Order confirmed!"); // JVM decides at RUNTIME which send() to call
}
// Output:
// Email: Order confirmed!
// SMS: Order confirmed!
```

**Real-world:** A "Pay" button on an e-commerce site. The same "pay()" method is called, but internally it routes to CreditCardPayment, UPIPayment, or WalletPayment based on what the user selected. The calling code doesn't need to know which payment processor is used.

---

### 4. Abstraction
**Theory:** Abstraction is hiding complex implementation details and showing only the essential features. You define **"WHAT"** an object does, not **"HOW"** it does it. Achieved via abstract classes and interfaces.

```java
// Abstraction via interface — defines WHAT, not HOW
public interface Database {
    void save(String data);
    String findById(String id);
    void delete(String id);
}

// Implementation 1 — PostgreSQL does it one way
public class PostgresDatabase implements Database {
    @Override public void save(String data) { /* SQL INSERT */ }
    @Override public String findById(String id) { /* SQL SELECT */ }
    @Override public void delete(String id) { /* SQL DELETE */ }
}

// Implementation 2 — MongoDB does it differently
public class MongoDatabase implements Database {
    @Override public void save(String data) { /* db.collection.insertOne */ }
    @Override public String findById(String id) { /* db.collection.findOne */ }
    @Override public void delete(String id) { /* db.collection.deleteOne */ }
}

// Client code works with the ABSTRACTION — doesn't know if it's Postgres or Mongo
public class UserService {
    private final Database db; // Abstraction!

    public UserService(Database db) { this.db = db; } // Injected at runtime

    public void createUser(String userData) {
        db.save(userData); // Don't care if it's Postgres or Mongo
    }
}
```

---

## Q1: What is the difference between `==` and `.equals()` in Java?

### Theory:
In Java, `==` compares **reference equality** (do both variables point to the same memory location?), while `.equals()` compares **value equality** (do both objects have the same content?).

For **primitive types** (`int`, `double`, etc.), `==` compares actual values.
For **objects** (`String`, `Integer`, custom classes), `==` compares memory addresses.

### Why this matters:
The default `equals()` in `Object` class uses `==` (reference check). You MUST override it in your domain classes for meaningful comparison. If you override `equals()`, you MUST also override `hashCode()` — this is a **contract** in Java. Violating it breaks `HashMap`, `HashSet`, and any hash-based collection.

```java
// REFERENCE vs VALUE comparison
String a = new String("hello");
String b = new String("hello");

System.out.println(a == b);       // false → different objects on heap
System.out.println(a.equals(b));  // true  → same character content

// String Pool (special optimization by JVM)
String c = "hello"; // Goes to String Pool
String d = "hello"; // Reuses same String Pool entry
System.out.println(c == d);       // true → BOTH reference same pool entry

// NEW keyword always creates fresh object on heap
String e = new String("hello"); // Heap object (NOT in pool)
System.out.println(c == e);       // false → pool vs heap
System.out.println(c.equals(e)); // true → same content
```

### String Pool Explained:
The **String Pool** (also called String Intern Pool) is a special memory region inside the JVM heap where Java stores string literals. When you write `"hello"`, the JVM checks if `"hello"` already exists in the pool. If yes, it returns the existing reference. If no, it creates a new entry.

```
JVM Memory:
├── Heap
│   ├── String Pool
│   │   └── "hello" (address: 0x100)
│   ├── new String("hello") → 0x200 (separate object)
│   └── new String("hello") → 0x300 (another separate object)
└── Stack
    ├── c → points to 0x100 (pool)
    ├── d → points to 0x100 (pool — same reference!)
    ├── a → points to 0x200 (heap)
    └── b → points to 0x300 (heap)
```

### Overriding equals() and hashCode() properly:
```java
public class Employee {
    private long id;
    private String name;
    private String department;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;                    // Same reference? Fast return
        if (o == null || getClass() != o.getClass()) return false; // Null or different class
        Employee e = (Employee) o;
        return id == e.id && Objects.equals(name, e.name); // Compare meaningful fields
    }

    @Override
    public int hashCode() {
        return Objects.hash(id, name); // MUST use same fields as equals()!
    }
    // WHY: If two objects are equal, they MUST have the same hashCode.
    // HashMap uses hashCode to find the bucket, then equals to find the entry.
    // If hashCode differs for equal objects → lookup fails → data corruption.
}
```

---

## Q2: Explain Java Memory Model — Heap, Stack, Metaspace

### Theory:
When the JVM starts, it divides memory into several **runtime data areas**. Understanding this is critical for debugging memory leaks, tuning garbage collection, and writing efficient code.

```
JVM Memory Layout:
┌─────────────────────────────────────────────────────┐
│                    JVM Process                       │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │         HEAP (shared across all threads)      │   │
│  │                                               │   │
│  │  ┌─────────────────────────────────────────┐  │   │
│  │  │       Young Generation                   │  │   │
│  │  │  ┌────────┐ ┌────────┐ ┌────────┐      │  │   │
│  │  │  │  Eden  │ │  S0    │ │  S1    │      │  │   │
│  │  │  │ (new)  │ │(surv.) │ │(surv.) │      │  │   │
│  │  │  └────────┘ └────────┘ └────────┘      │  │   │
│  │  └─────────────────────────────────────────┘  │   │
│  │  ┌─────────────────────────────────────────┐  │   │
│  │  │    Old Generation (Tenured)              │  │   │
│  │  │    (long-lived objects that survived     │  │   │
│  │  │     multiple GC cycles)                  │  │   │
│  │  └─────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│                                                      │
│  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │  Metaspace   │  │   Stack (one per thread)     │ │
│  │              │  │  ┌─────────────────────────┐ │ │
│  │ Class meta-  │  │  │ Thread 1 Stack          │ │ │
│  │ data, method │  │  │  [method frame]         │ │ │
│  │ info, static │  │  │  [method frame]         │ │ │
│  │ variables    │  │  │  [local vars, refs]     │ │ │
│  └──────────────┘  │  └─────────────────────────┘ │ │
│                     │  ┌─────────────────────────┐ │ │
│  ┌──────────────┐  │  │ Thread 2 Stack          │ │ │
│  │  Code Cache  │  │  │  [method frame]         │ │ │
│  │  (JIT comp.) │  │  └─────────────────────────┘ │ │
│  └──────────────┘  └──────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Each area explained:

**Heap (shared):**
- All **objects** and **arrays** live here
- Garbage Collector automatically manages this memory
- Divided into Young Gen (short-lived) and Old Gen (long-lived)
- **Young Generation**: New objects are born in **Eden**. If they survive a GC cycle, they move to Survivor spaces (S0/S1), bouncing between them. After N cycles (default 15), they "graduate" to Old Generation.
- Controlled by: `-Xms` (initial), `-Xmx` (maximum)

**Stack (per-thread):**
- Each thread has its **own stack** — not shared
- Stores: method call frames, local variables, method arguments, return addresses
- **LIFO** (Last In, First Out) — when a method returns, its frame is popped
- Stack Overflow? Too many recursive calls → `StackOverflowError`
- Controlled by: `-Xss` (default ~512KB per thread)

**Metaspace (since Java 8):**
- Replaced **PermGen** (which had fixed size and caused `OutOfMemoryError: PermGen space`)
- Stores: class metadata, method bytecode, static variables' structures
- Lives in **native memory** (not heap) — can grow dynamically
- Controlled by: `-XX:MetaspaceSize`, `-XX:MaxMetaspaceSize`

**Code Cache:**
- JIT (Just-In-Time) Compiler stores compiled native code here
- Hot methods (called frequently) are compiled to native machine code for speed

```java
public class MemoryDemo {
    // 'counter' metadata stored in Metaspace (class-level)
    static int counter = 0;

    public void process() {
        int localVar = 42;              // Stack (local variable)
        String name = "John";           // 'name' reference → Stack; "John" literal → String Pool in Heap
        Employee emp = new Employee();  // 'emp' reference → Stack; Employee object → Heap (Eden)
        List<String> list = new ArrayList<>(); // Reference → Stack; ArrayList object + internal array → Heap
    }
    // When process() returns, its stack frame is DESTROYED
    // The objects on heap are still alive until GC collects them
}
```

### GC Tuning for Production (12-year senior must know):
```bash
# G1 GC (recommended for Java 11+, general purpose)
-XX:+UseG1GC
-Xms2g -Xmx4g                    # Min/max heap (set equal in prod to avoid resizing)
-XX:MaxGCPauseMillis=200          # Target max GC pause
-XX:G1HeapRegionSize=16m
-XX:InitiatingHeapOccupancyPercent=45

# ZGC (Java 15+, ultra-low latency, sub-millisecond pauses)
-XX:+UseZGC
-XX:+ZGenerational                # Java 21+ Generational ZGC

# Shenandoah GC (Red Hat, concurrent evacuation)
-XX:+UseShenandoahGC

# Stack size per thread
-Xss512k                          # Default 512KB, reduce for many threads

# Metaspace
-XX:MetaspaceSize=256m
-XX:MaxMetaspaceSize=512m

# Heap dump on OOM (critical for production debugging)
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/logs/heapdump.hprof
```

---

## Q3: What is the difference between `final`, `finally`, and `finalize()`?

### Theory:
These three keywords look similar but are completely different concepts:

- **`final`** — a **modifier** keyword used to make things **constant/immutable**
- **`finally`** — a **block** used in exception handling that **always executes**
- **`finalize()`** — a **method** called by GC before destroying an object (**DEPRECATED since Java 9**)

```java
// ═══════════ FINAL ═══════════
// Final variable — value cannot change after assignment
final int MAX_CONNECTIONS = 50;  // Constant
// MAX_CONNECTIONS = 100; // ❌ Compile error!

// Final method — subclass cannot override
public class PaymentService {
    public final void validateAmount(BigDecimal amount) {
        // Subclass CANNOT change this validation logic
        if (amount.compareTo(BigDecimal.ZERO) <= 0)
            throw new IllegalArgumentException("Invalid amount");
    }
}

// Final class — CANNOT be extended (no inheritance allowed)
public final class ImmutableConfig {
    // String, Integer, LocalDate are all final classes
}
// class ChildConfig extends ImmutableConfig {} // ❌ Compile error!

// Final reference — reference can't change, but OBJECT CAN be mutated!
final List<String> list = new ArrayList<>();
list.add("hello");     // ✅ OK — modifying the object
// list = new ArrayList<>(); // ❌ Cannot reassign the reference

// ═══════════ FINALLY ═══════════
// Always runs — even if exception or return happens in try/catch
Connection connection = null;
try {
    connection = dataSource.getConnection();
    return processData(connection); // Even with return!
} catch (SQLException ex) {
    log.error("DB error", ex);
    throw new ServiceException("Query failed", ex);
} finally {
    // This ALWAYS runs — essential for cleanup
    if (connection != null) {
        connection.close(); // Release DB connection back to pool
    }
}

// Modern approach: try-with-resources (Java 7+)
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
    // conn.close() and ps.close() called automatically
    // Even on exception!
}

// ═══════════ FINALIZE() ═══════════
// DEPRECATED since Java 9! Do NOT use in new code.
@Override
protected void finalize() throws Throwable {
    // Called by GC before object is destroyed
    // Problems:
    // 1. No guarantee WHEN it will be called
    // 2. No guarantee IF it will be called
    // 3. Slows down GC
    // 4. Can accidentally resurrect the object
}
// Use AutoCloseable + try-with-resources instead
```

---

## Q4: Explain Generics, Type Erasure, and Wildcards

### Theory: What are Generics?
Generics allow you to write **type-safe** code that works with different types. Before generics (Java 1.4 and earlier), collections stored `Object` — you had to cast everything and hope for the best.

**Why Generics exist:** Catch type errors at **compile time** instead of getting `ClassCastException` at runtime.

```java
// BEFORE Generics (Java 1.4) — unsafe!
List list = new ArrayList();
list.add("hello");
list.add(123);        // No error! List accepts anything (Object)
String s = (String) list.get(1); // 💥 ClassCastException at RUNTIME!

// WITH Generics (Java 5+) — safe!
List<String> list = new ArrayList<>();
list.add("hello");
// list.add(123);     // ❌ Compile error! Type safety enforced.
String s = list.get(0); // No cast needed. Compiler guarantees String.
```

### Type Erasure:
**Theory:** Java generics are implemented via **type erasure** — the compiler checks types at compile time, then **removes** (erases) all generic type information for the runtime. At bytecode level, `List<String>` and `List<Integer>` are both just `List<Object>`.

This is why you CANNOT:
- `new T[]` — runtime doesn't know what T is
- `instanceof List<String>` — runtime only sees `List`
- Have `method(List<String>)` and `method(List<Integer>)` as overloads — they're the same after erasure

```java
// At compile time → generics checked
List<String> strings = new ArrayList<>();
strings.add("hello");

// At runtime (after erasure) → generics removed
List strings = new ArrayList();  // Same as List<Object>
strings.add("hello");
```

### Wildcards — PECS Rule:
**PECS = Producer Extends, Consumer Super** — the most important generics rule.

```java
// ═════ UPPER BOUNDED: <? extends Number> — "I produce T" — READ ONLY
public double sumList(List<? extends Number> list) {
    // Can read as Number — all elements ARE Number or its subtype
    double sum = 0;
    for (Number n : list) {
        sum += n.doubleValue(); // Safe read
    }
    // list.add(42); // ❌ Cannot add — compiler doesn't know if list is List<Integer> or List<Double>
    return sum;
}
// Works for: List<Integer>, List<Double>, List<Long>

// ═════ LOWER BOUNDED: <? super Integer> — "I consume T" — WRITE ONLY
public void addNumbers(List<? super Integer> list) {
    list.add(1);    // ✅ Safe — whatever the list is, Integer fits
    list.add(2);
    // Integer n = list.get(0); // ❌ Cannot read as Integer — might be List<Object>
    Object o = list.get(0);     // Only Object is guaranteed
}
// Works for: List<Integer>, List<Number>, List<Object>
```

---

## Q5: Exception Handling — Checked vs Unchecked

### Theory:
Java has a **two-tier exception system**:

1. **Checked Exceptions** — **compiler forces** you to handle them (extends `Exception`). These represent **recoverable conditions** the programmer should anticipate (file not found, network error, DB connection failure).

2. **Unchecked Exceptions** — compiler does NOT force handling (extends `RuntimeException`). These represent **programming bugs** (null pointer, array index out of bounds, class cast).

3. **Errors** — serious JVM-level problems (extends `Error`). **Never catch these** — `OutOfMemoryError`, `StackOverflowError`.

```
                  Throwable
                 /         \
            Error          Exception
           /    \          /        \
    OutOfMemory  StackOverflow  IOException    RuntimeException
                                 /      \         /          \
                         FileNotFound  SQL   NullPointer  ClassCast
                         (Checked)     (C)   (Unchecked)  (Unchecked)
```

```java
// CHECKED — you MUST handle or declare
public byte[] readFile(String path) throws IOException { // Must declare
    return Files.readAllBytes(Path.of(path));
}

// Calling code MUST either:
try {
    readFile("data.txt");
} catch (IOException e) {
    log.error("File not found: {}", e.getMessage());
}
// OR declare in its own signature: throws IOException

// UNCHECKED — compiler doesn't force handling
public int divide(int a, int b) {
    return a / b; // ArithmeticException if b=0 — unchecked
}

// CUSTOM EXCEPTION — production pattern
public class PaymentDeclinedException extends RuntimeException {
    private final String errorCode;
    private final String transactionId;
    private final BigDecimal amount;

    public PaymentDeclinedException(String errorCode, String message,
                                     String transactionId, BigDecimal amount) {
        super(message);
        this.errorCode = errorCode;
        this.transactionId = transactionId;
        this.amount = amount;
    }
    // getters...
}

// Global Exception Handler (Spring Boot)
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(PaymentDeclinedException.class)
    public ResponseEntity<ErrorResponse> handlePaymentDeclined(PaymentDeclinedException ex) {
        return ResponseEntity.status(HttpStatus.PAYMENT_REQUIRED)
            .body(new ErrorResponse(ex.getErrorCode(), ex.getMessage()));
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("Unexpected error", ex);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
            .body(new ErrorResponse("INTERNAL_ERROR", "Something went wrong"));
    }
}
```

---

## Q6: Abstract Class vs Interface — When to use which?

### Theory:
**Abstract Class** = "IS-A" relationship with shared state and behavior. Use when subclasses share common fields and partial implementation.

**Interface** = "CAN-DO" capability contract. Use when you want to define a capability that multiple unrelated classes can implement.

| Feature | Abstract Class | Interface (Java 8+) |
|---------|---------------|---------------------|
| Methods | Abstract + concrete | Abstract + default + static + private (Java 9) |
| Fields | Instance variables, any access | Only `public static final` (constants) |
| Constructor | ✅ Yes | ❌ No |
| Inheritance | **Single** (extends one) | **Multiple** (implements many) |
| Access modifiers | Any (public, protected, private) | Methods are `public` by default |
| When to use | Shared code + state | Define a contract / capability |

```java
// ABSTRACT CLASS — shared state + partial behavior
public abstract class Vehicle {
    protected String brand;        // Instance variable — shared state
    protected int mileage;
    private final String vin;      // Private field

    public Vehicle(String brand, String vin) {  // Constructor
        this.brand = brand;
        this.vin = vin;
    }

    public abstract void startEngine(); // Must be implemented by subclass

    // Concrete method — shared behavior
    public void refuel(int liters) {
        System.out.println("Refueling " + brand + " with " + liters + "L");
    }
}

// INTERFACE — capability contract
public interface GPS {
    String getLocation();                                    // Abstract
    default String getFormattedLocation() {                  // Default (Java 8)
        return "Location: " + getLocation();
    }
    static GPS noGPS() { return () -> "GPS Not Available"; } // Static factory (Java 8)
    private String formatCoordinates(double lat, double lon) { // Private (Java 9)
        return lat + "," + lon;
    }
}

public interface ElectricVehicle {
    int getBatteryLevel();
    default boolean needsCharging() { return getBatteryLevel() < 20; }
}

// A class can extend ONE abstract class + implement MULTIPLE interfaces
public class Tesla extends Vehicle implements GPS, ElectricVehicle {
    private int battery = 100;

    public Tesla(String vin) { super("Tesla", vin); }

    @Override public void startEngine() { System.out.println("Silent electric start"); }
    @Override public String getLocation() { return "37.7749,-122.4194"; }
    @Override public int getBatteryLevel() { return battery; }
}
```

---

## Q7: What is Immutability? How to create an Immutable class?

### Theory:
An **immutable object** is an object whose state **cannot be modified** after it's created. Once constructed, it's frozen forever.

**Why immutability matters (critical for 12-year seniors):**
1. **Thread-safe by default** — no synchronization needed (no one can change state)
2. **Safe as HashMap keys** — hashCode never changes
3. **Cacheable** — can be safely shared and reused
4. **Predictable** — no side effects from unexpected mutation
5. **GC-friendly** — no need to track field mutations

**Rules to create an immutable class:**
1. Class must be `final` (cannot be subclassed)
2. All fields must be `private final`
3. No setter methods
4. Deep copy mutable objects in constructor
5. Return copies (not references) of mutable fields in getters

```java
public final class ImmutableOrder {
    private final String orderId;
    private final BigDecimal amount;
    private final Instant createdAt;
    private final List<String> items; // Mutable type!

    public ImmutableOrder(String orderId, BigDecimal amount, List<String> items) {
        this.orderId = orderId;
        this.amount = amount;
        this.createdAt = Instant.now();
        // Rule 4: DEEP COPY mutable input
        this.items = Collections.unmodifiableList(new ArrayList<>(items));
    }

    public String getOrderId() { return orderId; }          // String is immutable — safe
    public BigDecimal getAmount() { return amount; }         // BigDecimal is immutable — safe
    public Instant getCreatedAt() { return createdAt; }      // Instant is immutable — safe
    public List<String> getItems() { return items; }         // Already unmodifiable — safe

    // NO setters exist — object is frozen
}

// Java 16+ Record — immutable by design!
public record Order(String orderId, BigDecimal amount, List<String> items) {
    // Compact constructor for validation + defensive copy
    public Order {
        Objects.requireNonNull(orderId, "orderId is required");
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        items = List.copyOf(items); // Immutable copy — cannot be modified
    }
}
```

---

## Q8: JVM Architecture and Class Loading

### Theory:
The **JVM (Java Virtual Machine)** is the heart of Java's platform independence. It's a virtual computer that executes Java bytecode. When you write Java code, it goes through:

```
Your Code (.java) → javac compiler → Bytecode (.class) → JVM → Native machine code
```

### JVM Components:
```
┌──────────────────────────────────────────────┐
│               JVM Architecture                │
│                                               │
│  1. CLASS LOADER SUBSYSTEM                    │
│     ┌─────────────────────────────────────┐   │
│     │ Bootstrap ClassLoader (java.*, core) │   │
│     │     ↓                                │   │
│     │ Extension ClassLoader (ext/*.jar)    │   │
│     │     ↓                                │   │
│     │ Application ClassLoader (your code) │   │
│     └─────────────────────────────────────┘   │
│     Phases: Loading → Linking → Initialization │
│             (Verify + Prepare + Resolve)      │
│                                               │
│  2. RUNTIME DATA AREAS                        │
│     • Method Area (Metaspace) — class info    │
│     • Heap — all objects                      │
│     • Stack — per thread, method frames       │
│     • PC Register — current instruction       │
│     • Native Method Stack — C/C++ methods     │
│                                               │
│  3. EXECUTION ENGINE                          │
│     • Interpreter — reads bytecode line by    │
│       line (slow but starts fast)             │
│     • JIT Compiler — compiles "hot" methods   │
│       to native code (fast after warmup)      │
│     • Garbage Collector — manages heap        │
│                                               │
│  4. NATIVE METHOD INTERFACE (JNI)             │
│     • Bridge to C/C++ native libraries        │
└──────────────────────────────────────────────┘
```

### Class Loading — Delegation Model:
The class loader follows **Parent Delegation Model**: Before loading a class, each loader asks its parent. This prevents duplicate class loading and ensures core Java classes (like `java.lang.String`) can't be replaced by malicious code.

```
Application ClassLoader: "Can I load com.company.PaymentService?"
  → asks Extension ClassLoader: "Can you load it?"
    → asks Bootstrap ClassLoader: "Can you load it?"
      → Bootstrap: "No, it's not in java.* or javax.*"
    → Extension: "No, it's not in ext/*"
  → Application: "Yes! I found it in classpath" → LOADS IT
```

---

## Q9: String, StringBuilder, StringBuffer

### Theory:

**String** — **Immutable**. Every modification creates a NEW String object. The old one becomes garbage. Stored in the String Pool for reuse.

**StringBuilder** — **Mutable**. Modifies the same internal character array in-place. **NOT thread-safe**. Use for single-threaded string building.

**StringBuffer** — **Mutable**. Same as StringBuilder but **thread-safe** (methods are `synchronized`). Slower due to synchronization overhead.

```java
// STRING — Immutable (each + creates new object)
String s = "hello";   // String Pool: "hello" created
s = s + " world";     // NEW String "hello world" created
s = s + "!";          // ANOTHER new String "hello world!" created
// 3 String objects created! "hello" and "hello world" are now garbage.

// In a loop — this is DISASTROUS:
String result = "";
for (int i = 0; i < 10000; i++) {
    result += i; // Creates 10,000 String objects! O(n²)
}

// STRINGBUILDER — Mutable (single object, in-place modification)
StringBuilder sb = new StringBuilder(64); // Pre-allocate capacity
for (int i = 0; i < 10000; i++) {
    sb.append(i); // Modifies internal array — O(n) total
}
String result = sb.toString();

// STRINGBUFFER — Thread-safe StringBuilder
StringBuffer sbuf = new StringBuffer();
// Every method is synchronized:
// public synchronized StringBuffer append(String str) { ... }

// Performance ranking (single thread):
// StringBuilder > StringBuffer >>> String concatenation in loops

// Modern Java (9+) optimization:
// Simple concatenation like: "Hello, " + name + "!"
// is optimized by compiler using invokedynamic + StringConcatFactory
// So for simple cases, + operator is fine.
```

---

## Q10: `static` keyword — all use cases

### Theory:
The `static` keyword means **"belongs to the class, not to any instance"**. Static members exist once per class, shared across all objects. They're loaded when the class is first loaded into memory.

```java
public class StaticDemo {

    // ═══ STATIC VARIABLE ═══
    // One copy shared by ALL instances
    static int instanceCount = 0;  // Class-level — in Metaspace

    // ═══ INSTANCE VARIABLE ═══
    String name;  // Each object has its own copy — on Heap

    public StaticDemo(String name) {
        this.name = name;
        instanceCount++; // All instances share this counter
    }

    // ═══ STATIC BLOCK ═══
    // Runs ONCE when class is first loaded by ClassLoader
    static {
        System.out.println("Class StaticDemo loaded into JVM");
        // Good for: loading config, native libraries, one-time setup
    }

    // ═══ STATIC METHOD ═══
    // Called without creating an object
    // Cannot access instance variables or 'this'
    public static int getInstanceCount() {
        return instanceCount;
        // this.name; // ❌ Compile error — no 'this' in static context
    }

    // ═══ STATIC NESTED CLASS ═══
    // Does NOT hold reference to outer class instance
    static class Config {
        String url = "localhost:5432";
        // Can be created without outer class: new StaticDemo.Config()
    }

    // ═══ STATIC IMPORT ═══
    // import static java.lang.Math.PI;
    // import static java.util.Collections.unmodifiableList;
    // Now use: PI instead of Math.PI
}

// Usage:
System.out.println(StaticDemo.getInstanceCount()); // 0 — called on CLASS
new StaticDemo("A");
new StaticDemo("B");
System.out.println(StaticDemo.getInstanceCount()); // 2 — shared counter
```
