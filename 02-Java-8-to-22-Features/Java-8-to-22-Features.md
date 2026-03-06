# 🌿 Java 8 → Java 22 — All Features Deep Dive (Theory + Code + Cross-Questions)
## Target: 12+ Years Experience

---

## 📖 Why Java Versions Matter in Interviews

Java has evolved dramatically from Java 8 (2014) to Java 21 (2023 LTS). At the 12-year level, interviewers expect you to know:
- **What** each feature does and **why** it was introduced
- **What problem** it solves (what was broken/painful before)
- **Trade-offs** and **pitfalls** (e.g., when NOT to use parallel streams)
- **Which versions are LTS** (Long-Term Support) and commonly deployed in enterprise

### LTS Versions roadmap used in production:
| Version | LTS | Widely Used In Production |
|---------|-----|---------------------------|
| Java 8 | ✅ | Huge legacy base — many orgs still on 8 |
| Java 11 | ✅ | Most common enterprise standard (2019-2023) |
| Java 17 | ✅ | Growing adoption (Spring Boot 3.x requires 17+) |
| Java 21 | ✅ | New projects, Virtual Threads |

---

## ☕ JAVA 8 (2014) — The Game Changer

### 1. Lambda Expressions

#### 📖 Theory:
**What:** A Lambda is an anonymous function (a function without a name) that can be passed as an argument or stored in a variable.

**Why it was introduced:** Before Java 8, passing behavior (like a Comparator, Runnable, or event handler) required creating verbose anonymous inner classes every time. This made simple callback-style code extremely noisy.

**How it works:** A Lambda expression implements a **Functional Interface** — an interface with exactly ONE abstract method. The compiler infers the types and creates the implementing class on the fly at compile time.

**Method Reference forms:**
- `String::compareTo` → Instance method (called on first argument)
- `System.out::println` → Instance method on a captured object
- `Integer::parseInt` → Static method
- `MyClass::new` → Constructor reference

```java
// Before Java 8 — verbose anonymous inner class
Comparator<String> comp = new Comparator<String>() {
    @Override
    public int compare(String a, String b) { return a.compareTo(b); }
};

// Java 8 Lambda — (parameters) -> body
Comparator<String> comp = (a, b) -> a.compareTo(b);

// Method reference (even cleaner — when lambda just forwards to an existing method)
Comparator<String> comp = String::compareTo;
```

### 2. Streams API

#### 📖 Theory:
**What:** Streams are a declarative, functional-style API for processing sequences of data.

**Why it was introduced:** Before Streams, processing collections required verbose `for` loops with manual state tracking. Streams provide a pipeline model: Source → Zero or more Intermediate Operations (lazy) → One Terminal Operation (triggers execution).

**Critical properties:**
- **Lazy:** Intermediate operations (`filter`, `map`) are NOT executed until a terminal (`collect`, `findFirst`) is called. A stream that `filter()s` then `findFirst()` stops immediately when the first match is found — does NOT traverse the rest.
- **Non-reusable:** A stream can be consumed ONCE. Calling a terminal operation twice throws `IllegalStateException`.
- **Parallel streams** use `ForkJoinPool.commonPool()`. NOT safe if operations have side effects or shared mutable state.

```java
List<Employee> employees = getEmployees();

// Real-world stream operations
Map<String, Double> avgSalaryByDept = employees.stream()
    .filter(e -> e.isActive())                              // Filter
    .collect(Collectors.groupingBy(                         // Group
        Employee::getDepartment,
        Collectors.averagingDouble(Employee::getSalary)     // Aggregate
    ));

// FlatMap — flatten nested collections
List<Integer> allOrderItems = orders.stream()
    .flatMap(order -> order.getItems().stream())
    .map(Item::getQuantity)
    .collect(Collectors.toList());

// Parallel stream (use with caution!)
long count = employees.parallelStream()
    .filter(e -> e.getSalary() > 100000)
    .count();
```

### 3. Optional — avoid NullPointerException

#### 📖 Theory:
**What:** `Optional<T>` is a container that may or may not hold a non-null value. It forces the caller to explicitly handle the "not found" case instead of risking a `NullPointerException`.

**Why it was introduced:** `NullPointerException` is the most common Java runtime exception (the "billion dollar mistake" as Tony Hoare called it). `Optional` makes the possibility of absence **explicit in the type system** — the caller cannot accidentally treat an `Optional<User>` as a `User`.

