# Chapter 6: Design Consistent Hashing

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-consistent-hashing)

To achieve horizontal scaling, it is important to distribute requests/data efficiently and evenly across servers. Consistent hashing is a commonly used technique to achieve this goal. But first, let us take an in-depth look at the problem.

---

## The rehashing problem

If you have *n* cache servers, a common way to balance the load is to use the following hash method:

*serverIndex = hash(key) % N*, where *N* is the size of the server pool.

Let us use an example to illustrate how it works. As shown in Table 1, we have 4 servers and 8 string keys with their hashes.

| **key** | **hash** | **hash % 4** |
|---------|----------|--------------|
| key0    | 18358617 | 1            |
| key1    | 26143584 | 0            |
| key2    | 18131146 | 2            |
| key3    | 35863496 | 0            |
| key4    | 34085809 | 1            |
| key5    | 27581703 | 3            |
| key6    | 38164978 | 2            |
| key7    | 22530351 | 3            |

*Table 1: Key distribution across 4 servers using modulo hashing.*

To fetch the server where a key is stored, we perform the modular operation *f(key) % 4*. For instance, *hash(key0) % 4 = 1* means a client must contact server 1 to fetch the cached data.

This approach works well when the size of the server pool is fixed, and the data distribution is even. However, problems arise when new servers are added, or existing servers are removed. For example, if server 1 goes offline, the size of the server pool becomes 3. Using the same hash function, we get the same hash value for a key. But applying modular operation gives us different server indexes because the number of servers is reduced by 1. We get the results as shown in Table 2 by applying *hash % 3*:

| **key** | **hash** | **hash % 3** |
|---------|----------|--------------|
| key0    | 18358617 | 0            |
| key1    | 26143584 | 0            |
| key2    | 18131146 | 1            |
| key3    | 35863496 | 2            |
| key4    | 34085809 | 1            |
| key5    | 27581703 | 0            |
| key6    | 38164978 | 1            |
| key7    | 22530351 | 0            |

*Table 2: Key distribution after server 1 goes offline — most keys are redistributed.*

As shown in Table 2, most keys are redistributed, not just the ones originally stored in the offline server (server 1). This means that when server 1 goes offline, most cache clients will connect to the wrong servers to fetch data. **This causes a storm of cache misses.** Consistent hashing is an effective technique to mitigate this problem.

---

## Consistent hashing

Quoted from Wikipedia: "Consistent hashing is a special kind of hashing such that when a hash table is re-sized and consistent hashing is used, only k/n keys need to be remapped on average, where k is the number of keys, and n is the number of slots. In contrast, in most traditional hash tables, a change in the number of array slots causes nearly all keys to be remapped."

### Hash space and hash ring

Assume SHA-1 is used as the hash function f, and the output range of the hash function is: *x0, x1, x2, x3, …, xn*. In cryptography, SHA-1's hash space goes from 0 to 2^160 - 1. That means *x0* corresponds to 0, *xn* corresponds to 2^160 – 1, and all the other hash values in the middle fall between 0 and 2^160 - 1.

By collecting both ends, we get a **hash ring**.

### Hash servers

Using the same hash function f, we map servers based on server IP or name onto the ring.

### Hash keys

One thing worth mentioning is that hash function used here is different from the one in "the rehashing problem," and there is no modular operation. Cache keys (key0, key1, key2, and key3) are hashed onto the hash ring.

### Server lookup

To determine which server a key is stored on, we go clockwise from the key position on the ring until a server is found. Going clockwise, *key0* is stored on *server 0*; *key1* is stored on *server 1*; *key2* is stored on *server 2* and *key3* is stored on *server 3*.

### Add a server

Using the logic described above, adding a new server will only require redistribution of a fraction of keys. After a new *server 4* is added, only *key0* needs to be redistributed. *k1, k2,* and *k3* remain on the same servers.

### Remove a server

When a server is removed, only a small fraction of keys require redistribution with consistent hashing. When *server 1* is removed, only *key1* must be remapped to *server 2*. The rest of the keys are unaffected.

### Java Example – Consistent Hashing Implementation

