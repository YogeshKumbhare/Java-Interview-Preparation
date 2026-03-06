# 🚀 Advanced APIs (GraphQL & gRPC) — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 Introduction: Why look beyond REST?

REST APIs have dominated the backend landscape for over a decade. However, REST has two major limitations for complex, high-traffic modern systems:
1.  **Overfetching / Underfetching:** Clients often receive too much data (overfetching) or require multiple round-trips to different endpoints to load a single page (underfetching).
2.  **Performance & Payload Size:** JSON via HTTP/1.1 is text-based and bulky, which adds latency for microservice-to-microservice communication.

To solve this, we use **GraphQL** (for the Client-to-Server boundary) and **gRPC** (for Server-to-Server / Microservice-to-Microservice boundaries).

---

## 📖 What is GraphQL?

GraphQL is a query language and server-side runtime for APIs that prioritizes giving clients **exactly the data they request and nothing more.**

### 1. The N+1 Problem in GraphQL

The **most critical issue** in GraphQL performance is the N+1 problem.
If a client queries a `Post` and its `Author`, a naive implementation queries the database once for the Post (1 query), and then, for each of the 10 Posts returned, it queries the DB for the Author (N queries). Overall, 11 queries instead of an efficient JOIN.

### 2. Solving N+1 with `DataLoader`
A DataLoader batches and caches requests, converting N queries into 1 batch query using the `IN` clause (e.g., `SELECT * FROM authors WHERE id IN (1, 2, 3)`).

### Spring Boot GraphQL Implementation

```java
// Schema Declaration (src/main/resources/graphql/schema.graphqls)
type Query {
    postById(id: ID!): Post
    recentPosts: [Post!]!
}

type Post {
    id: ID!
    title: String!
    content: String!
    author: Author!  # Complex relationship
}

type Author {
    id: ID!
    name: String!
}

// Controller Implementation
@Controller
public class PostGraphController {
    private final PostRepository postRepo;

    public PostGraphController(PostRepository postRepo) {
        this.postRepo = postRepo;
    }

    // Maps to type Query -> recentPosts
    @QueryMapping
    public List<Post> recentPosts() {
        return postRepo.findTop10ByOrderByCreatedAtDesc(); // DB Query 1
    }

    // Resolves the "author" field for the Post type
    // ⚠️ Without @BatchMapping, this causes the N+1 problem!
    @BatchMapping(typeName = "Post", field = "author")
    public Map<Post, Author> author(List<Post> posts, AuthorRepository authorRepo) {
        // Collect all author IDs from the posts list
        List<Long> authorIds = posts.stream().map(Post::getAuthorId).toList();
        
        // Single DB Query (Batching) using IN clause
        List<Author> authors = authorRepo.findAllById(authorIds);
        
        // Map the Author back to the Post object for the GraphQL engine
        return posts.stream().collect(Collectors.toMap(
            post -> post,
            post -> authors.stream()
                .filter(a -> a.getId().equals(post.getAuthorId()))
                .findFirst().orElseThrow()
        ));
    }
}
```

---

## 📖 What is gRPC?

gRPC (gRPC Remote Procedure Calls) is an open-source, high-performance RPC framework developed by Google.

### Why gRPC beats REST for Microservices:
1.  **Protocol Buffers (Protobufs):** Instead of bulky JSON text, data is serialized into highly compressed **binary format**. It's smaller and faster to parse.
2.  **HTTP/2 native:** Uses multiplexing (multiple parallel requests over a single TCP connection), header compression, and bi-directional streaming.
3.  **Strongly typed Contracts:** The `.proto` file strictly defines the API contract. Clients in any language (Java, Go, Python) auto-generate the client/server stubs. No need for Swagger or OpenAPI.

### Implementing gRPC in Java

