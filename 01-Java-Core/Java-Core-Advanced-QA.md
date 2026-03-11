# ☕ Java Core — Advanced Interview Questions (Part 2)
## Target: 12+ Years Experience | howtodoinjava.com + FAANG Inspired

> **Note:** This extends Java-Core-QA.md with frequently asked topics from top interview guides.

---

## Q: Is Java Pass-by-Value or Pass-by-Reference?

### Answer: Java is **ALWAYS Pass-by-Value**. Period. No exceptions.

```java
// PRIMITIVE — value is copied
public void changePrimitive(int x) {
    x = 100; // Changes local copy only, original is unaffected
}

int num = 42;
changePrimitive(num);
System.out.println(num); // Still 42 ✅

// OBJECT — the REFERENCE (pointer) is copied, NOT the object
public void changeObject(StringBuilder sb) {
    sb.append(" World"); // Modifies the SAME object (via copied reference)
}

StringBuilder str = new StringBuilder("Hello");
changeObject(str);
System.out.println(str); // "Hello World" ✅ — same object was modified

// THE PROOF — reassigning the reference
public void reassignObject(StringBuilder sb) {
    sb = new StringBuilder("New Object"); // Points local copy to new object
    // Original reference is unaffected!
}

StringBuilder str2 = new StringBuilder("Original");
reassignObject(str2);
System.out.println(str2); // Still "Original" ✅
// If Java were pass-by-reference, this would print "New Object"
```

### Memory Visualization:
```
Pass-by-value for objects:

  main()                  method()
  ┌─────────┐            ┌──────────┐
  │ str ──────────┐      │ sb ──────────┐  (copy of reference)
  └─────────┘     │      └──────────┘   │
                  ▼                      ▼
              ┌──────────────────────────────┐
              │  StringBuilder: "Hello"       │  ← SAME object on heap
              └──────────────────────────────┘

  sb.append(" World") → modifies the SAME object
  sb = new StringBuilder() → local sb points elsewhere, str is unaffected
```

---

## Q: Explain Serialization in Java

### Theory:
**Serialization** = converting an object into a byte stream (for storage/network transfer).
**Deserialization** = reverse — reconstruct the object from bytes.

```java
// Make a class serializable — implement Serializable (marker interface)
public class Employee implements Serializable {
    private static final long serialVersionUID = 1L; // ALWAYS declare!

    private String name;
    private int age;
    private transient String password; // ❌ NOT serialized (sensitive data)
    private static String company;     // ❌ NOT serialized (belongs to class, not object)

    // Constructor, getters, setters...
}

// Serialize (write to file/stream)
Employee emp = new Employee("Yogesh", 35, "secret123");
try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream("emp.ser"))) {
    oos.writeObject(emp);
}

// Deserialize (read from file/stream)
try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream("emp.ser"))) {
    Employee restored = (Employee) ois.readObject();
    System.out.println(restored.getName());     // "Yogesh"
    System.out.println(restored.getAge());      // 35
    System.out.println(restored.getPassword()); // null (transient!)
}
```

### Key Concepts:
```
1. serialVersionUID:
   - Version check during deserialization
   - If class changed but UID matches → deserializes (with defaults for new fields)
   - If UID doesn't match → InvalidClassException
   - ALWAYS declare explicitly, otherwise JVM auto-generates (fragile)

2. transient keyword:
   - Field is SKIPPED during serialization
   - Use for: passwords, calculated fields, non-serializable references

3. static fields:
   - NOT serialized (they belong to the class, not the object)

4. Externalizable interface:
   - Extends Serializable
   - YOU control what gets serialized (implement readExternal/writeExternal)
   - More efficient but more work
```

```java
// Custom serialization control
public class SecureEmployee implements Serializable {
    private String name;
    private String ssn; // Sensitive — encrypt before serializing

    // Called during serialization — customize what gets written
    private void writeObject(ObjectOutputStream oos) throws IOException {
        oos.defaultWriteObject(); // Write non-transient fields
        oos.writeObject(encrypt(ssn)); // Encrypt SSN before writing
    }

    // Called during deserialization
    private void readObject(ObjectInputStream ois) throws IOException, ClassNotFoundException {
        ois.defaultReadObject();
        this.ssn = decrypt((String) ois.readObject()); // Decrypt SSN
    }
}
```

