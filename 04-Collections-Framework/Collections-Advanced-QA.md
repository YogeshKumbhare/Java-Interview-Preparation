# 📦 Collections & Generics — Advanced Interview Questions
## Target: 12+ Years Experience | GFG + InterviewBit Inspired

> **Note:** This extends Collections-QA.md with Generics deep dive, Iterator patterns, and advanced collection topics.

---

## Q: Generics in Java — Type Safety at Compile Time

### Theory:
Generics allow you to write **type-safe code** that works with different types while catching errors at compile time instead of runtime.

```java
// WITHOUT Generics (pre-Java 5) — runtime ClassCastException danger!
List list = new ArrayList();
list.add("Hello");
list.add(42); // No error at compile time!
String s = (String) list.get(1); // 💥 ClassCastException at RUNTIME

// WITH Generics — compile-time safety
List<String> list = new ArrayList<>();
list.add("Hello");
// list.add(42); // ❌ COMPILE ERROR — caught early!
String s = list.get(0); // No casting needed
```

---

## Q: Bounded Type Parameters — extends and super

```java
// UPPER BOUND — <? extends T> — "read from" (Producer)
// Accepts T or any SUBCLASS of T
public double sumOfNumbers(List<? extends Number> numbers) {
    double sum = 0;
    for (Number n : numbers) {
        sum += n.doubleValue(); // Can READ as Number
    }
    // numbers.add(42); ❌ Can't add — compiler doesn't know exact type
    return sum;
}
sumOfNumbers(List.of(1, 2, 3));          // List<Integer> ✅
sumOfNumbers(List.of(1.5, 2.5));         // List<Double> ✅

// LOWER BOUND — <? super T> — "write to" (Consumer)
// Accepts T or any SUPERCLASS of T
public void addIntegers(List<? super Integer> list) {
    list.add(1);   // Can WRITE Integer
    list.add(2);   // Can WRITE Integer
    // Integer x = list.get(0); ❌ Can only read as Object
}
addIntegers(new ArrayList<Number>());    // ✅
addIntegers(new ArrayList<Object>());    // ✅

// PECS — Producer Extends, Consumer Super (Joshua Bloch Rule)
// If you READ from a collection → use extends
// If you WRITE to a collection → use super
// If you do BOTH → don't use wildcards
```

---

## Q: Type Erasure — What happens to Generics at runtime?

```java
// Java Generics are COMPILE-TIME only!
// At runtime, all generic type info is ERASED (replaced with Object or bound)

// What you write:
List<String> strings = new ArrayList<>();
List<Integer> numbers = new ArrayList<>();

// What JVM sees at runtime (after erasure):
List strings = new ArrayList(); // Just raw List
List numbers = new ArrayList(); // Same raw List!

// This is why:
strings.getClass() == numbers.getClass(); // TRUE! Both are just ArrayList

// Consequences of Type Erasure:
// 1. Can't create generic arrays: new T[10] ❌
// 2. Can't use instanceof with generics: obj instanceof List<String> ❌
// 3. Can't create generic instance: new T() ❌
// 4. Overloading doesn't work with erased types:
//    void process(List<String> list) {} ❌ CLASH!
//    void process(List<Integer> list) {} ❌ Both erase to List

// WHY type erasure? Backward compatibility with pre-Java-5 code
```

---

## Q: Fail-Fast vs Fail-Safe Iterators

```java
// FAIL-FAST — throws ConcurrentModificationException if collection modified during iteration
List<String> list = new ArrayList<>(List.of("A", "B", "C"));
Iterator<String> it = list.iterator();
while (it.hasNext()) {
    String s = it.next();
    if (s.equals("B")) {
        list.remove(s); // 💥 ConcurrentModificationException!
    }
}
// FIX: Use iterator.remove()
Iterator<String> it2 = list.iterator();
while (it2.hasNext()) {
    if (it2.next().equals("B")) {
        it2.remove(); // ✅ Safe removal through iterator
    }
}
// FIX 2: Use removeIf() (Java 8+)
list.removeIf(s -> s.equals("B")); // ✅ Clean and safe

// FAIL-SAFE — works on a COPY of collection, no exception
ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
map.put("A", 1); map.put("B", 2);
for (Map.Entry<String, Integer> entry : map.entrySet()) {
    map.put("C", 3); // ✅ No exception — ConcurrentHashMap is fail-safe
}
// Also fail-safe: CopyOnWriteArrayList, CopyOnWriteArraySet

// TRADEOFF:
// Fail-fast: Immediate error detection, shows bugs early
// Fail-safe: No exception, but may not reflect latest changes
```

---

## Q: HashMap Internal Working (Advanced — Java 8+)

