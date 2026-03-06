# 🔁 Recursion & Backtracking — Deep Dive Interview Guide
## Target: 12+ Years Experience | FAANG / Product-Based Companies

---

## 📖 Recursion Theory

**Recursion** is when a function calls itself to solve smaller instances of the same problem. Every recursive solution has:
1. **Base Case** — stopping condition (prevents infinite recursion)
2. **Recursive Case** — breaks problem into smaller subproblems
3. **Return Value** — combines results from subproblems

**Call Stack:** Each recursive call creates a new stack frame. Too many = `StackOverflowError`.

### Time Complexity of Recursion:
Use the **Master Theorem** or **Recurrence Relations**:
- `T(n) = T(n-1) + O(1)` → O(n) — linear recursion (factorial)
- `T(n) = T(n-1) + O(n)` → O(n²) — with linear work each call
- `T(n) = 2T(n/2) + O(n)` → O(n log n) — merge sort
- `T(n) = 2T(n-1)` → O(2ⁿ) — exponential (Fibonacci without memo)

---

## 1. 📌 Classic Recursion Problems

### 🔥 Factorial
```java
public long factorial(int n) {
    if (n <= 1) return 1;    // Base case
    return n * factorial(n - 1); // n! = n × (n-1)!
}
// Time: O(n) | Space: O(n) — call stack depth

// TAIL RECURSIVE version (JVM doesn't optimize, but shows understanding)
public long factorialTail(int n, long accumulator) {
    if (n <= 1) return accumulator;
    return factorialTail(n - 1, n * accumulator);
}
// Called as: factorialTail(5, 1) → 120
```

---

### 🔥 Power Function (Fast Exponentiation)
```java
// Calculate x^n in O(log n) — used in cryptography (RSA)
public double myPow(double x, int n) {
    long N = n; // Handle Integer.MIN_VALUE overflow
    if (N < 0) { x = 1 / x; N = -N; }
    return fastPow(x, N);
}

private double fastPow(double x, long n) {
    if (n == 0) return 1.0;
    double half = fastPow(x, n / 2);
    if (n % 2 == 0) return half * half;       // x^n = (x^(n/2))²
    else return half * half * x;               // x^n = (x^(n/2))² × x
}
// Time: O(log n) — halve n each step | Space: O(log n) — recursion depth
```

---

### 🔥 Tower of Hanoi
```java
// Move n disks from source to destination using auxiliary peg
// Rules: Only top disk can move, larger disk can't go on smaller
public void towerOfHanoi(int n, char source, char dest, char aux) {
    if (n == 1) {
        System.out.println("Move disk 1 from " + source + " to " + dest);
        return;
    }
    towerOfHanoi(n - 1, source, aux, dest);  // Move n-1 disks to auxiliary
    System.out.println("Move disk " + n + " from " + source + " to " + dest);
    towerOfHanoi(n - 1, aux, dest, source);  // Move n-1 from auxiliary to dest
}
// Time: O(2ⁿ - 1) ≈ O(2ⁿ) | Space: O(n) — recursion depth
// Total moves = 2ⁿ - 1 (e.g., 3 disks = 7 moves)
```

---

## 📖 Backtracking Theory

**Backtracking** = DFS + constraint checking + undo. Explore all possibilities, prune invalid paths early.

**Pattern:**
```
function backtrack(state, choices):
    if isGoal(state):
        addResult(state)
        return
    for choice in choices:
        if isValid(choice):
            makeChoice(choice)         // DO
            backtrack(newState)        // EXPLORE
            undoChoice(choice)         // UNDO (backtrack)
```

**Key difference from brute force:** Backtracking **prunes** — it abandons a path as soon as it determines it can't lead to a valid solution. Brute force explores everything.

---

## 2. 📌 Backtracking Problems

