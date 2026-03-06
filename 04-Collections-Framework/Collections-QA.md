# 📚 Collections Framework — Deep Dive (Theory + Code + Cross-Questions)
## Target: 12+ Years Experience

---

## 📖 What is the Java Collections Framework?

The Java Collections Framework (JCF) is a **unified architecture for representing and manipulating groups of objects**. It provides:
- **Interfaces** — Abstract types defining the contracts (`List`, `Set`, `Map`, `Queue`)
- **Implementations** — Concrete classes (`ArrayList`, `HashMap`, `TreeSet`)
- **Algorithms** — Utility methods in `Collections` and `Arrays`

### Why it matters at the senior level:
Choosing the wrong collection causes **production bugs** (using HashMap in a concurrent environment), **performance issues** (using LinkedList with random access), or **hidden OOM errors** (using an unbounded CachedThreadPool queue). A senior developer must know the internals — not just which one to use, but exactly *why*.

### Collection Hierarchy Overview:
```
Iterable
  └── Collection
        ├── List     → ArrayList, LinkedList, CopyOnWriteArrayList
        ├── Set      → HashSet, LinkedHashSet, TreeSet, CopyOnWriteArraySet
        └── Queue    → LinkedList, PriorityQueue, ArrayDeque, BlockingQueue variants
Map (NOT a Collection!)
  ├── HashMap, LinkedHashMap, TreeMap
  ├── ConcurrentHashMap, ConcurrentSkipListMap
  └── Hashtable (legacy — avoid)
```

---

## Q1: How does HashMap work internally?

### 📖 Theory:
A `HashMap` is the most-used Map implementation. Internally it is an **array of buckets** (called `Node<K,V>[]`). Each bucket stores a linked list of entries with the same hash bucket index. As of Java 8, when a bucket's linked list grows to 8+ entries AND the total map capacity is ≥ 64, it converts to a **Red-Black Tree** (O(log n) lookup). This solves the worst-case performance problem of hash flooding attacks.

**The 4 key steps of `put(key, value)`:**
1. `key.hashCode()` is computed
2. Hash is *spread* (XOR with right-shift) to reduce clustering in lower bits
3. Bucket index: `hash & (capacity - 1)` (bitwise AND is faster than modulo)
4. If bucket occupied, traverse list comparing keys with `.equals()`. If found → update; else → append.

**Load Factor & Rehashing:**
The Load Factor (default 0.75) determines when rehashing happens. At 75% capacity, HashMap creates a new array of double size and rehashes all entries. This is O(n) and causes a temporary pause — avoid it by pre-specifying capacity.

```java
// HashMap = Array of LinkedList/Red-Black Tree (Java 8+)
// Default capacity: 16 buckets, load factor: 0.75

// When you do: map.put("key", "value")

// Step 1: Calculate hashCode
int hash = key.hashCode();

// Step 2: Spread the hash (reduce collisions in lower bits)
hash = hash ^ (hash >>> 16); // XOR with right shift — mixes high bits into low bits

// Step 3: Find bucket index
int index = hash & (capacity - 1); // Same as hash % capacity but bitwise AND is ~10x faster

// Step 4: Add to bucket
// - If empty → add Node directly
// - If collision → traverse LinkedList (compare keys using equals()), add at end
// - If list size >= 8 AND capacity >= 64 → convert to Red-Black Tree (O(log n) lookup)
// - If tree size shrinks to 6 → convert back to LinkedList

// Pre-sizing to avoid expensive rehashing
// If you know you'll store ~1000 entries:
Map<String, Value> map = new HashMap<>(1334); // 1000 / 0.75 + 1 = no rehash!
```

### Hash Collision:
```java
// Two different keys can map to same bucket (collision)
// Example: "FB" and "Ea" have the same hashCode() in Java!

// Java handles via chaining (linked list per bucket):
// bucket[5] → Node("FB", v1) → Node("Ea", v2) → null

// Retrieval: get("Ea")
// 1. Compute hash, find bucket[5]
// 2. Traverse list, compare keys using equals() (== first for optimization)
// 3. Return matching value
```