---

## Q: What are Marker Interfaces? Name some examples.

### Theory:
A **Marker Interface** is an empty interface (no methods) that acts as a **metadata tag** to signal something to the JVM or framework.

```java
// Examples of marker interfaces:
public interface Serializable {}  // Tells JVM: "this object can be serialized"
public interface Cloneable {}     // Tells JVM: "this object can be cloned"
public interface Remote {}        // Tells JVM: "this object is for RMI"

// If you serialize a non-Serializable object → NotSerializableException
// If you clone a non-Cloneable object → CloneNotSupportedException
```

### Marker Interface vs Annotation:
```
Marker Interface:
  + Can use in type checks: if (obj instanceof Serializable)
  + Polymorphism: method parameter type can be Serializable
  - Can't add metadata (no fields/methods)

Annotation (@interface):
  + Can carry metadata: @Cacheable(ttl = 300)
  + More flexible, doesn't pollute class hierarchy
  + Framework reads via reflection
  - Can't use as method parameter type

Modern Java PREFERS annotations over marker interfaces.
Spring uses: @Component, @Transactional, @Cacheable
JPA uses: @Entity, @Table, @Column
```

---

## Q: hashCode() and equals() Contract — Why override both?

```java
// THE CONTRACT (from Object class javadoc):
// 1. If a.equals(b) is TRUE, then a.hashCode() MUST equal b.hashCode()
// 2. If a.hashCode() == b.hashCode(), equals MAY or MAY NOT be true (collision)
// 3. If a.equals(b) is FALSE, hashCodes CAN be equal (but shouldn't for performance)

// BROKEN CODE — only overrides equals, not hashCode:
public class Employee {
    private Long id;
    private String name;

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Employee emp = (Employee) o;
        return Objects.equals(id, emp.id);
    }
    // ❌ hashCode() NOT overridden!
}

// What goes wrong:
Employee e1 = new Employee(1L, "Yogesh");
Employee e2 = new Employee(1L, "Yogesh"); // Same ID

e1.equals(e2); // TRUE ✅

Set<Employee> set = new HashSet<>();
set.add(e1);
set.contains(e2); // FALSE ❌ — BROKEN!
// WHY: HashSet checks hashCode first. Default hashCode uses memory address.
// e1 and e2 have DIFFERENT memory addresses → different hashCodes → different buckets!

// ✅ CORRECT — always override both:
@Override
public int hashCode() {
    return Objects.hash(id); // Use same fields as equals()
}
```

### Rules for good hashCode():
```
1. Use the SAME fields as equals()
2. Use Objects.hash(field1, field2) — simple and correct
3. Immutable fields preferred (hashCode shouldn't change mid-lifecycle)
4. In JPA entities: use @NaturalId fields, NOT @Id (auto-generated IDs cause issues)
```

---

## Q: Deep Copy vs Shallow Copy

```java
// Shallow Copy — copies references, NOT the objects they point to
class Department {
    String name;
    List<String> employees; // Mutable object
}

Department dept1 = new Department("Engineering", List.of("Alice", "Bob"));
Department dept2 = dept1; // ❌ Not even a copy — same reference!

// Even with clone():
Department dept3 = (Department) dept1.clone(); // Shallow copy
// dept3.employees STILL points to the SAME list object as dept1.employees

// Deep Copy — recursively copies all nested objects
Department dept4 = new Department(dept1.name, new ArrayList<>(dept1.employees));
// dept4.employees is a NEW list — changes don't affect dept1

// Deep copy methods:
// 1. Manual: new ArrayList<>(original) for each collection
// 2. Serialization: serialize → deserialize (expensive but thorough)
// 3. Copy constructor: new Department(other)
// 4. Libraries: Apache Commons SerializationUtils.clone()
```

