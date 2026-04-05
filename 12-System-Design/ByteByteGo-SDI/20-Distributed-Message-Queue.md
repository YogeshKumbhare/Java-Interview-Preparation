# Chapter 20: Distributed Message Queue

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/distributed-message-queue)

Design a distributed message queue like Apache Kafka, RabbitMQ, or Amazon SQS.

---

## Step 1 - Understand the problem and establish design scope

**Functional requirements:** Producers send messages, consumers consume messages. Messages can be consumed repeatedly or only once. Historical data can be truncated. Message size is in KB range. Deliver messages in order within a partition. Configurable delivery semantics: at-least-once, at-most-once, exactly-once.

**Non-functional:** High throughput or low latency (configurable), scalable, persistent and durable.

---

## Step 2 - High-level design

### Messaging models

1. **Point-to-point**: A message consumed by only one consumer. Used for task distribution.
2. **Publish-subscribe**: A message delivered to all subscribed consumers. Used for event broadcasting.

### Key concepts

- **Topic**: A logical category for messages
- **Partition**: Each topic split into partitions for parallel processing
- **Producer**: Publishes messages to topics
- **Consumer**: Subscribes to topics and reads messages
- **Consumer group**: A group of consumers that jointly consume messages from a topic (each partition consumed by exactly one consumer in the group)
- **Broker**: A server that stores messages
- **Offset**: Position of a message within a partition

### Architecture

Producers → Brokers (with Partitions) → Consumers

Coordination service (ZooKeeper): Leader election, service discovery, cluster metadata.

### Java Example – Simple Message Queue

```java
import java.util.*;
import java.util.concurrent.*;

public class DistributedMessageQueue {

    record Message(String key, String value, long timestamp, int partition) {}

    static class Topic {
        final String name;
        final int numPartitions;
        final List<Queue<Message>> partitions;
        final Map<String, long[]> consumerOffsets = new ConcurrentHashMap<>();

        Topic(String name, int numPartitions) {
            this.name = name;
            this.numPartitions = numPartitions;
            this.partitions = new ArrayList<>();
            for (int i = 0; i < numPartitions; i++) {
                partitions.add(new ConcurrentLinkedQueue<>());
            }
        }

        int getPartition(String key) {
            return Math.abs(key.hashCode()) % numPartitions;
        }
    }

    private final Map<String, Topic> topics = new ConcurrentHashMap<>();

    public void createTopic(String name, int partitions) {
        topics.put(name, new Topic(name, partitions));
        System.out.println("Created topic: " + name + " with " + partitions + " partitions");
    }

    public void produce(String topicName, String key, String value) {
        Topic topic = topics.get(topicName);
        int partition = topic.getPartition(key);
        Message msg = new Message(key, value, System.currentTimeMillis(), partition);
        topic.partitions.get(partition).offer(msg);
        System.out.printf("[PRODUCE] %s → partition %d: {%s: %s}%n",
            topicName, partition, key, value);
    }

    public Message consume(String topicName, int partition) {
        Topic topic = topics.get(topicName);
        return topic.partitions.get(partition).poll();
    }

    public static void main(String[] args) {
        DistributedMessageQueue mq = new DistributedMessageQueue();
        mq.createTopic("orders", 3);

        // Produce messages
        mq.produce("orders", "order-1001", "iPhone 15 Pro");
        mq.produce("orders", "order-1002", "MacBook Air M3");
        mq.produce("orders", "order-1003", "AirPods Pro");
        mq.produce("orders", "order-1004", "iPad Mini");

        // Consume from each partition
        System.out.println("\n=== Consuming ===");
        for (int p = 0; p < 3; p++) {
            Message msg;
            while ((msg = mq.consume("orders", p)) != null) {
                System.out.printf("[CONSUME] partition %d: {%s: %s}%n",
                    p, msg.key(), msg.value());
            }
        }
    }
}
```

---

## Step 3 - Design deep dive

### Data storage
- **Write-ahead log (WAL)**: Messages appended to log files on disk
- Append-only → sequential writes → very fast (disk sequential I/O > random memory I/O)
- Segment files: rotate log files, old segments can be deleted/compacted

### Message delivery semantics

| Semantic | Description | Use Case |
|----------|-------------|----------|
| At-most-once | Commit offset before processing. Message may be lost. | Metrics where some loss OK |
| At-least-once | Commit offset after processing. May have duplicates. | Most common. Idempotent consumers. |
| Exactly-once | Combine dedup + idempotent writes + transactions | Financial transactions |

### Consumer rebalancing
When consumers join/leave a group, partitions are reassigned.

### Replication
- Each partition has one leader and N-1 followers
- Producer writes to leader, leader replicates to followers
- **ISR** (In-Sync Replicas): Only replicas that are caught up
- **ACK modes**: ack=0 (fire and forget), ack=1 (leader only), ack=all (all ISR)

---

## Step 4 - Wrap up

Additional talking points:
- **Dead letter queue**: For messages that cannot be processed
- **Message ordering guarantees**
- **Schema evolution** (Avro, Protobuf)
- **Backpressure handling**
- **Monitoring**: Consumer lag, throughput metrics
