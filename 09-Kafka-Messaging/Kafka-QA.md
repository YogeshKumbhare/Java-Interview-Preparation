# 📨 Apache Kafka & Messaging — Deep Dive Interview Q&A
## Target: 12+ Years Experience

---

## Q1: Explain Kafka Architecture

```
Kafka Cluster:
├── Broker 1 (Leader for P0, P2)
├── Broker 2 (Leader for P1, Follower for P0)
└── Broker 3 (Follower for P1, P2)
    ↑ Managed by ZooKeeper (or KRaft in Kafka 3.x)

Topic: order-events
└── Partition 0 [offset 0, 1, 2, 3, ...] → Broker 1 (Leader)
│   └── Replica on Broker 2 (Follower)
└── Partition 1 [offset 0, 1, 2, ...] → Broker 2 (Leader)
│   └── Replica on Broker 3 (Follower)
└── Partition 2 [offset 0, 1, 2, ...] → Broker 3 (Leader)
    └── Replica on Broker 1 (Follower)

Consumer Groups:
├── Group: "order-processor" → [Consumer A: P0, Consumer B: P1, Consumer C: P2]
└── Group: "order-analytics" → [Consumer X: P0, P1, P2] (separate group, independent offset)
```

---

## Q2: Kafka Producer Configuration — Zero Data Loss

```java
@Configuration
public class KafkaProducerConfig {

    @Bean
    public ProducerFactory<String, Object> producerFactory() {
        Map<String, Object> config = new HashMap<>();

        config.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");

        // Serialization
        config.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        config.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);

        // =================== DURABILITY CONFIG ===================
        // acks=all: Producer waits for ALL in-sync replicas to acknowledge
        config.put(ProducerConfig.ACKS_CONFIG, "all");

        // Idempotent producer: guarantees exactly-once delivery at producer level
        // (prevents duplicates on retry due to network issues)
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);

        // Retries: attempt again on transient failures
        config.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);

        // With idempotence, only 1 in-flight request to preserve ordering
        config.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);

        // =================== PERFORMANCE CONFIG ===================
        // Batch size: accumulate messages before sending
        config.put(ProducerConfig.BATCH_SIZE_CONFIG, 16384); // 16KB

        // Linger: wait up to 5ms to fill batch (trade latency for throughput)
        config.put(ProducerConfig.LINGER_MS_CONFIG, 5);

        // Compression
        config.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "snappy");

        return new DefaultKafkaProducerFactory<>(config);
    }

    @Bean
    public KafkaTemplate<String, Object> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }
}
```

---

## Q3: Kafka Consumer — Exactly-Once, Manual Acknowledgment

```java
@Configuration
public class KafkaConsumerConfig {

    @Bean
    public ConsumerFactory<String, OrderEvent> consumerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "kafka:9092");
        config.put(ConsumerConfig.GROUP_ID_CONFIG, "order-processor");

        // =================== RELIABILITY CONFIG ===================
        // Manual commit — you control when offset is committed
        config.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);

        // Fetch settings
        config.put(ConsumerConfig.MAX_POLL_RECORDS_CONFIG, 100);
        config.put(ConsumerConfig.MAX_POLL_INTERVAL_MS_CONFIG, 300000); // 5 min

        // Start from beginning if no committed offset
        config.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");

        return new DefaultKafkaConsumerFactory<>(config,
            new StringDeserializer(),
            new JsonDeserializer<>(OrderEvent.class));
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, OrderEvent> kafkaListenerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, OrderEvent> factory =
            new ConcurrentKafkaListenerContainerFactory<>();
        factory.setConsumerFactory(consumerFactory());

        // Manual acknowledgment
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);

        // Concurrency = number of partitions for max parallelism
        factory.setConcurrency(6); // For 6 partitions

        // Error handler with DLQ
        factory.setCommonErrorHandler(new DefaultErrorHandler(
            new DeadLetterPublishingRecoverer(kafkaTemplate,
                (record, ex) -> new TopicPartition(record.topic() + ".DLQ", record.partition())),
            new ExponentialBackOff(1000L, 2.0) // 1s, 2s, 4s, 8s...
        ));

        return factory;
    }
}

// Consumer Implementation
@Service
@Slf4j
public class OrderEventConsumer {

    @KafkaListener(
        topics = "order-events",
        groupId = "order-processor",
        containerFactory = "kafkaListenerFactory"
    )
    public void handleOrderEvent(
            ConsumerRecord<String, OrderEvent> record,
            Acknowledgment acknowledgment) {

        log.info("Processing: topic={}, partition={}, offset={}, key={}",
            record.topic(), record.partition(), record.offset(), record.key());

        try {
            orderService.processOrderEvent(record.value());
            acknowledgment.acknowledge(); // Commit ONLY after successful processing
            log.info("Committed offset: {}", record.offset());

        } catch (RetryableException ex) {
            // Don't acknowledge — message will be redelivered
            log.warn("Retryable error, will retry: {}", ex.getMessage());
            throw ex;

        } catch (NonRetryableException ex) {
            // Acknowledge to skip — send to DLQ manually
            log.error("Non-retryable error, sending to DLQ: {}", ex.getMessage());
            dlqService.send(record, ex);
            acknowledgment.acknowledge(); // Move past this message
        }
    }
}
```