**Interview Cross-Questions:**
> **Q: "What happens in HashMap if you use a mutable object as a key and then mutate it after insertion?"**
> A: "This is a disaster scenario. The `hashCode()` of the key changes after mutation, so when HashMap computes the bucket index for the new hash, it goes to a different bucket and finds nothing. The entry permanently 'disappears' from the Map without being deleted. This is why Map keys should always be **immutable** — `String`, `Integer`, enums, `UUID`. If you must use a mutable key, ensure the fields used in `hashCode()` and `equals()` are final and never modified."

---

## Q2: HashMap vs LinkedHashMap vs TreeMap vs ConcurrentHashMap

### 📖 Theory:

| Implementation | Internal Structure | Ordering | Thread-Safe | Performance |
|----------------|-------------------|----------|-------------|-------------|
| `HashMap` | Array of buckets (linked list / tree) | ❌ None | ❌ No | O(1) avg |
| `LinkedHashMap` | HashMap + doubly linked list | ✅ Insertion or Access Order | ❌ No | O(1) avg |
| `TreeMap` | Red-Black Tree | ✅ Sorted by Key | ❌ No | O(log n) |
| `ConcurrentHashMap` | Segmented HashMap | ❌ None | ✅ Yes | O(1) avg |
| `Hashtable` | Array of buckets | ❌ None | ✅ Yes (bad) | O(1) — but sync on whole map |

**`LinkedHashMap` superpower:** When constructed with `accessOrder=true`, it tracks the last-recently-accessed entry. Overriding `removeEldestEntry()` creates a perfect **LRU Cache** in under 5 lines of code!

```java
// HashMap — unordered, O(1) get/put, not thread-safe
Map<String, Integer> map = new HashMap<>();

// LinkedHashMap — maintains INSERTION ORDER by default
// With accessOrder=true → becomes an automatic LRU Cache
Map<String, Integer> lruCache = new LinkedHashMap<>(16, 0.75f, true) { // accessOrder=true
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, Integer> eldest) {
        return size() > 100; // Auto-evict the oldest accessed entry when > 100 entries
    }
};

// TreeMap — sorted by KEY (natural order or custom Comparator), O(log n)
Map<String, Integer> sorted = new TreeMap<>(); // Keys sorted A-Z
Map<String, Integer> reverseOrder = new TreeMap<>(Comparator.reverseOrder()); // Keys Z-A

// Range queries — only possible with TreeMap, not HashMap!
TreeMap<LocalDate, BigDecimal> salaryHistory = new TreeMap<>();
SortedMap<LocalDate, BigDecimal> lastYear = salaryHistory.tailMap(LocalDate.now().minusYears(1));

// ConcurrentHashMap — thread-safe, high concurrency (preferred over synchronizedMap)
ConcurrentHashMap<String, Integer> concurrent = new ConcurrentHashMap<>();
concurrent.putIfAbsent("key", value);            // Atomic — no race condition
concurrent.computeIfAbsent(key, k -> compute(k)); // Atomic compute-and-store
concurrent.merge(key, 1, Integer::sum);           // Atomic increment counter
```

---

## Q3: ConcurrentHashMap — How does it achieve thread safety without locking the whole map?

### 📖 Theory:
This is a **critical senior-level question**. The key insight is that `ConcurrentHashMap` achieves thread safety without locking the ENTIRE map.

**Java 7:** Used a **Segmented Locking** strategy. The map was divided into 16 "segments" (mini-HashMaps). Writes locked only the relevant segment, allowing 16 concurrent writers.

**Java 8+:** Abandoned segments. Now uses:
1. **CAS (Compare-And-Swap)** CPU instructions for writes to empty buckets — **no lock at all!**
2. **`synchronized` on the individual bucket node** (single object, not the map) when the bucket has a collision.
3. Multiple writes to *different* buckets are **fully concurrent** — no synchronization overhead between them.

Compare this to `Collections.synchronizedMap()` which uses a single `synchronized(this)` lock — only one thread can read OR write at any time.