### 🔥 Problem: Generate All Permutations (FAANG Classic)
```java
// Given [1,2,3], output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]
public List<List<Integer>> permute(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    backtrackPermute(nums, new ArrayList<>(), new boolean[nums.length], result);
    return result;
}

private void backtrackPermute(int[] nums, List<Integer> current,
                               boolean[] used, List<List<Integer>> result) {
    if (current.size() == nums.length) {
        result.add(new ArrayList<>(current)); // Deep copy — current will be modified!
        return;
    }

    for (int i = 0; i < nums.length; i++) {
        if (used[i]) continue; // Skip already-used elements

        used[i] = true;               // CHOOSE
        current.add(nums[i]);
        backtrackPermute(nums, current, used, result); // EXPLORE
        current.remove(current.size() - 1); // UNDO
        used[i] = false;
    }
}
// Time: O(n! × n) — n! permutations, each takes O(n) to copy
// Space: O(n) — recursion depth + current list
```

---

### 🔥 Problem: Subsets / Power Set (Amazon, Google)
```java
// Given [1,2,3], output: [[], [1], [2], [3], [1,2], [1,3], [2,3], [1,2,3]]
public List<List<Integer>> subsets(int[] nums) {
    List<List<Integer>> result = new ArrayList<>();
    backtrackSubsets(nums, 0, new ArrayList<>(), result);
    return result;
}

private void backtrackSubsets(int[] nums, int start, List<Integer> current,
                               List<List<Integer>> result) {
    result.add(new ArrayList<>(current)); // Every state is a valid subset!

    for (int i = start; i < nums.length; i++) {
        current.add(nums[i]);            // CHOOSE
        backtrackSubsets(nums, i + 1, current, result); // EXPLORE (i+1, not i!)
        current.remove(current.size() - 1); // UNDO
    }
}
// Time: O(2ⁿ × n) — 2ⁿ subsets, each up to O(n) to copy
// Space: O(n) — recursion depth
```

---

### 🔥 Problem: Combination Sum (Amazon, Facebook)
```java
// Find all unique combinations summing to target. Elements can be reused.
// [2,3,6,7], target=7 → [[2,2,3], [7]]
public List<List<Integer>> combinationSum(int[] candidates, int target) {
    List<List<Integer>> result = new ArrayList<>();
    Arrays.sort(candidates); // Sort for pruning
    backtrackCombo(candidates, target, 0, new ArrayList<>(), result);
    return result;
}

private void backtrackCombo(int[] candidates, int remaining, int start,
                             List<Integer> current, List<List<Integer>> result) {
    if (remaining == 0) {
        result.add(new ArrayList<>(current));
        return;
    }

    for (int i = start; i < candidates.length; i++) {
        if (candidates[i] > remaining) break; // PRUNE — sorted, so all after are too big

        current.add(candidates[i]);
        backtrackCombo(candidates, remaining - candidates[i], i, current, result); // i, not i+1 (reuse!)
        current.remove(current.size() - 1);
    }
}
// Time: O(2^(target/min)) worst case | Space: O(target/min) — recursion depth
```

---

### 🔥 Problem: N-Queens (Google, Microsoft — Hard)
```java
// Place N queens on N×N board so no two attack each other
public List<List<String>> solveNQueens(int n) {
    List<List<String>> solutions = new ArrayList<>();
    char[][] board = new char[n][n];
    for (char[] row : board) Arrays.fill(row, '.');
    backtrackQueens(board, 0, n, solutions);
    return solutions;
}

private void backtrackQueens(char[][] board, int row, int n,
                              List<List<String>> solutions) {
    if (row == n) { // All queens placed successfully
        List<String> solution = new ArrayList<>();
        for (char[] r : board) solution.add(new String(r));
        solutions.add(solution);
        return;
    }

    for (int col = 0; col < n; col++) {
        if (isSafe(board, row, col, n)) {
            board[row][col] = 'Q';     // PLACE queen
            backtrackQueens(board, row + 1, n, solutions); // EXPLORE next row
            board[row][col] = '.';     // REMOVE queen (backtrack)
        }
    }
}

private boolean isSafe(char[][] board, int row, int col, int n) {
    // Check column above
    for (int i = 0; i < row; i++)
        if (board[i][col] == 'Q') return false;

    // Check upper-left diagonal
    for (int i = row - 1, j = col - 1; i >= 0 && j >= 0; i--, j--)
        if (board[i][j] == 'Q') return false;

    // Check upper-right diagonal
    for (int i = row - 1, j = col + 1; i >= 0 && j < n; i--, j++)
        if (board[i][j] == 'Q') return false;

    return true;
}
// Time: O(n!) — at most n choices for row 1, n-1 for row 2, etc.
// Space: O(n²) — board + O(n) recursion depth
```

