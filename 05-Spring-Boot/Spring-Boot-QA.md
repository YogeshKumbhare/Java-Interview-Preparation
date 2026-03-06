# 🍃 Spring Boot — Deep Dive Interview Q&A
## Target: 12+ Years Experience

---

## Q1: How does Spring Boot Auto-configuration work internally?

### Answer — @EnableAutoConfiguration internals

```
1. @SpringBootApplication includes @EnableAutoConfiguration
2. SpringFactoriesLoader reads META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
3. Lists ~150 AutoConfiguration classes (DataSourceAutoConfiguration, etc.)
4. Each class annotated with @ConditionalOn* → loaded only if condition is true
```

```java
// How DataSourceAutoConfiguration decides to auto-configure:
@AutoConfiguration
@ConditionalOnClass({ DataSource.class, EmbeddedDatabaseType.class })
@ConditionalOnMissingBean(type = "io.r2dbc.spi.ConnectionFactory")
@EnableConfigurationProperties(DataSourceProperties.class)
@Import({ DataSourcePoolMetadataProvidersConfiguration.class,
         DataSourceCheckpointRestoreConfiguration.class })
public class DataSourceAutoConfiguration {

    @ConditionalOnMissingBean(DataSource.class)  // Only if NO DataSource bean exists
    @ConditionalOnSingleCandidate(EmbeddedDatabase.class)
    static class EmbeddedDatabaseConfiguration { /* ... */ }
}
```

### Custom Auto-configuration:
```java
// Your library auto-configures when on classpath
@AutoConfiguration
@ConditionalOnClass(PaymentGateway.class)
@ConditionalOnMissingBean(PaymentGateway.class)
@EnableConfigurationProperties(PaymentProperties.class)
public class PaymentAutoConfiguration {

    @Bean
    public PaymentGateway paymentGateway(PaymentProperties props) {
        return new PaymentGateway(props.getApiKey(), props.getBaseUrl());
    }
}
```

---

## Q2: Explain @Transactional propagation with real scenarios

### All Propagation Types with Examples:

```java
@Service
public class OrderFulfillmentService {

    @Autowired
    private OrderService orderService;

    @Autowired
    private NotificationService notificationService;

    // REQUIRES_NEW — Audit log must always be saved, even if main tx fails
    @Transactional(propagation = Propagation.REQUIRED) // Main transaction
    public void processOrder(Order order) {
        orderService.save(order);
        auditService.log(order); // Uses REQUIRES_NEW — its own tx
        paymentService.charge(order); // If this fails...
        // orderService.save is rolled back
        // BUT auditService.log is NOT rolled back (own committed tx)
    }
}

@Service
public class AuditService {
    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void log(Order order) {
        // New transaction, suspends outer
        auditRepo.save(new AuditLog(order));
        // Commits independently
    }
}
```

### Propagation Matrix:

| Propagation | Outer TX Exists | Outer TX Absent |
|-------------|----------------|----------------|
| `REQUIRED` | Use existing | Create new |
| `REQUIRES_NEW` | Suspend, create new | Create new |
| `NESTED` | Create savepoint | Create new |
| `SUPPORTS` | Use existing | No TX |
| `NOT_SUPPORTED` | Suspend, run without TX | Run without TX |
| `MANDATORY` | Use existing | Throw exception |
| `NEVER` | Throw exception | Run without TX |

---

## Q3: What is Spring AOP? How is it implemented?

### AOP Proxy Types:
```
1. JDK Dynamic Proxy — Interface-based. Fast. Default when bean implements interface.
2. CGLIB Proxy — Subclass-based. Used when no interface. Creates runtime subclass.

Spring Boot default: CGLIB (proxyTargetClass=true)
```

