# 🕷️ Design Web Crawler — System Design Interview

> **Source:** [Design Web Crawler w/ a Staff Engineer](https://www.youtube.com/watch?v=krsuaUp__pM)
> **Full Answer Key:** [hellointerview.com/web-crawler](https://www.hellointerview.com/learn/system-design/answer-keys/web-crawler)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Data Flow & System Interface](#2-data-flow--system-interface)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Fault Tolerance — Bad → Good → Great Solutions](#4-deep-dive-1-fault-tolerance--bad--good--great-solutions)
5. [Deep Dive 2: Politeness & robots.txt](#5-deep-dive-2-politeness--robotstxt)
6. [Deep Dive 3: URL Deduplication at Scale](#6-deep-dive-3-url-deduplication-at-scale)
7. [Deep Dive 4: Scaling to 10B Pages in 5 Days](#7-deep-dive-4-scaling-to-10b-pages-in-5-days)
8. [Interview Tips & Common Questions](#8-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Seed URLs** | Start from a set of seed URLs |
| **Crawl Web Pages** | Follow links, download HTML content |
| **Extract & Store** | Parse HTML, extract text, store content |
| **Discover New URLs** | Extract links → add to crawl frontier |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Scale** | 10 billion pages in ≤ 5 days | Google-scale |
| **Fault Tolerance** | No lost progress on crashes | Crawling takes days |
| **Politeness** | Respect robots.txt, rate limits | Don't DDoS websites |
| **Freshness** | Re-crawl changed pages | Web content changes |

### Back-of-Envelope
```
10B pages ÷ 5 days = 2B pages/day
= ~23,000 pages/second sustained for 5 days

Average page size: 100KB
Daily download: 2B × 100KB = 200TB/day
Total storage: 10B × 100KB = 1PB
```

---

## 2. Data Flow & System Interface

```
This is a DATA PIPELINE problem (no traditional API).

Data Flow:
  Seed URLs → URL Frontier (Queue) → Fetch → Parse → Extract URLs
                  ↑                                    │
                  └────────────────────────────────────┘
                      (discovered URLs fed back)

Stages:
  1. URL Frontier (priority queue): schedules URLs to crawl
  2. URL Fetcher: downloads HTML from external servers
  3. Content Parser: extracts text + metadata
  4. URL Extractor: discovers new links → back to frontier
  5. Content Store: saves parsed content (S3)
  6. Metadata DB: tracks URL status, last crawl time
```

---

## 3. High-Level Architecture

```
┌────────────────┐    ┌──────────────┐    ┌──────────────────┐
│ URL Frontier     │───│ URL Fetcher   │───│ Content Parser     │
│ (SQS / Kafka)   │    │ (Workers)     │    │ + URL Extractor    │
└────────────────┘    └──────┬───────┘    └─────────┬────────┘
        ↑                    │                      │
        │             ┌──────┴───────┐    ┌─────────┴────────┐
        │             │ S3 (Raw HTML) │    │ Metadata DB       │
        │             └──────────────┘    │ (URL status,      │
        │                                 │  robots.txt cache) │
        └─────────────────────────────────┘
                  (new URLs added to frontier)
                            │
                     ┌──────┴────────┐
                     │ Bloom Filter   │
                     │ (URL de-dup)   │
                     └───────────────┘
```

---

## 4. Deep Dive 1: Fault Tolerance — Bad → Good → Great Solutions

Crawling takes 5 days. Workers WILL crash. How do we avoid losing progress?

### Multi-Stage Pipeline with Stage-Level Recovery
```
The key insight: break crawling into STAGES with checkpoints.

Stage 1: URL Fetcher
  → Fetch HTML → store raw HTML in S3
  → If crash → message remains in queue → another worker retries

Stage 2: Text & URL Extraction
  → Read HTML from S3 → extract text + URLs → store results
  → If crash → HTML is safely in S3 → re-process

Each stage is independently recoverable.
No work from previous stages is lost.
```

### ❌ Bad Solution: In-Memory Timer for Retries
```
Worker maintains in-memory retry timer
→ Worker crashes → timer lost → URL never retried
→ All in-flight URLs are lost on crash
```

### ✅ Good Solution: Kafka with Manual Exponential Backoff
```
URLs in Kafka topic → worker reads URL → processes
→ Worker tracks offset → commits after success
→ If crash before commit → Kafka redelivers from last offset

Exponential backoff for failed fetches:
  Attempt 1: wait 1s → retry
  Attempt 2: wait 2s → retry
  Attempt 3: wait 4s → retry
  After N failures → send to dead-letter queue

Challenge: Kafka doesn't natively support delayed redelivery
→ Need custom retry logic in the worker
```

### ✅✅ Great Solution: SQS with Built-In Exponential Backoff
```
SQS advantages:
  1. Visibility timeout: message hidden from other workers until timeout
     → Worker crashes → message reappears after timeout → auto-retry
  2. ChangeMessageVisibility: extend timeout while processing
  3. Redrive policy: after N failures → auto-move to dead-letter queue
  4. No manual retry logic needed

vs Kafka:
  → Kafka retains messages in log, progress tracked by offset
  → Both work; SQS is simpler for this use case
```

### ✅✅ Advanced: Two-Stage URL Frontier (ByteByteGo Pattern)

> This is the production-grade URL Frontier design from the ByteByteGo System Design Interview book.

```
FRONT QUEUES (prioritization layer):
  URL incoming → compute priority (PageRank, update frequency, …)
  → Route to priority queue 1 (highest) through n (lowest)
  → Selector picks URLs from queues based on priority weights

BACK QUEUES (politeness layer, one queue per domain):
  Front queue URL → hash(domain) → assigned back queue
  → back_queue_1: all cnn.com URLs
  → back_queue_2: all nytimes.com URLs
  → Each worker can ONLY process one domain at a time → politeness guaranteed

DOMAIN SCHEDULER (min-heap):
  Heap key: next_allowed_fetch_time for each domain
  Heap.pop() → domain with earliest next fetch time
  → Worker fetches the URL for that domain
  → Update heap: domain.next_fetch_time = now + crawl_delay

Result:
  → No domain is over-crawled (politeness guaranteed by design)
  → High-priority pages crawled faster (prioritization guaranteed)
  → Completely decoupled from worker count (scalable)
```

---

## 5. Deep Dive 2: Politeness & robots.txt

### robots.txt Compliance
```
robots.txt example:
  User-agent: *
  Disallow: /private/
  Crawl-delay: 10        ← wait 10 seconds between requests

Crawler behavior:
  1. Before crawling any URL on domain X:
     a. Fetch robots.txt for domain X (if not cached)
     b. Parse rules → store in Metadata DB (cache TTL: 24 hours)
  2. Check: Is this URL allowed? (respect Disallow rules)
     → Disallowed → skip → acknowledge message → move on
  3. Check: Has Crawl-delay elapsed since last fetch from this domain?
     → NOT elapsed → ChangeMessageVisibility to defer processing
     → Elapsed → proceed to fetch

Per-domain rate limiting:
  → Track last_crawl_time per domain in Redis/Metadata DB
  → Max 1 request/second per domain (industry standard)
```

### Why Politeness Matters
```
Without rate limiting:
  → 1000 workers all crawling CNN.com simultaneously
  → CNN sees 1000 requests/second from our IP range
  → CNN blocks our IP → we can't crawl CNN at all
  → Or worse: CNN's site goes down → legal liability
```

---

## 6. Deep Dive 3: URL Deduplication at Scale

Before adding a URL to the frontier, check: "Have we already crawled or queued this URL?"

### ✅ Good Solution: Hash + Metadata DB
```
URL hash: SHA-256(normalized_url) → store in Metadata DB with index

Before adding URL:
  1. Normalize URL: lowercase, remove fragments, sort query params
  2. Hash: SHA-256(normalized_url)
  3. Query: SELECT 1 FROM crawled_urls WHERE hash = ? 
  4. If exists → skip. If not → add to frontier + insert hash.

Problem: 10B URLs × DB lookup per URL = enormous DB load
```

### ✅✅ Great Solution: Bloom Filter
```
In-memory Bloom filter:
  → 10B URLs with 1% false positive rate
  → Size: ~1.2GB (fits in RAM!)
  
Before adding URL:
  1. Check Bloom filter: BF.EXISTS url_filter url_hash
  2. "Definitely NOT seen" → add to frontier
  3. "Probably seen" (1% false positive) → skip
  
Why false positives are OK:
  → We skip a URL we haven't crawled → miss 1 page out of 10B
  → Acceptable trade-off for massive memory savings
  
Why false negatives are bad (and don't happen with Bloom filters):
  → Adding a URL we've already crawled → wasted work
  → Bloom filters guarantee: if added → always returns positive
```

### ✅✅ Advanced: Content-Level Deduplication with SimHash

> **URL dedup** catches duplicates from different URLs (same page, different paths). **Content dedup** catches near-duplicate pages (slightly different text, same content).

```
SimHash (used by Google for near-duplicate web page detection):
  1. Extract features from page: top-N TF-IDF terms + their weights
  2. For each term: compute bit_hash = hash(term) → 64-bit binary string
  3. For each bit position: 
     sum = Σ(weight × (+1 if bit=1, -1 if bit=0)) across all terms
  4. Final fingerprint: bit_i = 1 if sum_i > 0, else 0 → 64-bit fingerprint

Near-duplicate check:
  Hamming_distance(fingerprint_1, fingerprint_2) ≤ 3 → near-duplicate → skip
  (3-bit difference in 64-bit hash = ~95% similar content)

Storage: 64-bit fingerprint per page = 10B pages × 8 bytes = 80GB
  → Sharded across multiple machines, indexed for fast lookup

MinHash (alternative for Jaccard similarity):
  → Estimates % word overlap between two pages
  → Useful when near-duplicate threshold = "X% same words"
  → More expensive to compute than SimHash
```

---

## 7. Deep Dive 4: Scaling to 10B Pages in 5 Days

```
23,000 pages/second → need massive parallelism

1. Horizontal Scaling of Fetchers:
   → 1000+ crawler worker instances
   → Each worker fetches ~23 pages/second
   → Auto-scale based on queue depth

2. DNS Caching:
   → Cache DNS lookups in workers
   → Same domain = same IP → avoid repeated DNS queries
   → Multiple DNS providers for round-robin (avoid rate limits)

3. Geographic Distribution:
   → Deploy crawlers in multiple regions
   → Crawl EU sites from EU workers (lower latency)
   → Reduce cross-ocean bandwidth costs

4. Priority Queue (URL Frontier):
   → Not all pages are equal
   → High priority: news sites, frequently updated pages
   → Low priority: personal blogs, static pages
   → Re-crawl priority based on change frequency
```

---

## 8. Interview Tips & Common Questions

### Q: How do you handle JavaScript-rendered pages (SPAs)?
> Use a headless browser (Playwright, Puppeteer) for JS-heavy pages. Much more expensive (10x slower). Use selectively: detect if page needs JS rendering based on content type or known SPA frameworks.

### Q: How do you detect content changes for re-crawling?
> Store content hash (fingerprint) from last crawl. On re-crawl: compare new hash with stored hash. Change detected → update content and index. Unchanged → skip. Schedule re-crawl frequency based on historical change rate.

### Q: How do you handle spider traps?
> Infinite URL generation (e.g., calendar pages: /2024/01/01, /2024/01/02, ...). Solutions: max depth limit per domain, URL pattern detection, max pages per domain.

### Q: How do you normalize URLs?
> Remove fragments (#section). Lowercase hostname. Sort query parameters. Remove tracking parameters (utm_*). Convert to HTTPS. This prevents crawling the same page via different URLs.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
