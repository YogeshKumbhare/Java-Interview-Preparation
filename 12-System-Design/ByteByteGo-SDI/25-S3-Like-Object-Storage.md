# Chapter 25: S3-like Object Storage

> Source: [ByteByteGo - System Design Interview](https://bytebytego.com/courses/system-design-interview/s3-like-object-storage)

Design an object storage service like Amazon S3, Google Cloud Storage, or Azure Blob Storage.

---

## Step 1 - Understand the problem and establish design scope

**Features:** Bucket creation, object upload/download, object versioning, list objects by prefix.

**Non-functional:** 100 PB of data, data durability 99.9999% (six 9s), availability 99.99%, low storage cost.

**Estimations:** 10B objects stored, average object size 0.5 MB, 20% object updates/year, IOPS much lower than block storage.

**Object storage vs other storage:**
| Storage | Access | Use case |
|---------|--------|----------|
| Block | Low-level device | Databases, VM disks |
| File | Hierarchical file/directory | Shared files |
| Object | Flat namespace + metadata | Images, videos, backups, logs |

---

## Step 2 - High-level design

### Core concepts

- **Bucket**: Logical container for objects (like a top-level directory)
- **Object**: The data blob + metadata, identified by key
- Flat structure: `s3://bucket-name/path/to/object.jpg` (path is part of the key, not a directory)

### API Design

- `PUT /bucket-name` — Create bucket
- `PUT /bucket-name/object-key` — Upload object
- `GET /bucket-name/object-key` — Download object
- `DELETE /bucket-name/object-key` — Delete object
- `GET /bucket-name?prefix=path/&delimiter=/` — List objects

### Architecture

1. **API Service**: Stateless, handles authentication, routing
2. **Metadata Store**: Store bucket/object metadata (name, size, ACL, version) — sharded SQL or distributed KV
3. **Data Store**: Actual data storage — distributed across data nodes with replication
4. **IAM / Auth**: Access control

### Java Example – Object Storage Service

```java
import java.util.*;
import java.util.concurrent.*;
import java.security.*;

public class ObjectStorageService {
    record ObjectMeta(String bucket, String key, long size, String etag,
                      int version, long createdAt) {}

    private final Map<String, Set<String>> buckets = new ConcurrentHashMap<>();
    private final Map<String, byte[]> dataStore = new ConcurrentHashMap<>();
    private final Map<String, ObjectMeta> metadataStore = new ConcurrentHashMap<>();
    private final Map<String, Integer> versionCounter = new ConcurrentHashMap<>();

    public void createBucket(String bucketName) {
        buckets.putIfAbsent(bucketName, ConcurrentHashMap.newKeySet());
        System.out.println("🪣 Bucket created: " + bucketName);
    }

    public String putObject(String bucket, String key, byte[] data) {
        String fullKey = bucket + "/" + key;
        int version = versionCounter.merge(fullKey, 1, Integer::sum);
        String etag = md5(data);

        dataStore.put(fullKey + ":v" + version, data);
        metadataStore.put(fullKey, new ObjectMeta(bucket, key, data.length,
                          etag, version, System.currentTimeMillis()));
        buckets.get(bucket).add(key);

        System.out.printf("⬆️ PUT %s (v%d, %d bytes, etag=%s)%n",
            fullKey, version, data.length, etag.substring(0, 8));
        return etag;
    }

    public byte[] getObject(String bucket, String key) {
        ObjectMeta meta = metadataStore.get(bucket + "/" + key);
        if (meta == null) return null;
        return dataStore.get(bucket + "/" + key + ":v" + meta.version());
    }

    public List<String> listObjects(String bucket, String prefix) {
        return buckets.getOrDefault(bucket, Set.of()).stream()
            .filter(k -> k.startsWith(prefix))
            .sorted()
            .toList();
    }

    private String md5(byte[] data) {
        try {
            byte[] hash = MessageDigest.getInstance("MD5").digest(data);
            StringBuilder sb = new StringBuilder();
            for (byte b : hash) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (Exception e) { throw new RuntimeException(e); }
    }

    public static void main(String[] args) {
        ObjectStorageService s3 = new ObjectStorageService();
        s3.createBucket("my-photos");
        s3.putObject("my-photos", "2024/march/photo1.jpg", "JPEG_DATA_1".getBytes());
        s3.putObject("my-photos", "2024/march/photo2.jpg", "JPEG_DATA_2".getBytes());
        s3.putObject("my-photos", "2024/april/photo3.jpg", "JPEG_DATA_3".getBytes());
        // Version update
        s3.putObject("my-photos", "2024/march/photo1.jpg", "UPDATED_JPEG".getBytes());

        System.out.println("\nObjects with prefix '2024/march/':");
        s3.listObjects("my-photos", "2024/march/").forEach(k -> System.out.println("  " + k));

        byte[] data = s3.getObject("my-photos", "2024/march/photo1.jpg");
        System.out.println("\nRetrieved: " + new String(data));
    }
}
```

---

## Step 3 - Design deep dive

### Data store internals
- Objects split into chunks, stored across multiple data nodes
- **Erasure coding** (e.g., Reed-Solomon 8+4): 8 data chunks + 4 parity → tolerates up to 4 node failures. More storage-efficient than 3x replication.

### Data durability
- Replication across data centers
- Checksum verification on read
- Background integrity verification

### Metadata design
- **Bucket table**: owner, region, ACL, created_at
- **Object table**: bucket_id, object_key, version_id, size, etag, storage_class
- Sharded by bucket_id for scalability

### Garbage collection
- Deleted objects marked as tombstone → background GC process removes after retention period
- Orphaned data chunks cleaned up periodically

### Storage classes
| Class | Access | Cost | Use Case |
|-------|--------|------|----------|
| Standard | Frequent | $$$ | Hot data |
| Infrequent Access | 1-2x/month | $$ | Backups |
| Glacier/Archive | Rare | $ | Compliance |

---

## Step 4 - Wrap up

Additional talking points:
- **Multipart upload for large files**
- **Pre-signed URLs for secure access**
- **Cross-region replication**
- **Lifecycle policies** (auto-transition between storage classes)