```java
// Custom AOP Aspect — real-world: method execution time logging
@Aspect
@Component
@Slf4j
public class PerformanceMonitoringAspect {

    // Pointcut expressions
    @Pointcut("execution(* com.company.payment.service.*.*(..))")
    public void paymentServiceMethods() {}

    @Pointcut("@annotation(com.company.annotation.Monitored)")
    public void monitoredMethods() {}

    @Around("paymentServiceMethods() || monitoredMethods()")
    public Object measureExecutionTime(ProceedingJoinPoint pjp) throws Throwable {
        String method = pjp.getSignature().toShortString();
        StopWatch sw = new StopWatch();
        sw.start();
        try {
            Object result = pjp.proceed();
            sw.stop();
            log.info("[PERF] {} executed in {}ms", method, sw.getTotalTimeMillis());
            if (sw.getTotalTimeMillis() > 500) {
                log.warn("[SLOW] {} took {}ms — investigate!", method, sw.getTotalTimeMillis());
            }
            return result;
        } catch (Exception ex) {
            sw.stop();
            log.error("[PERF-ERROR] {} failed after {}ms", method, sw.getTotalTimeMillis());
            throw ex;
        }
    }

    // @Before, @After, @AfterReturning, @AfterThrowing
    @AfterThrowing(pointcut = "paymentServiceMethods()", throwing = "ex")
    public void logException(JoinPoint jp, Exception ex) {
        log.error("Exception in {}: {}", jp.getSignature(), ex.getMessage());
        // Send alert
    }
}
```

### AOP Pointcut expressions:
```java
// All public methods in service layer
execution(public * com.company.*.service.*.*(..))

// Methods that return List
execution(java.util.List com.company..*(..))

// Methods with specific annotation
@annotation(org.springframework.transaction.annotation.Transactional)

// Within a specific package (all methods)
within(com.company.payment..*)

// Methods with specific argument type
args(java.lang.String, ..)

// Bean-based pointcut
bean(paymentService)
```

---

## Q4: Spring Boot Actuator — Production Monitoring

```properties
# application.properties
management.endpoints.web.exposure.include=health,info,metrics,prometheus,env,loggers
management.endpoint.health.show-details=always
management.health.db.enabled=true
management.health.redis.enabled=true
```

### Custom Health Indicator:
```java
@Component
public class PaymentGatewayHealthIndicator implements HealthIndicator {

    private final PaymentGatewayClient client;

    @Override
    public Health health() {
        try {
            long start = System.currentTimeMillis();
            GatewayStatus status = client.ping();
            long responseTime = System.currentTimeMillis() - start;

            if (status.isUp()) {
                return Health.up()
                    .withDetail("responseTime", responseTime + "ms")
                    .withDetail("version", status.getVersion())
                    .build();
            }
            return Health.down().withDetail("reason", "Gateway reports DOWN").build();
        } catch (Exception ex) {
            return Health.down(ex)
                .withDetail("error", ex.getMessage())
                .build();
        }
    }
}
```

### Custom Metrics with Micrometer:
```java
@Service
public class PaymentMetricsService {

    private final Counter paymentSuccessCounter;
    private final Counter paymentFailureCounter;
    private final Timer paymentTimer;
    private final Gauge pendingPaymentsGauge;

    public PaymentMetricsService(MeterRegistry registry) {
        this.paymentSuccessCounter = registry.counter("payment.success", "type", "credit");
        this.paymentFailureCounter = registry.counter("payment.failure");
        this.paymentTimer = registry.timer("payment.processing.time");
        // Gauge reports current value dynamically
        this.pendingPaymentsGauge = Gauge
            .builder("payment.pending.count", this, obj -> obj.getPendingCount())
            .register(registry);
    }

    public PaymentResult process(Payment payment) {
        return paymentTimer.recordCallable(() -> {
            try {
                PaymentResult result = gateway.process(payment);
                paymentSuccessCounter.increment();
                return result;
            } catch (Exception ex) {
                paymentFailureCounter.increment();
                throw ex;
            }
        });
    }
}
```

---

