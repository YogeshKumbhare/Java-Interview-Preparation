# 🌐 Distributed Systems — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is a Distributed System?

A **distributed system** is a collection of **independent computers** (nodes) that appear to the user as a **single coherent system**. The nodes communicate over a network and coordinate to achieve a common goal.

**Why distributed systems?** Single machines have limits. You can't serve 1 billion users from one server. Distributed systems provide:
- **Scalability** — add more nodes to handle more load
- **Fault tolerance** — if one node dies, others continue
- **Geographic distribution** — serve users from nearby data centers

**Challenges:** Network is unreliable, clocks are out of sync, nodes can crash at any time.

---

## 📖 CAP Theorem — The Fundamental Trade-off

### Theory:
The **CAP theorem** (Brewer's theorem, 2000) states that a distributed system can guarantee at most **TWO** of the following three properties simultaneously:

```
       C (Consistency)
      / \
     /   \
    /     \
   /  Pick \
  / Only 2  \
 /           \
A ─────────── P
(Availability)  (Partition Tolerance)
```

1. **Consistency (C)**: Every read receives the **most recent write** or an error. All nodes see the same data at the same time.

2. **Availability (A)**: Every request receives a **response** (not necessarily the most recent data). The system always responds, never says "system unavailable."

3. **Partition Tolerance (P)**: The system continues to operate even when **network partitions** occur (messages between nodes are dropped or delayed).

### Why you MUST choose P:
In a real distributed system, **network partitions WILL happen** (cables cut, switches fail, packets lost). So you MUST pick P. The real choice is between:
- **CP (Consistency + Partition Tolerance)**: System may become unavailable during partition, but data is always correct.
- **AP (Availability + Partition Tolerance)**: System always responds, but data may be stale during partition.

### Real-world examples:
```
CP Systems (favor correctness):
├── PostgreSQL (ACID, synchronous replication)
├── MongoDB (with write concern majority)
├── Redis (single instance, not cluster)
├── ZooKeeper / etcd (consensus-based)
└── Banking transactions, stock trading

AP Systems (favor availability):
├── Cassandra (tunable consistency)
├── DynamoDB (eventually consistent by default)
├── DNS (propagation delay, stale records OK)
├── CDN caches (serve stale content over error)
└── Social media feeds, shopping carts
```

---

## 📖 Consistency Models

### Strong Consistency
After a write completes, **every subsequent read** will see that write. Expensive but safe.
```
Client A: writes X = 10
Client B: reads X → always sees 10 (even from different node)
```

### Eventual Consistency
After a write, replicas will **eventually** converge to the same value. May read stale data temporarily.
```
Client A: writes X = 10 (to Node 1)
Client B: reads X from Node 2 → might see old value 5
... a few milliseconds later ...
Client B: reads X from Node 2 → now sees 10
```

### Causal Consistency
If event A **causes** event B, then everyone sees A before B. Unrelated events may be seen in any order.

### Read-Your-Own-Write Consistency
After you write, **you** always see your own write. Others may see it later.

---

## 📖 Consensus Algorithms — How nodes agree

### Theory: What is Consensus?
In a distributed system, consensus is the problem of getting **multiple nodes to agree on a single value** even when some nodes may fail. This is fundamental for leader election, distributed locks, and replicated state machines.

### Raft Algorithm (most popular, used by etcd, Consul):
```
Three roles: Leader, Follower, Candidate

Normal operation:
1. One node is LEADER (receives all writes)
2. Leader sends log entries to FOLLOWERS
3. Followers acknowledge
4. When MAJORITY (quorum) ack → entry is committed
5. Leader responds to client: "Write committed"

Leader election:
1. Followers don't hear from Leader (heartbeat timeout)
2. A Follower becomes CANDIDATE → starts election
3. Candidate votes for itself, asks others, "Vote for me?"
4. If MAJORITY vote yes → becomes new LEADER
5. New Leader starts sending heartbeats

Quorum = (N/2) + 1
3 nodes → quorum = 2 (tolerate 1 failure)
5 nodes → quorum = 3 (tolerate 2 failures)
7 nodes → quorum = 4 (tolerate 3 failures)
```

#### Real-time Example Code: Leader Election using Apache Curator (ZooKeeper)
When running multiple instances of a cron job microservice, you only want *one* instance to actually fire the job (the Leader).
```java
@Service
@Slf4j
public class LeaderElectionService implements LeaderSelectorListener, Closeable {

    private final LeaderSelector leaderSelector;
    private final CuratorFramework client;

    public LeaderElectionService(CuratorFramework client) {
        this.client = client;
        // All instances try to acquire lock at this specific ZK path
        this.leaderSelector = new LeaderSelector(client, "/mutex/leader/cron-job", this);
        this.leaderSelector.autoRequeue(); // Re-join election if we lose leadership
        this.leaderSelector.start();
    }

    @Override
    public void takeLeadership(CuratorFramework client) throws Exception {
        log.info("I am the LEADER! Starting to process exclusive jobs...");
        try {
            // Keep leadership as long as this method doesn't exit.
            // If the node crashes, ZK detects session loss and elects a new leader.
            while (!Thread.currentThread().isInterrupted()) {
                doLeaderExclusiveWork();
                Thread.sleep(1000);
            }
        } catch (InterruptedException e) {
            log.warn("Leadership interrupted, relinquishing...");
            Thread.currentThread().interrupt();
        } finally {
            log.info("I am relinquishing leadership!");
        }
    }

    private void doLeaderExclusiveWork() {
        // Only the elected leader executes this code
    }

    @Override
    public void stateChanged(CuratorFramework client, ConnectionState newState) {
        if (newState == ConnectionState.SUSPENDED || newState == ConnectionState.LOST) {
            throw new CancelLeadershipException();
        }
    }

    @Override
    public void close() {
        leaderSelector.close();
    }
}
```

---

## 📖 Sharding — Horizontal Database Partitioning

### Theory:
**Sharding** splits a large dataset across **multiple databases** (shards), each containing a subset of the data. Each shard is an independent database on a separate machine.

### Sharding Strategies:

```
1. Hash-Based Sharding:
   shard = hash(userId) % num_shards
   User 101 → hash(101) % 4 = 1 → Shard 1
   User 205 → hash(205) % 4 = 3 → Shard 3
   Pro: Even distribution
   Con: Adding/removing shards requires rehashing ALL data (resharding)

2. Range-Based Sharding:
   Users 1-1,000,000 → Shard 1
   Users 1,000,001-2,000,000 → Shard 2
   Pro: Simple, range queries easy
   Con: Hot spots (recent users all on last shard)

3. Directory-Based Sharding:
   Lookup table: { userId → shardId }
   Pro: Flexible, can move users between shards
   Con: Lookup table is single point of failure
```

### Challenges with Sharding:
```
1. Cross-shard queries: JOIN across shards is very expensive
2. Cross-shard transactions: Need distributed transactions (2PC)
3. Rebalancing: Adding new shard requires data migration
4. Application complexity: Code must know which shard to query
5. Unique IDs: Auto-increment doesn't work across shards
   → Solution: Snowflake ID, UUID, or sequence service
```

#### Real-time Example Code: Hash-Based Database Sharding in Spring Boot
Using `AbstractRoutingDataSource` to dynamically route database queries to different shards based on the `userId`.

```java
// 1. Context Holder to store the current shard key (ThreadLocal)
public class ShardContextHolder {
    private static final ThreadLocal<String> CONTEXT = new ThreadLocal<>();
    public static void setShard(String shard) { CONTEXT.set(shard); }
    public static String getShard() { return CONTEXT.get(); }
    public static void clear() { CONTEXT.remove(); }
}

// 2. The Routing DataSource
public class ShardingDataSource extends AbstractRoutingDataSource {
    @Override
    protected Object determineCurrentLookupKey() {
        return ShardContextHolder.getShard(); // Returns "SHARD_1" or "SHARD_2"
    }
}

// 3. Service Layer resolving the shard before querying
@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;

    public User getUserProfile(Long userId) {
        try {
            // Determine Shard dynamically (Hash-based)
            int shardNumber = (int) (userId % 2) + 1; // Produces 1 or 2
            ShardContextHolder.setShard("SHARD_" + shardNumber);
            
            // Query executes against the elected database shard
            return userRepository.findById(userId).orElseThrow();
        } finally {
            ShardContextHolder.clear(); // Always clean up ThreadLocal!
        }
    }
}

// Configuration setup (simplified)
@Bean
public DataSource dataSource() {
    Map<Object, Object> targetDataSources = new HashMap<>();
    targetDataSources.put("SHARD_1", shard1DataSource());
    targetDataSources.put("SHARD_2", shard2DataSource());

    ShardingDataSource router = new ShardingDataSource();
    router.setTargetDataSources(targetDataSources);
    router.setDefaultTargetDataSource(shard1DataSource());
    return router;
}
```

---

## 📖 Replication — Data Redundancy

### Theory:
**Replication** means keeping **copies of the same data** on multiple nodes. If one node fails, another has the data. There are two main strategies:

### Synchronous Replication:
```
Client → Write to Primary
Primary → sends write to Replica 1 } Waits for BOTH
Primary → sends write to Replica 2 } to acknowledge
Primary → responds to Client: "Write committed"

Pro: Strong consistency — client knows ALL replicas have the data
Con: SLOW — must wait for slowest replica. If any replica is down → write fails
```

### Asynchronous Replication:
```
Client → Write to Primary
Primary → responds to Client: "Write committed" (FAST!)
Primary → sends write to Replica 1 (in background)
Primary → sends write to Replica 2 (in background)

Pro: FAST — client doesn't wait for replicas
Con: If Primary crashes before replicating → DATA LOSS
     Replicas may serve STALE data
```

### Semi-synchronous (Practical):
```
Wait for at least 1 replica to ack (out of N)
Balance between speed and safety
PostgreSQL: synchronous_commit = on, synchronous_standby_names = 'ANY 1 (replica1, replica2)'
```

---

## 📖 Distributed Locks

### Theory: Why distributed locks?
In a single-JVM app, `synchronized` or `ReentrantLock` prevents concurrent access. In microservices with multiple JVMs, you need a **distributed lock** — a lock visible to all instances.

### Redis-based Distributed Lock:
```java
@Service
public class DistributedLockService {
    private final StringRedisTemplate redis;

    /**
     * Acquire a distributed lock.
     * Only ONE instance across all JVMs can hold this lock at a time.
     */
    public boolean acquireLock(String lockKey, String requestId, Duration timeout) {
        Boolean acquired = redis.opsForValue()
            .setIfAbsent(lockKey, requestId, timeout);
        // SET key value NX EX timeout (atomic operation)
        // NX = only set if not exists
        // EX = expiry (prevents deadlock if holder crashes)
        return Boolean.TRUE.equals(acquired);
    }

    /**
     * Release lock — only if WE hold it (prevent releasing someone else's lock)
     */
    public boolean releaseLock(String lockKey, String requestId) {
        String script = """
            if redis.call('get', KEYS[1]) == ARGV[1] then
                return redis.call('del', KEYS[1])
            else
                return 0
            end
            """;
        // Lua script is ATOMIC in Redis
        Long result = redis.execute(
            new DefaultRedisScript<>(script, Long.class),
            List.of(lockKey),
            requestId
        );
        return result != null && result == 1L;
    }
}

// Usage: Prevent duplicate payment processing
@Service
public class PaymentService {
    public PaymentResult processPayment(String paymentId) {
        String lockKey = "payment-lock:" + paymentId;
        String requestId = UUID.randomUUID().toString(); // Unique to THIS request

        boolean locked = lockService.acquireLock(lockKey, requestId, Duration.ofSeconds(30));
        if (!locked) {
            return PaymentResult.inProgress("Payment already being processed");
        }

        try {
            // Only ONE instance processes this payment
            return doProcessPayment(paymentId);
        } finally {
            lockService.releaseLock(lockKey, requestId);
        }
    }
}
```

---

## 📖 Two-Phase Commit (2PC) — Distributed Transactions

### Theory:
2PC is a protocol to achieve **atomicity** across multiple databases/services. Either ALL participants commit, or ALL rollback.

```
Phase 1: PREPARE
  Coordinator → all Participants: "Can you commit?"
  Participant A: "Yes, I'm ready" (writes to WAL, holds locks)
  Participant B: "Yes, I'm ready"

Phase 2: COMMIT (if ALL said yes)
  Coordinator → all Participants: "COMMIT!"
  Participant A: commits
  Participant B: commits

Phase 2: ROLLBACK (if ANY said no)
  Coordinator → all Participants: "ROLLBACK!"
  Participant A: rolls back
  Participant B: rolls back

Problems with 2PC:
1. Blocking: If Coordinator crashes after Phase 1, participants are STUCK
2. Single point of failure: Coordinator is critical
3. Performance: Holds locks during entire protocol
→ That's why modern microservices prefer Saga pattern instead!
```

---

## Common Interview Questions:

### "How do you handle network partitions?"
```
Strategy 1: Retry with exponential backoff
  → Wait 1s, 2s, 4s, 8s, 16s... between retries
  → Add jitter (random delay) to prevent thundering herd

Strategy 2: Circuit breaker
  → Stop calling failed service after X failures
  → Serve cached/default response

Strategy 3: Event-driven (preferred)
  → Don't make synchronous calls across partitions
  → Use Kafka/message queue — publisher writes, consumer processes when available
```

### "What is the Split Brain problem?"
```
When network partition splits cluster into two groups:
  Group A: Nodes 1, 2 → elect their own leader
  Group B: Nodes 3, 4, 5 → elect their own leader

Now TWO leaders accept writes → DATA DIVERGENCE!

Solution: Quorum-based voting
  Only the group with MAJORITY (>50%) can elect leader
  Group A (2/5) → less than majority → becomes read-only
  Group B (3/5) → majority → continues as normal
```