**When to use:**
- ✅ Return type of repository methods (`findById` → `Optional<User>`)
- ✅ Configuration lookups where value may not exist
- ❌ Never use as a field, constructor parameter, or method parameter — use regular `null` check or default values
- ❌ Never use in collections — use an empty collection instead

```java
public Optional<User> findByEmail(String email) {
    return userRepo.findByEmail(email); // Returns Optional
}

// Usage
findByEmail("user@company.com")
    .filter(u -> u.isActive())
    .map(User::getName)
    .orElse("Anonymous");

// ⚠️ Anti-patterns
Optional<User> opt = findByEmail(email);
if (opt.isPresent()) {        // ❌ Don't do this — defeats the purpose
    return opt.get();
}
opt.get();                    // ❌ NPE risk if empty
```

### 4. Functional Interfaces

#### 📖 Theory:
**What:** A Functional Interface is any interface with **exactly one abstract method** (it can have default and static methods). The `@FunctionalInterface` annotation enforces this at compile time.

**Why it matters:** Lambdas work only because there is exactly one abstract method — the compiler knows which method the lambda is implementing. The four core functional interfaces from `java.util.function.*` cover virtually all use cases:

| Interface | Signature | Use Case |
|-----------|-----------|----------|
| `Function<T,R>` | T → R | Transform/map a value |
| `Predicate<T>` | T → boolean | Test/filter a value |
| `Consumer<T>` | T → void | Act on a value (side effect) |
| `Supplier<T>` | () → T | Generate/provide a value |

```java
// Built-in functional interfaces
Function<String, Integer>  f = Integer::parseInt;         // T → R
Predicate<String>          p = String::isEmpty;           // T → boolean
Consumer<String>           c = System.out::println;       // T → void
Supplier<String>           s = UUID::randomUUID;          // () → T
BiFunction<String,String,Integer> bf = String::compareTo; // T,U → R

// Custom functional interface
@FunctionalInterface
interface PaymentValidator {
    boolean validate(Payment payment);

    default PaymentValidator and(PaymentValidator other) {
        return p -> this.validate(p) && other.validate(p);
    }
}

// Usage
PaymentValidator validator =
    ((PaymentValidator) p -> p.getAmount() > 0)
    .and(p -> p.getCurrency() != null)
    .and(p -> p.getCardNumber() != null);
```

### 5. Default and Static methods in interfaces
```java
interface PaymentProcessor {
    void process(Payment payment);

    default void processWithLogging(Payment payment) {
        System.out.println("Processing: " + payment.getId());
        process(payment);
        System.out.println("Done: " + payment.getId());
    }

    static PaymentProcessor noOp() {
        return payment -> {}; // Factory
    }
}
```

### 6. Date/Time API (java.time)
```java
// Replaces java.util.Date (which was mutable and broken)
LocalDate today = LocalDate.now();
LocalTime now = LocalTime.now();
LocalDateTime dt = LocalDateTime.now();
ZonedDateTime zdt = ZonedDateTime.now(ZoneId.of("Asia/Kolkata"));

// Date calculations (immutable — returns new instances)
LocalDate nextMonth = today.plusMonths(1);
long days = ChronoUnit.DAYS.between(LocalDate.of(2020, 1, 1), today);

// Parse/Format
DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd-MM-yyyy HH:mm:ss");
LocalDateTime parsed = LocalDateTime.parse("25-01-2024 10:30:00", fmt);
String formatted = parsed.format(fmt);
```

---

## ☕ JAVA 9 (2017)

### 1. Module System (Project Jigsaw)
```java
// module-info.java
module com.mycompany.payment {
    requires java.base;           // Implicit
    requires spring.boot;
    requires com.fasterxml.jackson.databind;

    exports com.mycompany.payment.api;        // Public API
    exports com.mycompany.payment.model;
    // Internal packages NOT exported — strong encapsulation
}
```

### 2. Collection Factory Methods
```java
// Before Java 9
List<String> list = Arrays.asList("a", "b", "c"); // Fixed size, allows null

// Java 9 — Immutable, no nulls allowed
List<String> list = List.of("a", "b", "c");
Set<String> set = Set.of("x", "y", "z");
Map<String, Integer> map = Map.of("one", 1, "two", 2, "three", 3);
Map<String, Integer> map = Map.ofEntries(
    Map.entry("one", 1),
    Map.entry("two", 2)
);
```

