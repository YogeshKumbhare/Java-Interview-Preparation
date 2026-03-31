# Two Pointers: Pair Sum - Sorted

## Problem Statement
Given an array of integers sorted in ascending order and a target value, return the indexes of any pair of numbers in the array that sum to the target. The order of the indexes in the result doesn't matter. If no pair is found, return an empty array.

## Examples
### Example 1
**Input:** `nums = [-5, -2, 3, 4, 6]`, `target = 7`
**Output:** `[2, 3]`
**Explanation:** `nums[2] + nums[3] = 3 + 4 = 7`.

### Example 2
**Input:** `nums = [1, 1, 1]`, `target = 2`
**Output:** `[0, 1]`
**Explanation:** Other valid outputs could be `[1, 0]`, `[0, 2]`, `[2, 0]`, `[1, 2]` or `[2, 1]`.

## Intuition
The brute force solution involves checking all possible pairs using two nested loops. While this approach is simple to implement, its O(n²) time complexity makes it inefficient for large arrays.

### Brute Force Java Code
```java
import java.util.ArrayList;

public class Main {
    public ArrayList<Integer> pair_sum_sorted_brute_force(ArrayList<Integer> nums, int target) {
        int n = nums.size();
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                if (nums.get(i) + nums.get(j) == target) {
                    ArrayList<Integer> result = new ArrayList<>();
                    result.add(i);
                    result.add(j);
                    return result;
                }
            }
        }
        return new ArrayList<>();
    }
}
```

### Optimized Intuition: Two Pointers
Because the array is sorted, we can use two pointers—one starting at the beginning (`left`) and one at the end (`right`).
- If `nums[left] + nums[right] == target`, we've found the pair.
- If the sum is less than the target, we need a larger sum, so we move the `left` pointer to the right (`left += 1`).
- If the sum is greater than the target, we need a smaller sum, so we move the `right` pointer to the left (`right -= 1`).

## Walkthrough & Diagrams
1. **Initial State:** `nums = [-5, -2, 3, 4, 6]`, `target = 7`. `left = 0` (`-5`), `right = 4` (`6`). `Sum = 1`.
2. **Step 1:** `1 < 7`, so `left` moves to index 1. `left = 1` (`-2`), `right = 4` (`6`). `Sum = 4`.
3. **Step 2:** `4 < 7`, so `left` moves to index 2. `left = 2` (`3`), `right = 4` (`6`). `Sum = 9`.
4. **Step 3:** `9 > 7`, so `right` moves to index 3. `left = 2` (`3`), `right = 3` (`4`). `Sum = 7`. **Match found!**

## Implementation (Java)
```java
import java.util.ArrayList;

public class Main {
    public ArrayList<Integer> pair_sum_sorted(ArrayList<Integer> nums, int target) {
        int left = 0;
        int right = nums.size() - 1;
        while (left < right) {
            int current_sum = nums.get(left) + nums.get(right);
            if (current_sum == target) {
                ArrayList<Integer> result = new ArrayList<>();
                result.add(left);
                result.add(right);
                return result;
            } else if (current_sum < target) {
                left += 1;
            } else {
                right -= 1;
            }
        }
        return new ArrayList<>();
    }
}
```

## Complexity Analysis
- **Time Complexity:** O(n), where n is the number of elements in the array. Each element is visited at most once.
- **Space Complexity:** O(1), as we only use two pointer variables.

## Interview Tip
**Consider all information provided.**
When interviewers pose a problem, they sometimes provide only the minimum amount of information required for you to start solving it. Consequently, it’s crucial to thoroughly evaluate all that information to determine which details are essential for solving the problem efficiently. In this problem, the key to arriving at the optimal solution is recognizing that the input is sorted.
