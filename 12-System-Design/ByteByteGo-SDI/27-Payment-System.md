# Chapter 27: Payment System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/payment-system)

In this chapter, we design a payment system. E-commerce has exploded in popularity. A reliable, scalable, and flexible payment system is essential.

---

## Step 1 - Understand the Problem and Establish Design Scope

- **Type**: Payment backend for e-commerce like Amazon (pay-in and pay-out flows)
- **Payment**: Credit cards via third-party PSPs (Stripe, Braintree, Square)
- **Storage**: No sensitive card data stored locally
- **Scale**: Global, 1 million transactions/day, one currency in interview
- **Reconciliation**: Required between internal and external services

**Functional requirements:**
- Pay-in flow: receive money from customers on behalf of sellers
- Pay-out flow: send money to sellers around the world

**Non-functional requirements:**
- Reliability and fault tolerance
- Reconciliation process

**Back-of-the-envelope:**
- 1M txns/day = 10 TPS — focus is on correctness, not throughput

---

## Step 2 - High-Level Design

**Pay-in flow components:**

- **Payment service**: Accepts payment events, performs risk check (AML/CFT), coordinates process
- **Payment executor**: Executes single payment order via PSP
- **PSP (Payment Service Provider)**: Moves money from buyer credit card
- **Card schemes**: Visa, MasterCard, Discovery
- **Ledger**: Financial record of payment transactions
- **Wallet**: Merchant account balance

**Typical pay-in flow:**
1. User clicks "place order" → payment event to payment service
2. Payment service stores event in DB
3. Payment service calls payment executor for each order
4. Payment executor stores order, calls PSP
5. Payment service updates wallet (seller balance)
6. Payment service calls ledger

### APIs

**POST /v1/payments** — Execute a payment event

Fields: `buyer_info`, `checkout_id`, `credit_card_info`, `payment_orders`

payment_orders: `seller_account`, `amount` (string!), `currency` (ISO 4217), `payment_order_id`

> Amount is `string` not `double` to avoid floating-point precision errors.

**GET /v1/payments/{:id}** — Get execution status

### Data Model

**Payment event table:** `checkout_id` (PK), `buyer_info`, `seller_info`, `credit_card_info`, `is_payment_done`

**Payment order table:** `payment_order_id` (PK), `buyer_account`, `amount`, `currency`, `checkout_id` (FK), `payment_order_status` (NOT_STARTED → EXECUTING → SUCCESS/FAILED), `ledger_updated`, `wallet_updated`

### Double-entry Ledger

| Account | Debit | Credit |
|---------|-------|--------|
| buyer | $1 | |
| seller | | $1 |

Sum = 0. Every payment is debit one account, credit another.

### Pay-out Flow

Uses third-party pay-out providers (Tipalti) to move money from e-commerce bank → seller's bank.

---

## Step 3 - Design Deep Dive

### PSP Integration

**Hosted payment page flow:**
1. User clicks checkout → payment service gets payment order info
2. Payment service sends registration to PSP (amount, currency, redirect URL, UUID nonce)
3. PSP returns token (unique PSP-side payment ID)
4. Payment service stores token
5. Client displays PSP-hosted page (Stripe.js captures card, never reaches our servers)
6. User fills card details → PSP processes payment
7. PSP returns status → browser redirects to redirect URL
8. **Async**: PSP calls payment service webhook with final status

### Reconciliation

- Last line of defense when async communication fails
- PSPs/banks send daily **settlement files**
- Reconciliation system compares settlement file with ledger

**Mismatch resolution:**
1. Classifiable + auto-fixable → engineers automate
2. Classifiable, not auto-fixable → finance team job queue
3. Unclassifiable → finance team investigates

### Handling Payment Delays

When PSP deems a payment high risk or 3D Secure Authentication required:
- PSP returns pending status → client displays to user
- PSP notifies payment service via webhook when resolved
- OR payment service polls PSP for status updates

### Communication Among Internal Services

- **Synchronous (HTTP)**: Simple but poor failure isolation, tight coupling
- **Asynchronous (Kafka)**: Preferred for large-scale — scalability + failure resilience

### Handling Failed Payments

- **Retry queue**: Retryable errors (network errors, timeouts)
- **Dead letter queue**: After MAX_RETRIES exceeded, for debugging

