# 🍃 Spring Framework Advanced — Complete Interview Q&A
## Target: 12+ Years Experience | Every Spring Question Covered

> **Note:** This file covers topics NOT already in Spring-Boot-QA.md. Together they provide 100% coverage.

---

## Q15: Spring MVC Request Lifecycle — What happens when a request hits your Spring Boot app?

### Theory:
Understanding the full request lifecycle is critical — interviewers love this question because it tests deep Spring knowledge.

```
HTTP Request
    ↓
1. Tomcat (Embedded Server) receives HTTP request
    ↓
2. Servlet Filter Chain (Spring Security, CORS, Logging filters)
    ↓
3. DispatcherServlet (Front Controller — single entry point)
    ↓
4. HandlerMapping — finds the right Controller + method
   (RequestMappingHandlerMapping scans @RequestMapping/@GetMapping)
    ↓
5. HandlerInterceptor.preHandle() — cross-cutting (auth, logging)
    ↓
6. HandlerAdapter invokes the Controller method
    ↓
7. @RequestBody → HttpMessageConverter (Jackson) deserializes JSON → Java object
    ↓
8. @Valid triggers Bean Validation (JSR 380)
    ↓
9. Controller executes business logic (calls Service → Repository → DB)
    ↓
10. Return value → HttpMessageConverter serializes Java object → JSON
    ↓
11. HandlerInterceptor.postHandle()
    ↓
12. ViewResolver (if returning view name) or @ResponseBody (REST)
    ↓
13. HandlerInterceptor.afterCompletion()
    ↓
14. Response filters (compression, CORS headers)
    ↓
HTTP Response
```

```java
// Custom HandlerInterceptor — real-world: request logging + timing
@Component
public class RequestTimingInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest req, HttpServletResponse res,
                             Object handler) {
        req.setAttribute("startTime", System.currentTimeMillis());
        MDC.put("requestId", UUID.randomUUID().toString()); // For log tracing
        return true; // true = continue chain, false = block request
    }

    @Override
    public void postHandle(HttpServletRequest req, HttpServletResponse res,
                           Object handler, ModelAndView mav) {
        // After controller but before view rendering
    }

    @Override
    public void afterCompletion(HttpServletRequest req, HttpServletResponse res,
                                Object handler, Exception ex) {
        long duration = System.currentTimeMillis() - (Long) req.getAttribute("startTime");
        log.info("[{}] {} {} → {} ({}ms)", MDC.get("requestId"),
                req.getMethod(), req.getRequestURI(), res.getStatus(), duration);
        MDC.clear();
    }
}

// Register the interceptor
@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Autowired private RequestTimingInterceptor timingInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(timingInterceptor)
                .addPathPatterns("/api/**")
                .excludePathPatterns("/api/health");
    }
}
```

---

## Q16: DispatcherServlet — The Heart of Spring MVC

### Theory:
**DispatcherServlet** is the **Front Controller** — ALL HTTP requests go through it. Spring Boot auto-registers it mapped to `/`.

```
DispatcherServlet internal flow:
┌─────────────────────────────────────────┐
│            DispatcherServlet            │
│                                         │
│  doDispatch(request, response) {        │
│    1. getHandler()                      │
│       → HandlerMapping.getHandler()     │
│       → Returns HandlerExecutionChain   │
│         (Controller + Interceptors)     │
│                                         │
│    2. getHandlerAdapter()               │
│       → RequestMappingHandlerAdapter    │
│                                         │
│    3. applyPreHandle() — interceptors   │
│                                         │
│    4. adapter.handle() — invoke method  │
│       → Argument resolution            │
│       → Method invocation              │
│       → Return value handling          │
│                                         │
│    5. applyPostHandle()                 │
│                                         │
│    6. processDispatchResult()           │
│       → Render view or write response  │
│  }                                      │
└─────────────────────────────────────────┘
```

```java
// How Spring resolves method arguments:
@RestController
@RequestMapping("/api/orders")
public class OrderController {

    // @PathVariable — from URL path
    @GetMapping("/{orderId}")
    public Order getOrder(@PathVariable String orderId) { ... }

    // @RequestParam — from query string ?status=PENDING
    @GetMapping
    public List<Order> getOrders(@RequestParam(defaultValue = "ACTIVE") String status,
                                 @RequestParam(required = false) Integer page) { ... }

    // @RequestBody — from HTTP body (JSON deserialized by Jackson)
    @PostMapping
    public ResponseEntity<Order> createOrder(@Valid @RequestBody OrderRequest request) {
        Order order = orderService.create(request);
        URI location = URI.create("/api/orders/" + order.getId());
        return ResponseEntity.created(location).body(order);
    }

    // @RequestHeader — from HTTP headers
    @GetMapping("/me")
    public Order getMyOrder(@RequestHeader("X-User-Id") String userId) { ... }

    // @CookieValue — from cookies
    @GetMapping("/session")
    public Order getSessionOrder(@CookieValue("sessionId") String sessionId) { ... }

    // @ModelAttribute — from form data
    @PostMapping("/form")
    public String submitForm(@ModelAttribute OrderForm form) { ... }
}
```

---

## Q17: @RestController vs @Controller — What's the difference?

```java
// @Controller — returns VIEW NAME (MVC with Thymeleaf/JSP)
@Controller
public class PageController {
    @GetMapping("/home")
    public String homePage(Model model) {
        model.addAttribute("user", userService.getCurrentUser());
        return "home"; // Returns view name → ViewResolver finds home.html
    }
}

// @RestController = @Controller + @ResponseBody on every method
// Returns data directly (JSON/XML) — no view resolution
@RestController // Every method automatically has @ResponseBody
@RequestMapping("/api/users")
public class UserController {
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id); // Object → JSON automatically
    }
}

// @ResponseBody on individual methods (when using @Controller)
@Controller
public class HybridController {
    @GetMapping("/page")
    public String page() { return "page-view"; }  // Returns view

    @GetMapping("/api/data")
    @ResponseBody  // This specific method returns JSON
    public DataResponse getData() { return new DataResponse(); }
}
```

---

## Q18: Global Exception Handling — @ControllerAdvice & @ExceptionHandler

