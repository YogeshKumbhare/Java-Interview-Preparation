# ⚡ Reactive Programming (Spring WebFlux) — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Reactive Programming?

Reactive programming is an **asynchronous, non-blocking**, and **event-driven** programming paradigm that deals with data streams and the propagation of change. In the Java ecosystem, it's standardized by the **Reactive Streams** specification.

### Traditional (Spring MVC) vs Reactive (Spring WebFlux)

| Feature | Spring MVC (Traditional) | Spring WebFlux (Reactive) |
|---------|-------------------------|---------------------------|
| Architecture | Thread-per-request | Event Loop (Node.js style) |
| I/O Model | Blocking I/O | Non-blocking I/O |
| Server | Tomcat / Jetty | Netty / Undertow |
| Backpressure | Not supported | Native support |
| Ideal Use Case| CPU intensive, JDBC DBs | I/O intensive, streaming data, microservices gateways |
| Threads used | Hundreds (e.g., 200 default Tomcat) | Few (One per CPU core) |

> ⚠️ **Warning:** If you use a blocking database driver (like JDBC/Hibernate) in WebFlux, you ruin the reactive model. You MUST use reactive drivers like R2DBC, Reactive Redis, or Reactive MongoDB.

---

## 📖 Mono vs Flux (Project Reactor)

Project Reactor provides two core publishers:

1.  **`Mono<T>`**: Emits **0 or 1** element. (Similar to `Optional<T>` or a single Future). Use for typical HTTP requests returning one object.
2.  **`Flux<T>`**: Emits **0 to N** elements. Use for lists, streaming data (e.g., Server-Sent Events, continuously updating prices).

### Code Examples: Creating Monos and Fluxes

```java
// MONO — 0 or 1 element
Mono<String> mono = Mono.just("Hello Reactor")
                        .map(String::toUpperCase)
                        .doOnNext(System.out::println);
// Nothing happens until we SUBSCRIBE!
mono.subscribe(); 

// FLUX — 0 to N elements
Flux<Integer> flux = Flux.just(1, 2, 3, 4, 5)
                         .filter(n -> n % 2 == 0) // Keep evens: 2, 4
                         .map(n -> n * 10);       // Multiply: 20, 40

flux.subscribe(
    data -> System.out.println("Item: " + data),
    error -> System.err.println("Error: " + error),
    () -> System.out.println("Stream completed!")
);
```

---

## 📖 What is Backpressure?

**Backpressure** is a mechanism that allows the consumer (Subscriber) to tell the producer (Publisher) **how much data it can handle**. 
Without backpressure, a fast producer can overwhelm a slow consumer, leading to `OutOfMemoryError` (OOM).

**How it works:**
1. Subscriber requests exactly `n` items: `subscription.request(n)`
2. Publisher sends exactly `n` items, then waits.
3. Once the Subscriber processes them, it requests another batch.

---

## 📖 Real-World Spring WebFlux Example

### 1. Reactive Controller + WebClient

WebFlux applications don't use `RestTemplate` (which is blocking). They use the non-blocking `WebClient`.

```java
@RestController
@RequestMapping("/api/products")
public class ProductReactiveController {

    private final WebClient webClient;
    private final ProductRepository repository; // Uses R2DBC, not JPA!

    public ProductReactiveController(WebClient.Builder webClientBuilder, ProductRepository repo) {
        this.webClient = webClientBuilder.baseUrl("http://pricing-service").build();
        this.repository = repo;
    }

    // MONO: Get a single product and enrich it with a remote API call asynchronously
    @GetMapping("/{id}")
    public Mono<ResponseEntity<ProductDto>> getProduct(@PathVariable String id) {
        return repository.findById(id) // Non-blocking DB call (Returns Mono<Product>)
            .flatMap(product -> {
                // Non-blocking external API call
                Mono<Price> priceMono = webClient.get()
                    .uri("/prices/{id}", id)
                    .retrieve()
                    .bodyToMono(Price.class);
                
                // Combine product + price
                return priceMono.map(price -> new ProductDto(product, price));
            })
            .map(dto -> ResponseEntity.ok(dto))
            .defaultIfEmpty(ResponseEntity.notFound().build());
    }

    // FLUX: Streaming real-time data using Server-Sent Events (SSE)
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<ProductUpdate> streamUpdates() {
        return repository.findAllByStatus("ACTIVE")
                // Delay each element by 1 second to simulate a stream
                .delayElements(Duration.ofSeconds(1))
                .map(product -> new ProductUpdate(product.getId(), "UPDATED"));
    }
}
```

### 2. Reactive Database (R2DBC)
Reactive Relational Database Connectivity (R2DBC) enables reactive, non-blocking APIs for SQL databases (PostgreSQL, MySQL).

```java
public interface ProductRepository extends ReactiveCrudRepository<Product, String> {
    
    // Returns a Flux! The database connection is never blocked waiting for rows
    @Query("SELECT * FROM products WHERE status = :status")
    Flux<Product> findAllByStatus(String status);
}
```

---

## Common Interview Questions (Cross-Questioning)

### Q: "You mentioned WebFlux is faster. Should we migrate all our Spring Boot MVC microservices to WebFlux to improve performance?"
**Answer:**
*   "No. WebFlux does **not** make queries execute faster. It allows the server to handle **more concurrent connections** with fewer threads."
*   "If an API is CPU-heavy (image processing, encryption), WebFlux will perform WORSE because blocking one of the few Event-Loop threads halts the whole application."
*   "If the API is I/O heavy (API gateway, streaming data, chatting app) and we hit Tomcat's max thread limits, we should switch to WebFlux."

### Q: "What happens if a developer uses `Thread.sleep()` or calls a blocking JDBC database inside a WebFlux `map()` operator?"
**Answer:**
*   "This is a catastrophic anti-pattern called **Event Loop Blocking**. WebFlux runs on a very small thread pool (usually 1 thread per CPU core). If one thread calls `Thread.sleep()` or a blocking DB, that thread freezes."
*   "If all Event Loop threads freeze, the entire application stops accepting new requests, causing a complete system hang."
*   "We catch this in development using the **BlockHound** library, which crashes the app if any blocking call is detected in a reactive thread."

### Q: "How does Java 21 Virtual Threads (Project Loom) impact Spring WebFlux?"
**Answer:**
*   "Virtual Threads drastically reduce the need for WebFlux for many standard CRUD applications. Virtual threads allow traditional Spring MVC to scale to millions of concurrent connections without the complex Mono/Flux syntax."
*   "However, WebFlux remains relevant for backpressure handling and true continuous data streaming (like WebSockets or SSE), which Virtual Threads don't natively solve."
