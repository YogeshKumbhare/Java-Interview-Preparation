# 🔄 Multithreading Advanced — Concurrency Utilities & Patterns
## Target: 12+ Years Experience | howtodoinjava.com Inspired

> **Note:** This extends Multithreading-QA.md with concurrency utilities and classic patterns.

---

## Q: CountDownLatch vs CyclicBarrier vs Semaphore

### CountDownLatch — "Wait for N tasks to complete"
```java
// Scenario: Application startup — wait for all services to be ready
public class AppStartup {
    public static void main(String[] args) throws InterruptedException {
        int serviceCount = 3;
        CountDownLatch latch = new CountDownLatch(serviceCount);

        // Start services in parallel
        new Thread(() -> { initDatabase();    latch.countDown(); }).start();
        new Thread(() -> { initCache();       latch.countDown(); }).start();
        new Thread(() -> { initKafka();       latch.countDown(); }).start();

        latch.await(); // ⏳ Main thread blocks until count reaches 0
        System.out.println("All services ready! Starting server...");

        // With timeout:
        boolean ready = latch.await(30, TimeUnit.SECONDS);
        if (!ready) throw new StartupException("Services didn't start in 30s");
    }
}
// ONE-TIME USE — count can only go down, never reset
// countDown() is called by workers, await() by the waiting thread
```

### CyclicBarrier — "All threads wait for each other"
```java
// Scenario: Parallel computation — all threads must reach checkpoint before proceeding
public class ParallelComputation {
    public static void main(String[] args) {
        int threads = 3;
        // Barrier action runs when ALL threads arrive
        CyclicBarrier barrier = new CyclicBarrier(threads, () -> {
            System.out.println("All threads reached barrier! Merging results...");
        });

        for (int i = 0; i < threads; i++) {
            int partition = i;
            new Thread(() -> {
                System.out.println("Thread " + partition + " processing...");
                processPartition(partition);
                try {
                    barrier.await(); // ⏳ Wait for others to reach this point
                } catch (InterruptedException | BrokenBarrierException e) {
                    Thread.currentThread().interrupt();
                }
                // All proceed together after barrier
                System.out.println("Thread " + partition + " continuing...");
            }).start();
        }
    }
}
// REUSABLE — automatically resets after all threads arrive
// All threads wait for EACH OTHER (unlike CountDownLatch where one thread waits)
```

### Semaphore — "Limit concurrent access to a resource"
```java
// Scenario: Connection pool — max 5 concurrent database connections
public class ConnectionPool {
    private final Semaphore semaphore;
    private final Queue<Connection> pool;

    public ConnectionPool(int maxConnections) {
        this.semaphore = new Semaphore(maxConnections); // 5 permits
        this.pool = new ConcurrentLinkedQueue<>();
        for (int i = 0; i < maxConnections; i++) {
            pool.add(createConnection());
        }
    }

    public Connection acquire() throws InterruptedException {
        semaphore.acquire(); // ⏳ Blocks if all 5 permits taken
        return pool.poll();
    }

    public void release(Connection conn) {
        pool.offer(conn);
        semaphore.release(); // Return permit — another thread can proceed
    }
}

// Fair Semaphore — FIFO ordering (threads served in arrival order)
Semaphore fairSemaphore = new Semaphore(5, true); // true = fair
```

### Comparison Table:
| Feature | CountDownLatch | CyclicBarrier | Semaphore |
|---------|---------------|---------------|-----------|
| Purpose | Wait for N events | Sync threads at checkpoint | Limit concurrent access |
| Reusable | ❌ One-time use | ✅ Auto-resets | ✅ Reusable |
| Who waits | One thread waits | All threads wait for each other | Thread waits for permit |
| Release | countDown() by workers | await() by all | release() by any thread |
| Use case | Startup, shutdown | Parallel phases | Rate limiting, pools |

---

## Q: Producer-Consumer Pattern (Classic Interview Coding Question)

