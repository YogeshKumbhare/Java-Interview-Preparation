# 🧩 Data Structures & Algorithms (DSA) — Top Company Interview Guide
## Target: 12+ Years Experience | FAANG / Product-Based Companies

---

## 📖 Why DSA still matters at 12+ years?

At top-tier companies (Google, Amazon, Microsoft, JP Morgan, Goldman Sachs, Uber, Netflix), even senior engineers are tested on DSA. The reason is simple: your approach to DSA reveals **how you think**, not just what you know.

They test:
1. **Problem decomposition** — Can you break down the problem?
2. **Data structure selection** — Do you know WHY you chose that structure?
3. **Complexity analysis** — Can you prove time & space complexity?
4. **Edge cases** — Do you handle nulls, empty inputs, duplicates?
5. **Optimization** — Can you go from O(n²) to O(n)?

### How to read this module:
Each data structure section covers:
- **Theory** (what, why, internals)
- **Most frequently asked problems** (with categories)
- **Java implementation** with comments
- **Time & Space Complexity Table**
- **Cross-questioning scenarios**

---

## 1. 📦 Arrays & Strings

### 📖 Theory:
An **Array** is a contiguous block of memory storing elements of the same type. Direct access by index is O(1) because the memory address is computed as: `base_address + index × element_size`.

**Why it's the most common interview topic:** Arrays are the simplest structure, but mastering them requires understanding sliding windows, two pointers, prefix sums, and in-place algorithms.

### Complexity Table:
| Operation | Array | Dynamic Array (ArrayList) |
|-----------|-------|--------------------------|
| Access by index | O(1) | O(1) |
| Search (unsorted) | O(n) | O(n) |
| Insert at end | N/A | O(1) amortized |
| Insert at middle | O(n) | O(n) |
| Delete | O(n) | O(n) |

---

### 🔥 Problem 1: Two Sum (Most asked — Amazon, Google)
**Pattern:** Hash Map for O(n) lookup
```java
// Find two indices in array whose values sum to target
// NAIVE: O(n²) — nested loops checking all pairs
// OPTIMAL: O(n) — one pass with HashMap

public int[] twoSum(int[] nums, int target) {
    // Map stores: value → its index
    Map<Integer, Integer> seen = new HashMap<>();

    for (int i = 0; i < nums.length; i++) {
        int complement = target - nums[i]; // What do I need to complete the sum?

        if (seen.containsKey(complement)) {
            // Found it! complement was seen earlier at seen.get(complement)
            return new int[]{seen.get(complement), i};
        }
        // Store current number and its index for future lookups
        seen.put(nums[i], i);
    }
    return new int[]{}; // No solution found
}
// Time: O(n) — single pass | Space: O(n) — HashMap stores at most n entries
```

---

### 🔥 Problem 2: Sliding Window Maximum (Google, Microsoft)
**Pattern:** Sliding Window with Deque (monotonic)
```java
// Given array and window size k, find max in each sliding window
// NAIVE: O(n*k) — scan every window
// OPTIMAL: O(n) — monotonic deque stores indices of useful elements

public int[] maxSlidingWindow(int[] nums, int k) {
    int n = nums.length;
    int[] result = new int[n - k + 1];
    // Deque stores INDICES, front always has index of the MAX for current window
    Deque<Integer> deque = new ArrayDeque<>();

    for (int i = 0; i < n; i++) {
        // 1. Remove indices that are out of the current window from front
        while (!deque.isEmpty() && deque.peekFirst() < i - k + 1) {
            deque.pollFirst();
        }

        // 2. Remove indices from back whose VALUES are smaller than current
        //    (they can never be max while nums[i] is in the window)
        while (!deque.isEmpty() && nums[deque.peekLast()] < nums[i]) {
            deque.pollLast();
        }

        deque.addLast(i); // Add current index

        // 3. Start recording results only once first window is complete
        if (i >= k - 1) {
            result[i - k + 1] = nums[deque.peekFirst()]; // Front = max of window
        }
    }
    return result;
}
// Time: O(n) — each element added and removed from deque at most once
// Space: O(k) — deque holds at most k elements
```

---

### 🔥 Problem 3: Longest Substring Without Repeating Characters (FAANG classic)
**Pattern:** Sliding Window with HashMap
```java
public int lengthOfLongestSubstring(String s) {
    Map<Character, Integer> lastIndex = new HashMap<>(); // char → last seen index
    int maxLen = 0;
    int left = 0; // Left boundary of current valid window

    for (int right = 0; right < s.length(); right++) {
        char c = s.charAt(right);

        // If char seen before AND its last position is within current window
        if (lastIndex.containsKey(c) && lastIndex.get(c) >= left) {
            // Shrink window: move left pointer past the duplicate
            left = lastIndex.get(c) + 1;
        }

        lastIndex.put(c, right); // Update last seen index of char
        maxLen = Math.max(maxLen, right - left + 1); // Update max
    }
    return maxLen;
}
// Time: O(n) | Space: O(min(m, n)) where m = charset size (128 for ASCII)
// Example: "abcabcbb" → 3 ("abc"), "bbbbb" → 1 ("b"), "pwwkew" → 3 ("wke")
```

