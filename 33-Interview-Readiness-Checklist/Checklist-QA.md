# ✅ Complete Interview Readiness Checklist — Top Company Cracker Guide
## Target: FAANG / Product-Based / Investment Banks (JP Morgan, Goldman Sachs)

---

## 📖 How Top Companies Interview Senior Engineers

Different companies have different interview styles. Here's what each focuses on:

| Company | Primary Focus | Secondary Focus |
|---------|--------------|-----------------|
| **Google** | DSA (Hard), System Design | Java internals, OOP |
| **Amazon** | System Design, Leadership Principles | DSA (Medium), STAR answers |
| **Microsoft** | DSA (Medium-Hard), OOP & Design | Cloud (Azure), APIs |
| **JP Morgan / Goldman** | Core Java, Concurrency, System Design | Spring Boot, DB, Security |
| **Uber / Netflix** | System Design, Distributed Systems | DSA, Kafka, microservices |
| **Startups** | Full-stack breadth, quick delivery | Any of the above |

> **12+ year senior tip:** At this level, DSA is necessary but NOT sufficient. System design, architecture trade-offs, leadership (STAR), and production experience carry equal or greater weight.

---

## 🎯 Topic Coverage Status

### ✅ FULLY COVERED in this guide:

| # | Topic | Module |
|---|-------|--------|
| ✅ | Java Core (OOP, JVM, Generics) | `01-Java-Core` |
| ✅ | Java 8-22 Features | `02-Java-8-to-22-Features` |
| ✅ | Multithreading & Concurrency | `03-Multithreading-Concurrency` |
| ✅ | Collections Framework | `04-Collections-Framework` |
| ✅ | Spring Boot (Deep) | `05-Spring-Boot` |
| ✅ | Microservices | `06-Microservices` |
| ✅ | Design Patterns (14 GoF) | `07-Design-Patterns` |
| ✅ | SOLID Principles | `08-SOLID-Principles` |
| ✅ | Kafka & Messaging | `09-Kafka-Messaging` |
| ✅ | JPA / Hibernate / SQL | `10-Database-JPA-Hibernate` |
| ✅ | REST API Security | `11-REST-API-Security` |
| ✅ | System Design | `12-System-Design` |
| ✅ | Real-Time Production Scenarios | `13-Real-Time-Scenarios` |
| ✅ | JP Morgan Full Q&A | `14-JP-Morgan-Interview-Questions` |
| ✅ | Cloud & Docker & Kubernetes | `15-Cloud-Deployment` |
| ✅ | JVM Performance & GC | `16-Performance-Optimization` |
| ✅ | Distributed Systems | `17-Distributed-Systems` |
| ✅ | Event-Driven (CQRS, Saga, Outbox) | `18-Event-Driven-Architecture` |
| ✅ | Observability (Prometheus, Jaeger) | `19-Observability-Monitoring` |
| ✅ | Testing (JUnit, Testcontainers) | `20-Testing-Quality` |
| ✅ | DevOps & CI/CD | `21-DevOps-Automation` |
| ✅ | Advanced Security | `22-Advanced-Security` |
| ✅ | Leadership & Ownership (STAR) | `23-Leadership-System-Ownership` |
| ✅ | Domain-Driven Design | `24-Domain-Driven-Design` |
| ✅ | Data Engineering (Batch, CDC) | `25-Data-Engineering-Basics` |
| ✅ | Caching Strategies | `26-Caching-Strategies` |
| ✅ | Reactive / WebFlux | `27-Reactive-Programming` |
| ✅ | GraphQL & gRPC | `28-Advanced-APIs-GraphQL-gRPC` |
| ✅ | Messaging Patterns (RabbitMQ) | `29-Messaging-Patterns` |
| ✅ | Frontend Basics (React, CORS) | `30-Frontend-Basics-For-Backend` |
| ✅ | Cross-Questioning Scenarios | `31-Cross-Questioning-Deep-Dives` |
| ✅ | Data Structures & Algorithms | `32-Data-Structures-Algorithms` |

---

## 📋 The 10 Topics Most Missed by Senior Engineers (& Answers)

---

### 1. STAR Method — Behavioral Interview (Amazon especially)

Amazon's **14 Leadership Principles** drive ALL interviews. Every answer must follow STAR format.

**Most frequently asked behavioral questions:**