## Q5: Spring Security — JWT Authentication Flow

```java
// 1. Security Configuration
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .requestMatchers(HttpMethod.GET, "/api/products/**").hasAnyRole("USER", "ADMIN")
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .build();
    }

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder(12); // Cost factor 12
    }
}

// 2. JWT Filter
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest req,
                                    HttpServletResponse res,
                                    FilterChain chain) throws IOException, ServletException {
        String authHeader = req.getHeader("Authorization");

        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            chain.doFilter(req, res);
            return;
        }

        String token = authHeader.substring(7);

        try {
            Claims claims = jwtService.validateAndExtractClaims(token);
            String username = claims.getSubject();

            if (username != null && SecurityContextHolder.getContext().getAuthentication() == null) {
                UserDetails userDetails = userDetailsService.loadUserByUsername(username);
                UsernamePasswordAuthenticationToken authToken =
                    new UsernamePasswordAuthenticationToken(
                        userDetails, null, userDetails.getAuthorities());
                authToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(req));
                SecurityContextHolder.getContext().setAuthentication(authToken);
            }
        } catch (JwtException ex) {
            res.sendError(HttpServletResponse.SC_UNAUTHORIZED, "Invalid token");
            return;
        }

        chain.doFilter(req, res);
    }
}
```

---

## Q6: @Cacheable, @CachePut, @CacheEvict — Spring Caching

> **💡 Note:** For a comprehensive deep dive into caching concepts, types, strategies, and anomalies, refer to the [Caching Strategies Module](../26-Caching-Strategies/Caching-QA.md).

```java
@Service
public class ProductService {

    // Caches result, uses product ID as key
    @Cacheable(value = "products", key = "#id",
               condition = "#id > 0",
               unless = "#result == null")
    public Product getProduct(Long id) {
        log.info("Fetching from DB: {}", id); // Only logged on cache MISS
        return productRepo.findById(id).orElse(null);
    }

    // Always executes, updates cache with result
    @CachePut(value = "products", key = "#product.id")
    public Product updateProduct(Product product) {
        return productRepo.save(product);
    }

    // Removes from cache after method executes
    @CacheEvict(value = "products", key = "#id")
    public void deleteProduct(Long id) {
        productRepo.deleteById(id);
    }

    // Clear entire cache
    @CacheEvict(value = "products", allEntries = true)
    @Scheduled(fixedDelay = 3600000) // Every hour
    public void clearProductCache() {
        log.info("Product cache cleared");
    }
}
```

### Redis Cache Config:
```java
@Configuration
public class RedisConfig {

    @Bean
    public RedisCacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(30))          // TTL
            .serializeKeysWith(                         // Key serializer
                RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(                       // Value serializer
                RedisSerializationContext.SerializationPair.fromSerializer(
                    new GenericJackson2JsonRedisSerializer()))
            .disableCachingNullValues();                // Don't cache nulls

        Map<String, RedisCacheConfiguration> cacheConfigs = new HashMap<>();
        cacheConfigs.put("products", config.entryTtl(Duration.ofHours(1)));
        cacheConfigs.put("users", config.entryTtl(Duration.ofMinutes(10)));

        return RedisCacheManager.builder(factory)
            .cacheDefaults(config)
            .withInitialCacheConfigurations(cacheConfigs)
            .build();
    }
}
```

---

## Q7: Spring Boot Configuration — @ConfigurationProperties vs @Value

```java
// @Value — single property
@Value("${app.payment.gateway-url}")
private String gatewayUrl;

// @Value with default
@Value("${app.timeout:5000}")
private int timeout;

// @ConfigurationProperties — grouped config (PREFERRED for multiple props)
@Configuration
@ConfigurationProperties(prefix = "app.payment")
@Validated
public class PaymentProperties {
    @NotNull
    private String gatewayUrl;

    @Positive
    private int timeout = 5000;

    @Size(min = 32)
    private String apiKey;

    // Nested config
    private Retry retry = new Retry();

    @Data
    public static class Retry {
        private int maxAttempts = 3;
        private Duration backoff = Duration.ofSeconds(1);
    }
}

// application.yml
// app:
//   payment:
//     gateway-url: https://payment.example.com
//     timeout: 3000
//     api-key: abc123...
//     retry:
//       max-attempts: 5
//       backoff: 2s
```

