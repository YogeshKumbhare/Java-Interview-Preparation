# Chapter 16: Design Google Drive

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/design-google-drive)

Design a file storage and synchronization service like Google Drive, Dropbox, or OneDrive.

---

## Step 1 - Understand the problem and establish design scope

**Features:** Upload/download files, file sync across devices, see file revisions, share files, send notifications on file edits.

**Requirements:** 50 million signed up users, 10 million DAU, 10 GB free space per user, File size limit: 10 GB, Mobile + web support, High reliability, fast sync, low bandwidth.

**Estimations:** Average user has 500 files → total files = 50M * 500 = 25 billion; Storage = 50M * 10 GB = 500 PB.

---

## Step 2 - High-level design

### APIs

1. **Upload file**: `POST /files/upload` — supports simple and resumable uploads
2. **Download file**: `GET /files/download` — params: path
3. **Get file revisions**: `GET /files/list_revisions` — params: path, limit

### Architecture components

- **Block servers**: Split files into blocks, compress, encrypt, and upload to cloud storage. Only modified blocks are transferred (delta sync).
- **Cloud storage (S3)**: Store file blocks
- **Cold storage**: For inactive data
- **Load balancer**: Distribute requests
- **API servers**: Authentication, user profile, file metadata
- **Metadata database**: Stores user, file, block, version info
- **Metadata cache**: Cache frequently accessed metadata
- **Notification service**: Notify clients when files change (long polling / WebSocket)
- **Offline backup queue**: Store changes when client is offline

### Java Example – Block-level File Sync

```java
import java.security.MessageDigest;
import java.util.*;

public class BlockLevelSync {
    private static final int BLOCK_SIZE = 4 * 1024 * 1024; // 4 MB blocks
    
    record Block(int index, String hash, byte[] data) {}
    
    // Simulate cloud storage
    private final Map<String, byte[]> cloudStorage = new HashMap<>();
    
    public List<Block> splitIntoBlocks(byte[] fileData) {
        List<Block> blocks = new ArrayList<>();
        for (int i = 0; i < fileData.length; i += BLOCK_SIZE) {
            int end = Math.min(i + BLOCK_SIZE, fileData.length);
            byte[] blockData = Arrays.copyOfRange(fileData, i, end);
            String hash = computeHash(blockData);
            blocks.add(new Block(i / BLOCK_SIZE, hash, blockData));
        }
        return blocks;
    }
    
    public int syncFile(String fileId, byte[] newFileData) {
        List<Block> newBlocks = splitIntoBlocks(newFileData);
        int blocksUploaded = 0;
        
        for (Block block : newBlocks) {
            String key = fileId + "_block_" + block.index();
            String existingHash = cloudStorage.containsKey(key) ? 
                computeHash(cloudStorage.get(key)) : null;
            
            if (!block.hash().equals(existingHash)) {
                cloudStorage.put(key, block.data());
                blocksUploaded++;
                System.out.printf("  ↑ Uploaded block %d (hash: %s)%n", 
                    block.index(), block.hash().substring(0, 8));
            } else {
                System.out.printf("  ✓ Block %d unchanged, skipping%n", block.index());
            }
        }
        return blocksUploaded;
    }
    
    private String computeHash(byte[] data) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] hash = md.digest(data);
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) { throw new RuntimeException(e); }
    }
    
    public static void main(String[] args) {
        BlockLevelSync sync = new BlockLevelSync();
        
        // Initial upload
        byte[] fileV1 = new byte[10 * 1024 * 1024]; // 10 MB
        Arrays.fill(fileV1, (byte) 'A');
        System.out.println("=== Initial Upload ===");
        int uploaded = sync.syncFile("doc_001", fileV1);
        System.out.println("Blocks uploaded: " + uploaded);
        
        // Modify last 2 MB only (delta sync)
        byte[] fileV2 = fileV1.clone();
        Arrays.fill(fileV2, 8 * 1024 * 1024, 10 * 1024 * 1024, (byte) 'B');
        System.out.println("\n=== Delta Sync (modified last 2MB) ===");
        uploaded = sync.syncFile("doc_001", fileV2);
        System.out.println("Blocks uploaded: " + uploaded + " (only changed blocks!)");
    }
}
```

---

## Step 3 - Design deep dive

### Block servers
- **Delta sync**: Only upload modified blocks, not the full file
- **Compression**: Compress blocks using gzip/bzip2 to save bandwidth and storage

### Conflict resolution
When two users edit the same file:
- First version processed wins
- Second version is saved as a conflict copy
- User must resolve conflicts manually

### Metadata database
- Use a relational database (MySQL) for structured metadata
- Tables: user, device, workspace, file, file_version, block

### Upload flow
1. File split into blocks
2. Each block compressed and encrypted
3. Blocks uploaded to cloud storage
4. Metadata updated in Metadata DB
5. Notification sent to sync clients

### Download flow
1. Client notified of file change
2. Request metadata for new file version
3. Download only changed blocks
4. Reconstruct file from blocks

---

## Step 4 - Wrap up

Additional talking points:
- **Handling read/write conflicts across devices**
- **Encryption at rest and in transit**
- **File versioning and revision history**
- **Data deduplication across users**
