# Chapter 14: Design A Search Autocomplete System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-search-autocomplete-system)

When you type in the Google search box, suggestions appear below. This feature is called autocomplete, typeahead, search-as-you-type, or incremental search.

---

## Step 1 - Understand the problem and establish design scope

**Requirements:**
- Fast response time: autocomplete suggestions must appear within 100 milliseconds
- Relevant: suggestions should be relevant to the search term
- Sorted: results sorted by popularity or other ranking models
- Scalable: handle high traffic volume
- Highly available

**Back of the envelope estimation:**
- 10 million DAU
- Average 10 searches per user per day → 100 million queries/day
- Average 20 bytes per query string
- ~20 requests per query (one per character typed) with caching
- ~24,000 QPS; peak ~48,000 QPS

---

## Step 2 - High-level design

The system is broken into two parts:

### Data gathering service
- Gathers user search queries and aggregates them in real-time
- Frequency table stores query strings with their frequency
- Analytics logs → Aggregators → update frequency table

### Query service
- Given a search query, return top 5 most frequently searched terms
- Uses a **Trie** (prefix tree) data structure for efficient prefix matching

### Java Example – Trie-based Autocomplete

```java
import java.util.*;

public class AutocompleteSystem {

    static class TrieNode {
        Map<Character, TrieNode> children = new HashMap<>();
        Map<String, Integer> topQueries = new HashMap<>(); // query → frequency
    }

    private final TrieNode root = new TrieNode();

    public void addQuery(String query, int frequency) {
        TrieNode node = root;
        for (char c : query.toLowerCase().toCharArray()) {
            node = node.children.computeIfAbsent(c, k -> new TrieNode());
            // Update top queries at each node
            node.topQueries.merge(query, frequency, Integer::sum);
            // Keep only top 5
            if (node.topQueries.size() > 10) {
                node.topQueries.entrySet().stream()
                    .sorted(Map.Entry.comparingByValue())
                    .limit(node.topQueries.size() - 5)
                    .forEach(e -> node.topQueries.remove(e.getKey()));
            }
        }
    }

    public List<String> search(String prefix) {
        TrieNode node = root;
        for (char c : prefix.toLowerCase().toCharArray()) {
            node = node.children.get(c);
            if (node == null) return List.of();
        }
        return node.topQueries.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .limit(5)
            .map(Map.Entry::getKey)
            .toList();
    }

    public static void main(String[] args) {
        AutocompleteSystem ac = new AutocompleteSystem();

        // Populate with search queries and frequencies
        ac.addQuery("system design", 5000);
        ac.addQuery("system design interview", 3000);
        ac.addQuery("system of a down", 800);
        ac.addQuery("systematic", 500);
        ac.addQuery("sydney opera house", 400);
        ac.addQuery("syntax error", 300);

        System.out.println("=== Autocomplete Results ===");
        System.out.println("'sys' → " + ac.search("sys"));
        System.out.println("'system d' → " + ac.search("system d"));
        System.out.println("'syd' → " + ac.search("syd"));
    }
}
```

---

## Step 3 - Design deep dive

### Trie data structure

Each node stores:
- Children (26 characters or map-based)
- Cached top K queries at each node (optimization: avoids traversing all descendants)

**Time complexity**: O(p) where p is the length of the prefix

### Data gathering service (deep dive)

- Real-time updates are impractical at Google scale — update trie weekly/periodically
- **Analytics logs** → **Aggregators** (aggregate weekly) → **Aggregated data** → **Workers** → update Trie DB → **Trie Cache**
- Workers build trie from aggregated data and serialize to Trie DB

### Query service (deep dive)

1. Search query sent to load balancer
2. API servers check Trie Cache (Redis)
3. If not in cache, look up Trie DB and fill cache
4. Return top 5 results

**Optimizations:**
- AJAX requests (no full page reload)
- Browser caching (autocomplete results cached client-side)
- Data sampling (only log 1 in N queries)

### Trie operations

- **Create**: Built offline by workers from aggregated data
- **Update**: Two options — update weekly (replace whole trie) or update individual nodes directly
- **Delete**: Add a filter layer to remove hateful, violent, or dangerous autocomplete suggestions

### Scale the storage

- Shard by first character: 'a' → shard 1, 'b' → shard 2
- More even: shard by hash of first two characters
- Handle uneven distribution with a shard map manager

---

## Step 4 - Wrap up

Additional talking points:
- **Multi-language support**: Unicode trie nodes
- **Real-time search queries**: Different ranking model for trending topics
- **Country-specific results**: Different tries per country
- **Trending (real-time) searches**: Separate short-lived data structure for recent spikes