### 3. Stream improvements
```java
// takeWhile, dropWhile
List<Integer> nums = List.of(1, 2, 3, 4, 5, 6);
nums.stream().takeWhile(n -> n < 4).toList(); // [1, 2, 3]
nums.stream().dropWhile(n -> n < 4).toList(); // [4, 5, 6]

// Stream.iterate with predicate
Stream.iterate(1, n -> n < 100, n -> n * 2)
      .forEach(System.out::println); // 1, 2, 4, 8, 16, 32, 64
```

---

## ☕ JAVA 10 (2018)

### Local Variable Type Inference `var`
```java
// Before
HashMap<String, List<Order>> orders = new HashMap<String, List<Order>>();

// Java 10
var orders = new HashMap<String, List<Order>>(); // Type inferred

var list = List.of(1, 2, 3);   // List<Integer>
var name = "John";              // String

// NOTE: var only works in local method scope
// NOT allowed: class fields, method params, return types
```

---

## ☕ JAVA 11 (2018) — LTS

### 1. New String methods
```java
" hello ".isBlank();           // true
" hello ".strip();             // "hello" (Unicode-aware trim)
"line1\nline2\nline3".lines()  // Stream<String>
    .collect(Collectors.toList());
"abc".repeat(3);               // "abcabcabc"
```

### 2. Files utility
```java
// Write/Read string directly
Files.writeString(Path.of("test.txt"), "Hello World");
String content = Files.readString(Path.of("test.txt"));
```

### 3. `var` in Lambda
```java
// Java 11 — var in lambda parameters (allows annotations)
list.stream()
    .filter((@NotNull var s) -> !s.isBlank())
    .collect(Collectors.toList());
```

### 4. HTTP Client API (Standard)

#### 📖 Theory:
**What:** A modern, built-in HTTP client that replaces `HttpURLConnection`. Supports HTTP/1.1 and HTTP/2, synchronous and asynchronous requests, WebSocket, and reactive streams.

**Why:** `HttpURLConnection` was from JDK 1.1 (1997) — clunky API, no HTTP/2, no async. Developers used Apache HttpClient or OkHttp. Java 11 provides a standard solution.

```java
// Synchronous GET request
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://api.example.com/users/1"))
    .header("Accept", "application/json")
    .timeout(Duration.ofSeconds(10))
    .GET()
    .build();

HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
System.out.println(response.statusCode()); // 200
System.out.println(response.body());       // JSON string

// Asynchronous POST request
CompletableFuture<HttpResponse<String>> future = client.sendAsync(
    HttpRequest.newBuilder()
        .uri(URI.create("https://api.example.com/orders"))
        .header("Content-Type", "application/json")
        .POST(HttpRequest.BodyPublishers.ofString(
            "{\"item\": \"laptop\", \"qty\": 1}"
        ))
        .build(),
    HttpResponse.BodyHandlers.ofString()
);
future.thenAccept(resp -> System.out.println("Status: " + resp.statusCode()));
```

---

## ☕ JAVA 12 (2019)

### 1. Switch Expressions (Preview — finalized Java 14)
```java
// Preview of new switch syntax (-> arrow form)
String day = "MONDAY";
String type = switch (day) {
    case "MONDAY", "FRIDAY", "SUNDAY" -> "Fun day";
    case "TUESDAY"                    -> "Work day";
    default -> "Unknown";
};
```

### 2. Compact Number Formatting
```java
// Format numbers in human-readable compact form
NumberFormat fmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.SHORT);
System.out.println(fmt.format(1000));      // "1K"
System.out.println(fmt.format(1_000_000)); // "1M"
System.out.println(fmt.format(1_000_000_000)); // "1B"

// Long form
NumberFormat longFmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.LONG);
System.out.println(longFmt.format(1000));  // "1 thousand"
```

### 3. String::indent and String::transform
```java
String text = "Hello\nWorld";
System.out.println(text.indent(4));  // Adds 4 spaces to each line
//     Hello
//     World

// transform() — chain operations
String result = "  hello  "
    .transform(String::strip)
    .transform(String::toUpperCase);
// "HELLO"
```

### 4. Teeing Collector
```java
// Collect into TWO collectors simultaneously and merge results
var result = Stream.of(1, 2, 3, 4, 5)
    .collect(Collectors.teeing(
        Collectors.summingInt(i -> i),  // Sum = 15
        Collectors.counting(),           // Count = 5
        (sum, count) -> "Avg: " + (sum / count) // Merge
    ));
// result = "Avg: 3"
```

