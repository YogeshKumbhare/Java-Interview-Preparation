# Geometric Sequence Triplets

> Source: [ByteByteGo - Coding Patterns](https://bytebytego.com/courses/coding-patterns/hash-maps-and-sets/geometric-sequence-triplets)

## Problem Statement

Given an array of integers `arr` and a common ratio `r`, count the number of triplets `(i, j, k)` such that:
1. `i < j < k`
2. `arr[i]`, `arr[j]`, and `arr[k]` form a geometric progression with the common ratio `r`.

This means:
- `arr[j] = arr[i] * r`
- `arr[k] = arr[j] * r`

### Example

**Input:**
```java
arr = [1, 2, 2, 4];
r = 2;
```

**Output:** `2`

**Explanation:**
The valid triplets (represented by their indices) are:
- `(0, 1, 3)` which gives values `[1, 2, 4]`
- `(0, 2, 3)` which gives values `[1, 2, 4]`

---

## High-Level Design & Approach

To find the triplets efficiently, we can use the middle element (`arr[j]`) as our pivot point while iterating through the array. 

If we are currently at element `m` (where `m = arr[j]`), we need to find how many valid left elements (`m / r`) have already appeared, and how many valid right elements (`m * r`) are still available ahead of us. 

### Data Structures:
We will use **two Hash Maps**:
1. **`rightMap`**: Keeps track of the frequencies of elements to the right of our current middle pointer. Initially, this contains the frequency map of the *entire* array.
2. **`leftMap`**: Keeps track of the frequencies of elements to the left of our current middle pointer. Initially, this is empty.

### Algorithm:
1. **Initialize `rightMap`:** Iterate through the array and populate the frequencies of all elements.
2. **Iterate for the middle element:** For each element `m` in the array:
   - Decrease the count of `m` in `rightMap` by 1, since `m` is now the middle element and is no longer to our right.
   - **Check for Triplets**: If `m` is cleanly divisible by `r` (i.e., `m % r == 0`), calculate exactly how many valid triplets can be formed. The number of triplets with `m` in the middle is `leftMap.get(m / r) * rightMap.get(m * r)`. Add this to our total count.
   - **Update `leftMap`:** Enhance `leftMap` by increasing the count of `m` by 1. For the next iterations, `m` will be a "left" element.

---

## Complexity Analysis

- **Time Complexity**: $\mathcal{O}(N)$
  - We iterate through the array twice: once to populate the initial `rightMap` and once to find the triplets. Hash Map insertions and lookups operate in expected $\mathcal{O}(1)$ time. 
- **Space Complexity**: $\mathcal{O}(N)$
  - We use two Hash Maps (`leftMap` and `rightMap`). In the worst-case scenario (all distinct elements), they will store up to $N$ entries.

---

## Java Implementation

```java
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class GeometricSequenceTriplets {

    public static long countTriplets(List<Long> arr, long r) {
        // Keeps track of the frequency of elements to the left of the current element
        Map<Long, Long> leftMap = new HashMap<>();
        
        // Keeps track of the frequency of elements to the right of the current element
        Map<Long, Long> rightMap = new HashMap<>();

        // Populate the rightMap with the frequency of all elements initially
        for (long num : arr) {
            rightMap.put(num, rightMap.getOrDefault(num, 0L) + 1L);
        }

        long totalTriplets = 0;

        // Iterate through the array, treating each element as the potential middle element
        for (long mid : arr) {
            // Remove the current element from the rightMap since it is now the middle element
            rightMap.put(mid, rightMap.get(mid) - 1L);

            // Check if a valid triplet can be formed
            if (mid % r == 0) {
                long leftElement = mid / r;
                long rightElement = mid * r;

                // Multiply combinations of lefts and rights
                if (leftMap.containsKey(leftElement) && rightMap.containsKey(rightElement)) {
                    totalTriplets += leftMap.get(leftElement) * rightMap.get(rightElement);
                }
            }

            // Add the current element to the leftMap for the next iterations
            leftMap.put(mid, leftMap.getOrDefault(mid, 0L) + 1L);
        }

        return totalTriplets;
    }

    public static void main(String[] args) {
        List<Long> arr = List.of(1L, 2L, 2L, 4L);
        long r = 2;
        
        long result = countTriplets(arr, r);
        System.out.println("Total Triplets: " + result); 
        // Expected Output: 2
    }
}
```
