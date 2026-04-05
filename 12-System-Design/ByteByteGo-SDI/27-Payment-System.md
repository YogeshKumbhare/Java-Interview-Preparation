# Chapter 27: Payment System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/payment-system)

Design a payment system like Stripe, PayPal, or a payment backend for an e-commerce platform.

---

## Step 1 - Understand the problem and establish design scope

**Features:** Pay-in flow (receive money from customers), Pay-out flow (send money to sellers/merchants). Support multiple payment methods (credit card, bank transfer, digital wallets).

**Non-functional:** Reliability (no double charge, no lost payment), exactly-once processing, data consistency, fault tolerance.

**Estimations:** 1 million transactions/day, ~12 TPS average, peak 5x = 60 TPS.

---

## Step 2 - High-level design

### Pay-in flow
1. User places order on e-commerce site
2. Payment service creates a payment event
3. Payment service calls Payment Service Provider (PSP) — Stripe/Adyen
4. PSP processes with card network (Visa/Mastercard) and bank
5. PSP returns result → Payment service updates status
6. Wallet service / ledger updated

### Pay-out flow
1. Seller requests withdrawal
2. Payment service initiates payout via PSP
3. Money transferred to seller's bank account

### Key components

- **Payment Service**: Orchestrates payment flow
- **PSP (Payment Service Provider)**: Stripe, Adyen, Braintree
- **Ledger**: Double-entry bookkeeping for every transaction
- **Wallet**: Stores merchant/seller account balances

### Java Example – Payment Processing

```java
import java.util.*;
import java.util.concurrent.*;

public class PaymentService {
    enum PaymentStatus { PENDING, PROCESSING, SUCCESS, FAILED, REFUNDED }

    record Payment(String id, String orderId, double amount, String currency,
                   String paymentMethod, PaymentStatus status, long timestamp) {}

    record LedgerEntry(String txId, String debitAccount, String creditAccount,
                       double amount, long timestamp) {}

    private final Map<String, Payment> payments = new ConcurrentHashMap<>();
    private final List<LedgerEntry> ledger = new CopyOnWriteArrayList<>();
    private final Map<String, Double> wallets = new ConcurrentHashMap<>();
    private final Set<String> processedIdempotencyKeys = ConcurrentHashMap.newKeySet();

    public Payment processPayment(String idempotencyKey, String orderId,
                                   double amount, String currency) {
        // Idempotency check — prevent double charge
        if (processedIdempotencyKeys.contains(idempotencyKey)) {
            System.out.println("⚠️ Duplicate request detected: " + idempotencyKey);
            return payments.values().stream()
                .filter(p -> p.orderId().equals(orderId))
                .findFirst().orElse(null);
        }

        String paymentId = "PAY-" + UUID.randomUUID().toString().substring(0, 8);
        Payment payment = new Payment(paymentId, orderId, amount, currency,
                                       "CREDIT_CARD", PaymentStatus.PROCESSING,
                                       System.currentTimeMillis());
        payments.put(paymentId, payment);

        // Simulate PSP call
        boolean pspSuccess = simulatePSP(amount);

        PaymentStatus finalStatus = pspSuccess ? PaymentStatus.SUCCESS : PaymentStatus.FAILED;
        payment = new Payment(paymentId, orderId, amount, currency,
                               "CREDIT_CARD", finalStatus, payment.timestamp());
        payments.put(paymentId, payment);

        if (pspSuccess) {
            // Double-entry ledger
            ledger.add(new LedgerEntry(paymentId, "customer", "merchant",
                                        amount, System.currentTimeMillis()));
            wallets.merge("merchant", amount, Double::sum);
        }

        processedIdempotencyKeys.add(idempotencyKey);
        System.out.printf("%s Payment %s: $%.2f [%s]%n",
            pspSuccess ? "✅" : "❌", paymentId, amount, finalStatus);
        return payment;
    }

    private boolean simulatePSP(double amount) {
        return amount < 10000; // Decline large amounts for demo
    }

    public static void main(String[] args) {
        PaymentService service = new PaymentService();
        service.processPayment("idem-001", "ORD-1001", 99.99, "USD");
        service.processPayment("idem-002", "ORD-1002", 249.50, "USD");
        // Duplicate attempt
        service.processPayment("idem-001", "ORD-1001", 99.99, "USD");
        // Large amount (will fail)
        service.processPayment("idem-003", "ORD-1003", 15000.00, "USD");

        System.out.println("\nMerchant balance: $" + service.wallets.getOrDefault("merchant", 0.0));
        System.out.println("Ledger entries: " + service.ledger.size());
    }
}
```

---

## Step 3 - Design deep dive

### Exactly-once delivery
- **Idempotency key**: Client generates unique key per payment attempt → server deduplicates
- **At-least-once + idempotent operations**: Retry safely

### Double-entry ledger
Every transaction creates two entries: one debit and one credit. The sum of all debits must equal the sum of all credits.

### Retry and timeout handling
- PSP call may timeout → use a **reconciliation** process
- **Exponential backoff** for retries
- Final status resolution via PSP webhooks or polling

### Consistency
- Use **saga pattern** for distributed transactions across services (order, payment, inventory)
- Each step has a compensating action (e.g., refund if inventory check fails)

### Security
- PCI-DSS compliance
- Tokenize card numbers (never store raw card data)
- 3D Secure for additional authentication

---

## Step 4 - Wrap up

Additional talking points:
- **Refund flow**
- **Multi-currency support**
- **Fraud detection** (ML-based anomaly detection)
- **Regulatory compliance** (PCI-DSS, PSD2)
