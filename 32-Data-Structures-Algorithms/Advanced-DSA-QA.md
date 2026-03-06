# 🧩 Advanced DSA — Graph Algorithms, Trie, Greedy, Bit Manipulation
## Target: 12+ Years Experience | FAANG / Product-Based Companies

---

## 1. 🌐 Advanced Graph Algorithms

### 🔥 Dijkstra's Algorithm — Shortest Path (Weighted Graph)
```java
// Find shortest path from source to all vertices in weighted graph (non-negative weights)
// Uses a Min-Heap (PriorityQueue) — greedy approach

public int[] dijkstra(int n, List<int[]>[] graph, int source) {
    // graph[u] = list of {v, weight} edges
    int[] dist = new int[n];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[source] = 0;

    // Min-heap: {distance, node}
    PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[0] - b[0]);
    pq.offer(new int[]{0, source});

    while (!pq.isEmpty()) {
        int[] curr = pq.poll();
        int d = curr[0], u = curr[1];

        if (d > dist[u]) continue; // Skip outdated entries

        for (int[] edge : graph[u]) {
            int v = edge[0], weight = edge[1];
            int newDist = dist[u] + weight;

            if (newDist < dist[v]) {
                dist[v] = newDist;
                pq.offer(new int[]{newDist, v});
            }
        }
    }
    return dist; // dist[i] = shortest distance from source to i
}
// Time: O((V + E) log V) with binary heap | Space: O(V + E)
// Use: GPS navigation, network routing, Google Maps
// LIMITATION: Does NOT work with negative edge weights → use Bellman-Ford
```

---

### 🔥 Bellman-Ford — Shortest Path (Handles Negative Weights)
```java
// Works with negative weights, detects negative cycles
public int[] bellmanFord(int n, int[][] edges, int source) {
    int[] dist = new int[n];
    Arrays.fill(dist, Integer.MAX_VALUE);
    dist[source] = 0;

    // Relax all edges (V-1) times
    for (int i = 0; i < n - 1; i++) {
        for (int[] edge : edges) {
            int u = edge[0], v = edge[1], w = edge[2];
            if (dist[u] != Integer.MAX_VALUE && dist[u] + w < dist[v]) {
                dist[v] = dist[u] + w;
            }
        }
    }

    // Detect negative cycle (Vth iteration should not improve any distance)
    for (int[] edge : edges) {
        int u = edge[0], v = edge[1], w = edge[2];
        if (dist[u] != Integer.MAX_VALUE && dist[u] + w < dist[v]) {
            throw new RuntimeException("Negative cycle detected!");
        }
    }
    return dist;
}
// Time: O(V × E) | Space: O(V)
// Slower than Dijkstra but handles negative weights
```

---

### 🔥 Union-Find (Disjoint Set Union) — Connected Components
```java
// Efficiently tracks connected components. Two key operations:
// find(x): Which group does x belong to?
// union(x, y): Merge the groups of x and y

class UnionFind {
    private int[] parent, rank;
    private int components;

    public UnionFind(int n) {
        parent = new int[n];
        rank = new int[n];
        components = n;
        for (int i = 0; i < n; i++) parent[i] = i; // Each node is its own parent
    }

    // Path compression: make every node point directly to root
    public int find(int x) {
        if (parent[x] != x) {
            parent[x] = find(parent[x]); // Compress path
        }
        return parent[x];
    }

    // Union by rank: attach smaller tree under larger tree's root
    public boolean union(int x, int y) {
        int rootX = find(x), rootY = find(y);
        if (rootX == rootY) return false; // Already connected

        if (rank[rootX] < rank[rootY]) parent[rootX] = rootY;
        else if (rank[rootX] > rank[rootY]) parent[rootY] = rootX;
        else { parent[rootY] = rootX; rank[rootX]++; }

        components--;
        return true;
    }

    public boolean connected(int x, int y) { return find(x) == find(y); }
    public int getComponents() { return components; }
}
// Time: O(α(n)) ≈ O(1) per operation (inverse Ackermann — nearly constant)
// Space: O(n)

// USE CASE: Number of Connected Components
public int countComponents(int n, int[][] edges) {
    UnionFind uf = new UnionFind(n);
    for (int[] edge : edges) uf.union(edge[0], edge[1]);
    return uf.getComponents();
}

// USE CASE: Detect Cycle in Undirected Graph
public boolean hasCycle(int n, int[][] edges) {
    UnionFind uf = new UnionFind(n);
    for (int[] edge : edges) {
        if (!uf.union(edge[0], edge[1])) return true; // Already connected = cycle!
    }
    return false;
}
```

---

### 🔥 Topological Sort — DAG Ordering (Kahn's BFS Algorithm)
```java
// Order vertices so every directed edge u→v has u before v
// Use: build systems, task scheduling, course prerequisites

public int[] topologicalSort(int n, List<List<Integer>> adj) {
    int[] inDegree = new int[n];
    for (int u = 0; u < n; u++)
        for (int v : adj.get(u)) inDegree[v]++;

    Queue<Integer> queue = new LinkedList<>();
    for (int i = 0; i < n; i++)
        if (inDegree[i] == 0) queue.offer(i); // Start with nodes having no dependencies

    int[] order = new int[n];
    int idx = 0;

    while (!queue.isEmpty()) {
        int u = queue.poll();
        order[idx++] = u;

        for (int v : adj.get(u)) {
            if (--inDegree[v] == 0) queue.offer(v); // All dependencies met
        }
    }

    if (idx != n) throw new RuntimeException("Cycle detected — topological sort impossible!");
    return order;
}
// Time: O(V + E) | Space: O(V)
```