```java
// Java 8+ ConcurrentHashMap internal behavior:
// 1. First write to empty bucket → CAS (Compare-And-Swap) — NO LOCK!
// 2. Collision at same bucket → synchronized on that BUCKET NODE only
//    (Not entire map, not even entire bucket list)
// 3. Multiple writes to DIFFERENT buckets happen simultaneously

// Contrast with synchronizedMap:
// synchronizedMap → synchronized on ENTIRE map → one thread at a time (big bottleneck)
// ConcurrentHashMap: 100 buckets, 100 concurrent writes → each to different bucket = all fully concurrent!

// Operations that ARE atomic in ConcurrentHashMap (same for multiple lines):
concurrent.putIfAbsent("key", value);          // Add only if not exists
concurrent.computeIfAbsent(key, k -> compute(k)); // Compute if not exists (lazy init)
concurrent.merge(key, 1, Integer::sum);        // Atomic increment
concurrent.compute(key, (k, v) -> v == null ? 1 : v + 1); // Atomic update

// ⚠️ PITFALL: Compound actions (check-then-act) are NOT atomic!
// BAD — race condition possible:
if (!map.containsKey("key")) {  // Thread 1 checks: key not present
    map.put("key", newValue);   // Thread 2 also does this before Thread 1 writes!
}

// ✅ CORRECT — use atomic compound methods:
map.putIfAbsent("key", newValue);  // Single atomic operation
map.computeIfAbsent("key", k -> expensiveComputation(k)); // Even better for heavy init
```

**Interview Cross-Questions:**
> **Q: "ConcurrentHashMap allows concurrent reads. But `size()` might be inaccurate. How would you get an accurate count?"**
> A: "The `size()` on ConcurrentHashMap estimates the count from distributed counters and may be slightly stale under high contention. If accuracy is mission-critical (e.g., counting processed messages), I'd use `mappingCount()` which returns a `long` and is more reliable than `size()` for very large maps. For true accurate concurrent counting, I'd use `LongAdder` as the map's value type, which is explicitly designed for high-concurrency increments."

---

## Q4: ArrayList vs LinkedList — Deep Internals

### 📖 Theory:

**`ArrayList` is a resizable array.**
- Backed by `Object[] elementData`
- `get(i)`: O(1) — direct array index access (memory is contiguous, CPU cache-friendly)
- `add(end)`: O(1) amortized — occasionally O(n) when the internal array doubles in size
- `add(middle)` or `remove(middle)`: O(n) — must shift all elements right/left
- Memory: Compact. 8 bytes per reference. No extra overhead per element.

**`LinkedList` is a doubly-linked list.**
- Each element is a `Node<E>` containing the data + two pointers (previous and next)
- `get(i)`: O(n) — must traverse from head (or tail if i > size/2)
- `add(end)` or `addFirst()`: O(1) — just update tail/head pointer
- `add(middle)`: O(n) to find position + O(1) to insert (update just 2 pointers)
- Memory: Expensive. Each `Node` = 24+ bytes overhead. For 1M entries: 24MB+ of Node headers vs 8MB for ArrayList.

**Rule of thumb:** Use `ArrayList` in 95% of cases. Use `LinkedList` ONLY as a `Deque` (adding/removing from both ends). `ArrayDeque` is usually even faster than LinkedList as a Deque.

```java
// Performance comparison matrix:
//
//                    ArrayList    LinkedList
// get(i)             O(1) ←✅    O(n)
// add(end)           O(1) amort  O(1) ←✅
// add(index)         O(n)        O(n) (find pos)
// remove(index)      O(n)        O(n) (find pos)
// remove(known node) O(n) (find) O(1) ←✅ (update pointers only)
// Memory per element 8 bytes     24+ bytes overhead
// CPU cache          ✅ Excellent ❌ Cache misses (non-contiguous)

// Use ArrayList almost always
List<String> list = new ArrayList<>();

// Use LinkedList as a Deque (double-ended queue)
Deque<String> deque = new LinkedList<>();
deque.addFirst("front");  // O(1) — update head
deque.addLast("back");    // O(1) — update tail
deque.pollFirst();         // O(1) — remove from head
deque.pollLast();          // O(1) — remove from tail

// ArrayDeque is BETTER than LinkedList as a Deque (uses a circular array, less overhead)
Deque<String> faster = new ArrayDeque<>();
```