#### "Tell me about a time you had a production outage. What did you do?"
```
Situation:
  Our payment service was throwing 500 errors for 35% of checkout requests at 11 PM.
  Revenue impact: ~$50,000/hour. CEO was cc'd on alerts.

Task:
  I was the on-call engineer and had to lead the incident resolution.

Action:
  1. Checked Grafana dashboards → saw DB connection pool exhausted (HikariCP).
  2. Identified root cause: a new feature deployed 2 hours earlier had a
     @Transactional method calling an external Stripe API (held DB connection for ~10s).
  3. Immediate fix: rolled back the deployment (3 min using ArgoCD).
  4. Communicated status to stakeholders every 15 minutes via Slack incident channel.
  5. Next day: added a test to catch @Transactional + external HTTP combinations.
     Fixed the code to move the Stripe call OUTSIDE the transaction.

Result:
  Service restored in 11 minutes. Root cause fixed within 24 hours.
  Added this pattern to our architecture review checklist.
  Zero similar incidents in the 18 months since.
```

#### "Tell me about a time you disagreed with a technical decision and convinced your team."
```
Situation:
  Team wanted to migrate to microservices for a 6-month-old application with 5
  developers. The estimated migration would take 4 months on top of feature work.

Task:
  I believed it was premature optimization and needed to make the case for delay.

Action:
  I prepared a written proposal comparing:
  - Modular monolith (current codebase, with proper package boundaries)
  - Microservices (5 services + Kubernetes + distributed tracing overhead)
  
  I presented concrete data: our app handled 500 rps with p99 < 100ms on a single
  instance. We had no domain boundaries that needed independent scaling.
  
  I proposed a compromise: implement DDD-style bounded contexts within the monolith
  now, extract services only when a specific domain hits scale limits.

Result:
  Team agreed. We saved 4 months of platform work. 6 months later, only the
  Payment domain needed extraction (10x growth). The clean domain separation
  made that extraction take 3 weeks instead of months.
```

---

### 2. Java Memory Model — Topics Most Seniors Get Wrong

#### "What is the happens-before relationship?"
The JVM memory model doesn't guarantee that actions in one thread are visible to another thread UNLESS a **happens-before** relationship is established.

Happens-before relationships are established by:
- Thread `start()` — all actions before `t.start()` happen-before all actions in thread `t`
- `volatile` write — a volatile write happens-before subsequent reads of that variable
- `synchronized` release — unlocking a monitor happens-before any subsequent lock on the same monitor
- `Thread.join()` — all actions in thread `t` happen-before the return from `t.join()`

```java
// WITHOUT happens-before — possible to see x=0 even after flag=true in another thread:
int x = 0;
boolean flag = false;  // NOT volatile

// Thread 1:
x = 42;
flag = true;  // CPU may reorder — another thread may see flag=true but x=0

// WITH volatile — establishes happens-before:
volatile boolean flag = false;
// Thread 2's read of flag=true guarantees it will ALSO see x=42
// because the write to flag happens-after the write to x in Thread 1
```

---

### 3. JVM Internals — What Really Happens at Runtime

#### Class Loading Lifecycle:
```
1. LOADING:    ClassLoader finds and reads .class file bytes
2. LINKING:
   a. VERIFICATION:  Bytecode safety checks (no invalid array access, etc.)
   b. PREPARATION:   Static fields allocated in memory with DEFAULT values (0, null, false)
   c. RESOLUTION:    Symbolic references → actual memory addresses
3. INITIALIZATION: Static initializers and static field assignments run
4. USING:      Normal execution
5. UNLOADING:  ClassLoader and all classes it loaded are garbage collected together
```

```java
// STATIC INITIALIZATION ORDER matters!
public class Server {
    // These run in order during class initialization:
    static int port = getPort();            // Step 1: method called
    static final Logger log = Logger.getLogger(Server.class); // Step 2

    static {
        log.info("Server port: " + port);   // Step 3: static initializer block
    }
    // Order of static field declarations = order of initialization
}
```

---

### 4. Garbage Collection Deep Dive — Interview Questions

#### "Explain G1GC and when you'd tune it"

```
G1GC (Garbage First) — Default since Java 9:

Memory Layout:
  Heap is divided into equal-sized REGIONS (2048 by default, 1-32MB each)
  Regions are dynamically assigned as: Eden, Survivor, Old, Humongous (large objects)

Collection Cycle:
  1. Minor GC (Young Collection): Evacuate Eden → Survivor / Old regions
  2. Concurrent Marking: Scan Old regions while app runs (minimal pause)
  3. Mixed GC: Collect Young + selected Old regions (prioritizes most garbage = "Garbage First")
  4. Full GC (rare): Stop-the-World if concurrent marking can't keep up

Key JVM Flags:
  -Xms4g -Xmx4g              # Set heap (fix min=max to avoid dynamic sizing overhead)
  -XX:+UseG1GC                # Explicit (default since Java 9 anyway)
  -XX:MaxGCPauseMillis=200    # Target max pause (G1 tries to meet this)
  -XX:G1HeapRegionSize=8m     # Region size (larger = fewer regions = less overhead)
  -XX:InitiatingHeapOccupancyPercent=45  # Start concurrent marking at 45% heap usage
```

