# 🧪 Testing & Quality — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Software Testing?

Software testing is the process of verifying that your application **works correctly** and **meets requirements**. For a senior developer, testing is not an afterthought — it's a **design tool** that drives better architecture.

### Testing Pyramid:
```
              ┌─────────┐
              │ E2E/UI  │  ← Fewest (slow, brittle, expensive)
             ┌┴─────────┴┐
             │Integration │  ← Some (test service interactions)
            ┌┴────────────┴┐
            │  Unit Tests   │  ← Most tests (fast, isolated, cheap)
            └───────────────┘

Rule of thumb:
- 70% Unit Tests (fast, milliseconds each)
- 20% Integration Tests (test with real DB, Kafka, etc.)
- 10% E2E Tests (Selenium, full user flow)
```

---

## 📖 Unit Testing (JUnit 5 + Mockito)

### Theory:
A **unit test** tests a **single unit of code** (usually a method) in **isolation**. Dependencies are replaced with **mocks** (fake objects). Unit tests should be:
- **Fast** (run in milliseconds)
- **Independent** (no order dependency)
- **Repeatable** (same result every time, no external state)
- **Self-validating** (pass/fail, no manual checking)

```java
// What to test: Business logic, validation, transformations, calculations
// What NOT to test: Getters/setters, framework code, third-party libraries

@ExtendWith(MockitoExtension.class)
class PaymentServiceTest {

    @Mock
    private PaymentRepository paymentRepo;

    @Mock
    private PaymentGateway gateway;

    @Mock
    private KafkaTemplate<String, PaymentEvent> kafkaTemplate;

    @InjectMocks
    private PaymentService paymentService;

    @Captor
    private ArgumentCaptor<Payment> paymentCaptor;

    @Test
    @DisplayName("Should process valid payment and publish event")
    void processPayment_ValidRequest_Success() {
        // ARRANGE (Given)
        PaymentRequest request = new PaymentRequest("TX001", BigDecimal.valueOf(100), "USD");
        GatewayResponse gatewayResponse = new GatewayResponse("GW-123", "SUCCESS");
        when(gateway.charge(any())).thenReturn(gatewayResponse);
        when(paymentRepo.save(any())).thenAnswer(inv -> inv.getArgument(0));

        // ACT (When)
        PaymentResult result = paymentService.process(request);

        // ASSERT (Then)
        assertThat(result.getStatus()).isEqualTo("SUCCESS");
        assertThat(result.getTransactionId()).isEqualTo("GW-123");

        // Verify interactions
        verify(paymentRepo).save(paymentCaptor.capture());
        Payment savedPayment = paymentCaptor.getValue();
        assertThat(savedPayment.getAmount()).isEqualByComparingTo(BigDecimal.valueOf(100));
        assertThat(savedPayment.getCurrency()).isEqualTo("USD");

        verify(kafkaTemplate).send(eq("payment-events"), any(PaymentEvent.class));
    }

    @Test
    @DisplayName("Should throw exception for negative amount")
    void processPayment_NegativeAmount_ThrowsException() {
        PaymentRequest request = new PaymentRequest("TX002", BigDecimal.valueOf(-50), "USD");

        assertThatThrownBy(() -> paymentService.process(request))
            .isInstanceOf(InvalidPaymentException.class)
            .hasMessageContaining("Amount must be positive");

        verify(gateway, never()).charge(any()); // Gateway never called
        verify(paymentRepo, never()).save(any()); // Nothing saved
    }

    @Test
    @DisplayName("Should retry on gateway timeout and eventually succeed")
    void processPayment_GatewayTimeout_RetriesAndSucceeds() {
        PaymentRequest request = new PaymentRequest("TX003", BigDecimal.TEN, "USD");
        when(gateway.charge(any()))
            .thenThrow(new GatewayTimeoutException()) // First call fails
            .thenReturn(new GatewayResponse("GW-456", "SUCCESS")); // Second succeeds

        PaymentResult result = paymentService.process(request);

        assertThat(result.getStatus()).isEqualTo("SUCCESS");
        verify(gateway, times(2)).charge(any()); // Called twice
    }

    @ParameterizedTest
    @ValueSource(strings = {"", " ", "   "})
    @NullSource
    @DisplayName("Should reject blank or null currency")
    void processPayment_InvalidCurrency_ThrowsValidation(String currency) {
        PaymentRequest request = new PaymentRequest("TX004", BigDecimal.TEN, currency);

        assertThatThrownBy(() -> paymentService.process(request))
            .isInstanceOf(ValidationException.class);
    }
}
```

