# 🗃️ Hibernate & JPA — Advanced Interview Questions
## Target: 12+ Years Experience | InterviewBit + GFG Inspired

> **Note:** This extends JPA-Hibernate-QA.md and Hibernate-ACID-QA.md with frequently missed topics.

---

## Q: Hibernate Inheritance Mapping Strategies

### Theory:
How do you map a Java class hierarchy to relational database tables?

```java
// Parent entity
@Entity
@Inheritance(strategy = InheritanceType.SINGLE_TABLE) // Change strategy here
public abstract class Payment {
    @Id @GeneratedValue
    private Long id;
    private BigDecimal amount;
    private LocalDateTime paymentDate;
}

@Entity
public class CreditCardPayment extends Payment {
    private String cardNumber;
    private String cardHolderName;
}

@Entity
public class UPIPayment extends Payment {
    private String upiId;
    private String transactionRef;
}
```

### Strategy 1: SINGLE_TABLE (Default — Best Performance)
```
One table for entire hierarchy. Uses discriminator column.

payment table:
| id | dtype           | amount | payment_date | card_number | upi_id |
|----|-----------------|--------|--------------|-------------|--------|
| 1  | CreditCardPayment| 500   | 2024-01-15   | 4111...     | null   |
| 2  | UPIPayment       | 200   | 2024-01-16   | null        | yog@upi|

✅ Best performance — single table, no JOINs
✅ Polymorphic queries are fast
❌ Lots of NULL columns (subclass fields)
❌ Can't enforce NOT NULL on subclass columns
```

### Strategy 2: TABLE_PER_CLASS (One table per concrete class)
```
Each concrete class gets its own table with ALL columns (including parent).

credit_card_payment: | id | amount | payment_date | card_number | card_holder |
upi_payment:         | id | amount | payment_date | upi_id | transaction_ref |

✅ No NULLs — each table has only relevant columns
❌ Polymorphic queries require UNION ALL (slow)
❌ Duplicate columns (amount, payment_date in every table)
❌ ID generation must be shared across tables
```

### Strategy 3: JOINED (One table per class, JOINed together)
```
@Inheritance(strategy = InheritanceType.JOINED)

payment:              | id | amount | payment_date |
credit_card_payment:  | id | card_number | card_holder |  (FK → payment.id)
upi_payment:          | id | upi_id | transaction_ref |  (FK → payment.id)

✅ Normalized — no NULLs, no duplication
✅ Can enforce NOT NULL on subclass columns
❌ Polymorphic queries require JOINs (slower)
❌ INSERT requires multiple statements
```

### When to Use What:
```
Simple hierarchy, few subclass fields → SINGLE_TABLE (default, fastest)
Need strict schema, rare polymorphic queries → JOINED
Need complete separation → TABLE_PER_CLASS (avoid if possible)
```

---

## Q: Hibernate Entity States / Lifecycle

```
                    ┌─────────────────┐
    new Entity()    │    TRANSIENT     │  Not managed, no ID, not in DB
                    └────────┬────────┘
                             │ persist() / save()
                             ▼
                    ┌─────────────────┐
                    │   PERSISTENT    │  Managed by Session, has ID, synced with DB
                    │  (Managed)      │  Changes auto-detected (dirty checking)
                    └───┬─────────┬───┘
                        │         │
            detach() /  │         │  remove()
            close() /   │         │
            clear()     │         ▼
                        │    ┌─────────────────┐
                        │    │    REMOVED       │  Scheduled for deletion
                        │    └─────────────────┘
                        ▼
                    ┌─────────────────┐
                    │    DETACHED     │  Was managed, session closed
                    │                 │  Changes NOT auto-synced
                    └─────────────────┘
                             │ merge()
                             ▼
                    Back to PERSISTENT
```

```java
// Transient → Persistent
Employee emp = new Employee("Yogesh"); // TRANSIENT
session.persist(emp);                   // PERSISTENT (managed)

// Persistent → Detached
session.close();                        // emp is now DETACHED
// OR
session.evict(emp);                     // emp is DETACHED

// Detached → Persistent (re-attach)
Employee merged = session.merge(emp);   // Returns PERSISTENT copy

// Persistent → Removed
session.remove(emp);                    // Scheduled for DELETE

// DIRTY CHECKING (automatic update):
Employee emp = session.find(Employee.class, 1L); // PERSISTENT
emp.setSalary(100000); // Changed in memory
// NO explicit save() needed! Hibernate detects change at flush time
// and auto-generates UPDATE SQL
```

