# 📊 Data Engineering Basics — Deep Dive (Theory + Code)
## Target: 12+ Years Experience (Java Full Stack + Data Awareness)

---

## 📖 What is Data Engineering?

**Data Engineering** is the practice of designing, building, and maintaining the systems and infrastructure for **collecting, storing, and processing large volumes of data**. As a senior Java developer, you'll often work alongside data engineers or build systems that feed into data pipelines.

**Why Java devs need data engineering knowledge:**
- Your microservices PRODUCE data that analytics teams consume
- You may need to build ETL pipelines in Java/Spring Boot
- Interview questions increasingly cover data processing concepts
- Real-time dashboards and reporting require stream processing

---

## 📖 ETL vs ELT Pipelines

### Theory:
**ETL (Extract, Transform, Load):**
1. **Extract**: Pull data from sources (databases, APIs, files)
2. **Transform**: Clean, validate, aggregate, enrich the data
3. **Load**: Write to destination (data warehouse, analytics DB)

**ELT (Extract, Load, Transform):** Modern approach — load raw data first, transform later in the data warehouse (where compute is cheap).

```
ETL (Traditional):
  Source DB → [Extract] → [Transform in Java/Python] → [Load] → Data Warehouse

ELT (Modern):
  Source DB → [Extract] → [Load raw to warehouse] → [Transform in SQL/DBT]

When to use which:
  ETL: Data needs cleaning/anonymization BEFORE loading (GDPR, PII)
  ELT: Raw data is valuable, transform on-demand for different use cases
```

### Java ETL with Spring Batch:
```java
@Configuration
@EnableBatchProcessing
public class OrderEtlJobConfig {

    @Bean
    public Job orderEtlJob(JobRepository jobRepo, Step extractStep) {
        return new JobBuilder("orderEtlJob", jobRepo)
            .start(extractStep)
            .build();
    }

    @Bean
    public Step extractStep(JobRepository jobRepo, PlatformTransactionManager txManager) {
        return new StepBuilder("extractOrders", jobRepo)
            .<Order, AnalyticsOrder>chunk(1000, txManager) // Process 1000 at a time
            .reader(orderReader())          // EXTRACT
            .processor(orderProcessor())    // TRANSFORM
            .writer(analyticsWriter())      // LOAD
            .faultTolerant()
            .retryLimit(3)
            .retry(TransientException.class) // Retry transient failures
            .skipLimit(100)
            .skip(DataValidationException.class) // Skip bad records (up to 100)
            .build();
    }

    // EXTRACT: Read from source database
    @Bean
    public JdbcCursorItemReader<Order> orderReader() {
        return new JdbcCursorItemReaderBuilder<Order>()
            .name("orderReader")
            .dataSource(sourceDataSource)
            .sql("""
                SELECT o.id, o.user_id, o.total, o.status, o.created_at,
                       u.name, u.email, u.segment
                FROM orders o JOIN users u ON o.user_id = u.id
                WHERE o.created_at >= :yesterday
                """)
            .rowMapper(new OrderRowMapper())
            .build();
    }

    // TRANSFORM: Clean, enrich, aggregate
    @Bean
    public ItemProcessor<Order, AnalyticsOrder> orderProcessor() {
        return order -> {
            AnalyticsOrder analytics = new AnalyticsOrder();
            analytics.setOrderId(order.getId());
            analytics.setUserId(order.getUserId());
            analytics.setTotal(order.getTotal());
            analytics.setDate(order.getCreatedAt().toLocalDate());

            // Enrich: Calculate revenue bucket
            if (order.getTotal().compareTo(BigDecimal.valueOf(1000)) > 0) {
                analytics.setRevenueBucket("HIGH");
            } else if (order.getTotal().compareTo(BigDecimal.valueOf(100)) > 0) {
                analytics.setRevenueBucket("MEDIUM");
            } else {
                analytics.setRevenueBucket("LOW");
            }

            // Anonymize PII for analytics
            analytics.setUserEmail(hashPII(order.getUserEmail()));

            // Validation — skip invalid records
            if (order.getTotal().compareTo(BigDecimal.ZERO) < 0) {
                throw new DataValidationException("Negative total");
            }

            return analytics;
        };
    }

    // LOAD: Write to analytics database
    @Bean
    public JdbcBatchItemWriter<AnalyticsOrder> analyticsWriter() {
        return new JdbcBatchItemWriterBuilder<AnalyticsOrder>()
            .dataSource(analyticsDataSource)
            .sql("""
                INSERT INTO analytics_orders (order_id, user_id, total, date, revenue_bucket)
                VALUES (:orderId, :userId, :total, :date, :revenueBucket)
                ON CONFLICT (order_id) DO UPDATE SET total = :total
                """)
            .beanMapped()
            .build();
    }
}
```

---

## 📖 Batch Processing vs Stream Processing

### Theory:

| Feature | Batch Processing | Stream Processing |
|---------|-----------------|-------------------|
| Data | Processes data in **bulk** (hourly, daily) | Processes data in **real-time** (per event) |
| Latency | High (minutes to hours) | Low (milliseconds to seconds) |
| Use case | Reporting, analytics, ML training | Fraud detection, live dashboards, alerts |
| Tools | Spring Batch, Spark, Hadoop | Kafka Streams, Apache Flink, Spring Cloud Stream |
| Complexity | Simpler (known data size) | Harder (unbounded, windowing needed) |
| Example | "Daily sales report" | "Alert if fraud detected in payment" |