---

## 📖 Integration Testing (with Testcontainers)

### Theory:
**Integration tests** verify that multiple components **work together correctly**. Unlike unit tests that mock dependencies, integration tests use **real** databases, message queues, and external services.

**Testcontainers**: A Java library that runs Docker containers for tests. Start a real PostgreSQL, Redis, or Kafka instance just for your test, then tear it down after.

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@Testcontainers
class PaymentControllerIntegrationTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withDatabaseName("testdb")
        .withUsername("test")
        .withPassword("test");

    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);

    @Container
    static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.5.0"));

    @DynamicPropertySource
    static void setProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.datasource.username", postgres::getUsername);
        registry.add("spring.datasource.password", postgres::getPassword);
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Autowired
    private PaymentRepository paymentRepo;

    @Test
    @DisplayName("Full payment flow: API → DB → Kafka")
    void createPayment_FullFlow_Success() {
        // API call
        PaymentRequest request = new PaymentRequest("TX-INT-001", BigDecimal.valueOf(250), "USD");

        ResponseEntity<PaymentResponse> response = restTemplate.postForEntity(
            "/api/payments", request, PaymentResponse.class);

        // Verify HTTP response
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(response.getBody().getTransactionId()).isNotBlank();

        // Verify data in real PostgreSQL
        Payment savedPayment = paymentRepo.findByRequestId("TX-INT-001").orElseThrow();
        assertThat(savedPayment.getAmount()).isEqualByComparingTo(BigDecimal.valueOf(250));
        assertThat(savedPayment.getStatus()).isEqualTo("COMPLETED");

        // Verify Kafka event was published
        try (KafkaConsumer<String, String> consumer = createConsumer()) {
            consumer.subscribe(List.of("payment-events"));
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofSeconds(10));
            assertThat(records.count()).isGreaterThanOrEqualTo(1);
        }
    }
}
```

---

## 📖 Contract Testing (Consumer-Driven Contracts)

### Theory:
**Contract testing** ensures that a **consumer** (API caller) and **provider** (API server) **agree on the API format**. Instead of maintaining API documentation manually, contracts are code-based and verified automatically.

```java
// Producer side — verifies contract
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureStubRunner(
    stubsMode = StubRunnerProperties.StubsMode.LOCAL,
    ids = "com.company:payment-service:+:stubs:8080")
class PaymentContractTest {

    @Autowired
    private StubTrigger stubTrigger;

    @Test
    void shouldReturnPaymentForValidId() {
        // Trigger the stub contract
        stubTrigger.trigger("get_payment_by_id");

        // Verify against contract
        PaymentResponse response = restTemplate.getForObject(
            "http://localhost:8080/api/payments/TX001", PaymentResponse.class);

        assertThat(response.getTransactionId()).isEqualTo("TX001");
        assertThat(response.getStatus()).isEqualTo("COMPLETED");
    }
}
```

---

## 📖 Testing Best Practices (12-year Senior)

### Test Naming Convention:
```java
// Pattern: methodName_scenario_expectedResult
void processPayment_validRequest_returnsSuccess()
void processPayment_negativeAmount_throwsValidationException()
void getUser_invalidId_returns404()
void transferMoney_insufficientFunds_rollsBackTransaction()
```

### Test Coverage Guidelines:
```
What should have 90%+ coverage:
├── Business logic (services, domain)
├── Data validation
├── Error handling paths
└── Security rules

What can have lower coverage:
├── DTOs / POJOs (getters/setters)
├── Configuration classes
├── Framework-generated code
└── trivial delegation methods
```

### Mockito Advanced:
```java
// BDD style (Given-When-Then)
given(userService.findById("U001")).willReturn(Optional.of(testUser));

// Verify with argument matchers
verify(auditService).log(argThat(audit ->
    audit.getAction().equals("PAYMENT") &&
    audit.getAmount().compareTo(BigDecimal.TEN) == 0));

// Verify order of calls
InOrder inOrder = inOrder(paymentRepo, kafkaTemplate);
inOrder.verify(paymentRepo).save(any());     // First save
inOrder.verify(kafkaTemplate).send(any(), any()); // Then publish

// Spy — partial mock (use real object, override specific methods)
PaymentService spyService = spy(realPaymentService);
doReturn(cachedResult).when(spyService).expensiveValidation(any());
```
