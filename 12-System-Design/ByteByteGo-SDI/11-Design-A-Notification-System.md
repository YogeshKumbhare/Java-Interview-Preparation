# Chapter 11: Design A Notification System

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-notification-system)

A notification system has already become a very popular feature for many applications in recent years. A notification alerts a user with important information like breaking news, product updates, events, offerings, etc. It has become an indispensable part of our daily life. In this chapter, you are asked to design a notification system.

A notification is more than just mobile push notification. Three types of notification formats are: **mobile push notification**, **SMS message**, and **Email**.

![Figure 1 – Notification Types](images/ch11/figure-1.png)

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: What types of notifications does the system support?
**Interviewer**: Push notification, SMS message, and email.

**Candidate**: Is it a real-time system?
**Interviewer**: Let us say it is a soft real-time system. We want a user to receive notifications as soon as possible. However, if the system is under a high workload, a slight delay is acceptable.

**Candidate**: What are the supported devices?
**Interviewer**: iOS devices, android devices, and laptop/desktop.

**Candidate**: What triggers notifications?
**Interviewer**: Notifications can be triggered by client applications. They can also be scheduled on the server-side.

**Candidate**: Will users be able to opt-out?
**Interviewer**: Yes, users who choose to opt-out will no longer receive notifications.

**Candidate**: How many notifications are sent out each day?
**Interviewer**: 10 million mobile push notifications, 1 million SMS messages, and 5 million emails.

---

## Step 2 - Propose high-level design and get buy-in

### Different types of notifications

#### iOS push notification

![Figure 2 – iOS Push Notification](images/ch11/figure-2.png)

We primarily need three components to send an iOS push notification:

- **Provider**: Builds and sends notification requests to Apple Push Notification Service (APNS). Provides the device token and payload:

```json
{
   "aps":{
      "alert":{
         "title":"Game Request",
         "body":"Bob wants to play chess",
         "action-loc-key":"PLAY"
      },
      "badge":5
   }
}
```

- **APNS**: Remote service provided by Apple to propagate push notifications to iOS devices.
- **iOS Device**: End client, which receives push notifications.

#### Android push notification

Android adopts a similar notification flow. Instead of using APNs, **Firebase Cloud Messaging (FCM)** is commonly used to send push notifications to android devices.

![Figure 3 – Android Push Notification](images/ch11/figure-3.png)

#### SMS message

For SMS messages, third party SMS services like **Twilio**, **Nexmo**, and many others are commonly used. Most of them are commercial services.

![Figure 4 – SMS Message](images/ch11/figure-4.png)

#### Email

Although companies can set up their own email servers, many opt for commercial email services. **Sendgrid** and **Mailchimp** are among the most popular email services, which offer better delivery rate and data analytics.

![Figure 5 – Email Service](images/ch11/figure-5.png)

![Figure 6 – All Notification Types Overview](images/ch11/figure-6.png)

### Contact info gathering flow

To send notifications, we need to gather mobile device tokens, phone numbers, or email addresses. When a user installs our app or signs up for the first time, API servers collect user contact info and store it in the database.

![Figure 7 – Contact Info Gathering](images/ch11/figure-7.png)

![Figure 8 – Database Tables](images/ch11/figure-8.png)

Email addresses and phone numbers are stored in the user table, whereas device tokens are stored in the device table. A user can have multiple devices.

### Notification sending/receiving flow

#### High-level design

![Figure 9 – High-level Design](images/ch11/figure-9.png)

- **Service 1 to N**: A service can be a micro-service, a cron job, or a distributed system that triggers notification sending events.

- **Notification system**: The centerpiece of sending/receiving notifications. It provides APIs for services 1 to N, and builds notification payloads for third party services.

- **Third-party services**: Responsible for delivering notifications to users. Needs to pay extra attention to extensibility. For instance, FCM is unavailable in China; alternative third-party services such as Jpush, PushY, etc are used there.

**Three problems identified in this design:**

1. **Single point of failure (SPOF)**: A single notification server means SPOF.
2. **Hard to scale**: It is challenging to scale databases, caches, and different notification processing components independently.
3. **Performance bottleneck**: Processing and sending notifications can be resource intensive.

#### High-level design (improved)

After enumerating challenges in the initial design, we improve the design:

- Move the database and cache out of the notification server.
- Add more notification servers and set up automatic horizontal scaling.
- Introduce message queues to decouple the system components.

![Figure 10 – Improved High-level Design](images/ch11/figure-10.png)

The best way to go through the above diagram is from left to right:

- **Notification servers** provide the following functionalities:
  - Provide APIs for services to send notifications (only accessible internally to prevent spams).
  - Carry out basic validations to verify emails, phone numbers, etc.
  - Query the database or cache to fetch data needed to render a notification.
  - Put notification data to message queues for parallel processing.

API to send an email:
```
POST https://api.example.com/v/sms/send
Request body:
{
   "to":[{"user_id":123456}],
   "from":{"email":"from_address@example.com"},
   "subject":"Hello World!",
   "content":[{"type":"text/plain","value":"Hello, World!"}]
}
```

- **Cache**: User info, device info, notification templates are cached.
- **DB**: Stores data about user, notification, settings, etc.
- **Message queues**: Remove dependencies between components. Each notification type is assigned with a distinct message queue.
- **Workers**: Pull notification events from message queues and send them to the corresponding third-party services.

---

## Step 3 - Design deep dive

