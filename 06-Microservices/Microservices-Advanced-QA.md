# 🔗 Microservices — Advanced Interview Questions
## Target: 12+ Years Experience | InterviewBit + GFG Inspired

> **Note:** This extends Microservices-QA.md with frequently missed advanced topics.

---

## Q: Idempotency in Microservices — Why is it critical?

### Theory:
An **idempotent** operation produces the **same result** regardless of how many times it's called.

```
HTTP Method Idempotency:
  GET    → Idempotent ✅ (read-only, same result every time)
  PUT    → Idempotent ✅ (replace resource — result is same)
  DELETE → Idempotent ✅ (delete once = delete many = resource gone)
  POST   → NOT Idempotent ❌ (creates new resource each time!)
  PATCH  → NOT guaranteed (depends on implementation)
```

```java
// WHY it matters: Network retries!
// Client → API Gateway → Payment Service
// If Payment Service processes but response is lost,
// client retries → payment charged TWICE! 💸

// Solution: Idempotency Key
@PostMapping("/payments")
public ResponseEntity<Payment> createPayment(
        @RequestHeader("Idempotency-Key") String idempotencyKey,
        @RequestBody PaymentRequest request) {

    // Check if this key was already processed
    Optional<Payment> existing = paymentRepo.findByIdempotencyKey(idempotencyKey);
    if (existing.isPresent()) {
        return ResponseEntity.ok(existing.get()); // Return cached result
    }

    // Process payment
    Payment payment = paymentService.process(request);
    payment.setIdempotencyKey(idempotencyKey);
    paymentRepo.save(payment);
    return ResponseEntity.status(HttpStatus.CREATED).body(payment);
}

// Client generates unique key (UUID) per operation
// Retries send SAME key → server detects duplicate → returns original result
```

---

## Q: Distributed Transactions — Saga Pattern

### Theory:
In microservices, you CAN'T use a single database transaction across services (no shared DB). Use **Saga Pattern** instead.

```
Traditional Monolith:            Microservices (Saga):
┌─────────────────────┐          ┌──────┐  ┌──────┐  ┌──────┐
│ BEGIN TRANSACTION    │          │Order │→ │Stock │→ │Payment│
│   Create Order       │          │Svc   │  │Svc   │  │Svc    │
│   Deduct Stock       │          └──┬───┘  └──┬───┘  └──┬───┘
│   Charge Payment     │             │         │         │
│ COMMIT               │          Each has own DB — no shared TX!
└─────────────────────┘

Saga = sequence of LOCAL transactions with COMPENSATING actions
```

### Choreography Saga (Event-Driven):
```
1. OrderService creates order → publishes "OrderCreated" event
2. StockService listens → reserves stock → publishes "StockReserved"
3. PaymentService listens → charges card → publishes "PaymentCompleted"
4. OrderService listens → marks order as CONFIRMED

If PaymentService fails:
4. PaymentService publishes "PaymentFailed"
5. StockService listens → releases stock (COMPENSATING action)
6. OrderService listens → cancels order (COMPENSATING action)

✅ Loosely coupled, no orchestrator
❌ Hard to track, can become spaghetti with many services
```

### Orchestration Saga (Central Coordinator):
```java
// OrderSagaOrchestrator controls the flow
@Service
public class OrderSagaOrchestrator {

    public Order processOrder(OrderRequest request) {
        Order order = orderService.create(request);  // Step 1

        try {
            stockService.reserve(order);              // Step 2
            paymentService.charge(order);             // Step 3
            order.setStatus(CONFIRMED);
        } catch (StockException e) {
            order.setStatus(CANCELLED);               // Compensate
        } catch (PaymentException e) {
            stockService.release(order);              // Compensate Step 2
            order.setStatus(CANCELLED);               // Compensate Step 1
        }
        return orderService.save(order);
    }
}

// ✅ Easy to understand and debug
// ✅ Central place to see full flow
// ❌ Orchestrator is a single point of failure
// ❌ Tighter coupling to orchestrator
```

---

## Q: Consumer-Driven Contract Testing (PACT)

```
Problem: Service A calls Service B's API.
How do you ensure Service B doesn't break Service A when it changes?

Traditional: Integration tests (slow, flaky, require both services running)
Better: PACT — Consumer-Driven Contract Testing

Flow:
1. CONSUMER (Service A) writes a "contract" — what it expects
2. Contract is shared with PROVIDER (Service B)
3. Provider verifies its API matches the contract
4. If provider changes break the contract → build fails!

// Consumer side (Service A)
@Pact(consumer = "OrderService", provider = "PaymentService")
public RequestResponsePact createPact(PactDslWithProvider builder) {
    return builder
        .given("Payment exists")
        .uponReceiving("A request for payment")
        .path("/api/payments/123")
        .method("GET")
        .willRespondWith()
        .status(200)
        .body(new PactDslJsonBody()
            .integerType("id", 123)
            .stringType("status", "COMPLETED")
            .decimalType("amount", 99.99))
        .toPact();
}

// Provider side (Service B)
@Provider("PaymentService")
@PactBroker(url = "http://pact-broker:9292")
class PaymentProviderTest {
    @TestTemplate
    @ExtendWith(PactVerificationInvocationContextProvider.class)
    void verifyPact(PactVerificationContext context) {
        context.verifyInteraction();
    }
}

Benefits:
✅ Fast — no need to start other services
✅ Reliable — no flaky network issues
✅ Clear ownership — consumer defines what it needs
✅ CI/CD integrated — breaks build if contract violated
```

