# 🔄 Sorting Algorithms — Deep Dive Interview Guide
## Target: 12+ Years Experience | FAANG / Product-Based Companies

---

## 📖 Why Sorting matters in interviews?

Sorting is the **foundation of computer science**. Understanding sorting algorithms reveals:
1. **Algorithm design paradigms** — divide & conquer, greedy, counting
2. **Time-space tradeoffs** — when to trade memory for speed
3. **Stability** — does relative order of equal elements matter?
4. **In-place vs Extra space** — memory constraints in production
5. **Practical knowledge** — Java uses TimSort (hybrid merge+insertion sort)

---

## 📊 Sorting Algorithm Comparison Table

| Algorithm | Best | Average | Worst | Space | Stable? | In-Place? |
|-----------|------|---------|-------|-------|---------|-----------|
| Bubble Sort | O(n) | O(n²) | O(n²) | O(1) | ✅ | ✅ |
| Selection Sort | O(n²) | O(n²) | O(n²) | O(1) | ❌ | ✅ |
| Insertion Sort | O(n) | O(n²) | O(n²) | O(1) | ✅ | ✅ |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | O(n) | ✅ | ❌ |
| Quick Sort | O(n log n) | O(n log n) | O(n²) | O(log n) | ❌ | ✅ |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | O(1) | ❌ | ✅ |
| Counting Sort | O(n+k) | O(n+k) | O(n+k) | O(k) | ✅ | ❌ |
| Radix Sort | O(d·(n+k)) | O(d·(n+k)) | O(d·(n+k)) | O(n+k) | ✅ | ❌ |
| Tim Sort (Java) | O(n) | O(n log n) | O(n log n) | O(n) | ✅ | ❌ |

---

## 1. 📌 Bubble Sort — The Teaching Algorithm

### Theory:
Repeatedly swap adjacent elements if they are in the wrong order. After each pass, the largest unsorted element "bubbles up" to its correct position. **Never used in production** — purely educational.

```java
public void bubbleSort(int[] arr) {
    int n = arr.length;
    for (int i = 0; i < n - 1; i++) {
        boolean swapped = false; // Optimization: early termination
        for (int j = 0; j < n - i - 1; j++) {
            if (arr[j] > arr[j + 1]) {
                // Swap adjacent elements
                int temp = arr[j];
                arr[j] = arr[j + 1];
                arr[j + 1] = temp;
                swapped = true;
            }
        }
        if (!swapped) break; // Array is already sorted — O(n) best case!
    }
}
// Time: O(n²) average/worst, O(n) best (already sorted with optimization)
// Space: O(1) | Stable: Yes
```

---

## 2. 📌 Selection Sort — Find Minimum, Place It

### Theory:
Find the minimum element in unsorted portion, swap it with the first unsorted position. Simple but always O(n²) — no early termination possible.

```java
public void selectionSort(int[] arr) {
    int n = arr.length;
    for (int i = 0; i < n - 1; i++) {
        int minIdx = i;
        for (int j = i + 1; j < n; j++) {
            if (arr[j] < arr[minIdx]) {
                minIdx = j; // Track index of minimum
            }
        }
        // Swap minimum with first unsorted position
        int temp = arr[minIdx];
        arr[minIdx] = arr[i];
        arr[i] = temp;
    }
}
// Time: O(n²) all cases | Space: O(1) | Stable: No
// Why unstable? [5a, 3, 5b, 2] → selecting 2 and swapping with 5a changes 5a/5b order
```

---

## 3. 📌 Insertion Sort — Build Sorted Array One Element at a Time

### Theory:
Like sorting playing cards in hand. Pick each element and insert it into its correct position in the already-sorted left portion. **Best for small or nearly-sorted arrays** — Java's TimSort uses this for runs < 32 elements.

```java
public void insertionSort(int[] arr) {
    for (int i = 1; i < arr.length; i++) {
        int key = arr[i];       // Element to be inserted
        int j = i - 1;

        // Shift elements greater than key to the right
        while (j >= 0 && arr[j] > key) {
            arr[j + 1] = arr[j]; // Shift right
            j--;
        }
        arr[j + 1] = key; // Insert at correct position
    }
}
// Time: O(n) best (sorted), O(n²) avg/worst | Space: O(1) | Stable: Yes
// KEY: Adaptive — O(n) for nearly sorted data (few inversions)
```

---

## 4. 📌 Merge Sort — Divide, Sort, Merge (Guaranteed O(n log n))

### Theory:
**Divide and Conquer**: Split array in half recursively until single elements, then merge sorted halves. **Guaranteed** O(n log n) — no worst case degradation. Used for external sorting (sorting data larger than RAM).