---

### 5. SQL Deep Dive — Window Functions (Frequently missed)

#### "Find the second-highest salary per department"
```sql
-- Without Window Functions (subquery approach — works but slow)
SELECT department_id, MAX(salary)
FROM employees
WHERE salary NOT IN (SELECT MAX(salary) FROM employees GROUP BY department_id)
GROUP BY department_id;

-- WITH Window Functions (O(n log n) — elegant and fast)
SELECT department_id, salary, employee_name
FROM (
    SELECT
        department_id,
        salary,
        employee_name,
        DENSE_RANK() OVER (
            PARTITION BY department_id  -- Rank within each department separately
            ORDER BY salary DESC         -- Highest salary gets rank 1
        ) AS dept_rank
    FROM employees
) ranked
WHERE dept_rank = 2;  -- Second highest

-- Other Window functions you must know:
-- ROW_NUMBER(): Unique rank even for ties (1,2,3,4)
-- RANK():       Ties get same rank, next rank is skipped (1,2,2,4)
-- DENSE_RANK(): Ties get same rank, NO gaps (1,2,2,3) ← best for "Nth" problems
-- LAG(col, n):  Access value from n rows BEFORE current row
-- LEAD(col, n): Access value from n rows AFTER current row
-- SUM() OVER (PARTITION BY dept ORDER BY date): Running total per group
```

---

### 6. REST API Design Best Practices (Often tested via design questions)

```java
// Versioning strategies — each has trade-offs:

// 1. URI Versioning (most common, very clear)
//    GET /api/v1/users/{id}
//    GET /api/v2/users/{id}  ← Breaking changes go to v2

// 2. Header Versioning (cleaner URLs, less discoverable)
//    Accept: application/vnd.company.api+json;version=2

// 3. Query Param (simple but pollutes query space)
//    GET /api/users/{id}?version=2

// Standard HTTP Status Code Usage:
// 200 OK           — Successful GET, PUT, PATCH
// 201 Created      — Successful POST (with Location header pointing to new resource)
// 204 No Content   — Successful DELETE (or PUT with no response body)
// 400 Bad Request  — Invalid input (validation failure), must include error details
// 401 Unauthorized — Not authenticated (no/invalid token)
// 403 Forbidden    — Authenticated but not authorized (wrong role)
// 404 Not Found    — Resource doesn't exist
// 409 Conflict     — Duplicate (e.g., email already registered)
// 422 Unprocessable — Semantically invalid request (valid JSON but wrong business logic)
// 429 Too Many Requests — Rate limit exceeded
// 500 Internal Server Error — NEVER expose stack trace to client!
// 503 Service Unavailable — Circuit breaker open / instance restarting
```

---

### 7. Docker & Kubernetes — Production Questions

#### "Your K8s pod keeps OOMKilled. How do you debug it?"
```yaml
# Step 1: Check the pod description
kubectl describe pod payment-service-xyz --namespace=prod
# Look for: "OOMKilled" in State section, Last Exit Code: 137

# Step 2: Check metrics before the crash
kubectl top pod payment-service-xyz   # Current memory usage

# Step 3: Set proper memory limits with requests != limits
spec:
  containers:
  - name: payment-service
    resources:
      requests:
        memory: "512Mi"    # Guaranteed minimum (scheduler uses this)
        cpu: "250m"
      limits:
        memory: "1Gi"      # Maximum — OOMKilled if exceeded!
        cpu: "500m"
    # RULE: limits > requests to allow bursting but prevent runaway consumption

# Step 4: Add JVM heap flags to match container limits
# If container limit is 1Gi, set JVM heap to ~75% = 768m
# env: JAVA_OPTS: "-Xms512m -Xmx768m -XX:+UseG1GC"
# Without explicit Xmx, JVM defaults to 25% of TOTAL machine RAM (often 64GB server!)
# The JVM heap + JVM native memory (metaspace, code cache) together exceed the container limit!
```

---

### 8. API Rate Limiting — System Design Building Block