```java
// Production-grade global error handling
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {

    // 1. Business exceptions — known errors
    @ExceptionHandler(ResourceNotFoundException.class)
    @ResponseStatus(HttpStatus.NOT_FOUND)
    public ErrorResponse handleNotFound(ResourceNotFoundException ex, WebRequest request) {
        log.warn("Resource not found: {}", ex.getMessage());
        return ErrorResponse.builder()
                .timestamp(Instant.now())
                .status(404)
                .error("Not Found")
                .message(ex.getMessage())
                .path(request.getDescription(false))
                .build();
    }

    // 2. Validation errors — @Valid failed
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleValidation(MethodArgumentNotValidException ex) {
        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getFieldErrors().forEach(error ->
            errors.put(error.getField(), error.getDefaultMessage())
        );
        return ErrorResponse.builder()
                .status(400)
                .error("Validation Failed")
                .message("Request body has invalid fields")
                .fieldErrors(errors) // {"email": "must not be blank", "age": "must be > 0"}
                .build();
    }

    // 3. Constraint violations — @PathVariable/@RequestParam validation
    @ExceptionHandler(ConstraintViolationException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleConstraintViolation(ConstraintViolationException ex) {
        return ErrorResponse.builder()
                .status(400)
                .message(ex.getMessage())
                .build();
    }

    // 4. Optimistic locking — concurrent modification
    @ExceptionHandler(OptimisticLockingFailureException.class)
    @ResponseStatus(HttpStatus.CONFLICT)
    public ErrorResponse handleConflict(OptimisticLockingFailureException ex) {
        return ErrorResponse.builder()
                .status(409)
                .message("Resource was modified by another request. Please retry.")
                .build();
    }

    // 5. Catch-all — unexpected errors
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleGeneric(Exception ex) {
        log.error("Unexpected error", ex); // Full stack trace in logs
        return ErrorResponse.builder()
                .status(500)
                .message("An unexpected error occurred") // Don't expose internals!
                .build();
    }
}
```

---

## Q19: Spring Data JPA — Repository Pattern & Custom Queries

```java
// 1. JpaRepository — standard CRUD + pagination + sorting
public interface OrderRepository extends JpaRepository<Order, Long> {

    // Query derivation — Spring generates SQL from method name!
    List<Order> findByStatusAndCreatedAtAfter(OrderStatus status, Instant date);

    Optional<Order> findByOrderIdAndUserId(String orderId, Long userId);

    List<Order> findTop10ByUserIdOrderByCreatedAtDesc(Long userId);

    boolean existsByOrderIdAndStatus(String orderId, OrderStatus status);

    long countByStatus(OrderStatus status);

    // 2. @Query — custom JPQL
    @Query("SELECT o FROM Order o WHERE o.userId = :userId AND o.amount > :minAmount")
    List<Order> findLargeOrders(@Param("userId") Long userId,
                                @Param("minAmount") BigDecimal minAmount);

    // 3. Native SQL — when JPQL can't express the query
    @Query(value = "SELECT * FROM orders WHERE status = 'PENDING' " +
                   "AND created_at < NOW() - INTERVAL '24 hours'",
           nativeQuery = true)
    List<Order> findStaleOrders();

    // 4. @Modifying — for UPDATE/DELETE operations
    @Modifying
    @Transactional
    @Query("UPDATE Order o SET o.status = :status WHERE o.id = :id")
    int updateStatus(@Param("id") Long id, @Param("status") OrderStatus status);

    // 5. Pagination + Sorting
    Page<Order> findByUserId(Long userId, Pageable pageable);
    // Usage: orderRepo.findByUserId(1L, PageRequest.of(0, 20, Sort.by("createdAt").descending()));

    // 6. Projections — fetch only needed fields (performance!)
    @Query("SELECT o.orderId as orderId, o.status as status, o.amount as amount FROM Order o WHERE o.userId = :userId")
    List<OrderSummary> findOrderSummaries(@Param("userId") Long userId);
}

// Projection interface
public interface OrderSummary {
    String getOrderId();
    OrderStatus getStatus();
    BigDecimal getAmount();
}

// 7. Specification — dynamic queries (like WHERE clause builder)
public class OrderSpecifications {
    public static Specification<Order> hasStatus(OrderStatus status) {
        return (root, query, cb) -> cb.equal(root.get("status"), status);
    }

    public static Specification<Order> amountGreaterThan(BigDecimal amount) {
        return (root, query, cb) -> cb.greaterThan(root.get("amount"), amount);
    }

    public static Specification<Order> createdBetween(Instant from, Instant to) {
        return (root, query, cb) -> cb.between(root.get("createdAt"), from, to);
    }
}

// Usage: combine specs dynamically
public interface OrderRepository extends JpaRepository<Order, Long>,
                                         JpaSpecificationExecutor<Order> {}

// In service:
Specification<Order> spec = OrderSpecifications.hasStatus(PENDING)
    .and(OrderSpecifications.amountGreaterThan(BigDecimal.valueOf(1000)));
List<Order> results = orderRepo.findAll(spec);
```

---

## Q20: @Transactional Deep Dive — Isolation, Read-Only, Rollback

```java
@Service
public class AccountService {

    // DEFAULT: Propagation.REQUIRED, Isolation.DEFAULT, rollbackFor RuntimeException
    @Transactional
    public void transfer(Long fromId, Long toId, BigDecimal amount) {
        // Both operations in same transaction — atomic
        accountRepo.debit(fromId, amount);
        accountRepo.credit(toId, amount);
    }

    // ISOLATION LEVELS:
    @Transactional(isolation = Isolation.READ_COMMITTED)
    // Prevents: dirty reads
    // Allows: non-repeatable reads, phantom reads
    // DEFAULT for PostgreSQL

    @Transactional(isolation = Isolation.REPEATABLE_READ)
    // Prevents: dirty reads, non-repeatable reads
    // Allows: phantom reads
    // DEFAULT for MySQL InnoDB

    @Transactional(isolation = Isolation.SERIALIZABLE)
    // Prevents: ALL anomalies (dirty, non-repeatable, phantom)
    // SLOWEST — locks entire table range
    // Use for: financial calculations, balance checks

    // READ-ONLY optimization
    @Transactional(readOnly = true)
    public List<Order> getOrders(Long userId) {
        // Hibernate skips dirty-checking (faster)
        // DB may route to read replica
        return orderRepo.findByUserId(userId);
    }

    // ROLLBACK control
    @Transactional(rollbackFor = Exception.class) // Rollback on ALL exceptions
    // Default only rolls back on RuntimeException (unchecked)

    @Transactional(noRollbackFor = EmailSendException.class)
    // Don't rollback if email fails — order should still be saved

    // TIMEOUT
    @Transactional(timeout = 5) // 5 seconds — throws TransactionTimedOutException
    public void longRunning() { ... }
}

// ⚠️ GOTCHA: Self-invocation — @Transactional DOESN'T WORK on internal calls!
@Service
public class OrderService {
    @Transactional
    public void processOrder(Order order) {
        save(order);
        notifyCustomer(order); // ❌ This call BYPASSES the proxy!
    }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void notifyCustomer(Order order) {
        // NOT in a new transaction! Called directly, not through proxy
    }

    // FIX 1: Inject self
    @Autowired @Lazy private OrderService self;
    public void processOrderFixed(Order order) {
        save(order);
        self.notifyCustomer(order); // ✅ Goes through proxy
    }

    // FIX 2: Extract to separate service
    // FIX 3: Use TransactionTemplate for programmatic control
}
```

