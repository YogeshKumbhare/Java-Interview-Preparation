# 🧵 Multithreading & Concurrency — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Multithreading?

**Multithreading** is a programming concept where **multiple threads of execution run concurrently** within a single process. A **thread** is the smallest unit of CPU execution — a lightweight sub-process that shares memory with other threads in the same process.

### Why multithreading exists:
- **Modern CPUs have multiple cores** — without multithreading, a Java process uses only 1 core while 7 others sit idle (on an 8-core machine)
- **I/O operations are slow** — while waiting for a DB query (50ms), CPU can process thousands of other requests
- **User experience** — UI stays responsive while background work happens

### Process vs Thread:

| Feature | Process | Thread |
|---------|---------|--------|
| Memory | Own memory space (isolated) | Shares memory with other threads (same heap) |
| Creation | Expensive (new address space) | Cheap (shares parent process memory) |
| Communication | IPC (pipes, sockets, shared memory) | Direct (shared variables) — but needs synchronization! |
| Crash impact | One process crash doesn't affect others | One thread crash can crash entire process |
| Example | Running two Java apps | Running 100 HTTP handlers in one Tomcat |

### Types of Multitasking:
- **Process-based multitasking**: Running multiple programs simultaneously (Chrome + IntelliJ + Docker)
- **Thread-based multitasking**: Running multiple threads within one program (handling 1000 HTTP requests in Tomcat)

---

## 📖 How threads work in Java — Creating threads

### Two ways to create threads:

```java
// Way 1: Extend Thread class
public class MyThread extends Thread {
    @Override
    public void run() {
        System.out.println("Thread running: " + Thread.currentThread().getName());
    }
}
MyThread t = new MyThread();
t.start(); // Creates new OS thread and calls run()
// t.run(); // ❌ WRONG — runs in CURRENT thread, not new thread

// Way 2: Implement Runnable (PREFERRED — because Java supports single inheritance)
public class MyTask implements Runnable {
    @Override
    public void run() {
        System.out.println("Task running: " + Thread.currentThread().getName());
    }
}
Thread t = new Thread(new MyTask());
t.start();

// Way 3: Lambda (Java 8+, simplest)
Thread t = new Thread(() -> System.out.println("Lambda thread running"));
t.start();

// Way 4: Callable + Future (returns a result)
Callable<Integer> task = () -> {
    Thread.sleep(2000);
    return 42; // Can return value!
};
ExecutorService executor = Executors.newSingleThreadExecutor();
Future<Integer> future = executor.submit(task);
Integer result = future.get(); // Blocks until result is ready → 42
```

---

## 📖 Thread Lifecycle — 6 States

```
       start()
NEW ──────────→ RUNNABLE ←──────────────────────────────────
                  │   ↑                                    ↑
                  │   │ (CPU schedules)                   │
                  ↓   │                                    │
               RUNNING                                     │
                  │                                        │
           ┌─────┼─────────────┐                          │
           ↓     ↓             ↓                          │
       BLOCKED  WAITING   TIMED_WAITING                   │
           │     │             │                          │
           │     │             │    (lock acquired /       │
           │     │             │    notify() / timeout)    │
           └─────┴─────────────┴──────────────────────────┘
                  │
                  ↓ (run() completes or unhandled exception)
             TERMINATED

States explained:
• NEW: Thread created, not yet started
• RUNNABLE: Ready to run, waiting for CPU time slice
• RUNNING: Currently executing on a CPU core
• BLOCKED: Waiting to acquire a monitor lock (synchronized)
• WAITING: Waiting indefinitely — wait(), join(), park()
• TIMED_WAITING: Waiting with timeout — sleep(ms), wait(ms)
• TERMINATED: run() finished, thread is dead (cannot restart)
```

---

## Q1: What is the difference between `synchronized`, `volatile`, `ReentrantLock`?

### Theory:

**`volatile`** — Controls **visibility**. When a variable is marked volatile, any write by one thread is **immediately visible** to all other threads. Without volatile, threads may read stale cached values from their CPU cache. **Does NOT provide atomicity** — `counter++` is still NOT safe with volatile.