---

## ☕ JAVA 13 (2019)

### 1. Text Blocks (Preview — finalized Java 15)
```java
// Preview of multi-line string literals
String json = """
    {
        "name": "John",
        "age": 30
    }
    """;
// More readable than: "{\n  \"name\": \"John\"\n}"
```

### 2. Switch Expressions Enhanced (Second Preview)
```java
// Added `yield` keyword for returning values from block cases
int value = switch (status) {
    case "A" -> 1;
    case "B" -> {
        log("Processing B");
        yield 2;  // yield = return from block in switch expression
    }
    default -> 0;
};
```

### 3. Dynamic CDS Archives
```
Class Data Sharing (CDS):
- Allows sharing class metadata across JVM instances
- Java 13: Dynamic CDS — automatically archives when app exits
- Benefit: Faster startup for subsequent runs (10-20% improvement)

-XX:ArchiveClassesAtExit=app-cds.jsa   # Create archive at shutdown
-XX:SharedArchiveFile=app-cds.jsa       # Use archive at startup
```

---

## ☕ JAVA 14 (2020)

### Records (Preview → Stable in Java 16)

#### 📖 Theory:
**What:** Records are concise, transparent, immutable data carriers. They auto-generate `constructor`, `equals()`, `hashCode()`, and `toString()` based on the declared components.

**Why they were introduced:** Creating a simple DTO (e.g., `UserDTO` with 5 fields) required 50+ lines of boilerplate: getters, `equals()`, `hashCode()`, `toString()`. Developers used Lombok to reduce this. Records provide a standard Java language feature for pure data classes.

**Key constraints:**
- All fields are `private final` — automatically immutable!
- Records implicitly extend `java.lang.Record` — cannot extend another class
- CAN implement interfaces
- CAN add custom methods and compact constructors (for validation)

```java
// Concise immutable data class
record Point(int x, int y) {}

record PaymentDTO(
    String transactionId,
    BigDecimal amount,
    String currency,
    Instant timestamp
) {
    // Compact constructor for validation
    PaymentDTO {
        Objects.requireNonNull(transactionId);
        if (amount.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
    }

    // Custom method
    public boolean isInternational() {
        return !"INR".equals(currency);
    }
}

// Usage
var payment = new PaymentDTO("TX123", BigDecimal.valueOf(100), "USD", Instant.now());
payment.amount();         // Accessor method (no getAmount())
payment.transactionId();  // Getter
```

### Switch Expressions (Stable Java 14)
```java
// Old
String result;
switch (status) {
    case "PENDING": result = "Waiting"; break;
    case "PAID": result = "Completed"; break;
    default: result = "Unknown";
}

// Java 14 Switch Expression
String result = switch (status) {
    case "PENDING" -> "Waiting";
    case "PAID"    -> "Completed";
    default        -> "Unknown";
};

// With return value (complex logic)
int discount = switch (tier) {
    case "GOLD" -> {
        log.info("Gold member");
        yield 20; // yield — return value from block
    }
    case "SILVER" -> 10;
    default -> 0;
};
```

---

## ☕ JAVA 15-16

### Text Blocks
```java
// Old — messy JSON string
String json = "{\n  \"name\": \"John\",\n  \"age\": 30\n}";

// Java 15 Text Block
String json = """
        {
          "name": "John",
          "age": 30
        }
        """;

// SQL queries — game changer!
String query = """
        SELECT u.id, u.name, o.total
        FROM users u
        JOIN orders o ON u.id = o.user_id
        WHERE o.status = 'PAID'
          AND o.created_at >= :startDate
        ORDER BY o.total DESC
        """;
```

---

## ☕ JAVA 17 (2021) — LTS

### Sealed Classes

#### 📖 Theory:
**What:** Sealed classes restrict which other classes may extend or implement them. You explicitly list the allowed subtypes using the `permits` clause.

**Why they were introduced:** Without sealed classes, any class anywhere could extend your `Shape` class and add arbitrary behavior. Sealed classes restore control over the type hierarchy — especially important for algebraic data types and exhaustive pattern matching.

**Key benefit:** When combined with `switch` Pattern Matching, the compiler knows ALL possible subtypes. If you cover all permitted subclasses in a `switch`, there's NO need for a `default` case — the compiler won't even require it. Missing a case becomes a compile error!