---

## Q21: Spring WebFlux — Reactive Programming (Non-Blocking)

### Theory:
**Spring WebFlux** is the reactive alternative to Spring MVC. Uses **Project Reactor** (`Mono` and `Flux`) for non-blocking I/O. Single thread handles thousands of requests.

```
Spring MVC (Thread-per-request):          Spring WebFlux (Event Loop):
┌──────────┐                              ┌──────────┐
│ Request 1│→ Thread 1 ──── blocks ─┐     │ Request 1│→ Event Loop ─┐
│ Request 2│→ Thread 2 ──── blocks  │     │ Request 2│→ Event Loop  │ non-blocking
│ Request 3│→ Thread 3 ──── blocks  │     │ Request 3│→ Event Loop  │ all on few
│ ...      │→ Thread N ──── blocks  │     │ ...1000s │→ Event Loop ─┘ threads!
└──────────┘      200 max threads ──┘     └──────────┘
```

```java
@RestController
@RequestMapping("/api/orders")
public class ReactiveOrderController {

    // Mono<T> — 0 or 1 element (like Optional but asynchronous)
    @GetMapping("/{id}")
    public Mono<Order> getOrder(@PathVariable String id) {
        return orderService.findById(id); // Non-blocking database call
    }

    // Flux<T> — 0 to N elements (like Stream but asynchronous)
    @GetMapping
    public Flux<Order> getAllOrders() {
        return orderService.findAll(); // Streams results as they arrive
    }

    // Server-Sent Events — real-time streaming
    @GetMapping(value = "/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<Order> streamOrders() {
        return orderService.findAll()
                .delayElements(Duration.ofSeconds(1)); // Emit one per second
    }

    @PostMapping
    public Mono<ResponseEntity<Order>> createOrder(@Valid @RequestBody Mono<OrderRequest> request) {
        return request
                .flatMap(orderService::create)
                .map(order -> ResponseEntity.created(URI.create("/api/orders/" + order.getId()))
                        .body(order));
    }
}

// Reactive Repository (R2DBC — Reactive database driver)
public interface OrderRepository extends ReactiveCrudRepository<Order, String> {
    Flux<Order> findByUserId(String userId);
    Mono<Order> findByOrderId(String orderId);
}

// WebClient — reactive HTTP client (replaces RestTemplate)
@Service
public class PaymentClient {
    private final WebClient webClient;

    public PaymentClient(WebClient.Builder builder) {
        this.webClient = builder.baseUrl("http://payment-service").build();
    }

    public Mono<PaymentResponse> chargePayment(PaymentRequest request) {
        return webClient.post()
                .uri("/api/payments")
                .bodyValue(request)
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError,
                    resp -> resp.bodyToMono(String.class)
                               .flatMap(body -> Mono.error(new PaymentException(body))))
                .bodyToMono(PaymentResponse.class)
                .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)));
    }
}
```

### When to use WebFlux vs MVC:
| Use MVC | Use WebFlux |
|---------|-------------|
| CRUD apps, simple APIs | High concurrency (10K+ connections) |
| Team familiar with imperative | Streaming / real-time data |
| Blocking libraries (JDBC, JPA) | Microservice gateway |
| Easier debugging | Non-blocking end-to-end |

---

## Q22: Spring Scheduler — @Scheduled & Task Execution

```java
@Configuration
@EnableScheduling
@EnableAsync
public class SchedulerConfig {

    @Bean
    public TaskScheduler taskScheduler() {
        ThreadPoolTaskScheduler scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(5);
        scheduler.setThreadNamePrefix("scheduler-");
        scheduler.setErrorHandler(t -> log.error("Scheduler error", t));
        return scheduler;
    }

    @Bean
    public TaskExecutor asyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        return executor;
    }
}

@Service
@Slf4j
public class ScheduledTasks {

    // Fixed rate — runs every 60 seconds (measured from START of previous)
    @Scheduled(fixedRate = 60000)
    public void heartbeat() {
        log.info("Heartbeat at {}", Instant.now());
    }

    // Fixed delay — 30s AFTER previous execution COMPLETES
    @Scheduled(fixedDelay = 30000, initialDelay = 10000)
    public void processStaleOrders() {
        orderService.cancelStaleOrders();
    }

    // Cron expression — every day at 2 AM
    @Scheduled(cron = "0 0 2 * * ?")
    public void dailyReport() {
        reportService.generateDailyReport();
    }

    // Cron — every Monday at 9 AM
    @Scheduled(cron = "0 0 9 ? * MON")
    public void weeklyDigest() { ... }

    // Zone-aware cron
    @Scheduled(cron = "0 0 2 * * ?", zone = "Asia/Kolkata")
    public void dailyBackup() { ... }

    // @Async — execute method in separate thread
    @Async("asyncExecutor")
    public CompletableFuture<Report> generateReportAsync(String reportType) {
        Report report = heavyReportGeneration(reportType);
        return CompletableFuture.completedFuture(report);
    }
}

// Cron Expression Quick Reference:
// ┌──────── second (0-59)
// │ ┌────── minute (0-59)
// │ │ ┌──── hour (0-23)
// │ │ │ ┌── day of month (1-31)
// │ │ │ │ ┌ month (1-12)
// │ │ │ │ │ ┌ day of week (0-7, 0/7=Sun)
// │ │ │ │ │ │
// * * * * * *
// "0 0 * * * ?" → every hour
// "0 */15 * * * ?" → every 15 minutes
// "0 0 0 * * ?" → midnight daily
```

