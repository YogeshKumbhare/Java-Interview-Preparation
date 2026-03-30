# 📺 Design YouTube — System Design Interview

> **Source:** [Design YouTube w/ a Staff Engineer](https://www.youtube.com/watch?v=IUrQ5_g3XKs)
> **Full Answer Key:** [hellointerview.com/youtube](https://www.hellointerview.com/learn/system-design/answer-keys/youtube)

---

## Table of Contents
1. [Requirements](#1-requirements)
2. [Core Entities & API Design](#2-core-entities--api-design)
3. [High-Level Architecture](#3-high-level-architecture)
4. [Background: How Video Streaming Actually Works](#4-background-how-video-streaming-actually-works)
5. [Deep Dive 1: Video Storage — Bad → Good → Great Solutions](#5-deep-dive-1-video-storage--bad--good--great-solutions)
6. [Deep Dive 2: Video Streaming — Bad → Good → Great Solutions](#6-deep-dive-2-video-streaming--bad--good--great-solutions)
7. [Deep Dive 3: Video Processing Pipeline (Transcoding)](#7-deep-dive-3-video-processing-pipeline-transcoding)
8. [Deep Dive 4: Resumable Uploads](#8-deep-dive-4-resumable-uploads)
9. [Deep Dive 5: Scaling to Billions of Daily Views](#9-deep-dive-5-scaling-to-billions-of-daily-views)
10. [What is Expected at Each Level?](#10-what-is-expected-at-each-level)
11. [Interview Tips & Common Questions](#11-interview-tips--common-questions)

---

## 1. Requirements

### Functional Requirements
| Feature | Description |
|---------|-------------|
| **Upload Video** | Users upload large video files (up to several GB) |
| **Stream Video** | Smooth playback with adaptive quality |
| **Search** | Search videos by title, tags, description |

### Non-Functional Requirements
| Requirement | Target | Why |
|-------------|--------|-----|
| **Availability** | 99.99% | Global platform, billions rely on it |
| **Low Latency** | Fast time-to-first-frame | Users have short attention spans |
| **Scalability** | 500 hours of video uploaded per minute | Massive write load |
| **Reliability** | No lost uploads | User-generated content is irreplaceable |

### Back-of-Envelope
```
Users: 2B monthly, 500M daily
Uploads: 500 hours of video/minute → ~720K videos/day
Storage per video: average 5-min × 100MB source = 500MB
  After transcoding (5 resolutions × segments): ~1.5GB per video
Daily storage growth: 720K × 1.5GB = ~1PB/day
Views: 5B views/day → ~58K views/second
```

---

## 2. Core Entities & API Design

### Entities
```
Video       → id, user_id, title, description, tags[], 
              status (uploading|processing|ready|failed), created_at
VideoMetadata → format, resolution, codec, duration, segments[]
              chunks: [{ id, fingerprint, status (uploaded|not_uploaded), etag }]
Segment     → id, video_id, resolution, codec, url, duration_seconds
Manifest    → id, video_id, type (master|media), url
```

### API
```
POST   /v1/videos                  → { title, description } → returns video_id + presigned URLs
PATCH  /v1/videos/{id}/chunks      → Update chunk upload status
GET    /v1/videos/{id}             → Video metadata
GET    /v1/videos/{id}/manifest    → Returns HLS/DASH manifest URL
GET    /v1/search?q=               → Full-text search
```

---

## 3. High-Level Architecture

```
┌──────────┐    ┌──────────────┐    ┌──────────────────┐
│  Client   │───│  API Gateway  │───│ Video Service      │
└──────┬───┘    └──────────────┘    └───────┬──────────┘
       │                                    │
       │  Presigned URLs                    │
       │         ┌──────────────┐    ┌──────┴──────────┐
       └────────│  S3 (Raw)     │    │  Video DB        │
                │ (Source files)│    │  (Cassandra)     │
                └──────┬───────┘    └─────────────────┘
                       │
                ┌──────┴────────────────────┐
                │  Video Processing Service  │
                │  (DAG: split → transcode   │
                │   → manifest → notify)     │
                └──────┬────────────────────┘
                       │
                ┌──────┴───────┐    ┌──────────────┐
                │ S3 (Processed)│───│     CDN       │
                │ (Segments)    │    │ (Edge nodes)  │
                └──────────────┘    └──────────────┘
```

---

## 4. Background: How Video Streaming Actually Works

This is foundation knowledge the video explains before diving into solutions:

```
A video is NOT one big file that downloads completely before playing.

Modern streaming (HLS/DASH):
  1. Video is divided into small segments (2-10 seconds each)
  2. Each segment exists in MULTIPLE formats:
     - 360p @ 500kbps    (mobile, poor network)
     - 720p @ 2.5Mbps    (tablet, average network)
     - 1080p @ 5Mbps     (desktop, good network)
     - 4K @ 15Mbps       (TV, excellent network)
  3. A "manifest" file lists ALL available segments and formats
  4. The player:
     a. Downloads manifest
     b. Starts with lowest quality (fast start)
     c. Measures download speed
     d. Dynamically switches quality based on bandwidth:
        - Network fast → upgrade to 1080p
        - Network drops → downgrade to 360p
     e. This is called "Adaptive Bitrate Streaming" (ABR)
```

---

## 5. Deep Dive 1: Video Storage — Bad → Good → Great Solutions

### ❌ Bad Solution: Store the Raw Video Only

```
User uploads a 4K ProRes file (50GB) → store as-is in S3
→ Every viewer downloads the same 50GB file
→ Mobile user on 3G cannot stream 4K
→ No quality adaptation
```

### ✅ Good Solution: Store Different Video Formats (Full Files)

```
Transcode raw video into multiple format/resolution combos:
  video_123_360p.mp4
  video_123_720p.mp4
  video_123_1080p.mp4
  video_123_4k.mp4

Player selects format based on device/network
→ Better, but user must choose upfront
→ Can't switch mid-stream if network changes
→ Still large files to download before playing
```

### ✅✅ Great Solution: Store Different Formats as SEGMENTS

```
Split each format into 10-second segments:
  video_123/360p/segment_001.ts
  video_123/360p/segment_002.ts
  ...
  video_123/1080p/segment_001.ts
  video_123/1080p/segment_002.ts
  ...

Plus manifest files:
  video_123/master.m3u8      → lists all available quality levels
  video_123/360p/media.m3u8  → lists all 360p segments
  video_123/1080p/media.m3u8 → lists all 1080p segments
```

**This enables:**
- ✅ Adaptive bitrate switching on segment boundaries
- ✅ Fast start (play immediately, buffer as you go)
- ✅ Seek support (jump to segment N)
- ✅ CDN-friendly (small files, independently cacheable)

---

## 6. Deep Dive 2: Video Streaming — Bad → Good → Great Solutions

### ❌ Bad Solution: Download Entire Video File

```
Client → download video_123_720p.mp4 (500MB)
→ Must wait for full download before playing
→ Wastes bandwidth if user watches only 30 seconds
```

### ✅ Good Solution: Download Segments Incrementally

```
1. Client downloads manifest
2. Downloads segment 1 → plays it (start within 2 seconds!)
3. While playing segment 1, downloads segment 2
4. Continues prefetching next segment

→ No waiting for full download
→ Bandwidth proportional to watch time
```

### ✅✅ Great Solution: Adaptive Bitrate Streaming (ABR)

```
HLS/DASH Master Manifest Example:

#EXTM3U
#EXT-X-STREAM-INF:BANDWIDTH=500000,RESOLUTION=640x360
  360p/media.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480
  480p/media.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=2500000,RESOLUTION=1280x720
  720p/media.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=5000000,RESOLUTION=1920x1080
  1080p/media.m3u8
#EXT-X-STREAM-INF:BANDWIDTH=15000000,RESOLUTION=3840x2160
  4k/media.m3u8

Player behavior:
  1. Download master manifest
  2. Start with 360p (fastest start)
  3. After each segment download, measure throughput:
     downloaded 1MB in 0.1s → throughput = 80Mbps
     → Can handle 1080p (needs 5Mbps) → switch UP
  4. Network congestion detected:
     downloaded 1MB in 2s → throughput = 4Mbps
     → Can't handle 1080p → switch DOWN to 720p
  5. Seamless transitions at segment boundaries (no buffering!)
```

---

## 7. Deep Dive 3: Video Processing Pipeline (Transcoding)

### The DAG (Directed Acyclic Graph) Workflow

```
S3 upload complete → event notification → Processing Pipeline:

1. SPLIT: Raw video → 10-second segments using ffmpeg
   → Parallelizable: each segment processed independently

2. TRANSCODE: For each segment, generate ALL resolutions:
   → Worker 1: segment_001 → [360p, 480p, 720p, 1080p, 4K]
   → Worker 2: segment_002 → [360p, 480p, 720p, 1080p, 4K]
   → Worker N: segment_N → [360p, 480p, 720p, 1080p, 4K]

3. ADDITIONAL PROCESSING (parallel):
   → Audio extraction and transcoding
   → Thumbnail generation (extract keyframes)
   → Transcript generation (speech-to-text)
   → Content moderation (detect inappropriate content)

4. MANIFEST GENERATION:
   → Create master manifest + media manifests per resolution
   → Store all in S3

5. UPDATE METADATA:
   → Video status: "processing" → "ready"
   → Upload manifests and segments to CDN
   → Notify user: "Your video is ready!"
```

### Parallel Speedup
```
60-minute video:
  360 segments × 5 resolutions = 1,800 transcoding tasks
  
  Sequential (1 worker): ~24 hours
  Parallel (100 workers): ~15 minutes
  
Tool: Temporal workflow orchestrator for DAG execution
  → Automatic retries on failed tasks
  → Progress tracking
  → Crash recovery (resume from failed segment)
```

---

## 8. Deep Dive 4: Resumable Uploads

Same pattern as Dropbox (the video references this):

```
1. Client chunks video into 5-10MB parts
2. Compute fingerprint for each chunk
3. POST to backend → get presigned URLs per chunk
4. Upload chunks to S3 in parallel
5. On success → PATCH backend with chunk status + S3 ETag
6. Backend verifies via S3 ListParts API
7. When all chunks uploaded → call S3 CompleteMultipartUpload
8. S3 emits ObjectCreated event → triggers processing pipeline

Resume: If upload interrupted → client fetches existing chunk statuses
        → Resumes from first un-uploaded chunk
```

---

## 9. Deep Dive 5: Scaling to Billions of Daily Views

```
Component-by-component:

1. Video Service (stateless)
   → Horizontally scale + load balancer
   → Handles metadata queries and presigned URL generation

2. Video Metadata DB (Cassandra)
   → Partitioned by videoId → uniform distribution
   → Leaderless replication → handles hot videos
   → Watch out: viral video = hot partition → may need caching

3. Video Processing Service
   → Internal queueing (Kafka/SQS) for burst handling
   → Auto-scale workers based on queue depth
   → Elastic: scale up during peak upload times

4. S3 (Object Storage)
   → Virtually unlimited scaling within a region
   → Cross-region replication for global access
   → S3 Transfer Acceleration for faster uploads

5. CDN (CloudFront/Akamai)
   → Edge-cached segments globally
   → Popular videos: push-based replication to all edges
   → Long-tail: pull-based (cache on first access)
   → Cache hit ratio target: >95% for hot content
   → This is where the REAL scaling happens for reads
```

---

## 10. What is Expected at Each Level?

### Mid-Level
- Upload to S3, store metadata, serve videos
- Understand why you need transcoding for different devices

### Senior
- Segmented video with adaptive bitrate (HLS/DASH)
- CDN for global distribution
- Chunked/resumable uploads with S3 multipart
- Video processing pipeline concept

### Staff+
- DAG-based orchestration with Temporal
- Parallel transcoding across workers
- CDN push vs pull strategies
- Back-of-envelope: storage growth, bandwidth costs
- Content moderation in the processing pipeline
- S3 Transfer Acceleration for global uploaders

---

## 11. Interview Tips & Common Questions

### Q: Why not stream directly from S3?
> S3 is not geo-distributed. A user in Tokyo streaming from US-East S3 = 200ms+ latency per segment request. CDN edge nodes serve from the closest geographic location. S3 is the origin; CDN is the delivery layer.

### Q: How do you handle a video going viral?
> CDN absorbs the traffic. Hot videos are replicated across ALL edge nodes. Origin (S3) is hit only on CDN cache misses. Monitor CDN cache hit ratio — if it drops, pre-warm the cache.

### Q: What codec should you recommend?
> H.264: most compatible, every device supports it. VP9: better compression, used by YouTube. AV1: best compression, gaining support. Trade-off: newer codecs = better compression but slower encoding. Start with H.264, add VP9/AV1 for bandwidth savings.

### Q: How do you handle duplicated video uploads?
> Compute fingerprint of the raw video. If fingerprint matches an existing video → deduplicate storage. Flag for review (copyright detection). YouTube uses Content ID system for this.

---

*Documentation from: [System Design Walkthroughs Playlist](https://www.youtube.com/playlist?list=PL5q3E8eRUieWtYLmRU3z94-vGRcwKr9tM)*