---

## Q8: Spring Boot Testing — Full Stack

```java
// Unit Test
@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {
    @Mock
    private PaymentRepository paymentRepo;

    @Mock
    private KafkaTemplate<String, PaymentEvent> kafkaTemplate;

    @InjectMocks
    private PaymentService paymentService;

    @Test
    void processPayment_ShouldSaveAndPublish() {
        Payment payment = new Payment("TX001", BigDecimal.TEN);
        when(paymentRepo.save(any())).thenReturn(payment);

        PaymentResult result = paymentService.process(payment);

        assertThat(result.getStatus()).isEqualTo("SUCCESS");
        verify(paymentRepo).save(payment);
        verify(kafkaTemplate).send(eq("payment-events"), any());
    }
}

// Integration Test
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@TestPropertySource(locations = "classpath:application-test.properties")
class PaymentControllerIntegrationTest {

    @Autowired
    private TestRestTemplate restTemplate;

    @MockBean
    private PaymentGatewayClient gatewayClient;

    @Test
    void createPayment_Returns201() {
        when(gatewayClient.charge(any())).thenReturn(new GatewayResponse("TX99", "SUCCESS"));

        PaymentRequest request = new PaymentRequest(BigDecimal.valueOf(100), "USD");
        ResponseEntity<PaymentResponse> response =
            restTemplate.postForEntity("/api/payments", request, PaymentResponse.class);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody().getTransactionId()).isEqualTo("TX99");
    }
}

// WebMvcTest — Controller layer only
@WebMvcTest(PaymentController.class)
class PaymentControllerTest {
    @Autowired
    private MockMvc mockMvc;

    @MockBean
    private PaymentService paymentService;

    @Test
    void getPayment_NotFound_Returns404() throws Exception {
        when(paymentService.findById("TX999")).thenThrow(new PaymentNotFoundException("TX999"));

        mockMvc.perform(get("/api/payments/TX999"))
            .andExpect(status().isNotFound())
            .andExpect(jsonPath("$.errorCode").value("PAYMENT_NOT_FOUND"));
    }
}
```

---

## Q9: What is ApplicationContext? BeanFactory vs ApplicationContext

### Theory:
**ApplicationContext** is the **central IoC (Inversion of Control) container** in Spring. It's responsible for:
1. **Creating** beans (objects)
2. **Configuring** beans (injecting dependencies)
3. **Managing** bean lifecycle (init → use → destroy)
4. **Providing** enterprise features (events, i18n, AOP, resource loading)

### BeanFactory vs ApplicationContext:

```
                    BeanFactory (interface)
                         │
                         ▼
                  ApplicationContext (interface)
                    /          \
      AnnotationConfigApplicationContext    WebApplicationContext
      ClassPathXmlApplicationContext        ServletWebServerApplicationContext
```

| Feature | BeanFactory | ApplicationContext |
|---------|------------|-------------------|
| Bean instantiation | **Lazy** (on first request) | **Eager** (at startup) |
| Event publishing | ❌ No | ✅ Yes (`ApplicationEventPublisher`) |
| Internationalization (i18n) | ❌ No | ✅ Yes (`MessageSource`) |
| AOP support | ❌ No | ✅ Yes (auto-proxy creation) |
| Environment/Profiles | ❌ No | ✅ Yes (`@Profile`, `Environment`) |
| Annotation processing | ❌ No | ✅ Yes (`@Autowired`, `@Value`) |
| Use case | Lightweight/embedded | **Always use this** in Spring Boot |