---

## Q: Access Modifiers in Java

| Modifier | Same Class | Same Package | Subclass (diff pkg) | Other Packages |
|----------|-----------|-------------|---------------------|----------------|
| `private` | ✅ | ❌ | ❌ | ❌ |
| `default` (no modifier) | ✅ | ✅ | ❌ | ❌ |
| `protected` | ✅ | ✅ | ✅ | ❌ |
| `public` | ✅ | ✅ | ✅ | ✅ |

```java
// Common interview trick: Can a class be private?
// Top-level class: only public or default (package-private)
// Inner class: can be private, protected, public, or default

// protected gotcha:
// Subclass in DIFFERENT package can access protected members
// BUT only through inheritance (this.protectedMethod()), NOT through reference
```

---

## Q: finally Block — When Does It NOT Execute?

```java
// finally ALWAYS executes... almost.
try {
    return 1;
} finally {
    System.out.println("I STILL run!"); // Runs even with return in try!
}

// When finally does NOT execute:
// 1. System.exit(0) in try/catch
// 2. JVM crash (segfault, kill -9)
// 3. Infinite loop in try block
// 4. Thread.stop() is called (deprecated)

// GOTCHA: What does this return?
try {
    return 1;
} finally {
    return 2; // ⚠️ This OVERWRITES the try's return! Returns 2!
    // NEVER return from finally block — it's a code smell
}
```

---

## Q: Why is String immutable in Java?

```
1. STRING POOL: JVM caches strings in a pool. If "Hello" is mutable,
   changing it affects every reference pointing to the same pooled object.

2. SECURITY: Strings hold class names, database URLs, passwords.
   If mutable, malicious code could change a file path after security check.

3. HASHCODE CACHING: String caches its hashCode after first calculation.
   HashMap relies on this. If String were mutable, hashCode could change
   after insertion → object becomes "lost" in the wrong bucket.

4. THREAD SAFETY: Immutable objects are inherently thread-safe.
   No synchronization needed when sharing strings across threads.
```

---

## Q: Comparable vs Comparator

```java
// Comparable — natural ordering, implemented BY the class itself
public class Employee implements Comparable<Employee> {
    private String name;
    private int salary;

    @Override
    public int compareTo(Employee other) {
        return Integer.compare(this.salary, other.salary); // Natural order by salary
    }
}
Collections.sort(employees); // Uses compareTo automatically

// Comparator — external, multiple sort strategies
Comparator<Employee> byName = Comparator.comparing(Employee::getName);
Comparator<Employee> bySalaryDesc = Comparator.comparing(Employee::getSalary).reversed();
Comparator<Employee> byNameThenSalary = byName.thenComparing(Employee::getSalary);

employees.sort(byName);          // Sort by name
employees.sort(bySalaryDesc);    // Sort by salary descending

// Key difference:
// Comparable: ONE natural ordering, built INTO the class (compareTo)
// Comparator: MULTIPLE orderings, EXTERNAL to the class
```

---

## Q: Exception Handling — Checked vs Unchecked

```
Exception Hierarchy:
  Throwable
  ├── Error (DON'T catch — JVM problems)
  │   ├── OutOfMemoryError
  │   ├── StackOverflowError
  │   └── NoClassDefFoundError
  └── Exception
      ├── Checked Exceptions (MUST handle — compile error otherwise)
      │   ├── IOException
      │   ├── SQLException
      │   ├── ClassNotFoundException
      │   └── InterruptedException
      └── RuntimeException (Unchecked — compiler doesn't force you)
          ├── NullPointerException
          ├── ArrayIndexOutOfBoundsException
          ├── ClassCastException
          ├── IllegalArgumentException
          └── ConcurrentModificationException

Best Practices:
1. Catch specific exceptions, NOT generic Exception
2. Don't swallow exceptions: catch(Exception e) {} ← NEVER do this!
3. Use try-with-resources for AutoCloseable objects
4. Create custom exceptions for business logic
5. @ControllerAdvice for global exception handling in Spring
```

