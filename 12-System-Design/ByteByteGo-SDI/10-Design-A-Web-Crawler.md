# Chapter 10: Design A Web Crawler

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-a-web-crawler)

A web crawler is widely used by search engines to discover new or updated content on the web. Content can be a web page, an image, a video, a PDF file, etc. A web crawler starts by collecting a few seed URLs, then visits those pages, extracts URLs from them, and adds them to the list of URLs to visit.

A crawler is used for many purposes: **search engine indexing**, **web archiving**, **web mining**, and **web monitoring**.

---

## Step 1 - Understand the problem and establish design scope

**Basic algorithm:**
1. Given a set of seed URLs, download all web pages at those URLs.
2. Extract URLs from those pages.
3. Add new URLs to the list of URLs to download. Repeat.

**Requirements:**
- Scalability: The web is very large. Crawling should be efficient using parallelization.
- Robustness: Handle bad HTML, unresponsive servers, crashes, and malicious links.
- Politeness: Should not make too many requests to a website within a short time interval.
- Extensibility: Minimal changes needed to support new content types.

**Back of the envelope estimation:**
- 1 billion web pages per month
- QPS: 1,000,000,000 / 30 / 24 / 3600 = ~400 pages/sec
- Peak QPS: 800 pages/sec
- Average page size: 500 KB
- Storage/month: 1 billion * 500 KB = 500 TB
- Storage for 5 years: 500 TB * 12 * 5 = 30 PB

---

## Step 2 - High-level design

Key components:
1. **Seed URLs**: Starting point for the crawl process
2. **URL Frontier**: FIFO queue that stores URLs to be downloaded
3. **HTML Downloader**: Downloads web pages from the internet
4. **DNS Resolver**: Translates URL to IP address
5. **Content Parser**: Parses and validates HTML pages
6. **Content Seen?**: Eliminates data redundancy using hash comparison
7. **Content Storage**: Store HTML content (most on disk, popular on memory)
8. **URL Extractor**: Parses and extracts links from HTML pages
9. **URL Filter**: Excludes blacklisted URLs, error links, etc.
10. **URL Seen?**: Keep track of visited URLs using bloom filter or hash table
11. **URL Storage**: Store already-visited URLs

### Java Example – Simple Web Crawler

```java
import java.util.*;
import java.util.concurrent.*;

public class SimpleWebCrawler {
    private final Set<String> visited = ConcurrentHashMap.newKeySet();
    private final Queue<String> frontier = new ConcurrentLinkedQueue<>();
    private final int maxPages;

    public SimpleWebCrawler(int maxPages) {
        this.maxPages = maxPages;
    }

    public void crawl(List<String> seedUrls) {
        frontier.addAll(seedUrls);

        int crawled = 0;
        while (!frontier.isEmpty() && crawled < maxPages) {
            String url = frontier.poll();
            if (url == null || visited.contains(url)) continue;

            visited.add(url);
            crawled++;
            System.out.println("Crawling: " + url);

            // Simulate extracting URLs
            List<String> extractedUrls = extractUrls(url);
            for (String newUrl : extractedUrls) {
                if (!visited.contains(newUrl)) {
                    frontier.add(newUrl);
                }
            }
        }
        System.out.println("Total pages crawled: " + crawled);
    }

    private List<String> extractUrls(String url) {
        // In real implementation, download page and parse HTML
        return List.of(); // placeholder
    }

    public static void main(String[] args) {
        SimpleWebCrawler crawler = new SimpleWebCrawler(100);
        crawler.crawl(List.of("https://example.com", "https://example.org"));
    }
}
```

---

## Step 3 - Design deep dive

### DFS vs BFS
- **DFS**: Depth can be very deep. Not practical.
- **BFS**: Standard approach using FIFO queue.

### URL Frontier
The URL frontier is an important component implementing **politeness**, **priority**, and **freshness**.

- **Politeness**: Ensure only one request at a time to the same host. Use a queue router + mapping table + queue selector + worker threads.
- **Priority**: Prioritize URLs based on usefulness (PageRank, update frequency, traffic).
- **Freshness**: Recrawl based on web page update history.

### Robustness
- Consistent hashing for distributing crawl servers
- Save crawl state and data for recovery
- Exception handling
- Data validation

### Extensibility
- PNG/PDF/video downloader modules can be plugged in
- URL extractor extracts different types of links

### Detect and avoid problematic content
- **Redundant content**: ~30% of web content is duplicated. Use hash/checksum comparison.
- **Spider traps**: Infinite loops. Set a maximal length for URLs.
- **Data noise**: Filter ads, spam, etc.

---

## Step 4 - Wrap up

Additional talking points:
- **Server-side rendering**: Many websites use JavaScript to generate content dynamically
- **Filter unwanted pages**: Anti-spam component
- **Database replication and sharding**
- **Horizontal scaling**
- **Availability, consistency, and reliability**
- **Analytics**