### Reliability

#### How to prevent data loss?

The notification system persists notification data in a database and implements a retry mechanism.

![Figure 11 – Notification Log DB](images/ch11/figure-11.png)

#### Will recipients receive a notification exactly once?

The short answer is **no**. To reduce the duplication occurrence, we introduce a dedupe mechanism. When a notification event first arrives, we check if it is seen before by checking the event ID. If it is seen before, it is discarded. Otherwise, we will send out the notification.

### Additional components and considerations

#### Notification template

A large notification system sends out millions of notifications per day. Notification templates are introduced to avoid building every notification from scratch.

```
BODY:
You dreamed of it. We dared it. [ITEM NAME] is back — only until [DATE].

CTA:
Order Now. Or, Save My [ITEM NAME]
```

Benefits: consistent format, reduced margin error, and time savings.

#### Notification setting

Users can have fine-grained control over notification settings stored in the notification setting table:

```
user_id bigInt
channel varchar # push notification, email or SMS
opt_in boolean # opt-in to receive notification
```

Before any notification is sent to a user, we first check if a user is opted-in.

#### Rate limiting

To avoid overwhelming users with too many notifications, we can limit the number of notifications a user can receive.

#### Retry mechanism

When a third-party service fails to send a notification, the notification will be added to the message queue for retrying. If the problem persists, an alert will be sent out to developers.

#### Security in push notifications

For iOS or Android apps, **appKey** and **appSecret** are used to secure push notification APIs. Only authenticated or verified clients are allowed to send push notifications.

#### Monitor queued notifications

A key metric to monitor is the total number of queued notifications. If the number is large, the notification events are not processed fast enough by workers. More workers are needed.

![Figure 12 – Queued Notifications Monitoring](images/ch11/figure-12.png)

#### Events tracking

Notification metrics such as open rate, click rate, and engagement are important. Analytics service implements events tracking.

![Figure 13 – Event Tracking](images/ch11/figure-13.png)

### Updated design

![Figure 14 – Updated Notification System Design](images/ch11/figure-14.png)

New components added:
- Notification servers equipped with authentication and rate-limiting.
- Retry mechanism to handle notification failures.
- Notification templates for consistent notification creation.
- Monitoring and tracking systems for system health checks.

### Java Example – Notification Dispatcher

```java
import java.util.concurrent.*;

public class NotificationDispatcher {

    enum NotificationType { PUSH, SMS, EMAIL }

    record NotificationEvent(String userId, NotificationType type, String message) {}

    private final BlockingQueue<NotificationEvent> pushQueue = new LinkedBlockingQueue<>();
    private final BlockingQueue<NotificationEvent> smsQueue = new LinkedBlockingQueue<>();
    private final BlockingQueue<NotificationEvent> emailQueue = new LinkedBlockingQueue<>();

    public void dispatch(NotificationEvent event) {
        switch (event.type()) {
            case PUSH  -> pushQueue.offer(event);
            case SMS   -> smsQueue.offer(event);
            case EMAIL -> emailQueue.offer(event);
        }
    }

    public void startWorkers() {
        ExecutorService executor = Executors.newFixedThreadPool(3);
        executor.submit(() -> processQueue(pushQueue,  "APNS/FCM"));
        executor.submit(() -> processQueue(smsQueue,   "Twilio"));
        executor.submit(() -> processQueue(emailQueue, "SendGrid"));
    }

    private void processQueue(BlockingQueue<NotificationEvent> queue, String provider) {
        while (true) {
            try {
                NotificationEvent event = queue.take();
                System.out.printf("[%s] Sending to user %s: %s%n",
                    provider, event.userId(), event.message());
                // Call third-party service here
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            }
        }
    }

    public static void main(String[] args) {
        NotificationDispatcher dispatcher = new NotificationDispatcher();
        dispatcher.startWorkers();

        dispatcher.dispatch(new NotificationEvent("user1", NotificationType.PUSH, "New message!"));
        dispatcher.dispatch(new NotificationEvent("user2", NotificationType.EMAIL, "Your order shipped"));
        dispatcher.dispatch(new NotificationEvent("user3", NotificationType.SMS, "OTP: 123456"));
    }
}
```

---

## Step 4 - Wrap up

In this chapter, we described the design of a scalable notification system that supports multiple notification formats: push notification, SMS message, and email. We adopted message queues to decouple system components.

- **Reliability**: A robust retry mechanism to minimize the failure rate.
- **Security**: AppKey/appSecret pair is used to ensure only verified clients can send notifications.
- **Tracking and monitoring**: Implemented in any stage of a notification flow to capture important stats.
- **Respect user settings**: Users may opt-out of receiving notifications.
- **Rate limiting**: Users will appreciate a frequency capping on the number of notifications they receive.

---

## Reference materials

[1] Twilio SMS: https://www.twilio.com/sms

[2] Nexmo SMS: https://www.nexmo.com/products/sms

[3] Sendgrid: https://sendgrid.com/

[4] Mailchimp: https://mailchimp.com/

[5] You Cannot Have Exactly-Once Delivery: https://bravenewgeek.com/you-cannot-have-exactly-once-delivery/

[6] Security in Push Notifications: https://cloud.ibm.com/docs/event-notifications?topic=event-notifications-en-push-apns

[7] Key metrics for RabbitMQ monitoring: https://www.datadoghq.com/blog/rabbitmq-monitoring/