```java
// 1. hashCode() → determines BUCKET index
// 2. equals() → resolves collisions within bucket
// 3. Bucket structure:
//    - Initially: LinkedList (O(n) worst case)
//    - After 8 entries: Converts to Red-Black Tree (O(log n))
//    - Below 6 entries: Converts back to LinkedList

// Index calculation:
int hash = key.hashCode();
int index = hash & (capacity - 1); // Bitwise AND (faster than modulo)
// This is why capacity MUST be power of 2

// Load Factor & Rehashing:
// Default: capacity=16, loadFactor=0.75
// When size > capacity * loadFactor (12), HashMap DOUBLES capacity
// All entries are REHASHED (expensive!) → avoided with good initial capacity

// Null key handling:
// HashMap allows ONE null key → always goes to bucket[0]
// Hashtable does NOT allow null key → throws NullPointerException

// Java 8 optimization:
// resize() improved from O(n²) to O(n) using high/low bit splitting
// Bucket collision: LinkedList → Red-Black Tree (Treeification)
```

---

## Q: Collections Utility Class — Important Methods

```java
// Sorting
Collections.sort(list);                    // Natural order
Collections.sort(list, Comparator.reverseOrder()); // Reverse
Collections.sort(list, Comparator.comparing(Employee::getSalary));

// Searching (list MUST be sorted first)
int index = Collections.binarySearch(list, "target");

// Thread-safe wrappers
List<String> syncList = Collections.synchronizedList(new ArrayList<>());
Map<String, Integer> syncMap = Collections.synchronizedMap(new HashMap<>());
// WARNING: Still need to synchronize iteration!

// Unmodifiable (immutable view)
List<String> readOnly = Collections.unmodifiableList(list);
// readOnly.add("x"); → UnsupportedOperationException

// Java 9+ factory methods (truly immutable):
List<String> immutable = List.of("A", "B", "C");
Map<String, Integer> immMap = Map.of("key1", 1, "key2", 2);
Set<String> immSet = Set.of("X", "Y", "Z");

// Other useful methods:
Collections.frequency(list, "target");    // Count occurrences
Collections.disjoint(list1, list2);       // True if no common elements
Collections.swap(list, i, j);            // Swap elements
Collections.shuffle(list);               // Random order
```

---

## Q: TreeMap vs HashMap vs LinkedHashMap

```
| Feature | HashMap | LinkedHashMap | TreeMap |
|---------|---------|---------------|---------|
| Order | No order | Insertion order | Sorted (natural/comparator) |
| null key | 1 null key | 1 null key | ❌ No null key |
| Performance | O(1) avg | O(1) avg | O(log n) |
| Backed by | Hash table | HashTable + LinkedList | Red-Black Tree |
| Use case | General purpose | LRU cache | Sorted data, range queries |

TreeMap unique features:
  firstKey(), lastKey()
  headMap(key), tailMap(key), subMap(from, to)
  floorKey(key), ceilingKey(key)  // nearest key ≤ / ≥
```

```java
// LRU Cache with LinkedHashMap (classic interview question!)
public class LRUCache<K, V> extends LinkedHashMap<K, V> {
    private final int capacity;

    public LRUCache(int capacity) {
        super(capacity, 0.75f, true); // true = access-order (not insertion-order)
        this.capacity = capacity;
    }

    @Override
    protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
        return size() > capacity; // Remove least recently used when full
    }
}
```

---

## 🎯 Collections Cross-Questioning

### Q: "Why not always use ConcurrentHashMap instead of HashMap?"
> **Answer:** "ConcurrentHashMap has overhead — it uses CAS operations and volatile reads even for single-threaded access. In single-threaded code, HashMap is faster. Also, ConcurrentHashMap doesn't allow null keys or values (unlike HashMap). Rule: Use HashMap for single-threaded, ConcurrentHashMap for multi-threaded, Collections.synchronizedMap() only as a quick wrapper."

### Q: "When would you choose a LinkedList over ArrayList?"
> **Answer:** "Almost never in practice. ArrayList is faster for almost everything due to CPU cache locality (contiguous memory). LinkedList only wins for frequent insertions/deletions at the BEGINNING or when using it as a Deque (queue). Even for middle insertions, ArrayList's arraycopy is faster than LinkedList's pointer traversal. Modern Java best practice: default to ArrayList."

### Q: "What is the difference between Enumeration and Iterator?"
> **Answer:** "Iterator replaced Enumeration (legacy). Iterator adds `remove()` method and is fail-fast. Enumeration only has `hasMoreElements()` and `nextElement()`. Iterator works with all Collection types, while Enumeration is from legacy classes (Vector, Hashtable). Always use Iterator or enhanced for-loop."

---

## Q: Hashtable vs ConcurrentHashMap — Deep Comparison

### This is one of the TOP 5 most asked Java collections interview questions!

| Feature | Hashtable | ConcurrentHashMap |
|---------|-----------|-------------------|
| **Introduced** | Java 1.0 (legacy) | Java 1.5 (java.util.concurrent) |
| **Locking** | Synchronized on ENTIRE map | Segment-level / Bucket-level locking |
| **Performance** | ❌ Slow — one thread at a time | ✅ Fast — multiple threads concurrently |
| **null key** | ❌ Not allowed | ❌ Not allowed |
| **null value** | ❌ Not allowed | ❌ Not allowed |
| **Iterator** | Fail-safe (Enumeration) | Fail-safe (weakly consistent) |
| **Thread-safe** | ✅ Yes (coarse-grained) | ✅ Yes (fine-grained) |
| **Extends** | Dictionary (legacy) | AbstractMap |
| **Recommended** | ❌ NEVER use | ✅ Always prefer this |

