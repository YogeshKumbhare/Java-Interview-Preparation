# 🔧 Microservices — Deep Dive Interview Q&A
## Target: 12+ Years Experience

---

## Q1: What are the key patterns in Microservices architecture?

### Core Patterns:
```
Communication Patterns:
├── Synchronous: REST / gRPC
└── Asynchronous: Kafka / RabbitMQ / SNS

Resilience Patterns:
├── Circuit Breaker (Resilience4j)
├── Retry with Exponential Backoff
├── Bulkhead (limit concurrency per service)
├── Timeout
└── Rate Limiter

Data Patterns:
├── Database per service
├── Saga (choreography / orchestration)
├── CQRS (Command Query Responsibility Segregation)
├── Event Sourcing
└── Outbox Pattern

Infrastructure Patterns:
├── API Gateway (single entry point)
├── Service Discovery (Eureka / Consul)
├── Config Server (Spring Cloud Config)
└── Distributed Tracing (Sleuth + Zipkin)
```

---

## Q2: How do you design a Microservices system from scratch? (System Design)

### Example: E-Commerce with 12+ year thinking

```
Client (Mobile/Web)
     ↓ HTTPS
API Gateway (Spring Cloud Gateway)
     ├── Authentication/Authorization
     ├── Rate Limiting
     ├── Load Balancing
     └── SSL Termination
     ↓
Load Balancer
     ├── User Service (3 replicas)
     ├── Product Service (3 replicas)
     ├── Order Service (3 replicas)
     └── Payment Service (3 replicas)
     ↓
Communication Layer:
     ├── Sync: Feign Client (REST) / gRPC (high performance)
     └── Async: Kafka Topics (order-events, payment-events)
     ↓
Data Layer:
     ├── User DB: PostgreSQL (Strong consistency)
     ├── Product DB: MongoDB (flexible schema)
     ├── Order DB: PostgreSQL
     └── Payment DB: PostgreSQL (ACID critical)
     ↓
Supporting Services:
     ├── Eureka (Service Registry)
     ├── Spring Cloud Config Server
     ├── Zipkin (Distributed Tracing)
     └── ELK Stack (Centralized Logging)
```

---

## Q3: Implement Circuit Breaker with Resilience4j (Full Example)

```java
// pom.xml
// <dependency>
//     <groupId>io.github.resilience4j</groupId>
//     <artifactId>resilience4j-spring-boot3</artifactId>
// </dependency>

// application.yml
resilience4j:
  circuitbreaker:
    instances:
      inventoryService:
        register-health-indicator: true
        failure-rate-threshold: 50          # 50% failure → OPEN
        slow-call-rate-threshold: 80        # 80% slow → OPEN
        slow-call-duration-threshold: 2s    # > 2s = slow
        wait-duration-in-open-state: 30s   # Stay OPEN 30s before HALF-OPEN
        permitted-number-of-calls-in-half-open-state: 3
        sliding-window-size: 10
        minimum-number-of-calls: 5
  retry:
    instances:
      inventoryService:
        max-attempts: 3
        wait-duration: 500ms
        exponential-backoff-multiplier: 2
        retry-exceptions:
          - feign.FeignException$ServiceUnavailable
          - java.net.ConnectException
  timelimiter:
    instances:
      inventoryService:
        timeout-duration: 3s

// Service
@Service
@Slf4j
public class OrderService {

    private final InventoryServiceClient inventoryClient;

    @CircuitBreaker(name = "inventoryService", fallbackMethod = "inventoryFallback")
    @Retry(name = "inventoryService")
    @TimeLimiter(name = "inventoryService")
    public CompletableFuture<InventoryStatus> checkInventory(String productId) {
        return CompletableFuture.supplyAsync(
            () -> inventoryClient.checkStock(productId)
        );
    }

    // Fallback — called when circuit is OPEN
    public CompletableFuture<InventoryStatus> inventoryFallback(
            String productId, Exception ex) {
        log.warn("Inventory service unavailable for productId={}, reason={}",
            productId, ex.getMessage());
        // Return cached/default response — never fail the customer
        return CompletableFuture.completedFuture(
            InventoryStatus.assume(productId, true) // Optimistic — check later
        );
    }
}
```

### Circuit Breaker States:
```
CLOSED (normal) → OPEN (failing) → HALF-OPEN (testing) → CLOSED (recovered)

CLOSED: Requests flow normally. Tracks failure rate.
  └── failure rate > 50% → transitions to OPEN

OPEN: Rejects requests immediately. Returns fallback.
  └── After 30s → transitions to HALF-OPEN

HALF-OPEN: Allows limited requests (3) to test service.
  └── If 3 succeed → CLOSED
  └── If any fail → OPEN again
```