---

## Q23: Spring Filters vs Interceptors vs AOP — When to use which?

```
Request Flow:
  HTTP Request
      ↓
  ┌─── FILTER (Servlet level) ──────────┐
  │  Security, CORS, Logging, Encoding  │
  │  Access: HttpServletRequest/Response│
  │  No access to Spring beans easily   │
  └─────────────────────────────────────┘
      ↓
  DispatcherServlet
      ↓
  ┌─── INTERCEPTOR (Spring MVC level) ──┐
  │  Auth checks, Timing, Audit logging │
  │  Access: Handler (Controller) info  │
  │  Full Spring context access         │
  └─────────────────────────────────────┘
      ↓
  ┌─── AOP (Method level) ──────────────┐
  │  @Transactional, @Cacheable, Custom│
  │  Works on ANY Spring bean method    │
  │  Not limited to web requests        │
  └─────────────────────────────────────┘
      ↓
  Controller → Service → Repository
```

| | Filter | Interceptor | AOP |
|--|--------|-------------|-----|
| **Level** | Servlet (pre-Spring) | Spring MVC | Any Spring bean |
| **Interface** | `javax.servlet.Filter` | `HandlerInterceptor` | `@Aspect` |
| **Access** | Request/Response only | Handler + ModelAndView | Method args + return |
| **Use for** | Security, CORS, compression | Request logging, auth | Cross-cutting concerns |
| **Scope** | ALL requests (including static) | Only dispatched requests | Any method invocation |

```java
// FILTER example — request/response logging
@Component
@Order(1) // Execution order among filters
public class RequestLoggingFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws IOException, ServletException {
        ContentCachingRequestWrapper wrappedReq = new ContentCachingRequestWrapper(request);
        ContentCachingResponseWrapper wrappedRes = new ContentCachingResponseWrapper(response);

        long start = System.currentTimeMillis();
        filterChain.doFilter(wrappedReq, wrappedRes);
        long duration = System.currentTimeMillis() - start;

        log.info("{} {} → {} ({}ms)", request.getMethod(),
                request.getRequestURI(), response.getStatus(), duration);

        wrappedRes.copyBodyToResponse(); // IMPORTANT: copy cached body to actual response
    }
}
```

---

## Q24: Spring Validation — Bean Validation (JSR 380)

```java
// Request DTO with validation annotations
public class CreateUserRequest {

    @NotBlank(message = "Name is required")
    @Size(min = 2, max = 100, message = "Name must be 2-100 characters")
    private String name;

    @NotBlank(message = "Email is required")
    @Email(message = "Invalid email format")
    private String email;

    @NotNull(message = "Age is required")
    @Min(value = 18, message = "Must be at least 18")
    @Max(value = 120, message = "Must be at most 120")
    private Integer age;

    @Pattern(regexp = "^\\+[1-9]\\d{6,14}$", message = "Invalid phone number")
    private String phone;

    @NotNull @Valid  // @Valid triggers cascading validation on nested object
    private Address address;
}

public class Address {
    @NotBlank private String street;
    @NotBlank private String city;
    @Pattern(regexp = "^[0-9]{6}$") private String pincode;
}

// Controller — @Valid triggers validation
@PostMapping("/users")
public ResponseEntity<User> createUser(@Valid @RequestBody CreateUserRequest request) {
    // If validation fails, MethodArgumentNotValidException is thrown BEFORE this line
    return ResponseEntity.status(HttpStatus.CREATED)
            .body(userService.create(request));
}

// Custom Validator — business rules
@Constraint(validatedBy = UniqueEmailValidator.class)
@Target(ElementType.FIELD)
@Retention(RetentionPolicy.RUNTIME)
public @interface UniqueEmail {
    String message() default "Email already registered";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class UniqueEmailValidator implements ConstraintValidator<UniqueEmail, String> {
    @Autowired private UserRepository userRepo;

    @Override
    public boolean isValid(String email, ConstraintValidatorContext ctx) {
        return email != null && !userRepo.existsByEmail(email);
    }
}

// Validation Groups — different rules for create vs update
public interface OnCreate {}
public interface OnUpdate {}

public class UserRequest {
    @Null(groups = OnCreate.class)    // ID must be null when creating
    @NotNull(groups = OnUpdate.class) // ID required when updating
    private Long id;

    @NotBlank(groups = {OnCreate.class, OnUpdate.class})
    private String name;
}

@PostMapping
public User create(@Validated(OnCreate.class) @RequestBody UserRequest req) { ... }

@PutMapping
public User update(@Validated(OnUpdate.class) @RequestBody UserRequest req) { ... }
```

---

## Q25: RestTemplate vs WebClient vs Feign — Calling External APIs

```java
// 1. RestTemplate — SYNCHRONOUS, BLOCKING (Legacy, still widely used)
@Configuration
public class RestTemplateConfig {
    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder
                .setConnectTimeout(Duration.ofSeconds(3))
                .setReadTimeout(Duration.ofSeconds(5))
                .additionalInterceptors(new LoggingInterceptor())
                .errorHandler(new CustomErrorHandler())
                .build();
    }
}

@Service
public class PaymentServiceClient {
    private final RestTemplate restTemplate;

    public PaymentResponse charge(PaymentRequest request) {
        ResponseEntity<PaymentResponse> response = restTemplate.exchange(
            "http://payment-service/api/charge",
            HttpMethod.POST,
            new HttpEntity<>(request, createHeaders()),
            PaymentResponse.class
        );
        return response.getBody();
    }
}

// 2. WebClient — NON-BLOCKING, REACTIVE (Recommended for new code)
@Configuration
public class WebClientConfig {
    @Bean
    public WebClient paymentWebClient() {
        return WebClient.builder()
                .baseUrl("http://payment-service")
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .filter(ExchangeFilterFunctions.basicAuthentication("user", "pass"))
                .build();
    }
}

@Service
public class PaymentClient {
    public Mono<PaymentResponse> charge(PaymentRequest request) {
        return webClient.post()
                .uri("/api/charge")
                .bodyValue(request)
                .retrieve()
                .bodyToMono(PaymentResponse.class)
                .timeout(Duration.ofSeconds(5))
                .retryWhen(Retry.backoff(3, Duration.ofMillis(500)));
    }

    // Use .block() if you need synchronous result in MVC app
    public PaymentResponse chargeSync(PaymentRequest request) {
        return charge(request).block(); // Blocks calling thread
    }
}

// 3. OpenFeign — DECLARATIVE REST client (Spring Cloud)
@FeignClient(name = "payment-service",
             url = "${payment.service.url}",
             fallback = PaymentFallback.class)
public interface PaymentFeignClient {

    @PostMapping("/api/charge")
    PaymentResponse charge(@RequestBody PaymentRequest request);

    @GetMapping("/api/payments/{id}")
    PaymentResponse getPayment(@PathVariable String id);
}

// Comparison:
// RestTemplate: Simple, blocking, being phased out
// WebClient:    Non-blocking, fluent API, supports streaming, RECOMMENDED
// Feign:        Declarative, Spring Cloud, auto-discovery, circuit breaker
```

