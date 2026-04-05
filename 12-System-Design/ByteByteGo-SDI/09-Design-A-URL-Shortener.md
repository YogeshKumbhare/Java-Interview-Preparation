# Chapter 9: Design A URL Shortener

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-url-shortener)

Designing a URL shortening service like TinyURL is a classic system design interview question.

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: Can you give an example of how a URL shortener work?
**Interviewer**: Assume URL `https://www.systeminterview.com/q=chatsystem&c=loggedin&v=v3&l=long` is the original URL. Your service creates an alias with shorter length: `https://tinyurl.com/y7keocwj`. If you click the alias, it redirects you to the original URL.

**Candidate**: What is the traffic volume?
**Interviewer**: 100 million URLs are generated per day.

**Candidate**: How long is the shortened URL?
**Interviewer**: As short as possible.

**Candidate**: What characters are allowed?
**Interviewer**: Numbers (0-9) and characters (a-z, A-Z).

**Candidate**: Can shortened URLs be deleted or updated?
**Interviewer**: For simplicity, let us assume shortened URLs cannot be deleted or updated.

**Requirements summary:**
- URL shortening: given a long URL → return a much shorter URL
- URL redirecting: given a shorter URL → redirect to the original URL
- High availability, scalability, and fault tolerance

**Back of the envelope estimation:**
- Write operation: 100 million URLs/day
- Write operation per second: 100 million / 24 / 3600 = ~1160
- Read operation: assuming 10:1 read-to-write ratio → 11600 reads/sec
- Assuming 10 year storage: 100 million * 365 * 10 = 365 billion records
- Average URL length: 100 bytes
- Storage over 10 years: 365 billion * 100 bytes = ~36.5 TB

---

## Step 2 - Propose high-level design

### API Endpoints

1. **URL shortening**: `POST /api/v1/data/shorten` — request parameter: `{longUrl: longURLString}` — return shortURL
2. **URL redirecting**: `GET /api/v1/shortUrl` — return longURL for HTTP redirection

### URL redirecting

When a user clicks a short URL, the server receives the request, changes the short URL to the long URL with **301 redirect** (permanent) or **302 redirect** (temporary).

- **301 redirect**: Permanently moved. Browser caches the response. Reduces server load.
- **302 redirect**: Temporarily moved. Useful for tracking click rate and source.

### URL shortening

To convert a long URL to a unique short URL, we need a hash function *f(longURL) → hashValue*.

### Java Example – URL Shortener with Base62

```java
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

public class URLShortener {
    private static final String BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";
    private final ConcurrentHashMap<String, String> shortToLong = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, String> longToShort = new ConcurrentHashMap<>();
    private final AtomicLong idCounter = new AtomicLong(100_000_000L);

    public String shorten(String longUrl) {
        if (longToShort.containsKey(longUrl)) {
            return longToShort.get(longUrl);
        }
        long id = idCounter.incrementAndGet();
        String shortUrl = base62Encode(id);
        shortToLong.put(shortUrl, longUrl);
        longToShort.put(longUrl, shortUrl);
        return shortUrl;
    }

    public String redirect(String shortUrl) {
        return shortToLong.get(shortUrl);
    }

    private String base62Encode(long value) {
        StringBuilder sb = new StringBuilder();
        while (value > 0) {
            sb.append(BASE62.charAt((int)(value % 62)));
            value /= 62;
        }
        return sb.reverse().toString();
    }

    public static void main(String[] args) {
        URLShortener shortener = new URLShortener();
        String longUrl = "https://www.systeminterview.com/q=chatsystem&c=loggedin&v=v3&l=long";
        String shortUrl = shortener.shorten(longUrl);
        System.out.println("Short URL: " + shortUrl);
        System.out.println("Redirect:  " + shortener.redirect(shortUrl));
    }
}
```

---

## Step 3 - Design deep dive

### Hash + collision resolution

A well-known hash function (MD5, SHA-1) can be used but produces long hash values. We take the first 7 characters. If collision occurs, append a predefined string and rehash.

### Base 62 conversion

Base 62 conversion uses 62 characters `[0-9, a-z, A-Z]`. A 7-character short URL can represent 62^7 = ~3.5 trillion URLs.

| Approach | Hash + collision | Base 62 |
|----------|-----------------|---------|
| Short URL length | Fixed | Not fixed (increases with ID) |
| Collision? | Yes, needs resolution | No |
| URL guessable? | No | Yes (sequential IDs) |

### URL shortening flow

1. Input: longURL
2. Check if longURL is in DB
3. If yes, return existing shortURL
4. If not, generate new unique ID
5. Convert to shortURL using base 62
6. Save to DB

### URL redirecting flow

1. User clicks short URL
2. Load balancer forwards request to web servers
3. If shortURL is in cache, return longURL
4. If not in cache, fetch from DB
5. Redirect user with 301/302

---

## Step 4 - Wrap up

Additional talking points:
- **Rate limiter**: filter out malicious requests
- **Web server scaling**: stateless, easy to scale
- **Database scaling**: replication and sharding
- **Analytics**: track click events for business insights
- **Availability, consistency, and reliability**
