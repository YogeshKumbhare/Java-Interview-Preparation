# Chapter 28: Digital Wallet

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/digital-wallet)

Payment platforms provide a digital wallet service where clients store money and spend it later. Users can transfer money directly between digital wallets without extra fees.

---

## Step 1 - Understand the Problem and Establish Design Scope

- Focus: balance transfer operations between two digital wallets
- Scale: 1,000,000 TPS
- Correctness: transactional guarantees + reproducibility (reconstruct historical balance by replaying data)
- Availability: 99.99%
- No foreign exchange

**Back-of-the-envelope:**
- Each transfer = 2 operations (debit + credit) = 2M TPS needed
- Assume 1,000 TPS per DB node → **2,000 nodes** needed

| Per-node TPS | Node Number |
|-------------|-------------|
| 100 | 20,000 |
| 1,000 | 2,000 |
| 10,000 | 200 |

---

## Step 2 - High-Level Design

### API Design

**POST /v1/wallet/balance_transfer**

| Field | Description | Type |
|-------|-------------|------|
| from_account | Debit account | string |
| to_account | Credit account | string |
| amount | Amount of money | **string** (not double) |
| currency | ISO 4217 | string |
| transaction_id | UUID for deduplication | uuid |

### Option 1: In-Memory Sharding Solution

- Use **Redis** cluster for account balances
- Shard by hash(accountId) % N partitions
- **Zookeeper** stores sharding info (partition count, Redis node addresses)
- Stateless **wallet service** handles transfer commands

```java
String accountID = "A";
int partitionNumber = 7;
int myPartition = accountID.hashCode() % partitionNumber;
```

**Problem**: If wallet service crashes after updating one Redis node, the second update is lost. No atomicity across two Redis nodes.

### Option 2: Distributed Transactions with Relational Database

Replace Redis with transactional relational databases. Still problem: updates on two different databases need to be atomic.

**Solution A: Two-Phase Commit (2PC)**

Phase 1 (Prepare): Coordinator locks both databases, asks them to prepare
Phase 2 (Commit/Abort): If all say "yes" → commit; if any says "no" → abort

**Problems with 2PC**:
- Not performant — locks held for a long time
- Coordinator is single point of failure

**Solution B: TC/C (Try-Confirm/Cancel)**

Each phase is a separate, independent transaction.

| Phase | Operation | Account A | Account C |
|-------|-----------|-----------|-----------|
| 1 (Try) | | Balance: -$1 | NOP |
| 2 (Confirm) | | NOP | Balance: +$1 |
| 2 (Cancel) | | Balance: +$1 | NOP |

**Valid operation order**: Must deduct before adding (only Choice 1 is valid).

**Out-of-order execution**: Cancel may arrive before Try. Solution: leave out-of-order flag when Cancel seen without Try; Try checks this flag and returns failure.

**Phase status table**: Stores distributed transaction progress (ID, content, Try phase status per DB, phase 2 name, phase 2 status, out-of-order flag).

**Solution C: Saga**

All operations in linear order. Each is an independent local transaction.
- On failure: **compensating transactions** rolled back in reverse order
- If n operations: prepare 2n operations (n normal + n compensating)

**Coordination modes:**
- **Choreography**: Fully decentralized, services subscribe to each other's events (complex)
- **Orchestration**: Single coordinator instructs services ⭐ (preferred for digital wallet)

**2PC vs TC/C vs Saga:**

| | 2PC | TC/C | Saga |
|--|-----|------|------|
| First phase | Uncommitted | Committed | Committed |
| Second phase | Commit/abort | New compensation | Compensation |
| Operation order | Any | Any | Linear only |
| Parallel execution | No (locked) | Yes | No |
| Partial inconsistency visible | Database hides | Yes | Yes |

**TC/C choice**: If latency-sensitive and many operations.
**Saga choice**: If latency is not critical, or few services; follows microservice trend.

### Option 3: Event Sourcing (Recommended for Reproducibility)

**Four key concepts:**

1. **Command**: Intended action from outside world (e.g., "Transfer $1 from A to C"). Put in FIFO queue.
2. **Event**: Validated command that must be executed. Past tense ("Transferred $1 from A to C"). Deterministic.
3. **State**: Account balances (map data structure, stored in key-value store or relational DB).
4. **State machine**: Validates commands → generates events; applies events → updates state.