### Using BlockingQueue (Preferred):
```java
// BlockingQueue handles all synchronization automatically!
public class ProducerConsumer {
    private final BlockingQueue<String> queue = new LinkedBlockingQueue<>(10); // Capacity 10

    // Producer — blocks if queue is full
    class Producer implements Runnable {
        @Override
        public void run() {
            try {
                for (int i = 0; i < 100; i++) {
                    String item = "Item-" + i;
                    queue.put(item); // ⏳ Blocks if queue full (backpressure!)
                    System.out.println("Produced: " + item);
                }
                queue.put("POISON_PILL"); // Signal consumer to stop
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    // Consumer — blocks if queue is empty
    class Consumer implements Runnable {
        @Override
        public void run() {
            try {
                while (true) {
                    String item = queue.take(); // ⏳ Blocks if queue empty
                    if ("POISON_PILL".equals(item)) break; // Shutdown signal
                    System.out.println("Consumed: " + item);
                    process(item);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }

    public void start() {
        new Thread(new Producer()).start();
        new Thread(new Consumer()).start();
        new Thread(new Consumer()).start(); // Multiple consumers!
    }
}
```

### Using wait/notify (Classic Interview Version):
```java
// Manual synchronization — interviewers love asking this!
public class ProducerConsumerWaitNotify {
    private final Queue<Integer> queue = new LinkedList<>();
    private final int capacity = 10;

    public void produce(int value) throws InterruptedException {
        synchronized (queue) {
            while (queue.size() == capacity) {
                queue.wait(); // ⏳ Release lock, wait for consumer to consume
            }
            queue.add(value);
            System.out.println("Produced: " + value);
            queue.notifyAll(); // Wake up waiting consumers
        }
    }

    public int consume() throws InterruptedException {
        synchronized (queue) {
            while (queue.isEmpty()) {
                queue.wait(); // ⏳ Release lock, wait for producer to produce
            }
            int value = queue.poll();
            System.out.println("Consumed: " + value);
            queue.notifyAll(); // Wake up waiting producers
            return value;
        }
    }
}
// KEY POINTS:
// 1. ALWAYS use while() loop, not if(), for wait() — spurious wakeups!
// 2. Use notifyAll() not notify() — notify() wakes ONE random thread
// 3. wait() and notify() MUST be inside synchronized block
```

---

## Q: BlockingQueue Implementations

```
BlockingQueue Implementations:
├── ArrayBlockingQueue: Fixed size, fair/unfair, backed by array
├── LinkedBlockingQueue: Optionally bounded, higher throughput than Array
├── PriorityBlockingQueue: Unbounded, elements sorted by priority
├── SynchronousQueue: Zero capacity — handoff point (producer blocks until consumer takes)
├── DelayQueue: Elements available only after delay expires (scheduled tasks)
└── LinkedTransferQueue: Producer waits until consumer receives (like SynchronousQueue + queue)

| Method | Throws Exception | Returns Value | Blocks | Times Out |
|--------|-----------------|---------------|--------|-----------|
| Insert | add(e)          | offer(e)      | put(e) | offer(e, time, unit) |
| Remove | remove()        | poll()        | take() | poll(time, unit) |
| Examine| element()       | peek()        | —      | — |
```

---

## Q: ReentrantLock vs synchronized

```java
// synchronized — simple, implicit lock
public synchronized void transfer(Account from, Account to, int amount) {
    from.debit(amount);
    to.credit(amount);
}

// ReentrantLock — explicit lock with more features
private final ReentrantLock lock = new ReentrantLock(true); // true = fair

public void transferWithLock(Account from, Account to, int amount) {
    lock.lock(); // Acquire lock
    try {
        from.debit(amount);
        to.credit(amount);
    } finally {
        lock.unlock(); // ALWAYS unlock in finally!
    }
}

// ReentrantLock advantages over synchronized:
// 1. tryLock() — non-blocking attempt
boolean acquired = lock.tryLock(5, TimeUnit.SECONDS); // Timeout!
if (!acquired) throw new TimeoutException("Could not acquire lock");

// 2. lockInterruptibly() — can interrupt a waiting thread
lock.lockInterruptibly();

// 3. Condition variables (multiple wait sets)
Condition notEmpty = lock.newCondition();
Condition notFull = lock.newCondition();
// notEmpty.await();  — wait until not empty
// notFull.signal();  — signal one waiting thread

// 4. Fair locking — threads served in FIFO order
ReentrantLock fairLock = new ReentrantLock(true);
```