```java
// Restrict class hierarchy explicitly
public sealed class Shape
    permits Circle, Rectangle, Triangle {}

public final class Circle extends Shape {
    private final double radius;
    Circle(double radius) { this.radius = radius; }
    public double area() { return Math.PI * radius * radius; }
}

public final class Rectangle extends Shape {
    private final double w, h;
    Rectangle(double w, double h) { this.w = w; this.h = h; }
    public double area() { return w * h; }
}

// Pattern matching with sealed class
double area = switch (shape) {
    case Circle c    -> c.area();
    case Rectangle r -> r.area();
    case Triangle t  -> t.area();
    // No default needed — compiler knows all subtypes!
};
```

### Pattern Matching for instanceof (Java 16+)
```java
// Old
if (obj instanceof String) {
    String s = (String) obj; // Explicit cast
    System.out.println(s.length());
}

// Java 16 Pattern Matching
if (obj instanceof String s) { // Binding variable 's'
    System.out.println(s.length()); // 's' scoped here
}

// With conditions
if (obj instanceof String s && s.length() > 5) {
    System.out.println(s.toUpperCase());
}
```

### Helpful NullPointerExceptions (JEP 358)
```java
// Before Java 14:
// Exception: java.lang.NullPointerException
//   at MyClass.process(MyClass.java:42)
// WHICH variable was null? No clue!

// Java 14+:
// Exception: java.lang.NullPointerException:
//   Cannot invoke "String.length()" because "user.getAddress().getCity()" is null
//   at MyClass.process(MyClass.java:42)
// NOW you know EXACTLY which part of the chain was null!
// Enabled by default in Java 17+
// Enable earlier: -XX:+ShowCodeDetailsInExceptionMessages
```

---

## ☕ JAVA 18 (2022)

### 1. Simple Web Server (JEP 408)
```bash
# Start a minimal HTTP file server from command line — no code!
jwebserver --port 8080 --directory /path/to/files

# Useful for: Testing, serving static files, prototyping
# NOT for production — single-threaded, serves files only
```

```java
// Programmatic API
var server = SimpleFileServer.createFileServer(
    new InetSocketAddress(8080),
    Path.of("/www"),
    SimpleFileServer.OutputLevel.VERBOSE
);
server.start();
```

### 2. UTF-8 by Default (JEP 400)
```
Before Java 18:
- Default charset was PLATFORM-DEPENDENT!
- Windows: windows-1252, Linux: UTF-8, Mac: UTF-8
- Code that worked on Linux could BREAK on Windows due to different encoding!
- Required: -Dfile.encoding=UTF-8 everywhere

Java 18+:
- UTF-8 is the DEFAULT charset on ALL platforms
- No more platform-dependent encoding bugs!
- Charset.defaultCharset() always returns UTF-8
```

### 3. Code Snippets in JavaDoc (JEP 413)
```java
/**
 * Example usage:
 * {@snippet :
 * var list = List.of(1, 2, 3);
 * list.forEach(System.out::println); // @highlight
 * }
 */
public void process() { }
// Replaces <pre><code> blocks — supports syntax highlighting!
```

---

## ☕ JAVA 19 (2022)

### 1. Virtual Threads (First Preview — finalized Java 21)
```java
// First preview of lightweight threads (Project Loom)
Thread.startVirtualThread(() -> {
    System.out.println("Running on: " + Thread.currentThread());
});
// This was the preview that led to Java 21's GA virtual threads
```

### 2. Structured Concurrency (Incubator — JEP 428)

#### 📖 Theory:
**What:** Treats groups of related concurrent tasks as a SINGLE unit of work. If one task fails, all related tasks are cancelled. This prevents thread leaks and orphaned tasks.

**Why:** With `ExecutorService`, if you submit 3 tasks and task 2 fails, tasks 1 and 3 keep running as orphans — wasting resources and potentially causing inconsistencies.

```java
// Structured Concurrency: all-or-nothing
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<User> userTask = scope.fork(() -> fetchUser(userId));
    Subtask<Order> orderTask = scope.fork(() -> fetchOrders(userId));

    scope.join();           // Wait for ALL tasks
    scope.throwIfFailed();  // Propagate any failure

    // Both succeeded — safe to use results
    return new UserProfile(userTask.get(), orderTask.get());
}
// If fetchOrders fails → fetchUser is automatically cancelled!
```

### 3. Foreign Function & Memory API (Preview)
```java
// Call native C functions from Java WITHOUT JNI!
// Modern replacement for sun.misc.Unsafe
try (Arena arena = Arena.ofConfined()) {
    MemorySegment cString = arena.allocateFrom("Hello");
    // Can pass to native C functions via method handles
}
```