```java
// Spring Boot creates ApplicationContext automatically via SpringApplication.run()
@SpringBootApplication
public class MyApp {
    public static void main(String[] args) {
        // Returns ConfigurableApplicationContext
        ApplicationContext ctx = SpringApplication.run(MyApp.class, args);

        // Get bean by type
        PaymentService service = ctx.getBean(PaymentService.class);

        // Get bean by name
        PaymentService service2 = (PaymentService) ctx.getBean("paymentService");

        // Check if bean exists
        boolean exists = ctx.containsBean("paymentService"); // true

        // Get all bean names of a type
        String[] names = ctx.getBeanNamesForType(PaymentService.class);

        // Get environment properties
        String port = ctx.getEnvironment().getProperty("server.port");

        // Get total bean count
        int count = ctx.getBeanDefinitionCount(); // typically 200+ in Spring Boot
    }
}
```

---

## Q10: Spring Bean Lifecycle — From Creation to Destruction

### Theory:
When Spring creates a bean, it goes through a well-defined lifecycle. Understanding this is critical for resource management (DB connections, thread pools, caches).

```
  Bean Lifecycle (Full Sequence):
  ┌─────────────────────────────────────────────────────┐
  │ 1. Instantiation (constructor called)               │
  │ 2. Populate Properties (DI — @Autowired injected)   │
  │ 3. BeanNameAware.setBeanName()                      │
  │ 4. BeanFactoryAware.setBeanFactory()                │
  │ 5. ApplicationContextAware.setApplicationContext()  │
  │ 6. BeanPostProcessor.postProcessBeforeInit()        │
  │ 7. @PostConstruct / InitializingBean.afterPropertiesSet() │
  │ 8. Custom init-method                               │
  │ 9. BeanPostProcessor.postProcessAfterInit()         │
  │    ─── BEAN IS READY FOR USE ───                    │
  │ 10. @PreDestroy / DisposableBean.destroy()          │
  │ 11. Custom destroy-method                           │
  └─────────────────────────────────────────────────────┘
```

```java
@Component
public class PaymentGatewayClient implements InitializingBean, DisposableBean,
        ApplicationContextAware {

    private HttpClient httpClient;
    private ApplicationContext applicationContext;

    // Step 5: ApplicationContextAware — get reference to context
    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        this.applicationContext = ctx;
        // Useful for: programmatically getting other beans, environment props
    }

    // Step 7a: @PostConstruct — called AFTER all dependencies injected
    @PostConstruct
    public void init() {
        // Initialize HTTP client, open connections, warm up cache
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();
        log.info("PaymentGatewayClient initialized with HTTP client");
    }

    // Step 7b: InitializingBean — alternative to @PostConstruct
    @Override
    public void afterPropertiesSet() {
        // Validate required configuration
        Objects.requireNonNull(apiKey, "Payment API key must be configured");
    }

    // Step 10a: @PreDestroy — cleanup before bean is removed
    @PreDestroy
    public void cleanup() {
        log.info("Shutting down PaymentGatewayClient...");
        // Close connections, flush buffers, release resources
    }

    // Step 10b: DisposableBean — alternative to @PreDestroy
    @Override
    public void destroy() {
        httpClient.close();
    }
}

// BEST PRACTICE: Use @PostConstruct and @PreDestroy (cleaner than interfaces)
```

---

## Q11: Bean Scopes in Spring

### Theory:
**Bean scope** determines how many instances of a bean Spring creates and how long they live.

| Scope | Instances | Lifetime | Use Case |
|-------|-----------|----------|----------|
| **singleton** (default) | One per ApplicationContext | Entire app lifecycle | Services, Repos, Config |
| **prototype** | New instance per request | Until garbage collected | Stateful objects, builders |
| **request** | One per HTTP request | Single HTTP request | Request-scoped data |
| **session** | One per HTTP session | User session | Shopping cart, user prefs |
| **application** | One per ServletContext | App lifecycle (like singleton) | Shared across servlets |

