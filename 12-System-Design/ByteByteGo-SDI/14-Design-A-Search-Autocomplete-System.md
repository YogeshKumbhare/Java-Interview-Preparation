# Chapter 14: Design A Search Autocomplete System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-search-autocomplete-system)

When searching on Google or shopping at Amazon, as you type in the search box, one or more matches for the search term are presented to you. This feature is referred to as autocomplete, typeahead, search-as-you-type, or incremental search. Search autocomplete is an important feature of many products. This leads us to the interview question: design a search autocomplete system, also called "design top k" or "design top k most searched queries".

![Figure 1 – Autocomplete Example](images/ch14/figure-1.png)

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: Is the matching only supported at the beginning of a search query or in the middle as well?
**Interviewer**: Only at the beginning of a search query.

**Candidate**: How many autocomplete suggestions should the system return?
**Interviewer**: 5

**Candidate**: How does the system know which 5 suggestions to return?
**Interviewer**: This is determined by popularity, decided by the historical query frequency.

**Candidate**: Does the system support spell check?
**Interviewer**: No, spell check or autocorrect is not supported.

**Candidate**: Are search queries in English?
**Interviewer**: Yes. If time allows at the end, we can discuss multi-language support.

**Candidate**: Do we allow capitalization and special characters?
**Interviewer**: No, we assume all search queries have lowercase alphabetic characters.

**Candidate**: How many users use the product?
**Interviewer**: 10 million DAU.

**Requirements Summary:**
- Fast response time: results within 100 milliseconds
- Relevant: suggestions relevant to the search term
- Sorted: results sorted by popularity or other ranking models
- Scalable: handles high traffic volume
- Highly available: remains available when part of the system is offline

**Back of the envelope estimation:**
- 10 million DAU, 10 searches per day
- 20 bytes of data per query string (4 words × 5 characters = 20 bytes)
- ~24,000 QPS = 10M * 10 queries * 20 characters / 24h / 3600s
- Peak QPS = ~48,000
- 0.4 GB of new data added to storage daily (20% new queries)

---

## Step 2 - Propose high-level design and get buy-in

At the high-level, the system is broken down into two:

- **Data gathering service**: Gathers user input queries and aggregates them in real-time.
- **Query service**: Given a search query or prefix, return 5 most frequently searched terms.

### Data gathering service

A frequency table that stores the query string and its frequency. When users type queries, the frequency table is updated.

![Figure 2 – Frequency Table](images/ch14/figure-2.png)

### Query service

| Query | Frequency |
|-------|-----------|
| twitter | 35 |
| twitch | 29 |
| twilight | 25 |
| twin peak | 21 |
| twitch prime | 18 |
| twitter search | 14 |
| twillo | 10 |
| twin peak sf | 8 |

When a user types "tw", the top 5 searched queries are displayed. SQL query to get top 5:

![Figure 4 – SQL Query](images/ch14/figure-4.png)

This is acceptable when the data set is small. When it is large, accessing the database becomes a bottleneck.

---

## Step 3 - Design deep dive

### Trie data structure

Relational databases are inefficient for fetching top 5 search queries. The **trie (prefix tree)** data structure overcomes this problem.

A trie is a tree-like data structure that can compactly store strings. The name comes from the word retrieval.

- A trie is a tree-like data structure.
- The root represents an empty string.
- Each node stores a character and has 26 children, one for each possible character.
- Each tree node represents a single word or a prefix string.

![Figure 5 – Trie Structure](images/ch14/figure-5.png)

Basic trie with frequency info added:

| Query | Frequency |
|-------|-----------|
| tree | 10 |
| try | 29 |
| true | 35 |
| toy | 14 |
| wish | 25 |
| win | 50 |

![Figure 6 – Trie with Frequency](images/ch14/figure-6.png)

**Algorithm to get top k most searched queries:**

1. Find the prefix. Time complexity: O(p).
2. Traverse the subtree from the prefix node to get all valid children. Time complexity: O(c)
3. Sort the children and get top k. Time complexity: O(clogc)

Total time complexity: O(p) + O(c) + O(clogc)

**Two optimizations:**

1. **Limit the max length of a prefix**: It is safe to say p is a small integer, say 50. Reduces time complexity to O(1).

2. **Cache top search queries at each node**: Store top k most frequently used queries at each node.

![Figure 8 – Trie with Cached Top Queries](images/ch14/figure-8.png)

After applying optimizations: each step is O(1), so the algorithm is O(1).

### Data gathering service