---

## Q5: HashSet / TreeSet / LinkedHashSet

### 📖 Theory:

**`HashSet`** is backed by a `HashMap` where the set elements are the map's KEYS and all values are a dummy `PRESENT` object. This gives it O(1) add/contains/remove.

**`TreeSet`** is backed by a `TreeMap` (Red-Black Tree). Elements are stored **sorted** (natural order via `Comparable`, or custom `Comparator`). This gives O(log n) operations but adds powerful range query operations (`headSet()`, `tailSet()`, `subSet()`).

**`LinkedHashSet`** is backed by `LinkedHashMap`, maintaining **insertion order** with O(1) operations. Use it when you need uniqueness AND insertion-order preservation.

**Critical Rule:** If you put custom objects into a `HashSet` or `HashMap` key, you MUST override **both `hashCode()` AND `equals()`** consistently. The contract: if `a.equals(b)` is true, then `a.hashCode() == b.hashCode()` must be true. Violating this causes duplicate logical objects in a Set or unretrievable entries in a Map.

```java
// HashSet — backed by HashMap, O(1) add/remove/contains, unordered
Set<String> set = new HashSet<>();
set.contains("apple"); // O(1)

// TreeSet — backed by TreeMap (Red-Black Tree), natural-sorted, O(log n)
TreeSet<Integer> ts = new TreeSet<>();
ts.addAll(List.of(5, 2, 8, 1, 4, 9));
ts.first();           // 1 — Smallest element, O(log n)
ts.last();            // 9 — Largest element, O(log n)
ts.headSet(5);        // {1, 2, 4} — Elements strictly < 5
ts.tailSet(5);        // {5, 8, 9} — Elements >= 5
ts.subSet(2, 8);      // {2, 4, 5} — Elements in range [2, 8)

// LinkedHashSet — maintains insertion order, O(1) operations
Set<String> ordered = new LinkedHashSet<>();
// Great for: "unique items that must stay in the order I added them"

// ⚠️ CRITICAL: Override hashCode AND equals for custom objects in Sets/Map keys
// @EqualsAndHashCode from Lombok is the easiest way
@EqualsAndHashCode(onlyExplicitlyIncluded = true)
public class Employee {
    @EqualsAndHashCode.Include
    private final String employeeId; // Identity based on ID

    private String name; // Name changes don't affect set membership
}
Set<Employee> employees = new HashSet<>();
// Without @EqualsAndHashCode: two Employee objects with same ID are treated as DIFFERENT!
```

---

## Q6: BlockingQueue — thread-safe producer-consumer

### 📖 Theory:
`BlockingQueue` is a thread-safe queue that **blocks the caller** in two key scenarios:
- **Producer** tries to `put()` item but queue is **full** → producer thread pauses
- **Consumer** tries to `take()` item but queue is **empty** → consumer thread pauses

This built-in blocking eliminates the need for manual `wait()/notify()` in producer-consumer scenarios. It also provides natural **backpressure**: if consumers are slow, producers automatically slow down.

**Implementations:**
| Class | Bounded? | FIFO? | Best For |
|-------|---------|-------|---------|
| `ArrayBlockingQueue` | ✅ Fixed capacity | ✅ Yes | Bounded producer-consumer; backpressure |
| `LinkedBlockingQueue` | Optional (default unbounded) | ✅ Yes | General task queues (careful: unbounded = OOM risk!) |
| `PriorityBlockingQueue` | ❌ Unbounded | ❌ Priority-first | Task scheduling by priority |
| `SynchronousQueue` | Capacity=0 (no storage) | N/A | Direct handoff; thread pool task dispatch |
| `DelayQueue` | ❌ Unbounded | ❌ Delay-first | Scheduled retry queues |

