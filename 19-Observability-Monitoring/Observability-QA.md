# 🔍 Observability & Monitoring — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Observability?

**Observability** is the ability to understand the **internal state** of a system by examining its **external outputs**. If your system is observable, you can answer any question about what happened, why it happened, and how to fix it — without deploying new code.

### The Three Pillars:
```
┌──────────────────────────────────────────────────────────────┐
│                    OBSERVABILITY                              │
│                                                               │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────────┐   │
│   │   LOGGING    │   │   METRICS   │   │   TRACING       │   │
│   │             │   │             │   │                 │   │
│   │  What       │   │  How much   │   │  Where did the  │   │
│   │  happened?  │   │  / how fast?│   │  request go?    │   │
│   │             │   │             │   │                 │   │
│   │  SLF4J      │   │  Micrometer │   │  OpenTelemetry  │   │
│   │  Logback    │   │  Prometheus │   │  Jaeger/Zipkin  │   │
│   │  ELK Stack  │   │  Grafana   │   │                 │   │
│   └─────────────┘   └─────────────┘   └─────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 📖 Pillar 1: Logging

### Theory:
Logging records **discrete events** that happened in your application. Good logging is the difference between debugging for 5 minutes vs. 5 hours.

### Logging Levels:
```
TRACE → DEBUG → INFO → WARN → ERROR → FATAL

TRACE: Fine-grained debug info (method entry/exit, loop iterations)
DEBUG: Diagnostic info for developers (variable values, SQL queries)
INFO:  Business events (user registered, payment processed, order placed)
WARN:  Potential problems (retry attempt, deprecated API call, slow query)
ERROR: Something failed but app continues (payment failed, DB connection lost)
FATAL: App must shutdown (config missing, cert expired, license invalid)
```

### Structured Logging (JSON — essential for production):
```java
// SLF4J + Logback configuration
// logback-spring.xml
<configuration>
    <appender name="CONSOLE" class="ch.qos.logback.core.ConsoleAppender">
        <encoder class="net.logstash.logback.encoder.LogstashEncoder">
            <customFields>{"service":"payment-service","env":"production"}</customFields>
        </encoder>
    </appender>

    <root level="INFO">
        <appender-ref ref="CONSOLE"/>
    </root>

    <!-- SQL logging only in debug profile -->
    <springProfile name="debug">
        <logger name="org.hibernate.SQL" level="DEBUG"/>
    </springProfile>
</configuration>

// Output (JSON — parseable by ELK/Splunk):
// {"timestamp":"2024-01-15T10:30:00","level":"INFO","service":"payment-service",
//  "traceId":"abc123","userId":"U001","message":"Payment processed",
//  "paymentId":"P456","amount":100.00,"duration_ms":230}
```

### Best Practices for Seniors:
```java
@Service
@Slf4j
public class PaymentService {

    public PaymentResult process(PaymentRequest req) {
        // ✅ Use MDC for contextual logging (appears in ALL log lines automatically)
        MDC.put("paymentId", req.getPaymentId());
        MDC.put("userId", req.getUserId());
        MDC.put("traceId", req.getTraceId());

        try {
            log.info("Processing payment. amount={}, currency={}",
                req.getAmount(), req.getCurrency()); // Key-value pairs!

            PaymentResult result = gateway.charge(req);

            log.info("Payment successful. txId={}, duration_ms={}",
                result.getTransactionId(), result.getDurationMs());

            return result;
        } catch (PaymentException ex) {
            // ❌ DON'T: log.error("Error: " + ex); → concatenation in hot path
            // ✅ DO: Use parameterized logging
            log.error("Payment failed. errorCode={}, reason={}",
                ex.getErrorCode(), ex.getMessage(), ex); // Last arg = full stack trace
            throw ex;
        } finally {
            MDC.clear(); // Always clean up MDC!
        }
    }
}
```

---

## 📖 Pillar 2: Metrics (Micrometer + Prometheus + Grafana)

### Theory:
**Metrics** are **numerical measurements** collected at regular intervals. Unlike logs (discrete events), metrics show trends and aggregates.

### Four Types of Metrics:
```
Counter: Ever-increasing count (requests served, errors occurred)
  payment.success.count = 15,234

Gauge: Current value that can go up or down (active connections, queue size)
  jvm.memory.used = 456MB

Timer: Measures duration + count (request latency)
  http.request.duration.p99 = 230ms

Distribution Summary: Like Timer but for non-time values (request size, batch size)
  http.request.body.size.mean = 1.2KB
```

### Implementation:
```java
@Service
public class PaymentMetricsService {