**`synchronized`** — Provides both **mutual exclusion** (only one thread executes at a time) and **visibility** (changes are flushed to main memory). Uses **intrinsic locks** (monitor locks) built into every Java object.

**`ReentrantLock`** — Similar to synchronized but with **advanced features**: tryLock (non-blocking), fairness (longest-waiting thread gets lock first), interruptible waiting, and Condition objects for fine-grained wait/notify.

### When to use which:

| Need | Use This | Why |
|------|----------|-----|
| Simple flag (stop/start) | `volatile` | Just need visibility, no complex operations |
| Shared mutable state | `synchronized` | Simple, automatic lock release |
| Advanced locking (tryLock, fairness) | `ReentrantLock` | More control, but manual unlock in finally |
| High-read, low-write cache | `ReadWriteLock` | Multiple readers allowed simultaneously |
| Ultra-high performance reads | `StampedLock` (Java 8) | Optimistic reading — no lock for reads |

```java
// ═══════════ VOLATILE ═══════════
// USE CASE: A flag to signal thread to stop
public class WorkerThread extends Thread {
    private volatile boolean running = true;
    // Without volatile: other thread sets running=false, but THIS thread
    // continues because it reads from CPU cache (stale value = true)

    public void stopWorker() { running = false; }

    @Override
    public void run() {
        while (running) {  // Reads from main memory (not CPU cache)
            doWork();
        }
    }
}
// But volatile does NOT make this safe:
// volatile int counter = 0;
// counter++; // READ counter → INCREMENT → WRITE counter (3 steps, not atomic!)
// Two threads could both read 5, both write 6. Lost update!

// ═══════════ SYNCHRONIZED ═══════════
// USE CASE: Thread-safe counter
public class Counter {
    private int count = 0;

    // Method-level lock (locks on 'this' object)
    public synchronized void increment() {
        count++; // Only ONE thread executes this at a time
    }

    // Block-level lock (more granular — preferred)
    private final Object lock = new Object();
    public void decrement() {
        synchronized (lock) { // Lock on specific object
            count--;
        }
    }

    // Static synchronized — locks on Class object (Counter.class)
    public static synchronized void globalReset() {
        // Class-level lock, not instance-level
    }
}

// ═══════════ REENTRANT LOCK ═══════════
// USE CASE: TryLock — don't block, do something else if lock unavailable
public class TicketBookingService {
    private final ReentrantLock seatLock = new ReentrantLock(true); // true = fair
    private int availableSeats = 100;

    public BookingResult bookSeat(String userId) {
        // Try to acquire lock for 2 seconds, then give up
        boolean acquired = false;
        try {
            acquired = seatLock.tryLock(2, TimeUnit.SECONDS);
            if (!acquired) {
                return BookingResult.failed("System busy, please retry");
            }
            if (availableSeats <= 0) {
                return BookingResult.failed("Sold out");
            }
            availableSeats--;
            return BookingResult.success(userId, availableSeats);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt(); // Restore interrupted status
            return BookingResult.failed("Interrupted");
        } finally {
            if (acquired) {
                seatLock.unlock(); // ⚠️ ALWAYS in finally!
            }
        }
    }
}
```

---

## Q2: `ExecutorService` — Thread Pools Explained

### Theory: What is a Thread Pool?
A **Thread Pool** is a collection of pre-created threads that are reused for executing tasks. Instead of creating a new thread for every task (expensive: ~1MB stack + OS-level thread creation), you submit tasks to a pool which assigns them to available threads.

**Analogy:** A bank has 5 teller windows (threads). Customers (tasks) wait in a queue. When a teller finishes with one customer, the next customer in queue is served. If all tellers are busy and the queue is full, new customers are rejected.

