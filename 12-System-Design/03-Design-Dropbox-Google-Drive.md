# 📁 Design Dropbox / Google Drive — System Design Interview

> **Source:** [Design Dropbox/Google Drive w/ a Staff Engineer](https://www.youtube.com/watch?v=_UZ1ngy-kOI)
> **Full Answer Key:** [hellointerview.com/dropbox](https://www.hellointerview.com/learn/system-design/answer-keys/dropbox)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Deep Dive 1: How Do We Support Large File Uploads (50GB)?](#4-deep-dive-1-how-do-we-support-large-file-uploads-50gb)
5. [Deep Dive 2: Server-Side Chunk Verification (The Great Solution)](#5-deep-dive-2-server-side-chunk-verification-the-great-solution)
6. [Deep Dive 3: How Do We Make Uploads/Downloads/Syncing Fast?](#6-deep-dive-3-how-do-we-make-uploadsdownloadssyncing-fast)
7. [Deep Dive 4: How Do We Ensure File Security?](#7-deep-dive-4-how-do-we-ensure-file-security)
8. [Deep Dive 5: File Synchronization Across Devices](#8-deep-dive-5-file-synchronization-across-devices)
9. [What is Expected at Each Level?](#9-what-is-expected-at-each-level)
10. [Interview Tips & Common Questions](#10-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Upload Files** | Upload files up to 50GB reliably |
| **Download Files** | Download files from any device |
| **Auto-Sync** | Changes sync automatically across devices |
| **File Sharing** | Share files/folders with other users |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Reliability** | Zero data loss | Losing user files is unacceptable |
| **Availability** | 99.9%+ | Users depend on access 24/7 |
| **Scalability** | Billions of files | Global user base |
| **Low Latency** | Small changes sync within seconds | Delta sync |
| **Bandwidth Efficiency** | Minimize data transfer | Deduplication, compression |

---

## 2. Core Entities & API Design

### Entities
```
User         → id, name, email, storage_quota_bytes, used_bytes
FileMetadata → id, name, user_id, parent_folder_id, size, mime_type, 
               status (uploading|uploaded), fingerprint, created_at, updated_at
               chunks: [{ id, fingerprint, status (uploaded|not_uploaded), etag }]
Share        → id, file_id, shared_with_user_id, permission (read|write)
```

### API
```
POST   /v1/files                    → Create file metadata, get presigned URLs
PATCH  /v1/files/{id}/chunks        → Update chunk status after upload
POST   /v1/files/{id}/complete      → Finalize upload
GET    /v1/files/{id}/download      → Get presigned download URL (or CDN URL)
GET    /v1/files/{id}/versions      → List all versions
GET    /v1/sync?since=last_sync     → Get changes since last sync
POST   /v1/shares                   → Share file with user
```

> **Key Design Decision:** Never route file bytes through your application servers. Upload/download directly to/from blob storage (S3) using presigned URLs.

---

## 3. High-Level Architecture

```
┌──────────────┐    ┌──────────────┐    ┌───────────────────┐
│ Desktop/Web  │───│  API Gateway  │───│  File Service       │
│   Client     │    │              │    │ (Metadata CRUD)    │
└──────┬───────┘    └──────┬───────┘    └─────────┬─────────┘
       │                   │                      │
       │            ┌──────┴───────┐    ┌─────────┴─────────┐
       │            │ Notification  │    │    Metadata DB     │
       │            │ Service (WS)  │    │ (PostgreSQL/MySQL) │
       │            └──────────────┘    └───────────────────┘
       │
       │  Presigned URLs (direct upload/download)
       │            ┌──────────────┐
       └───────────│  S3 / GCS     │  (Object Storage for chunks)
                    └──────┬───────┘
                           │
                    ┌──────┴───────┐
                    │     CDN       │  (For downloads, shared files)
                    └──────────────┘
```

---

## 4. Deep Dive 1: How Do We Support Large File Uploads (50GB)?

### The Math (mentioned in the video)
```
50GB file × 8 bits/byte ÷ 100Mbps connection = 4,000 seconds = 1.11 hours
→ That's too long for a single HTTP POST request
→ Web servers have timeouts (Amazon API Gateway max payload: 10MB!)
→ Network interruptions are inevitable over 1+ hour uploads
```

### Why Chunking?
| Problem | Without Chunks | With Chunks |
|---------|---------------|-------------|
| Network drops at 49GB | Start over from 0 | Resume from last failed chunk |
| Progress indicator | Impossible | Show % complete |
| Timeouts | Request exceeds server limits | Each chunk is 5-10MB, well within limits |
| Parallel uploads | No | Upload chunks in parallel |
| Deduplication | Must upload entire file | Skip unchanged chunks |

### ❌ Bad Solution: Single POST to API Server

```
Client → API Server → S3
```
**Problems:** API server becomes bandwidth bottleneck. 50GB request exceeds all API Gateway limits. No resumability. No parallelism.

### ✅ Good Solution: Chunked Upload via Client PATCH

```
1. Client chunks file into 5-10MB pieces
2. Client calculates fingerprint (SHA-256) for each chunk
3. Client uploads chunks directly to S3 (presigned URLs)
4. On success, client sends PATCH to backend: { chunk_id, status: "uploaded" }
5. Backend updates FileMetadata.chunks array
```

**Challenge:** Client controls the status update → what if client lies or fails between upload and PATCH?

### ✅✅ Great Solution: Server-Side Chunk Verification

This is the recommended approach from the video. See next section for full details.

---

## 5. Deep Dive 2: Server-Side Chunk Verification (The Great Solution)

```
Step 1: CLIENT — Chunk the file
  - Split into 5-10MB chunks
  - Calculate fingerprint (SHA-256) for each chunk AND the entire file
  
Step 2: CLIENT → BACKEND — Check if file already exists
  POST /v1/files/check { fingerprint: "abc123" }
  → If file exists with status "uploading" → resume (return existing chunk statuses)
  → If file exists with status "uploaded" → skip (instant "upload"!)
  
Step 3: BACKEND → S3 — Initiate multipart upload
  - Call S3 CreateMultipartUpload API → get uploadId
  - Generate presigned URLs for each chunk (with uploadId + partNumber)
  - Save FileMetadata: { status: "uploading", chunks: [...not_uploaded...] }
  - Return uploadId + presigned URLs to client

Step 4: CLIENT → S3 — Upload chunks directly
  - Upload each chunk to its presigned URL
  - S3 returns ETag for each part
  - Client relays { chunkId, etag } to backend via PATCH

Step 5: BACKEND — Verify each chunk
  - Call S3 ListParts API to verify the chunk actually exists
  - Compare fingerprint/ETag
  - Update chunk status to "uploaded"

Step 6: BACKEND → S3 — Finalize
  - When ALL chunks are "uploaded":
    Call S3 CompleteMultipartUpload API (with part numbers + ETags)
  - S3 assembles parts into single object
  - Only after S3 confirms → update FileMetadata status to "uploaded"
```

### Resume Flow
```
Client exits at chunk 47 of 100 → Reopens app
  1. POST /files/check { fingerprint: "abc123" }
  2. Backend: "File exists, status: uploading, uploaded chunks: 1-46"
  3. Client: "Resume from chunk 47"
  → Only uploads remaining 53 chunks instead of all 100
```

---

## 6. Deep Dive 3: How Do We Make Uploads/Downloads/Syncing Fast?

### Delta Sync (Only Upload Changed Parts)
```
User edits a 1GB Photoshop file, changing a single layer:
  Without delta sync: upload entire 1GB → slow, wasteful
  With delta sync:    only upload changed chunks → maybe 10MB

How:
  1. Client re-chunks the modified file
  2. Computes new fingerprints for each chunk
  3. Compares with stored fingerprints:
     - chunk 15: fingerprint changed → upload
     - chunks 1-14, 16-100: fingerprints unchanged → skip
  4. Server updates file version with new chunk list
```

### Content-Defined Chunking (CDC) vs Fixed-Size Chunking
```
Fixed-Size Chunking (naive):
  Every 8MB = new chunk boundary regardless of content
  
  Boundary-Shift Problem:
    Original file: [chunk_1][chunk_2][chunk_3]
    Insert 1 byte at start: [NEW_chunk_1'][chunk_2'][chunk_3']
    → ALL chunk boundaries shifted → ALL fingerprints changed
    → Must re-upload ENTIRE file even for 1-byte insertion!

Content-Defined Chunking (smart):
  Use rolling hash to find boundaries based on CONTENT patterns:
  - Classic: Rabin fingerprinting (polynomial rolling hash)
  - Modern:  FastCDC (used by Dropbox and AWS Snowball)
             → 10x faster than Rabin fingerprinting
             → Better chunk-size distribution
             → Same boundary-stability guarantee
  
  How rolling hash works:
    Slide a window of N bytes across the file
    Compute hash of window at each position
    If hash % threshold == 0 → set chunk boundary HERE
    Content determines boundaries, not position
  
  With CDC:
    Insert 1 byte at start → only the first chunk boundary shifts
    → Other chunks maintain same boundaries + fingerprints
    → Upload only 1-2 modified chunks instead of all ← huge savings
    
  SHA-256 for integrity verification:
    Each chunk fingerprint = SHA-256(chunk_bytes)
    Guarantees data hasn't been corrupted in transit or storage
```

### Compression
```
Before uploading each chunk:
  - Compress using Zstandard (Zstd) or Gzip
  - Reduces transfer size by 30-80% depending on file type
  - Already-compressed files (JPEG, MP4) won't benefit much
  - Client compresses → uploads compressed chunk → S3 stores compressed
  - On download → client decompresses
```

### Download Optimization: CDN + Range Requests
```
For downloads:
  - Serve via CDN (CloudFront) → edge-cached, low latency
  - Use HTTP Range Requests for partial downloads
  - If user only needs page 5 of a PDF → download only those bytes
  - Parallel chunk downloads for faster reconstruction
```

---

## 7. Deep Dive 4: How Do We Ensure File Security?

### Three Layers of Security

| Layer | Mechanism | Details |
|-------|-----------|---------|
| **In Transit** | HTTPS (TLS 1.3) | All data encrypted between client ↔ S3 and client ↔ backend |
| **At Rest** | S3 Server-Side Encryption (SSE-S3 or SSE-KMS) | S3 encrypts with a unique key per object; key stored separately |
| **Access Control** | Presigned URLs + Share Table ACL | Time-limited URLs (15 min); server checks share permissions before generating URLs |

### Presigned URL Security
```
1. GENERATION: Server creates signed URL with:
   - URL path to specific S3 object
   - Expiration timestamp (15 min)
   - Signature using server's secret key
   - Optional: IP restriction

2. DISTRIBUTION: Only given to authenticated, authorized users
   - Backend checks: "Does this user own this file or have share access?"
   
3. VALIDATION: S3/CloudFront verifies:
   - Signature validity (tamper-proof)
   - Expiration not exceeded
   - If invalid → HTTP 403 Forbidden
```

### End-to-End Encryption (E2EE) — Bonus
```
For maximum privacy (like Boxcryptor):
  - Client encrypts chunks BEFORE uploading
  - Server/S3 never sees unencrypted data
  - Only the user's device has the decryption key
  → Mention this as a privacy extension if asked
```

---

## 8. Deep Dive 5: File Synchronization Across Devices

### Change Detection (Client-Side)
```
Desktop client uses File System Watcher:
  - macOS: FSEvents API
  - Windows: ReadDirectoryChangesW
  - Linux: inotify

When file change detected:
  1. Re-chunk modified file (Content-Defined Chunking)
  2. Compute new fingerprints
  3. Upload only changed chunks
  4. Notify backend: "File X updated, version 5"
```

### Cross-Device Notification
```
Device A uploads change → Backend updates metadata
  → WebSocket push to all other devices: "file X changed, version 5"
  → Device B receives notification
  → Device B: "My local version is 4, need version 5"
  → Device B fetches new metadata: which chunks changed?
  → Device B downloads only changed chunks from S3/CDN
  → Device B reconstructs file locally
```

### Conflict Resolution
```
Device A and B both edit file.txt while offline:

Option 1: Last Writer Wins (simple but may lose data)
Option 2: Create conflict copy (Dropbox approach):
  "file.txt" ← Device A's version (first to sync)
  "file (conflict copy from Device B).txt" ← Device B's version
  → User manually resolves

Option 3: Operational Transform (Google Docs approach):
  → Only for text-based collaborative editing
  → Not applicable for binary files
```

---

## 9. What is Expected at Each Level?

### Mid-Level
- Upload/download flow with S3
- Basic metadata service with database
- Understand why presigned URLs are important

### Senior
- Chunking for large files with resumability
- Deduplication via fingerprints (same content = same hash = stored once)
- File sharing with access control (ACL/share table)
- Cross-device sync with WebSocket notifications
- CDN for download optimization

### Staff+
- Content-Defined Chunking (CDC) for bandwidth efficiency
- S3 Multipart Upload API with server-side verification
- Compression (Zstd/Brotli) for transfer optimization
- End-to-end encryption discussion
- Conflict resolution strategies
- Sharding metadata DB by user_id
- Back-of-envelope: storage growth, bandwidth costs

---

## 10. Interview Tips & Common Questions

### Q: Why not store files directly in the database?
> Databases optimize for structured queries with indexes and transactions. Binary blobs don't benefit from this. S3 provides: virtually unlimited storage, 11 nines of durability, built-in CDN integration, and costs ~$0.023/GB vs ~$0.10/GB for RDS. That's 4x cheaper.

### Q: How does deduplication work?
> Content-addressable storage: `fingerprint(chunk) = SHA-256 hash`. Same content → same hash → stored once in S3. If User A and User B upload the same file, the chunks are identical hashes. Only metadata records differ. Dropbox reported this reduces storage by ~75%.

### Q: How do you handle versioning?
> Each file update creates a new FileMetadata version with a new list of chunk references. Old chunks remain in S3 (for older versions). Garbage collection removes chunks when no version references them. Users can "restore" old versions by re-pointing to old chunk list.

### Q: What's the sharding strategy for metadata?
> Shard by `user_id`. All files for a user live on the same shard. Benefits: directory listing = single-shard query, sharing = cross-shard (but rare). Use consistent hashing for even distribution.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