---

## Q26: Spring Boot Starters — How they work

### Theory:
A **starter** is a dependency that bundles everything you need for a specific feature. It contains:
1. **Dependencies** — all required libraries
2. **Auto-configuration** — sensible defaults
3. **No code** — just a pom.xml pulling in the right jars

```
spring-boot-starter-web
├── spring-webmvc
├── spring-boot-starter-tomcat (embedded server)
├── spring-boot-starter-json (Jackson)
└── spring-boot-starter-validation (Hibernate Validator)

spring-boot-starter-data-jpa
├── spring-data-jpa
├── hibernate-core
├── spring-boot-starter-jdbc
└── HikariCP (connection pool)

spring-boot-starter-security
├── spring-security-web
├── spring-security-config
└── spring-security-core
```

### Creating a Custom Starter:
```java
// 1. Create auto-configuration module
@AutoConfiguration
@ConditionalOnClass(SmsService.class)
@EnableConfigurationProperties(SmsProperties.class)
public class SmsAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean
    public SmsService smsService(SmsProperties properties) {
        return new TwilioSmsService(properties.getAccountSid(), properties.getAuthToken());
    }
}

// 2. Register in META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
// com.company.sms.SmsAutoConfiguration

// 3. Create starter module (just a pom.xml with dependency on auto-config module)
// Other projects just add: <dependency>company-sms-spring-boot-starter</dependency>
// SmsService is automatically available!
```

---

## Q27: CORS (Cross-Origin Resource Sharing)

```java
// Method-level CORS
@RestController
@CrossOrigin(origins = "http://localhost:3000")
public class ProductController {
    @GetMapping("/products")
    public List<Product> getProducts() { ... }
}

// Global CORS configuration
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins("https://myapp.com", "https://admin.myapp.com")
                .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH")
                .allowedHeaders("Authorization", "Content-Type", "X-Request-Id")
                .exposedHeaders("X-Total-Count", "X-Page-Number")
                .allowCredentials(true)
                .maxAge(3600); // Pre-flight cache (seconds)
    }
}

// CORS with Spring Security (MUST configure both!)
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    return http
        .cors(cors -> cors.configurationSource(corsConfigSource()))
        .csrf(csrf -> csrf.disable())
        .build();
}

@Bean
public CorsConfigurationSource corsConfigSource() {
    CorsConfiguration config = new CorsConfiguration();
    config.setAllowedOrigins(List.of("https://myapp.com"));
    config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
    config.setAllowedHeaders(List.of("*"));
    config.setAllowCredentials(true);

    UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
    source.registerCorsConfiguration("/api/**", config);
    return source;
}
```

---

## Q28: Spring Boot DevTools, Conditional Annotations & Embedded Server

### DevTools:
```properties
# application-dev.properties
spring.devtools.restart.enabled=true
spring.devtools.livereload.enabled=true
# Automatic restart on code change — uses two classloaders
# Base classloader (libraries) stays, restart classloader reloads your code
```

### All @Conditional Annotations:
```java
@ConditionalOnProperty(name = "feature.payments.enabled", havingValue = "true")
@ConditionalOnClass(DataSource.class)        // Class is on classpath
@ConditionalOnMissingClass("com.oracle.OracleDriver") // Class NOT on classpath
@ConditionalOnBean(PaymentGateway.class)     // Bean exists in context
@ConditionalOnMissingBean(CacheManager.class) // Bean does NOT exist
@ConditionalOnWebApplication                  // Running as web app
@ConditionalOnExpression("${feature.enabled} and ${feature.premium}")
@ConditionalOnJava(JavaVersion.SEVENTEEN)     // Specific Java version
@ConditionalOnResource(resources = "classpath:schema.sql")
```

### Embedded Server Configuration:
```properties
# Switch from Tomcat to Undertow or Jetty:
# Exclude Tomcat, add Undertow
# spring-boot-starter-web → exclude spring-boot-starter-tomcat
# Add: spring-boot-starter-undertow

server.port=8080
server.servlet.context-path=/api
server.tomcat.max-threads=200
server.tomcat.accept-count=100
server.tomcat.max-connections=10000
server.compression.enabled=true
server.compression.min-response-size=1024
```

---

## Q29: Spring Boot Internationalization (i18n) & Content Negotiation

```java
// i18n — Multi-language support
// messages.properties (default)
// greeting=Hello, {0}!
// messages_hi.properties
// greeting=नमस्ते, {0}!

@Configuration
public class I18nConfig implements WebMvcConfigurer {
    @Bean
    public LocaleResolver localeResolver() {
        AcceptHeaderLocaleResolver resolver = new AcceptHeaderLocaleResolver();
        resolver.setDefaultLocale(Locale.ENGLISH);
        return resolver;
    }

    @Bean
    public MessageSource messageSource() {
        ResourceBundleMessageSource source = new ResourceBundleMessageSource();
        source.setBasename("messages");
        source.setDefaultEncoding("UTF-8");
        return source;
    }
}

@RestController
public class GreetingController {
    @Autowired private MessageSource messageSource;

    @GetMapping("/greet")
    public String greet(@RequestHeader(value = "Accept-Language", defaultValue = "en") String lang) {
        return messageSource.getMessage("greeting", new Object[]{"Yogesh"},
                Locale.forLanguageTag(lang));
    }
}

// Content Negotiation — JSON + XML from same endpoint
// Add jackson-dataformat-xml dependency
@GetMapping(value = "/products/{id}",
            produces = {MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
public Product getProduct(@PathVariable Long id) {
    return productService.findById(id);
    // Client sends Accept: application/json → JSON response
    // Client sends Accept: application/xml → XML response
}
```