#### Step 1: Define the Contract (`payment.proto`)
```protobuf
syntax = "proto3";
package payment;
option java_multiple_files = true;
option java_package = "com.company.payment.grpc";

// The service interface
service PaymentService {
  // Unary RPC (similar to a standard REST call)
  rpc ProcessPayment (PaymentRequest) returns (PaymentResponse);
  
  // Streaming RPC (Client streams data, server responds once)
  rpc BatchPayments (stream PaymentRequest) returns (BatchResponse);
}

// The request message
message PaymentRequest {
  string order_id = 1;
  double amount = 2;
  string currency = 3;
}

// The response message
message PaymentResponse {
  string transaction_id = 1;
  string status = 2;
  string error_message = 3; // optional
}

message BatchResponse {
  int32 total_processed = 1;
  int32 total_failed = 2;
}
```

#### Step 2: Implement the gRPC Server (Spring Boot)

```java
import io.grpc.stub.StreamObserver;
import net.devh.boot.grpc.server.service.GrpcService;

@GrpcService // Exposes the service on the gRPC port (default 9090)
public class PaymentGrpcServiceImpl extends PaymentServiceGrpc.PaymentServiceImplBase {

    private final PaymentProcessor processor;

    public PaymentGrpcServiceImpl(PaymentProcessor processor) {
        this.processor = processor;
    }

    @Override
    public void processPayment(PaymentRequest request, StreamObserver<PaymentResponse> responseObserver) {
        
        // 1. Process business logic
        PaymentResult result = processor.charge(request.getOrderId(), request.getAmount());
        
        // 2. Build the protobuf response message
        PaymentResponse response = PaymentResponse.newBuilder()
            .setTransactionId(result.getTxId())
            .setStatus(result.isSuccess() ? "SUCCESS" : "FAILED")
            .build();
            
        // 3. Send the response back to client
        responseObserver.onNext(response);
        
        // 4. Mark the HTTP/2 stream as complete
        responseObserver.onCompleted(); 
    }
}
```

---

## Common Interview Questions (Cross-Questioning)

### Q: "If gRPC is so much faster than REST, why don't we use it for our frontend web application instead of REST or GraphQL?"
**Answer:**
*   "Browsers cannot natively speak raw HTTP/2 framing, which gRPC deeply requires. A browser Javascript client cannot directly establish a gRPC connection without a proxy."
*   "We would have to use `gRPC-Web`, which requires a specialized Envoy proxy layer to translate HTTP/1.1 REST to gRPC. This adds unnecessary architectural complexity."
*   "The standard industry pattern is: GraphQL (or REST) for the external Frontend-to-Backend boundary (for flexibility and caching), and gRPC strictly for internal Backend-to-Backend microservice communication (for speed and low payload size)."

### Q: "GraphQL allows users to build dynamic queries. How do you prevent a malicious user from requesting a deeply nested query that crashes the database?"
**Example Malicious Query:**
```graphql
query { author { posts { comments { author { posts { ... } } } } } }
```
**Answer:**
*   "We must implement **Query Depth Limiting** (e.g., maximum depth of 5 nested objects)."
*   "We also enforce **Query Complexity Analysis**. Each field is assigned a cost (e.g., grabbing a String field = 1, fetching an array of Posts = 10, fetching nested Authors = 20). If the calculated complexity score exceeds a threshold (e.g., > 100), the GraphQL server rejects the request immediately."
*   "Finally, we implement strict hard limits using timeouts and rate limiters on the API Gateway."

### Q: "How do you handle load balancing a gRPC cluster on Kubernetes?"
**Answer:**
*   "Standard HTTP/1.1 load balancing (Layer 4 TCP load balancing) fails with gRPC. Because gRPC uses a single, long-lived HTTP/2 TCP connection (multiplexing), a standard Kubernetes `Service` will route the connection to *a single pod*, and all subsequent gRPC calls will stick to that one pod forever, causing an unbalanced load."
*   "To fix this, we must use **Layer 7 (Application) Load Balancing**. We implement proxy meshes like **Envoy, Linkerd, or an NGINX Ingress Controller** configured specifically for `grpc-backend`. These tools understand HTTP/2 frames and will round-robin the *individual requests within the stream* across all available pods, even over a single TCP connection."
