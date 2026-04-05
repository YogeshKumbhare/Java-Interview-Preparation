# Chapter 28: Digital Wallet

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/digital-wallet)

Design a digital wallet service that allows users to store money, transfer funds, and track transactions.

---

## Step 1 - Understand the problem and establish design scope

**Features:** Balance management, money transfer between wallets, transaction history.

**Non-functional:** Reliability (no money lost), correctness (balance always accurate), high availability, support 1 million TPS at peak.

**Key challenge:** Ensuring correctness of balance under high concurrency and distributed environment.

---

## Step 2 - High-level design

### API Design

- `POST /v1/wallet/transfer` — params: from_wallet, to_wallet, amount, currency, idempotency_key
- `GET /v1/wallet/{id}/balance` — Get current balance
- `GET /v1/wallet/{id}/transactions` — Get transaction history

### In-memory vs distributed approaches

#### Approach 1: Store balance in relational DB
- Simple, uses ACID transactions
- `UPDATE wallet SET balance = balance - amount WHERE id = ? AND balance >= amount`
- Relies on DB row-level locking
- Bottleneck at high TPS

#### Approach 2: Event sourcing
- Don't store balance directly, store events (credits/debits)
- Balance = sum of all events
- Append-only, immutable event log
- Natural audit trail

### Java Example – Digital Wallet with Event Sourcing

```java
import java.util.*;
import java.util.concurrent.*;

public class DigitalWallet {
    enum TransactionType { CREDIT, DEBIT }

    record Transaction(String id, String walletId, TransactionType type,
                       double amount, long timestamp, String description) {}

    private final Map<String, List<Transaction>> eventStore = new ConcurrentHashMap<>();
    private final Set<String> processedKeys = ConcurrentHashMap.newKeySet();

    public void createWallet(String walletId, double initialBalance) {
        Transaction init = new Transaction(UUID.randomUUID().toString(), walletId,
            TransactionType.CREDIT, initialBalance, System.currentTimeMillis(), "Initial deposit");
        eventStore.computeIfAbsent(walletId, k -> new CopyOnWriteArrayList<>()).add(init);
        System.out.printf("🔑 Wallet %s created with $%.2f%n", walletId, initialBalance);
    }

    public synchronized boolean transfer(String idempotencyKey, String fromWallet,
                                          String toWallet, double amount) {
        if (processedKeys.contains(idempotencyKey)) {
            System.out.println("⚠️ Duplicate transfer: " + idempotencyKey);
            return false;
        }

        double balance = getBalance(fromWallet);
        if (balance < amount) {
            System.out.printf("❌ Insufficient funds: %s has $%.2f, need $%.2f%n",
                fromWallet, balance, amount);
            return false;
        }

        String txId = UUID.randomUUID().toString().substring(0, 8);
        long now = System.currentTimeMillis();

        eventStore.get(fromWallet).add(new Transaction(txId, fromWallet,
            TransactionType.DEBIT, amount, now, "Transfer to " + toWallet));
        eventStore.computeIfAbsent(toWallet, k -> new CopyOnWriteArrayList<>())
                  .add(new Transaction(txId, toWallet,
            TransactionType.CREDIT, amount, now, "Transfer from " + fromWallet));

        processedKeys.add(idempotencyKey);
        System.out.printf("✅ Transfer: %s → %s: $%.2f%n", fromWallet, toWallet, amount);
        return true;
    }

    public double getBalance(String walletId) {
        return eventStore.getOrDefault(walletId, List.of()).stream()
            .mapToDouble(t -> t.type() == TransactionType.CREDIT ? t.amount() : -t.amount())
            .sum();
    }

    public List<Transaction> getHistory(String walletId) {
        return eventStore.getOrDefault(walletId, List.of());
    }

    public static void main(String[] args) {
        DigitalWallet wallet = new DigitalWallet();
        wallet.createWallet("alice", 1000.0);
        wallet.createWallet("bob", 500.0);

        wallet.transfer("tx-001", "alice", "bob", 250.0);
        wallet.transfer("tx-002", "bob", "alice", 100.0);
        wallet.transfer("tx-001", "alice", "bob", 250.0); // duplicate
        wallet.transfer("tx-003", "bob", "alice", 1000.0); // insufficient

        System.out.printf("%nAlice balance: $%.2f%n", wallet.getBalance("alice"));
        System.out.printf("Bob balance: $%.2f%n", wallet.getBalance("bob"));
    }
}
```

---

## Step 3 - Design deep dive

### CQRS (Command Query Responsibility Segregation)
- **Write model**: Append events to event store (optimized for writes)
- **Read model**: Materialized view of balances (optimized for reads)
- Async projection updates read model from events

### Distributed transactions
- For cross-shard transfers, use **Two-Phase Commit (2PC)** or **Saga pattern**
- TC/C (Try-Confirm/Cancel): reserve amount → confirm → release on failure

### Audit and compliance
- Event sourcing provides a natural, immutable audit log
- Every balance change traceable to a specific event
- Regulatory requirements (KYC, AML) integration

### Performance at scale
- Partition wallets by user_id hash
- Hot wallets (merchants) may need special handling (sub-accounts)
- Cache balances in Redis, invalidate on new events

---

## Step 4 - Wrap up

Additional talking points:
- **Currency conversion**
- **Interest calculation**
- **Withdrawal to bank account**
- **Fraud detection and limits**