---

## Q30: Spring Boot Logging & MDC

```java
// application.yml
// logging:
//   level:
//     root: INFO
//     com.company.payment: DEBUG
//     org.springframework.web: WARN
//   pattern:
//     console: "%d{HH:mm:ss.SSS} [%thread] [%X{requestId}] %-5level %logger{36} - %msg%n"
//   file:
//     name: logs/application.log
//     max-size: 100MB
//     max-history: 30

// Structured Logging with MDC (Mapped Diagnostic Context)
@Component
public class MDCFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws IOException, ServletException {
        try {
            MDC.put("requestId", UUID.randomUUID().toString());
            MDC.put("userId", extractUserId(req));
            MDC.put("clientIp", req.getRemoteAddr());
            chain.doFilter(req, res);
        } finally {
            MDC.clear(); // CRITICAL: prevent memory leak in thread pool
        }
    }
}

// Now ALL log statements automatically include requestId, userId, clientIp
@Service @Slf4j
public class PaymentService {
    public void process(Payment p) {
        log.info("Processing payment: {}", p.getId());
        // Output: 10:30:45.123 [http-8080-1] [req-abc-123] INFO PaymentService - Processing payment: PAY-001
    }
}
```

---

## Q31: Spring Boot Actuator Deep Dive — Custom Endpoints

```java
// Custom actuator endpoint
@Component
@Endpoint(id = "app-info")
public class AppInfoEndpoint {

    @ReadOperation // GET /actuator/app-info
    public Map<String, Object> info() {
        return Map.of(
            "version", "2.5.0",
            "uptime", ManagementFactory.getRuntimeMXBean().getUptime(),
            "activeProfiles", Arrays.asList(env.getActiveProfiles()),
            "javaVersion", System.getProperty("java.version"),
            "totalMemory", Runtime.getRuntime().totalMemory(),
            "freeMemory", Runtime.getRuntime().freeMemory()
        );
    }

    @WriteOperation // POST /actuator/app-info
    public String setLogLevel(@Selector String logger, String level) {
        LoggerContext ctx = (LoggerContext) LoggerFactory.getILoggerFactory();
        ctx.getLogger(logger).setLevel(Level.valueOf(level));
        return "Log level set to " + level;
    }
}

// Prometheus metrics for Grafana dashboards
// Dependency: micrometer-registry-prometheus
// Exposes /actuator/prometheus with all metrics in Prometheus format
// Custom business metric:
@Service
public class OrderMetrics {
    private final MeterRegistry registry;

    public void orderPlaced(Order order) {
        registry.counter("orders.placed",
            "type", order.getType().name(),
            "region", order.getRegion()
        ).increment();

        registry.timer("order.processing.time").record(Duration.ofMillis(order.getProcessingMs()));
    }
}
```

---

## 🎯 Spring Framework Cross-Questioning Scenarios

### Q: "How does Spring handle thread safety for singleton beans?"
> **Answer:** "Spring does NOT make singletons thread-safe automatically. Since singleton beans are shared across all threads, you must ensure thread safety yourself. Rules: (1) Don't use mutable instance variables for request-specific data. (2) Use local variables inside methods (stack-confined = thread-safe). (3) For shared mutable state, use `ConcurrentHashMap`, `AtomicInteger`, or `synchronized`. (4) For request-scoped data, use `@Scope(SCOPE_REQUEST)` or `ThreadLocal`. In practice, most service beans are stateless (no mutable fields), which is inherently thread-safe."

### Q: "What is the difference between @Component, @Service, @Repository, @Controller?"
> **Answer:** "Functionally they're identical — all register the class as a Spring bean via component scanning. The difference is **semantic**: `@Component` is generic, `@Service` marks business logic, `@Repository` marks data access (adds automatic exception translation — converts JDBC exceptions to Spring's `DataAccessException`), `@Controller` marks web handlers. Using the right stereotype makes code self-documenting and enables layer-specific features."

### Q: "How does Spring Boot decide which auto-configurations to apply?"
> **Answer:** "`@SpringBootApplication` includes `@EnableAutoConfiguration`. At startup, Spring reads `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` listing ~150 auto-configuration classes. Each class has `@ConditionalOn*` annotations — `@ConditionalOnClass` checks if a library is on the classpath, `@ConditionalOnMissingBean` ensures your custom bean takes priority. To debug: set `debug=true` in application.properties — you'll see a conditions evaluation report showing every auto-config that was applied or skipped."

### Q: "Explain the N+1 query problem and how to solve it"
> **Answer:** "When loading a parent entity with `@OneToMany`, JPA runs 1 query for parents + N queries for each parent's children = N+1 queries. Example: loading 100 orders, each with items = 101 queries! Solutions: (1) `JOIN FETCH` in JPQL: `SELECT o FROM Order o JOIN FETCH o.items`. (2) `@EntityGraph(attributePaths = 'items')` on repository method. (3) `@BatchSize(size = 50)` on the collection — loads children in batches. (4) `FetchType.LAZY` + `Hibernate.initialize()` when needed. In production I use `@EntityGraph` or projections."

### Q: "What happens when Spring Boot starts? Describe the startup sequence."
> **Answer:** "1. `main()` calls `SpringApplication.run()`. 2. Determines app type (Servlet, Reactive, None). 3. Loads `SpringApplicationRunListeners`. 4. Prepares `Environment` (reads properties, profiles). 5. Creates `ApplicationContext` (AnnotationConfig for web). 6. Loads bean definitions via component scan + auto-configuration. 7. Refreshes context — instantiates all singleton beans, dependency injection. 8. Calls `CommandLineRunner` and `ApplicationRunner` beans. 9. Starts embedded server (Tomcat). 10. Publishes `ApplicationReadyEvent`. The whole process takes ~2-5 seconds for a typical app."

---