---

## 2. 🔤 Trie (Prefix Tree)

### Theory:
A **Trie** stores strings character-by-character in a tree. Each path from root to a node represents a prefix. Used for: autocomplete, spell checker, IP routing, phone contacts.

```java
class Trie {
    private TrieNode root = new TrieNode();

    static class TrieNode {
        TrieNode[] children = new TrieNode[26]; // a-z
        boolean isEnd = false;
    }

    // Insert word — O(word.length)
    public void insert(String word) {
        TrieNode node = root;
        for (char c : word.toCharArray()) {
            int idx = c - 'a';
            if (node.children[idx] == null) {
                node.children[idx] = new TrieNode();
            }
            node = node.children[idx];
        }
        node.isEnd = true;
    }

    // Search for exact word — O(word.length)
    public boolean search(String word) {
        TrieNode node = findNode(word);
        return node != null && node.isEnd;
    }

    // Check if any word starts with prefix — O(prefix.length)
    public boolean startsWith(String prefix) {
        return findNode(prefix) != null;
    }

    private TrieNode findNode(String s) {
        TrieNode node = root;
        for (char c : s.toCharArray()) {
            int idx = c - 'a';
            if (node.children[idx] == null) return null;
            node = node.children[idx];
        }
        return node;
    }
}
// Insert/Search/StartsWith: O(L) where L = word length
// Space: O(ALPHABET_SIZE × L × N) worst case
```

---

## 3. 💰 Greedy Algorithms

### Theory:
Greedy makes the **locally optimal** choice at each step, hoping it leads to the global optimum. Works when the problem has **greedy choice property** and **optimal substructure**.

### 🔥 Activity Selection / Meeting Rooms
```java
// How many non-overlapping meetings can you attend?
// GREEDY: sort by end time, always pick the earliest ending meeting
public int maxMeetings(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[1] - b[1]); // Sort by END time
    int count = 1, lastEnd = intervals[0][1];

    for (int i = 1; i < intervals.length; i++) {
        if (intervals[i][0] >= lastEnd) { // No overlap
            count++;
            lastEnd = intervals[i][1];
        }
    }
    return count;
}
// Time: O(n log n) | Space: O(1)
```

### 🔥 Merge Intervals (Amazon, Google)
```java
public int[][] merge(int[][] intervals) {
    Arrays.sort(intervals, (a, b) -> a[0] - b[0]); // Sort by START time
    List<int[]> merged = new ArrayList<>();
    merged.add(intervals[0]);

    for (int i = 1; i < intervals.length; i++) {
        int[] last = merged.get(merged.size() - 1);
        if (intervals[i][0] <= last[1]) { // Overlapping
            last[1] = Math.max(last[1], intervals[i][1]); // Extend end
        } else {
            merged.add(intervals[i]); // No overlap — new interval
        }
    }
    return merged.toArray(new int[0][]);
}
// Time: O(n log n) | Space: O(n)
```

### 🔥 Jump Game (Can you reach the last index?)
```java
public boolean canJump(int[] nums) {
    int maxReach = 0;
    for (int i = 0; i < nums.length; i++) {
        if (i > maxReach) return false; // Can't reach this position
        maxReach = Math.max(maxReach, i + nums[i]);
    }
    return true;
}
// Time: O(n) | Space: O(1)
```

---

## 4. 🔢 Bit Manipulation

### Common Operations:
```java
// Check if nth bit is set
boolean isSet = (num & (1 << n)) != 0;

// Set nth bit
num = num | (1 << n);

// Clear nth bit
num = num & ~(1 << n);

// Toggle nth bit
num = num ^ (1 << n);

// Check if power of 2
boolean isPow2 = (n > 0) && (n & (n - 1)) == 0;
// WHY: powers of 2 have exactly one bit set: 1000...0
//      n-1 flips all bits after that: 0111...1
//      AND gives 0!

// Count set bits (Brian Kernighan's algorithm)
public int countBits(int n) {
    int count = 0;
    while (n != 0) {
        n &= (n - 1); // Removes lowest set bit
        count++;
    }
    return count;
}
// Time: O(number of set bits) | Space: O(1)
```

### 🔥 Single Number (XOR trick)
```java
// Every element appears twice except one. Find the unique element.
public int singleNumber(int[] nums) {
    int result = 0;
    for (int num : nums) {
        result ^= num; // XOR: a^a=0, a^0=a
    }
    return result;
}
// Time: O(n) | Space: O(1)
// WHY: [4,1,2,1,2] → 4^1^2^1^2 = 4^(1^1)^(2^2) = 4^0^0 = 4
```

---

## 📊 Algorithm Pattern Recognition Cheat Sheet

| If you see... | Think... | Data Structure |
|--------------|----------|----------------|
| "Top K / Kth largest" | Heap | PriorityQueue |
| "Find shortest path" | BFS (unweighted), Dijkstra (weighted) | Queue, PriorityQueue |
| "Connected components" | Union-Find or DFS | UnionFind / Stack |
| "Prefix matching" | Trie | Trie |
| "Substring / window" | Sliding Window | HashMap + two pointers |
| "Sorted array search" | Binary Search | Array |
| "Tree traversal" | DFS (recursive) or BFS | Stack / Queue |
| "Parentheses / nesting" | Stack | Stack |
| "O(1) lookup" | Hashing | HashMap / HashSet |
| "Count ways / min cost" | Dynamic Programming | Array (1D/2D) |
| "Explore all possibilities" | Backtracking | Recursion |
| "Scheduling / intervals" | Greedy (sort by end time) | Sorting |
| "Unique element / XOR" | Bit Manipulation | XOR |