---

## Q: save() vs persist() vs merge() vs saveOrUpdate()

```
| Method | Return | ID assigned | Entity state |
|--------|--------|-------------|-------------|
| persist() | void | At flush | Must be transient |
| save() | Serializable (ID) | Immediately | Transient → Persistent |
| merge() | Managed copy | At flush | Detached → returns Persistent copy |
| saveOrUpdate() | void | Immediately | Transient or Detached → Persistent |

BEST PRACTICE: Use persist() for new entities, merge() for detached entities
save() and saveOrUpdate() are Hibernate-specific (not JPA standard)
```

---

## Q: get() vs load() in Hibernate

```java
// get() — hits database IMMEDIATELY, returns null if not found
Employee emp = session.get(Employee.class, 1L);
// SQL fired NOW: SELECT * FROM employees WHERE id = 1
if (emp == null) { /* handle not found */ }

// load() — returns PROXY, hits DB only when you access a property
Employee empProxy = session.load(Employee.class, 1L);
// NO SQL yet! Returns a proxy object
String name = empProxy.getName(); // SQL fired NOW (lazy loading)
// Throws ObjectNotFoundException if ID doesn't exist

// WHEN TO USE:
// get() → when you need the full object or need to check existence
// load() → when you just need the reference (for setting relationships)
// Example: order.setCustomer(session.load(Customer.class, customerId));
//          ↑ No need to load full Customer, just need the FK reference
```

---

## Q: HQL vs Criteria API vs Native SQL

```java
// 1. HQL (Hibernate Query Language) — object-oriented SQL
String hql = "SELECT e FROM Employee e WHERE e.department.name = :dept AND e.salary > :min";
List<Employee> employees = session.createQuery(hql, Employee.class)
    .setParameter("dept", "Engineering")
    .setParameter("min", 50000)
    .getResultList();

// 2. Criteria API (JPA 2.0) — type-safe, programmatic
CriteriaBuilder cb = entityManager.getCriteriaBuilder();
CriteriaQuery<Employee> cq = cb.createQuery(Employee.class);
Root<Employee> root = cq.from(Employee.class);
cq.select(root).where(
    cb.and(
        cb.equal(root.get("department").get("name"), "Engineering"),
        cb.greaterThan(root.get("salary"), 50000)
    )
);
List<Employee> results = entityManager.createQuery(cq).getResultList();

// 3. Native SQL — raw database SQL
String sql = "SELECT * FROM employees e JOIN departments d ON e.dept_id = d.id WHERE d.name = ?";
List<Employee> nativeResults = session.createNativeQuery(sql, Employee.class)
    .setParameter(1, "Engineering")
    .getResultList();

// WHEN TO USE:
// HQL: Most queries — readable, database-agnostic
// Criteria: Dynamic queries with many optional filters
// Native: Complex queries, stored procedures, DB-specific features
```

---

## Q: Second-Level Cache in Hibernate

```java
// First-Level Cache: Session scoped (automatic, always on)
// Second-Level Cache: SessionFactory scoped (shared across sessions)

// Enable with EhCache or Hazelcast:
// application.properties:
// spring.jpa.properties.hibernate.cache.use_second_level_cache=true
// spring.jpa.properties.hibernate.cache.region.factory_class=org.hibernate.cache.ehcache.EhCacheRegionFactory

@Entity
@Cacheable
@Cache(usage = CacheConcurrencyStrategy.READ_WRITE) // Cache strategy
public class Product {
    @Id
    private Long id;
    private String name;
    private BigDecimal price;
}

// Cache strategies:
// READ_ONLY: Never changes — best performance (reference data)
// READ_WRITE: Can change — uses locks (most common)
// NONSTRICT_READ_WRITE: Rarely changes — no locks (eventual consistency)
// TRANSACTIONAL: Requires JTA transaction manager

// Query Cache (caches query results, NOT entities):
// spring.jpa.properties.hibernate.cache.use_query_cache=true
List<Product> products = session.createQuery("FROM Product WHERE price < 100", Product.class)
    .setCacheable(true) // Cache this query's results
    .getResultList();
```