```java
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.*;

public class ConsistentHashing {

    private final TreeMap<Long, String> ring = new TreeMap<>();
    private final int numberOfVirtualNodes;

    public ConsistentHashing(List<String> servers, int numberOfVirtualNodes) {
        this.numberOfVirtualNodes = numberOfVirtualNodes;
        for (String server : servers) {
            addServer(server);
        }
    }

    public void addServer(String server) {
        for (int i = 0; i < numberOfVirtualNodes; i++) {
            long hash = hash(server + "#" + i);
            ring.put(hash, server);
        }
        System.out.println("Added server: " + server
            + " with " + numberOfVirtualNodes + " virtual nodes");
    }

    public void removeServer(String server) {
        for (int i = 0; i < numberOfVirtualNodes; i++) {
            long hash = hash(server + "#" + i);
            ring.remove(hash);
        }
        System.out.println("Removed server: " + server);
    }

    public String getServer(String key) {
        if (ring.isEmpty()) return null;

        long hash = hash(key);
        // Find the first server node clockwise on the ring
        Map.Entry<Long, String> entry = ring.ceilingEntry(hash);
        if (entry == null) {
            // Wrap around to the first entry
            entry = ring.firstEntry();
        }
        return entry.getValue();
    }

    private long hash(String key) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-1");
            byte[] digest = md.digest(key.getBytes());
            // Use the first 8 bytes for a long hash
            long hash = 0;
            for (int i = 0; i < 8; i++) {
                hash = (hash << 8) | (digest[i] & 0xFF);
            }
            return hash;
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    public static void main(String[] args) {
        List<String> servers = new ArrayList<>(
            List.of("server-0", "server-1", "server-2", "server-3")
        );

        ConsistentHashing ch = new ConsistentHashing(servers, 150);

        System.out.println("\n=== Key Distribution ===");
        Map<String, List<String>> distribution = new HashMap<>();
        String[] keys = {"user_1", "user_2", "user_3", "order_100",
                         "order_200", "session_abc", "session_xyz", "product_42"};

        for (String key : keys) {
            String server = ch.getServer(key);
            distribution.computeIfAbsent(server, k -> new ArrayList<>()).add(key);
            System.out.printf("%-20s → %s%n", key, server);
        }

        // Simulate server removal
        System.out.println("\n=== After Removing server-1 ===");
        ch.removeServer("server-1");
        for (String key : keys) {
            String server = ch.getServer(key);
            System.out.printf("%-20s → %s%n", key, server);
        }

        // Simulate adding a new server
        System.out.println("\n=== After Adding server-4 ===");
        ch.addServer("server-4");
        for (String key : keys) {
            String server = ch.getServer(key);
            System.out.printf("%-20s → %s%n", key, server);
        }
    }
}
```

---

### Two issues in the basic approach

The consistent hashing algorithm was introduced by Karger et al. at MIT. The basic steps are:

- Map servers and keys on to the ring using a uniformly distributed hash function.
- To find out which server a key is mapped to, go clockwise from the key position until the first server on the ring is found.

Two problems are identified with this approach:

1. **Uneven partitions**: It is impossible to keep the same size of partitions on the ring for all servers considering a server can be added or removed. A partition is the hash space between adjacent servers.

2. **Non-uniform key distribution**: It is possible to have a non-uniform key distribution on the ring where most keys are stored on one server.

A technique called **virtual nodes** or **replicas** is used to solve these problems.

### Virtual nodes

A virtual node refers to the real node, and each server is represented by multiple virtual nodes on the ring. Instead of using *s0*, we have *s0_0, s0_1*, and *s0_2* to represent *server 0* on the ring. Similarly, *s1_0, s1_1*, and *s1_2* represent server 1 on the ring. With virtual nodes, each server is responsible for multiple partitions.

To find which server a key is stored on, we go clockwise from the key's location and find the first virtual node encountered on the ring.

As the number of virtual nodes increases, the distribution of keys becomes more balanced. This is because the standard deviation gets smaller with more virtual nodes, leading to balanced data distribution. The outcome of an experiment shows that with one or two hundred virtual nodes, the standard deviation is between 5% (200 virtual nodes) and 10% (100 virtual nodes) of the mean. However, more spaces are needed to store data about virtual nodes. **This is a tradeoff**, and we can tune the number of virtual nodes to fit our system requirements.

### Find affected keys

When a server is added or removed, a fraction of data needs to be redistributed. How can we find the affected range to redistribute the keys?

- **When a server is added**: The affected range starts from the newly added node and moves anticlockwise around the ring until a server is found. Keys in that range need to be redistributed.

- **When a server is removed**: The affected range starts from the removed node and moves anticlockwise around the ring until a server is found. Keys in that range must be redistributed to the next server clockwise.

---

## Wrap up

In this chapter, we had an in-depth discussion about consistent hashing, including why it is needed and how it works. The benefits of consistent hashing include:

- **Minimized keys are redistributed** when servers are added or removed.
- **It is easy to scale horizontally** because data are more evenly distributed.
- **Mitigate hotspot key problem.** Excessive access to a specific shard could cause server overload. Imagine data for Katy Perry, Justin Bieber, and Lady Gaga all end up on the same shard. Consistent hashing helps to mitigate the problem by distributing the data more evenly.

Consistent hashing is widely used in real-world systems, including some notable ones:

- Partitioning component of Amazon's Dynamo database [3]
- Data partitioning across the cluster in Apache Cassandra [4]
- Discord chat application [5]
- Akamai content delivery network [6]
- Maglev network load balancer [7]

---

## Reference materials

[1] Consistent hashing: [https://en.wikipedia.org/wiki/Consistent_hashing](https://en.wikipedia.org/wiki/Consistent_hashing)

[2] Consistent Hashing: [https://tom-e-white.com/2007/11/consistent-hashing.html](https://tom-e-white.com/2007/11/consistent-hashing.html)

[3] Dynamo: Amazon's Highly Available Key-value Store: [https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)

[4] Cassandra - A Decentralized Structured Storage System: [http://www.cs.cornell.edu/Projects/ladis2009/papers/Lakshman-ladis2009.PDF](http://www.cs.cornell.edu/Projects/ladis2009/papers/Lakshman-ladis2009.PDF)

[5] How Discord Scaled Elixir to 5,000,000 Concurrent Users: [https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users](https://discord.com/blog/how-discord-scaled-elixir-to-5-000-000-concurrent-users)

[6] CS168: The Modern Algorithmic Toolbox Lecture #1: [http://theory.stanford.edu/~tim/s16/l/l1.pdf](http://theory.stanford.edu/~tim/s16/l/l1.pdf)

[7] Maglev: A Fast and Reliable Software Network Load Balancer: [https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/44824.pdf](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/44824.pdf)