```
ThreadPool internals:
┌─────────────────────────────────────────┐
│           Task Queue (BlockingQueue)     │
│  [Task5] [Task4] [Task3]               │
└─────────┬───────────────────────────────┘
          ↓
┌─────────────────────────────────────────┐
│         Worker Threads                   │
│  Thread-1: executing Task1               │
│  Thread-2: executing Task2               │
│  Thread-3: idle (waiting for task)       │
│  Thread-4: idle                          │
│  Thread-5: idle                          │
└─────────────────────────────────────────┘
```

### Types of Thread Pools:

```java
// 1. FIXED THREAD POOL — fixed number of threads (production standard)
ExecutorService fixed = Executors.newFixedThreadPool(10);
// Creates 10 threads. If all busy, tasks wait in unbounded queue.
// ⚠️ Problem: Queue is UNBOUNDED → can cause OutOfMemoryError if tasks pile up!

// 2. CACHED THREAD POOL — creates threads as needed
ExecutorService cached = Executors.newCachedThreadPool();
// No limit! Creates new thread for each task if all are busy.
// ⚠️ DANGEROUS in production: 10,000 tasks = 10,000 threads = crash!

// 3. SINGLE THREAD — sequential execution
ExecutorService single = Executors.newSingleThreadExecutor();
// One thread. Tasks execute in FIFO order. Guarantees ordering.

// 4. SCHEDULED — delayed or periodic tasks
ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(5);
scheduler.schedule(() -> cleanup(), 10, TimeUnit.SECONDS);     // Run once after 10s
scheduler.scheduleAtFixedRate(() -> poll(), 0, 5, TimeUnit.SECONDS);  // Every 5 seconds
scheduler.scheduleWithFixedDelay(() -> sync(), 0, 5, TimeUnit.SECONDS); // 5s after previous finishes

// 5. CUSTOM THREAD POOL (RECOMMENDED for production — full control)
ExecutorService production = new ThreadPoolExecutor(
    5,                            // corePoolSize — always keep 5 threads alive
    20,                           // maximumPoolSize — scale up to 20 under load
    60L, TimeUnit.SECONDS,        // keepAliveTime — idle threads beyond core die after 60s
    new LinkedBlockingQueue<>(500), // BOUNDED queue! Max 500 tasks waiting
    new ThreadFactory() {
        private final AtomicInteger counter = new AtomicInteger(0);
        @Override
        public Thread newThread(Runnable r) {
            Thread t = new Thread(r);
            t.setName("payment-worker-" + counter.incrementAndGet()); // Named threads!
            t.setDaemon(false);
            t.setUncaughtExceptionHandler((thread, ex) -> {
                log.error("Thread {} crashed: {}", thread.getName(), ex.getMessage(), ex);
            });
            return t;
        }
    },
    new ThreadPoolExecutor.CallerRunsPolicy() // Rejection policy
);

// How ThreadPoolExecutor decides:
// 1. Task arrives → if active threads < corePoolSize → create new thread
// 2. Task arrives → if active threads >= corePoolSize → put in queue
// 3. Queue is full → if active threads < maximumPoolSize → create new thread
// 4. Queue full AND maximumPoolSize reached → apply REJECTION POLICY
```

### Rejection Policies Explained:

| Policy | What happens when queue is full AND maxPool reached |
|--------|----------------------------------------------|
| `AbortPolicy` (default) | Throws `RejectedExecutionException` → task is lost |
| `CallerRunsPolicy` | The thread that submitted the task runs it itself → **backpressure** |
| `DiscardPolicy` | Silently drops the new task → **dangerous**, task lost without notice |
| `DiscardOldestPolicy` | Drops the oldest task in queue, submits new one |

---

## Q3: CompletableFuture — Async Programming

### Theory: What is CompletableFuture?
`CompletableFuture` (Java 8) enables **non-blocking, asynchronous programming** with a fluent API for composing, combining, and chaining async operations. Think of it as JavaScript Promises for Java.

**Why it exists:** Without it, combining async results was painful — nested callbacks, manual thread management, no error handling pipeline.

