# Chapter 26: Real-time Gaming Leaderboard

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/real-time-gaming-leaderboard)

Design a real-time leaderboard for an online mobile game, like Clash of Clans or Fortnite.

---

## Step 1 - Understand the problem and establish design scope

**Functional requirements:**
- Display top 10 players on the leaderboard
- Show a specific user's rank
- Display players who are +/- 4 ranks above/below the desired user

**Non-functional requirements:**
- Real-time update of scores
- Score updates should be reflected on the leaderboard in real-time
- General scalability, availability, and reliability

**Back of the envelope estimation:**
- 5 million DAU
- 25 million MAU
- Average 10 games played per DAU per day
- QPS for scoring: 5M * 10 / 86400 = ~580 writes/sec
- Peak QPS: 5x = ~2900/sec
- QPS for leaderboard read: 50 reads/sec

---

## Step 2 - High-level design

### API Design

1. `POST /v1/scores` — User wins a game, update score. Params: `user_id, points`
2. `GET /v1/scores` — Fetch top 10 leaderboard
3. `GET /v1/scores/{user_id}` — Fetch rank and score for a specific user

### High-level architecture

Game Service → Leaderboard Service → Data Store (Redis Sorted Set)

### Why Redis Sorted Set?

Redis Sorted Sets (ZSET) provide:
- `ZADD`: Add user with score — O(log n)
- `ZINCRBY`: Increment user score — O(log n)
- `ZREVRANK`: Get user rank (descending) — O(log n)
- `ZREVRANGE`: Get top N users — O(log n + m)
- `ZRANGEBYSCORE`: Get users in score range

This is significantly better than SQL-based approaches that require sorting the entire table.

### Java Example – Leaderboard with Redis Sorted Set

```java
import java.util.*;

/**
 * Simulates Redis Sorted Set behavior for a leaderboard
 * using Java's TreeMap.
 */
public class Leaderboard {
    // score -> set of user IDs (to handle same scores)
    private final TreeMap<Integer, Set<String>> scoreBoard = new TreeMap<>(Comparator.reverseOrder());
    private final Map<String, Integer> userScores = new HashMap<>();

    public void updateScore(String userId, int points) {
        // Remove old entry
        if (userScores.containsKey(userId)) {
            int oldScore = userScores.get(userId);
            scoreBoard.get(oldScore).remove(userId);
            if (scoreBoard.get(oldScore).isEmpty()) {
                scoreBoard.remove(oldScore);
            }
        }

        // Add new score
        int newScore = userScores.getOrDefault(userId, 0) + points;
        userScores.put(userId, newScore);
        scoreBoard.computeIfAbsent(newScore, k -> new LinkedHashSet<>()).add(userId);
    }

    public List<Map.Entry<String, Integer>> getTopN(int n) {
        List<Map.Entry<String, Integer>> result = new ArrayList<>();
        for (var entry : scoreBoard.entrySet()) {
            for (String userId : entry.getValue()) {
                result.add(Map.entry(userId, entry.getKey()));
                if (result.size() >= n) return result;
            }
        }
        return result;
    }

    public int getRank(String userId) {
        if (!userScores.containsKey(userId)) return -1;
        int rank = 0;
        int targetScore = userScores.get(userId);
        for (var entry : scoreBoard.entrySet()) {
            if (entry.getKey() > targetScore) {
                rank += entry.getValue().size();
            } else {
                for (String uid : entry.getValue()) {
                    rank++;
                    if (uid.equals(userId)) return rank;
                }
            }
        }
        return -1;
    }

    public static void main(String[] args) {
        Leaderboard lb = new Leaderboard();
        lb.updateScore("player_1", 100);
        lb.updateScore("player_2", 250);
        lb.updateScore("player_3", 180);
        lb.updateScore("player_4", 320);
        lb.updateScore("player_5", 150);
        lb.updateScore("player_1", 200); // player_1 now has 300

        System.out.println("=== Top 5 Leaderboard ===");
        var top5 = lb.getTopN(5);
        int rank = 1;
        for (var entry : top5) {
            System.out.printf("#%d  %-12s  %d pts%n", rank++, entry.getKey(), entry.getValue());
        }

        System.out.println("\nPlayer 3 rank: " + lb.getRank("player_3"));
    }
}
```

---

## Step 3 - Design deep dive

### Using Redis Sorted Sets

```
// When user wins a game
ZINCRBY leaderboard 1 user_1

// Get top 10
ZREVRANGE leaderboard 0 9 WITHSCORES

// Get user rank (0-indexed)
ZREVRANK leaderboard user_1

// Get user score
ZSCORE leaderboard user_1
```

### Scale considerations

For 5 million DAU, a single Redis node can handle the traffic since Redis can handle ~100K operations/sec.

For larger scale:
- **Sharding**: Partition by game mode or season
- **Read replicas**: Use Redis replicas for read-heavy leaderboard fetches
- **Periodic persistence**: Redis provides RDB and AOF persistence

### Handling ties

When two users have the same score:
- Use secondary sort by timestamp (earlier achievement = higher rank)
- Store as: `score * 1_000_000_000 + (MAX_TIMESTAMP - actual_timestamp)`

### Monthly/weekly leaderboards

- Use separate sorted sets per time period: `leaderboard:2024-03`, `leaderboard:2024-W12`
- Set TTL on old leaderboards to auto-expire

---

## Step 4 - Wrap up

Additional talking points:
- **System failure recovery**: Redis persistence (RDB snapshots + AOF)
- **Relative leaderboard**: Show friends-only leaderboard
- **Tournament leaderboards**: Time-boxed competitions
- **Anti-cheat mechanisms**: Score validation, anomaly detection