---

## Q4: Saga Pattern — Handle Distributed Transactions

### Choreography-based Saga:
```
Order Service: Save order (PENDING) → Publish OrderCreated
    ↓ Kafka
Payment Service: Subscribe OrderCreated → Charge card → Publish PaymentCompleted
    ↓ Kafka
Inventory Service: Subscribe PaymentCompleted → Reserve stock → Publish StockReserved
    ↓ Kafka
Shipping Service: Subscribe StockReserved → Schedule shipment → Publish ShippingScheduled
    ↓ Kafka
Order Service: Subscribe ShippingScheduled → Update order to CONFIRMED

FAILURE PATH:
Payment fails → Publish PaymentFailed
Order Service: Subscribe PaymentFailed → Update order to CANCELLED → Publish OrderCancelled
```

```java
@Service
public class PaymentService {

    @KafkaListener(topics = "order-created")
    public void handleOrderCreated(OrderCreatedEvent event) {
        try {
            GatewayResponse response = gateway.charge(
                event.getOrderId(),
                event.getAmount(),
                event.getCustomerCardToken()
            );

            // Success → trigger next step
            kafkaTemplate.send("payment-completed", new PaymentCompletedEvent(
                event.getOrderId(),
                response.getTransactionId()
            ));

        } catch (PaymentException ex) {
            // Failure → trigger compensating transaction
            kafkaTemplate.send("payment-failed", new PaymentFailedEvent(
                event.getOrderId(),
                ex.getErrorCode(),
                ex.getMessage()
            ));
        }
    }
}
```

---

## Q5: Service Discovery with Eureka

```java
// Eureka Server
@SpringBootApplication
@EnableEurekaServer
public class ServiceRegistryApplication {
    public static void main(String[] args) {
        SpringApplication.run(ServiceRegistryApplication.class, args);
    }
}

// Eureka Client (each microservice)
@SpringBootApplication
@EnableDiscoveryClient
public class PaymentServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(PaymentServiceApplication.class, args);
    }
}

// application.yml for client
eureka:
  client:
    service-url:
      defaultZone: http://eureka-server:8761/eureka
    fetch-registry: true
    register-with-eureka: true
  instance:
    prefer-ip-address: true
    instance-id: ${spring.application.name}:${server.port}
    lease-renewal-interval-in-seconds: 10  # Heartbeat every 10s

// Feign Client — service-to-service with load balancing
@FeignClient(name = "inventory-service", fallback = InventoryFallback.class)
public interface InventoryServiceClient {
    @GetMapping("/api/inventory/{productId}")
    InventoryStatus checkStock(@PathVariable String productId);

    @PostMapping("/api/inventory/reserve")
    ReservationResult reserveStock(@RequestBody ReservationRequest request);
}

@Component
public class InventoryFallback implements InventoryServiceClient {
    @Override
    public InventoryStatus checkStock(String productId) {
        return InventoryStatus.unknown(productId);
    }

    @Override
    public ReservationResult reserveStock(ReservationRequest request) {
        throw new ServiceUnavailableException("Inventory service unavailable");
    }
}
```

---

## Q6: API Gateway with Spring Cloud Gateway

```java
@Configuration
public class GatewayConfig {

    @Bean
    public RouteLocator routeLocator(RouteLocatorBuilder builder) {
        return builder.routes()
            // User Service route
            .route("user-service", r -> r
                .path("/api/users/**")
                .filters(f -> f
                    .stripPrefix(1)
                    .addRequestHeader("X-Service-Name", "gateway")
                    .requestRateLimiter(config -> config
                        .setRateLimiter(redisRateLimiter())
                        .setKeyResolver(userKeyResolver()))
                    .circuitBreaker(cb -> cb
                        .setName("user-service-cb")
                        .setFallbackUri("forward:/fallback/users"))
                )
                .uri("lb://user-service"))  // Load balanced
            // Payment Service route with auth
            .route("payment-service", r -> r
                .path("/api/payments/**")
                .filters(f -> f
                    .filter(jwtAuthGatewayFilter)
                    .retry(config -> config.setRetries(3).setMethods(HttpMethod.GET)))
                .uri("lb://payment-service"))
            .build();
    }

    @Bean
    public RedisRateLimiter redisRateLimiter() {
        return new RedisRateLimiter(10, 20, 1); // 10 req/sec, burst 20
    }
}
```