---

## Q: Service Mesh — Istio / Linkerd

```
Service Mesh = infrastructure layer for service-to-service communication

Without Service Mesh:              With Service Mesh:
App handles:                       Sidecar Proxy handles:
- Retries                          - Retries
- Circuit breaking                 - Circuit breaking
- mTLS                             - mTLS (automatic!)
- Load balancing                   - Load balancing
- Observability                    - Observability
                                   - Traffic management

Architecture:
┌─────────────────────────┐
│     Control Plane        │  (Istio/Linkerd control)
│  (Config, Certs, Rules)  │
└──────────┬──────────────┘
           │ configures
     ┌─────▼─────┐    ┌──────────┐
     │ Pod       │    │ Pod      │
     │ ┌───────┐ │    │ ┌──────┐ │
     │ │App    │ │    │ │App   │ │
     │ │       │ │    │ │      │ │
     │ └───┬───┘ │    │ └──┬───┘ │
     │ ┌───▼───┐ │    │ ┌──▼───┐ │
     │ │Envoy  │◄├────┤►│Envoy │ │  (sidecar proxy)
     │ │Proxy  │ │    │ │Proxy │ │
     │ └───────┘ │    │ └──────┘ │
     └───────────┘    └──────────┘

Benefits:
✅ Zero code changes — networking logic separated from business logic
✅ Automatic mTLS — all communication encrypted
✅ Traffic splitting — canary deployments (90% v1, 10% v2)
✅ Observability — distributed traces without code instrumentation
```

---

## Q: API Versioning Strategies

```java
// 1. URI Path versioning (most common)
@GetMapping("/api/v1/users")
public List<UserV1> getUsersV1() { ... }

@GetMapping("/api/v2/users")
public List<UserV2> getUsersV2() { ... }
// ✅ Simple, explicit, easy to cache
// ❌ URL changes, forces client updates

// 2. Header versioning
@GetMapping("/api/users")
public ResponseEntity<?> getUsers(
        @RequestHeader(value = "API-Version", defaultValue = "1") String version) {
    if ("2".equals(version)) return ResponseEntity.ok(getUsersV2());
    return ResponseEntity.ok(getUsersV1());
}
// ✅ Clean URLs
// ❌ Hidden, harder to test in browser

// 3. Query parameter versioning
@GetMapping("/api/users")
public ResponseEntity<?> getUsers(@RequestParam(defaultValue = "1") int version) { ... }
// GET /api/users?version=2
// ✅ Easy to use
// ❌ Can be overlooked, caching issues

// 4. Content negotiation (Accept header)
@GetMapping(value = "/api/users",
            produces = "application/vnd.company.v2+json")
public List<UserV2> getUsersV2() { ... }
// ✅ RESTful, clean
// ❌ Complex, hard to test

// BEST PRACTICE: Use URI path versioning for public APIs
// Support at most 2-3 versions simultaneously
// Deprecate with warning headers before removing
```

---

## Q: Distributed Tracing — How requests flow across services

```
Request: User → API Gateway → OrderService → PaymentService → NotificationService

Without tracing: "Something is slow" — WHERE?
With tracing: See exact time spent in each service

Tools: Zipkin, Jaeger, AWS X-Ray
Protocol: OpenTelemetry (standard)

Trace structure:
Trace (entire request lifecycle)
└── Span: API Gateway (2ms)
    └── Span: OrderService (150ms)
        ├── Span: DB Query (50ms)
        └── Span: PaymentService (80ms)
            └── Span: Stripe API (60ms)
```

```java
// Spring Boot 3 with Micrometer Tracing (built-in!)
// Just add dependency: micrometer-tracing-bridge-brave + zipkin-reporter

// Trace ID propagated automatically in HTTP headers:
// traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

// Custom span for specific operation
@Autowired
private Tracer tracer;

public PaymentResult processPayment(PaymentRequest req) {
    Span span = tracer.nextSpan().name("process-payment").start();
    try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
        span.tag("payment.type", req.getType());
        span.tag("payment.amount", req.getAmount().toString());
        return doProcess(req);
    } finally {
        span.end();
    }
}
```