| Feature | synchronized | ReentrantLock |
|---------|-------------|---------------|
| Syntax | Implicit (block/method) | Explicit (lock/unlock) |
| Try-lock | ❌ No | ✅ tryLock(timeout) |
| Interruptible | ❌ No | ✅ lockInterruptibly() |
| Fair locking | ❌ No | ✅ Optional |
| Conditions | 1 (wait/notify) | Multiple Condition objects |
| Performance | Similar (since Java 6 optimized) | Similar |
| **Use** | Simple cases | Complex locking needs |

---

## Q: ReadWriteLock — Concurrent Readers, Exclusive Writer

```java
// Multiple threads can READ simultaneously, but WRITE is exclusive
// Perfect for: caches, config stores, read-heavy workloads

private final ReadWriteLock rwLock = new ReentrantReadWriteLock();
private final Lock readLock = rwLock.readLock();
private final Lock writeLock = rwLock.writeLock();
private Map<String, Object> cache = new HashMap<>();

// Multiple readers can execute simultaneously
public Object get(String key) {
    readLock.lock();
    try {
        return cache.get(key);
    } finally {
        readLock.unlock();
    }
}

// Writers get exclusive access — blocks all readers and other writers
public void put(String key, Object value) {
    writeLock.lock();
    try {
        cache.put(key, value);
    } finally {
        writeLock.unlock();
    }
}
// StampedLock (Java 8+) — optimistic read lock (even faster for reads)
```

---

## Q: Thread dump — What is it and how to capture it?

```
Thread Dump = snapshot of all threads with their states and stack traces.
Use it to diagnose: deadlocks, hangs, high CPU, thread leaks.

How to capture:
1. jstack <pid>
2. kill -3 <pid> (Linux/Mac)
3. jcmd <pid> Thread.print
4. VisualVM (GUI)
5. Actuator: /actuator/threaddump (Spring Boot)
6. Programmatic: Thread.getAllStackTraces()

Thread States in dump:
  RUNNABLE — executing or ready to execute
  BLOCKED — waiting to acquire a monitor lock
  WAITING — Object.wait(), Thread.join(), LockSupport.park()
  TIMED_WAITING — Thread.sleep(), wait(timeout)
  NEW — created but not started
  TERMINATED — execution completed

Deadlock detection:
  jstack shows "Found one Java-level deadlock:" at the bottom
  Lists the threads and which locks they hold vs. which they're waiting for
```

---

## 🎯 Concurrency Cross-Questioning

### Q: "sleep() vs wait() — what's the difference?"
> **Answer:** "`sleep()` is a Thread method — pauses for specified time, does NOT release the lock. `wait()` is an Object method — must be called inside `synchronized`, RELEASES the lock, and waits until `notify()` or `notifyAll()` is called. Use `sleep()` for timed pauses, `wait()` for inter-thread communication."

### Q: "What is a ForkJoinPool? When do you use it?"
> **Answer:** "ForkJoinPool is for **divide-and-conquer** parallelism. It splits a task into subtasks (fork), processes them in parallel, then combines results (join). Uses **work-stealing** — idle threads steal tasks from busy threads' queues. Java's `parallelStream()` and `CompletableFuture` use the common ForkJoinPool internally. Use it for CPU-intensive recursive tasks (merge sort, tree processing), NOT for I/O tasks."

### Q: "What is a daemon thread? What happens if only daemon threads are left?"
> **Answer:** "Daemon threads are background helper threads (GC, finalizer). When all non-daemon (user) threads finish, the JVM exits immediately — daemon threads are killed without running their `finally` blocks. Set with `thread.setDaemon(true)` BEFORE `thread.start()`. Example: a logging thread should be daemon — don't keep the app alive just because it's running."