```java
public void mergeSort(int[] arr, int left, int right) {
    if (left >= right) return; // Base case: single element is sorted

    int mid = left + (right - left) / 2;

    mergeSort(arr, left, mid);       // Sort left half
    mergeSort(arr, mid + 1, right);  // Sort right half
    merge(arr, left, mid, right);    // Merge two sorted halves
}

private void merge(int[] arr, int left, int mid, int right) {
    // Create temp arrays for left and right halves
    int[] leftArr = Arrays.copyOfRange(arr, left, mid + 1);
    int[] rightArr = Arrays.copyOfRange(arr, mid + 1, right + 1);

    int i = 0, j = 0, k = left;

    // Merge by comparing front elements of both halves
    while (i < leftArr.length && j < rightArr.length) {
        if (leftArr[i] <= rightArr[j]) { // <= makes it STABLE
            arr[k++] = leftArr[i++];
        } else {
            arr[k++] = rightArr[j++];
        }
    }

    // Copy remaining elements
    while (i < leftArr.length) arr[k++] = leftArr[i++];
    while (j < rightArr.length) arr[k++] = rightArr[j++];
}
// Time: O(n log n) ALL cases | Space: O(n) — temp arrays
// Stable: Yes | NOT in-place (requires O(n) extra space)
// WHY O(n log n)? log n levels of recursion × O(n) merge per level
```

---

## 5. 📌 Quick Sort — Partition-Based (Fastest in Practice)

### Theory:
Choose a **pivot** element, partition array into elements < pivot and > pivot, recursively sort partitions. **Fastest in practice** for in-memory sorting due to cache-friendliness (sequential memory access).

```java
public void quickSort(int[] arr, int low, int high) {
    if (low >= high) return;

    int pivotIdx = partition(arr, low, high);
    quickSort(arr, low, pivotIdx - 1);  // Sort left of pivot
    quickSort(arr, pivotIdx + 1, high); // Sort right of pivot
}

// Lomuto Partition Scheme
private int partition(int[] arr, int low, int high) {
    int pivot = arr[high]; // Choose last element as pivot
    int i = low - 1;       // Index of smaller element boundary

    for (int j = low; j < high; j++) {
        if (arr[j] < pivot) {
            i++;
            swap(arr, i, j); // Move smaller element to left partition
        }
    }
    swap(arr, i + 1, high); // Place pivot at its correct sorted position
    return i + 1;            // Return pivot's final index
}

private void swap(int[] arr, int a, int b) {
    int temp = arr[a]; arr[a] = arr[b]; arr[b] = temp;
}
// Time: O(n log n) avg, O(n²) worst (sorted array + bad pivot)
// Space: O(log n) — call stack | Stable: No | In-place: Yes

// 🔥 THREE-WAY PARTITION (Dutch National Flag — handles duplicates efficiently)
// Useful when array has many duplicate values
public void quickSort3Way(int[] arr, int lo, int hi) {
    if (lo >= hi) return;
    int lt = lo, gt = hi, i = lo + 1;
    int pivot = arr[lo];

    while (i <= gt) {
        if (arr[i] < pivot) swap(arr, lt++, i++);
        else if (arr[i] > pivot) swap(arr, i, gt--);
        else i++;
    }
    // arr[lo..lt-1] < pivot = arr[lt..gt] < arr[gt+1..hi]
    quickSort3Way(arr, lo, lt - 1);
    quickSort3Way(arr, gt + 1, hi);
}
```

### Why Quick Sort O(n²) is rare in practice:
1. **Randomized pivot** — choose random element instead of first/last
2. **Median-of-three** — pick median of first, middle, last elements
3. **Introsort** (C++ std::sort) — falls back to HeapSort if recursion too deep

---

## 6. 📌 Heap Sort — Guaranteed O(n log n), In-Place

### Theory:
Build a max-heap, then repeatedly extract the maximum element and place it at the end. Guaranteed O(n log n) with O(1) space. Not commonly used due to poor cache performance (non-sequential memory access).

```java
public void heapSort(int[] arr) {
    int n = arr.length;

    // Phase 1: Build Max-Heap (bottom-up heapify) — O(n)
    for (int i = n / 2 - 1; i >= 0; i--) {
        heapify(arr, n, i);
    }

    // Phase 2: Extract elements one by one — O(n log n)
    for (int i = n - 1; i > 0; i--) {
        swap(arr, 0, i);      // Move current max to end
        heapify(arr, i, 0);   // Restore heap property on reduced heap
    }
}

private void heapify(int[] arr, int n, int i) {
    int largest = i;
    int left = 2 * i + 1;
    int right = 2 * i + 2;

    if (left < n && arr[left] > arr[largest]) largest = left;
    if (right < n && arr[right] > arr[largest]) largest = right;

    if (largest != i) {
        swap(arr, i, largest);
        heapify(arr, n, largest); // Recursively fix the affected subtree
    }
}
// Time: O(n log n) ALL cases | Space: O(1) | Stable: No
```

---

## 7. 📌 Counting Sort — O(n+k) Linear Time! (Non-Comparison Based)

### Theory:
Count occurrences of each value, then reconstruct sorted array from counts. Works only for **non-negative integers** within a known range [0, k]. **Linear time** — breaks the O(n log n) comparison sort lower bound.