## 📘 Additional Spring Topics (from DigitalOcean Interview Guide)

---

## Q32: Spring Bean Autowiring Types

```java
// Autowiring = automatic dependency injection by Spring

// 1. @Autowired by TYPE (default)
@Service
public class OrderService {
    @Autowired  // Injects bean by matching TYPE
    private PaymentGateway gateway; // Finds a bean of type PaymentGateway
}

// 2. @Qualifier — resolve ambiguity when multiple beans of same type
@Service
public class OrderService {
    @Autowired
    @Qualifier("stripeGateway") // Injects specific bean by NAME
    private PaymentGateway gateway;
}

// 3. @Primary — default bean when multiple candidates exist
@Configuration
public class GatewayConfig {
    @Bean @Primary  // This is the default PaymentGateway
    public PaymentGateway stripeGateway() { return new StripeGateway(); }

    @Bean
    public PaymentGateway paypalGateway() { return new PaypalGateway(); }
}

// 4. Constructor injection (RECOMMENDED — immutable, testable)
@Service
public class OrderService {
    private final PaymentGateway gateway;
    private final OrderRepository orderRepo;

    // @Autowired not needed if single constructor (Spring 4.3+)
    public OrderService(PaymentGateway gateway, OrderRepository orderRepo) {
        this.gateway = gateway;
        this.orderRepo = orderRepo;
    }
}

// 5. Setter injection
@Service
public class OrderService {
    private PaymentGateway gateway;

    @Autowired
    public void setGateway(PaymentGateway gateway) {
        this.gateway = gateway;
    }
}

// BEST PRACTICE: Always use CONSTRUCTOR injection
// WHY: Makes dependencies explicit, supports immutability (final fields),
//      easier to unit test (just pass mocks in constructor)
```

---

## Q33: Design Patterns Used in Spring Framework

```
1. Singleton Pattern:
   - Spring beans are singleton by default (one instance per IoC container)
   - Different from GoF singleton (per JVM) — Spring singleton is per context

2. Factory Pattern:
   - BeanFactory / ApplicationContext acts as a factory
   - Creates and manages bean instances

3. Proxy Pattern:
   - @Transactional, @Cacheable, @Async all use dynamic proxies
   - JDK proxy (interface-based) or CGLIB proxy (subclass-based)

4. Template Method Pattern:
   - JdbcTemplate, RestTemplate, JmsTemplate
   - Defines skeleton, subclass/callback fills in specifics

5. Observer Pattern:
   - ApplicationEvent / ApplicationListener
   - @EventListener for decoupled event publishing

6. Strategy Pattern:
   - Spring Security AuthenticationProvider implementations
   - Multiple implementations behind an interface, selected at runtime

7. Front Controller Pattern:
   - DispatcherServlet handles ALL incoming requests
   - Routes to appropriate @Controller

8. Dependency Injection (IoC):
   - The foundation of entire Spring Framework
   - Objects don't create dependencies — container injects them

9. Adapter Pattern:
   - HandlerAdapter adapts different handler types to DispatcherServlet
   - Spring MVC supports @Controller, HttpRequestHandler, SimpleController

10. Decorator Pattern:
    - ServerHttpRequestDecorator in WebFlux
    - ContentCachingRequestWrapper in Servlet API
```

---

## Q34: Spring JdbcTemplate & Spring DAO

```java
// Spring DAO (Data Access Object) pattern — abstracts data access layer
// JdbcTemplate eliminates boilerplate JDBC code (connection, statement, close)

@Repository
public class EmployeeDao {
    private final JdbcTemplate jdbcTemplate;

    public EmployeeDao(JdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    // Query for single value
    public int getEmployeeCount() {
        return jdbcTemplate.queryForObject(
            "SELECT COUNT(*) FROM employees", Integer.class);
    }

    // Query for single object
    public Employee findById(Long id) {
        return jdbcTemplate.queryForObject(
            "SELECT * FROM employees WHERE id = ?",
            (rs, rowNum) -> new Employee(
                rs.getLong("id"),
                rs.getString("name"),
                rs.getString("email"),
                rs.getBigDecimal("salary")
            ), id);
    }

    // Query for list
    public List<Employee> findAll() {
        return jdbcTemplate.query(
            "SELECT * FROM employees ORDER BY name",
            (rs, rowNum) -> new Employee(
                rs.getLong("id"),
                rs.getString("name"),
                rs.getString("email"),
                rs.getBigDecimal("salary")
            ));
    }

    // Insert / Update / Delete
    public int save(Employee emp) {
        return jdbcTemplate.update(
            "INSERT INTO employees (name, email, salary) VALUES (?, ?, ?)",
            emp.getName(), emp.getEmail(), emp.getSalary());
    }

    // Batch operations
    public int[] batchInsert(List<Employee> employees) {
        return jdbcTemplate.batchUpdate(
            "INSERT INTO employees (name, email) VALUES (?, ?)",
            new BatchPreparedStatementSetter() {
                @Override
                public void setValues(PreparedStatement ps, int i) throws SQLException {
                    ps.setString(1, employees.get(i).getName());
                    ps.setString(2, employees.get(i).getEmail());
                }
                @Override
                public int getBatchSize() { return employees.size(); }
            });
    }
}

// NamedParameterJdbcTemplate — more readable
@Repository
public class OrderDao {
    private final NamedParameterJdbcTemplate namedJdbc;

    public List<Order> findByStatus(String status) {
        MapSqlParameterSource params = new MapSqlParameterSource()
            .addValue("status", status);
        return namedJdbc.query(
            "SELECT * FROM orders WHERE status = :status", params, orderRowMapper);
    }
}

// JdbcTemplate vs JPA:
// JdbcTemplate: Full SQL control, better for complex queries, no entity mapping overhead
// JPA: ORM, less SQL, better for CRUD, lazy loading, caching
// Use JdbcTemplate for: reporting queries, stored procedures, legacy DB schemas
// Use JPA for: standard CRUD operations, domain-driven design
```

---

## Q35: File Upload with MultipartResolver