---

## ☕ JAVA 20 (2023)

### 1. Scoped Values (Incubator — JEP 429)

#### 📖 Theory:
**What:** Scoped Values are an alternative to `ThreadLocal` designed for virtual threads. They are immutable within a scope and automatically cleaned up.

**Why ThreadLocal is problematic:**
- Mutable: any code can call `threadLocal.set()` → unpredictable state
- Leak-prone: forgetting `threadLocal.remove()` → memory leak in thread pools
- Inheritance: `InheritableThreadLocal` copies values to child threads → expensive with millions of virtual threads!

```java
final static ScopedValue<User> CURRENT_USER = ScopedValue.newInstance();

void handleRequest(User user) {
    ScopedValue.runWhere(CURRENT_USER, user, () -> {
        // CURRENT_USER is bound ONLY within this scope
        processOrder();  // Can access CURRENT_USER.get()
    });
    // CURRENT_USER is automatically unbound here — no cleanup needed!
}

void processOrder() {
    User user = CURRENT_USER.get(); // Access the scoped value
    // No need to pass User through every method parameter!
}
```

### 2. Record Patterns (Second Preview)
```java
// Enhanced destructuring for records
record Point(int x, int y) {}

void printSum(Object obj) {
    if (obj instanceof Point(int x, int y)) {  // Destructure record
        System.out.println(x + y);
    }
}
```

### 3. Virtual Threads (Second Preview)
```java
// Continued refinement before GA in Java 21
// Key change: Virtual threads are now DAEMON threads by default
Thread.ofVirtual().name("worker").start(() -> {
    System.out.println("Virtual thread: " + Thread.currentThread());
});
```

---

## ☕ JAVA 21 (2023) — LTS

### 1. Virtual Threads (GA)

#### 📖 Theory:
**What:** Virtual Threads are lightweight threads managed by the JVM (not the OS). Thousands of virtual threads share a small pool of OS threads (carrier threads).

**Why they were introduced:** Traditional platform threads map 1:1 to OS threads. Each OS thread costs ~1MB of stack memory. A typical Tomcat web server is configured with 200 threads max — limiting it to 200 concurrent requests. With virtual threads, you can create millions of threads cheaply, enabling massive I/O concurrency without reactive programming complexity.

**Key difference from Platform threads:**
- When a virtual thread performs I/O (DB query, HTTP call), it is **unmounted** from its carrier thread. The carrier thread immediately picks up another virtual thread. When the I/O completes, the virtual thread is re-mounted on any available carrier — no OS thread sits idle during I/O!

**When virtual threads help:** I/O-bound workloads (HTTP APIs, DB queries)
**When they don't help:** CPU-bound workloads (image processing, cryptography) — still limited by CPU cores

```java
// Millions of virtual threads without memory issues
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 1_000_000).forEach(i ->
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        })
    );
} // All tasks complete here
```

### 2. Sequenced Collections
```java
// New interfaces: SequencedCollection, SequencedSet, SequencedMap
List<String> list = new ArrayList<>(List.of("a", "b", "c"));
list.getFirst(); // "a" — new method
list.getLast();  // "c" — new method
list.reversed(); // ["c", "b", "a"] — reversed view

LinkedHashMap<String, Integer> map = new LinkedHashMap<>();
map.put("one", 1);
map.put("two", 2);
map.firstEntry(); // Map.Entry<"one", 1>
map.lastEntry();  // Map.Entry<"two", 2>
```

### 3. Record Patterns
```java
record Point(int x, int y) {}
record Line(Point start, Point end) {}

Object obj = new Line(new Point(1, 2), new Point(3, 4));

// Pattern matching with nested records
if (obj instanceof Line(Point(var x1, var y1), Point(var x2, var y2))) {
    System.out.println("Length: " + Math.hypot(x2-x1, y2-y1));
}
```

### 4. Pattern Matching in Switch (switch with types)
```java
Object value = getValue();

String description = switch (value) {
    case Integer i when i < 0 -> "Negative: " + i;
    case Integer i             -> "Positive: " + i;
    case String s              -> "Text: " + s;
    case null                  -> "null value";
    default                    -> "Other: " + value;
};
```

---

## ☕ JAVA 22 (2024)

