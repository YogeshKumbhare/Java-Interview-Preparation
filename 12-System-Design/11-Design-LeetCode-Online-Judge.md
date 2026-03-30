# ⚖️ Design LeetCode (Online Judge) — System Design Interview

> **Source:** [Design LeetCode w/ a Staff Engineer](https://www.youtube.com/watch?v=1xHADtekTNg)
> **Full Answer Key:** [hellointerview.com/leetcode](https://www.hellointerview.com/learn/system-design/answer-keys/leetcode)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Code Execution — Bad → Good → Great Solutions](#4-deep-dive-1-code-execution--bad--good--great-solutions)
5. [Deep Dive 2: Isolation & Security When Running User Code](#5-deep-dive-2-isolation--security-when-running-user-code)
6. [Deep Dive 3: Real-Time Leaderboard for Competitions](#6-deep-dive-3-real-time-leaderboard-for-competitions)
7. [Deep Dive 4: Scaling for Contest Spikes](#7-deep-dive-4-scaling-for-contest-spikes)
8. [Deep Dive 5: How Does Test Case Execution Actually Work?](#8-deep-dive-5-how-does-test-case-execution-actually-work)
9. [What is Expected at Each Level?](#9-what-is-expected-at-each-level)
10. [Interview Tips & Common Questions](#10-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Browse Problems** | View list of coding problems, filter by difficulty/topic |
| **Code & Submit** | In-browser editor with multi-language support, submit code |
| **Get Verdict** | Compile, run against test cases, return verdict within 5 seconds |
| **Contests** | Real-time competitions with live leaderboard |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Security** | **#1 priority** — code MUST NOT escape sandbox | Running untrusted code! |
| **Latency** | Verdict within 5 seconds | User experience |
| **Scalability** | 10K+ concurrent submissions during contests | Burst traffic |
| **Fairness** | One user can't affect others | Resource isolation |

---

## 2. Core Entities & API Design

### Entities
```
Problem     → id, title, description, difficulty, test_cases[]
              boilerplate_code: { "python": "class Solution:...", "java": "..." }
TestCase    → id, problem_id, input, expected_output, is_hidden, type
Submission  → id, user_id, problem_id, language, code, verdict, runtime_ms, memory_kb
Contest     → id, title, start_time, end_time, problem_ids[]
```

### API
```
GET    /v1/problems                    → Browse problems
GET    /v1/problems/{id}               → Problem details + visible test cases
POST   /v1/submissions                 → { problem_id, language, code } → submission_id
GET    /v1/submissions/{id}/status      → Verdict (poll or WebSocket/SSE)
GET    /v1/contests/{id}/leaderboard    → Real-time leaderboard
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌─────────────────┐
│  Browser  │───│  API Gateway  │───│ Problem Service   │
│ (Editor)  │    └──────┬───────┘    └─────────────────┘
│           │           │
│◄──SSE/WS──┤    ┌──────┴───────┐    ┌─────────────────┐
│ (Verdict) │    │ Submission    │───│   SQS / Kafka     │
└──────────┘    │ Service       │    └────────┬────────┘
                └──────────────┘             │
                                    ┌────────┴────────┐
                                    │  Code Execution   │
                                    │  Workers (ECS)    │
                                    │                   │
                                    │  ┌─────────────┐  │
                                    │  │ Docker/Firecracker│
                                    │  │ (Sandboxed)  │  │
                                    │  └─────────────┘  │
                                    └────────┬────────┘
                                             │
                                    ┌────────┴────────┐
                                    │  Results DB       │
                                    │ + Redis (Leaderboard)│
                                    └─────────────────┘
```

---

## 4. Deep Dive 1: Code Execution — Bad → Good → Great Solutions

### ❌ Bad Solution: Run Code in the API Server

```
POST /submit → API server compiles & runs the code
```
**Why it's terrible:**
- User submits `while(true){}` → API server hangs forever
- User submits `rm -rf /` → host filesystem destroyed
- User submits fork bomb → all resources consumed
- No isolation between users
- API server becomes single point of failure

### ✅ Good Solution: Run Code in a Virtual Machine (VM)

```
Spin up a VM for each submission:
  → Install language runtime (Python, Java, C++)
  → Copy code into VM
  → Execute with timeout
  → Capture stdout/stderr
  → Shut down VM
```
**Better:** Full OS-level isolation. Cross-user attacks impossible.
**Problems:** VM boot time = 30-60 seconds. Too slow. Too expensive (one VM per submission).

### ✅✅ Great Solution: Run Code in a Container (Docker)

```
Pre-built container images per language:
  leetcode-python:3.11
  leetcode-java:17
  leetcode-cpp:17

Execution flow:
  1. Worker pulls submission from queue
  2. Select pre-warmed container from pool
  3. Inject user code + test input
  4. Execute with strict resource limits (cgroups)
  5. Capture output, runtime, memory usage
  6. Compare with expected output → verdict
  7. Destroy/reset container
```
**Why Docker is great:** 
- ✅ Container startup: ~100ms (vs 30-60s for VM)
- ✅ Pre-warmed pool: 0ms startup (container already running)
- ✅ Lightweight: 100s of containers per host
- ❌ Shares host kernel → need additional security

### ✅✅ Great Solution: Serverless Functions (AWS Lambda)

```
Lambda function per language:
  → AWS manages isolation (Firecracker micro-VMs under the hood)
  → Auto-scales to thousands of concurrent executions
  → Pay-per-execution (no idle cost)
  → 15-minute timeout (more than enough for code execution)
```

---

## 5. Deep Dive 2: Isolation & Security When Running User Code

### Defense-in-Depth (5 Layers)

```
Layer 1: READ-ONLY FILESYSTEM
  → Mount code directory as read-only
  → Write output only to /tmp (auto-deleted after execution)
  → Prevents: malicious file creation, disk filling

Layer 2: CPU AND MEMORY BOUNDS (cgroups)
  → CPU: max 2 seconds per test case
  → Memory: max 256MB
  → PIDs: max 10 processes (prevents fork bombs)
  → If exceeded → process killed → verdict: TLE or MLE

Layer 3: EXPLICIT TIMEOUT
  → Wrap execution in a watchdog with 5-second hard kill
  → Prevents: infinite loops, sleep attacks
  → Even if code bypasses CPU limit, this kills it

Layer 4: NETWORK DISABLED
  → Use VPC Security Groups and NACLs
  → Block ALL outbound and inbound traffic
  → Prevents: data exfiltration, C2 communication, crypto mining

Layer 5: SYSTEM CALL RESTRICTIONS (seccomp)
  → Whitelist only essential syscalls (read, write, mmap, etc.)
  → Block dangerous syscalls (execve, mount, reboot, etc.)
  → Prevents: container escape, privilege escalation
```

### Isolation Tiers: From Good to Best

> The industry uses a **progressive hardening** approach based on trust level and security requirements.

```
TIER 1: Docker Containers (Good — most online judges)
  → NetworkMode: "none" → no internet
  → CapDrop: ["ALL"] → no Linux capabilities
  → --security-opt seccomp=/path/to/profile.json
  → Run as UID 999 (nobody/non-root)
  → Fast (~100ms startup), easy to manage
  → Weakness: shares host kernel → potential container escape

TIER 2: isolate (Better — used by Codeforces, ICPC, IOI)
  → Open-source tool built specifically for competitive programming judges
  → Uses Linux namespaces + cgroups (lighter than full Docker)
  → ~5ms overhead (vs 100ms for Docker)
  → Fine-grained control: per-wall-clock-time, per-CPU-time, per-memory
  → Kernel bypass for higher accuracy time measurement
  → Install: typically used with the `isolate` binary
  → Default choice for competitive programming: Codeforces, IOI official judge

TIER 3: AWS Firecracker MicroVMs (Best — AWS Lambda, Fargate)
  → True hardware-level VM isolation (separate kernel per execution)
  → Even a host kernel CVE CANNOT escape the VM boundary
  → 125ms startup time (vs seconds for EC2, ~100ms for Docker)
  → Built by AWS, open-sourced 2018, now industry gold standard
  → AWS Lambda uses Firecracker for EVERY function execution
  → Best for: financial institutions, government, highest security needs
```

---

## 6. Deep Dive 3: Real-Time Leaderboard for Competitions

### ❌ Bad Solution: Polling the Database

```
Every client polls: SELECT * FROM submissions WHERE contest_id = ? ORDER BY score
→ 10K participants × poll every 5s = 2K queries/second on the DB
→ Results are stale (5s polling gap)
```

### ✅ Good Solution: Cache with Periodic Updates

```
Background job aggregates scores → stores in cache
Clients read from cache
→ Reduces DB load
→ Still has update delay
```

### ✅✅ Great Solution: Redis Sorted Set with Long-Polling/SSE

```
Redis Sorted Set:
  ZADD leaderboard:{contest_id} score user_id

On each accepted submission:
  new_score = old_score + problem_points - time_penalty
  ZADD leaderboard:{contest_id} new_score user_id

To get top-50:
  ZREVRANGE leaderboard:{contest_id} 0 49 WITHSCORES
  → O(log N + K) for top-K query

Real-time updates to clients:
  → Server monitors Redis → pushes updates via SSE/WebSocket
  → Client refreshes leaderboard only when data changes
  → Periodic polling fallback (every 30s) for clients without SSE
```

---

## 7. Deep Dive 4: Scaling for Contest Spikes

### The Problem
```
Normal: ~100 submissions/minute
Contest start: 10,000 submissions in first 5 minutes = 100x spike
Weekly contest: 100K participants → burst to 1,000 submissions/sec
```

### ❌ Bad Solution: Vertical Scaling
More powerful server → still has a ceiling. Single point of failure.

### ✅✅ Great Solution: Dynamic Horizontal Scaling

```
ECS (Elastic Container Service) with auto-scaling:
  → Target: queue depth per worker ≤ 5
  → Queue depth rises → auto-launch more workers
  → Contest ends → queue drains → workers scale down

Pre-scaling for known events:
  → 30 minutes before contest start → pre-warm 500 workers
  → Immediately ready for burst
```

### ✅✅ Great Solution: Queue-Based Architecture (SQS/Kafka)

```
Submission Service → SQS → Workers

Why SQS is great here:
  → Automatically handles burst (buffer submissions)
  → Built-in retry with dead-letter queue
  → Visibility timeout: if worker crashes → message reappears
  → FIFO mode available for ordered processing
  → Workers consume at their own pace → no overload

Priority Queue:
  → Contest submissions: HIGH priority queue
  → Practice submissions: LOW priority queue
  → Contest submissions always processed first
```

---

## 8. Deep Dive 5: How Does Test Case Execution Actually Work?

This is a detail the video covers that's often missed:

```
Problem: "Maximum Depth of Binary Tree"

Test Case stored as:
{
  "type": "tree",
  "input": [3, 9, 20, null, null, 15, 7],  // level-order representation
  "output": 3
}

User's code (Python):
  class Solution:
      def maxDepth(self, root):
          # user's implementation

Execution steps inside the container:
  1. DESERIALIZE input: [3,9,20,null,null,15,7] → TreeNode structure
  2. CALL user's function: solution.maxDepth(root)
  3. SERIALIZE output: result → comparable format
  4. COMPARE: user_output == expected_output
  
Each language needs a "driver" program:
  - Handles input parsing
  - Calls user's function with proper types
  - Captures output
  - Handles edge cases (null input, empty arrays)
```

### Running Multiple Test Cases
```
For each test case:
  1. Run code with test input
  2. If output != expected → verdict: WRONG ANSWER (stop)
  3. If timeout exceeded → verdict: TLE (stop)
  4. If memory exceeded → verdict: MLE (stop)
  
If ALL test cases pass → verdict: ACCEPTED ✅
  Record: max(runtime across tests), max(memory across tests)
```

---

## 9. What is Expected at Each Level?

### Mid-Level
- Basic submission → execution → verdict flow
- Understand why you can't run code on the API server
- Database for storing problems and submissions

### Senior
- Container-based execution with resource limits
- Queue-based architecture for scaling
- Security layers (cgroups, read-only FS, no network)
- Redis leaderboard for contests

### Staff+
- Seccomp profiles for syscall restriction
- Pre-warmed container pools vs serverless trade-offs
- SQS with priority queues for contest vs practice
- Test case driver architecture (serialization/deserialization)
- Back-of-envelope: workers needed for 10K concurrent submissions
- Firecracker micro-VMs for kernel-level isolation

---

## 10. Interview Tips & Common Questions

### Q: What if someone writes an infinite loop?
> Three defense layers: (1) cgroup CPU limit kills process after 2 CPU-seconds, (2) explicit 5-second watchdog timer, (3) container auto-destroyed after timeout. Verdict: Time Limit Exceeded.

### Q: How do you ensure deterministic judging?
> Pin exact compiler/runtime versions in container images (Python 3.11.4, not "latest"). Use identical hardware specs for all workers. Disable non-deterministic optimizations. Memory limits are strict to prevent garbage collection timing differences.

### Q: How do you handle multiple languages?
> Each language = separate container image with its specific runtime + driver program. The `language` field in the submission routes to the correct image. Pre-warm containers for popular languages (Python, Java, C++).

### Q: How does the leaderboard scoring work?
> Score = sum of solved problem points. Tie-breaking = total time (time of last accepted submission). Penalty: +10 minutes per wrong submission on a solved problem. Redis ZADD with composite score: `score * 1e6 - total_time_seconds`.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