```java
// BlockingQueue implementations explained:
// LinkedBlockingQueue  — optionally bounded FIFO (DEFAULT unbounded = OOM risk!)
// ArrayBlockingQueue   — bounded (fixed capacity) FIFO — ✅ preferred for production
// PriorityBlockingQueue — unbounded, priority-ordered (not FIFO)
// SynchronousQueue     — capacity=0, direct handoff producer→consumer
// DelayQueue           — elements only available after delay expires (retry scheduling)

// ✅ Production: Bounded queue with backpressure (prevents OOM from task backlog)
BlockingQueue<Payment> paymentQueue = new ArrayBlockingQueue<>(1000);

// Producer thread — blocks automatically if queue is FULL (backpressure!)
paymentQueue.put(payment);                              // Blocks until space available
paymentQueue.offer(payment, 500, TimeUnit.MILLISECONDS); // Wait max 500ms, returns false if timeout

// Consumer thread
Payment p = paymentQueue.take();                         // Blocks if queue is EMPTY
Payment p = paymentQueue.poll(1, TimeUnit.SECONDS);      // Wait max 1 sec, returns null if timeout

// SynchronousQueue — used in Executors.newCachedThreadPool()
// ⚠️ Zero storage! If no consumer is waiting, put() blocks immediately.
// Each put() must be matched by a take() in another thread — direct handoff.
SynchronousQueue<Order> tradingQueue = new SynchronousQueue<>();

// DelayQueue — retry pattern (payment retry after 5 seconds)
class RetryTask implements Delayed {
    private final long executeAt;
    // implements getDelay() and compareTo()
}
DelayQueue<RetryTask> retryQueue = new DelayQueue<>();
retryQueue.put(new RetryTask(5, TimeUnit.SECONDS)); // Only retrievable after 5s
```

---

## Q7: Comparable vs Comparator

### 📖 Theory:
**`Comparable<T>`** is implemented BY the class itself. It defines the class's **natural ordering** — the default way objects of this type should be sorted (e.g., `String` sorts alphabetically, `Integer` sorts numerically). A class can have **only one** `compareTo()` implementation.

**`Comparator<T>`** is an external **strategy** object. It defines an **alternate ordering** separate from the class. You can have **many different Comparators** for the same class — by name, by salary, by date, in reverse. Comparators can be composed using `thenComparing()`.

**`compareTo()` / `compare()` Contract:** Returns negative if less than, 0 if equal, positive if greater than.

```java
// Comparable — natural ordering (INSIDE the class)
public class Employee implements Comparable<Employee> {
    private String name;
    private int salary;

    @Override
    public int compareTo(Employee other) {
        // Natural order: by salary ascending
        return Integer.compare(this.salary, other.salary);
        // Use Integer.compare() — never subtract! (overflow danger with negative numbers)
    }
}

// This now works automatically:
List<Employee> list = getEmployees();
Collections.sort(list); // Uses Comparable.compareTo()

// Comparator — external, ad-hoc ordering (OUTSIDE the class)
Comparator<Employee> byName = Comparator.comparing(Employee::getName);
Comparator<Employee> bySalaryDesc = Comparator.comparingInt(Employee::getSalary).reversed();

// Chained: Sort by department, then by salary descending within each department, then by name
Comparator<Employee> complex = Comparator
    .comparing(Employee::getDepartment)
    .thenComparing(Comparator.comparingInt(Employee::getSalary).reversed())
    .thenComparing(Employee::getName);

list.sort(complex);

employees.stream()
    .sorted(complex)
    .collect(Collectors.toList());
```

---

## Q8: Non-obvious but critical Collection operations

### 📖 Theory:
Senior developers need to know the fine print — where collections behave unexpectedly.