```java
// ═══ BASIC: Run task asynchronously ═══
CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> {
    // Runs in ForkJoinPool.commonPool() by default
    return callExternalApi(); // Non-blocking
});

String result = future.get();     // Blocks until done
String result = future.join();    // Same but throws unchecked exception
String result = future.get(5, TimeUnit.SECONDS); // With timeout

// ═══ CHAINING: Step-by-step pipeline ═══
CompletableFuture.supplyAsync(() -> fetchUserFromDB(userId))      // Step 1: DB call
    .thenApply(user -> enrichWithProfile(user))                    // Step 2: Enrich
    .thenApplyAsync(user -> fetchOrders(user))                     // Step 3: On different thread
    .thenAccept(orders -> sendNotification(orders))                // Step 4: No return value
    .exceptionally(ex -> {                                          // Error handling
        log.error("Pipeline failed: {}", ex.getMessage());
        return null;
    });

// ═══ PARALLEL: Multiple independent calls ═══
// Scenario: Build order summary (need user, payment, items — all independent)
@Service
public class OrderSummaryService {
    public OrderSummary build(String orderId) {
        CompletableFuture<User> userFuture =
            CompletableFuture.supplyAsync(() -> userService.getUser(orderId));

        CompletableFuture<Payment> paymentFuture =
            CompletableFuture.supplyAsync(() -> paymentService.getPayment(orderId));

        CompletableFuture<List<Item>> itemsFuture =
            CompletableFuture.supplyAsync(() -> inventoryService.getItems(orderId));

        // Wait for ALL to finish, then combine
        return CompletableFuture.allOf(userFuture, paymentFuture, itemsFuture)
            .thenApply(v -> new OrderSummary(
                userFuture.join(),      // Already complete
                paymentFuture.join(),
                itemsFuture.join()
            ))
            .get(5, TimeUnit.SECONDS); // 5-second global timeout
    }
    // Without parallel: 3 sequential calls = 200ms + 150ms + 100ms = 450ms
    // With parallel: slowest call determines total = max(200, 150, 100) = 200ms!
}

// ═══ COMBINE TWO FUTURES ═══
CompletableFuture<String> priceFuture = CompletableFuture.supplyAsync(() -> getPrice());
CompletableFuture<String> stockFuture = CompletableFuture.supplyAsync(() -> getStock());

CompletableFuture<String> combined = priceFuture.thenCombine(stockFuture,
    (price, stock) -> "Price: " + price + ", Stock: " + stock);

// ═══ FIRST TO COMPLETE (race) ═══
CompletableFuture<String> fastest = CompletableFuture.anyOf(api1, api2, api3)
    .thenApply(result -> (String) result); // Take whichever finishes first
```

---

## Q4: Deadlock — What, Why, How to Prevent

### Theory: What is a Deadlock?
A **deadlock** is a situation where two or more threads are **permanently blocked**, each waiting for a lock that the other holds. No thread can proceed — the system is frozen.

**Four conditions for deadlock (ALL must be true simultaneously):**
1. **Mutual Exclusion**: Resources cannot be shared (only one thread can hold a lock)
2. **Hold and Wait**: Thread holds one resource while waiting for another
3. **No Preemption**: Locks cannot be forcefully taken from a thread
4. **Circular Wait**: Thread A waits for B, B waits for A (circular chain)

**Analogy:** Two cars meet on a narrow one-lane bridge from opposite directions. Neither can move forward, neither is willing to reverse. Both wait forever.