    private final Counter successCounter;
    private final Counter failureCounter;
    private final Timer processingTimer;
    private final AtomicInteger pendingGauge;

    public PaymentMetricsService(MeterRegistry registry) {
        // Counters
        this.successCounter = Counter.builder("payment.processed")
            .tag("result", "success")
            .description("Successful payments")
            .register(registry);

        this.failureCounter = Counter.builder("payment.processed")
            .tag("result", "failure")
            .register(registry);

        // Timer
        this.processingTimer = Timer.builder("payment.processing.duration")
            .description("Payment processing time")
            .publishPercentiles(0.5, 0.95, 0.99) // p50, p95, p99
            .publishPercentileHistogram()
            .register(registry);

        // Gauge
        this.pendingGauge = registry.gauge("payment.pending.count",
            new AtomicInteger(0));
    }

    public PaymentResult process(PaymentRequest request) {
        pendingGauge.incrementAndGet();
        return processingTimer.recordCallable(() -> {
            try {
                PaymentResult result = gateway.charge(request);
                successCounter.increment();
                return result;
            } catch (Exception ex) {
                failureCounter.increment();
                throw ex;
            } finally {
                pendingGauge.decrementAndGet();
            }
        });
    }
}
```

### Prometheus Alert Rules:
```yaml
groups:
  - name: payment-alerts
    rules:
      - alert: HighPaymentFailureRate
        expr: |
          rate(payment_processed_total{result="failure"}[5m])
          / rate(payment_processed_total[5m]) > 0.05
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Payment failure rate > 5% for 2 minutes"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            rate(payment_processing_duration_seconds_bucket[5m])
          ) > 2
        for: 5m
        annotations:
          summary: "Payment p99 latency > 2 seconds"

      - alert: JVMHeapHigh
        expr: jvm_memory_used_bytes{area="heap"} / jvm_memory_max_bytes{area="heap"} > 0.85
        for: 5m
        annotations:
          summary: "Heap usage > 85%"
```

---

## 📖 Pillar 3: Distributed Tracing (OpenTelemetry)

### Theory:
**Distributed tracing** tracks a single request as it flows through **multiple microservices**. Each service adds a **span** (a timed operation) to the **trace** (the entire journey).

```
User sends: POST /api/orders

Trace: abc-123 (entire request journey)
├── Span: API Gateway (5ms)
│   └── Span: Order Service - createOrder() (120ms)
│       ├── Span: DB Query - save order (15ms)
│       ├── Span: Payment Service - charge() (80ms)   ← Slowest!
│       │   ├── Span: Fraud Check API (30ms)
│       │   └── Span: Bank Gateway (45ms)
│       └── Span: Kafka - publish event (5ms)
└── Total: 125ms
```

### Spring Boot + OpenTelemetry:
```xml
<dependency>
    <groupId>io.opentelemetry.instrumentation</groupId>
    <artifactId>opentelemetry-spring-boot-starter</artifactId>
</dependency>
```

```yaml
# application.yml
otel:
  exporter:
    otlp:
      endpoint: http://jaeger:4317
  service:
    name: payment-service
  traces:
    sampler:
      probability: 1.0  # 100% in dev, reduce in prod (e.g., 0.1 = 10%)
```

### Custom Span:
```java
@Service
public class PaymentGatewayService {

    private final Tracer tracer;

    public GatewayResponse charge(PaymentRequest request) {
        Span span = tracer.spanBuilder("payment.gateway.charge")
            .setAttribute("payment.id", request.getPaymentId())
            .setAttribute("payment.amount", request.getAmount().doubleValue())
            .setAttribute("payment.currency", request.getCurrency())
            .startSpan();

        try (Scope scope = span.makeCurrent()) {
            GatewayResponse response = httpClient.post(gatewayUrl, request);
            span.setAttribute("gateway.txid", response.getTransactionId());
            span.setStatus(StatusCode.OK);
            return response;
        } catch (Exception ex) {
            span.recordException(ex);
            span.setStatus(StatusCode.ERROR, ex.getMessage());
            throw ex;
        } finally {
            span.end();
        }
    }
}
```

---

## ELK Stack (Elasticsearch + Logstash + Kibana):

```
Application → Logstash (parse/transform) → Elasticsearch (store/index) → Kibana (visualize/search)

logstash.conf:
input {
  tcp { port => 5000 codec => json }
}
filter {
  json { source => "message" }
  date { match => ["timestamp", "ISO8601"] }
}
output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "app-logs-%{+YYYY.MM.dd}"
  }
}
```