```java
// SINGLETON (default) — only ONE instance across entire application
@Service // Implicitly @Scope("singleton")
public class PaymentService {
    // Shared by all threads — MUST be thread-safe!
    // Don't store request-specific state here
}

// PROTOTYPE — new instance every time it's requested
@Component
@Scope("prototype")
public class ReportGenerator {
    private List<String> data = new ArrayList<>(); // Safe — each caller gets own instance
}

// REQUEST scope — one per HTTP request
@Component
@Scope(value = WebApplicationContext.SCOPE_REQUEST, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestContext {
    private String correlationId;
    private Instant requestStartTime;
    // Each HTTP request gets its own instance — automatically destroyed after response
}

// ⚠️ GOTCHA: Injecting prototype into singleton
@Service // Singleton
public class OrderService {
    @Autowired
    private ReportGenerator generator; // ❌ WRONG! Same prototype instance always!
    // Spring injects prototype ONCE during singleton creation, then reuses it

    // ✅ CORRECT: Use Provider or ObjectFactory
    @Autowired
    private ObjectProvider<ReportGenerator> generatorProvider;

    public void generateReport() {
        ReportGenerator gen = generatorProvider.getObject(); // New instance each time!
    }
}
```

---

## Q12: IoC and Dependency Injection — Core Concepts

### Theory:
**IoC (Inversion of Control)** — instead of YOUR code creating dependencies, the **container** creates them and gives them to you. Control is "inverted" — you don't call the framework, the framework calls you.

**DI (Dependency Injection)** — the mechanism to achieve IoC. Spring injects dependencies via:
1. **Constructor Injection** (✅ RECOMMENDED)
2. **Setter Injection**
3. **Field Injection** (❌ AVOID in production)

```java
// ✅ BEST: Constructor Injection — immutable, testable, no Spring dependency
@Service
public class OrderService {
    private final PaymentService paymentService;    // final = immutable
    private final OrderRepository orderRepository;
    private final KafkaTemplate<String, OrderEvent> kafka;

    // Spring auto-detects single constructor — no @Autowired needed (Spring 4.3+)
    public OrderService(PaymentService paymentService,
                        OrderRepository orderRepository,
                        KafkaTemplate<String, OrderEvent> kafka) {
        this.paymentService = paymentService;
        this.orderRepository = orderRepository;
        this.kafka = kafka;
    }
    // WHY: Easy to unit test — just pass mocks in constructor
    // WHY: Fields are final — guaranteed initialized, thread-safe
}

// ⚠️ SETTER Injection — for optional dependencies only
@Service
public class NotificationService {
    private EmailSender emailSender;

    @Autowired(required = false)  // Optional — app works without it
    public void setEmailSender(EmailSender emailSender) {
        this.emailSender = emailSender;
    }
}

// ❌ AVOID: Field Injection — hard to test, hides dependencies
@Service
public class BadService {
    @Autowired  // ❌ Can't easily mock in unit tests without reflection
    private PaymentService paymentService;
    // Can't make final, can't see dependencies from outside
}
```

### Qualifier and Primary:
```java
// When multiple beans of same type exist
public interface NotificationSender {
    void send(String message);
}

@Service("emailSender")
public class EmailSender implements NotificationSender { /* ... */ }

@Service("smsSender")
public class SmsSender implements NotificationSender { /* ... */ }

@Service
public class AlertService {
    // Option 1: @Qualifier — specify exactly which bean
    public AlertService(@Qualifier("emailSender") NotificationSender sender) {
        this.sender = sender;
    }
}

// Option 2: @Primary — default when no qualifier specified
@Service
@Primary  // This will be injected when no @Qualifier is used
public class EmailSender implements NotificationSender { /* ... */ }
```

---

## Q13: Spring Application Events