### Locking Mechanism — The Key Difference:

```
Hashtable (ENTIRE map locked):
┌─────────────────────────────────────┐
│ 🔒 synchronized(this)              │  ← ONE big lock for everything
│  Bucket[0] → Entry → Entry          │
│  Bucket[1] → Entry                  │
│  Bucket[2] → Entry → Entry → Entry  │
│  Bucket[3] → Entry                  │
│  ...                                 │
└─────────────────────────────────────┘
Thread A writes to Bucket[0] → ALL other threads BLOCKED
Even Thread B reading Bucket[3] must WAIT ❌

ConcurrentHashMap (Java 7 — Segment locking):
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 🔒 Segment 0 │  │ 🔒 Segment 1 │  │ 🔒 Segment 2 │  │ 🔒 Segment 3 │
│ Bucket[0]    │  │ Bucket[4]    │  │ Bucket[8]    │  │ Bucket[12]   │
│ Bucket[1]    │  │ Bucket[5]    │  │ Bucket[9]    │  │ Bucket[13]   │
│ Bucket[2]    │  │ Bucket[6]    │  │ Bucket[10]   │  │ Bucket[14]   │
│ Bucket[3]    │  │ Bucket[7]    │  │ Bucket[11]   │  │ Bucket[15]   │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
Thread A locks Segment 0 → Thread B can STILL access Segment 1, 2, 3! ✅

ConcurrentHashMap (Java 8+ — Node/Bucket-level locking with CAS):
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│🔓 B[0] │ │🔒 B[1] │ │🔓 B[2] │ │🔓 B[3] │ │🔒 B[4] │
└────────┘ └────────┘ └────────┘ └────────┘ └────────┘
Even MORE granular! Lock only the specific bucket being modified
Uses CAS (Compare-And-Swap) for reads — NO lock needed for reading! ✅
```

### Code Examples:

```java
// ❌ DON'T use Hashtable — it's legacy!
Hashtable<String, Integer> ht = new Hashtable<>();
ht.put("A", 1);
// ht.put(null, 1);   // 💥 NullPointerException
// ht.put("A", null); // 💥 NullPointerException

// ✅ USE ConcurrentHashMap
ConcurrentHashMap<String, Integer> chm = new ConcurrentHashMap<>();
chm.put("A", 1);
// chm.put(null, 1);   // 💥 NullPointerException (same as Hashtable)
// chm.put("A", null); // 💥 NullPointerException (same as Hashtable)

// WHY no null allowed in ConcurrentHashMap?
// Because in concurrent context, you can't distinguish between:
// "key doesn't exist" vs "key exists with null value"
// map.get(key) returning null is AMBIGUOUS in multi-threaded code!
// HashMap allows it because in single-threaded code, you can use containsKey()

// ConcurrentHashMap atomic operations (not possible with Hashtable easily):
chm.putIfAbsent("B", 2);              // Atomic: put only if key doesn't exist
chm.compute("A", (k, v) -> v + 10);   // Atomic: compute new value
chm.merge("A", 5, Integer::sum);      // Atomic: merge with existing value
chm.computeIfAbsent("C", k -> expensiveCompute(k)); // Lazy initialization
chm.replace("A", 1, 100);             // Atomic: replace only if current value matches

// forEach, reduce, search — parallel operations (Java 8+):
chm.forEach(2, (key, value) ->        // parallelism threshold = 2
    System.out.println(key + "=" + value)
);

long sum = chm.reduceValues(2, Long::sum); // Parallel reduction
```

### Performance Benchmark Comparison:

```
Scenario: 4 threads, 1 million operations each

Hashtable (full synchronization):
  Writes: ~3,200 ms    ← All threads fight for ONE lock
  Reads:  ~2,800 ms    ← Even reads are synchronized! ❌

Collections.synchronizedMap(new HashMap<>()):
  Writes: ~3,100 ms    ← Same problem — one lock wrapping HashMap
  Reads:  ~2,600 ms    ← Slightly better than Hashtable

ConcurrentHashMap:
  Writes: ~800 ms      ← 4x faster! Bucket-level locking ✅
  Reads:  ~200 ms      ← 14x faster! Lock-free reads with volatile ✅
```

### When to Use What:

```
HashMap            → Single-threaded code (fastest, allows null)
ConcurrentHashMap  → Multi-threaded code (ALWAYS prefer this)
Hashtable          → NEVER use (legacy, use ConcurrentHashMap instead)
synchronizedMap()  → Quick wrapper, but ConcurrentHashMap is better

Interview one-liner:
"Hashtable locks the ENTIRE map on every operation.
 ConcurrentHashMap locks only the specific bucket being modified,
 and reads are completely lock-free using volatile + CAS.
 That's why ConcurrentHashMap is ~10x faster under concurrency."
```