---

## Q7: Distributed Tracing with Sleuth + Zipkin

```yaml
# application.yml
spring:
  sleuth:
    sampler:
      probability: 1.0  # 100% sampling (reduce in prod)
  zipkin:
    base-url: http://zipkin:9411

# Every log now includes traceId and spanId:
# [payment-service,traceId=abc123,spanId=def456] Processing payment
```

```java
// Custom span
@Service
public class PaymentService {

    private final Tracer tracer;

    public PaymentResult processPayment(Payment payment) {
        Span span = tracer.nextSpan().name("payment.gateway.charge").start();
        try (Tracer.SpanInScope ws = tracer.withSpanInScope(span)) {
            span.tag("payment.id", payment.getId());
            span.tag("payment.amount", payment.getAmount().toString());

            GatewayResponse response = gateway.charge(payment);

            span.tag("gateway.tx.id", response.getTransactionId());
            return PaymentResult.success(response);
        } catch (Exception ex) {
            span.error(ex);
            throw ex;
        } finally {
            span.finish();
        }
    }
}
```

---

## Q8: CQRS Pattern — Command Query Responsibility Segregation

```
Command Side (Write):
  └── OrderCommandService
      ├── createOrder() → writes to PostgreSQL → publishes OrderCreated
      └── cancelOrder() → writes to PostgreSQL → publishes OrderCancelled

Query Side (Read):
  └── OrderQueryService
      ├── getOrderById() → reads from Elasticsearch (denormalized view)
      └── getOrdersByCustomer() → reads from Read DB (optimized for queries)

Event Router:
  └── Kafka Consumer listens to events
      └── Updates Elasticsearch index
      └── Updates Read DB
```

```java
// Command Handler
@Service
@Transactional
public class OrderCommandService {

    public OrderId createOrder(CreateOrderCommand cmd) {
        Order order = Order.create(cmd);
        orderRepo.save(order);
        // Publish event for query side synchronization
        eventPublisher.publish(new OrderCreatedEvent(order));
        return order.getId();
    }
}

// Order Query Handler (reads from optimized read model)
@Service
@Transactional(readOnly = true)
public class OrderQueryService {

    @Autowired
    private OrderReadRepository readRepo; // Elasticsearch or optimized DB

    public OrderView getOrder(String orderId) {
        return readRepo.findById(orderId)
            .orElseThrow(() -> new OrderNotFoundException(orderId));
    }

    public Page<OrderSummary> getCustomerOrders(String customerId, Pageable pageable) {
        return readRepo.findByCustomerId(customerId, pageable);
    }
}

// Event Handler — syncs command side to query side
@KafkaListener(topics = "order-events")
@Transactional
public void handleOrderEvent(OrderEvent event) {
    switch (event.getType()) {
        case "ORDER_CREATED" -> {
            OrderView view = OrderView.from(event);
            orderReadRepo.save(view);
            elasticsearchRepo.index(view);
        }
        case "ORDER_CANCELLED" -> {
            orderReadRepo.updateStatus(event.getOrderId(), "CANCELLED");
            elasticsearchRepo.updateStatus(event.getOrderId(), "CANCELLED");
        }
    }
}
```

---

## Q9: Common Microservices Interview Questions

### "How do you handle service to service authentication?"
```java
// OAuth2 Client Credentials (M2M — Machine to Machine)
@Configuration
public class ServiceSecurityConfig {
    @Bean
    public OAuth2AuthorizedClientManager clientManager(
            ClientRegistrationRepository repo,
            OAuth2AuthorizedClientService service) {
        return new AuthorizedClientServiceOAuth2AuthorizedClientManager(repo, service);
    }

    @Bean
    public WebClient orderServiceClient(OAuth2AuthorizedClientManager manager) {
        // Automatically attaches Bearer token to every request
        return WebClient.builder()
            .baseUrl("http://order-service")
            .apply(oauth2Client.oauth2Configuration(manager))
            .build();
    }
}
```

### "What is the difference between REST and gRPC?"
```
REST:
  + Human readable (JSON)
  + Browser compatible
  + Easy to debug
  - Larger payload
  - No streaming
  - Loose contract

gRPC (Protocol Buffers):
  + Binary → 5-10x smaller, faster serialization
  + Streaming (bidirectional)
  + Strict contract (proto file)
  + Code generation
  - Not human readable
  - Not browser native (needs grpc-web)
  Use: internal microservice communication at high throughput
```
