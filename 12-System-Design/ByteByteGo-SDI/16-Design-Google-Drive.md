# Chapter 16: Design Google Drive

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-google-drive)

In this chapter, you are asked to design Google Drive. Google Drive is a file storage and synchronization service that helps you store documents, photos, videos, and other files in the cloud. You can access your files from any computer, smartphone, and tablet.

---

## Step 1 - Understand the problem and establish design scope

**Candidate**: What are the most important features?
**Interviewer**: Upload and download files, file sync, and notifications.

**Candidate**: Is this a mobile app, a web app, or both?
**Interviewer**: Both.

**Candidate**: What are the supported file formats?
**Interviewer**: Any file type.

**Candidate**: Do files need to be encrypted?
**Interviewer**: Yes, files in the storage must be encrypted.

**Candidate**: Is there a file size limit?
**Interviewer**: Yes, files must be 10 GB or smaller.

**Candidate**: How many users does the product have?
**Interviewer**: 10M DAU.

**Focus features:**
- Add files (drag and drop)
- Download files
- Sync files across multiple devices
- See file revisions
- Share files
- Send notifications when a file is edited, deleted, or shared

**Non-functional requirements:**
- **Reliability**: Data loss is unacceptable.
- **Fast sync speed**: Slow sync drives users away.
- **Bandwidth usage**: Minimize unnecessary network traffic.
- **Scalability**: Handle high volumes of traffic.
- **High availability**: Stay usable even with server outages.

**Back of the envelope estimation:**
- 50 million signed up users, 10 million DAU
- Users get 10 GB free space → Total: 500 Petabyte
- Users upload 2 files/day, avg file size 500 KB
- QPS for upload API: ~240; Peak QPS: 480

---

## Step 2 - Propose high-level design and get buy-in

### Starting with a single server

Simple setup: Apache web server, MySQL database, `drive/` directory as root. Namespace per user, file identified by `namespace + relative path`.

### APIs

**1. Upload a file to Google Drive**

```
POST https://api.example.com/files/upload?uploadType=resumable

Simple upload: for small files
Resumable upload: for large files (3 steps: get URL, upload, resume if interrupted)
```

**2. Download a file from Google Drive**
```
GET https://api.example.com/files/download
Params: path: download file path
```

**3. Get file revisions**
```
GET https://api.example.com/files/list_revisions
Params: path, limit
```

All APIs require user authentication and use HTTPS.

### Moving away from single server

When storage fills up → shard data, then migrate to Amazon S3 (industry-leading scalability, data availability, security).

S3 supports same-region and cross-region replication. Files replicated across multiple regions to prevent data loss.

Improvements:
- **Load balancer**: Ensures evenly distributed traffic, failover.
- **Web servers**: Add/remove based on traffic load.
- **Metadata database**: Out of server to avoid SPOF, with replication and sharding.
- **File storage**: Amazon S3 with replication in two separate geographical regions.

![Figure 7 – Updated Design](images/ch16/figure-7.png)

### Sync conflicts

When two users modify the same file at the same time:
- First version processed wins.
- Second user gets a sync conflict — presented with both copies.
- User can merge or override.

![Figure 8 – Sync Conflict](images/ch16/figure-8.png)

### High-level design

![Figure 10 – High-level Design](images/ch16/figure-10.png)

Key components:
- **User**: Browser or mobile app.
- **Block servers**: Split files into blocks, compress, encrypt, upload to cloud storage. Max block size: 4MB (Dropbox reference).
- **Cloud storage**: Files split into blocks stored here.
- **Cold storage**: For inactive data (files not accessed for months/years).
- **Load balancer**: Distributes requests among API servers.
- **API servers**: User authentication, managing profiles, updating file metadata.
- **Metadata database**: Stores metadata of users, files, blocks, versions.
- **Metadata cache**: Fast retrieval of frequently accessed metadata.
- **Notification service**: Publisher/subscriber system to inform clients of file changes.
- **Offline backup queue**: Stores info about changes for offline clients.

---

## Step 3 - Design deep dive

### Block servers

**Delta sync**: When a file is modified, only modified blocks are synced (using sync algorithm). Reduces network bandwidth.

**Compression**: Apply compression algorithms based on file type (gzip/bzip2 for text; different for images/videos).

![Figure 11 – Block Server](images/ch16/figure-11.png)

Steps for new file:
1. File is split into smaller blocks.
2. Each block is compressed.
3. Each block is encrypted before sending.
4. Blocks are uploaded to cloud storage.

![Figure 12 – Delta Sync](images/ch16/figure-12.png)

Only modified blocks ("block 2" and "block 5") are transferred.

### High consistency requirement

Strong consistency required by default — unacceptable for a file to show differently across clients.

- Memory caches use eventual consistency by default → must programmatically enforce strong consistency.
- Invalidate caches on database write.
- We choose **relational databases** because ACID is natively supported.

### Metadata database schema

![Figure 13 – Database Schema](images/ch16/figure-13.png)

| Table | Description |
|-------|-------------|
| User | Basic info: username, email, profile photo |
| Device | Device info, push_id for mobile notifications |
| Namespace | Root directory of a user |
| File | Everything about the latest file |
| File_version | Version history (read-only rows for integrity) |
| Block | File block data. File reconstructed by joining all blocks in correct order |