**Properties:**
- One command may generate any number of events (including zero)
- Events are deterministic; commands may contain randomness
- Event list is stored in FIFO queue (Kafka)

**Dynamic view:**
1. Read command from queue
2. Read balance state from DB
3. Validate command → generate two events (A:-$1 and C:+$1)
4. Apply event → update balance in DB

**Reproducibility**: Replay all events from beginning → always get the same historical states. Solves audit questions:
- Balance at any given time? → replay events up to that point
- Is balance correct? → recalculate from event list
- Is logic correct after code change? → run different code versions against same events

### CQRS (Command-Query Responsibility Segregation)

Rather than publishing state, event sourcing publishes all events. External systems rebuild their own state.

- **Write** state machine: handles balance updates
- **Read-only** state machines: build views for queries (balance queries, time-period analysis, reconciliation)

---

## Step 3 - Design Deep Dive

### High-Performance Event Sourcing

**File-based optimization:**

1. Save commands and events to **local disk** (avoid network transit to Kafka)
2. Use **mmap** (memory-mapped files): maps disk file to memory array. OS caches recent data in memory. Sequential writes — very fast even on HDD.
3. Save state to **local disk** using:
   - **SQLite**: file-based local relational DB
   - **RocksDB**: file-based key-value store with LSM tree ⭐ (optimized for writes)

**Snapshot optimization:**
- Periodically stop state machine and save current state to file
- On restart: load latest snapshot → resume from there (no need to replay from beginning)
- Finance teams often require daily snapshots at 00:00
- Snapshots stored in object storage (HDFS)

### Reliable High-Performance Event Sourcing

**What needs reliability**: Only the **event list** needs strong reliability guarantee.
- State and snapshots can always be regenerated from events
- Commands cannot guarantee event reproducibility (may contain randomness)

**Consensus via Raft algorithm:**
- Set up 3 event sourcing nodes
- Leader receives commands, converts to events, appends to event list
- Raft replicates events to followers
- As long as majority (2/3) of nodes are up → system works
- On leader crash: Raft automatically elects new leader

Node roles in Raft: **Leader**, **Candidate**, **Follower**

Fault tolerance: 5 nodes → tolerates 2 failures; 3 nodes → tolerates 1 failure.

### Distributed Event Sourcing (1M TPS)

**Two challenges with single Raft group:**
1. CQRS response can be slow (polling-based)
2. Single Raft group capacity is limited

**Fix 1: Push model (vs. pull)**

- Pull model: client polls periodically — not real-time, can overload
- **Push model** ⭐: read-only state machine pushes execution status to reverse proxy as soon as event received → real-time response to user

**Fix 2: Sharding with distributed transactions**

Partition data (e.g., hash(key) % 2). Use TC/C or Saga across partitions.

**Final distributed flow (Saga + CQRS + Raft):**
1. User sends transfer command to Saga coordinator
2. Coordinator creates phase status record
3. Coordinator sends A-$1 to Partition 1's Raft group
4. Raft leader validates, converts to event, synchronizes via Raft
5. Event sourced to read path via CQRS
6. Read path pushes status to Saga coordinator
7. Coordinator records success, sends C+$1 to Partition 2
8. Same process on Partition 2
9. Saga coordinator records completion → responds to user

### Java Example – Event Sourcing Wallet