### 1. Unnamed Variables `_` (JEP 456)
```java
// Ignore variables you don't need
try {
    riskyOperation();
} catch (Exception _) { // Unnamed — you know it happened, don't need it
    log.warn("Operation failed");
}

// In patterns
switch (obj) {
    case Point(int x, int _) -> System.out.println("x=" + x); // Ignore y
}
```

### 2. String Templates (Preview)
```java
// FUTURE: String interpolation
String name = "World";
String message = STR."Hello \{name}!"; // "Hello World!"

// Multi-line
String json = STR."""
    {
      "user": "\{user.getName()}",
      "age": \{user.getAge()}
    }
    """;
```

### 3. Gatherers (JEP 461 Preview) — Custom stream operations
```java
// Sliding window
Stream.of(1,2,3,4,5)
    .gather(Gatherers.windowSliding(3))
    .toList(); // [[1,2,3], [2,3,4], [3,4,5]]

// Fixed window
Stream.of(1,2,3,4,5)
    .gather(Gatherers.windowFixed(2))
    .toList(); // [[1,2], [3,4], [5]]
```

---

## 📊 Complete Version Summary Table — Java 8 to 22

| Version | Year | LTS | Key Features | Interview Importance |
|---------|------|-----|-------------|--------------------|
| **8** | 2014 | ✅ | Lambdas, Streams, Optional, DateTime, Functional Interfaces, Default Methods | ⭐⭐⭐⭐⭐ — MUST KNOW |
| **9** | 2017 | ❌ | Module System (Jigsaw), Collection.of(), Stream improvements, JShell, Private Interface Methods | ⭐⭐⭐ |
| **10** | 2018 | ❌ | `var` (local variable inference), Parallel Full GC for G1, Application CDS | ⭐⭐⭐ |
| **11** | 2018 | ✅ | HTTP Client API, String methods (isBlank, strip, lines, repeat), Files.readString, `var` in lambda | ⭐⭐⭐⭐ |
| **12** | 2019 | ❌ | Switch Expressions (preview), Compact Number Formatting, String.indent/transform, Teeing Collector | ⭐⭐ |
| **13** | 2019 | ❌ | Text Blocks (preview), yield in switch, Dynamic CDS Archives | ⭐⭐ |
| **14** | 2020 | ❌ | Records (preview), Switch Expressions (stable), Helpful NPEs, CMS GC Removed | ⭐⭐⭐ |
| **15** | 2020 | ❌ | Text Blocks (stable), Sealed Classes (preview), Hidden Classes, EdDSA | ⭐⭐ |
| **16** | 2021 | ❌ | Records (stable), Pattern Matching instanceof (stable), Elastic Metaspace, ZGC Concurrent Thread-Stack | ⭐⭐⭐ |
| **17** | 2021 | ✅ | Sealed Classes (stable), Pattern Matching for switch (preview), Foreign Function API, Strongly Encapsulate JDK Internals | ⭐⭐⭐⭐ |
| **18** | 2022 | ❌ | Simple Web Server, UTF-8 by Default, Code Snippets in JavaDoc | ⭐⭐ |
| **19** | 2022 | ❌ | Virtual Threads (preview), Structured Concurrency (incubator), Foreign Function API | ⭐⭐ |
| **20** | 2023 | ❌ | Scoped Values (incubator), Record Patterns (preview), Virtual Threads (2nd preview) | ⭐⭐ |
| **21** | 2023 | ✅ | **Virtual Threads (GA)**, Sequenced Collections, Record Patterns, Pattern Matching Switch (stable), Generational ZGC, Structured Concurrency | ⭐⭐⭐⭐⭐ — MUST KNOW |
| **22** | 2024 | ❌ | Unnamed Variables (`_`), Gatherers (preview), String Templates (2nd preview), Foreign Function API (stable), Region Pinning G1 | ⭐⭐⭐ |

### 📋 LTS Release Timeline:
```
Java 8 (2014) → Java 11 (2018) → Java 17 (2021) → Java 21 (2023) → Java 25 (2025 expected)
     3 years          3 years           2 years          2 years

Rule: New LTS every 2 years (since Java 17). Interview focus: 8, 11, 17, 21
```

---

# ═══════════════════════════════════════════════════════════════
# 🎯 JAVA VERSION CROSS-QUESTIONING — INTERVIEW DEEP DIVES
# ═══════════════════════════════════════════════════════════════

### Q1: "Why shouldn't you use Records everywhere instead of regular classes?"