```java
// ═══ DEADLOCK EXAMPLE ═══
Object lock1 = new Object();
Object lock2 = new Object();

// Thread 1: Acquires lock1, then tries to get lock2
Thread t1 = new Thread(() -> {
    synchronized (lock1) {         // ✅ Acquired lock1
        sleep(100);                 // Small delay → ensures both threads lock
        synchronized (lock2) {     // ❌ WAITING for lock2 (held by t2)
            System.out.println("Thread 1: Both locks");
        }
    }
});

// Thread 2: Acquires lock2, then tries to get lock1 (REVERSE ORDER!)
Thread t2 = new Thread(() -> {
    synchronized (lock2) {         // ✅ Acquired lock2
        sleep(100);
        synchronized (lock1) {     // ❌ WAITING for lock1 (held by t1)
            System.out.println("Thread 2: Both locks");
        }
    }
});
// DEADLOCK! t1 holds lock1, waits for lock2. t2 holds lock2, waits for lock1.
// Neither can proceed. Both frozen forever.

// ═══ PREVENTION STRATEGIES ═══

// Strategy 1: LOCK ORDERING — always acquire locks in SAME ORDER
Thread t1 = new Thread(() -> {
    synchronized (lock1) {        // Always lock1 first
        synchronized (lock2) {    // Then lock2
            doWork();
        }
    }
});
Thread t2 = new Thread(() -> {
    synchronized (lock1) {        // SAME ORDER: lock1 first
        synchronized (lock2) {    // Then lock2
            doWork();
        }
    }
});
// No circular wait → no deadlock!

// Strategy 2: TRYLOCK with TIMEOUT (ReentrantLock)
ReentrantLock lockA = new ReentrantLock();
ReentrantLock lockB = new ReentrantLock();

public void transferMoney(Account from, Account to, BigDecimal amount) {
    boolean locked = false;
    try {
        locked = lockA.tryLock(1, TimeUnit.SECONDS);
        if (locked) {
            boolean locked2 = lockB.tryLock(1, TimeUnit.SECONDS);
            if (locked2) {
                try {
                    from.debit(amount);
                    to.credit(amount);
                } finally {
                    lockB.unlock();
                }
            }
        }
        if (!locked) {
            // Could not acquire locks — retry or escalate
            log.warn("Transfer failed — locks unavailable. Retrying...");
        }
    } finally {
        if (locked) lockA.unlock();
    }
}

// Strategy 3: Use higher-level concurrency utilities
// ConcurrentHashMap, BlockingQueue, Atomic* → avoid explicit locks entirely
```

---

## Q5: `wait()` vs `sleep()` — Deep Difference

### Theory:

| Feature | `wait()` | `sleep()` |
|---------|----------|-----------|
| Belongs to | `java.lang.Object` class | `java.lang.Thread` class |
| Lock release | **YES** — releases monitor lock | **NO** — holds lock throughout |
| Wake up by | `notify()`, `notifyAll()`, or timeout | Only by timeout or `interrupt()` |
| Where to call | MUST be inside `synchronized` block | Anywhere |
| Purpose | **Inter-thread communication** | **Pause current thread** |

```java
// wait() — "I'm done for now, let someone else work on this shared resource"
// sleep() — "I'm tired, I'll just nap while holding everything"

// PRODUCER-CONSUMER using wait/notify (classic interview pattern)
public class MessageQueue {
    private final Queue<String> queue = new LinkedList<>();
    private final int MAX_SIZE = 10;

    // Producer: add messages to queue
    public synchronized void produce(String message) throws InterruptedException {
        while (queue.size() == MAX_SIZE) {
            // Queue full! Release lock and WAIT for consumer to remove items
            wait(); // Releases the lock → consumer can now enter
        }
        queue.add(message);
        System.out.println("Produced: " + message + ", Queue size: " + queue.size());
        notifyAll(); // Wake up consumers waiting for messages
    }

    // Consumer: remove messages from queue
    public synchronized String consume() throws InterruptedException {
        while (queue.isEmpty()) {
            // Queue empty! Release lock and WAIT for producer to add items
            wait(); // Releases the lock → producer can now enter
        }
        String message = queue.poll();
        System.out.println("Consumed: " + message + ", Queue size: " + queue.size());
        notifyAll(); // Wake up producers waiting for space
        return message;
    }
}

// WHY while() and not if()?
// Spurious wakeup: thread can wake up without notify/notifyAll being called.
// Always re-check condition after waking up!
```

---

## Q6: ThreadLocal — What and Why

### Theory:
**ThreadLocal** provides **per-thread variable storage**. Each thread accessing a ThreadLocal variable gets its own independent copy. No synchronization needed because no sharing!