```java
import java.util.*;
import java.util.concurrent.*;

public class EventSourcedWallet {

    // Commands and Events
    record TransferCommand(String commandId, String from, String to, double amount) {}
    record WalletEvent(String eventId, String account, double delta, long timestamp) {}

    private final List<TransferCommand> commandLog = new ArrayList<>();
    private final List<WalletEvent> eventLog = new ArrayList<>();
    private final Map<String, Double> state = new HashMap<>(); // account -> balance

    public void addAccount(String accountId, double initialBalance) {
        state.put(accountId, initialBalance);
        eventLog.add(new WalletEvent(UUID.randomUUID().toString(), accountId,
            initialBalance, System.currentTimeMillis()));
    }

    public boolean processCommand(String commandId, String from, String to, double amount) {
        TransferCommand cmd = new TransferCommand(commandId, from, to, amount);
        commandLog.add(cmd);

        // Validate
        double fromBalance = state.getOrDefault(from, 0.0);
        if (fromBalance < amount) {
            System.out.println("Command rejected: insufficient balance for " + from);
            return false;
        }

        // Generate events (deterministic)
        String eventId1 = UUID.randomUUID().toString();
        String eventId2 = UUID.randomUUID().toString();
        long ts = System.currentTimeMillis();

        WalletEvent debitEvent = new WalletEvent(eventId1, from, -amount, ts);
        WalletEvent creditEvent = new WalletEvent(eventId2, to, amount, ts);

        // Apply events to state
        applyEvent(debitEvent);
        applyEvent(creditEvent);

        eventLog.add(debitEvent);
        eventLog.add(creditEvent);

        System.out.printf("Transfer %.2f from %s to %s: SUCCESS%n", amount, from, to);
        return true;
    }

    private void applyEvent(WalletEvent event) {
        state.merge(event.account(), event.delta(), Double::sum);
    }

    // Reproducibility: replay events
    public Map<String, Double> replayFromBeginning() {
        Map<String, Double> replayState = new HashMap<>();
        for (WalletEvent event : eventLog) {
            replayState.merge(event.account(), event.delta(), Double::sum);
        }
        return replayState;
    }

    public void printBalances() {
        System.out.println("Current balances:");
        state.forEach((acc, bal) -> System.out.printf("  %s: %.2f%n", acc, bal));
    }

    public static void main(String[] args) {
        EventSourcedWallet wallet = new EventSourcedWallet();
        wallet.addAccount("alice", 100.0);
        wallet.addAccount("bob", 50.0);
        wallet.addAccount("carol", 25.0);

        wallet.processCommand("cmd-1", "alice", "bob", 30.0);
        wallet.processCommand("cmd-2", "bob", "carol", 20.0);
        wallet.processCommand("cmd-3", "carol", "alice", 200.0); // Should fail

        wallet.printBalances();

        System.out.println("\nReplayed balances (reproducibility):");
        wallet.replayFromBeginning().forEach((acc, bal) ->
            System.out.printf("  %s: %.2f%n", acc, bal));
    }
}
```

---

## Step 4 - Wrap Up

**Three design iterations:**

1. **In-memory (Redis)**: Fast but no atomicity across nodes
2. **Distributed transactions (2PC/TC/C/Saga)**: Atomicity but hard to audit
3. **Event sourcing**: Atomicity + full reproducibility + audit capability ⭐

**Final enhancements:**
- File-based storage (mmap, RocksDB) for performance
- Raft consensus for reliability
- CQRS + push model for real-time response
- Sharding with Saga/TC/C for 1M TPS scale

---

## Reference materials

[1] Transactional guarantees: https://docs.oracle.com/cd/E17275_01/html/programmer_reference/rep_trans.html
[2] TPC-E Top Price/Performance Results: http://tpc.org/tpce/results/tpce_price_perf_results5.asp
[3] ISO 4217: https://en.wikipedia.org/wiki/ISO_4217
[4] Apache Zookeeper: https://zookeeper.apache.org/
[5] Designing Data-Intensive Applications (Kleppmann)
[6] X/Open XA: https://en.wikipedia.org/wiki/X/Open_XA
[7] Compensating transaction: https://en.wikipedia.org/wiki/Compensating_transaction
[8] SAGAS paper: https://www.cs.cornell.edu/andru/cs711/2002fa/reading/sagas.pdf
[9] Domain-Driven Design (Evans)
[10] Apache Kafka: https://kafka.apache.org/
[11] CQRS: https://martinfowler.com/bliki/CQRS.html
[12] Comparing Random and Sequential Access: https://deliveryimages.acm.org/10.1145/1570000/1563874/jacobs3.jpg
[13] mmap: https://man7.org/linux/man-pages/man2/mmap.2.html
[14] SQLite: https://www.sqlite.org/index.html
[15] RocksDB: https://rocksdb.org/
[16] Apache Hadoop HDFS: https://hadoop.apache.org/
[17] Raft: https://raft.github.io/
[18] Reverse proxy: https://en.wikipedia.org/wiki/Reverse_proxy