```java
// Custom exception hierarchy for a payment system
public class PaymentException extends RuntimeException {
    private final String errorCode;
    public PaymentException(String errorCode, String message) {
        super(message);
        this.errorCode = errorCode;
    }
}

public class InsufficientBalanceException extends PaymentException {
    public InsufficientBalanceException(BigDecimal balance, BigDecimal required) {
        super("INSUFFICIENT_BALANCE",
              "Balance " + balance + " is less than required " + required);
    }
}
```

---

## 🎯 Java Core Cross-Questioning (from howtodoinjava.com patterns)

### Q: "Can we create an immutable class with mutable fields?"
> **Answer:** "Yes, but you must defensively copy. In the constructor, deep-copy the mutable field (`this.list = new ArrayList<>(list)`). In the getter, return an unmodifiable view (`Collections.unmodifiableList(list)`) or a new copy. The key principle: the class never exposes a reference to its internal mutable state. This is exactly what the `Collections.unmodifiableXxx()` wrappers do."

### Q: "What happens if equals() returns true but hashCode() returns different values?"
> **Answer:** "HashMap/HashSet will be BROKEN. When you do `set.contains(obj)`, it first calculates `obj.hashCode()`, goes to that bucket, then checks `equals()`. If hashCodes differ, it looks in the wrong bucket and never finds the object — even though `equals()` would return true. This violates the contract and causes silent data loss in collections."

### Q: "Can a constructor be private? When would you use it?"
> **Answer:** "Yes! Private constructors prevent direct instantiation. Use cases: (1) **Singleton pattern** — only one instance via `getInstance()`. (2) **Factory methods** — `of()`, `valueOf()`, `newInstance()` with meaningful names. (3) **Utility classes** — `Math`, `Collections` — only static methods, no instance needed. (4) **Builder pattern** — constructor is private, only Builder can create the object."

---

## 📘 Additional Topics (from GeeksforGeeks + InterviewBit)

---

## Q: Composition vs Inheritance — Why "prefer composition"?

```java
// INHERITANCE — "IS-A" relationship
// Employee IS-A Person
class Person { String name; }
class Employee extends Person { String empId; }

// COMPOSITION — "HAS-A" relationship
// Car HAS-A Engine
class Engine {
    void start() { System.out.println("Engine started"); }
}
class Car {
    private final Engine engine; // Composed object

    Car(Engine engine) { this.engine = engine; }

    void start() {
        engine.start(); // Delegate to composed object
        System.out.println("Car is ready");
    }
}
```

### Why Composition is Preferred:
```
1. FLEXIBILITY: Can swap implementations at runtime
   → Inject MockEngine in tests, RealEngine in production

2. ENCAPSULATION: Internal details hidden
   → Changing Engine internals doesn't break Car

3. AVOIDS FRAGILE BASE CLASS: Changing parent class can break all subclasses
   → Composition is immune to this

4. MULTIPLE "INHERITANCE": Java doesn't support multiple class inheritance
   → But you can compose multiple objects

5. TESTABILITY: Easy to mock composed objects
   → Inheritance creates tight coupling

RULE: Use inheritance for genuine "IS-A" (Dog IS-A Animal)
      Use composition for "HAS-A" or "USES-A" (Car HAS-A Engine)
      When in doubt → use composition
```

---

## Q: Java Reflection API — What is it and when to use it?

```java
// Reflection = ability to inspect and modify classes, methods, fields at RUNTIME
// Used by: Spring (DI, annotations), Hibernate (entity mapping), JUnit (test discovery)

Class<?> clazz = Class.forName("com.company.Employee");

// Create instance without 'new'
Object obj = clazz.getDeclaredConstructor().newInstance();

// Get all declared methods
Method[] methods = clazz.getDeclaredMethods();
for (Method m : methods) {
    System.out.println(m.getName() + " - " + m.getReturnType());
}

// Invoke private method!
Method privateMethod = clazz.getDeclaredMethod("calculateBonus", double.class);
privateMethod.setAccessible(true); // Bypass private access
Object result = privateMethod.invoke(obj, 50000.0);

// Read private field
Field salaryField = clazz.getDeclaredField("salary");
salaryField.setAccessible(true);
double salary = (double) salaryField.get(obj);

// Check annotations
if (clazz.isAnnotationPresent(Entity.class)) {
    System.out.println("This is a JPA entity");
}
```