### Upload flow

Two parallel requests:
1. Add file metadata → set status to "pending" → notify notification service
2. Upload to block servers → chunk/compress/encrypt → upload to cloud → callback to API servers → status changes to "uploaded" → notify notification service

![Figure 14 – Upload Flow](images/ch16/figure-14.png)

### Download flow

Triggered when a file is added or edited elsewhere.

1. Notification service informs client of changes.
2. Client requests metadata via API servers.
3. API servers fetch metadata from DB.
4. Client downloads blocks from block servers.
5. Block servers get blocks from cloud storage.
6. Client reconstructs file.

![Figure 15 – Download Flow](images/ch16/figure-15.png)

### Notification service

To reduce conflicts, any local file mutation must be informed to other clients.

Options:
- **Long polling**: Dropbox uses this. Client holds connection open until changes detected.
- **WebSocket**: Bi-directional persistent connection.

**Why long polling over WebSocket**: Notification service communication is not bi-directional. Notifications are infrequent with no burst of data. WebSocket suited for real-time chat apps.

### Save storage space

Techniques to reduce storage costs:
1. **De-duplicate data blocks**: Same hash value = identical blocks.
2. **Intelligent data backup strategy**:
   - Set a limit on number of versions to store.
   - Keep valuable versions only.
3. **Move infrequently used data to cold storage**: Amazon S3 Glacier — much cheaper than S3.

### Failure Handling

| Component | Failure Handling |
|-----------|-----------------|
| Load balancer | Secondary becomes active; heartbeat monitoring |
| Block server | Other servers pick up unfinished jobs |
| Cloud storage | Replicated across regions; fetch from different region |
| API server | Stateless; redirect to other servers |
| Metadata cache | Replicated; bring up new cache server |
| Metadata DB Master | Promote slave to master |
| Metadata DB Slave | Use another slave; bring up replacement |
| Notification service | Clients must reconnect to different server |
| Offline backup queue | Consumers re-subscribe to backup queue |

### Java Example – File Sync Service

```java
import java.util.*;
import java.security.MessageDigest;

public class FileSyncService {

    record FileBlock(int blockIndex, byte[] data, String hash) {}
    record FileVersion(String fileId, int version, List<FileBlock> blocks) {}

    private final Map<String, List<FileVersion>> versionHistory = new HashMap<>();
    private final Map<String, byte[]> blockStorage = new HashMap<>();

    public String computeHash(byte[] data) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(data);
            return HexFormat.of().formatHex(hash).substring(0, 16);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public void uploadFile(String fileId, byte[][] chunks) {
        List<FileBlock> blocks = new ArrayList<>();
        for (int i = 0; i < chunks.length; i++) {
            String hash = computeHash(chunks[i]);
            if (!blockStorage.containsKey(hash)) {
                blockStorage.put(hash, chunks[i]); // de-duplication
                System.out.println("Stored new block " + i + " [hash:" + hash + "]");
            } else {
                System.out.println("Block " + i + " already exists (dedup): " + hash);
            }
            blocks.add(new FileBlock(i, chunks[i], hash));
        }
        int version = versionHistory.getOrDefault(fileId, List.of()).size() + 1;
        versionHistory.computeIfAbsent(fileId, k -> new ArrayList<>())
                      .add(new FileVersion(fileId, version, blocks));
        System.out.println("File " + fileId + " uploaded. Version: " + version);
    }

    public List<FileVersion> getVersionHistory(String fileId) {
        return versionHistory.getOrDefault(fileId, List.of());
    }

    public static void main(String[] args) {
        FileSyncService service = new FileSyncService();

        byte[][] v1 = { "Block1Data".getBytes(), "Block2Data".getBytes() };
        byte[][] v2 = { "Block1Data".getBytes(), "Block2DataModified".getBytes() }; // delta

        service.uploadFile("doc123", v1);
        service.uploadFile("doc123", v2); // block1 deduped, block2 new

        System.out.println("\nVersion history for doc123:");
        service.getVersionHistory("doc123").forEach(v ->
            System.out.println("  Version " + v.version() + ": " + v.blocks().size() + " blocks")
        );
    }
}
```

---

## Step 4 - Wrap up

We proposed a system supporting: strong consistency, low network bandwidth (delta sync), and fast sync.

Two key flows: **manage file metadata** and **file sync**. Notification service uses long polling to keep clients up to date.

Alternative approach: upload directly to cloud storage from client (avoids block servers). Drawback: encoding/encryption logic must be on each platform (iOS, Android, Web) — error-prone.

Another evolution: move presence service out of notification servers for better extensibility.

---

## Reference materials

[1] Google Drive: https://www.google.com/drive/
[2] Upload file data: https://developers.google.com/drive/api/v2/manage-uploads
[3] Amazon S3: https://aws.amazon.com/s3
[4] Differential Synchronization: https://neil.fraser.name/writing/sync/
[5] How We've Scaled Dropbox: https://youtu.be/PE4gwstWhmc
[6] Tridgell, A., & Mackerras, P. (1996). The rsync algorithm.
[7] ACID: https://en.wikipedia.org/wiki/ACID
[8] Amazon S3 Glacier: https://aws.amazon.com/glacier/faqs/
