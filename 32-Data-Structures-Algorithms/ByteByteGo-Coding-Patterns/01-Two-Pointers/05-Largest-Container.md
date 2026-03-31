# Two Pointers: Largest Container

## Problem Statement
Given an array of non-negative integers `heights`, where each element represents the height of a vertical line, find two lines that together with the x-axis form a container, such that the container contains the most water. Return the maximum amount of water a container can store.

## Examples
### Example 1
**Input:** `heights = [2, 7, 8, 3, 7, 6]`
**Output:** `24`
**Explanation:** The maximum water is between `heights[1]` (7) and `heights[5]` (6). Width = `5 - 1 = 4`. Area = `min(7, 6) * 4 = 24`.

## Intuition
The amount of water stored is determined by the distance between the two lines (width) and the height of the shorter line.
`Amount = min(heights[i], heights[j]) * (j - i)`

### Brute Force
Check every possible pair of lines and keep track of the maximum area.

#### Brute Force Java Code
```java
import java.util.ArrayList;

public class Main {
    public int largest_container_brute_force(ArrayList<Integer> heights) {
        int n = heights.size();
        int max_water = 0;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int water = Math.min(heights.get(i), heights.get(j)) * (j - i);
                max_water = Math.max(max_water, water);
            }
        }
        return max_water;
    }
}
```

### Optimized Intuition: Two Pointers
Start with two pointers at the extreme ends of the array. The width is maximized at the start.
To find a larger area, we must find taller lines, because any inward movement decreases the width.
- If `heights[left] < heights[right]`, moving `right` inward won't help because the height is limited by `heights[left]`. So we move `left` inward.
- If `heights[right] < heights[left]`, move `right` inward.
- If they are equal, moving either (or both) could potentially find a taller line.

## Walkthrough & Diagrams
1. **Initial State:** `heights = [2, 7, 8, 3, 7, 6]`. `left = 0` (2), `right = 5` (6). `Water = min(2, 6) * 5 = 10`. `max_water = 10`.
2. **Step 1:** `heights[left] < heights[right]`, so `left++`. `left = 1` (7), `right = 5` (6). `Water = min(7, 6) * 4 = 24`. `max_water = 24`.
3. **Step 2:** `heights[right] < heights[left]`, so `right--`. `left = 1` (7), `right = 4` (7). `Water = min(7, 7) * 3 = 21`. `max_water = 24`.
4. **Step 3:** `heights[left] == heights[right]`, move both. `left = 2` (8), `right = 3` (3). `Water = min(8, 3) * 1 = 3`. `max_water = 24`.
5. **Step 4:** `left == right`, stop.

## Implementation (Java)
```java
import java.util.ArrayList;

public class Main {
    public int largest_container(ArrayList<Integer> heights) {
        int max_water = 0;
        int left = 0, right = heights.size() - 1;
        while (left < right) {
            int water = Math.min(heights.get(left), heights.get(right)) * (right - left);
            max_water = Math.max(max_water, water);
            if (heights.get(left) < heights.get(right)) {
                left++;
            } else if (heights.get(left) > heights.get(right)) {
                right--;
            } else {
                left++;
                right--;
            }
        }
        return max_water;
    }
}
```

## Complexity Analysis
- **Time Complexity:** O(n). Each element is visited at most once.
- **Space Complexity:** O(1).