**Retry strategies:**
- Immediate retry
- Fixed intervals
- Incremental intervals
- **Exponential backoff**: 1s → 2s → 4s ⭐
- Cancel (permanent failures)

### Exactly-Once Delivery

= at-least-once (retry) + at-most-once (idempotency)

**Idempotency key**: UUID added to HTTP header `idempotency-key: <value>`

Scenario 1 (double click): Second request with same idempotency key → 429 Too Many Requests

Scenario 2 (network failure): Same nonce → same PSP token → PSP identifies duplicate, returns previous status

### Consistency

- Exactly-once processing internally
- Idempotency + reconciliation with external PSP
- Replicas: consensus algorithms (Paxos, Raft) or consensus DBs (YugabyteDB, CockroachDB)

### Payment Security

| Problem | Solution |
|---------|---------|
| Eavesdropping | HTTPS |
| Data tampering | Encryption + integrity monitoring |
| MITM attack | SSL with certificate pinning |
| Data loss | DB replication + snapshots |
| DDoS | Rate limiting + firewall |
| Card theft | Tokenization |
| PCI compliance | PCI DSS |
| Fraud | AVS, CVV, user behavior analysis |

### Java Example – Payment with Idempotency

```java
import java.util.*;
import java.util.concurrent.*;

public class PaymentService {

    enum Status { NOT_STARTED, EXECUTING, SUCCESS, FAILED }

    record PaymentOrder(String orderId, String buyer, String amount, Status status) {}

    private final Map<String, PaymentOrder> paymentDB = new ConcurrentHashMap<>();
    private final Queue<String> retryQueue = new LinkedList<>();
    private final Map<String, Integer> retryCounts = new ConcurrentHashMap<>();
    private static final int MAX_RETRIES = 3;

    public String processPayment(String orderId, String buyer, String amount, String currency) {
        // Idempotency check
        if (paymentDB.containsKey(orderId)) {
            System.out.println("Duplicate detected. Status: " + paymentDB.get(orderId).status());
            return paymentDB.get(orderId).status().toString();
        }
        paymentDB.put(orderId, new PaymentOrder(orderId, buyer, amount, Status.EXECUTING));

        boolean pspSuccess = Math.random() > 0.4; // Simulate PSP call
        Status finalStatus = pspSuccess ? Status.SUCCESS : Status.FAILED;

        if (!pspSuccess) retryQueue.offer(orderId);
        paymentDB.put(orderId, new PaymentOrder(orderId, buyer, amount, finalStatus));
        System.out.println("Payment " + orderId + ": " + finalStatus);
        return finalStatus.toString();
    }

    public void processRetries() {
        while (!retryQueue.isEmpty()) {
            String orderId = retryQueue.poll();
            int retries = retryCounts.getOrDefault(orderId, 0);
            if (retries >= MAX_RETRIES) {
                System.out.println("Dead letter queue: " + orderId);
                continue;
            }
            retryCounts.put(orderId, retries + 1);
            PaymentOrder order = paymentDB.get(orderId);
            // Reset for retry
            paymentDB.remove(orderId);
            processPayment(orderId, order.buyer(), order.amount(), "USD");
        }
    }

    public static void main(String[] args) {
        PaymentService service = new PaymentService();
        service.processPayment("order-001", "alice", "99.99", "USD");
        service.processPayment("order-001", "alice", "99.99", "USD"); // Idempotency test
        service.processRetries();
    }
}
```

---

## Step 4 - Wrap Up

- Covered: pay-in, pay-out, retry, idempotency, reconciliation, consistency, security
- Additional: monitoring, alerting, debugging tools, currency exchange, geography-specific payment methods

## Reference materials

[1] Payment system: https://en.wikipedia.org/wiki/Payment_system
[2] AML/CFT: https://en.wikipedia.org/wiki/Money_laundering
[5] Stripe API: https://stripe.com/docs/api
[6] Double-entry bookkeeping: https://en.wikipedia.org/wiki/Double-entry_bookkeeping
[8] PCI DSS: https://en.wikipedia.org/wiki/Payment_Card_Industry_Data_Security_Standard
[16] Chain Services with Exactly-Once Guarantees: https://www.confluent.io/blog/chain-services-exactly-guarantees/
[17] Exponential backoff: https://en.wikipedia.org/wiki/Exponential_backoff
[18] Idempotence: https://en.wikipedia.org/wiki/Idempotence
[22] Raft: https://raft.github.io/