### When to Use / Avoid:
```
USE: Frameworks, libraries, serialization, testing, dependency injection
AVOID: Regular application code — reflection is:
  - SLOW (bypasses JVM optimizations)
  - UNSAFE (bypasses compile-time type checking)
  - FRAGILE (refactoring breaks string-based lookups)
```

---

## Q: Java ClassLoader — How classes are loaded

```
ClassLoader Hierarchy (Delegation Model):
  1. Bootstrap ClassLoader → loads rt.jar (java.lang, java.util)
     ↓ delegates to
  2. Extension/Platform ClassLoader → loads ext/*.jar
     ↓ delegates to
  3. Application/System ClassLoader → loads your app classes (classpath)
     ↓ delegates to
  4. Custom ClassLoader → loads classes from DB, network, plugins

Loading process:
  1. Loading: Reads .class file bytes from disk/network
  2. Linking:
     a. Verification: Checks bytecode is valid and safe
     b. Preparation: Allocates memory for static variables
     c. Resolution: Symbolic references → direct references
  3. Initialization: Executes static blocks and initializers

ClassNotFoundException vs NoClassDefFoundError:
  ClassNotFoundException: Class not found on classpath at RUNTIME (checked)
  NoClassDefFoundError: Class was present at COMPILE time but missing at RUNTIME (error)
```

---

## Q: Strong, Weak, Soft, and Phantom References

```java
// 1. STRONG reference (default) — object never garbage collected
String str = "Hello"; // Strong reference — GC cannot touch it

// 2. SOFT reference — GC collects ONLY when memory is low
SoftReference<byte[]> cache = new SoftReference<>(new byte[1024 * 1024]);
byte[] data = cache.get(); // May return null if GC collected it
// USE CASE: Memory-sensitive caches (image cache)

// 3. WEAK reference — GC collects at NEXT cycle (even if memory is fine)
WeakReference<Employee> weakEmp = new WeakReference<>(new Employee("John"));
Employee emp = weakEmp.get(); // May return null
// USE CASE: WeakHashMap — cache that auto-cleans when keys unused

// 4. PHANTOM reference — cannot retrieve object, only for cleanup notification
PhantomReference<Object> phantom = new PhantomReference<>(obj, referenceQueue);
phantom.get(); // ALWAYS returns null
// USE CASE: Track when object is finalized (alternative to finalize())

// Reference strength: Strong > Soft > Weak > Phantom
// GC collects: Strong=never, Soft=when OOM, Weak=anytime, Phantom=after finalize
```

---

## Q: throw vs throws

```java
// THROW — actually throws an exception object (used INSIDE method)
public void withdraw(double amount) {
    if (amount > balance) {
        throw new InsufficientFundsException("Balance: " + balance); // Throw HERE
    }
    balance -= amount;
}

// THROWS — declares that a method MIGHT throw (used in METHOD SIGNATURE)
public void readFile(String path) throws IOException, FileNotFoundException {
    // Tells caller: "I might throw these — handle them or declare them too"
    BufferedReader reader = new BufferedReader(new FileReader(path));
}

// KEY DIFFERENCES:
// throw: used inside code, throws ONE exception at a time
// throws: used in signature, can declare MULTIPLE exceptions
// throw: followed by exception OBJECT (throw new XyzException())
// throws: followed by exception CLASS (throws XyzException)
```

---

## Q: final, finally, finalize — The Classic Trio