```java
// Unmodifiable vs Immutable — a critical distinction!
// Collections.unmodifiableList() — view; original list mutations still show through!
List<String> mutableList = new ArrayList<>(List.of("a", "b"));
List<String> unmodifiable = Collections.unmodifiableList(mutableList);
mutableList.add("c");       // Works!
// unmodifiable now has ["a", "b", "c"] — it was mutated!

// Java 9 List.of() — truly immutable, no null allowed, no mutations via any reference
List<String> immutable = List.of("a", "b", "c");
// immutable.add("d"); // → UnsupportedOperationException

// Synchronized wrappers — use ConcurrentHashMap instead!
// synchronizedMap locks the ENTIRE map on every operation — one thread at a time
Map<String, String> synced = Collections.synchronizedMap(new HashMap<>());
// ⚠️ Even with synchronizedMap, iterating requires external synchronization:
synchronized (synced) {
    for (String key : synced.keySet()) { /* safe */ }
}
// ConcurrentHashMap doesn't need this — its iterator is weakly consistent

// Binary search — list must be SORTED first!
List<Integer> sorted = Arrays.asList(1, 3, 5, 7, 9);
int index = Collections.binarySearch(sorted, 5); // Returns 2 (index)
int missing = Collections.binarySearch(sorted, 4); // Returns negative (-(insertionPoint)-1)

// Frequency and disjoint
Collections.frequency(list, "apple");         // Count occurrences
Collections.disjoint(list1, list2);           // True if no common elements

// Min/Max with custom comparator
Employee highest = Collections.max(employees, Comparator.comparingDouble(Employee::getSalary));
```

---

## Q9: Streams and Collections — Advanced Operations

### 📖 Theory:

Java Streams are NOT data structures — they are a **pipeline of operations** over a data source. Key properties:
- **Lazy evaluation**: Intermediate operations (`filter`, `map`) are not executed until a terminal operation (`collect`, `findFirst`) is called.
- **Single-use**: A stream can only be consumed once. Attempting to use after terminal throws `IllegalStateException`.
- **Parallel streams**: `parallelStream()` or `stream().parallel()` splits work across `ForkJoinPool.commonPool()`. Use carefully — thread-safety requirements for the function still apply, and overhead is not worth it for small collections.

```java
// Collectors.groupingBy with downstream collector
Map<String, Long> countByDept = employees.stream()
    .collect(Collectors.groupingBy(Employee::getDepartment, Collectors.counting()));

// Top-paid employee per department
Map<String, Optional<Employee>> highestPerDept = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::getDepartment,
        Collectors.maxBy(Comparator.comparingDouble(Employee::getSalary))
    ));

// Partitioning — binary grouping (true/false)
Map<Boolean, List<Employee>> activeInactive = employees.stream()
    .collect(Collectors.partitioningBy(Employee::isActive));
List<Employee> active = activeInactive.get(true);
List<Employee> inactive = activeInactive.get(false);

// toMap — collect to Map (with merge function for duplicate keys)
Map<Long, Employee> byId = employees.stream()
    .collect(Collectors.toMap(
        Employee::getId,
        Function.identity(),
        (existing, replacement) -> existing // Merge: keep first if duplicate IDs
    ));

// Joining strings
String names = employees.stream()
    .map(Employee::getName)
    .collect(Collectors.joining(", ", "[", "]"));
// e.g., "[Alice, Bob, Charlie]"

// Statistics summary in one pass
IntSummaryStatistics stats = employees.stream()
    .mapToInt(Employee::getAge)
    .summaryStatistics();
System.out.printf("Min: %d, Max: %d, Avg: %.1f, Count: %d%n",
    stats.getMin(), stats.getMax(), stats.getAverage(), stats.getCount());

// ⚠️ Parallel stream pitfall — not thread-safe with stateful lambdas:
List<String> shared = new ArrayList<>();
// BAD: shared is not thread-safe — parallel writes are a race condition
Stream.of("a","b","c").parallel().forEach(shared::add);
// GOOD: Collect to thread-safe result
List<String> safe = Stream.of("a","b","c").parallel().collect(Collectors.toList());
```

**Interview Cross-Questions:**
> **Q: "You used `Collectors.toList()`. In Java 16, `Stream.toList()` was added. Are they the same?"**
> A: "No, they are subtly different and this catches many developers. `Collectors.toList()` returns a mutable `ArrayList` — you can add to it. `Stream.toList()` (Java 16+) returns an **unmodifiable list**. If you pass the result to a method that tries to sort or modify it, you'll get `UnsupportedOperationException`. I always use `Stream.toList()` for immutable results (usually preferred) and `Collectors.toCollection(ArrayList::new)` when I explicitly need a mutable list."
