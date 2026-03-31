# Two Pointers: Triplet Sum

## Problem Statement
Given an array of integers, return all triplets `[a, b, c]` such that `a + b + c = 0`. The solution must not contain duplicate triplets.

## Examples
### Example 1
**Input:** `nums = [0, -1, 2, -3, 1]`
**Output:** `[[-3, 1, 2], [-1, 0, 1]]`
**Explanation:** `(-3) + 1 + 2 = 0` and `(-1) + 0 + 1 = 0`.

## Intuition
### Brute Force
The brute force solution involves using three nested loops to check all possible triplets. To avoid duplicate triplets, we can sort each triplet and store it in a hash set.

#### Brute Force Java Code
```java
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Collections;

public class Main {
    public ArrayList<ArrayList<Integer>> triplet_sum_brute_force(ArrayList<Integer> nums) {
        int n = nums.size();
        HashSet<ArrayList<Integer>> triplets = new HashSet<>();
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                for (int k = j + 1; k < n; k++) {
                    if (nums.get(i) + nums.get(j) + nums.get(k) == 0) {
                        ArrayList<Integer> triplet = new ArrayList<>();
                        triplet.add(nums.get(i));
                        triplet.add(nums.get(j));
                        triplet.add(nums.get(k));
                        Collections.sort(triplet);
                        triplets.add(triplet);
                    }
                }
            }
        }
        return new ArrayList<>(triplets);
    }
}
```

### Optimized Intuition: Two Pointers
1. **Sort the array:** Sorting helps in easily identifying duplicates and using the two-pointer approach for the subproblem.
2. **Iterate through the array:** Let the current element be `a` at index `i`.
3. **Find pairs:** For each `a`, find all pairs `[b, c]` in the remaining part of the array (from `i + 1` to `n - 1`) such that `b + c = -a`.
4. **Avoid duplicates:**
   - Skip the same `a` if `nums[i] == nums[i-1]`.
   - Skip the same `b` if `nums[left] == nums[left-1]` while looking for pairs.
5. **Optimization:** Since the array is sorted, if `nums[i] > 0`, then `a`, `b`, and `c` will all be positive, and their sum can never be 0. We can stop early.

## Walkthrough & Diagrams
1. **Initial State:** `nums = [0, -1, 2, -3, 1]`. Sorted: `[-3, -1, 0, 1, 2]`.
2. **Step 1:** `i = 0`, `a = -3`. Target sum for `b + c` is `3`.
   - `left = 1` (`-1`), `right = 4` (`2`). Sum = 1. `1 < 3`, move `left`.
   - `left = 2` (`0`), `right = 4` (`2`). Sum = 2. `2 < 3`, move `left`.
   - `left = 3` (`1`), `right = 4` (`2`). Sum = 3. **Match!** Triplet: `[-3, 1, 2]`.
3. **Step 2:** `i = 1`, `a = -1`. Target sum for `b + c` is `1`.
   - `left = 2` (`0`), `right = 4` (`2`). Sum = 2. `2 > 1`, move `right`.
   - `left = 2` (`0`), `right = 3` (`1`). Sum = 1. **Match!** Triplet: `[-1, 0, 1]`.
4. **Step 3:** `i = 2`, `a = 0`. Target sum for `b + c` is `0`.
   - `left = 3` (`1`), `right = 4` (`2`). Sum = 3. `3 > 0`, move `right`.
   - `left == right`, stop.

## Implementation (Java)
```java
import java.util.ArrayList;
import java.util.Collections;

public class Main {
    public ArrayList<ArrayList<Integer>> triplet_sum(ArrayList<Integer> nums) {
        ArrayList<ArrayList<Integer>> triplets = new ArrayList<>();
        Collections.sort(nums);
        for (int i = 0; i < nums.size(); i++) {
            if (nums.get(i) > 0) {
                break;
            }
            if (i > 0 && nums.get(i).equals(nums.get(i - 1))) {
                continue;
            }
            ArrayList<ArrayList<Integer>> pairs = pair_sum_sorted_all_pairs(nums, i + 1, -nums.get(i));
            for (ArrayList<Integer> pair : pairs) {
                ArrayList<Integer> triplet = new ArrayList<>();
                triplet.add(nums.get(i));
                triplet.addAll(pair);
                triplets.add(triplet);
            }
        }
        return triplets;
    }

    public ArrayList<ArrayList<Integer>> pair_sum_sorted_all_pairs(ArrayList<Integer> nums, int start, int target) {
        ArrayList<ArrayList<Integer>> pairs = new ArrayList<>();
        int left = start;
        int right = nums.size() - 1;
        while (left < right) {
            int sum = nums.get(left) + nums.get(right);
            if (sum == target) {
                ArrayList<Integer> pair = new ArrayList<>();
                pair.add(nums.get(left));
                pair.add(nums.get(right));
                pairs.add(pair);
                left += 1;
                while (left < right && nums.get(left).equals(nums.get(left - 1))) {
                    left += 1;
                }
            } else if (sum < target) {
                left += 1;
            } else {
                right -= 1;
            }
        }
        return pairs;
    }
}
```

## Complexity Analysis
- **Time Complexity:** O(n²). Sorting takes O(n log n). The loop runs n times, and each `pair_sum_sorted_all_pairs` takes O(n). Overall: O(n log n + n²) = O(n²).
- **Space Complexity:** O(n) or O(log n) depending on the sorting algorithm's implementation (O(n) for Timsort used in Java/Python). This excludes the space for the output list.

## Test Cases
- `nums = []` -> `[]` (Empty array)
- `nums = [0]` -> `[]` (Single element)
- `nums = [1, -1]` -> `[]` (Two elements)
- `nums = [0, 0, 0]` -> `[[0, 0, 0]]` (All zeros)