```java
// 1. FINAL — keyword for immutability
final int MAX = 100;        // Variable: value can't change
final class Utility {}       // Class: can't be inherited
final void process() {}      // Method: can't be overridden

// 2. FINALLY — block that ALWAYS executes after try/catch
try {
    riskyOperation();
} catch (Exception e) {
    handleError(e);
} finally {
    closeResources(); // Runs regardless of exception
}
// Better: try-with-resources (Java 7+)
try (Connection conn = dataSource.getConnection()) {
    // conn.close() called automatically
}

// 3. FINALIZE — method called before GC (DEPRECATED since Java 9)
@Override
protected void finalize() throws Throwable {
    // Don't use! Unpredictable timing, performance penalty
    // Use Cleaner (Java 9+) or try-with-resources instead
}
```

---

## Q: Common Causes of Memory Leaks in Java

```java
// Even with GC, memory leaks happen when objects are referenced but unused:

// 1. STATIC COLLECTIONS that keep growing
private static final List<Object> cache = new ArrayList<>();
cache.add(data); // Never removed → grows forever → OutOfMemoryError

// 2. UNCLOSED RESOURCES
Connection conn = dataSource.getConnection();
// If exception occurs before conn.close() → connection leaked
// FIX: try-with-resources

// 3. INNER CLASS holding reference to outer class
class Outer {
    byte[] largeData = new byte[10_000_000]; // 10MB
    class Inner { // Non-static inner class holds implicit ref to Outer!
        void doWork() { }
    }
    // Inner keeps Outer (and its 10MB) alive even if Outer is "unused"
    // FIX: Use static inner class
}

// 4. THREADLOCAL not cleaned
ThreadLocal<UserContext> context = new ThreadLocal<>();
context.set(new UserContext()); // In Tomcat thread pool, thread is reused!
// FIX: ALWAYS call context.remove() in finally block

// 5. LISTENERS/CALLBACKS never unregistered
eventBus.register(myListener); // If never unregistered → leaked

// DETECTION: Use VisualVM, Eclipse MAT, or -XX:+HeapDumpOnOutOfMemoryError
```

---

## Q: String Pool Internals & String Interning

```java
// String Pool = special area in heap where JVM caches string literals

String s1 = "Hello";        // Goes to String Pool
String s2 = "Hello";        // Reuses SAME object from pool
System.out.println(s1 == s2); // TRUE ✅ — same reference

String s3 = new String("Hello"); // Creates NEW object on heap (NOT pool)
System.out.println(s1 == s3);    // FALSE ❌ — different objects
System.out.println(s1.equals(s3)); // TRUE ✅ — same content

// intern() — manually add to pool
String s4 = s3.intern(); // Puts s3's value into pool, returns pool reference
System.out.println(s1 == s4); // TRUE ✅ — s4 now points to pooled "Hello"

// HOW MANY OBJECTS created?
String s = new String("Java"); // Creates 2 objects:
// 1. "Java" literal → String Pool (if not already there)
// 2. new String() → separate object on heap

// CONCATENATION:
String result = "Hello" + " " + "World"; // Compiler optimizes to "Hello World" (1 object)
String name = "World";
String greeting = "Hello " + name; // NOT optimized — StringBuilder used at runtime
```

---

## 🎯 Tricky Output-Based Questions (from InterviewBit/GFG)

### Q: What does this print?
```java
System.out.println('b' + 'i' + 't');
// Answer: 319 (NOT "bit")
// WHY: char + char = int arithmetic: 98 + 105 + 116 = 319
// FIX: System.out.println("" + 'b' + 'i' + 't'); → prints "bit"
```

### Q: What does this print?
```java
System.out.println(10 + 20 + "Hello" + 10 + 20);
// Answer: "30Hello1020"
// WHY: Left to right: 10+20=30, 30+"Hello"="30Hello", +"10"="30Hello10", +"20"="30Hello1020"
// Once String is in the equation, everything after becomes string concatenation
```

### Q: What is the output?
```java
String s1 = "abc";
String s2 = "abc";
String s3 = new String("abc");
System.out.println(s1 == s2);       // true (same pool reference)
System.out.println(s1 == s3);       // false (different objects)
System.out.println(s1.equals(s3));  // true (same content)
System.out.println(s1 == s3.intern()); // true (intern returns pool ref)
```
