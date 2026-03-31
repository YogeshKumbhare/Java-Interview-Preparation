# 📌 Next Lexicographical Sequence — Two Pointers

## 📖 Source
**ByteByteGo** — Coding Interview Patterns → Two Pointers

---

## 📝 Problem Statement

Given a string `s`, find the **next lexicographical permutation** of its characters. If already the largest permutation, return the smallest (reversed).

### Examples

| Input | Output |
|-------|--------|
| `"abcedda"` | `"abcedad"` |
| `"abc"` | `"acb"` |

---

## 💡 Approach — 4-Step Algorithm

1. **Find Pivot:** Traverse right→left, find first char smaller than its right neighbor
2. **Find Successor:** Traverse right→left, find first char larger than pivot
3. **Swap** pivot and successor
4. **Reverse suffix** after pivot position (to minimize the increase)

> If no pivot exists → string is the largest permutation → reverse the whole string.

---

## ✅ Java Solution

```java
public class NextLexicographicalSequence {

    public static String nextSequence(String s) {
        char[] chars = s.toCharArray();
        int n = chars.length;

        // Step 1: Find the pivot (rightmost char smaller than its next)
        int pivot = n - 2;
        while (pivot >= 0 && chars[pivot] >= chars[pivot + 1]) {
            pivot--;
        }

        // No pivot → reverse entire string (smallest permutation)
        if (pivot == -1) {
            reverse(chars, 0, n - 1);
            return new String(chars);
        }

        // Step 2: Find rightmost successor to pivot
        int successor = n - 1;
        while (chars[successor] <= chars[pivot]) {
            successor--;
        }

        // Step 3: Swap pivot and successor
        swap(chars, pivot, successor);

        // Step 4: Reverse the suffix after pivot
        reverse(chars, pivot + 1, n - 1);

        return new String(chars);
    }

    private static void swap(char[] arr, int i, int j) {
        char temp = arr[i];
        arr[i] = arr[j];
        arr[j] = temp;
    }

    private static void reverse(char[] arr, int left, int right) {
        while (left < right) {
            swap(arr, left, right);
            left++;
            right--;
        }
    }

    // --- Test ---
    public static void main(String[] args) {
        System.out.println(nextSequence("abc"));     // "acb"
        System.out.println(nextSequence("abcedda")); // "abcedad"
        System.out.println(nextSequence("cba"));     // "abc" (wraps around)
    }
}
```

---

## ⏱️ Complexity

| Metric | Value |
|--------|-------|
| **Time** | `O(n)` — at most two linear scans |
| **Space** | `O(n)` — char array copy of string |
