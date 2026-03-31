# 📌 Introduction to Two Pointers

## 📖 Source
**ByteByteGo** — Coding Interview Patterns → Two Pointers Module

---

## 🧠 Intuition

A **two-pointer pattern** uses two variables (pointers) that represent indices or positions within a data structure like an array or linked list. Introducing a second pointer enables **comparisons** between elements at two different positions.

A naive approach often uses nested loops — **O(n²)**:

```java
for (int i = 0; i < n; i++) {
    for (int j = i + 1; j < n; j++) {
        compare(nums[i], nums[j]);
    }
}
```

Two-pointer techniques exploit **predictable structure** (e.g., sorted arrays) to reduce this to **O(n)**.

---

## 🔑 Two-Pointer Strategies

### 1️⃣ Inward Traversal
- Pointers start at **opposite ends** and move toward each other
- Ideal when comparing elements from both ends (e.g., palindrome check, container problems)

### 2️⃣ Unidirectional Traversal
- Both pointers start at the **same end** and move in the same direction
- One pointer **finds** information, the other **tracks** information
- Common in partitioning and sliding window variants

---

## ✅ When to Use Two Pointers?

| Indicator | Example |
|-----------|---------|
| **Sorted input** | Pair sum in sorted array |
| **Symmetrical structure** | Palindrome validation |
| **Pair/triplet** of values needed | Two Sum, Three Sum |
| **Linear data structure** | Arrays, linked lists |

---

## 🌍 Real-World Example

**Garbage Collection (Memory Compaction):**
- A **scan pointer** traverses the heap to find live objects
- A **free pointer** tracks the next available relocation slot
- Live objects are shifted to the free pointer position → contiguous memory is freed up