---

## Q4: Kafka — How to ensure ordering?

```
Kafka guarantees ordering WITHIN a partition.

To maintain order for related messages (e.g., same orderId):
→ Use orderId as the MESSAGE KEY
→ Messages with same key ALWAYS go to SAME partition
→ Same partition → processed by SAME consumer

Example:
Order 123 → [CREATED, PAYMENT_RECEIVED, SHIPPED, DELIVERED]
All 4 events have key="order-123" → same partition → processed in order
```

```java
// Producer with partition key
public void publishOrderEvent(String orderId, OrderEvent event) {
    kafkaTemplate.send(
        "order-events",
        orderId,  // KEY — ensures ordering per orderId
        event
    );
}

// Custom partitioner — route VIP orders to dedicated partition
public class PriorityPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes, Cluster cluster) {
        List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
        int numPartitions = partitions.size();

        if (value instanceof OrderEvent event && event.isVIP()) {
            // VIP orders → partitions 0, 1 (reserved for VIP)
            return Math.abs(key.hashCode()) % 2;
        }
        // Regular orders → partitions 2 to N
        return 2 + (Math.abs(key.hashCode()) % (numPartitions - 2));
    }
}
```

---

## Q5: Kafka Consumer Rebalancing — What happens?

```
Rebalance Trigger Events:
├── New consumer joins the group
├── Consumer leaves (crash / timeout)
├── New partitions added to topic
└── Consumer calls unsubscribe()

During Rebalance:
1. GroupCoordinator (broker) detects change
2. Triggers rebalance — ALL consumers STOP processing (stop-the-world)
3. onPartitionsRevoked() called — commit pending offsets
4. New partition assignment calculated
5. onPartitionsAssigned() called — resume from committed offsets
```

```java
@Service
public class OrderConsumerWithRebalance implements ConsumerSeekAware {

    @KafkaListener(topics = "order-events")
    public void consume(ConsumerRecord<String, OrderEvent> record,
                        Acknowledgment ack) {
        orderService.process(record.value());
        ack.acknowledge();
    }

    // Called BEFORE rebalance — save state and commit offsets
    @Override
    public void onPartitionsRevoked(Collection<TopicPartition> partitions) {
        log.info("Partitions revoked: {}", partitions);
        // Flush any in-memory state to DB
        stateStore.flush();
    }

    // Called AFTER rebalance — restore state for new partitions
    @Override
    public void onPartitionsAssigned(Collection<TopicPartition> partitions) {
        log.info("Partitions assigned: {}", partitions);
        // Reload state for newly assigned partitions
        stateStore.loadForPartitions(partitions);
    }
}
```

---

## Q6: Kafka — DLQ (Dead Letter Queue) Pattern

