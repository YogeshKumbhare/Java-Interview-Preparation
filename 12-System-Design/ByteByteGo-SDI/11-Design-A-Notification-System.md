# Chapter 11: Design A Notification System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-notification-system)

A notification system sends important information to users. It supports multiple channels: mobile push notification, SMS, and email.

---

## Step 1 - Understand the problem and establish design scope

**Requirements:**
- Push notification, SMS, email
- Soft real-time: want a user to receive ASAP, but slight delay OK under high workload
- Supported devices: iOS, Android, laptop/desktop
- Notifications can be triggered by client applications or server-side scheduled
- Users can opt-out
- 10 million mobile push, 1 million SMS, 5 million email per day

---

## Step 2 - High-level design

### Different types of notifications

#### iOS push notification
- Provider → APNs (Apple Push Notification Service) → iOS Device
- Requires device token and payload

#### Android push notification
- Provider → FCM (Firebase Cloud Messaging) → Android Device

#### SMS message
- Provider → SMS Service (Twilio, Nexmo) → SMS

#### Email
- Provider → Email Service (Mailchimp, SendGrid) → Email

### Contact info gathering flow
When a user installs the app or signs up, the API server collects user contact info and stores it in the database.

**Contact info table:**
| Column | Type |
|--------|------|
| user_id | bigint |
| device_token | varchar |
| phone_number | varchar |
| email | varchar |
| channel | enum (push/sms/email) |
| opt_in | boolean |

### High-level design

1. **Services 1 to N**: Different services trigger notification events (billing, shipping, etc.)
2. **Notification System**: Orchestrates sending notifications
   - Provides APIs for services to send notifications
   - Carries out basic validations
   - Queries DB for user contact info
   - Creates notification events and puts them into message queues
3. **Message Queues**: Each notification channel has its own queue to decouple components
4. **Workers**: Pull events from queues and send to third-party services

### Java Example – Notification Service

```java
import java.util.*;
import java.util.concurrent.*;

public class NotificationService {
    
    enum Channel { PUSH, SMS, EMAIL }
    
    record Notification(String userId, Channel channel, String content, long timestamp) {}
    
    private final Map<Channel, BlockingQueue<Notification>> queues = new ConcurrentHashMap<>();
    private final ExecutorService workers = Executors.newFixedThreadPool(6);
    
    public NotificationService() {
        for (Channel ch : Channel.values()) {
            queues.put(ch, new LinkedBlockingQueue<>());
            // Start 2 workers per channel
            for (int i = 0; i < 2; i++) {
                workers.submit(() -> processQueue(ch));
            }
        }
    }
    
    public void send(String userId, Channel channel, String content) {
        Notification notif = new Notification(userId, channel, content, System.currentTimeMillis());
        queues.get(channel).offer(notif);
        System.out.printf("[QUEUED] %s → %s: %s%n", userId, channel, content);
    }
    
    private void processQueue(Channel channel) {
        while (!Thread.currentThread().isInterrupted()) {
            try {
                Notification notif = queues.get(channel).take();
                // Simulate sending
                Thread.sleep(100);
                System.out.printf("[SENT] %s via %s: %s%n", 
                    notif.userId(), notif.channel(), notif.content());
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
    }
    
    public static void main(String[] args) throws InterruptedException {
        NotificationService service = new NotificationService();
        service.send("user_1", Channel.PUSH, "Your order has shipped!");
        service.send("user_2", Channel.EMAIL, "Welcome to our platform");
        service.send("user_3", Channel.SMS, "Your OTP is 482910");
        service.send("user_1", Channel.EMAIL, "Weekly digest");
        Thread.sleep(2000);
        service.workers.shutdownNow();
    }
}
```

---

## Step 3 - Design deep dive

### Reliability

- **How to prevent data loss?** Persist notifications in a notification log database. Workers retry on failure.
- **Will recipients receive duplicate notifications?** Deduplicate using event_id. Check if event_id has been seen before sending.

### Additional components

- **Notification template**: Predefined templates with parameters to maintain consistency
- **Notification settings**: Users control which notifications they want to receive per channel
- **Rate limiting**: Limit how many notifications a user can receive → avoid overwhelming
- **Retry mechanism**: If a third-party service fails, add the notification back to the queue for retry
- **Security**: Only verified/authenticated clients should send notifications via APIs using appKey/appSecret
- **Monitor queued notifications**: Track total queued, processing time, etc.
- **Events tracking**: Open rate, click rate, engagement metrics

### Updated design

1. Notification servers with authentication + rate limiting
2. Cache for user info, device info, templates
3. Database for notification log, settings
4. Per-channel message queues
5. Workers for each channel
6. Third-party service integration
7. Analytics service for tracking

---

## Step 4 - Wrap up

Additional talking points:
- **Reliability**: Robust retry and fallback mechanism
- **Security**: appKey/appSecret authentication
- **Tracking and monitoring**: Fine-grained analytics
- **Respect user settings**: Unsubscribe mechanism
- **Rate limiting**: Frequency capping