```java
// Token Bucket Algorithm (most common in production)
// Tokens refill at a fixed rate; each request consumes 1 token

@Component
public class TokenBucketRateLimiter {
    private final Map<String, AtomicLong> tokens = new ConcurrentHashMap<>();
    private final Map<String, Long> lastRefill = new ConcurrentHashMap<>();
    private final long maxTokens = 100;      // Burst limit: 100 req
    private final long refillRate = 10;       // Refill 10 tokens/second
    private final long refillIntervalMs = 1000;

    public boolean allowRequest(String userId) {
        long now = System.currentTimeMillis();
        tokens.computeIfAbsent(userId, k -> new AtomicLong(maxTokens));
        lastRefill.computeIfAbsent(userId, k -> now);

        // Calculate tokens to add since last refill
        long elapsed = now - lastRefill.get(userId);
        if (elapsed > refillIntervalMs) {
            long tokensToAdd = (elapsed / refillIntervalMs) * refillRate;
            tokens.get(userId).updateAndGet(t -> Math.min(maxTokens, t + tokensToAdd));
            lastRefill.put(userId, now);
        }

        // Consume one token
        return tokens.get(userId).getAndUpdate(t -> t > 0 ? t - 1 : 0) > 0;
    }
}

// In production use Redis + Lua script for distributed rate limiting:
// - Lua script ensures atomicity across multiple app instances
// - Redis INCR + EXPIRE per userId per time window
```

---

### 9. Git & Code Review Best Practices (Asked in leadership rounds)

#### "How do you handle a PR where a junior developer wrote complex but unmaintainable code?"
```
Framework for code reviews:
  1. Separate the PERSON from the CODE — never make it personal
  2. Ask questions before making statements: "Can you walk me through your reasoning here?"
  3. Provide concrete suggestions: NOT "this is wrong", BUT "here's an alternative: [code]"
  4. Priority label: P1 (blocking), P2 (should fix), P3 (nit/suggestion)
  5. Explain WHY, not just WHAT needs to change — create learning opportunities

For complex but unmaintainable code specifically:
  "I can see you solved the problem creatively. Could we add some comments explaining
  the algorithm? Looking at this 6 months from now, maintainability becomes critical.
  Would you be open to exploring [simpler alternative] here?"

PR Checklist items I enforce on every PR:
  ✅ Tests: Unit + integration coverage for new behavior
  ✅ No new externally-facing exceptions exposing internal details
  ✅ @Transactional boundaries don't include external HTTP calls
  ✅ Thread safety: shared state is properly handled
  ✅ No secrets/credentials committed
  ✅ Observability: logs have trace IDs, metrics updated
  ✅ DB migrations are backward-compatible (no breaking column drops/renames)
```

---

### 10. Microservices — 12 Network Fallacies (Every Architect Should Know)

In distributed systems, the **8 Fallacies of Distributed Computing** define what junior developers falsely assume:

```
Developers new to microservices assume:
1. "The network is reliable"   → Use circuit breakers (Resilience4j), retries, timeouts
2. "Latency is zero"           → Async where possible, cache aggressively, measure p99
3. "Bandwidth is infinite"     → Compress large payloads, use Protobuf over JSON for internal APIs
4. "The network is secure"     → Zero-trust: mTLS between services, never assume internal calls are safe
5. "Topology doesn't change"   → Use service discovery (Eureka, Consul) not hardcoded hostnames
6. "There is one administrator"→ Design for partial failures — one team's service may be down
7. "Transport cost is zero"    → Network I/O is NOT free — profile and optimize inter-service calls
8. "The network is homogeneous"→ Services may run in different regions, JVM versions, load conditions
```

---

## 📅 Recommended 4-Week Interview Preparation Plan

### Week 1: Foundations
| Day | Focus | Module |
|-----|-------|--------|
| 1-2 | Java Core — OOP, JVM, Generics, Memory | `01-Java-Core` |
| 3 | Java 8-21 Features | `02-Java-8-to-22-Features` |
| 4-5 | Multithreading Deep Dive | `03-Multithreading-Concurrency` |
| 6-7 | Collections Internal | `04-Collections-Framework` |

### Week 2: Framework & Architecture
| Day | Focus | Module |
|-----|-------|--------|
| 1-2 | Spring Boot, AOP, @Transactional | `05-Spring-Boot` |
| 3 | Design Patterns (all 14) | `07-Design-Patterns` |
| 4 | SOLID Principles | `08-SOLID-Principles` |
| 5-6 | Microservices + System Design | `06-Microservices` + `12-System-Design` |
| 7 | Database / JPA / SQL | `10-Database-JPA-Hibernate` |

