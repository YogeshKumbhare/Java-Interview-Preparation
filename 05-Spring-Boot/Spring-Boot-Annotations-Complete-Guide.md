# 🍃 Spring Boot Annotations — Complete Reference Guide
## Target: 12+ Years Experience | Every Annotation Covered with Cross-Questions

> **Covers:** Core Spring, Spring Boot, Spring MVC, Spring Data JPA, Spring Security, Spring Cloud, Spring AOP, Spring Test, and more.

---

## 📋 Table of Contents

1. [Core Spring Framework Annotations](#1-core-spring-framework-annotations)
2. [Spring Boot Specific Annotations](#2-spring-boot-specific-annotations)
3. [Spring MVC / Web Annotations](#3-spring-mvc--web-annotations)
4. [Spring Data JPA / Persistence Annotations](#4-spring-data-jpa--persistence-annotations)
5. [Spring Security Annotations](#5-spring-security-annotations)
6. [Spring AOP Annotations](#6-spring-aop-annotations)
7. [Spring Cloud / Microservices Annotations](#7-spring-cloud--microservices-annotations)
8. [Spring Scheduling & Async Annotations](#8-spring-scheduling--async-annotations)
9. [Spring Caching Annotations](#9-spring-caching-annotations)
10. [Spring Testing Annotations](#10-spring-testing-annotations)
11. [Spring Validation Annotations (JSR 380)](#11-spring-validation-annotations-jsr-380)
12. [Spring Boot 3 / Spring 6 New Annotations](#12-spring-boot-3--spring-6-new-annotations)
13. [Cross-Questions & Tricky Interview Scenarios](#13-cross-questions--tricky-interview-scenarios)

---

## 1. Core Spring Framework Annotations

### 1.1 Stereotype Annotations (Bean Registration)

- **`@Component`**
  > **Explanation:** Generic annotation to register any class as a Spring bean.
- **`@Service`**
  > **Explanation:** Semantic marker for the business logic layer; behaves fundamentally like `@Component`.
- **`@Repository`**
  > **Explanation:** Marker for the data access layer (DAO); automatically translates raw SQL/JPA exceptions into Spring's consistent `DataAccessException` hierarchy.
- **`@Controller`**
  > **Explanation:** Marks a class as an MVC Controller, used for returning View names (like JSP or Thymeleaf).
- **`@RestController`**
  > **Explanation:** A convenience annotation that combines `@Controller` and `@ResponseBody`. Every method returns data directly (JSON/XML) rather than a View.

```java
// @Component — generic bean (use when none of the others fit)
@Component
public class EmailSender {
    public void send(String to, String body) { /* ... */ }
}

// @Service — business layer, NO special behavior beyond @Component
@Service
public class OrderService {
    private final OrderRepository orderRepo;
    private final EmailSender emailSender;

    public OrderService(OrderRepository orderRepo, EmailSender emailSender) {
        this.orderRepo = orderRepo;
        this.emailSender = emailSender;
    }

    public Order placeOrder(OrderRequest request) {
        Order order = orderRepo.save(mapToEntity(request));
        emailSender.send(request.getEmail(), "Order placed!");
        return order;
    }
}

// @Repository — data access layer
// SPECIAL: Translates JDBC/JPA exceptions → Spring's DataAccessException hierarchy
@Repository
public class OrderRepositoryImpl implements OrderRepositoryCustom {
    @PersistenceContext
    private EntityManager em;

    public List<Order> findExpensiveOrders(BigDecimal minAmount) {
        // If a JPA PersistenceException occurs here, Spring auto-translates it
        // to DataAccessException → easier to catch in service layer
        return em.createQuery("SELECT o FROM Order o WHERE o.amount > :min", Order.class)
                 .setParameter("min", minAmount)
                 .getResultList();
    }
}

// @Controller — returns VIEW NAMES (Thymeleaf, JSP)
@Controller
public class HomeController {
    @GetMapping("/")
    public String home(Model model) {
        model.addAttribute("title", "Welcome");
        return "home"; // → ViewResolver finds home.html
    }
}

// @RestController = @Controller + @ResponseBody
// Every method return value → JSON/XML (via HttpMessageConverter)
@RestController
@RequestMapping("/api/users")
public class UserApiController {
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id); // → Jackson serializes to JSON
    }
}
```

> **Cross-Question:** *"Is there any functional difference between @Service and @Component?"*
> **Answer:** No functional difference — both register a bean. `@Service` is purely semantic, making code self-documenting. However, `@Repository` IS different — it enables automatic exception translation via `PersistenceExceptionTranslationPostProcessor`.

---

### 1.2 Configuration Annotations

- **`@Configuration`**
  > **Explanation:** Marks a class as a source of bean definitions. Crucially, Spring creates a CGLIB proxy for any class annotated with `@Configuration`. This means calling one `@Bean` method from another within the same class will not execute the method again; instead, the proxy intercepts the call and serves the already instantiated singleton bean from the context, ensuring proper inter-bean dependencies.
- **`@Bean`**
  > **Explanation:** Used at the method level (typically inside `@Configuration` classes) to explicitly tell Spring to manage the returned object as a bean. Use this when integrating 3rd-party library classes into your Spring context where you cannot add `@Component` directly to their source code. The method name becomes the default bean ID.
- **`@ComponentScan`**
  > **Explanation:** Instructs Spring where to look for stereotype-annotated classes (`@Component`, `@Service`, etc.). You can specify base packages explicitly. If omitted, it defaults to scanning the package of the class declaring it and all sub-packages. It also heavily supports include and exclude filters (e.g., Regex, AspectJ) to fine-tune what enters the container.
- **`@Import`**
  > **Explanation:** Facilitates modular configuration. Rather than cramming all bean definitions into a single file, you can organize them logically and use `@Import({DatabaseConfig.class, WebConfig.class})` to stitch them together into one unified application context.
- **`@PropertySource`**
  > **Explanation:** Loads external properties files (like `classpath:application.properties`) into the Spring `Environment`. This allows configuration values to be easily injected via `@Value` or `@ConfigurationProperties`. Be careful: it does not support YAML files out-of-the-box unless custom PropertySourceFactory is provided.
- **`@Profile`**
  > **Explanation:** A behavioral annotation that dictates *when* a bean or configuration should be instantiated based on active profiles (like `dev`, `prod`, `test`). It essentially acts as a switch, avoiding conflicting bean definitions or loading heavy components in light environments.

```java
// @Configuration — declares the class as a source of @Bean definitions
// Internally, Spring creates a CGLIB proxy of this class to ensure
// @Bean methods return singleton instances (inter-bean references work)
@Configuration
public class AppConfig {

    @Bean // Method return value registered as a bean, method name = bean name
    public RestTemplate restTemplate() {
        return new RestTemplateBuilder()
                .setConnectTimeout(Duration.ofSeconds(3))
                .setReadTimeout(Duration.ofSeconds(5))
                .build();
    }

    @Bean("customObjectMapper") // Custom bean name
    @Primary // Default when multiple ObjectMapper beans exist
    public ObjectMapper objectMapper() {
        return new ObjectMapper()
                .registerModule(new JavaTimeModule())
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }
}

// @ComponentScan — tells Spring WHERE to scan for beans
// @SpringBootApplication already includes @ComponentScan on its package
@Configuration
@ComponentScan(basePackages = {"com.company.core", "com.company.payment"},
               excludeFilters = @ComponentScan.Filter(
                   type = FilterType.REGEX,
                   pattern = "com\\.company\\.legacy\\..*"))
public class ScanConfig {}

// @Import — explicitly imports another @Configuration class
@Configuration
@Import({SecurityConfig.class, CacheConfig.class})
public class RootConfig {}

// @PropertySource — loads external properties file
@Configuration
@PropertySource("classpath:payment.properties")
@PropertySource("classpath:email-${spring.profiles.active}.properties")
public class ExternalConfig {}

// @Profile — bean is ONLY created when specific profile is active
@Configuration
@Profile("production")
public class ProdDataSourceConfig {
    @Bean
    public DataSource dataSource() {
        // Production HikariCP pool
        HikariDataSource ds = new HikariDataSource();
        ds.setJdbcUrl("jdbc:postgresql://prod-db:5432/mydb");
        ds.setMaximumPoolSize(50);
        return ds;
    }
}

@Configuration
@Profile("dev")
public class DevDataSourceConfig {
    @Bean
    public DataSource dataSource() {
        // H2 in-memory for development
        return new EmbeddedDatabaseBuilder()
                .setType(EmbeddedDatabaseType.H2)
                .build();
    }
}
```

> **Cross-Question:** *"What's the difference between @Configuration and @Component for defining @Bean methods?"*
> **Answer:** `@Configuration` uses **CGLIB proxying** — calling one `@Bean` method from another returns the SAME singleton instance. `@Component` with `@Bean` methods does NOT proxy — each call creates a NEW instance. This is called "lite mode" vs "full mode". Always use `@Configuration` for `@Bean` definitions.

---

### 1.3 Dependency Injection Annotations

- **`@Autowired`**
  > **Explanation:** The cornerstone of Spring's Dependency Injection. It tells Spring to find a matching bean by *Type* and inject it. It can be applied to constructors, setters, or fields. Modern best practice heavily favors Constructor Injection over field injection because it ensures immutability (`final` fields) and drastically improves unit testability since no reflection is needed to mock dependencies.
- **`@Qualifier`**
  > **Explanation:** Resolves the `NoUniqueBeanDefinitionException` when Spring finds multiple beans of the same type. Paired with `@Autowired`, it narrows the lookup down by combining type-based injection with a specific bean name. 
- **`@Primary`**
  > **Explanation:** An alternative to `@Qualifier` for resolving ambiguities. By placing `@Primary` on one specific `@Bean` or `@Component` definition, you tell Spring: "If multiple beans of this type exist, inject this one by default."
- **`@Lazy`**
  > **Explanation:** Modifies the bean lifecycle. By default, beans are eagerly instantiated at startup. When `@Lazy` is used, the bean is not created until it is explicitly requested or injected into another bean for the first time. It is highly useful for optimizing startup times or circumventing circular dependency problems.
- **`@Value`**
  > **Explanation:** Used to inject primitive values, standard strings, and arrays from properties files or the OS environment. Highly powerful as it completely supports SpEL (Spring Expression Language) to dynamically evaluate complex expressions at runtime (e.g., accessing default system values or splitting command-line arguments).
- **`@ConfigurationProperties`**
  > **Explanation:** An advanced alternative to `@Value`. It allows binding an entire group of external properties (defined by a common prefix like `app.payment`) directly to a strongly-typed Java POJO. It supports hierarchical/nested structures, validation (`@Validated`), and IDE auto-completion, making it the preferred way to handle complex configurations.

```java
// @Autowired — inject dependency by TYPE
// Can be used on: constructor, field, setter
@Service
public class PaymentService {

    // ✅ BEST: Constructor Injection (immutable, testable, no @Autowired needed if single constructor)
    private final PaymentGateway gateway;
    private final OrderRepository orderRepo;

    // @Autowired is OPTIONAL if only one constructor (Spring 4.3+)
    public PaymentService(PaymentGateway gateway, OrderRepository orderRepo) {
        this.gateway = gateway;
        this.orderRepo = orderRepo;
    }
}

// @Qualifier — resolve ambiguity when MULTIPLE beans of same type exist
@Service
public class NotificationService {
    private final MessageSender sender;

    public NotificationService(@Qualifier("smsSender") MessageSender sender) {
        this.sender = sender;
    }
}

@Component("emailSender")
public class EmailMessageSender implements MessageSender { /* ... */ }

@Component("smsSender")
public class SmsMessageSender implements MessageSender { /* ... */ }

// @Primary — marks ONE bean as the DEFAULT when multiple candidates exist
@Bean @Primary
public PaymentGateway stripeGateway() { return new StripeGateway(); }

@Bean
public PaymentGateway paypalGateway() { return new PaypalGateway(); }
// → @Autowired PaymentGateway gateway; ← injects Stripe (primary)

// @Lazy — bean creation deferred until FIRST ACCESS
@Component
@Lazy // Not created at startup — only when first injected/accessed
public class HeavyReportEngine {
    public HeavyReportEngine() {
        // Expensive initialization (loads ML model, etc.)
        loadModel();
    }
}

// @Value — inject values from properties/environment
@Component
public class AppSettings {
    @Value("${app.name}")                    // From application.properties
    private String appName;

    @Value("${app.timeout:5000}")            // With default value
    private int timeout;

    @Value("${APP_SECRET_KEY}")              // Environment variable
    private String secretKey;

    @Value("#{systemProperties['user.home']}") // SpEL expression
    private String userHome;

    @Value("#{${app.feature-flags}}")        // Inject as Map
    private Map<String, Boolean> featureFlags;

    @Value("#{'${app.allowed-origins}'.split(',')}") // Inject as List
    private List<String> allowedOrigins;
}

// @ConfigurationProperties — type-safe grouped config (PREFERRED over @Value)
@Configuration
@ConfigurationProperties(prefix = "app.payment")
@Validated
public class PaymentProperties {
    @NotNull private String gatewayUrl;
    @Positive private int timeout;
    @NotBlank private String apiKey;
    private RetryConfig retry = new RetryConfig();

    // Nested config
    public static class RetryConfig {
        private int maxAttempts = 3;
        private Duration backoff = Duration.ofSeconds(1);
        // getters & setters
    }
    // getters & setters
}
// application.yml:
// app.payment:
//   gateway-url: https://api.stripe.com
//   timeout: 5000
//   api-key: sk_live_xxx
//   retry:
//     max-attempts: 5
//     backoff: 2s
```

> **Cross-Question:** *"Why is constructor injection preferred over field injection?"*
> **Answer:** (1) **Immutability** — fields can be `final`. (2) **Testability** — pass mocks directly in constructor, no reflection needed. (3) **Required dependencies are explicit** — if you miss one, compilation fails. (4) No Spring dependency in test code. (5) Prevents circular dependencies at startup (fails fast).

---

### 1.4 Bean Lifecycle Annotations

- **`@PostConstruct`**
  > **Explanation:** Part of standard JSR-250 (Java EE), this annotation marks a method to execute immediately *after* the bean object is constructed and *all* dependency injections are finished. It is the perfect place for initialization logic that requires the injected dependencies to be fully populated (e.g., warming up a cache or verifying connections).
- **`@PreDestroy`**
  > **Explanation:** The counterpart to `@PostConstruct`. Spring invokes this method right before the ApplicationContext shuts down and the bean is destroyed. Ideal for critical teardown logic such as releasing thread pools, closing network connections, or saving final state.
- **`@Scope`**
  > **Explanation:** Overrides the default `singleton` pattern of Spring. Common values include `prototype` (a brand new instance created every single time it's injected/requested), `request` (new bean per HTTP request), and `session` (new bean per user HTTP session). Proper scoping is vital for resolving concurrency issues in stateful beans.
- **`@DependsOn`**
  > **Explanation:** Explicitly forces Spring to instantiate one or more specific beans *before* the current bean is initialized. Highly useful when no direct dependency relationship (via `@Autowired`) exists, but Bean A absolutely relies on Bean B being fully configured first (e.g., a data initializer bean relying on the database migrator bean).
- **`@Order`**
  > **Explanation:** Controls the execution sequence of ordered lists of beans. Extremely useful when you have multiple implementations of an interface (like an HTTP `Filter` or an `Aspect`) and need them to fire sequentially. Lower numbers indicate higher priority (executed first).
- **`@Lookup`**
  > **Explanation:** A powerful tool for "Method Injection." When you map a `prototype` bean as a field into a `singleton` bean, you only get one instance of the prototype. Annotated with `@Lookup` on an abstract method, Spring overrides that method at runtime via CGLIB, ensuring it dynamically fetches a fresh new prototype from the container upon every method invocation.

```java
@Component
public class CacheWarmer {

    @PostConstruct // Called AFTER dependency injection is complete
    public void init() {
        log.info("Warming up cache...");
        loadFrequentData();
        // Use for: initialization, cache warming, validation
    }

    @PreDestroy // Called BEFORE bean is removed from container (app shutdown)
    public void cleanup() {
        log.info("Releasing resources...");
        closeConnections();
        // Use for: cleanup, releasing resources, flushing buffers
    }
}

// @Scope — controls how many instances Spring creates
@Component
@Scope("prototype") // New instance for EVERY injection/request
public class ShoppingCart { /* ... */ }

// Available scopes:
// singleton  — (DEFAULT) one instance per Spring container
// prototype  — new instance per injection
// request    — one per HTTP request (web only)
// session    — one per HTTP session (web only)
// application — one per ServletContext
// websocket  — one per WebSocket session

// @DependsOn — forces bean creation ORDER
@Component
@DependsOn({"cacheManager", "dataSource"})
public class DataInitializer {
    // Guaranteed: cacheManager & dataSource created BEFORE this bean
}

// @Order — defines execution ORDER (smaller = first)
@Component
@Order(1) // Executes first
public class SecurityFilter implements Filter { /* ... */ }

@Component
@Order(2) // Executes second
public class LoggingFilter implements Filter { /* ... */ }

// @Lookup — method injection for prototype beans inside singletons
@Component
public abstract class NotificationService {
    @Lookup // Spring overrides this — returns NEW prototype each time
    public abstract NotificationTask createTask();

    public void sendBatch(List<User> users) {
        users.forEach(user -> {
            NotificationTask task = createTask(); // Fresh prototype!
            task.execute(user);
        });
    }
}
```

> **Cross-Question:** *"What happens if you inject a prototype-scoped bean into a singleton?"*
> **Answer:** You get the SAME prototype instance every time — because the singleton is created ONCE, and the prototype is injected ONCE at creation time. Fixes: (1) `@Lookup` method injection. (2) `ObjectFactory<T>` or `Provider<T>` injection. (3) Scoped proxy (`@Scope(proxyMode = ScopedProxyMode.TARGET_CLASS)`).

---

## 2. Spring Boot Specific Annotations

- **`@SpringBootApplication`**
  > **Explanation:** The definitive entry-point annotation that jump-starts a Spring Boot application. It is primarily a macro that combines three significant annotations natively: `@Configuration` (marks the class as a bean source), `@EnableAutoConfiguration` (unleashes the magic of intelligent inference), and `@ComponentScan` (starts scanning the current package and all child packages).
- **`@EnableAutoConfiguration`**
  > **Explanation:** The "magic" engine of Spring Boot. When processed, Boot inspects the classpath, existing beans, and properties, and automatically instantiates missing infrastructure components. For example, if it detects `tomcat-embed-core` and Spring Web MVC on the classpath, it automatically boots up an embedded Tomcat server without requiring explicit manual configuration.
- **`@ConditionalOn...`** (e.g., `Property`, `Class`, `MissingBean`): **Deep Dive:** These serve as the backbone for creating robust auto-configuration classes. They dynamically evaluate conditions at runtime. Examples include `@ConditionalOnProperty` (load bean only if a specific property is defined/true) and `@ConditionalOnMissingBean` (only instantiate this default fallback component if the user hasn't provided their own implementation).
- **`@EnableConfigurationProperties`**
  > **Explanation:** Explicitly informs Spring to process specific types annotated with `@ConfigurationProperties`. Without this (or `@ConfigurationPropertiesScan`), the property binding POJOs won't be instantiated and added to the application context.
- **`@ConfigurationPropertiesScan`**
  > **Explanation:** Instead of individually listing out property classes inside `@EnableConfigurationProperties({...})`, this newer annotation automatically scans designated packages to dynamically find and register all classes annotated with `@ConfigurationProperties`.

```java
// @SpringBootApplication — THE entry point annotation
// = @Configuration + @EnableAutoConfiguration + @ComponentScan
@SpringBootApplication
public class MyApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyApplication.class, args);
    }
}

// Customize what it scans/excludes:
@SpringBootApplication(
    scanBasePackages = "com.company",
    exclude = {DataSourceAutoConfiguration.class, SecurityAutoConfiguration.class}
)
public class MyApplication { /* ... */ }

// @EnableAutoConfiguration — triggers auto-configuration magic
// Reads META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
// Each auto-config class has @ConditionalOn* annotations to decide if it applies

// @Conditional Annotations — control WHEN beans are created
@Configuration
public class ConditionalBeansDemo {

    @Bean
    @ConditionalOnProperty(name = "feature.payments.enabled", havingValue = "true")
    public PaymentService paymentService() { return new PaymentService(); }
    // Bean created ONLY if property is "true"

    @Bean
    @ConditionalOnClass(name = "com.amazonaws.services.s3.AmazonS3")
    public FileStorage s3Storage() { return new S3FileStorage(); }
    // Bean created ONLY if AWS SDK is on classpath

    @Bean
    @ConditionalOnMissingBean(FileStorage.class)
    public FileStorage localStorage() { return new LocalFileStorage(); }
    // Fallback: created ONLY if no other FileStorage bean exists

    @Bean
    @ConditionalOnBean(DataSource.class)
    public DatabaseHealthChecker dbHealthChecker() { return new DatabaseHealthChecker(); }
    // Created ONLY if a DataSource bean exists

    @Bean
    @ConditionalOnWebApplication
    public WebMetricsCollector webMetrics() { return new WebMetricsCollector(); }
    // Web apps only

    @Bean
    @ConditionalOnExpression("${feature.premium:false} and ${feature.enabled:true}")
    public PremiumFeature premiumFeature() { return new PremiumFeature(); }
    // SpEL expression must evaluate to true

    @Bean
    @ConditionalOnJava(JavaVersion.SEVENTEEN)
    public RecordProcessor recordProcessor() { return new RecordProcessor(); }
    // Java 17+ only

    @Bean
    @ConditionalOnResource(resources = "classpath:templates/email.html")
    public EmailTemplateService emailService() { return new EmailTemplateService(); }
    // Resource must exist on classpath
}

// @EnableConfigurationProperties — binds properties POJO to config
@Configuration
@EnableConfigurationProperties(PaymentProperties.class)
public class PaymentConfig { /* ... */ }

// @ConfigurationPropertiesScan — auto-scan for @ConfigurationProperties classes
@SpringBootApplication
@ConfigurationPropertiesScan("com.company.config")
public class MyApplication { /* ... */ }
```

> **Cross-Question:** *"How does Spring Boot decide which auto-configurations to apply?"*
> **Answer:** On startup, Spring reads all `AutoConfiguration.imports` files (~150 classes). Each class has `@ConditionalOn*` annotations. For example, `DataSourceAutoConfiguration` has `@ConditionalOnClass(DataSource.class)` — if H2/PostgreSQL driver is on classpath, it auto-creates a `DataSource`. Set `debug=true` in properties to see the full conditions evaluation report.

---

## 3. Spring MVC / Web Annotations

### 3.1 Request Mapping Annotations

- **`@RequestMapping`**
  > **Explanation:** The foundational annotation for mapping web requests to specific Spring Controller methods. It works universally for all HTTP methods (GET, POST, etc.) and allows granular configurations such as restricting mapping by headers, consumable media types, or producible media types. When placed at the class level, it provides a base URI path for all handler methods within that controller.
- **`@GetMapping`**, **`@PostMapping`**, **`@PutMapping`**, **`@DeleteMapping`**, **`@PatchMapping`**
  > **Explanation:** These serve as composed shortcuts for `@RequestMapping(method = RequestMethod.GET)` (and their respective methods). Introduced to reduce verbosity and enforce clean RESTful API design, they inherently document the expected HTTP interaction directly making the code easier to read and maintain.

```java
@RestController
@RequestMapping("/api/v1/products") // Base path for all methods
public class ProductController {

    // @GetMapping — HTTP GET (read resources)
    @GetMapping                              // GET /api/v1/products
    public List<Product> getAll() { /* ... */ }

    @GetMapping("/{id}")                     // GET /api/v1/products/123
    public Product getById(@PathVariable Long id) { /* ... */ }

    @GetMapping(params = "category")         // GET /api/v1/products?category=electronics
    public List<Product> getByCategory(@RequestParam String category) { /* ... */ }

    // @PostMapping — HTTP POST (create resources)
    @PostMapping                             // POST /api/v1/products
    @ResponseStatus(HttpStatus.CREATED)      // Returns 201 instead of 200
    public Product create(@Valid @RequestBody ProductRequest req) { /* ... */ }

    // @PutMapping — HTTP PUT (full update)
    @PutMapping("/{id}")                     // PUT /api/v1/products/123
    public Product update(@PathVariable Long id, @Valid @RequestBody ProductRequest req) { /* ... */ }

    // @PatchMapping — HTTP PATCH (partial update)
    @PatchMapping("/{id}")                   // PATCH /api/v1/products/123
    public Product partialUpdate(@PathVariable Long id, @RequestBody Map<String, Object> updates) { /* ... */ }

    // @DeleteMapping — HTTP DELETE (remove resources)
    @DeleteMapping("/{id}")                  // DELETE /api/v1/products/123
    @ResponseStatus(HttpStatus.NO_CONTENT)   // Returns 204
    public void delete(@PathVariable Long id) { /* ... */ }

    // @RequestMapping — the GENERIC version (supports any HTTP method)
    @RequestMapping(value = "/search", method = RequestMethod.GET,
                    produces = MediaType.APPLICATION_JSON_VALUE,
                    consumes = MediaType.APPLICATION_JSON_VALUE)
    public List<Product> search(@RequestBody SearchCriteria criteria) { /* ... */ }
}
```

### 3.2 Method Parameter Annotations

- **`@PathVariable`**
  > **Explanation:** Binds a URI template variable (e.g., the `123` in `/users/123`) directly to a Java method parameter. By default, it is required, and omitting it results in a `404 Not Found`. Use this for resources that are essential to identifying the endpoint target.
- **`@RequestParam`**
  > **Explanation:** Extracts query string parameters (e.g., `?category=books`) or form-data payloads. Unlike `@PathVariable`, it allows defining `required=false` and `defaultValue="10"`, making it excellent for optional search filters, pagination, or sorting inputs.
- **`@RequestBody`**
  > **Explanation:** Instructs Spring to read the raw HTTP request body (usually JSON) and map it into a Java object using an `HttpMessageConverter` (like Jackson). Crucial for accepting complex payloads in POST/PUT paths. If combined with `@Valid`, Spring will automatically validate the incoming object before executing the method.
- **`@RequestHeader`**
  > **Explanation:** Explicitly binds an upcoming HTTP request header (like `Authorization` or `X-Forwarded-For`) to a method parameter. Highly useful when extracting tracing IDs or JWT tokens directly inside the controller method.
- **`@CookieValue`**
  > **Explanation:** Extracts the value of a specific HTTP cookie. Saves you from injecting the entire `HttpServletRequest` just to iterate through its cookie array.
- **`@ModelAttribute`**
  > **Explanation:** Primarily used in classic MVC (Thymeleaf/JSP). It binds form data parameters directly to a domain object and automatically adds that object to the Model view. It can also act as a method-level annotation to pre-populate common model data across all methods in a controller.
- **`@ResponseStatus`**
  > **Explanation:** Forces a specific HTTP status code (like `201 CREATED` or `204 NO CONTENT`) to be returned. You can apply this either to a successful controller method or place it directly on a custom Exception class (e.g., throwing `ResourceNotFoundException` automatically triggers a `404`).
- **`@ExceptionHandler`**
  > **Explanation:** Provides a mechanism to handle exceptions at the Controller level. Instead of wrapping logic in try/catch blocks, you define a single method annotated with `@ExceptionHandler(CustomException.class)` that triggers exclusively when that exception is thrown anywhere within the controller.
- **`@RestControllerAdvice`**
  > **Explanation:** A specialization of Spring's AOP conceptually. It acts as a global interceptor that catches exceptions thrown by *any* `@RestController` across the application. Using this, you create a unified error-handling mechanism and a standard JSON error response schema for your entire API.
- **`@CrossOrigin`**
  > **Explanation:** Bypasses browser Same-Origin Policy enforcement by adding appropriate CORS HTTP headers (like `Access-Control-Allow-Origin`). Applied per controller or per method, allowing fine-grained access exclusively for approved frontend domains.

```java
@RestController
public class DemoController {

    @GetMapping("/demo")
    public String demo(
        @PathVariable Long id,                                      // From URL: /demo/{id}
        @RequestParam(defaultValue = "10") int limit,               // From query: ?limit=10
        @RequestParam(required = false) String filter,              // Optional query param
        @RequestHeader("Authorization") String authHeader,          // From HTTP header
        @RequestHeader(value = "X-Request-Id", required = false) String reqId,
        @CookieValue(value = "sessionId", required = false) String session, // From cookie
        @RequestBody OrderRequest body,                             // From HTTP body (JSON)
        @ModelAttribute UserForm form,                              // From form data
        @MatrixVariable Map<String, String> matrixVars,             // From matrix: /demo;color=red
        HttpServletRequest request,                                 // Raw servlet request
        Principal principal                                         // Authenticated user
    ) { /* ... */ }
}

// @CrossOrigin — CORS at controller/method level
@RestController
@CrossOrigin(origins = {"http://localhost:3000", "https://myapp.com"},
             methods = {RequestMethod.GET, RequestMethod.POST},
             maxAge = 3600)
public class ApiController { /* ... */ }

// @ResponseStatus — set HTTP status code
@ResponseStatus(HttpStatus.NOT_FOUND)
public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String msg) { super(msg); }
}
// Whenever this exception is thrown → automatic 404 response

// @ExceptionHandler — handle exceptions in a controller
@RestController
public class OrderController {
    @ExceptionHandler(IllegalArgumentException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public ErrorResponse handleBadRequest(IllegalArgumentException ex) {
        return new ErrorResponse(400, ex.getMessage());
    }
}

// @ControllerAdvice / @RestControllerAdvice — GLOBAL exception handling
@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(Exception.class)
    @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
    public ErrorResponse handleAll(Exception ex) {
        return new ErrorResponse(500, "Internal error");
    }
}
```

> **Cross-Question:** *"What's the difference between @RequestParam and @PathVariable?"*
> **Answer:** `@PathVariable` extracts from URL path (`/users/{id}` → id=123), `@RequestParam` extracts from query string (`/users?id=123`). Use `@PathVariable` for required resource identifiers, `@RequestParam` for optional filtering/pagination. `@PathVariable` is mandatory by default; `@RequestParam` can have `required=false` and `defaultValue`.

---

## 4. Spring Data JPA / Persistence Annotations

### 4.1 Entity Mapping Annotations (javax/jakarta.persistence)

- **`@Entity`**
  > **Explanation:** Denotes that a POJO is a persistent JPA entity. The JPA provider (like Hibernate) maps this class directly to a database table. Every `@Entity` class must have a no-args constructor (protected or public) so the object can be instantiated via reflection during queries.
- **`@Table`**
  > **Explanation:** While `@Entity` is mandatory, `@Table` is optional. Use it to override the default table name mapping, declare the schema, or establish multi-column indexes and unique constraints directly at the database level.
- **`@Id`**
  > **Explanation:** Indicates the primary key of the entity. Every `@Entity` must possess an `@Id` field to uniquely identify rows in the database sequence.
- **`@GeneratedValue`**
  > **Explanation:** Dictates how the `@Id` is generated. Usually paired with `strategy = GenerationType.IDENTITY` (relies on SQL auto-increment columns like MySQL) or `GenerationType.SEQUENCE` (relies on database sequences, highly optimized in PostgreSQL for batch inserts).
- **`@Column`**
  > **Explanation:** Allows fine-tuning of column data constraints. Specifically useful for defining `nullable=false`, limiting `length=50` for Strings (which defines the VARCHAR limit), or explicitly setting `unique=true`.
- **`@Enumerated`**
  > **Explanation:** Determines how Java `Enum` types are stored. By default, JPA stores Enums as `ORDINAL` (integer indexes), which breaks terribly if you re-order the Enum elements. Always use `@Enumerated(EnumType.STRING)` to safely store the readable string value.
- **`@Transient`**
  > **Explanation:** Instructs Hibernate to completely ignore the field. This field will not be mapped to any database column, nor will it participate in any saving or fetching operations. Excellent for calculated runtime values like `totalPrice`.
- **`@OneToOne`**, **`@OneToMany`**, **`@ManyToOne`**, **`@ManyToMany`**
  > **Explanation:** Maps relational DB connections. Crucial details: `@ManyToOne` is fetched `EAGER` by default. `@OneToMany` is fetched `LAZY` by default. Best practice: explicitly set `fetch = FetchType.LAZY` for all nested associations to prevent performance-killing N+1 queries. 
- **`@JoinColumn`**, **`@JoinTable`**
  > **Explanation:** Specifies exactly *how* relationships are physically joined. `@JoinColumn` creates a specific foreign key column in the current table pointing to the target. `@JoinTable` is mandatory for many-to-many associations and creates an intermediate "mapping" table linking the primary IDs of both relations.
- **`@Embeddable`**, **`@Embedded`**
  > **Explanation:** Used for composition. An `@Embeddable` POJO (like `Address`) groups multiple columns natively. `@Embedded` places those columns directly into the parent table (e.g., `User` table gets `street`, `city`, `zipCode` columns directly). This prevents unnecessary JOINs while keeping Java code clean.
- **`@Version`**
  > **Explanation:** Implements Optimistic Locking natively. When an entity is updated, Hibernate verifies the Version column hasn't changed. If it has (indicating another thread modified it concurrently), an `OptimisticLockException` is thrown, preventing lost updates without requiring expensive pessimistic database locks.

```java
@Entity                              // Marks class as a JPA entity (maps to DB table)
@Table(name = "orders",              // Table name (defaults to class name)
       schema = "public",
       uniqueConstraints = @UniqueConstraint(columnNames = {"order_number", "user_id"}),
       indexes = @Index(name = "idx_order_status", columnList = "status"))
public class Order {

    @Id                              // Primary key
    @GeneratedValue(strategy = GenerationType.IDENTITY)  // Auto-increment
    // Strategies: IDENTITY (DB auto-inc), SEQUENCE (DB sequence), TABLE, UUID
    private Long id;

    @Column(name = "order_number", nullable = false, unique = true, length = 50)
    private String orderNumber;

    @Column(precision = 10, scale = 2) // For BigDecimal
    private BigDecimal amount;

    @Enumerated(EnumType.STRING)     // Store enum as STRING (not ordinal!)
    @Column(nullable = false)
    private OrderStatus status;

    @Temporal(TemporalType.TIMESTAMP) // For java.util.Date (not needed for java.time)
    private Date createdAt;

    @Lob                             // Large object (CLOB/BLOB)
    private String description;

    @Transient                       // NOT persisted — excluded from DB
    private BigDecimal calculatedTax;

    @Version                         // Optimistic locking — auto-incremented on update
    private Long version;            // If version mismatch → OptimisticLockException

    @CreatedDate                     // Auto-set on creation (Spring Data Auditing)
    private Instant createdAt;

    @LastModifiedDate                // Auto-set on update
    private Instant updatedAt;

    @CreatedBy                       // Auto-set creator (needs AuditorAware bean)
    private String createdBy;
}

// RELATIONSHIP Annotations
@Entity
public class Order {

    @ManyToOne(fetch = FetchType.LAZY)         // Many orders → one user
    @JoinColumn(name = "user_id")              // FK column in orders table
    private User user;

    @OneToMany(mappedBy = "order",             // One order → many items
               cascade = CascadeType.ALL,       // Cascade all operations
               orphanRemoval = true,            // Delete orphan items
               fetch = FetchType.LAZY)          // LAZY is default for collections
    private List<OrderItem> items = new ArrayList<>();

    @OneToOne(cascade = CascadeType.ALL)       // One order → one payment
    @JoinColumn(name = "payment_id")
    private Payment payment;

    @ManyToMany                                // Many orders → many tags
    @JoinTable(name = "order_tags",
               joinColumns = @JoinColumn(name = "order_id"),
               inverseJoinColumns = @JoinColumn(name = "tag_id"))
    private Set<Tag> tags = new HashSet<>();
}

// @Embeddable / @Embedded — reusable value objects
@Embeddable
public class Address {
    private String street;
    private String city;
    @Column(name = "zip_code")
    private String zipCode;
}

@Entity
public class User {
    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "home_street")),
        @AttributeOverride(name = "city", column = @Column(name = "home_city"))
    })
    private Address homeAddress;

    @Embedded
    @AttributeOverrides({
        @AttributeOverride(name = "street", column = @Column(name = "work_street")),
        @AttributeOverride(name = "city", column = @Column(name = "work_city"))
    })
    private Address workAddress;
}

// @Inheritance — mapping inheritance strategies
@Entity
@Inheritance(strategy = InheritanceType.SINGLE_TABLE) // All in one table
@DiscriminatorColumn(name = "payment_type")
public abstract class Payment { /* ... */ }

@Entity
@DiscriminatorValue("CREDIT_CARD")
public class CreditCardPayment extends Payment { /* ... */ }

// Other strategies: TABLE_PER_CLASS, JOINED
```

### 4.2 Spring Data Repository Annotations

- **`@EnableJpaRepositories`**
  > **Explanation:** Instructs Spring Boot to scan specific packages for interfaces extending `JpaRepository`. Boot does this automatically, but you need this annotation if your repositories reside in a modular package hierarchy outside the root `@SpringBootApplication` context.
- **`@EnableJpaAuditing`**
  > **Explanation:** Activates the JPA auditing engine. Paired with `@EntityListeners(AuditingEntityListener.class)` on entities, it guarantees fields like `@CreatedDate`, `@LastModifiedDate`, and `@CreatedBy` are intrinsically populated upon `save()` operations without writing explicit boilerplate code.
- **`@Query`**
  > **Explanation:** When dynamic generated methods (`findByEmailAndStatus`) aren't expressive enough, `@Query` allows you to write direct Java Persistence Query Language (JPQL) or `nativeQuery=true` raw SQL. JPQL is database agnostic, while native queries execute direct SQL bound to your exact RDBMS syntax.
- **`@Modifying`**
  > **Explanation:** By default, Spring Data assumes `@Query` operations are read-only (`SELECT`). For an explicitly created query meant to modify rows (`UPDATE` or `DELETE`), this annotation is rigidly required to clear the Hibernate entity cache and flag the transaction as mutable.
- **`@Param`**
  > **Explanation:** explicitly maps interface method arguments to the named variables (`:myVariable`) used inside an explicit `@Query`. This solves the issue of Java stripping parameter variable names from byte-code compilation.
- **`@EntityGraph`**
  > **Explanation:** The definitive silver bullet for resolving the N+1 query problem. Overriding a repository's fetch-type locally, an `@EntityGraph` informs Spring to load all nested `LAZY` relationships in a single optimized SQL `JOIN` command only for that specific query.
- **`@Lock`**
  > **Explanation:** Extends standard database locking controls. For instance, `LockModeType.PESSIMISTIC_WRITE` issues a `SELECT ... FOR UPDATE` query structure at the database level. Useful if you need serialized access against rows to prevent race-condition concurrency anomalies over critical financial or inventory updates.

```java
// @EnableJpaRepositories — enables JPA repositories scanning
@Configuration
@EnableJpaRepositories(basePackages = "com.company.repository")
public class JpaConfig { /* ... */ }

// @EnableJpaAuditing — enables @CreatedDate, @LastModifiedDate
@Configuration
@EnableJpaAuditing(auditorAwareRef = "auditorProvider")
public class AuditConfig {
    @Bean
    public AuditorAware<String> auditorProvider() {
        return () -> Optional.ofNullable(SecurityContextHolder.getContext()
                .getAuthentication().getName());
    }
}

// @Query, @Modifying, @Param — custom queries
public interface UserRepository extends JpaRepository<User, Long> {

    @Query("SELECT u FROM User u WHERE u.email = :email")
    Optional<User> findByEmail(@Param("email") String email);

    @Query(value = "SELECT * FROM users WHERE status = ?1", nativeQuery = true)
    List<User> findByStatusNative(String status);

    @Modifying
    @Transactional
    @Query("UPDATE User u SET u.active = false WHERE u.lastLogin < :date")
    int deactivateInactiveUsers(@Param("date") Instant date);

    @EntityGraph(attributePaths = {"orders", "orders.items"}) // Solves N+1!
    Optional<User> findWithOrdersById(Long id);

    @Lock(LockModeType.PESSIMISTIC_WRITE) // SELECT ... FOR UPDATE
    Optional<User> findAndLockById(Long id);
}

// @NamedQuery — pre-defined named queries on entity
@Entity
@NamedQuery(name = "User.findActiveUsers",
            query = "SELECT u FROM User u WHERE u.active = true")
public class User { /* ... */ }
```

> **Cross-Question:** *"What's the difference between FetchType.LAZY and FetchType.EAGER? Which is default?"*
> **Answer:** `LAZY` — loads data on first access (proxy). `EAGER` — loads immediately with parent. **Defaults:** `@ManyToOne` and `@OneToOne` = EAGER. `@OneToMany` and `@ManyToMany` = LAZY. **Best practice:** Always use LAZY and fetch explicitly with `@EntityGraph` or `JOIN FETCH` to avoid N+1 queries.

---

## 5. Spring Security Annotations

- **`@EnableWebSecurity`**
  > **Explanation:** A class-level annotation that flips the switch to activate Spring Security's rigorous web-security model. Combined with `@Configuration`, it allows you to inject `HttpSecurity` and programmatically construct robust security filter chains, configure CSRF, CORS, form login, and OAuth2 resource limits.
- **`@EnableMethodSecurity`**
  > **Explanation:** (Replaces the deprecated `@EnableGlobalMethodSecurity` in Spring 3.0+). It activates annotations like `@PreAuthorize` globally. By default, Spring Security only protects URLs; this pushes authorization deep into the service layer, protecting specific method executions irrespective of how they were invoked.
- **`@PreAuthorize`**, **`@PostAuthorize`**
  > **Explanation:** Extremely powerful method-level security that leverages SpEL (Spring Expression Language). `@PreAuthorize("hasRole('ADMIN')")` evaluates before the method executes. `@PostAuthorize` allows the method to execute and calculates logic against the generated `returnObject` before deciding whether to throw an AccessDeniedException.
- **`@PreFilter`**, **`@PostFilter`**
  > **Explanation:** Primarily used to secure collections. `@PreFilter` strips unauthorized elements out of a `List` argument *before* it passes to the method. `@PostFilter` silently strips elements out of the returned `List` that the current user lacks permission to see, providing elegant data subsetting without polluting business logic.
- **`@Secured`**, **`@RolesAllowed`**
  > **Explanation:** The legacy and JSR-250 standard approaches to method security, respectively. Unlike @`PreAuthorize`, they do *not* support SpEL. They are strictly limited to simple String matches (e.g., `"ROLE_USER"`). It is highly recommended to use `@PreAuthorize` in modern applications instead.
- **`@AuthenticationPrincipal`**
  > **Explanation:** Resolves the `SecurityContextHolder.getContext().getAuthentication().getPrincipal()` object and injects it directly into an `@RestController` method parameter. It elegantly decouples your controller from static Spring Security API calls, improving testability.
- **`@WithMockUser`**
  > **Explanation:** Specifically engineered for the `spring-security-test` library. It synthetically populates the `SecurityContext` with a mock authenticated user, bypassing the physical login flow so you can write crisp `@SpringBootTest` tests that focus strictly on authorization logic.

```java
// @EnableWebSecurity — enables Spring Security's web support
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http.csrf(c -> c.disable())
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/public/**").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated())
            .build();
    }
}

// @EnableMethodSecurity — enables method-level security (Spring Security 6+)
// Replaces deprecated @EnableGlobalMethodSecurity
@Configuration
@EnableMethodSecurity(prePostEnabled = true, securedEnabled = true, jsr250Enabled = true)
public class MethodSecurityConfig { /* ... */ }

// Method-Level Security Annotations
@Service
public class OrderService {

    @PreAuthorize("hasRole('ADMIN') or #userId == authentication.principal.id")
    // Checked BEFORE method execution — SpEL expression
    public Order getOrder(Long userId, Long orderId) { /* ... */ }

    @PostAuthorize("returnObject.userId == authentication.principal.id")
    // Checked AFTER method execution — access return value
    public Order findOrder(Long orderId) { /* ... */ }

    @PreFilter("filterObject.userId == authentication.principal.id")
    // Filters INPUT collection before method runs
    public void deleteOrders(List<Order> orders) { /* ... */ }

    @PostFilter("filterObject.status != 'DRAFT'")
    // Filters OUTPUT collection after method runs
    public List<Order> getAllOrders() { /* ... */ }

    @Secured({"ROLE_ADMIN", "ROLE_MANAGER"})
    // Simpler than @PreAuthorize — just roles, no SpEL
    public void deleteUser(Long userId) { /* ... */ }

    @RolesAllowed({"ADMIN", "MANAGER"})
    // JSR-250 standard (Jakarta) — same as @Secured but standard
    public void resetPassword(Long userId) { /* ... */ }
}

// @AuthenticationPrincipal — inject current authenticated user
@GetMapping("/me")
public UserProfile getProfile(@AuthenticationPrincipal UserDetails user) {
    return userService.getProfile(user.getUsername());
}

// @WithMockUser — for testing secured methods
@Test
@WithMockUser(username = "admin", roles = {"ADMIN"})
void adminCanDeleteUsers() { /* ... */ }
```

> **Cross-Question:** *"Difference between @Secured and @PreAuthorize?"*
> **Answer:** `@Secured` only supports role-based checks (no expressions). `@PreAuthorize` supports **Spring Expression Language (SpEL)** — can check method parameters, authentication details, custom beans, etc. `@PreAuthorize` is more powerful and preferred for complex authorization logic.

---

## 6. Spring AOP Annotations

- **`@EnableAspectJAutoProxy`**
  > **Explanation:** Triggers Spring's auto-proxy creation engine. When active, Spring scans for `@Aspect` beans and dynamically generates either JDK Dynamic Proxies (for interfaces) or CGLIB proxies (for classes) to seamlessly wrap your target beans with aspect logic.
- **`@Aspect`**
  > **Explanation:** Originates from the AspectJ library but is intrinsically supported by Spring AOP. It marks a class not as business logic, but as a centralized module containing cross-cutting concerns (like logging, telemetry, or transaction management) separated from your core code.
- **`@Pointcut`**
  > **Explanation:** Centralizes your target expressions. Instead of repeatedly writing `execution(* com.myapp.service.*.*(..))` on every piece of advice, you define it once above an empty method annotated with `@Pointcut`, and reference that method name elsewhere.
- **`@Before`**
  > **Explanation:** An AOP advice that triggers strictly before a join point (method execution). It's primarily used for non-blocking concerns like debug logging, auditing, or security validation. It cannot prevent the method from executing unless it deliberately throws a RuntimeException.
- **`@After`**
  > **Explanation:** often called "After (Finally)" advice. It executes unconditionally after the matched method concludes, regardless of whether the method returned gracefully or threw an exception. Ideal for releasing physical resources or tracking endpoint conclusion.
- **`@AfterReturning`**
  > **Explanation:** Executes strictly if the matched method completes without throwing an exception. It provides explicit access to the `returning` object, allowing you to read (but not modify) the method's generated output payload before sending it out.
- **`@AfterThrowing`**
  > **Explanation:** Executes strictly if the matched method throws an exception. Highly valuable for establishing a centralized, non-intrusive logging matrix for specific types of infrastructure failures, allowing business logic to remain uncluttered.
- **`@Around`**
  > **Explanation:** The absolute most powerful AOP annotation. It completely envelops the target method via `ProceedingJoinPoint`. You control exactly *when* (and *if*) the target method executes via `proceed()`. This is essential for features like execution timers, retry mechanisms, or transparently caching and swallowing exceptions.

```java
// @EnableAspectJAutoProxy — enables AOP proxy creation
@Configuration
@EnableAspectJAutoProxy
public class AopConfig { /* ... */ }

@Aspect       // Marks class as an AOP Aspect
@Component    // Must also be a Spring bean
@Slf4j
public class LoggingAspect {

    // @Pointcut — defines WHERE advice applies
    @Pointcut("execution(* com.company.service.*.*(..))")
    public void serviceLayer() {}

    // @Before — runs BEFORE the target method
    @Before("serviceLayer()")
    public void logBefore(JoinPoint jp) {
        log.info("→ {}.{}()", jp.getTarget().getClass().getSimpleName(),
                jp.getSignature().getName());
    }

    // @After — runs AFTER (regardless of success/failure)
    @After("serviceLayer()")
    public void logAfter(JoinPoint jp) {
        log.info("← {}", jp.getSignature().getName());
    }

    // @AfterReturning — runs AFTER successful return
    @AfterReturning(pointcut = "serviceLayer()", returning = "result")
    public void logReturn(JoinPoint jp, Object result) {
        log.info("Returned: {}", result);
    }

    // @AfterThrowing — runs if method THROWS exception
    @AfterThrowing(pointcut = "serviceLayer()", throwing = "ex")
    public void logException(JoinPoint jp, Exception ex) {
        log.error("Exception in {}: {}", jp.getSignature(), ex.getMessage());
    }

    // @Around — MOST powerful — wraps method execution
    @Around("@annotation(com.company.annotation.Monitored)")
    public Object measureTime(ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        try {
            Object result = pjp.proceed(); // Execute original method
            return result;
        } finally {
            long duration = (System.nanoTime() - start) / 1_000_000;
            log.info("{}() took {}ms", pjp.getSignature().getName(), duration);
        }
    }
}

// Pointcut Expression Examples:
// execution(* com.company.service.*.*(..))     — All methods in service package
// execution(public * *(..))                     — All public methods
// @annotation(Transactional)                    — Methods with @Transactional
// within(com.company.controller..*)             — All classes in controller package
// bean(*Service)                                — Beans ending with "Service"
// args(String, ..)                              — Methods with first arg String
```

> **Cross-Question:** *"Spring AOP uses proxy-based AOP. What are its limitations?"*
> **Answer:** (1) Only works on **public methods** (private/protected are not proxied). (2) **Self-invocation** bypasses the proxy — calling `this.method()` skips AOP advice. (3) Only works on **Spring beans** — plain Java objects are not proxied. (4) Uses either JDK dynamic proxies (interface-based) or CGLIB proxies (subclass-based). For full power, use AspectJ with compile-time weaving.

---

## 7. Spring Cloud / Microservices Annotations

- **`@EnableEurekaServer`**, **`@EnableDiscoveryClient`**
  > **Explanation:** The pillars of service discovery. `@EnableEurekaServer` spins up a dedicated Netflix Eureka registry node. Downstream microservices use `@EnableDiscoveryClient` to autonomously register their dynamic physical IP addresses with the server on startup, eliminating the need for hardcoded local network IPs.
- **`@EnableConfigServer`**
  > **Explanation:** Turns a standard Spring Boot application into a centralized Spring Cloud Config orchestrator. It connects natively to an external backing store (typically Git, Vault, or AWS Parameter Store) and serves configuration properties over HTTP to all other microservices in the cluster based on their profile.
- **`@EnableFeignClients`**, **`@FeignClient`**
  > **Explanation:** Pioneered by Netflix, this eliminates `RestTemplate` boilerplate. By annotating a Java interface with `@FeignClient`, Spring automatically generates a dynamic implementation at runtime that handles HTTP connections, Eureka payload resolution, and JSON parsing seamlessly under the hood.
- **`@CircuitBreaker`**, **`@Retry`**, **`@RateLimiter`**
  > **Explanation:** Sourced from the Resilience4j library (the modern replacement for Netflix Hystrix). These annotations drastically improve microservice durability. `@CircuitBreaker` cuts immediate connections to failing downstream services. `@RateLimiter` ensures APIs don't exceed threshold constraints, mitigating DDoS failures. 
- **`@StreamListener`**, **`@EnableBinding`**
  > **Explanation:** *Legacy Warning:* These annotations powered older versions of Spring Cloud Stream to bind RabitMQ/Kafka topics dynamically to methods. In current Spring versions, they are entirely deprecated in favor of Java 8 Functional Interfaces (`Supplier`, `Function`, `Consumer`) integrated with Cloud Stream.

```java
// SERVICE DISCOVERY
@SpringBootApplication
@EnableEurekaServer           // Makes this app a Eureka registry server
public class RegistryApp { /* ... */ }

@SpringBootApplication
@EnableDiscoveryClient        // Registers app with Eureka/Consul/Zookeeper
public class OrderServiceApp { /* ... */ }

// CONFIG SERVER
@SpringBootApplication
@EnableConfigServer           // Centralized config server (Git-backed)
public class ConfigServerApp { /* ... */ }

// FEIGN CLIENT — declarative REST client
@EnableFeignClients           // Enable Feign client scanning
@SpringBootApplication
public class App { /* ... */ }

@FeignClient(name = "user-service",
             fallback = UserClientFallback.class,       // Circuit breaker fallback
             configuration = FeignConfig.class)
public interface UserClient {
    @GetMapping("/api/users/{id}")
    UserDTO getUser(@PathVariable("id") Long id);

    @PostMapping("/api/users")
    UserDTO createUser(@RequestBody CreateUserRequest req);
}

// CIRCUIT BREAKER (Resilience4j)
@Service
public class PaymentService {
    @CircuitBreaker(name = "paymentService", fallbackMethod = "fallbackPayment")
    @Retry(name = "paymentService")
    @RateLimiter(name = "paymentService")
    @Bulkhead(name = "paymentService")
    @TimeLimiter(name = "paymentService")
    public PaymentResponse processPayment(PaymentRequest req) { /* ... */ }

    public PaymentResponse fallbackPayment(PaymentRequest req, Throwable t) {
        return new PaymentResponse("QUEUED", "Payment queued for retry");
    }
}

// API GATEWAY (Spring Cloud Gateway)
// Configured via application.yml, not annotations typically
// But route predicates and filters use annotations in custom filters
@Component
public class AuthGatewayFilter implements GatewayFilter {
    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // Custom gateway filter logic
        return chain.filter(exchange);
    }
}

// STREAM (Event-Driven with Kafka/RabbitMQ)
@SpringBootApplication
@EnableBinding(Sink.class) // Legacy — newer: use functional style
public class EventConsumer {
    @StreamListener(Sink.INPUT)
    public void handleEvent(OrderEvent event) { /* ... */ }
}
```

---

## 8. Spring Scheduling & Async Annotations

- **`@EnableScheduling`**
  > **Explanation:** Kickstarts Spring's background task scheduling infrastructure. Without this annotation on a `@Configuration` class, Spring simply parses `@Scheduled` annotations but ignores them, creating zero recurring threads.
- **`@Scheduled`**
  > **Explanation:** Converts any zero-argument method into an automated background job. It supports `fixedDelay` (wait X ms after the *completion* of the prior run), `fixedRate` (trigger exactly every X ms), or Unix-style `cron` configurations (`"0 0 2 * * ?"`). Caution: By default, Spring uses a single-threaded task scheduler, so a long-running job will block all other jobs unless reconfigured.
- **`@EnableAsync`**
  > **Explanation:** Wakes up Spring's asynchronous processing engine. It commands Spring to search for methods marked `@Async` and wrap them in CGLIB proxies capable of offloading executions into dedicated worker thread pools.
- **`@Async`**
  > **Explanation:** Placed on a method (usually returning `void` or `CompletableFuture`), it forces the physical execution of that method to immediately disconnect from the calling HTTP Tomcat thread and run on a detached background `ThreadPoolTaskExecutor`. Excellent for fire-and-forget logic like sending verification emails without blocking the user's web request.

```java
@Configuration
@EnableScheduling  // Enables @Scheduled methods
@EnableAsync       // Enables @Async methods
public class AsyncScheduleConfig { /* ... */ }

@Service
public class ScheduledJobs {

    @Scheduled(fixedRate = 60000)                    // Every 60s (from START of previous)
    public void heartbeat() { /* ... */ }

    @Scheduled(fixedDelay = 30000, initialDelay = 5000) // 30s after COMPLETION, 5s initial wait
    public void processQueue() { /* ... */ }

    @Scheduled(cron = "0 0 2 * * ?")                // Daily at 2 AM
    public void dailyCleanup() { /* ... */ }

    @Scheduled(cron = "0 0 9 ? * MON-FRI", zone = "Asia/Kolkata") // Weekdays 9 AM IST
    public void sendReport() { /* ... */ }
}

@Service
public class AsyncService {

    @Async                    // Runs in separate thread (default SimpleAsyncTaskExecutor)
    public void sendEmail(String to) { /* fire-and-forget */ }

    @Async("customExecutor")  // Use named executor bean
    public CompletableFuture<Report> generateReport(String type) {
        Report r = heavyComputation(type);
        return CompletableFuture.completedFuture(r); // Return result asynchronously
    }
}
```

> **Cross-Question:** *"What's the difference between fixedRate and fixedDelay?"*
> **Answer:** `fixedRate` — next execution starts N ms after **START** of previous (can overlap if method takes longer). `fixedDelay` — next execution starts N ms after **COMPLETION** of previous (no overlap). Use `fixedDelay` for sequential tasks, `fixedRate` for periodic heartbeats.

---

## 9. Spring Caching Annotations

- **`@EnableCaching`**
  > **Explanation:** Bootstraps Spring's annotation-driven cache management. Under the hood, it triggers an auto-configured `CacheManager` (e.g., Redis, Caffeine, EhCache) and generates AOP proxies around any beans that declare caching annotations, allowing Spring to transparently intercept method calls.
- **`@Cacheable`**
  > **Explanation:** A highly optimized "read-through" cache marker. When a method is called, the AOP proxy first checks the CacheManager. If the exact cache key exists, the method is bypassed entirely, and the cached JSON/object is returned. If missing, the method executes, and its `returnObject` is automatically serialized and saved into the cache. Excellent for heavy database reads.
- **`@CachePut`**
  > **Explanation:** Acts as an "update-through" cache marker. Unlike `@Cacheable`, the annotated method *always* executes. Once it finishes, the returned object is explicitly forced into the cache, overwriting any previous data for that key. Essential for `update()` methods to keep the cache in sync with the live database.
- **`@CacheEvict`**
  > **Explanation:** The "cache invalidation" annotation. Triggers the deletion of one specific key or an entire cache region (`allEntries=true`). Typically attached to `delete()` methods to ensure obsolete data doesn't persist, preventing severe data-stale anomalies in production.
- **`@Caching`**
  > **Explanation:** A composite annotation required when complex workflows demand multiple caching operations simultaneously on a single method. For example, updating a User might require a `@CacheEvict` on the `userSearchList` cache *and* a `@CachePut` on the specific `user:{id}` cache concurrently.

```java
@Configuration
@EnableCaching // Enables Spring's caching infrastructure
public class CacheConfig { /* ... */ }

@Service
public class ProductService {

    @Cacheable(value = "products", key = "#id")
    // First call → executes method, stores result in cache
    // Subsequent calls with same key → returns cached result (skips method)
    public Product findById(Long id) { return productRepo.findById(id).orElseThrow(); }

    @Cacheable(value = "products", key = "#name", unless = "#result == null")
    // unless → don't cache null results
    public Product findByName(String name) { /* ... */ }

    @Cacheable(value = "products", key = "#filter.category + '-' + #filter.page",
               condition = "#filter.page < 10")
    // condition → only cache first 10 pages
    public List<Product> search(ProductFilter filter) { /* ... */ }

    @CachePut(value = "products", key = "#product.id")
    // ALWAYS executes method AND updates cache (use for create/update)
    public Product save(Product product) { return productRepo.save(product); }

    @CacheEvict(value = "products", key = "#id")
    // Removes entry from cache
    public void delete(Long id) { productRepo.deleteById(id); }

    @CacheEvict(value = "products", allEntries = true)
    // Clears ENTIRE cache
    public void clearCache() { /* ... */ }

    @Caching(evict = {
        @CacheEvict(value = "products", key = "#product.id"),
        @CacheEvict(value = "productList", allEntries = true)
    })
    // Multiple cache operations on single method
    public Product update(Product product) { /* ... */ }
}
```

---

## 10. Spring Testing Annotations

- **`@SpringBootTest`**
  > **Explanation:** The heaviest and most profound testing annotation. It spins up the *entire* Spring `ApplicationContext`, bootstrapping every single bean exactly like a physical production start (including embedded Tomcats if `webEnvironment=RANDOM_PORT` is set). Used strictly for end-to-end integration tests.
- **`@WebMvcTest`**
  > **Explanation:** A "slice" testing annotation. Instead of loading the entire application, it specifically only instantiates Spring MVC controllers, Jackson converters, and security filters. Business services are *not* loaded and must be mocked. Highly optimized for isolating API Endpoint HTTP tests.
- **`@DataJpaTest`**
  > **Explanation:** Another "slice" testing annotation, heavily optimized for the persistence layer. It selectively boots Hibernate, Spring Data Repositories, and Flyway/Liquibase, completely ignoring Web and Service layers. Crucially, it automatically redirects the DataSource to an embedded in-memory database (like H2) and automatically rolls back all transactions after every test method to maintain pristine test state.
- **`@MockBean`**
  > **Explanation:** A Spring Boot specific fusion of Mockito and the ApplicationContext. It dynamically creates a Mockito mock, forcibly evicts the real bean from the Spring context for that test, and injects the mock globally. Essential for isolating modules (e.g., mocking an external Payment Gateway during an OrderService integration test).
- **`@SpyBean`**
  > **Explanation:** Similiar to `@MockBean`, but it creates a Mockito `Spy`. A spy wraps the *real* instantiated bean. This allows the real method logic to execute naturally, but allows test code to intercept specific calls, verify method interaction counts, or partially mock specific sub-methods.
- **`@TestConfiguration`**
  > **Explanation:** Denotes a `@Configuration` class specifically written to supplement test environments. Unlike regular configs in `src/test/java`, classes annotated with `@TestConfiguration` are completely ignored by component scanning unless explicitly imported, allowing you to narrowly inject test-specific helper beans (like Mock Mail Servers) only into designated tests.
- **`@DirtiesContext`**
  > **Explanation:** A destructive but necessary test annotation. If a specific test method permanently mutates the global ApplicationContext (e.g., physically altering a global static singleton bean or forcing a destructive property change), this annotation commands Spring Test framework to completely destroy and reboot the context for the next test class, preventing cascading test failures.

```java
// @SpringBootTest — full integration test (loads entire context)
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OrderIntegrationTest {
    @Autowired private TestRestTemplate restTemplate;
    @LocalServerPort private int port;              // Injected random port
}

// @WebMvcTest — test ONLY the web layer (controllers)
@WebMvcTest(OrderController.class) // Loads only this controller + MVC infra
class OrderControllerTest {
    @Autowired private MockMvc mockMvc;
    @MockBean private OrderService orderService;    // Mock the service
}

// @DataJpaTest — test ONLY JPA repositories
@DataJpaTest // Auto-configures H2 + EntityManager + Repos + rolls back after each test
class OrderRepositoryTest {
    @Autowired private TestEntityManager entityManager;
    @Autowired private OrderRepository orderRepo;
}

// @MockBean — replaces a bean with Mockito mock IN the context
// @SpyBean — wraps a bean with Mockito spy (partial mock)
@SpringBootTest
class PaymentTest {
    @MockBean private PaymentGateway gateway;   // Completely mocked
    @SpyBean private NotificationService notif; // Real bean, can verify calls
}

// Other testing annotations:
@TestConfiguration    // Extra config for tests only
@ActiveProfiles("test") // Activate test profile
@Sql("/test-data.sql")  // Execute SQL before test
@DirtiesContext      // Reset ApplicationContext after test class/method
@TestPropertySource(properties = "app.feature=false") // Override properties

// Unit testing — no Spring needed
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock private OrderRepository orderRepo;
    @InjectMocks private OrderService orderService;

    @Test
    void shouldCreateOrder() {
        when(orderRepo.save(any())).thenReturn(testOrder);
        Order result = orderService.create(request);
        assertThat(result).isNotNull();
        verify(orderRepo).save(any());
    }
}
```

---

## 11. Spring Validation Annotations (JSR 380)

- **`@NotNull`**, **`@NotEmpty`**, **`@NotBlank`**
  > **Explanation:** The absolute holy trinity of missing-data validation. `@NotNull` only ensures the reference isn't explicit null (allows empty strings/lists). `@NotEmpty` goes further, failing if a string length is 0 or a list has 0 elements. `@NotBlank` is the strictest: it trims strings and fails if only whitespace remains. Applies flawlessly to API JSON request bodies.
- **`@Size`**, **`@Min`**, **`@Max`**, **`@Positive`**
  > **Explanation:** Core numeric boundary validation. `@Size(min=2, max=10)` validates the length of Strings, Lists, or Maps. `@Min`/`@Max` apply to integral types (checking value bounds). `@Positive`/`@Negative` enforce that a BigDecimal or Integer strictly evaluates respectively, throwing a `400 Bad Request` if bound with `@Valid` on a controller.
- **`@Email`**, **`@Pattern`**
  > **Explanation:** Implements rigorous pattern matching. `@Email` provides RFC-compliant inbox formatting validation syntactically, while `@Pattern(regexp = "^\\d{10}$")` unlocks infinite regex matching power (e.g., strictly validating complex passwords, phone numbers, or zip codes) directly at the DTO layer.
- **`@Past`**, **`@Future`**
  > **Explanation:** Temporal validation against the physical JVM clock. `@Past(orPresent=true)` ensures a birthday or creation timestamp is logically sound. `@Future` validates that token expirations, scheduling dates, or subscription ends haven't already occurred.
- **`@Valid`**
  > **Explanation:** The master trigger switch defined by the Jakarta EE standard. When placed on a Controller parameter (e.g., `@Valid @RequestBody User user`), it commands Spring to inspect the incoming object and evaluate every internal `@NotNull` or `@Size` variable. Crucially, if placed upon an inner DTO field (like an `Address` inside a `User`), it triggers recursive descending cascade validation.
- **`@Validated`**
  > **Explanation:** Spring's proprietary superset power-up for `@Valid`. It supports complex "Validation Groups". For instance, you can dictate that `@NotNull(groups=OnUpdate.class)` only triggers during HTTP PUT requests, but is entirely ignored during HTTP POST requests to the same DTO POJO.

```java
public class UserRequest {
    @NotNull(message = "ID required for update")
    private Long id;

    @NotBlank(message = "Name is required")        // Not null + not empty + not whitespace
    @Size(min = 2, max = 100)
    private String name;

    @Email(message = "Invalid email")
    @NotEmpty
    private String email;

    @Min(18) @Max(120)
    private Integer age;

    @Positive                                       // Must be > 0
    private BigDecimal salary;

    @PositiveOrZero                                 // Must be >= 0
    private Integer experience;

    @Past                                           // Must be in the past
    private LocalDate dateOfBirth;

    @Future                                         // Must be in the future
    private LocalDate subscriptionEnd;

    @PastOrPresent
    private Instant createdAt;

    @Pattern(regexp = "^\\+[1-9]\\d{6,14}$")       // Regex validation
    private String phone;

    @NotEmpty
    @Size(min = 1, max = 5)
    private List<@NotBlank String> tags;            // Validate elements too!

    @Valid                                          // Cascade validation to nested object
    @NotNull
    private Address address;

    @AssertTrue(message = "Must accept terms")
    private Boolean termsAccepted;

    @Digits(integer = 5, fraction = 2)             // e.g., 12345.67
    private BigDecimal price;
}

// @Validated vs @Valid:
// @Valid   — JSR 380 standard, triggers cascading validation
// @Validated — Spring extension, supports VALIDATION GROUPS
@PostMapping
public User create(@Validated(OnCreate.class) @RequestBody UserRequest req) { /* ... */ }
```

---

## 12. Spring Boot 3 / Spring 6 New Annotations

- **`@HttpExchange`**, **`@GetExchange`** (etc): **Deep Dive:** Introduced in Spring 6 / Boot 3 as a native replacement to `OpenFeign`. It creates an entirely declarative approach to writing REST Clients using Java Interfaces. Simply returning a `User` from `@GetExchange("/users/{id}")` allows `HttpServiceProxyFactory` (backed by `WebClient` or newly `RestClient`) to dynamically produce the HTTP networking calls seamlessly.
- **`@AutoConfiguration`**
  > **Explanation:** Spring Boot 3's new foundational annotation strictly for infrastructure libraries. Historically, massive starter libraries used standard `@Configuration` mixed with heavy `@AutoConfigureBefore`/`After` annotations which was fragile. `@AutoConfiguration(after = DataSourceAutoConfiguration.class)` now intrinsically provides a robust, optimized, and strictly-ordered parsing engine solely dedicated to internal Boot initialization.

```java
// HTTP Interface Clients (Spring 6) — replaces Feign for simple cases
@HttpExchange("/api/users")
public interface UserClient {
    @GetExchange("/{id}")
    User getUser(@PathVariable Long id);

    @PostExchange
    User createUser(@RequestBody User user);

    @DeleteExchange("/{id}")
    void deleteUser(@PathVariable Long id);
}

// Usage:
@Configuration
public class ClientConfig {
    @Bean
    UserClient userClient(WebClient.Builder builder) {
        WebClient client = builder.baseUrl("http://user-service").build();
        return HttpServiceProxyFactory.builderFor(WebClientAdapter.create(client))
                .build().createClient(UserClient.class);
    }
}

// @AutoConfiguration (replaces @Configuration for auto-config classes)
@AutoConfiguration(after = DataSourceAutoConfiguration.class)
@ConditionalOnClass(SmsService.class)
public class SmsAutoConfiguration { /* ... */ }

// Problem Details (RFC 7807) — standardized error responses
// Built into Spring 6 — no annotation needed, just enable:
// spring.mvc.problemdetail.enabled=true

// Virtual Threads support (Java 21+)
// spring.threads.virtual.enabled=true
// All @Async, @Scheduled, request handlers use virtual threads automatically

// @Observability — built-in with Micrometer
// Auto-instruments @Controller, @Service, RestClient, JdbcTemplate
// Zero-code distributed tracing with Zipkin/Jaeger
```

---

## 13. Cross-Questions & Tricky Interview Scenarios

### Q: "What happens if @Transactional method calls another @Transactional method in the SAME class?"
> **Answer:** The second `@Transactional` is **IGNORED** — it's a self-invocation problem. Spring AOP uses proxies. When you call `this.method()`, you bypass the proxy. **Fix:** (1) Inject self with `@Lazy`. (2) Extract to a separate bean. (3) Use `TransactionTemplate` programmatically.

### Q: "Can you use @Autowired with interfaces that have multiple implementations?"
> **Answer:** Yes, with (1) `@Qualifier("beanName")`. (2) `@Primary` on one implementation. (3) `List<Interface>` — Spring injects ALL implementations. (4) `Map<String, Interface>` — bean name as key.

### Q: "What's the order of filter vs interceptor vs AOP execution?"
> **Answer:** Filter (Servlet) → DispatcherServlet → Interceptor (preHandle) → AOP (@Before) → Controller Method → AOP (@After) → Interceptor (postHandle) → Interceptor (afterCompletion) → Filter (returns).

### Q: "Difference between @Bean and @Component?"
> **Answer:** `@Component` — class-level, auto-detected by `@ComponentScan`. Used on YOUR classes. `@Bean` — method-level, explicitly declared in `@Configuration`. Used when you can't modify the class (third-party) or need custom initialization logic.

### Q: "What happens when both @Profile and @ConditionalOnProperty are on a bean?"
> **Answer:** BOTH conditions must be true. `@Profile` checks active profile, `@ConditionalOnProperty` checks config values. They are AND-ed — the bean is ONLY created if profile matches AND property condition is met.

### Q: "Can @Transactional work on private methods?"
> **Answer:** **NO** — Spring AOP proxies cannot intercept private methods. The annotation is silently ignored. Use public methods only. AspectJ compile-time weaving CAN handle private methods, but Spring's default proxy-based AOP cannot.

### Q: "What's the difference between @Controller and @RestController internally?"
> **Answer:** `@RestController` = `@Controller` + `@ResponseBody`. With `@Controller`, return value goes to `ViewResolver`. With `@RestController`, return value goes through `HttpMessageConverter` (Jackson) → JSON. You can mix both in one class using `@Controller` + `@ResponseBody` on specific methods.

### Q: "How do you handle circular dependencies?"
> **Answer:** (1) Redesign — usually a design smell. (2) `@Lazy` on one injection point. (3) Setter injection instead of constructor. (4) `@PostConstruct` initialization. (5) `ObjectProvider<T>`. Spring Boot 2.6+ disables circular references by default — `spring.main.allow-circular-references=true` to re-enable (not recommended).

### Q: "List all annotations you'd use in a typical Spring Boot REST controller"
> **Answer:** Class level: `@RestController`, `@RequestMapping`, `@CrossOrigin`, `@Validated`, `@Slf4j`. Method level: `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@ResponseStatus`. Parameter level: `@PathVariable`, `@RequestParam`, `@RequestBody`, `@RequestHeader`, `@Valid`. Exception: `@ExceptionHandler`. Security: `@PreAuthorize`.

---

## 14. Spring Application Events Annotations

- **`@EventListener`**
  > **Explanation:** Eliminates the necessity to implement the legacy `ApplicationListener<E>` interface. By placing this on a standard bean method, Spring automatically detects it and routes any `ApplicationEvent` published (via `ApplicationEventPublisher`) matching the method's argument type. Excellent for designing decoupled, event-driven internal architectures where domain services broadcast state-changes silently.
- **`@TransactionalEventListener`**
  > **Explanation:** A highly specialized expansion of `@EventListener` crucial for data consistency. It binds the execution of the listener to a specific phase of the active transaction (default is `AFTER_COMMIT`). If the upstream transaction rolls back because of an error, this listener fundamentally *aborts* execution. Use this exclusively for triggering irreversible side-effects (like dispatching SMS or Kafka messages) so they only trigger if the database write is absolutely finalized.

```java
// Spring's event-driven model decouples components — publisher doesn't know about listeners

// @EventListener — listen for application events (replacement for ApplicationListener interface)
@Component
public class OrderEventHandler {

    @EventListener // Listens for OrderPlacedEvent
    public void onOrderPlaced(OrderPlacedEvent event) {
        log.info("Order placed: {}", event.getOrderId());
        emailService.sendConfirmation(event);
    }

    @EventListener(condition = "#event.amount > 10000") // Conditional — fires only for large orders
    public void onLargeOrder(OrderPlacedEvent event) {
        alertService.notifyManager(event);
    }

    @EventListener({OrderPlacedEvent.class, OrderCancelledEvent.class}) // Multiple event types
    public void onAnyOrderEvent(Object event) { /* ... */ }
}

// @TransactionalEventListener — fires ONLY after transaction commits/rollbacks
@Component
public class AnalyticsHandler {

    @TransactionalEventListener(phase = TransactionPhase.AFTER_COMMIT)
    // Phases: BEFORE_COMMIT, AFTER_COMMIT (default), AFTER_ROLLBACK, AFTER_COMPLETION
    public void trackOrder(OrderPlacedEvent event) {
        // SAFE: Only runs if order was actually saved to DB
        // If transaction rolls back → this listener NEVER fires
        analyticsService.trackRevenue(event.getAmount());
    }

    @TransactionalEventListener(phase = TransactionPhase.AFTER_ROLLBACK)
    public void onOrderFailed(OrderPlacedEvent event) {
        monitoringService.reportFailure(event.getOrderId());
    }
}

// Publishing custom events
@Service
public class OrderService {
    private final ApplicationEventPublisher publisher;

    @Transactional
    public Order placeOrder(OrderRequest req) {
        Order order = orderRepo.save(toEntity(req));
        publisher.publishEvent(new OrderPlacedEvent(this, order)); // Publish!
        return order;
    }
}

// Built-in Spring Events you can listen for:
@Component
public class AppLifecycleListener {
    @EventListener
    public void onStartup(ApplicationReadyEvent event) {
        log.info("Application is ready! Port: {}", event.getApplicationContext()
                .getEnvironment().getProperty("server.port"));
    }

    @EventListener
    public void onStarted(ApplicationStartedEvent event) { /* After context refresh, before runners */ }

    @EventListener
    public void onContextRefresh(ContextRefreshedEvent event) { /* Context refreshed */ }

    @EventListener
    public void onContextClosed(ContextClosedEvent event) { /* Graceful shutdown */ }

    @EventListener
    public void onServletReady(ServletWebServerInitializedEvent event) {
        int port = event.getWebServer().getPort(); // Get actual port
    }
}
```

> **Cross-Question:** *"What's the difference between @EventListener and @TransactionalEventListener?"*
> **Answer:** `@EventListener` fires **immediately** when `publishEvent()` is called — even if the transaction hasn't committed yet. If the TX rolls back, the listener has already executed (notification sent for order that doesn't exist!). `@TransactionalEventListener` with `AFTER_COMMIT` waits until the transaction succeeds. **Always use @TransactionalEventListener for side-effects** like emails, notifications, analytics.

---

## 15. @Transactional — Complete Propagation & Isolation Reference

- **`@Transactional`**
  > **Explanation:** The cornerstone of Spring's declarative data integrity. When applied, Spring AOP dynamically creates a proxy that opens a database connection, begins a transaction, executes the method, and either commits (on success) or rolls back (if a `RuntimeException` is thrown). It exposes rigid control parameters like `propagation` (how boundaries merge or suspend existing transactions) and `isolation` (mitigating dirty reads and phantom reads dynamically at the DB engine).
- **`@EnableTransactionManagement`**
  > **Explanation:** The global activator that commands the Spring `ApplicationContext` to search for `@Transactional` annotations. Note: Spring Boot automatically engages this mechanism if spring-data or spring-tx are detected on the classpath; manual inclusion is generally only required in highly customized config modules or pure vanilla Spring MVC setups.

```java
// PROPAGATION TYPES — what happens when a transactional method calls another transactional method

@Service
public class TransactionDemo {

    @Transactional(propagation = Propagation.REQUIRED)    // DEFAULT
    // Outer TX exists → JOIN it. No outer TX → CREATE new.
    public void required() { /* ... */ }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    // ALWAYS creates a NEW transaction. Outer TX is SUSPENDED.
    // Use for: audit logs, independent operations
    public void requiresNew() { /* ... */ }

    @Transactional(propagation = Propagation.NESTED)
    // Creates a SAVEPOINT within the outer TX.
    // If inner fails → rolls back to savepoint (outer continues).
    public void nested() { /* ... */ }

    @Transactional(propagation = Propagation.SUPPORTS)
    // Outer TX exists → JOIN it. No outer TX → run WITHOUT TX.
    public void supports() { /* ... */ }

    @Transactional(propagation = Propagation.NOT_SUPPORTED)
    // SUSPENDS outer TX. Always runs WITHOUT TX.
    public void notSupported() { /* ... */ }

    @Transactional(propagation = Propagation.MANDATORY)
    // REQUIRES existing TX. If no outer TX → throws exception!
    public void mandatory() { /* ... */ }

    @Transactional(propagation = Propagation.NEVER)
    // Must NOT run in a TX. If outer TX exists → throws exception!
    public void never() { /* ... */ }
}

// ISOLATION LEVELS
@Transactional(isolation = Isolation.READ_UNCOMMITTED)  // Allows dirty reads
@Transactional(isolation = Isolation.READ_COMMITTED)    // DEFAULT for PostgreSQL
@Transactional(isolation = Isolation.REPEATABLE_READ)   // DEFAULT for MySQL
@Transactional(isolation = Isolation.SERIALIZABLE)      // Strictest — full table lock

// ROLLBACK rules
@Transactional(rollbackFor = Exception.class)           // Rollback on ALL exceptions
@Transactional(rollbackFor = {IOException.class, SQLException.class}) // Specific
@Transactional(noRollbackFor = EmailException.class)    // Don't rollback for email failure

// READ-ONLY optimization
@Transactional(readOnly = true)
// Hibernate skips dirty-checking, DB may route to read-replica

// TIMEOUT
@Transactional(timeout = 10) // 10 seconds — throws TransactionTimedOutException

// @EnableTransactionManagement — enables @Transactional processing
@Configuration
@EnableTransactionManagement
public class TransactionConfig { /* Auto-configured by Spring Boot */ }
```

### Propagation Matrix:

| Propagation | Outer TX Exists | Outer TX Absent |
|-------------|----------------|-----------------|
| `REQUIRED` | Join existing | Create new |
| `REQUIRES_NEW` | Suspend, create new | Create new |
| `NESTED` | Create savepoint | Create new |
| `SUPPORTS` | Join existing | Run without TX |
| `NOT_SUPPORTED` | Suspend, run without TX | Run without TX |
| `MANDATORY` | Join existing | ❌ Exception! |
| `NEVER` | ❌ Exception! | Run without TX |

> **Cross-Question:** *"When would you use REQUIRES_NEW vs NESTED?"*
> **Answer:** `REQUIRES_NEW` — completely independent transaction. If inner commits and outer rolls back, inner changes are KEPT. Use for **audit logs**. `NESTED` — savepoint within outer TX. If inner rolls back, only inner changes are lost; outer can continue. If outer rolls back, inner is also rolled back. Use when you want **partial rollback** capability.

---

## 16. Spring Actuator Annotations

- **`@Endpoint`**
  > **Explanation:** Promotes a standard bean into a first-class Spring Boot Actuator component. Instead of writing standard `@RestController` endpoints mapping to `/api/v1/health`, utilizing `@Endpoint(id="my-metrics")` safely registers your operational logic natively under the Actuator pathway (e.g., `/actuator/my-metrics`), inheriting all globally defined Actuator security and exposure configurations automatically. (Exposed on both JMX and HTTP).
- **`@ReadOperation`**, **`@WriteOperation`**, **`@DeleteOperation`**
  > **Explanation:** Strictly bound to `@Endpoint` classes, these dictate the operation mapping. A `@ReadOperation` method is implicitly mapped to an HTTP `GET`, `@WriteOperation` strictly expects an HTTP `POST` (typically sending JSON in the body), and `@DeleteOperation` maps to HTTP `DELETE`. It provides a technology-agnostic interface abstracting away standard Servlet semantics.
- **`@WebEndpoint`**
  > **Explanation:** Identical functionality to `@Endpoint`, but explicitly restricts this component exclusively to HTTP traffic (Restricting JMX exposure completely). Ideal if your tooling/infrastructure accesses Actuator purely via REST.
- **`@Timed`**, **`@Counted`**
  > **Explanation:** Provided by Micrometer (Spring's observability engine). Placing `@Timed` on an endpoint instructs Spring to wrap the method and precisely calculate its execution latency percentiles (p95, p99). Placing `@Counted` tracks invocation counts. Both publish this telemetry natively to Prometheus endpoints (`/actuator/prometheus`) with zero manual gauge coding.

```java
// @Endpoint — create custom actuator endpoints
@Component
@Endpoint(id = "app-info")  // Accessible at /actuator/app-info
public class AppInfoEndpoint {

    @ReadOperation   // HTTP GET /actuator/app-info
    public Map<String, Object> info() {
        return Map.of(
            "version", "2.5.0",
            "uptime", ManagementFactory.getRuntimeMXBean().getUptime(),
            "javaVersion", System.getProperty("java.version")
        );
    }

    @ReadOperation   // HTTP GET /actuator/app-info/{component}
    public Map<String, String> component(@Selector String component) {
        return Map.of("component", component, "status", "UP");
    }

    @WriteOperation  // HTTP POST /actuator/app-info
    public String update(@Selector String key, String value) {
        return "Updated " + key + " to " + value;
    }

    @DeleteOperation // HTTP DELETE /actuator/app-info/{key}
    public String delete(@Selector String key) {
        return "Deleted " + key;
    }
}

// @WebEndpoint — endpoint exposed ONLY over HTTP (not JMX)
@Component
@WebEndpoint(id = "custom-health")
public class CustomHealthEndpoint { /* ... */ }

// @RestControllerEndpoint — full Spring MVC endpoint with actuator integration
@Component
@RestControllerEndpoint(id = "admin-panel")
public class AdminEndpoint {
    @GetMapping("/stats")
    public Map<String, Object> getStats() { return statsService.getAll(); }
}

// @Timed — Micrometer annotation for auto-timing methods
@RestController
public class OrderController {
    @Timed(value = "order.creation.time", description = "Time to create orders")
    @PostMapping("/api/orders")
    public Order create(@RequestBody OrderRequest req) { /* ... */ }
}

// @Counted — Micrometer annotation for auto-counting method invocations
@Service
public class PaymentService {
    @Counted(value = "payment.processed", description = "Payments processed")
    public void process(Payment payment) { /* ... */ }
}
```

---

## 17. Spring Cloud Config & Refresh Annotations

- **`@RefreshScope`**
  > **Explanation:** An extraordinary lifesaver in modern Cloud-Native environments. When a bean is annotated with `@RefreshScope`, Spring wraps it in a special proxy. If a developer pushes a configuration change to Git/Consul and hits the `/actuator/refresh` endpoint, Spring actually destroys that specific proxy and seamlessly constructs a new bean instance injected with the newest properties—all without suffering a full JVM downtime/restart.
- **`@EnableConfigServer`**
  > **Explanation:** Converts a basic Spring Boot container into a distributed Configuration Authority. The resulting application natively pulls `.yml` files from Git remotes or HashiCorp Vault instances and serves them securely over REST to all other microservices in your architecture scaling horizontally, standardizing the 12-Factor App design methodology natively.

```java
// @RefreshScope — bean is RECREATED when /actuator/refresh is called
// Used with Spring Cloud Config for dynamic property reload WITHOUT restart
@Component
@RefreshScope
@ConfigurationProperties("app.feature-flags")
public class FeatureFlags {
    private boolean darkMode;
    private boolean betaFeatures;
    private int maxRetries;
    // When /actuator/refresh is called → new FeatureFlags instance with updated values
}

// @EnableConfigServer — marks app as Spring Cloud Config Server
@SpringBootApplication
@EnableConfigServer
public class ConfigServerApp { /* ... */ }

// @EnableConfigurationProperties — used to bind @ConfigurationProperties to Spring context
@SpringBootApplication
@EnableConfigurationProperties({AppProperties.class, SecurityProperties.class})
public class MyApp { /* ... */ }
```

---

## 18. Spring Aware Interfaces (Callback Annotations)

- **`ApplicationContextAware`**, **`EnvironmentAware`**, **`ResourceLoaderAware`**
  > **Explanation:** While strictly interfaces and not annotations, they serve a vital callback mechanism. By implementing them, Spring's `BeanPostProcessor` lifecycle guarantees that the required core framework object (like the `ApplicationContext` itself) is forcefully injected into your bean via a setter execution shortly after initialization. This is a powerful backdoor when normal `@Autowired` fails due to circular dependencies or when writing custom deep-framework integration code.

```java
// These interfaces allow beans to be AWARE of their container environment
// Spring calls the setter methods automatically after injection

@Component
public class ContextAwareBean implements
        ApplicationContextAware,   // Access to ApplicationContext
        BeanNameAware,             // Know your own bean name
        BeanFactoryAware,          // Access to BeanFactory
        EnvironmentAware,          // Access to Environment (profiles, properties)
        ResourceLoaderAware,       // Load resources (classpath:, file:, etc.)
        ApplicationEventPublisherAware, // Publish events manually
        MessageSourceAware,        // Access i18n MessageSource
        ServletContextAware {      // Access ServletContext (web apps)

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        // Programmatic access to Spring container
        PaymentService ps = ctx.getBean(PaymentService.class);
    }

    @Override
    public void setBeanName(String name) {
        log.info("My bean name is: {}", name);
    }

    @Override
    public void setEnvironment(Environment env) {
        String profile = env.getActiveProfiles()[0];
        String dbUrl = env.getProperty("spring.datasource.url");
    }

    @Override
    public void setResourceLoader(ResourceLoader loader) {
        Resource resource = loader.getResource("classpath:data/initial.json");
    }
    // ... other setters
}

// MODERN ALTERNATIVE: Just inject directly (preferred in Spring Boot)
@Component
public class ModernBean {
    private final ApplicationContext ctx;        // Inject via constructor
    private final Environment env;

    public ModernBean(ApplicationContext ctx, Environment env) {
        this.ctx = ctx;
        this.env = env;
    }
}
```

> **Cross-Question:** *"When would you use Aware interfaces instead of just @Autowired injection?"*
> **Answer:** In most cases, use `@Autowired`/constructor injection — it's cleaner. Use Aware interfaces when: (1) Building **framework code** or libraries. (2) Need access during **very early bean lifecycle** (before full DI). (3) Building custom `BeanPostProcessor` or `BeanFactoryPostProcessor`. In application code, constructor injection is always preferred.

---

## 19. Lombok Annotations Commonly Used with Spring

- **`@Data`**, **`@Getter`**, **`@Setter`**
  > **Explanation:** Eliminates standard Java boilerplate. `@Data` is a heavy aggregation that injects getters, setters for all non-final fields, an aggressive `equals()` and `hashCode()`, and a comprehensive `toString()`. **Caution:** Never use `@Data` on JPA Entities; the generated `equals()/hashCode()` frequently breaks Hibernate proxies and triggers `StackOverflowException` via infinite relationship recursion.
- **`@NoArgsConstructor`**, **`@AllArgsConstructor`**, **`@RequiredArgsConstructor`**
  > **Explanation:** Generates AST-level constructors. `@RequiredArgsConstructor` is the de-facto standard in modern Spring APIs. When coupled with `private final Dependency dependency;`, it automatically generates a constructor binding that dependency. Spring natively detects this single constructor and autowires dependencies without needing the `@Autowired` annotation.
- **`@Builder`**
  > **Explanation:** Instantly applies the Gang of Four Builder creational pattern to a class. It creates an inner static builder class allowing fluent, chained object construction (`User.builder().id(1).name("Bob").build()`). Highly desirable for constructing massive test fixture objects cleanly or maintaining immutability.
- **`@Slf4j`**
  > **Explanation:** Injects `private static final org.slf4j.Logger log = org.slf4j.LoggerFactory.getLogger(YourClass.class);` implicitly into your class. This removes the repetitive logger declaration ritual and standardizes logging handles purely on `log.info(...)`.
- **`@Value`** (Lombok): **Deep Dive:** The immutable sibling of `@Data`. It mandates every field as `private final`, generates getters (but critically *no setters*), and produces a complete All-Args constructor. Extremely useful for constructing thread-safe Response DTOs. Do not confuse this interface with Spring's `@Value` property injection annotation!

```java
// Lombok reduces boilerplate — critical for Spring development

@Data           // Generates getters, setters, toString, equals, hashCode
@Builder        // Builder pattern: User.builder().name("John").build()
@NoArgsConstructor  // Required by JPA entities
@AllArgsConstructor // All-args constructor
@Entity
public class User {
    @Id @GeneratedValue
    private Long id;
    private String name;
    private String email;
}

@Service
@RequiredArgsConstructor  // Constructor for all FINAL fields → enables constructor injection
@Slf4j                    // Creates: private static final Logger log = LoggerFactory.getLogger(...)
public class OrderService {
    private final OrderRepository orderRepo;     // Injected via generated constructor
    private final PaymentGateway gateway;        // Injected via generated constructor

    public Order process(OrderRequest req) {
        log.info("Processing order: {}", req.getId()); // @Slf4j provides 'log'
        return orderRepo.save(toEntity(req));
    }
}

@Getter @Setter          // Only getters and setters (not full @Data)
@ToString(exclude = "password") // Exclude sensitive fields from toString
@EqualsAndHashCode(of = "id")  // Only use 'id' for equality
@Entity
public class Account { /* ... */ }

// @Value (Lombok) — IMMUTABLE class (do NOT confuse with Spring's @Value)
@lombok.Value  // All fields are private final, generated all-args constructor
public class OrderResponse {
    String orderId;
    BigDecimal amount;
    OrderStatus status;
}

// @With — immutable copy with one field changed
@With
@lombok.Value
public class Config {
    String host;
    int port;
}
// Config newConfig = config.withPort(9090); // Returns new instance
```

> **Cross-Question:** *"Why do JPA entities need @NoArgsConstructor?"*
> **Answer:** JPA (Hibernate) uses **reflection** to instantiate entities. It needs a no-args constructor to create objects before setting fields. `@NoArgsConstructor(access = AccessLevel.PROTECTED)` is best — satisfies JPA while discouraging direct use. `@AllArgsConstructor` or `@Builder` can be added for application code.

---

## 20. Spring WebSocket Annotations

- **`@EnableWebSocketMessageBroker`**
  > **Explanation:** Activates Spring's high-level WebSocket message routing. Instead of dealing with raw text payloads over low-level sockets, this configures an internal STOMP (Simple Text Oriented Message Protocol) sub-protocol, bridging WebSocket semantics explicitly into Spring MVC.
- **`@MessageMapping`**
  > **Explanation:** Conceptually identically to `@RequestMapping`, but for WebSocket datagrams instead of HTTP. If a client transmits a STOMP payload marked for `/chat.send`, a controller method annotated with `@MessageMapping("/chat.send")` effortlessly intercepts it, parsing the payload into a Java object automatically.
- **`@SendTo`**
  > **Explanation:** A broadcast declarative. Whatever object the `@MessageMapping` method returns will be converted to JSON and immediately blasted over the WebSocket broker to *every single connected user* currently subscribed to the destination specified within this annotation (e.g., `/topic/all`).
- **`@SendToUser`**
  > **Explanation:** The unicast equivalent to `@SendTo`. Instead of broadcasting globally, Spring examines the internal STOMP session headers, locates the unique session queue belonging strictly to the user who fired the initial mapping message, and routes the response confidentially back to them exclusively.
- **`@SubscribeMapping`**
  > **Explanation:** An interceptor for the initial client handshake. When a JavaScript client sends a STOMP `SUBSCRIBE` command to a specific topic, this method fires, evaluates logic, and returns a payload synchronously *once*. Often utilized to dump historical chat messages instantly upon joining a room.

```java
@Configuration
@EnableWebSocketMessageBroker // Enable STOMP over WebSocket
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {
    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws").withSockJS();
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic", "/queue");
        registry.setApplicationDestinationPrefixes("/app");
    }
}

@Controller
public class ChatController {

    @MessageMapping("/chat.send")     // Handles messages sent to /app/chat.send
    @SendTo("/topic/public")          // Broadcasts to all subscribers of /topic/public
    public ChatMessage sendMessage(ChatMessage message) {
        return message;
    }

    @MessageMapping("/chat.private")
    @SendToUser("/queue/reply")       // Sends to SPECIFIC user's queue
    public ChatMessage privateMessage(ChatMessage message, Principal principal) {
        return message;
    }

    @SubscribeMapping("/initial-data") // Responds when user first subscribes
    public List<ChatMessage> getHistory() {
        return chatService.getRecentMessages();
    }
}

// @EnableWebSocket — for raw WebSocket (without STOMP)
@Configuration
@EnableWebSocket
public class RawWebSocketConfig implements WebSocketConfigurer {
    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(myHandler(), "/raw-ws");
    }
}
```

---

## 21. Spring Batch Annotations

- **`@EnableBatchProcessing`**
  > **Explanation:** Modifies the ApplicationContext slightly to register several critical Spring Batch pipeline components explicitly, primarily injecting bean definitions for `JobRepository`, `JobLauncher`, and `JobRegistry`, which manage the persisted metadata (status, chunks) of massive ETL background jobs.
- **`@StepScope`**
  > **Explanation:** A crucial workaround for Batch architecture. When you define `ItemReader` or `ItemWriter` beans, you often need to pass runtime Job parameters (like an execution date or filename) that aren't known when the JVM starts. `@StepScope` delays the physical instantiation of that bean until the specific batch `Step` actually commences execution, allowing `@Value("#{jobParameters['file']}")` evaluations to resolve correctly.
- **`@JobScope`**
  > **Explanation:** Identical concept to `@StepScope`, but tied to the overarching `Job` execution lifespan. It ensures stateful beans (like cumulative calculation tools or caching stores) are freshly instantiated each time a Job starts and destroyed cleanly upon completion, eliminating cross-contamination between scheduled job runs.

```java
@Configuration
@EnableBatchProcessing // Enables Spring Batch infrastructure (JobRepository, JobLauncher)
public class BatchConfig {

    @Bean
    public Job importJob(JobRepository jobRepository, Step step1, Step step2) {
        return new JobBuilder("importJob", jobRepository)
                .start(step1)
                .next(step2)
                .build();
    }

    @Bean
    public Step step1(JobRepository jobRepository, PlatformTransactionManager txManager) {
        return new StepBuilder("step1", jobRepository)
                .<InputRecord, OutputRecord>chunk(100, txManager) // Process 100 records at a time
                .reader(reader())
                .processor(processor())
                .writer(writer())
                .build();
    }

    @Bean
    @StepScope // Bean scoped to a step execution — allows late binding of job parameters
    public FlatFileItemReader<InputRecord> reader(
            @Value("#{jobParameters['inputFile']}") String file) {
        // @Value with jobParameters — only works with @StepScope!
        return new FlatFileItemReaderBuilder<InputRecord>()
                .name("reader")
                .resource(new FileSystemResource(file))
                .delimited().names("id", "name", "amount")
                .targetType(InputRecord.class)
                .build();
    }

    @Bean
    @JobScope // Bean scoped to a job execution
    public MyTasklet cleanupTasklet(@Value("#{jobParameters['date']}") String date) {
        return new MyTasklet(date);
    }
}
```

---

## 22. Additional Cross-Questions & Tricky Scenarios

### Q: "How does Spring handle thread safety for singleton beans?"
> **Answer:** Spring does NOT make singletons thread-safe. Since singletons are shared across threads: (1) Don't store mutable request-specific state. (2) Use local variables (stack-confined). (3) For shared state, use `ConcurrentHashMap`, `AtomicInteger`, `synchronized`. (4) For request data, use `@Scope(SCOPE_REQUEST)` or `ThreadLocal`. Most service beans are stateless (no mutable fields) = inherently thread-safe.

### Q: "What is @EventListener vs implementing ApplicationListener interface?"
> **Answer:** `ApplicationListener<T>` is the old interface approach — requires implementing the interface and registering as bean. `@EventListener` is annotation-based (Spring 4.2+) — more flexible: supports SpEL conditions, multiple events, return-based event chaining. Always prefer `@EventListener`.

### Q: "How do you make @Scheduled work in a clustered environment?"
> **Answer:** `@Scheduled` runs on EVERY instance in a cluster — causing duplicate executions! Solutions: (1) **ShedLock** — distributed lock using DB/Redis/Zookeeper. (2) **Quartz Scheduler** with JDBC store for cluster-aware scheduling. (3) **Leader election** — only one instance runs scheduled tasks. (4) **Spring Cloud Task** for one-off executions.

### Q: "What's @RefreshScope and when do you use it?"
> **Answer:** `@RefreshScope` (Spring Cloud) recreates a bean when `/actuator/refresh` is hit. Without it, `@ConfigurationProperties` beans cache values at startup. With `@RefreshScope`, you can change config in Config Server and refresh without restart. Internally, it creates a proxy that discards the old bean and creates a new one with updated properties.

### Q: "Difference between @Qualifier, @Primary, and @Conditional?"
> **Answer:** `@Primary` — one default bean among multiple candidates (automatic selection). `@Qualifier` — explicit selection by name at injection point. `@Conditional*` — controls WHETHER a bean is created at all. Precedence: `@Conditional` decides if bean exists → `@Primary` sets default → `@Qualifier` overrides at injection point.

### Q: "What annotations does Spring Boot auto-apply that you never see?"
> **Answer:** Many! `@EnableAutoConfiguration` triggers: `DataSourceAutoConfiguration` (HikariCP), `JpaRepositoriesAutoConfiguration` (scans `@Repository`), `WebMvcAutoConfiguration` (DispatcherServlet, Jackson), `SecurityAutoConfiguration` (basic security), `CacheAutoConfiguration`, `AopAutoConfiguration` (CGLIB proxies). That's why Spring Boot "just works" with minimal config.

### Q: "Can you use @Async on the same method as @Transactional?"
> **Answer:** Yes, but be careful! `@Async` makes the method run in a different thread — the transaction context is NOT propagated. The async method runs in its own transaction (if `@Transactional` is on it). The caller's transaction doesn't wait for the async method. This is fine for fire-and-forget operations but dangerous if you need atomicity.

### Q: "What's the difference between @Component, @Bean and @Import?"
> **Answer:** `@Component` — class-level, auto-scanned. `@Bean` — method-level in `@Configuration`, manual control over instantiation. `@Import` — brings another `@Configuration` class into the context, useful for modular config. All three register beans, but at different abstraction levels.

---

## 📊 Quick Reference — All Annotations by Category

| Category | Key Annotations |
|----------|----------------|
| **Stereotype** | `@Component`, `@Service`, `@Repository`, `@Controller`, `@RestController` |
| **Config** | `@Configuration`, `@Bean`, `@Import`, `@PropertySource`, `@Profile`, `@ConfigurationPropertiesScan` |
| **DI** | `@Autowired`, `@Qualifier`, `@Primary`, `@Value`, `@Lazy`, `@ConfigurationProperties`, `@Lookup` |
| **Lifecycle** | `@PostConstruct`, `@PreDestroy`, `@Scope`, `@DependsOn`, `@Order` |
| **Boot** | `@SpringBootApplication`, `@EnableAutoConfiguration`, `@ComponentScan`, `@ConditionalOn*` |
| **Web** | `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping` |
| **Params** | `@PathVariable`, `@RequestParam`, `@RequestBody`, `@RequestHeader`, `@CookieValue`, `@ModelAttribute`, `@MatrixVariable` |
| **Response** | `@ResponseBody`, `@ResponseStatus`, `@CrossOrigin` |
| **Exception** | `@ExceptionHandler`, `@ControllerAdvice`, `@RestControllerAdvice` |
| **JPA Entity** | `@Entity`, `@Table`, `@Id`, `@GeneratedValue`, `@Column`, `@Enumerated`, `@Lob`, `@Transient`, `@Version`, `@Temporal` |
| **JPA Relations** | `@OneToOne`, `@OneToMany`, `@ManyToOne`, `@ManyToMany`, `@JoinColumn`, `@JoinTable`, `@ElementCollection` |
| **JPA Embedded** | `@Embeddable`, `@Embedded`, `@AttributeOverride`, `@AttributeOverrides` |
| **JPA Inheritance** | `@Inheritance`, `@DiscriminatorColumn`, `@DiscriminatorValue`, `@MappedSuperclass` |
| **JPA Query** | `@Query`, `@Modifying`, `@Param`, `@NamedQuery`, `@EntityGraph`, `@Lock`, `@PersistenceContext` |
| **JPA Audit** | `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`, `@LastModifiedBy`, `@EnableJpaAuditing`, `@EntityListeners` |
| **Transaction** | `@Transactional`, `@EnableTransactionManagement` (Propagation, Isolation, rollbackFor, readOnly, timeout) |
| **Security** | `@EnableWebSecurity`, `@EnableMethodSecurity`, `@PreAuthorize`, `@PostAuthorize`, `@PreFilter`, `@PostFilter`, `@Secured`, `@RolesAllowed`, `@AuthenticationPrincipal`, `@WithMockUser` |
| **AOP** | `@Aspect`, `@Pointcut`, `@Before`, `@After`, `@AfterReturning`, `@AfterThrowing`, `@Around`, `@EnableAspectJAutoProxy` |
| **Events** | `@EventListener`, `@TransactionalEventListener`, `ApplicationEventPublisherAware` |
| **Cache** | `@EnableCaching`, `@Cacheable`, `@CachePut`, `@CacheEvict`, `@Caching` |
| **Schedule** | `@EnableScheduling`, `@Scheduled`, `@EnableAsync`, `@Async` |
| **Cloud** | `@EnableEurekaServer`, `@EnableDiscoveryClient`, `@EnableConfigServer`, `@FeignClient`, `@EnableFeignClients`, `@RefreshScope` |
| **Resilience** | `@CircuitBreaker`, `@Retry`, `@RateLimiter`, `@Bulkhead`, `@TimeLimiter` |
| **Validation** | `@Valid`, `@Validated`, `@NotNull`, `@NotBlank`, `@NotEmpty`, `@Size`, `@Min`, `@Max`, `@Email`, `@Pattern`, `@Past`, `@Future`, `@Positive`, `@Digits`, `@AssertTrue`, `@Constraint` |
| **Actuator** | `@Endpoint`, `@ReadOperation`, `@WriteOperation`, `@DeleteOperation`, `@WebEndpoint`, `@Selector`, `@Timed`, `@Counted` |
| **WebSocket** | `@EnableWebSocketMessageBroker`, `@MessageMapping`, `@SendTo`, `@SendToUser`, `@SubscribeMapping` |
| **Batch** | `@EnableBatchProcessing`, `@StepScope`, `@JobScope` |
| **Test** | `@SpringBootTest`, `@WebMvcTest`, `@DataJpaTest`, `@MockBean`, `@SpyBean`, `@ActiveProfiles`, `@TestConfiguration`, `@Sql`, `@DirtiesContext`, `@TestPropertySource` |
| **Lombok** | `@Data`, `@Builder`, `@AllArgsConstructor`, `@NoArgsConstructor`, `@RequiredArgsConstructor`, `@Slf4j`, `@Getter`, `@Setter`, `@ToString`, `@EqualsAndHashCode`, `@With` |
| **Spring 6** | `@HttpExchange`, `@GetExchange`, `@PostExchange`, `@DeleteExchange`, `@AutoConfiguration` |

---

> **📌 Total Annotations Covered: 175+** — This is the most comprehensive Spring Boot annotations guide covering Core Spring, Spring Boot, MVC, JPA, Security, AOP, Cloud, Events, Actuator, WebSocket, Batch, Testing, Validation, and Lombok. Every annotation includes **why** and **where** to use it, with **cross-questions** for interview readiness.