---

### 🔥 Problem 4: Subarray Sum Equals K (Amazon, Facebook)
**Pattern:** Prefix Sum + HashMap
```java
// Count number of contiguous subarrays with sum equal to k
// KEY INSIGHT: prefixSum[j] - prefixSum[i] = k means subarray [i+1..j] sums to k
// So: we need prefixSum[i] = prefixSum[j] - k

public int subarraySum(int[] nums, int k) {
    Map<Integer, Integer> prefixCount = new HashMap<>();
    prefixCount.put(0, 1); // Empty subarray has sum 0 (handles subarrays starting at index 0)

    int sum = 0, count = 0;

    for (int num : nums) {
        sum += num; // Running prefix sum up to this index

        // How many times has (sum - k) appeared as a prefix sum?
        // Each occurrence means we found a valid subarray ending here
        count += prefixCount.getOrDefault(sum - k, 0);

        // Record this prefix sum
        prefixCount.merge(sum, 1, Integer::sum); // Increment count for this sum
    }
    return count;
}
// Time: O(n) | Space: O(n)
// Example: [1,1,1], k=2 → 2 (subarrays [1,1] at positions [0,1] and [1,2])
```

---

## 2. 🔗 Linked List

### 📖 Theory:
A **Linked List** is a sequence of nodes where each node stores data and a pointer to the next node. Unlike arrays, nodes are NOT contiguous in memory.

**Why Linked Lists appear in interviews:**
- Tests pointer manipulation skill
- Cycle detection, reversal, and merge patterns are universally applicable
- Many advanced structures (LRU Cache, Graph adjacency lists) are built on linked lists

**Key properties:**
- Access: O(n) — must traverse from head
- Insert/Delete at known position: O(1)
- Insert/Delete by value: O(n) to find + O(1) to remove

```java
// Standard ListNode definition (used in all problems below)
public class ListNode {
    int val;
    ListNode next;
    ListNode(int val) { this.val = val; }
}
```

---

### 🔥 Problem 5: Reverse a Linked List (Every company asks this)
**Pattern:** Iterative pointer manipulation
```java
public ListNode reverseList(ListNode head) {
    ListNode prev = null;    // Will become new tail (points to null)
    ListNode curr = head;    // Start at head

    while (curr != null) {
        ListNode nextTemp = curr.next; // Save next node before we overwrite curr.next!
        curr.next = prev;              // Reverse the pointer
        prev = curr;                   // Move prev forward
        curr = nextTemp;               // Move curr forward
    }
    // When curr is null, prev is at the original tail = new head
    return prev;
}
// Time: O(n) — single pass | Space: O(1) — in-place, no extra storage
// Trace: 1->2->3->null  becomes  null<-1<-2<-3 (return 3)

// RECURSIVE VERSION (understand both for follow-up questions)
public ListNode reverseListRecursive(ListNode head) {
    if (head == null || head.next == null) return head; // Base case

    ListNode newHead = reverseListRecursive(head.next); // Recurse to end
    head.next.next = head; // Node after head points BACK to head
    head.next = null;       // Head now points to null (it's the new tail)
    return newHead;
}
// Time: O(n) | Space: O(n) — recursion call stack depth
```

---