### Theory:
ApplicationContext acts as an **event publisher**. You can publish custom events and listen for them — great for **decoupling components**.

```java
// 1. DEFINE an event
public class OrderPlacedEvent extends ApplicationEvent {
    private final String orderId;
    private final BigDecimal amount;

    public OrderPlacedEvent(Object source, String orderId, BigDecimal amount) {
        super(source);
        this.orderId = orderId;
        this.amount = amount;
    }
    // getters...
}

// 2. PUBLISH the event
@Service
public class OrderService {
    private final ApplicationEventPublisher eventPublisher;

    public OrderService(ApplicationEventPublisher eventPublisher) {
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public Order placeOrder(OrderRequest request) {
        Order order = orderRepo.save(toOrder(request));
        // Publish event — all listeners will be notified
        eventPublisher.publishEvent(new OrderPlacedEvent(this, order.getId(), order.getAmount()));
        return order;
    }
}

// 3. LISTEN for the event
@Component
public class NotificationListener {
    @EventListener
    public void onOrderPlaced(OrderPlacedEvent event) {
        emailService.sendOrderConfirmation(event.getOrderId());
    }
}

@Component
public class InventoryListener {
    @EventListener
    @Async  // Process asynchronously — non-blocking
    public void onOrderPlaced(OrderPlacedEvent event) {
        inventoryService.reserveStock(event.getOrderId());
    }
}

// 4. TRANSACTIONAL event listener — executes AFTER transaction commits
@Component
public class AnalyticsListener {
    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    public void onOrderPlaced(OrderPlacedEvent event) {
        // Only runs if the order was actually committed to DB
        analyticsService.trackOrder(event.getOrderId(), event.getAmount());
    }
}
```

---

## Q14: Spring Profiles — Environment-Specific Configuration

```java
// Activate profile: spring.profiles.active=dev (or prod, staging, test)
@Configuration
@Profile("dev")
public class DevConfig {
    @Bean
    public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .build();
    }
}

@Configuration
@Profile("prod")
public class ProdConfig {
    @Bean
    public DataSource dataSource() {
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl("jdbc:postgresql://prod-db:5432/app");
        ds.setMaximumPoolSize(20);
        return ds;
    }
}

// Profile-specific property files: application-dev.yml, application-prod.yml
// application-dev.yml:
//   logging.level.root: DEBUG
//   spring.jpa.show-sql: true
//
// application-prod.yml:
//   logging.level.root: WARN
//   spring.jpa.show-sql: false
```

---

## 🎯 Spring Boot Cross-Questioning Scenarios

### Q: "What happens if two beans have a circular dependency?"
> **Answer:** "Spring can resolve circular dependencies for **singleton beans using setter/field injection** — it uses a three-level cache (singletonObjects, earlySingletonObjects, singletonFactories) to inject partially-constructed beans. However, **constructor injection circular dependencies FAIL** with `BeanCurrentlyInCreationException`. Spring Boot 2.6+ **disallows** circular dependencies by default. Fix: use `@Lazy` on one dependency, redesign with events, or extract shared logic into a third service."

### Q: "Can you refresh an ApplicationContext at runtime?"
> **Answer:** "Yes, `ConfigurableApplicationContext.refresh()` reloads all beans. But in production, you typically use **Spring Cloud Config** with `@RefreshScope` to hot-reload specific beans when configuration changes, without restarting the entire context. Actuator's `/actuator/refresh` endpoint triggers this."

### Q: "Why is field injection considered bad practice?"
> **Answer:** "Three reasons: (1) **Testability** — you can't easily pass mocks without reflection or Spring context. Constructor injection lets you `new MyService(mockRepo)`. (2) **Hidden dependencies** — the class looks like it has no dependencies from outside, but fails at runtime without them. (3) **Immutability** — fields can't be `final`, so they could theoretically be reassigned. Constructor injection makes dependencies explicit, immutable, and testable."
