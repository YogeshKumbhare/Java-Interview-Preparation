# 🔍 Design Facebook Post Search — System Design Interview

> **Source:** [Design FB Post Search w/ Ex-Meta Interviewer](https://www.youtube.com/watch?v=l38XL9914fs)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: Inverted Index — How Search Works](#4-deep-dive-1-inverted-index--how-search-works)
5. [Deep Dive 2: Tokenization Pipeline (Building the Index)](#5-deep-dive-2-tokenization-pipeline-building-the-index)
6. [Deep Dive 3: Query Execution (Searching the Index)](#6-deep-dive-3-query-execution-searching-the-index)
7. [Deep Dive 4: Near Real-Time Indexing](#7-deep-dive-4-near-real-time-indexing)
8. [Deep Dive 5: Sharding Strategies](#8-deep-dive-5-sharding-strategies)
9. [Deep Dive 6: Relevance Ranking (TF-IDF, BM25)](#9-deep-dive-6-relevance-ranking-tf-idf-bm25)
10. [Interview Tips & Common Questions](#10-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Keyword Search** | Search posts by text content |
| **Near Real-Time** | New posts searchable within seconds |
| **Sorting** | Sort by recency or relevance |
| **Filtering** | Filter by date range, author, content type |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Scale** | Billions of posts indexed | Facebook scale |
| **Latency** | Sub-second query response | User experience |
| **Availability** | High — search must always work | Core feature |
| **Freshness** | Posts searchable within 5-10 seconds | "Near real-time" |

---

## 2. Core Entities & API Design

### Entities
```
Post       → id, user_id, content, media_type, created_at, like_count
SearchIndex → term → posting_list: [{ post_id, score, timestamp }, ...]
```

### API
```
GET /v1/search?q=world+cup&sort=relevance&limit=20&cursor=
GET /v1/search?q=birthday&author={userId}&start_date=2024-01-01

Response:
{
  "results": [
    { "post_id": "abc123", "snippet": "...World Cup final...", "score": 0.95 },
    { "post_id": "def456", "snippet": "...watching the World Cup...", "score": 0.82 }
  ],
  "cursor": "next_page_token"
}
```

---

## 3. High-Level Architecture

```
┌──────────────┐    ┌──────────────┐
│ Post Creation │───│    Kafka       │  (CDC: Change Data Capture)
│ (Post Service)│    │ (post_events) │
└──────────────┘    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │  Indexing      │
                    │  Workers       │  (Tokenize → build inverted index)
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │ Inverted Index │
                    │ (Distributed,  │
                    │  Elasticsearch │
                    │  or custom)    │
                    └──────┬───────┘
                           │
┌──────────┐    ┌──────────┴───────┐    ┌──────────────┐
│  Client   │───│  Search Service   │───│ Post Metadata │
└──────────┘    │ (Query parser +   │    │ DB (hydrate)  │
                │  ranker)          │    └──────────────┘
                └──────────────────┘
```

---

## 4. Deep Dive 1: Inverted Index — How Search Works

This is the foundational concept the video explains in detail.

### Regular Index vs Inverted Index
```
REGULAR INDEX (Forward Index):
  post_1 → ["the", "world", "cup", "is", "amazing"]
  post_2 → ["watching", "world", "news", "today"]

INVERTED INDEX (from term → documents):
  "world"    → [post_1, post_2]
  "cup"      → [post_1]
  "amazing"  → [post_1]
  "watching" → [post_2]
  "news"     → [post_2]
  "today"    → [post_2]

Why "inverted"? 
  → It inverts the document → terms relationship
  → Instead of "what words are in this document?" 
  → It answers "which documents contain this word?"
  → This is exactly what search needs!
```

---

## 5. Deep Dive 2: Tokenization Pipeline (Building the Index)

### Step-by-Step Tokenization

```
Input: "The 2024 World Cup is AMAZING!! 🏆 #football"

Step 1: TOKENIZE (split into words)
  → ["The", "2024", "World", "Cup", "is", "AMAZING!!", "🏆", "#football"]

Step 2: LOWERCASE
  → ["the", "2024", "world", "cup", "is", "amazing!!", "🏆", "#football"]

Step 3: REMOVE PUNCTUATION & SPECIAL CHARS
  → ["the", "2024", "world", "cup", "is", "amazing", "football"]

Step 4: REMOVE STOP WORDS (common words with no search value)
  Stop words: the, is, a, an, and, or, but, in, on, at...
  → ["2024", "world", "cup", "amazing", "football"]

Step 5: STEMMING (reduce words to root form)
  "amazing" → "amaz"
  "running" → "run"
  "football" → "football" (no change — already root)
  → ["2024", "world", "cup", "amaz", "football"]

Step 6: INSERT INTO INVERTED INDEX
  For each token → add this post_id to the token's posting list:
  "2024"     → [..., post_1]
  "world"    → [..., post_1]
  "cup"      → [..., post_1]
  "amaz"     → [..., post_1]
  "football" → [..., post_1]
```

### Posting List Structure
```
Term: "world"
Posting List (sorted by relevance score DESC):
[
  { post_id: "abc", timestamp: 1711814400, tf: 3, score: 0.95 },
  { post_id: "def", timestamp: 1711810800, tf: 1, score: 0.72 },
  { post_id: "ghi", timestamp: 1711807200, tf: 2, score: 0.63 },
  ...potentially millions of entries
]

tf = term frequency (how many times "world" appears in this post)
score = pre-computed relevance score (BM25)
```

---

## 6. Deep Dive 3: Query Execution (Searching the Index)

```
Query: "world cup highlights"

Step 1: TOKENIZE QUERY (same pipeline as indexing)
  → ["world", "cup", "highlight"] (stemmed)

Step 2: FETCH POSTING LISTS for each term:
  "world"     → [post_1, post_2, post_5, post_9, post_12, ...]  (1M entries)
  "cup"       → [post_1, post_5, post_9, post_23, ...]          (500K entries)
  "highlight" → [post_1, post_9, post_45, ...]                  (100K entries)

Step 3: INTERSECT posting lists (AND query):
  "world" ∩ "cup" ∩ "highlight" → [post_1, post_9]
  
  Optimization: start with SHORTEST posting list ("highlight")
  → Lookup each post_id in longer lists: O(log N) with binary search
  → Way faster than full intersection

Step 4: RANK results by relevance score
  post_1: combined_score = 0.95 (BM25)
  post_9: combined_score = 0.82

Step 5: HYDRATE (fetch full post content from Post DB)
  → Only for top 20 results (not all matches)

Step 6: RETURN with highlighted snippets
  → "...the World Cup highlights were incredible..."
```

---

## 7. Deep Dive 4: Near Real-Time Indexing

```
How does a post become searchable within seconds?

1. User creates post → written to Post DB
2. CDC (Change Data Capture) captures the INSERT
   → Published as event to Kafka topic "post_events"
3. Indexing Worker consumes from Kafka:
   a. Tokenize post content (pipeline from Deep Dive 2)
   b. For each token → append post_id to posting list in index
4. Post is now searchable via the inverted index

Latency: DB write (5ms) + Kafka (50ms) + Indexing (100ms) = ~200ms
→ Post is searchable within 200ms of creation! ✅
```

### Handling Deletes and Updates
```
Post DELETED:
  CDC event with delete flag → Indexing Worker:
  Option A: Remove post_id from all posting lists (eager)
  Option B: Mark as "tombstone" → filter at query time (lazy)
  → Lazy is faster, eager is cleaner. Start with lazy.

Post UPDATED (content changed):
  Old tokens: ["world", "cup"]
  New tokens: ["world", "match"]
  → Remove post from "cup" posting list
  → Add post to "match" posting list
  → Or simpler: delete old + re-index entire post
```

---

## 8. Deep Dive 5: Sharding Strategies

### Strategy 1: Shard by Term (Term Partitioning)
```
Shard A: terms starting with "a"-"m" → all posting lists for these terms
Shard B: terms starting with "n"-"z" → all posting lists for these terms

Query "world cup":
  → "world" lives on Shard B
  → "cup" lives on Shard A
  → Query BOTH shards in parallel → merge intersection

Pros: Only relevant shards are queried (not scatter-gather for everything)
Cons: Hot terms ("love", "happy") create massive hot shards
      Write skew: some shards get disproportionate updates
```

### Strategy 2: Shard by Document (Document Partitioning) ← Preferred
```
Shard A: posts 1-1M → has its own COMPLETE inverted index for these posts
Shard B: posts 1M-2M → has its own COMPLETE inverted index for these posts

Query "world cup":
  → Query ALL shards in parallel (scatter)
  → Each shard returns its local top-K results
  → Merge + re-rank globally (gather)
  → Return final top-K

Pros: ✅ Even write distribution (no hot shards)
      ✅ Each shard is self-contained (can be Elasticsearch instance)
Cons: ❌ Every query fans out to ALL shards
      ❌ With 100 shards → 100 concurrent queries per user query
      But: each shard responds in <10ms → total latency still <50ms
```

### Replication for Availability
```
Each shard = 3 replicas (1 primary + 2 replicas)
  → Writes go to primary
  → Reads distributed across replicas (load balancing)
  → If primary fails → replica promoted automatically
  → Cross-datacenter replication for disaster recovery
```

---

## 9. Deep Dive 6: Relevance Ranking (TF-IDF, BM25)

### TF-IDF (Term Frequency × Inverse Document Frequency)
```
TF (Term Frequency): How often does this term appear in THIS post?
  → "world" appears 3 times in post_1 → TF = 3/total_words

IDF (Inverse Document Frequency): How rare is this term ACROSS ALL posts?
  → "world" appears in 1M out of 1B posts → IDF = log(1B/1M) = 3.0
  → "the" appears in 900M out of 1B posts → IDF = log(1B/900M) = 0.05
  
  "world" has HIGH IDF → it's distinctive, useful for search
  "the" has LOW IDF → it's common, not useful for search

Score = TF × IDF
  → Words that are frequent IN this post but rare OVERALL score highest
```

### BM25 (Modern Improvement Over TF-IDF)
```
BM25 adds:
  1. Term frequency saturation: 3 occurrences of "world" is better than 1,
     but 30 occurrences isn't much better than 3 (diminishing returns)
     → Prevents keyword stuffing from getting unfair score boosts
  2. Document length normalization: longer posts naturally have more term 
     occurrences → normalize by post length divided by average post length
     → Prevents longer posts from being unfairly ranked higher

BM25 is what Elasticsearch, Apache Solr, and Lucene use by default.
In interview: mention BM25 as the industry standard ranking function.
```

### Social Ranking Signals (Facebook-Specific)
```
Beyond text relevance, add social signals:
  - Like count (engagement proxy)
  - Recency (exponential decay)
  - Relationship to viewer (friend's post > stranger's post)
  - Content type (video > text)

Final score = BM25_score × w1 + recency_boost × w2 + social_score × w3
```

### ✅✅ Industry Reality: Meta's Unicorn Search System

> Meta (Facebook) built **Unicorn**, a custom distributed search index that powers Facebook's entire search. It's not Elasticsearch — it's a proprietary purpose-built system.

```
Unicorn's Key Design Decisions:
  1. HYBRID INDEX: Real-time layer + Batch layer
     → Real-time: in-memory inverted index for recent posts (last 24 hours)
        → Searchable within seconds of posting
        → Updates streamed via Kafka + indexing workers
     → Batch: immutable, compressed index segments for older content
        → Generated by Spark jobs, highly optimized for disk reads
        → Merged periodically, old segments discarded
  
  2. VERTICAL SHARDING (by content type):
     → posts_index, events_index, groups_index, people_index
     → Separate index clusters per content type
     → Federated search: query multiple clusters → merge results

  3. HORIZONTAL SHARDING (by document ID range):
     → post_ids 0-1B → Shard 1
     → post_ids 1B-2B → Shard 2
     → All shards queried in parallel (scatter-gather) per cluster shard

  4. PRIVACY FILTERING (post-retrieval):
     → Search index contains posts regardless of privacy settings
     → After retrieving top results: apply ACL filter
        "Can current user see this post?"
     → Filter happens AFTER ranking, not before (for performance)
     → May reduce top-K to fewer than K results (acceptable)
```

---

## 10. Interview Tips & Common Questions

### Q: Why not just use Elasticsearch?
> In a system design interview, say: "Elasticsearch IS an inverted index with distributed sharding — let me explain how it works internally." Then walk through tokenization, posting lists, and query execution. The interviewer wants you to understand the INTERNALS, not just say "use Elasticsearch."

### Q: How do you handle typos and fuzzy search?
> **Edit distance** (Levenshtein): "wrold" → "world" (1 edit). **N-gram tokenization**: split "world" → ["wor", "orl", "rld"] → match partial strings. **Phonetic matching** (Soundex): "shawn" matches "sean". Mention as extension — don't volunteer complexity.

### Q: What about privacy? (It's Facebook)
> Search results MUST respect privacy settings. When querying, add a filter: "only return posts visible to current user." This requires a permission check layer between index lookup and result return. Can cache user's friend list for fast ACL checking.

### Q: How do you handle the "Hot Key" problem?
> Popular terms ("birthday", "happy") → massive posting lists. Cache frequent query results in Redis (TTL: 1 min). Pre-compute "hot term" summaries with top results.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
