# Chapter 15: Design YouTube

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-youtube)

YouTube is the most popular video sharing platform. Design a system like YouTube/Netflix/Vimeo.

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: What features are important?
**Interviewer**: Upload a video and watch a video.

**Candidate**: What clients do we need to support?
**Interviewer**: Mobile apps, web browsers, and smart TV.

**Candidate**: How many daily active users?
**Interviewer**: 5 million.

**Candidate**: Average daily time spent on the product?
**Interviewer**: 30 minutes.

**Candidate**: Need to support international users?
**Interviewer**: Yes, a large percentage of users are international.

**Candidate**: What are the supported video resolutions?
**Interviewer**: Accept most video resolutions and formats.

**Candidate**: Is encryption required?
**Interviewer**: Yes.

**Candidate**: File size limit?
**Interviewer**: Maximum 1GB.

**Back of the envelope estimation:**
- 5 million DAU
- 10% upload a video daily = 500K videos/day
- Average video size: 300 MB
- Daily storage: 500K * 300 MB = 150 TB/day
- CDN cost: at $0.02/GB → $150K/day for streaming

---

## Step 2 - High-level design

### System components

1. **Client**: Computer, mobile, smartTV
2. **CDN**: Videos are stored in CDN. When you press play, a video is streamed from CDN.
3. **API servers**: Everything else — feed recommendation, generating video upload URL, updating metadata, user signup, etc.

### Video uploading flow

1. User uploads video to Original Storage
2. Transcoding servers fetch video and convert to multiple formats/resolutions
3. Transcoded videos distributed to CDN
4. Completion handler updates Metadata DB
5. API servers inform user video is ready

### Video streaming flow

Streaming means your device continuously receives video streams from remote sources. Most popular streaming protocol: **MPEG-DASH**, **HLS** (Apple), **Microsoft Smooth Streaming**, **Adobe HDS**.

---

## Step 3 - Design deep dive

### Video transcoding

Reasons to encode videos:
- Raw video consumes large amounts of storage
- Many devices only support certain types of video formats
- Need multiple quality levels for network conditions
- Higher resolution = better quality but requires more bandwidth

**Directed Acyclic Graph (DAG) model for transcoding:**
- Video → split into audio and video
- Video tasks: inspection, encoding (360p, 480p, 720p, 1080p), thumbnail generation, watermark
- Audio tasks: encoding (AAC, MP3, etc.)

### System optimizations

#### Speed optimization
- **Parallelize video uploading**: Split video into smaller chunks (GOP alignment). Upload in parallel.
- **Place upload centers close to users**: Use CDN as upload centers.
- **Parallelism everywhere**: Build a loosely coupled system using message queues.

#### Safety optimization
- **Pre-signed upload URL**: Only authorized users can upload.
- **Protect videos**: DRM (Digital Rights Management), AES encryption, visual watermarking.

#### Cost-saving optimization
- Only serve popular videos from CDN; serve long tail from high-capacity storage servers
- Short videos can be encoded on-demand
- Some videos popular only in certain regions — no need to distribute to all CDN nodes
- Build your own CDN like Netflix

### Error handling

- **Recoverable error**: retry operation (e.g., transcoding failure → retry)
- **Non-recoverable error**: return proper error code (e.g., malformed video format)

### Java Example – Video Processing Pipeline

```java
import java.util.*;
import java.util.concurrent.*;

public class VideoProcessingPipeline {

    record VideoTask(String videoId, String resolution, String status) {}

    private final ExecutorService executor = Executors.newFixedThreadPool(4);
    private final Queue<VideoTask> completedTasks = new ConcurrentLinkedQueue<>();

    public void processVideo(String videoId) {
        String[] resolutions = {"360p", "480p", "720p", "1080p"};
        List<Future<?>> futures = new ArrayList<>();

        System.out.println("Starting transcoding for video: " + videoId);

        for (String res : resolutions) {
            futures.add(executor.submit(() -> {
                System.out.println("  Transcoding " + videoId + " → " + res);
                try { Thread.sleep(1000); } catch (InterruptedException e) {}
                completedTasks.add(new VideoTask(videoId, res, "DONE"));
                System.out.println("  ✅ Completed " + videoId + " → " + res);
            }));
        }

        // Wait for all transcodings
        for (Future<?> f : futures) {
            try { f.get(); } catch (Exception e) { e.printStackTrace(); }
        }

        System.out.println("All transcoding complete for: " + videoId);
        System.out.println("Pushing to CDN...");
    }

    public static void main(String[] args) {
        VideoProcessingPipeline pipeline = new VideoProcessingPipeline();
        pipeline.processVideo("vid_001");
        pipeline.executor.shutdown();
    }
}
```

---

## Step 4 - Wrap up

Additional talking points:
- **Live streaming**: Different latency requirements, different streaming protocols, smaller chunks
- **Video takedowns**: Videos violating copyrights/regulations need to be removed
- **Copyright**: YouTube uses ContentID to detect copyrighted material