### 🔥 Problem 6: Detect Cycle in Linked List (Floyd's Algorithm)
**Pattern:** Fast and Slow Pointer (Floyd's Tortoise & Hare)
```java
// A cycle exists when following next pointers brings you to a node you've visited

// PHASE 1: Detect if cycle exists
public boolean hasCycle(ListNode head) {
    ListNode slow = head; // Moves 1 step at a time (tortoise)
    ListNode fast = head; // Moves 2 steps at a time (hare)

    while (fast != null && fast.next != null) {
        slow = slow.next;       // +1
        fast = fast.next.next;  // +2

        if (slow == fast) return true; // They met inside the cycle!
    }
    return false; // fast reached null → no cycle
}

// PHASE 2: Find the STARTING NODE of the cycle (bonus question!)
public ListNode detectCycleStart(ListNode head) {
    ListNode slow = head, fast = head;

    // First: detect meeting point
    while (fast != null && fast.next != null) {
        slow = slow.next;
        fast = fast.next.next;
        if (slow == fast) break;
    }
    if (fast == null || fast.next == null) return null; // No cycle

    // KEY INSIGHT (mathematical proof):
    // Distance from head to cycle start = distance from meeting point to cycle start
    // So: reset one pointer to head, advance both 1 step at a time
    slow = head;
    while (slow != fast) {
        slow = slow.next;
        fast = fast.next; // Now moving at SAME speed
    }
    return slow; // Both pointers meet at cycle start!
}
// Time: O(n) | Space: O(1)
```

---

### 🔥 Problem 7: Merge Two Sorted Lists (Amazon, Microsoft)
```java
public ListNode mergeTwoLists(ListNode list1, ListNode list2) {
    // Dummy head simplifies edge cases (avoids null-checking the starting node)
    ListNode dummy = new ListNode(0);
    ListNode curr = dummy;

    while (list1 != null && list2 != null) {
        if (list1.val <= list2.val) {
            curr.next = list1;
            list1 = list1.next;
        } else {
            curr.next = list2;
            list2 = list2.next;
        }
        curr = curr.next;
    }
    // Attach the remaining portion of the non-exhausted list
    curr.next = (list1 != null) ? list1 : list2;

    return dummy.next; // Skip the dummy placeholder
}
// Time: O(m + n) | Space: O(1) — in-place linking
```

---

### 🔥 Problem 8: LRU Cache (Every senior interview — JP Morgan, Goldman, Amazon)
**Pattern:** HashMap + Doubly Linked List
```java
// LRU Cache: O(1) get and put
// HashMap: key → node (for O(1) access)
// Doubly Linked List: maintains LRU order (head = most recent, tail = least recent)

class LRUCache {
    private final int capacity;
    private final Map<Integer, Node> cache = new HashMap<>();

    // Doubly linked list sentinels (dummy nodes avoid null checks)
    private final Node head = new Node(0, 0); // Most recently used side
    private final Node tail = new Node(0, 0); // Least recently used side

    // Node structure for doubly linked list
    static class Node {
        int key, val;
        Node prev, next;
        Node(int k, int v) { key = k; val = v; }
    }

    public LRUCache(int capacity) {
        this.capacity = capacity;
        head.next = tail; // Initial state: head <-> tail
        tail.prev = head;
    }

    public int get(int key) {
        if (!cache.containsKey(key)) return -1;
        Node node = cache.get(key);
        moveToFront(node); // Mark as most recently used
        return node.val;
    }

    public void put(int key, int value) {
        if (cache.containsKey(key)) {
            Node node = cache.get(key);
            node.val = value;
            moveToFront(node); // Already exists — update and mark recent
        } else {
            if (cache.size() == capacity) {
                // EVICT: Remove the least recently used (node just before tail)
                Node lru = tail.prev;
                remove(lru);
                cache.remove(lru.key);
            }
            Node newNode = new Node(key, value);
            insertAtFront(newNode);
            cache.put(key, newNode);
        }
    }

    // Remove a node from the doubly linked list
    private void remove(Node node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
    }

    // Insert right after head (most recently used position)
    private void insertAtFront(Node node) {
        node.next = head.next;
        node.prev = head;
        head.next.prev = node;
        head.next = node;
    }

    private void moveToFront(Node node) {
        remove(node);
        insertAtFront(node);
    }
}
// get: O(1) | put: O(1) | Space: O(capacity)
```

---

## 3. 📚 Stack & Queue

### 📖 Theory:
- **Stack:** LIFO (Last In, First Out). `push()` and `pop()` from the same end.
- **Queue:** FIFO (First In, First Out). `offer()` at rear, `poll()` from front.

**Real-world analogy:**
- Stack = Undo history in VS Code (last action undone first)
- Queue = Print queue (first document sent prints first)

**Java implementations:**
- Stack: Use `Deque<T>` with `ArrayDeque` (faster than `java.util.Stack`)
- Queue: Use `ArrayDeque` as `Queue<T>` or `LinkedList`

---

### 🔥 Problem 9: Valid Parentheses (Universal classic)
```java
// Given string of brackets, determine if they are correctly balanced and nested
public boolean isValid(String s) {
    Deque<Character> stack = new ArrayDeque<>();

    for (char c : s.toCharArray()) {
        // Push opening brackets onto stack
        if (c == '(' || c == '{' || c == '[') {
            stack.push(c);
        } else {
            // Closing bracket: check if top of stack is matching opener
            if (stack.isEmpty()) return false; // Nothing to match with

            char top = stack.pop();
            if (c == ')' && top != '(') return false;
            if (c == '}' && top != '{') return false;
            if (c == ']' && top != '[') return false;
        }
    }
    // Valid only if all openers were matched (stack is empty)
    return stack.isEmpty();
}
// Time: O(n) | Space: O(n)
```

---

### 🔥 Problem 10: Min Stack — O(1) getMin (Amazon, Bloomberg)
```java
// Design a stack that supports push, pop, top, and retrieving the minimum element in O(1)
class MinStack {
    private final Deque<Integer> stack = new ArrayDeque<>();
    private final Deque<Integer> minStack = new ArrayDeque<>(); // Tracks minimums

    public void push(int val) {
        stack.push(val);
        // Push to minStack only if val <= current min (or minStack is empty)
        int currentMin = minStack.isEmpty() ? val : minStack.peek();
        minStack.push(Math.min(val, currentMin));
        // minStack top always holds the minimum for all elements currently in stack
    }

    public void pop() {
        stack.pop();
        minStack.pop(); // Pop both stacks together to stay in sync
    }

    public int top() { return stack.peek(); }

    public int getMin() { return minStack.peek(); } // O(1)!
}
// All operations: O(1) | Space: O(n) — two synchronized stacks
```

---

### 🔥 Problem 11: Next Greater Element (Monotonic Stack Pattern)
```java
// For each element, find the next element to the right that is greater
// NAIVE: O(n²) | OPTIMAL: O(n) using monotonic stack

public int[] nextGreaterElement(int[] nums) {
    int n = nums.length;
    int[] result = new int[n];
    Arrays.fill(result, -1); // Default: -1 if no greater element exists

    // Stack stores INDICES of elements waiting for their "next greater"
    Deque<Integer> stack = new ArrayDeque<>(); // Monotonic decreasing stack

    for (int i = 0; i < n; i++) {
        // Pop all elements smaller than nums[i] — nums[i] IS their next greater!
        while (!stack.isEmpty() && nums[stack.peek()] < nums[i]) {
            int idx = stack.pop();
            result[idx] = nums[i]; // Found next greater for element at idx
        }
        stack.push(i); // Push current index (still waiting for its next greater)
    }
    return result; // Remaining elements in stack got -1 (already filled)
}
// Time: O(n) — each element pushed & popped from stack exactly once
// Space: O(n) — stack holds at most n elements
// Example: [2,1,2,4,3] → [4,2,4,-1,-1]
```

---

## 4. 🌳 Trees (Binary Tree & BST)

### 📖 Theory:
A **Binary Tree** is a hierarchical structure where each node has at most two children (left and right).

A **Binary Search Tree (BST)** adds the ordering invariant:
- All nodes in the **left subtree** are **less** than the current node
- All nodes in the **right subtree** are **greater** than the current node
- This gives O(log n) average-case search, insert, delete (O(n) worst case if unbalanced)

**Self-balancing BSTs** (AVL Tree, Red-Black Tree) maintain O(log n) worst case. Java's `TreeMap` and `TreeSet` use Red-Black Trees internally.

**DFS Traversals (recursive, O(n) time, O(h) space where h = tree height):**
- **Inorder (LNR):** Left → Node → Right → Gives **sorted order for BST!**
- **Preorder (NLR):** Node → Left → Right → Used for **tree serialization / copying**
- **Postorder (LRN):** Left → Right → Node → Used for **deleting a tree, computing sizes**

**BFS Traversal (Level-order):** Uses a Queue. Explores level by level.

```java
// Standard TreeNode definition
public class TreeNode {
    int val;
    TreeNode left, right;
    TreeNode(int val) { this.val = val; }
}
```

---

### 🔥 Problem 12: Maximum Depth of Binary Tree (Universal classic)
```java
// DFS recursive approach — elegant and efficient
public int maxDepth(TreeNode root) {
    if (root == null) return 0; // Base: empty tree has depth 0

    int leftDepth = maxDepth(root.left);   // Depth of left subtree
    int rightDepth = maxDepth(root.right); // Depth of right subtree

    // Height = 1 (for current node) + max of subtree heights
    return 1 + Math.max(leftDepth, rightDepth);
}
// Time: O(n) — visit every node once | Space: O(h) — call stack depth = tree height
// O(n) space worst case (skewed tree), O(log n) for balanced tree

// Iterative BFS approach (counts levels)
public int maxDepthBFS(TreeNode root) {
    if (root == null) return 0;
    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);
    int depth = 0;

    while (!queue.isEmpty()) {
        int levelSize = queue.size(); // All nodes at current level
        depth++;
        for (int i = 0; i < levelSize; i++) {
            TreeNode node = queue.poll();
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
    }
    return depth;
}
```

---

### 🔥 Problem 13: Level Order Traversal / BFS (Amazon, Microsoft)
```java
// Return all nodes grouped by level: [[3], [9,20], [15,7]]
public List<List<Integer>> levelOrder(TreeNode root) {
    List<List<Integer>> result = new ArrayList<>();
    if (root == null) return result;

    Queue<TreeNode> queue = new LinkedList<>();
    queue.offer(root);

    while (!queue.isEmpty()) {
        int levelSize = queue.size(); // Snapshot of current level count
        List<Integer> currentLevel = new ArrayList<>();

        for (int i = 0; i < levelSize; i++) {
            TreeNode node = queue.poll();
            currentLevel.add(node.val);

            // Enqueue children for NEXT level processing
            if (node.left != null) queue.offer(node.left);
            if (node.right != null) queue.offer(node.right);
        }
        result.add(currentLevel);
    }
    return result;
}
// Time: O(n) | Space: O(w) where w = max width of the tree (at most n/2 for last level)
```

---

### 🔥 Problem 14: Validate Binary Search Tree (Google, Amazon)
```java
// Common mistake: only checking root.left < root and root.right > root
// WRONG: A right-subtree node could be smaller than root's ancestor!
// CORRECT: Pass min/max bounds that each node must satisfy

public boolean isValidBST(TreeNode root) {
    return validate(root, Long.MIN_VALUE, Long.MAX_VALUE);
}

private boolean validate(TreeNode node, long min, long max) {
    if (node == null) return true; // Null leaves are valid

    // Current node value MUST be strictly within (min, max)
    if (node.val <= min || node.val >= max) return false;

    // Left subtree: all values must be < node.val (node.val becomes the new max)
    // Right subtree: all values must be > node.val (node.val becomes the new min)
    return validate(node.left, min, node.val) &&
           validate(node.right, node.val, max);
}
// Time: O(n) | Space: O(h) call stack
// Example of why naive check fails:
//      5
//     / \
//    1   4
//       / \
//      3   6
// 4's right child (6) is > 4, but 4 < 5 violates BST. Naive check misses this!
```

---

### 🔥 Problem 15: Lowest Common Ancestor of BST (Facebook, Amazon)
```java
// LCA in BST: exploit BST property instead of checking all nodes
public TreeNode lowestCommonAncestor(TreeNode root, TreeNode p, TreeNode q) {
    // If both p and q are less than root → LCA is in left subtree
    if (p.val < root.val && q.val < root.val) {
        return lowestCommonAncestor(root.left, p, q);
    }
    // If both are greater → LCA is in right subtree
    if (p.val > root.val && q.val > root.val) {
        return lowestCommonAncestor(root.right, p, q);
    }
    // p and q are on opposite sides (or one IS root) → current root is LCA!
    return root;
}
// Time: O(h) — O(log n) for balanced, O(n) for skewed | Space: O(h)
```

---

### 🔥 Problem 16: Serialize & Deserialize Binary Tree (Hard — Google, Uber)
```java
// Convert tree to string and back — BFS approach
public class Codec {
    public String serialize(TreeNode root) {
        if (root == null) return "null";
        StringBuilder sb = new StringBuilder();
        Queue<TreeNode> q = new LinkedList<>();
        q.offer(root);

        while (!q.isEmpty()) {
            TreeNode node = q.poll();
            if (node == null) {
                sb.append("null,");
            } else {
                sb.append(node.val).append(",");
                q.offer(node.left);  // Queue null children too!
                q.offer(node.right);
            }
        }
        return sb.toString();
    }

    public TreeNode deserialize(String data) {
        String[] nodes = data.split(",");
        if (nodes[0].equals("null")) return null;

        TreeNode root = new TreeNode(Integer.parseInt(nodes[0]));
        Queue<TreeNode> q = new LinkedList<>();
        q.offer(root);
        int i = 1;

        while (!q.isEmpty() && i < nodes.length) {
            TreeNode node = q.poll();

            if (!nodes[i].equals("null")) {
                node.left = new TreeNode(Integer.parseInt(nodes[i]));
                q.offer(node.left);
            }
            i++;
            if (i < nodes.length && !nodes[i].equals("null")) {
                node.right = new TreeNode(Integer.parseInt(nodes[i]));
                q.offer(node.right);
            }
            i++;
        }
        return root;
    }
}
// Time: O(n) for both serialize and deserialize | Space: O(n)
```

---

## 5. 🌐 Graph

### 📖 Theory:
A **Graph** is a set of **vertices (nodes)** connected by **edges**. Unlike trees, graphs can have cycles and disconnected components.

**Representations:**
- **Adjacency List:** `Map<Integer, List<Integer>>` — memory efficient for sparse graphs O(V+E)
- **Adjacency Matrix:** `boolean[V][V]` — fast edge lookup O(1) but O(V²) memory

**Key Algorithms:**
- **BFS (Breadth-First Search):** Queue-based. Finds SHORTEST PATH in unweighted graphs. Level by level.
- **DFS (Depth-First Search):** Stack/Recursion-based. Explores as deep as possible first. Used for cycle detection, topological sort.

---

### 🔥 Problem 17: Number of Islands (DFS / BFS — Amazon, Netflix, Uber)
```java
// Grid of '1' (land) and '0' (water). Count distinct islands.
// KEY INSIGHT: DFS/BFS on each unvisited '1' marks the entire island as visited

public int numIslands(char[][] grid) {
    if (grid == null || grid.length == 0) return 0;
    int rows = grid.length, cols = grid[0].length;
    int count = 0;

    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (grid[r][c] == '1') { // Found an unvisited land cell
                count++;             // New island!
                dfsFlood(grid, r, c); // Sink the entire island (mark '0')
            }
        }
    }
    return count;
}

private void dfsFlood(char[][] grid, int r, int c) {
    // Boundary check and water check
    if (r < 0 || r >= grid.length || c < 0 || c >= grid[0].length || grid[r][c] != '1') {
        return;
    }
    grid[r][c] = '0'; // Mark as visited (sink the cell — in-place modification!)

    // Explore all 4 directions
    dfsFlood(grid, r + 1, c); // Down
    dfsFlood(grid, r - 1, c); // Up
    dfsFlood(grid, r, c + 1); // Right
    dfsFlood(grid, r, c - 1); // Left
}
// Time: O(R × C) — visit each cell at most once | Space: O(R × C) — recursion stack
```

---

### 🔥 Problem 18: Course Schedule — Cycle Detection (Topological Sort)
```java
// Can you finish all courses given prerequisites? (directed graph cycle detection)
// If cycle exists in prerequisite graph → impossible to complete!

public boolean canFinish(int numCourses, int[][] prerequisites) {
    // Build adjacency list
    List<List<Integer>> adj = new ArrayList<>();
    for (int i = 0; i < numCourses; i++) adj.add(new ArrayList<>());

    for (int[] pre : prerequisites) {
        adj.get(pre[1]).add(pre[0]); // pre[1] must be taken before pre[0]
    }

    // 0: unvisited, 1: in current DFS path (cycle detection!), 2: fully processed
    int[] state = new int[numCourses];

    for (int i = 0; i < numCourses; i++) {
        if (state[i] == 0 && hasCycle(i, adj, state)) return false;
    }
    return true;
}

private boolean hasCycle(int node, List<List<Integer>> adj, int[] state) {
    state[node] = 1; // Mark as currently being explored

    for (int neighbor : adj.get(node)) {
        if (state[neighbor] == 1) return true;  // Found back edge → CYCLE!
        if (state[neighbor] == 0 && hasCycle(neighbor, adj, state)) return true;
    }

    state[node] = 2; // Fully explored — no cycle through this node
    return false;
}
// Time: O(V + E) | Space: O(V + E) — adjacency list + state array
```

---

## 6. 📊 Heap / Priority Queue

### 📖 Theory:
A **Heap** is a complete binary tree satisfying the heap property:
- **Min-Heap:** Parent ≤ children → `peek()` returns **minimum** — Java's `PriorityQueue` default
- **Max-Heap:** Parent ≥ children → `peek()` returns **maximum** — use `PriorityQueue(Collections.reverseOrder())`

**Operations:** `add()` O(log n), `poll()` O(log n), `peek()` O(1)

**When to use heap:** "K most...", "Kth largest...", "Find median", "Merge K sorted..."

---

### 🔥 Problem 19: Kth Largest Element (Amazon, Apple, Google)
```java
// Find Kth largest element in an array
// APPROACH 1: Sort descending → O(n log n) — too slow for follow-up
// APPROACH 2: Min-Heap of size K → O(n log k) — optimal!

public int findKthLargest(int[] nums, int k) {
    // Min-heap of size k — holds the K largest elements seen so far
    PriorityQueue<Integer> minHeap = new PriorityQueue<>();

    for (int num : nums) {
        minHeap.offer(num); // Add element

        if (minHeap.size() > k) {
            minHeap.poll(); // Remove smallest — not in top-K anymore
        }
    }
    // Heap now contains exactly K largest elements
    // The SMALLEST among them (at top of min-heap) is the Kth largest!
    return minHeap.peek();
}
// Time: O(n log k) | Space: O(k) — heap size limited to k
// Example: [3,2,1,5,6,4], k=2 → 5
```

---

### 🔥 Problem 20: Find Median from Data Stream (Hard — Google, Microsoft)
**Pattern:** Two Heaps (Max-Heap + Min-Heap)
```java
// KEY INSIGHT: Split numbers into two halves
// - Left half in MAX-Heap (so we can get the max of smaller half instantly)
// - Right half in MIN-Heap (so we can get the min of larger half instantly)
// - Median = top of one heap (odd count) or average of both tops (even count)

class MedianFinder {
    private final PriorityQueue<Integer> lowerHalf = new PriorityQueue<>(Collections.reverseOrder()); // Max-heap
    private final PriorityQueue<Integer> upperHalf = new PriorityQueue<>(); // Min-heap

    public void addNum(int num) {
        // Always add to lower half FIRST
        lowerHalf.offer(num);

        // Balance: ensure lowerHalf.top() <= upperHalf.top()
        if (!upperHalf.isEmpty() && lowerHalf.peek() > upperHalf.peek()) {
            upperHalf.offer(lowerHalf.poll()); // Move max of lower to upper
        }

        // Balance sizes: lower can have at most 1 more element than upper
        if (lowerHalf.size() > upperHalf.size() + 1) {
            upperHalf.offer(lowerHalf.poll());
        } else if (upperHalf.size() > lowerHalf.size()) {
            lowerHalf.offer(upperHalf.poll());
        }
    }

    public double findMedian() {
        if (lowerHalf.size() > upperHalf.size()) {
            return lowerHalf.peek(); // Odd count — lower has extra element
        }
        return (lowerHalf.peek() + upperHalf.peek()) / 2.0; // Even — average of two middles
    }
}
// addNum: O(log n) | findMedian: O(1) | Space: O(n)
```

---

## 7. 💡 Dynamic Programming (DP)

### 📖 Theory:
**Dynamic Programming** breaks a complex problem into overlapping subproblems, solves each once, and stores results (memoization/tabulation) to avoid recomputation.

**Two approaches:**
- **Top-Down (Memoization):** Recursion + cache (HashMap or array). Start from the original problem and recurse.
- **Bottom-Up (Tabulation):** Iterative. Build up solutions from smaller subproblems.

**How to identify DP:**
- "Count the number of ways..."
- "Find the minimum/maximum..."
- "Is it possible to..."
- Problem has **optimal substructure** (optimal solution built from optimal solutions of subproblems) and **overlapping subproblems**.

---

### 🔥 Problem 21: Fibonacci (Foundation — all companies)
```java
// Top-Down (Memoization)
public int fib(int n) {
    if (n <= 1) return n;
    int[] memo = new int[n + 1];
    Arrays.fill(memo, -1);
    return fibMemo(n, memo);
}
private int fibMemo(int n, int[] memo) {
    if (n <= 1) return n;
    if (memo[n] != -1) return memo[n]; // Already computed!
    memo[n] = fibMemo(n-1, memo) + fibMemo(n-2, memo);
    return memo[n];
}
// Time: O(n) | Space: O(n)

// Bottom-Up (Tabulation) — most space-efficient
public int fibOptimal(int n) {
    if (n <= 1) return n;
    int prev2 = 0, prev1 = 1;
    for (int i = 2; i <= n; i++) {
        int curr = prev1 + prev2;
        prev2 = prev1;
        prev1 = curr;
    }
    return prev1;
}
// Time: O(n) | Space: O(1) — only two variables!
```

---

### 🔥 Problem 22: Longest Common Subsequence (Google, Amazon)
```java
// LCS: Longest sequence of characters common to both strings (not necessarily contiguous)
// e.g. "ABCBDAB" and "BDCAB" → "BCAB" (length 4)

public int longestCommonSubsequence(String text1, String text2) {
    int m = text1.length(), n = text2.length();
    // dp[i][j] = LCS length for text1[0..i-1] and text2[0..j-1]
    int[][] dp = new int[m + 1][n + 1];

    for (int i = 1; i <= m; i++) {
        for (int j = 1; j <= n; j++) {
            if (text1.charAt(i-1) == text2.charAt(j-1)) {
                // Characters match — extend the LCS found without these chars
                dp[i][j] = dp[i-1][j-1] + 1;
            } else {
                // No match — take the best of skipping from either string
                dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
            }
        }
    }
    return dp[m][n];
}
// Time: O(m × n) | Space: O(m × n) — can be optimized to O(n) with rolling array
```

---

### 🔥 Problem 23: 0/1 Knapsack (Classic DP — all companies)
```java
// Given items with weights and values, maximize value within weight limit W
// Each item can only be used ONCE (0/1 = use it or don't)

public int knapsack(int W, int[] weights, int[] values, int n) {
    // dp[i][w] = max value using first i items with capacity w
    int[][] dp = new int[n + 1][W + 1];

    for (int i = 1; i <= n; i++) {
        for (int w = 1; w <= W; w++) {
            // Option 1: Don't include item i
            dp[i][w] = dp[i-1][w];

            // Option 2: Include item i (only if it fits)
            if (weights[i-1] <= w) {
                int withItem = values[i-1] + dp[i-1][w - weights[i-1]];
                dp[i][w] = Math.max(dp[i][w], withItem);
            }
        }
    }
    return dp[n][W];
}
// Time: O(n × W) | Space: O(n × W) — can be reduced to O(W) with 1D array
```

---

### 🔥 Problem 24: Word Break (Google, Amazon, Facebook)
```java
// Can string s be segmented into words from wordDict?
// e.g. "leetcode", ["leet","code"] → true

public boolean wordBreak(String s, List<String> wordDict) {
    Set<String> wordSet = new HashSet<>(wordDict); // O(1) lookup
    int n = s.length();

    // dp[i] = true if s[0..i-1] can be segmented using wordDict
    boolean[] dp = new boolean[n + 1];
    dp[0] = true; // Empty string is always valid (base case)

    for (int i = 1; i <= n; i++) {
        for (int j = 0; j < i; j++) {
            // If s[0..j-1] is valid AND s[j..i-1] is in dictionary
            if (dp[j] && wordSet.contains(s.substring(j, i))) {
                dp[i] = true;
                break; // Found a valid split — no need to check further j's
            }
        }
    }
    return dp[n];
}
// Time: O(n² × m) where m = max word length (substring check) | Space: O(n)
```

---

## 8. 🔍 Binary Search (Advanced Patterns)

### 📖 Theory:
Binary Search is O(log n) search on **sorted** data. The key insight most developers miss: **Binary Search can be applied to ANY monotonically increasing/decreasing function**, not just sorted arrays. If you can model the problem as "find the boundary where condition changes from false to true", binary search applies.

---

### 🔥 Problem 25: Search in Rotated Sorted Array (Amazon, Facebook)
```java
// Array [4,5,6,7,0,1,2] — sorted but rotated at some pivot
// Find target without knowing where rotation happened

public int search(int[] nums, int target) {
    int left = 0, right = nums.length - 1;

    while (left <= right) {
        int mid = left + (right - left) / 2; // Avoids int overflow vs (left+right)/2

        if (nums[mid] == target) return mid;

        // Determine which HALF is sorted
        if (nums[left] <= nums[mid]) { // Left half is sorted
            if (target >= nums[left] && target < nums[mid]) {
                right = mid - 1; // Target in sorted left half
            } else {
                left = mid + 1;  // Target in right half
            }
        } else { // Right half is sorted
            if (target > nums[mid] && target <= nums[right]) {
                left = mid + 1; // Target in sorted right half
            } else {
                right = mid - 1; // Target in left half
            }
        }
    }
    return -1;
}
// Time: O(log n) | Space: O(1)
```

---

## 9. 📋 Big-O Complexity Quick Reference

### Data Structure Operations Complexity:

| Data Structure | Access | Search | Insert | Delete |
|---------------|--------|--------|--------|--------|
| Array | O(1) | O(n) | O(n) | O(n) |
| ArrayList | O(1) | O(n) | O(1)* | O(n) |
| LinkedList | O(n) | O(n) | O(1) at head | O(1) at known node |
| Stack / Queue | O(n) | O(n) | O(1) | O(1) |
| HashMap | O(1)* | O(1)* | O(1)* | O(1)* |
| TreeMap / BST | O(log n) | O(log n) | O(log n) | O(log n) |
| Min/Max Heap | O(1) peek | O(n) | O(log n) | O(log n) |

*Amortized / Average case

### Common Algorithm Complexities:

| Algorithm | Time | Space |
|-----------|------|-------|
| Binary Search | O(log n) | O(1) |
| DFS / BFS | O(V + E) | O(V) |
| Merge Sort | O(n log n) | O(n) |
| Quick Sort | O(n log n) avg, O(n²) worst | O(log n) |
| Dijkstra's | O((V+E) log V) | O(V) |
| DP (2D) | O(m × n) | O(m × n) |

---

## 🎯 DSA Cross-Questioning Scenarios

### Q: "You used a HashMap for Two Sum. What if the interviewer says 'no extra space'?"
> **Answer:** "With O(1) space, sort the array first (O(n log n)), then use the two-pointer technique: start with `left=0, right=n-1`. If `nums[left] + nums[right] == target` → return indices. If the sum is too small → move `left` right. If too large → move `right` left. But this only works for the VALUES problem — returning original indices requires the unsorted index mapping, reintroducing O(n) space. I'd clarify the requirement: can we return the values or do we strictly need original indices?"

### Q: "Your LRU Cache uses O(n) space for n entries. If memory is critical, how would you handle it in production?"
> **Answer:** "In production, we wouldn't implement LRU ourselves. We'd use Redis with `maxmemory-policy allkeys-lru`. Redis implements LRU efficiently using a random sampling approximation (samples 5 random keys, evicts the least recently used among those). For an L1 in-memory cache in a Java service, Caffeine's `CaffeineCache` implements W-TinyLFU, which outperforms LRU for real workload patterns. The hand-rolled `LinkedHashMap` LRU is for demonstrating pointer manipulation skill — not production use."

### Q: "You solved Number of Islands with DFS. The recursion depth could hit StackOverflowError for a 10,000×10,000 grid of all land. How do you handle this?"
> **Answer:** "You're absolutely right — recursive DFS has a call stack depth equal to the number of connected cells, which could be 100M for a giant all-land grid. The fix is to use an iterative DFS with an explicit `Deque<int[]>` stack (replacing the JVM call stack), or switch to BFS with a `Queue`. In production, I'd use BFS by default for grid problems since the queue size is bounded by the perimeter of the island, not its area, reducing memory pressure for large solid land masses."