```java
@Configuration
public class DlqConfig {

    @Bean
    public NewTopic orderEventsDlq() {
        return TopicBuilder.name("order-events.DLQ")
            .partitions(6)
            .replicas(3)
            .build();
    }
}

// DLQ Processor — manual review and replay
@Service
public class DlqProcessor {

    @KafkaListener(topics = "order-events.DLQ", groupId = "dlq-processor")
    public void processDlq(
            @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
            @Header("kafka_dlt-original-topic") String originalTopic,
            @Header("kafka_dlt-exception-message") String errorMessage,
            @Header("kafka_dlt-original-offset") long originalOffset,
            ConsumerRecord<String, OrderEvent> record) {

        log.error("DLQ message from topic={}, offset={}, error={}",
            originalTopic, originalOffset, errorMessage);

        // Store in DB for manual review
        FailedMessage failed = new FailedMessage();
        failed.setOriginalTopic(originalTopic);
        failed.setPayload(objectMapper.writeValueAsString(record.value()));
        failed.setErrorMessage(errorMessage);
        failed.setOriginalOffset(originalOffset);
        failed.setFailedAt(Instant.now());
        failed.setStatus("PENDING_REVIEW");
        failedMessageRepo.save(failed);

        // Alert ops team
        slackNotifier.alert(
            String.format("⚠️ DLQ: %d failures on %s. Check DLQ dashboard!",
                dlqCount.incrementAndGet(), originalTopic)
        );
    }

    // Admin endpoint to replay DLQ messages
    public void replayMessage(String failedMessageId) {
        FailedMessage msg = failedMessageRepo.findById(failedMessageId).orElseThrow();
        OrderEvent event = objectMapper.readValue(msg.getPayload(), OrderEvent.class);
        kafkaTemplate.send(msg.getOriginalTopic(), event.getOrderId(), event);
        msg.setStatus("REPLAYED");
        failedMessageRepo.save(msg);
    }
}
```

---

## Q7: Kafka Transactions (Exactly-Once Semantics)

```java
// Transactional producer — atomic: produce + consume + produce(new topic) 
@Configuration
public class KafkaTransactionConfig {
    @Bean
    public ProducerFactory<String, Object> transactionalProducerFactory() {
        Map<String, Object> config = new HashMap<>();
        config.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
        config.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "payment-tx-${spring.application.instance}");
        return new DefaultKafkaProducerFactory<>(config);
    }
}

@Service
public class TransactionalPaymentProcessor {

    @Transactional  // Spring + Kafka transaction
    @KafkaListener(topics = "payment-commands")
    public void processPaymentCommand(PaymentCommand command, Acknowledgment ack) {
        // All of this is ATOMIC — either all happens or nothing
        Payment payment = paymentRepo.save(new Payment(command)); // DB write
        kafkaTemplate.send("payment-events", payment.toEvent()); // Kafka produce
        kafkaTemplate.send("notification-events", payment.toNotification()); // Kafka produce
        ack.acknowledge(); // Consumer offset commit
        // If any step fails, ENTIRE transaction is rolled back
    }
}
```

---

## Q8: Common Kafka Interview Questions

### "What is the difference between at-most-once, at-least-once, exactly-once?"
```
At-most-once (fire-and-forget):
  Producer sends, doesn't wait for ACK
  Consumer commits before processing
  Risk: Message lost if consumer crashes

At-least-once (default):
  Producer retries on failure
  Consumer commits after processing
  Risk: Message processed multiple times on retry
  Solution: Make consumer IDEMPOTENT

Exactly-once:
  Kafka transactions + idempotent producer
  Strongest guarantee
  Higher latency - use only when critical (financial transactions)
```

### "How do you scale Kafka consumers?"
```
Rule: Max parallelism = number of partitions

10 partitions → max 10 consumers in a group
(11th consumer would be idle — no partition to assign)

Scaling steps:
1. First increase topic partitions (can only increase, never decrease!)
2. Then add more consumer instances
3. Kafka auto-rebalances assignments

In Kubernetes:
kubectl scale deployment payment-consumer --replicas=10
(assuming topic has 10+ partitions)
```

### "What is Log Compaction?"
```
Normal topics: Delete old segments based on retention time
Compacted topics: Keep ONLY the latest value per key

Use case: User preferences, product catalog (maintain latest state)

Topic config:
log.cleanup.policy=compact
log.min.cleanable.dirty.ratio=0.5
```
