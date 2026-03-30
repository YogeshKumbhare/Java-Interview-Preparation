# 📚 System Design Interview — Complete Guide

> **Source:** [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM) by Hello Interview (Ex-Meta Staff Engineers)

A comprehensive collection of **17 system design interview walkthroughs** with detailed documentation covering requirements, architecture, deep dives, and interview Q&A.

---

## 📖 Index

| # | Topic | Difficulty | Key Concepts | File |
|---|-------|-----------|-------------|------|
| 0 | [Message Queues](./Message-Queues-System-Design.md) | ⭐⭐ | Pub/Sub, Partitions, Consumer Groups, Idempotency | Foundational |
| 1 | [Design Ticketmaster](./01-Design-Ticketmaster.md) | ⭐⭐⭐ | Concurrency, Seat Locking, Virtual Waiting Room | Booking System |
| 2 | [Design Uber](./02-Design-Uber.md) | ⭐⭐⭐⭐ | Geospatial Indexing, H3/Geohash, Real-Time Matching | Ride-Hailing |
| 3 | [Design Dropbox/Google Drive](./03-Design-Dropbox-Google-Drive.md) | ⭐⭐⭐ | Chunking, Deduplication, Pre-signed URLs, File Sync | File Storage |
| 4 | [Design Bitly (URL Shortener)](./04-Design-Bitly-URL-Shortener.md) | ⭐⭐ | Base62 Encoding, Read-Heavy Cache, 301 vs 302 | URL Shortening |
| 5 | [Design Twitter](./05-Design-Twitter.md) | ⭐⭐⭐⭐ | Fan-Out on Write/Read, Celebrity Problem, Timeline | Social Feed |
| 6 | [Design WhatsApp](./06-Design-WhatsApp.md) | ⭐⭐⭐⭐ | WebSocket, Delivery Receipts, Offline Inbox | Messaging |
| 7 | [Design Ad Click Aggregator](./07-Design-Ad-Click-Aggregator.md) | ⭐⭐⭐⭐ | Lambda Architecture, Flink, Click Fraud, Exactly-Once | Data Pipeline |
| 8 | [Design Web Crawler](./08-Design-Web-Crawler.md) | ⭐⭐⭐ | URL Frontier, Bloom Filter, Politeness, BFS | Infrastructure |
| 9 | [Design YouTube](./09-Design-YouTube.md) | ⭐⭐⭐⭐ | Video Transcoding, CDN, Adaptive Bitrate, HLS/DASH | Video Streaming |
| 10 | [Design Rate Limiter](./10-Design-Distributed-Rate-Limiter.md) | ⭐⭐⭐ | Token Bucket, Sliding Window, Redis Lua, Atomic Ops | Infrastructure |
| 11 | [Design LeetCode (Online Judge)](./11-Design-LeetCode-Online-Judge.md) | ⭐⭐⭐ | Sandboxed Execution, Firecracker, Container Security | Code Execution |
| 12 | [Design Tinder](./12-Design-Tinder.md) | ⭐⭐⭐⭐ | Geospatial, Async Swipe, Bloom Filter, Recommendation | Dating App |
| 13 | [Design Live Comments](./13-Design-Live-Comments.md) | ⭐⭐⭐ | WebSocket Fan-Out, Pub/Sub, Backpressure, Sampling | Real-Time |
| 14 | [Design Facebook News Feed](./14-Design-Facebook-News-Feed.md) | ⭐⭐⭐⭐ | Hybrid Fan-Out, ML Ranking, EdgeRank, Personalization | Social Feed |
| 15 | [Top-K / Heavy Hitters](./15-Top-K-Heavy-Hitters.md) | ⭐⭐⭐⭐ | Count-Min Sketch, Space-Saving, Streaming Aggregation | Data Structure |
| 16 | [Design Facebook Post Search](./16-Design-Facebook-Post-Search.md) | ⭐⭐⭐ | Inverted Index, Tokenization, Sharding, BM25 | Search |

---

## 🗂️ By Category

### Social & Communication
- [Design Twitter](./05-Design-Twitter.md) — Feed generation, fan-out strategies
- [Design WhatsApp](./06-Design-WhatsApp.md) — Real-time messaging, delivery receipts
- [Design Facebook News Feed](./14-Design-Facebook-News-Feed.md) — Ranking, personalization
- [Design Live Comments](./13-Design-Live-Comments.md) — Real-time broadcasting

### Location-Based
- [Design Uber](./02-Design-Uber.md) — Geospatial indexing, ride matching
- [Design Tinder](./12-Design-Tinder.md) — Proximity matching, swiping

### Content & Media
- [Design YouTube](./09-Design-YouTube.md) — Video upload, transcoding, streaming
- [Design Dropbox/Google Drive](./03-Design-Dropbox-Google-Drive.md) — File sync, chunking

### Data & Analytics
- [Design Ad Click Aggregator](./07-Design-Ad-Click-Aggregator.md) — Real-time aggregation
- [Top-K / Heavy Hitters](./15-Top-K-Heavy-Hitters.md) — Streaming data structures
- [Design Facebook Post Search](./16-Design-Facebook-Post-Search.md) — Full-text search

### Infrastructure & Foundational
- [Message Queues](./Message-Queues-System-Design.md) — Core messaging concepts
- [Design Rate Limiter](./10-Design-Distributed-Rate-Limiter.md) — API protection
- [Design Web Crawler](./08-Design-Web-Crawler.md) — Distributed crawling

### Booking & E-Commerce
- [Design Ticketmaster](./01-Design-Ticketmaster.md) — Seat booking, concurrency
- [Design Bitly](./04-Design-Bitly-URL-Shortener.md) — URL shortening

### Code Execution
- [Design LeetCode](./11-Design-LeetCode-Online-Judge.md) — Sandboxed execution

---

## 🔑 Common Patterns Across All Designs

| Pattern | Used In |
|---------|---------|
| **Message Queues (Kafka)** | ALL designs — decoupling, async processing |
| **Redis Caching** | Bitly, Twitter, Tinder, Rate Limiter, Top-K, News Feed |
| **WebSocket** | WhatsApp, Uber, Live Comments, Tinder, LeetCode |
| **Pre-signed URLs** | Dropbox, YouTube — direct client-to-storage upload |
| **Fan-Out on Write** | Twitter, News Feed, WhatsApp (groups) |
| **Geospatial Indexing** | Uber (H3), Tinder (S2/Quadtree) |
| **Inverted Index** | FB Post Search, Web Crawler |
| **Bloom Filter** | Web Crawler (URL dedup), Tinder (seen profiles) |
| **Optimistic Concurrency** | Ticketmaster (seat booking), Uber (driver matching) |
| **Lambda Architecture** | Ad Click Aggregator, Top-K |
| **CDN** | YouTube (video delivery), Ticketmaster (static pages) |
| **Cassandra/NoSQL** | WhatsApp, Twitter, Tinder — high write throughput |

---

> **💡 Pro Tip:** Most system design interviews follow the same framework:
> 1. **Requirements** (5 min) — Clarify functional + non-functional
> 2. **Core Entities** (2 min) — Data models
> 3. **API Design** (3 min) — REST endpoints
> 4. **High-Level Architecture** (10 min) — Boxes and arrows
> 5. **Deep Dives** (15 min) — 2-3 hard problems specific to the system

---

*All documentation created from the [System Design Walkthroughs](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM) playlist by Hello Interview*