**Use cases:**
- **Request context** in web apps (current user, trace ID, locale)
- **SimpleDateFormat** cache (notoriously NOT thread-safe)
- **Database connection per thread** (before connection pooling)

**Danger:** In thread pools (Tomcat, ExecutorService), threads are **reused**. If you don't clean up ThreadLocal → **memory leak** AND **data leaking between requests**.

```java
// Real-world: Request context in Spring Boot
public class RequestContext {
    private static final ThreadLocal<Map<String, String>> CONTEXT =
        ThreadLocal.withInitial(HashMap::new);

    public static void setUserId(String userId) {
        CONTEXT.get().put("userId", userId);
    }

    public static String getUserId() {
        return CONTEXT.get().get("userId");
    }

    public static void setTraceId(String traceId) {
        CONTEXT.get().put("traceId", traceId);
    }

    // ⚠️ CRITICAL: Must call this in finally!
    public static void clear() {
        CONTEXT.remove(); // Without this: memory leak + data leak!
    }
}

// Filter that sets and clears context
@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class RequestContextFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws IOException, ServletException {
        try {
            RequestContext.setUserId(request.getHeader("X-User-Id"));
            RequestContext.setTraceId(UUID.randomUUID().toString());
            chain.doFilter(request, response);
        } finally {
            RequestContext.clear(); // ⚠️ ALWAYS CLEAR IN FINALLY!
        }
    }
}

// Later in any service, same thread can access:
String userId = RequestContext.getUserId(); // Gets THIS thread's userId
```

---

## Q7: Virtual Threads (Java 21) — Project Loom

### Theory: What are Virtual Threads?

**Traditional (Platform) Threads:** Each Java thread maps 1:1 to an OS thread. OS threads are heavy (~1MB stack, kernel scheduling). Creating 10,000 OS threads = 10GB RAM just for stacks!

**Virtual Threads:** Lightweight threads managed by the JVM, not the OS. They're mapped M:N to a small pool of OS threads (carrier threads). You can create **1 million** virtual threads without issues.

**Analogy:** Platform threads are like hiring a dedicated driver for each car journey. Virtual threads are like Uber — a small pool of drivers serves millions of rides.

```
Platform Threads:
  Java Thread 1 ──→ OS Thread 1 (1MB stack)
  Java Thread 2 ──→ OS Thread 2 (1MB stack)
  ...
  Java Thread 1000 ──→ OS Thread 1000 (1GB RAM used!)

Virtual Threads:
  Virtual Thread 1 ─┐
  Virtual Thread 2  │──→ Carrier Thread 1 (OS Thread)
  Virtual Thread 3 ─┘
  Virtual Thread 4 ─┐
  Virtual Thread 5  │──→ Carrier Thread 2 (OS Thread)
  Virtual Thread 6 ─┘
  ...
  Virtual Thread 1,000,000 → Only ~16 OS threads needed!
```

```java
// Creating Virtual Threads (Java 21+)
Thread vThread = Thread.ofVirtual()
    .name("vt-worker")
    .start(() -> {
        // Blocking I/O is FINE with virtual threads!
        String result = httpClient.send(request); // Blocks virtual thread, NOT OS thread
    });

// With ExecutorService (most practical)
try (ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor()) {
    // Submit 1 MILLION tasks — each gets its own virtual thread!
    List<Future<String>> futures = new ArrayList<>();
    for (int i = 0; i < 1_000_000; i++) {
        futures.add(executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1)); // Each sleeps 1 second
            return "done"; // But overall takes ~1 second total!
        }));
    }
}

// Spring Boot 3.2+ — enable globally!
// application.properties:
// spring.threads.virtual.enabled=true
// Every HTTP request handler now uses virtual threads instead of platform threads!
```

**When to use Virtual Threads:**
- ✅ I/O-bound: HTTP calls, DB queries, file I/O
- ❌ CPU-bound: Computing Fibonacci, ML training, image processing

**When NOT to use:**
- Tasks that use `synchronized` heavily (pins virtual thread to carrier)
- Tasks that are CPU-intensive (no benefit — CPU is the bottleneck)