Updating the trie on every query is not practical:
- Users enter billions of queries per day.
- Top suggestions may not change much once the trie is built.

![Figure 9 – Data Gathering Service](images/ch14/figure-9.png)

- **Analytics Logs**: Stores raw data about search queries. Logs are append-only.
- **Aggregators**: Aggregate data, e.g., rebuild trie weekly.
- **Workers**: Build the trie data structure and store it in Trie DB.
- **Trie Cache**: Distributed cache system keeping trie in memory for fast read.
- **Trie DB**: Persistent storage. Two options:
  1. Document store (MongoDB) — periodic snapshot of trie
  2. Key-value store — every prefix mapped to a key

### Query service

![Figure 11 – Improved Query Service](images/ch14/figure-11.png)

1. A search query is sent to the load balancer.
2. The load balancer routes the request to API servers.
3. API servers get trie data from Trie Cache and construct autocomplete suggestions.
4. On cache miss, replenish data from Trie DB.

**Query service optimizations:**
- **AJAX request**: Allows sending/receiving without refreshing the whole web page.
- **Browser caching**: Google caches results in browser for 1 hour (`Cache-Control: private, max-age=3600`).
- **Data sampling**: Only 1 out of every N requests is logged.

### Trie operations

**Create**: Trie is created by workers using aggregated data from Analytics Log/DB.

**Update:**
- Option 1: Update the trie weekly.
- Option 2: Update individual trie node directly (slow, avoid for large tries).

**Delete**: Add a filter layer in front of Trie Cache to filter out hateful, violent, or illegal suggestions.

![Figure 14 – Filter Layer](images/ch14/figure-14.png)

### Scale the storage

To shard: divide based on first character. If we need 26 servers, split by 'a' to 'z'. To analyze data imbalance, use a **shard map manager** with lookup tables.

![Figure 15 – Shard Map](images/ch14/figure-15.png)

### Java Example – Trie Autocomplete

```java
import java.util.*;

public class TrieAutocomplete {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        Map<String, Integer> topQueries = new HashMap<>(); // cached top k
    }

    private final TrieNode root = new TrieNode();
    private static final int TOP_K = 5;

    public void insert(String word, int frequency) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            node.children.putIfAbsent(c, new TrieNode());
            node = node.children.get(c);
            updateTopQueries(node.topQueries, word, frequency);
        }
    }

    private void updateTopQueries(Map<String, Integer> topQueries, String word, int freq) {
        topQueries.put(word, freq);
        if (topQueries.size() > TOP_K) {
            String minKey = Collections.min(topQueries.entrySet(),
                Map.Entry.comparingByValue()).getKey();
            topQueries.remove(minKey);
        }
    }

    public List<String> search(String prefix) {
        TrieNode node = root;
        for (char c : prefix.toCharArray()) {
            if (!node.children.containsKey(c)) return List.of();
            node = node.children.get(c);
        }
        return node.topQueries.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .map(Map.Entry::getKey)
            .toList();
    }

    public static void main(String[] args) {
        TrieAutocomplete trie = new TrieAutocomplete();
        trie.insert("twitter", 35);
        trie.insert("twitch", 29);
        trie.insert("twilight", 25);
        trie.insert("twin peak", 21);
        trie.insert("twitch prime", 18);
        trie.insert("twitter search", 14);

        System.out.println("Autocomplete 'tw': " + trie.search("tw"));
        System.out.println("Autocomplete 'twi': " + trie.search("twi"));
    }
}
```

---

## Step 4 - Wrap up

**Interviewer**: How do you extend your design to support multiple languages?
**Answer**: Store Unicode characters in trie nodes.

**Interviewer**: What if top search queries in one country are different from others?
**Answer**: Build different tries for different countries. Store tries in CDNs.

**Interviewer**: How can we support the trending (real-time) search queries?
**Answer**: Reduce the working data set by sharding. Change the ranking model to assign more weight to recent search queries. Use stream processing: Apache Kafka, Apache Storm, Apache Spark Streaming.

---

## Reference materials

[1] The Life of a Typeahead Query: https://www.facebook.com/notes/facebook-engineering/the-life-of-a-typeahead-query/389105248919/

[2] How We Built Prefixy: https://medium.com/@prefixyteam/how-we-built-prefixy-a-scalable-prefix-search-service-for-powering-autocomplete-c20f98e2eff1

[3] MongoDB wikipedia: https://en.wikipedia.org/wiki/MongoDB

[4] Unicode frequently asked questions: https://www.unicode.org/faq/basic_q.html

[5] Apache kafka: https://kafka.apache.org/documentation/