### Week 3: Infrastructure & Advanced Topics
| Day | Focus | Module |
|-----|-------|--------|
| 1 | Kafka | `09-Kafka-Messaging` |
| 2 | Distributed Systems | `17-Distributed-Systems` |
| 3 | Caching + Event-Driven | `26-Caching-Strategies` + `18-Event-Driven-Architecture` |
| 4 | Performance + Observability | `16-Performance-Optimization` + `19-Observability-Monitoring` |
| 5 | Security | `22-Advanced-Security` |
| 6-7 | Cloud / Docker / K8s | `15-Cloud-Deployment` |

### Week 4: Mock Interviews
| Day | Focus | Module |
|-----|-------|--------|
| 1-2 | DSA Practice (Arrays, Trees, DP) | `32-Data-Structures-Algorithms` |
| 3 | Leadership & STAR Answers | `23-Leadership-System-Ownership` |
| 4 | JP Morgan Full Q&A (30 questions timed) | `14-JP-Morgan-Interview-Questions` |
| 5 | Cross-questioning Scenarios | `31-Cross-Questioning-Deep-Dives` |
| 6 | System Design Mock (1 hour whiteboard) | `12-System-Design` |
| 7 | Final Review + Rest | All README checklists |

---

## ⚡ 48 Must-Know Interview Questions by Category

### Java Core (8 Questions)
1. How does `String.intern()` work and when would you use it?
2. What's the difference between shallow copy and deep copy in Java?
3. Explain Java Memory Model and happens-before relationship
4. What is Type Erasure in Generics? What are `?`, `? extends T`, `? super T`?
5. How does the ClassLoader delegation model work? What is the parent-first rule?
6. When is `finalize()` called and why should you use `try-with-resources` instead?
7. What is the difference between `==` and `equals()` for Strings?
8. What are the 4 types of references in Java? (Strong, Soft, Weak, Phantom)

### Multithreading (6 Questions)
1. Explain the ThreadPoolExecutor rejection policies
2. What is a race condition? Give a real example in a payment system
3. How do you diagnose a deadlock in production? (`jstack`, thread dumps)
4. What is `CompletableFuture.allOf()` vs `anyOf()`?
5. Why must `ThreadLocal` be cleaned up in a web container?
6. What is the difference between `Executors.newCachedThreadPool()` and `newFixedThreadPool()`? When is each dangerous?

### Spring Boot (6 Questions)
1. How does Spring Boot auto-configuration work? What is `spring.factories`?
2. Explain @Transactional propagation: REQUIRED vs REQUIRES_NEW vs NESTED
3. Why does @Transactional not work for private methods?
4. What is the difference between `@Component`, `@Service`, `@Repository`, `@Controller`?
5. How does Spring AOP choose between JDK Dynamic Proxy and CGLIB?
6. What is `BeanDefinitionRegistryPostProcessor` and why would you use it?

### Database / JPA (6 Questions)
1. Solve the N+1 problem: 3 different approaches with trade-offs
2. Explain optimistic vs pessimistic locking with a real-world scenario
3. What is `@EntityGraph` and when does it beat `JOIN FETCH`?
4. How does HikariCP connection validation work? What is `connectionTestQuery`?
5. What is a covering index and how does it speed up queries?
6. Explain `SERIALIZABLE` vs `REPEATABLE_READ` isolation levels with examples

### System Design (6 Questions)
1. Design a URL Shortener (tinyurl.com)
2. Design a distributed rate limiter
3. Design a notification service (email, SMS, push) at 10M users/day
4. How do you design a system to handle 1M concurrent WebSocket connections?
5. Design a real-time leaderboard for a gaming platform
6. How does consistent hashing work? Why it's used for distributed caching?

### Kafka / Messaging (4 Questions)
1. How do you ensure exactly-once delivery in Kafka?
2. What causes Kafka consumer rebalancing and how do you minimize it?
3. Design an order processing system using Kafka that handles duplicate messages
4. RabbitMQ vs Kafka: which for real-time analytics pipeline? Which for task queues?

### Leadership / STAR (6 Questions)
1. Tell me about a time you made an architectural decision you later regretted
2. How have you handled a situation where your team disagreed with a tech decision?
3. How do you mentor a junior developer who writes working but unreadable code?
4. Describe how you handled a critical production incident
5. Tell me about a time you had to deliver a feature with incomplete requirements
6. How do you evaluate technical debt? When do you push to pay it down?

### DSA (6 Questions — for DSA-heavy interviews)
1. Implement LRU Cache with O(1) operations (LinkedHashMap AND from scratch)
2. Find cycle in a linked list AND find the starting node of the cycle
3. Serialize and deserialize a binary tree
4. Find the Kth largest element in an unsorted array
5. Implement a rate limiter using a sliding window algorithm
6. Merge K sorted lists efficiently (using a priority queue)
