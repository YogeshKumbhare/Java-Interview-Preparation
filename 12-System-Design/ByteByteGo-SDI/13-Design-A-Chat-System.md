# Chapter 13: Design A Chat System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-chat-system)

A chat system like Facebook Messenger, WeChat, or WhatsApp. The focus is on designing the backend that supports both 1-on-1 and group chat.

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: What kind of chat app shall we design? 1-on-1 or group based?
**Interviewer**: Both 1-on-1 and group chat.

**Candidate**: Is this a mobile app, web app, or both?
**Interviewer**: Both.

**Candidate**: What is the scale? Startup or massive scale?
**Interviewer**: 50 million DAU.

**Candidate**: Group chat member limit?
**Interviewer**: Max 100 people.

**Candidate**: Important features? Attachments?
**Interviewer**: 1-on-1 chat, group chat, online indicator. Text only.

**Candidate**: Message size limit?
**Interviewer**: Text length is less than 100,000 characters.

**Candidate**: End-to-end encryption?
**Interviewer**: Not required. But discuss if time permits.

**Candidate**: How long shall we store chat history?
**Interviewer**: Forever.

---

## Step 2 - High-level design

### Communication protocols

- **HTTP**: Good for sending (client-initiated). Client sends message to chat service via HTTP.
- **Polling**: Client periodically asks server for new messages. Costly if done frequently.
- **Long polling**: Client holds connection open until new messages or timeout. Better than polling but still has drawbacks.
- **WebSocket**: Bi-directional, persistent connection. Most efficient for real-time communication. Both sending and receiving use WebSocket.

### High-level components

- **Stateless Services**: Authentication, service discovery, user profile, group management → behind load balancer
- **Stateful Service**: Chat service — maintains persistent WebSocket connections
- **Third-party integration**: Push notification service

### Storage

- **Relational DB** for generic data (user profiles, settings, friend lists)
- **Key-value store** for chat data: chat history is enormous, recent chats are accessed frequently, random access (search, mention). **Recommended: key-value stores** like HBase, Cassandra.

### Java Example – WebSocket Chat Server

```java
import java.util.*;
import java.util.concurrent.*;

public class ChatService {
    // userId -> list of messages
    private final Map<Long, Queue<Message>> messageQueues = new ConcurrentHashMap<>();
    // Online status
    private final Set<Long> onlineUsers = ConcurrentHashMap.newKeySet();

    record Message(long messageId, long fromUserId, long toUserId,
                   String content, long timestamp) {}

    public void userConnected(long userId) {
        onlineUsers.add(userId);
        messageQueues.putIfAbsent(userId, new ConcurrentLinkedQueue<>());
        System.out.println("User " + userId + " is ONLINE");
    }

    public void userDisconnected(long userId) {
        onlineUsers.remove(userId);
        System.out.println("User " + userId + " is OFFLINE");
    }

    public void sendMessage(long fromUserId, long toUserId, String content) {
        Message msg = new Message(
            System.nanoTime(), fromUserId, toUserId,
            content, System.currentTimeMillis());

        if (onlineUsers.contains(toUserId)) {
            // Deliver immediately via WebSocket
            messageQueues.computeIfAbsent(toUserId, k -> new ConcurrentLinkedQueue<>())
                         .add(msg);
            System.out.printf("[DELIVERED] %d → %d: %s%n", fromUserId, toUserId, content);
        } else {
            // Store for later + send push notification
            messageQueues.computeIfAbsent(toUserId, k -> new ConcurrentLinkedQueue<>())
                         .add(msg);
            System.out.printf("[STORED] %d → %d: %s (offline)%n",
                fromUserId, toUserId, content);
        }
    }

    public List<Message> getUnreadMessages(long userId) {
        Queue<Message> queue = messageQueues.getOrDefault(userId, new ConcurrentLinkedQueue<>());
        List<Message> messages = new ArrayList<>(queue);
        queue.clear();
        return messages;
    }

    public static void main(String[] args) {
        ChatService chat = new ChatService();
        chat.userConnected(1L);
        chat.userConnected(2L);

        chat.sendMessage(1L, 2L, "Hey! How are you?");
        chat.sendMessage(2L, 1L, "I'm good, thanks!");
        chat.sendMessage(1L, 3L, "Hello! Are you there?"); // user 3 offline

        System.out.println("\nUser 2's unread: " + chat.getUnreadMessages(2L));
    }
}
```

---

## Step 3 - Design deep dive

### Message table (1-on-1)

| Column | Type |
|--------|------|
| message_id | bigint (primary key) |
| message_from | bigint |
| message_to | bigint |
| content | text |
| created_at | timestamp |

### Message table (group chat)

| Column | Type |
|--------|------|
| channel_id | bigint (partition key) |
| message_id | bigint |
| user_id | bigint |
| content | text |
| created_at | timestamp |

### Message ID generation

- Must be unique and sortable by time
- Options: Auto-increment (not for NoSQL), global ID generator (Snowflake), local sequence number (per channel)
- **Recommended**: Local auto-increment sequence within each 1-on-1 channel or group channel

### Service discovery

- **Apache ZooKeeper**: Registers all chat servers and picks the best server for a client based on geographical location, server capacity, etc.

### Online presence

- **User login**: Change status to online, update `last_active_at`
- **User logout**: Change status to offline
- **Disconnection**: Use heartbeat mechanism — client sends heartbeat every X seconds, if no response within Y seconds, mark offline
- **Fanout**: Use pub/sub model — each friend pair subscribes to each other's status channel

---

## Step 4 - Wrap up

Additional talking points:
- **Extend to support media files** (photos/videos): compression, cloud storage, thumbnails
- **End-to-end encryption**
- **Caching messages on client-side**
- **Improve load time**
- **Error handling**: message resend mechanism, retry queue
