# Two Pointers: Is Palindrome Valid

## Problem Statement
Given a string, determine if it's a palindrome after removing all non-alphanumeric characters and ignoring the case of the letters.

## Examples
### Example 1
**Input:** `s = "a dog! a panic in a pagoda."`
**Output:** `true`
**Explanation:** After removing non-alphanumeric characters and converting to lowercase, the string becomes `adogapanicinapagoda`, which is a palindrome.

### Example 2
**Input:** `s = "abc123"`
**Output:** `false`

## Intuition
A common approach is to create a new string by removing non-alphanumeric characters, reversing it, and checking if it's equal to the original cleaned string. However, this requires O(n) extra space.

### Optimized Intuition: Two Pointers
We can use two pointers, `left` and `right`, starting at the beginning and end of the string, respectively.
1. Move the `left` pointer to the right until it points to an alphanumeric character.
2. Move the `right` pointer to the left until it points to an alphanumeric character.
3. Compare the characters at `left` and `right` (ignoring case). If they don't match, it's not a palindrome.
4. Continue until the pointers meet.

## Walkthrough & Diagrams
1. **Initial State:** `s = "a + 2 c ! 2 a"`. `left = 0` ('a'), `right = 10` ('a').
2. **Step 1:** `s[0]` and `s[10]` match ('a'). `left = 1`, `right = 9`.
3. **Step 2:** `s[1]` is '+', not alphanumeric. Move `left` to 2 ('2').
4. **Step 3:** `s[9]` is ' ', not alphanumeric. Move `right` to 8 ('2').
5. **Step 4:** `s[2]` and `s[8]` match ('2'). `left = 3`, `right = 7`.
6. **Step 5:** `s[3]` is ' ', not alphanumeric. Move `left` to 4 ('c').
7. **Step 6:** `s[7]` is '!', not alphanumeric. Move `right` to 6 ('c').
8. **Step 7:** `s[4]` and `s[6]` match ('c'). `left = 5`, `right = 5`. Pointers meet.

## Implementation (Java)
```java
public class Main {
    public Boolean is_palindrome_valid(String s) {
        int left = 0, right = s.length() - 1;
        while (left < right) {
            // Skip non-alphanumeric characters from the left.
            while (left < right && !Character.isLetterOrDigit(s.charAt(left))) {
                left++;
            }
            // Skip non-alphanumeric characters from the right.
            while (left < right && !Character.isLetterOrDigit(s.charAt(right))) {
                right--;
            }
            // If the characters at the left and right pointers don’t match, the string is
            // not a palindrome.
            if (Character.toLowerCase(s.charAt(left)) != Character.toLowerCase(s.charAt(right))) {
                return false;
            }
            left++;
            right--;
        }
        return true;
    }
}
```

## Complexity Analysis
- **Time Complexity:** O(n), where n is the length of the string. Each character is visited at most twice (once by the `left` or `right` pointer).
- **Space Complexity:** O(1), as we only use two pointer variables and don't create any new strings.