```java
public int[] countingSort(int[] arr) {
    int max = Arrays.stream(arr).max().orElse(0);
    int[] count = new int[max + 1]; // Count array for range [0, max]

    // Count occurrences
    for (int num : arr) count[num]++;

    // Reconstruct sorted array
    int idx = 0;
    for (int i = 0; i <= max; i++) {
        while (count[i]-- > 0) {
            arr[idx++] = i;
        }
    }
    return arr;
}
// Time: O(n + k) where k = max value | Space: O(k) | Stable: Yes (with prefix sum version)
// Use when: range of values (k) is comparable to n
// Don't use when: k >> n (e.g., sorting 10 numbers in range 0-1,000,000 = waste)
```

---

## 8. 📌 Radix Sort — Sort by Digits

### Theory:
Sort numbers digit by digit, from least significant to most significant. Each digit-level sort uses a stable sort (usually counting sort). Works for integers and strings of fixed length.

```java
public void radixSort(int[] arr) {
    int max = Arrays.stream(arr).max().orElse(0);

    // Sort for each digit position (1, 10, 100, ...)
    for (int exp = 1; max / exp > 0; exp *= 10) {
        countingSortByDigit(arr, exp);
    }
}

private void countingSortByDigit(int[] arr, int exp) {
    int n = arr.length;
    int[] output = new int[n];
    int[] count = new int[10]; // Digits 0-9

    for (int num : arr) count[(num / exp) % 10]++;
    for (int i = 1; i < 10; i++) count[i] += count[i - 1]; // Prefix sum

    // Build output in reverse for stability
    for (int i = n - 1; i >= 0; i--) {
        int digit = (arr[i] / exp) % 10;
        output[--count[digit]] = arr[i];
    }
    System.arraycopy(output, 0, arr, 0, n);
}
// Time: O(d × (n + k)) where d = number of digits, k = 10
// Space: O(n + k) | Stable: Yes
```

---

## 9. 📌 Java's Built-in Sorting — TimSort

### Theory:
`Arrays.sort()` uses **Dual-Pivot QuickSort** for primitives and **TimSort** for objects.

**TimSort** (used by `Collections.sort()` and `Arrays.sort(Object[])`):
- Hybrid of Merge Sort + Insertion Sort
- Finds natural "runs" (already sorted subsequences) in data
- Uses Insertion Sort for short runs (< 32 elements)
- Merges runs using Merge Sort principles
- **Adaptive**: O(n) on already-sorted data, O(n log n) worst case
- **Stable**: Yes — preserves relative order of equal elements

```java
// Primitives — Dual-Pivot QuickSort (NOT stable)
int[] nums = {5, 3, 8, 1, 2};
Arrays.sort(nums); // Uses dual-pivot QuickSort internally

// Objects — TimSort (STABLE)
Integer[] nums2 = {5, 3, 8, 1, 2};
Arrays.sort(nums2); // Uses TimSort

// Custom comparator
Arrays.sort(intervals, (a, b) -> a[0] - b[0]); // Sort by first element
Arrays.sort(people, Comparator.comparingInt(p -> p.age)
                               .thenComparing(p -> p.name));

// Collections.sort — TimSort on lists
List<String> names = new ArrayList<>(List.of("Charlie", "Alice", "Bob"));
Collections.sort(names); // Natural order: Alice, Bob, Charlie
names.sort(Comparator.reverseOrder()); // Reverse: Charlie, Bob, Alice
```

---

## 🎯 Sorting Cross-Questioning Scenarios

### Q: "Why does Java use QuickSort for primitives but TimSort for objects?"
> **Answer:** "Stability doesn't matter for primitives (you can't tell two equal `int`s apart), so Java uses Dual-Pivot QuickSort which has better cache performance and no extra allocation. For objects, stability is important (equal `Employees` sorted by dept should keep their name order), so TimSort is used. TimSort also has O(n) performance on nearly-sorted data, which is common in real-world datasets."

### Q: "When would you choose Merge Sort over Quick Sort?"
> **Answer:** "Three cases: (1) Stability is required — merge sort is stable, quicksort is not. (2) Worst-case guarantee is needed — merge sort is always O(n log n), quicksort degrades to O(n²). (3) External sorting — data doesn't fit in RAM; merge sort's sequential access pattern works well with disk I/O. In practice, for in-memory sorting, quicksort wins due to cache locality."

### Q: "Can you sort in less than O(n log n)?"
> **Answer:** "Yes! O(n log n) is the lower bound for *comparison-based* sorting. Non-comparison sorts like Counting Sort O(n+k), Radix Sort O(d·n), and Bucket Sort O(n+k) achieve linear time — but only for specific data types (integers within known range, fixed-length strings). For arbitrary objects using comparisons, O(n log n) is provably optimal."

### Q: "You have 100GB of data and 4GB of RAM. How do you sort it?"
> **Answer:** "External Merge Sort: (1) Read 4GB chunks into RAM, sort each using QuickSort, write sorted chunks to disk. (2) K-way merge the sorted chunks using a min-heap of size K (one element from each chunk). This uses minimal RAM while producing the final sorted output. This is how `sort` command in Linux works for large files, and it's the basis of Hadoop MapReduce's sort phase."
