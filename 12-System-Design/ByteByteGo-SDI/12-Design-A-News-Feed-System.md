# Chapter 12: Design A News Feed System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-news-feed-system)

A news feed is the constantly updating list of stories in the middle of your home page. It includes status updates, photos, videos, links, app activity, and likes from people, pages, and groups that you follow.

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: Is this a mobile app? Or a web app? Or both?
**Interviewer**: Both.

**Candidate**: What are the important features?
**Interviewer**: A user can publish a post and see friends' posts on the news feed page.

**Candidate**: Is the news feed sorted by reverse chronological order or by a ranking algorithm?
**Interviewer**: Feed is sorted by reverse chronological order for simplicity.

**Candidate**: How many friends can a user have?
**Interviewer**: 5000.

**Candidate**: What is the traffic volume?
**Interviewer**: 10 million DAU.

**Candidate**: Can the feed contain images, videos, or just text?
**Interviewer**: It can contain media files, including images and videos.

---

## Step 2 - High-level design

The design is divided into two flows:

### Feed publishing

When a user publishes a post, data is written into cache and database, and the post is populated into friends' news feed.

Components: Web servers → Post service → Fanout service → Notification service

### Newsfeed building

The news feed is built by aggregating friends' posts in reverse chronological order.

Components: Web servers → News Feed Service → News Feed Cache

### Fanout models

#### Fanout on write (push model)
- News feed is pre-computed during write time and delivered immediately to friends' cache.
- **Pros**: News feed generated in real-time and pushed immediately. Fetching is fast.
- **Cons**: If a user has many friends (celebrity problem), generating the news feed takes a lot of time. Inactive users waste computing resources.

#### Fanout on read (pull model)
- News feed is generated during read time. Recent posts are pulled when a user loads their page.
- **Pros**: Works better for inactive users. No hotkey problem.
- **Cons**: Fetching is slow since news feed is not pre-computed.

**Hybrid approach**: Use push model for most users. For celebrities with huge followings, use pull model.

### Java Example – Fanout Service

```java
import java.util.*;
import java.util.concurrent.*;

public class FanoutService {
    // userId -> list of feed items (pre-computed feed cache)
    private final Map<Long, List<FeedItem>> feedCache = new ConcurrentHashMap<>();
    // userId -> list of friend IDs
    private final Map<Long, List<Long>> friendsGraph = new ConcurrentHashMap<>();

    record FeedItem(long postId, long authorId, String content, long timestamp) {}

    public void publishPost(long authorId, String content) {
        FeedItem item = new FeedItem(
            System.nanoTime(), authorId, content, System.currentTimeMillis());

        // Fanout on write: push to all friends' feeds
        List<Long> friends = friendsGraph.getOrDefault(authorId, List.of());
        for (long friendId : friends) {
            feedCache.computeIfAbsent(friendId, k -> new CopyOnWriteArrayList<>())
                     .add(0, item); // prepend (reverse chronological)
        }
        System.out.println("Published post by user " + authorId
            + " → fanned out to " + friends.size() + " friends");
    }

    public List<FeedItem> getNewsFeed(long userId, int limit) {
        List<FeedItem> feed = feedCache.getOrDefault(userId, List.of());
        return feed.subList(0, Math.min(limit, feed.size()));
    }

    public static void main(String[] args) {
        FanoutService service = new FanoutService();

        // Setup friends graph
        service.friendsGraph.put(1L, List.of(2L, 3L, 4L));
        service.friendsGraph.put(2L, List.of(1L, 3L));

        // User 1 publishes a post
        service.publishPost(1L, "Hello World from User 1!");
        service.publishPost(2L, "Good morning from User 2!");

        // User 3 checks their feed
        var feed = service.getNewsFeed(3L, 10);
        System.out.println("\nUser 3's News Feed:");
        feed.forEach(f -> System.out.println("  " + f.authorId() + ": " + f.content()));
    }
}
```

---

## Step 3 - Design deep dive

### Feed publishing deep dive

1. User sends post via `POST /v1/me/feed?content=Hello&auth_token={token}`
2. Web server performs authentication and rate limiting
3. Post Service stores post in Post DB and Post Cache
4. Fanout Service fetches friend IDs from Graph DB
5. Gets friend info from User Cache
6. Sends messages to Message Queue
7. Fanout Workers deliver to News Feed Cache

### News feed retrieval deep dive

1. User sends `GET /v1/me/feed`
2. Load balancer distributes request
3. Web server routes to News Feed Service
4. News Feed Service gets post IDs from News Feed Cache
5. Fetches user info and post content from User Cache and Post Cache
6. Fully hydrated feed returned via CDN to client

### Cache architecture

Feed system requires multiple cache tiers:
- **News Feed**: stores IDs of news feeds
- **Content**: stores every post data (hot cache)
- **Social Graph**: stores user relationship data
- **Action**: stores user actions (liked, replied, etc.)
- **Counters**: stores likes count, replies count, followers, etc.

---

## Step 4 - Wrap up

Additional talking points:
- **Database scaling**: vertical vs horizontal, SQL vs NoSQL
- **Keep web tier stateless**
- **Cache data as much as possible**
- **Support multiple data centers**
- **Lose couple components with message queues**
- **Monitor key metrics**: QPS, latency during peak hours
