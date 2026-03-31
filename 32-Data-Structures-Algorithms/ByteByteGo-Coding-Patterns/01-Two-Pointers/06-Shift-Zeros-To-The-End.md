# 📌 Shift Zeros to the End — Two Pointers

## 📖 Source
**ByteByteGo** — Coding Interview Patterns → Two Pointers

---

## 📝 Problem Statement

Given an integer array `nums`, move all `0`s to the **end** while maintaining the relative order of non-zero elements. Do this **in-place**.

### Example

| Input | Output |
|-------|--------|
| `[0, 1, 0, 3, 12]` | `[1, 3, 12, 0, 0]` |

---

## 💡 Approach — Unidirectional Two Pointers

- `left` pointer: position for next non-zero element
- `right` pointer: scans through the array
- When `nums[right] ≠ 0` → swap with `nums[left]`, advance `left`

> **Pattern:** This is the classic **partition** technique — separate zeros from non-zeros while preserving order.

---

## ✅ Java Solution

```java
public class ShiftZeros {

    public static void shiftZerosToEnd(int[] nums) {
        int left = 0;  // Position for next non-zero element

        for (int right = 0; right < nums.length; right++) {
            if (nums[right] != 0) {
                if (right != left) {
                    // Swap
                    int temp = nums[left];
                    nums[left] = nums[right];
                    nums[right] = temp;
                }
                left++;
            }
        }
    }

    // --- Test ---
    public static void main(String[] args) {
        int[] nums = {0, 1, 0, 3, 12};
        shiftZerosToEnd(nums);
        System.out.println(java.util.Arrays.toString(nums));  // [1, 3, 12, 0, 0]
    }
}
```

---

## ⏱️ Complexity

| Metric | Value |
|--------|-------|
| **Time** | `O(n)` — each element visited once |
| **Space** | `O(1)` — in-place |