```java
// Spring Boot auto-configures MultipartResolver
// application.properties:
// spring.servlet.multipart.max-file-size=10MB
// spring.servlet.multipart.max-request-size=50MB
// spring.servlet.multipart.enabled=true

@RestController
@RequestMapping("/api/files")
public class FileUploadController {

    @Value("${upload.dir:/tmp/uploads}")
    private String uploadDir;

    // Single file upload
    @PostMapping("/upload")
    public ResponseEntity<Map<String, String>> uploadFile(
            @RequestParam("file") MultipartFile file) {

        if (file.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("error", "File is empty"));
        }

        // Validate file type
        String contentType = file.getContentType();
        if (!List.of("image/jpeg", "image/png", "application/pdf").contains(contentType)) {
            return ResponseEntity.badRequest().body(Map.of("error", "Invalid file type"));
        }

        try {
            // Sanitize filename (prevent path traversal attack!)
            String fileName = UUID.randomUUID() + "_" +
                StringUtils.cleanPath(file.getOriginalFilename());
            Path targetPath = Paths.get(uploadDir).resolve(fileName);
            Files.copy(file.getInputStream(), targetPath, StandardCopyOption.REPLACE_EXISTING);

            return ResponseEntity.ok(Map.of(
                "fileName", fileName,
                "size", String.valueOf(file.getSize()),
                "url", "/api/files/" + fileName
            ));
        } catch (IOException e) {
            throw new FileStorageException("Failed to store file", e);
        }
    }

    // Multiple file upload
    @PostMapping("/upload-multiple")
    public ResponseEntity<List<String>> uploadMultiple(
            @RequestParam("files") MultipartFile[] files) {
        List<String> fileNames = Arrays.stream(files)
            .map(file -> saveFile(file))
            .collect(Collectors.toList());
        return ResponseEntity.ok(fileNames);
    }

    // File download
    @GetMapping("/{fileName}")
    public ResponseEntity<Resource> downloadFile(@PathVariable String fileName) {
        Path filePath = Paths.get(uploadDir).resolve(fileName).normalize();
        Resource resource = new UrlResource(filePath.toUri());

        return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_OCTET_STREAM)
            .header(HttpHeaders.CONTENT_DISPOSITION,
                    "attachment; filename=\"" + resource.getFilename() + "\"")
            .body(resource);
    }
}
```

---

## Q36: ContextLoaderListener & Application Context Hierarchy

```
Spring MVC has TWO application contexts:

1. Root ApplicationContext (created by ContextLoaderListener)
   ├── @Service beans
   ├── @Repository beans
   ├── DataSource, TransactionManager
   └── Shared across all DispatcherServlets

2. Servlet ApplicationContext (created by DispatcherServlet)
   ├── @Controller beans
   ├── ViewResolver
   ├── HandlerMapping
   └── Specific to one DispatcherServlet

Context Hierarchy:
┌──────────────────────────────────┐
│   Root Context (ContextLoader)   │
│   Services, Repos, DataSource    │
│                                  │
│  ┌───────────────┐ ┌──────────┐ │
│  │ Servlet Ctx 1 │ │ Ctx 2    │ │
│  │ Controllers   │ │ API Ctrl │ │
│  └───────────────┘ └──────────┘ │
└──────────────────────────────────┘

NOTE: In Spring Boot, there's typically ONE unified ApplicationContext.
The context hierarchy concept is mainly relevant for traditional
Spring MVC (war deployment) applications.
```

---

## Q37: Spring Boot 3 — Key Features & Migration

```
Spring Boot 3 Major Changes:

1. JAVA 17+ REQUIRED (minimum baseline)
   - Records, sealed classes, pattern matching available

2. JAKARTA EE (javax → jakarta namespace)
   - javax.servlet → jakarta.servlet
   - javax.persistence → jakarta.persistence
   - javax.validation → jakarta.validation
   # BIGGEST migration effort — global find & replace

3. SPRING FRAMEWORK 6 underneath
   - Native support for GraalVM native images
   - Virtual Threads (Java 21) support: spring.threads.virtual.enabled=true

4. OBSERVABILITY (built-in)
   - Micrometer Observation API (unified metrics + tracing)
   - Auto-instrumented with Zipkin, Jaeger
   - observation.auto-configure=true

5. HTTP Interface Clients (replaces Feign for simple cases)
   @HttpExchange("/api/users")
   interface UserClient {
       @GetExchange("/{id}")
       User getUser(@PathVariable Long id);

       @PostExchange
       User createUser(@RequestBody User user);
   }

6. Problem Details (RFC 7807) — standardized error responses
   - ProblemDetail class built into Spring 6
   - Returns structured JSON errors: type, title, status, detail, instance

7. AOT (Ahead-of-Time) Processing
   - Pre-computes bean definitions at build time
   - Faster startup for cloud/serverless deployments
```

---

## Q38: HTTPS/SSL Configuration in Spring Boot

```properties
# application.properties
server.port=8443
server.ssl.enabled=true
server.ssl.key-store=classpath:keystore.p12
server.ssl.key-store-password=changeit
server.ssl.key-store-type=PKCS12
server.ssl.key-alias=myapp

# Generate self-signed certificate (for development):
# keytool -genkeypair -alias myapp -keyalg RSA -keysize 2048
#         -storetype PKCS12 -keystore keystore.p12 -validity 365
```

```java
// Redirect HTTP → HTTPS
@Configuration
public class HttpsRedirectConfig {

    @Bean
    public ServletWebServerFactory servletContainer() {
        TomcatServletWebServerFactory tomcat = new TomcatServletWebServerFactory() {
            @Override
            protected void postProcessContext(Context context) {
                SecurityConstraint secConstraint = new SecurityConstraint();
                secConstraint.setUserConstraint("CONFIDENTIAL");
                SecurityCollection collection = new SecurityCollection();
                collection.addPattern("/*");
                secConstraint.addCollection(collection);
                context.addConstraint(secConstraint);
            }
        };
        tomcat.addAdditionalTomcatConnectors(httpConnector());
        return tomcat;
    }

    private Connector httpConnector() {
        Connector connector = new Connector(TomcatServletWebServerFactory.DEFAULT_PROTOCOL);
        connector.setScheme("http");
        connector.setPort(8080);
        connector.setSecure(false);
        connector.setRedirectPort(8443);
        return connector;
    }
}

// In production: Use a reverse proxy (Nginx/AWS ALB) for SSL termination
// instead of configuring SSL directly in Spring Boot
// The proxy handles certificates; Spring Boot runs plain HTTP behind it
```