### Stream Processing with Kafka Streams:
```java
// Real-time order analytics — process events as they arrive
@Configuration
public class OrderStreamConfig {

    @Bean
    public KStream<String, OrderEvent> orderAnalyticsStream(StreamsBuilder builder) {
        // Source: consume from order-events topic
        KStream<String, OrderEvent> orders = builder.stream(
            "order-events",
            Consumed.with(Serdes.String(), orderEventSerde)
        );

        // Real-time: Count orders per region per minute
        KTable<Windowed<String>, Long> ordersPerRegion = orders
            .filter((key, event) -> event.getStatus().equals("COMPLETED"))
            .groupBy((key, event) -> event.getRegion())
            .windowedBy(TimeWindows.of(Duration.ofMinutes(1))) // 1-minute window
            .count(Materialized.as("orders-per-region-store"));

        // Real-time: Revenue per product category
        KTable<String, BigDecimal> revenueByCategory = orders
            .filter((key, event) -> event.getStatus().equals("COMPLETED"))
            .groupBy((key, event) -> event.getCategory())
            .aggregate(
                () -> BigDecimal.ZERO,
                (key, event, total) -> total.add(event.getAmount()),
                Materialized.with(Serdes.String(), bigDecimalSerde)
            );

        // Real-time: Fraud detection — alert on high-value orders
        orders
            .filter((key, event) -> event.getAmount().compareTo(new BigDecimal("50000")) > 0)
            .peek((key, event) ->
                log.warn("🚨 High-value order detected: {} amount: {}",
                    event.getOrderId(), event.getAmount()))
            .to("fraud-alerts"); // Send to fraud alert topic

        return orders;
    }
}
```

---

## 📖 Change Data Capture (CDC) — Debezium

### Theory:
**CDC** captures **every change** (INSERT, UPDATE, DELETE) made to a database and streams it as events. Instead of polling the database for changes, you get real-time notifications.

**Use cases:**
- Sync databases (PostgreSQL → Elasticsearch for search)
- Feed event-driven architecture (DB change → Kafka event → downstream services)
- Build audit logs (every DB change captured)
- Real-time reporting (dashboard updates within seconds of DB change)

```json
// Debezium connector configuration
{
  "name": "order-source-connector",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "postgres",
    "database.port": "5432",
    "database.dbname": "orders_db",
    "database.user": "debezium",
    "database.password": "${vault:db_cdc_password}",
    "table.include.list": "public.orders,public.order_items",
    "topic.prefix": "cdc",
    "slot.name": "debezium_orders",
    "plugin.name": "pgoutput",
    "transforms": "unwrap",
    "transforms.unwrap.type": "io.debezium.transforms.ExtractNewRecordState"
  }
}

// Debezium produces events to Kafka:
// Topic: cdc.public.orders
// Event: {
//   "before": { "id": 1, "status": "PENDING", "total": 100 },
//   "after":  { "id": 1, "status": "PAID", "total": 100 },
//   "op": "u",  // u=update, c=create, d=delete
//   "ts_ms": 1700000000
// }
```

### Consuming CDC events in Spring:
```java
@Service
public class OrderCdcConsumer {

    @KafkaListener(topics = "cdc.public.orders")
    public void syncToElasticsearch(DebeziumEvent event) {
        switch (event.getOperation()) {
            case "c", "u" -> {
                OrderDocument doc = mapToDocument(event.getAfter());
                elasticsearchRepo.save(doc); // Sync to Elasticsearch
            }
            case "d" -> {
                elasticsearchRepo.deleteById(event.getBefore().getId());
            }
        }
    }
}
```

---

## 📖 Data Architecture for Java Full Stack

### Common Data Architecture Patterns:

```
1. OLTP (Online Transaction Processing) — Your Spring Boot app
   PostgreSQL, MySQL — optimized for writes, ACID transactions
   Use case: User registration, payment processing

2. OLAP (Online Analytical Processing) — Reporting
   ClickHouse, Snowflake, BigQuery — optimized for reads, aggregations
   Use case: Monthly revenue report, user behavior analysis

3. Data Lake — Raw data storage
   S3, HDFS — stores raw, unstructured data (JSON, CSV, logs)
   Use case: ML training data, historical logs

4. Data Lakehouse — Best of both (data lake + warehouse)
   Delta Lake, Apache Iceberg — structured queries on raw data
   Use case: Real-time analytics on historical data

Typical Java Full Stack Data Flow:
┌───────────┐   ┌──────────┐   ┌───────────┐   ┌────────────┐
│ Spring    │──→│  Kafka   │──→│  Spark/   │──→│ ClickHouse │
│ Boot API  │   │          │   │  Flink    │   │ (Analytics)│
│(PostgreSQL)│  │(Events)  │   │(Processing)│  │(Dashboard) │
└───────────┘   └──────────┘   └───────────┘   └────────────┘
  OLTP            Streaming     Batch/Stream      OLAP
```

---

## Common Interview Questions:

### "How would you design a real-time analytics dashboard?"
```
Architecture:
1. Source: Application DB (PostgreSQL) — writes happen here
2. CDC: Debezium captures changes → publishes to Kafka
3. Stream Processing: Kafka Streams aggregates per minute/hour
4. Sink: ClickHouse (OLAP DB optimized for analytics)
5. Dashboard: Grafana queries ClickHouse every 10 seconds

Why not query PostgreSQL directly?
- Analytics queries (GROUP BY, JOIN, aggregate) are expensive
- They block transactional queries (same DB)
- OLAP databases handle aggregations 10-100x faster
```

### "What is Apache Spark and when would you use it?"
```
Apache Spark is a distributed computing framework for large-scale data processing.

Java Full Stack developer use cases:
1. Process 10 million records for year-end report (too large for DB query)
2. Train ML model on user behavior data
3. Data migration between systems (ETL at scale)
4. Log analysis across 100 servers

Spark vs Kafka Streams:
Spark: Batch + micro-batch. Process LARGE datasets. Runs as job.
Kafka Streams: True real-time. Process EVENTS as they arrive. Runs as app.
```