---

### 🔥 Problem: Sudoku Solver (Hard — Google)
```java
public void solveSudoku(char[][] board) {
    solve(board);
}

private boolean solve(char[][] board) {
    for (int row = 0; row < 9; row++) {
        for (int col = 0; col < 9; col++) {
            if (board[row][col] != '.') continue; // Skip filled cells

            for (char num = '1'; num <= '9'; num++) {
                if (isValidPlacement(board, row, col, num)) {
                    board[row][col] = num;   // TRY this number

                    if (solve(board)) return true; // EXPLORE — if solved, done!

                    board[row][col] = '.';   // UNDO — this number didn't work
                }
            }
            return false; // No valid number for this cell — backtrack!
        }
    }
    return true; // All cells filled — solved!
}

private boolean isValidPlacement(char[][] board, int row, int col, char num) {
    for (int i = 0; i < 9; i++) {
        if (board[row][i] == num) return false; // Check row
        if (board[i][col] == num) return false; // Check column
        // Check 3×3 box
        int boxRow = 3 * (row / 3) + i / 3;
        int boxCol = 3 * (col / 3) + i % 3;
        if (board[boxRow][boxCol] == num) return false;
    }
    return true;
}
// Time: O(9^(empty_cells)) worst case, but pruning makes it much faster
// Space: O(81) — board is modified in place, O(81) max recursion depth
```

---

### 🔥 Problem: Word Search in Grid (Amazon, Microsoft)
```java
// Given a 2D grid and a word, check if word exists by moving adjacent cells
public boolean exist(char[][] board, String word) {
    int rows = board.length, cols = board[0].length;
    for (int r = 0; r < rows; r++) {
        for (int c = 0; c < cols; c++) {
            if (board[r][c] == word.charAt(0) && dfs(board, word, r, c, 0)) {
                return true;
            }
        }
    }
    return false;
}

private boolean dfs(char[][] board, String word, int r, int c, int idx) {
    if (idx == word.length()) return true; // All characters matched!

    if (r < 0 || r >= board.length || c < 0 || c >= board[0].length
        || board[r][c] != word.charAt(idx)) {
        return false; // Boundary check or character mismatch
    }

    char temp = board[r][c];
    board[r][c] = '#'; // Mark as visited (in-place, no extra Set needed!)

    boolean found = dfs(board, word, r + 1, c, idx + 1) // Down
                 || dfs(board, word, r - 1, c, idx + 1) // Up
                 || dfs(board, word, r, c + 1, idx + 1) // Right
                 || dfs(board, word, r, c - 1, idx + 1); // Left

    board[r][c] = temp; // BACKTRACK — restore original character
    return found;
}
// Time: O(R × C × 4^L) where L = word length | Space: O(L) — recursion depth
```

---

## 🎯 Recursion & Backtracking Cross-Questioning

### Q: "How do you avoid StackOverflowError in deep recursion?"
> **Answer:** "Three approaches: (1) Convert to iterative using an explicit stack (`Deque<>`). (2) Increase JVM stack size with `-Xss` flag (e.g., `-Xss4m`). (3) Use tail call optimization — Java doesn't support TCO, but Kotlin and Scala do. In practice, I convert to iterative for production-critical deep recursion."

### Q: "Recursion vs Iteration — when to use which?"
> **Answer:** "Use recursion when the problem is naturally hierarchical (trees, graphs, divide & conquer). Use iteration when: (1) depth could be very large (tree with 100K nodes), (2) performance is critical (iteration avoids function call overhead), (3) the problem maps naturally to loops (array scanning). Most tree traversals I write recursively for clarity but know the iterative versions for production."

### Q: "What is the difference between backtracking and dynamic programming?"
> **Answer:** "Both explore solution spaces, but: Backtracking explores ALL paths and prunes invalid ones (DFS + undo). DP stores overlapping subproblem results to avoid recomputation. Key test: if subproblems overlap (same inputs) → use DP. If all decisions are independent and you need ALL solutions → use backtracking. Example: 'count ways to reach target sum' → DP. 'List all combinations that sum to target' → backtracking."