> **Answer:** "Records are for **transparent data carriers only**. They have restrictions:
> 1. No mutable fields (ALL fields are `private final`) — can't use for entities that change state
> 2. Cannot extend other classes (implicitly extend `Record`) — no inheritance
> 3. `equals()` and `hashCode()` are based on ALL fields — can't customize to use just `id`
> 4. JPA/Hibernate entities need mutable setters, proxying, and a no-arg constructor — Records don't support this!
>
> Use Records for: DTOs, API responses, method return types, value objects.
> Use classes for: JPA entities, Spring beans (need mutability), objects with behavior."

---

### Q2: "Virtual Threads use carrier threads. What happens if a virtual thread calls a synchronized block?"

> **Answer:** "This is a critical gotcha called **PINNING**. When a virtual thread enters a `synchronized` block, it gets **pinned** to its carrier thread — the carrier thread CANNOT be reused by other virtual threads until the synchronized block exits.
>
> If all carrier threads (default = CPU cores) are pinned by synchronized blocks → no virtual threads can make progress → **virtual thread starvation**!
>
> **Fix:** Replace `synchronized` with `ReentrantLock`:
> ```java
> // BAD: pins virtual thread to carrier
> synchronized (lockObject) { dbCall(); }
>
> // GOOD: ReentrantLock doesn't cause pinning
> lock.lock();
> try { dbCall(); }
> finally { lock.unlock(); }
> ```
>
> **Detect pinning:** `-Djdk.tracePinnedThreads=full` — logs warning when pinning occurs."

---

### Q3: "If you're migrating from Java 8 to Java 17, what are the top 5 breaking changes?"

> **Answer:**
> 1. **Strong encapsulation of JDK internals (JEP 403):** `sun.misc.Unsafe`, `sun.reflect.*` are no longer accessible by default. Fix: `--add-opens java.base/sun.misc=ALL-UNNAMED` or migrate to public APIs.
> 2. **Nashorn JavaScript engine removed (Java 15):** If you used `ScriptEngine` with JS → switch to GraalJS.
> 3. **CMS GC removed (Java 14):** If you used `-XX:+UseConcMarkSweepGC` → switch to G1GC (default).
> 4. **Applet API deprecated (Java 9, removed Java 17):** Web-based Java applets no longer supported.
> 5. **javax → jakarta namespace:** Spring Boot 3 (which requires Java 17+) moved to Jakarta EE. All `javax.servlet.*` imports become `jakarta.servlet.*`.
>
> **Migration strategy:** Use `jdeps --jdk-internals` to find all usages of internal APIs before upgrading.

---

### Q4: "When would you NOT use var? Give me edge cases."

> **Answer:** "var should be avoided when it HIDES the type and reduces readability:
> ```java
> // BAD: What type is result? Can't tell without IDE
> var result = service.process(data);
>
> // GOOD: Type is clear
> ProcessingResult result = service.process(data);
>
> // BAD: Diamond + var = type lost
> var list = new ArrayList<>();  // ArrayList<Object>! Not ArrayList<String>!
>
> // GOOD: Type is explicit
> var list = new ArrayList<String>();  // OK — type is clear
> ```
>
> **Rules of thumb:**
> - ✅ Use var when the type is obvious from the RHS: `var list = List.of(1,2,3);`
> - ✅ Use var to reduce verbosity: `var map = new HashMap<String, List<Order>>();`
> - ❌ Never use var for method return types (not allowed anyway)
> - ❌ Never use var when it makes code harder to understand"

---

### Q5: "Explain the difference between Structured Concurrency and CompletableFuture"

> **Answer:** "CompletableFuture is a **reactive/callback-based** approach. Structured Concurrency is an **imperative/blocking** approach that works beautifully with virtual threads.
>
> | Aspect | CompletableFuture | Structured Concurrency |
> |--------|------------------|----------------------|
> | Style | Reactive (callbacks) | Imperative (blocking) |
> | Error handling | `.exceptionally()` chains | try-catch (standard!) |
> | Cancellation | Manual, error-prone | Automatic (scope closes → cancel all) |
> | Thread leak risk | High (orphaned futures) | Zero (scope enforced) |
> | Readability | Complex chains | Linear code flow |
> | Best with | Platform threads | Virtual threads |
>
> **Key insight:** Structured Concurrency + Virtual Threads gives you the concurrency of reactive programming with the readability of synchronous code. This is why many teams are moving AWAY from WebFlux/Reactor back to Spring MVC with virtual threads."
