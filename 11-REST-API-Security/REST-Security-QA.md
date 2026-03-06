# 🔐 REST API Security — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is REST API Security?

**REST API Security** ensures that only **authorized users** can access your API endpoints, and the data transmitted is **confidential and tamper-proof**. Without proper security, your API is open to data breaches, unauthorized access, and abuse.

### Authentication vs Authorization:

```
Authentication (AuthN): WHO are you?
  → "I am user John with password xyz"
  → Verified by: JWT token, OAuth2, API Key, session

Authorization (AuthZ): WHAT can you do?
  → "John has ROLE_ADMIN, so he can delete users"
  → Verified by: Role-based (RBAC), Attribute-based (ABAC), Policy-based
```

---

## 📖 OAuth 2.0 — The Industry Standard

### Theory:
**OAuth 2.0** is an **authorization framework** that enables third-party applications to access resources on behalf of a user WITHOUT sharing their password.

### OAuth 2.0 Flows:
```
1. Authorization Code Flow (most secure, for web apps):
   User → redirected to Auth Server → logs in → gets auth code
   → App exchanges auth code for access token

2. Client Credentials Flow (machine-to-machine):
   Service A → sends client_id + client_secret to Auth Server
   → gets access token → calls Service B with token

3. PKCE Flow (for mobile/SPA — no client secret):
   Like Auth Code but with code_verifier/code_challenge
   Prevents auth code interception

4. Implicit Flow (DEPRECATED — don't use):
   Token returned directly in URL → security risk
```

### Authorization Code Flow Diagram:
```
User        Frontend       Auth Server     Backend API
  │             │                │              │
  ├──click login──→             │              │
  │             ├──redirect to──→│              │
  │             │              login page       │
  │             │◄──user logs in──┤              │
  │             │    auth code    │              │
  │             ├──exchange code──→│              │
  │             │◄──access_token──┤              │
  │             │  refresh_token  │              │
  │             ├──API call + Bearer token──────→│
  │             │◄──────────data───────────────┤│
```

### Spring Security OAuth2 + JWT:
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .authorizeHttpRequests(auth -> auth
                // Public endpoints
                .requestMatchers("/api/auth/**", "/actuator/health").permitAll()
                // Role-based access
                .requestMatchers(HttpMethod.GET, "/api/products/**").hasAnyRole("USER", "ADMIN")
                .requestMatchers(HttpMethod.POST, "/api/products/**").hasRole("ADMIN")
                .requestMatchers(HttpMethod.DELETE, "/api/**").hasRole("ADMIN")
                // Everything else requires authentication
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(ex -> ex
                .authenticationEntryPoint((req, res, authEx) -> {
                    res.setStatus(401);
                    res.getWriter().write("{\"error\":\"Unauthorized\"}");
                })
                .accessDeniedHandler((req, res, accessEx) -> {
                    res.setStatus(403);
                    res.getWriter().write("{\"error\":\"Access denied\"}");
                })
            )
            .build();
    }
}

// JWT Authentication Filter
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws IOException, ServletException {
        String header = request.getHeader("Authorization");

        if (header == null || !header.startsWith("Bearer ")) {
            chain.doFilter(request, response);
            return;
        }

        String token = header.substring(7);

        try {
            Claims claims = jwtService.validateAndExtract(token);
            String username = claims.getSubject();
            List<String> roles = claims.get("roles", List.class);

            UsernamePasswordAuthenticationToken auth =
                new UsernamePasswordAuthenticationToken(
                    username,
                    null,
                    roles.stream()
                        .map(SimpleGrantedAuthority::new)
                        .collect(Collectors.toList())
                );
            auth.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
            SecurityContextHolder.getContext().setAuthentication(auth);

        } catch (TokenExpiredException ex) {
            response.setStatus(HttpStatus.UNAUTHORIZED.value());
            response.getWriter().write("{\"error\":\"Token expired\"}");
            return;
        }

        chain.doFilter(request, response);
    }
}
```

---

## 📖 Method-Level Security

```java
@Service
@PreAuthorize("hasRole('ADMIN') or hasRole('MANAGER')")
public class UserManagementService {

    @PreAuthorize("hasRole('ADMIN')")
    public void deleteUser(String userId) {
        // Only ADMINs can delete users
    }

    @PreAuthorize("#userId == authentication.principal.username or hasRole('ADMIN')")
    public UserProfile getProfile(String userId) {
        // Users can see their own profile, ADMINs can see anyone's
    }

    @PostAuthorize("returnObject.owner == authentication.principal.username")
    public Document getDocument(String docId) {
        // Checks AFTER method execution — only return if user owns the document
    }
}
```

---

## 📖 API Rate Limiting

```java
@Component
public class RateLimitFilter extends OncePerRequestFilter {

    private final Cache<String, AtomicInteger> requestCounts =
        Caffeine.newBuilder()
            .expireAfterWrite(1, TimeUnit.MINUTES)
            .build();

    private static final int MAX_REQUESTS_PER_MINUTE = 100;

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain chain) throws IOException, ServletException {
        String clientId = extractClientIdentifier(request);
        AtomicInteger count = requestCounts.get(clientId, k -> new AtomicInteger(0));

        if (count.incrementAndGet() > MAX_REQUESTS_PER_MINUTE) {
            response.setStatus(429);
            response.setHeader("Retry-After", "60");
            response.getWriter().write("{\"error\":\"Rate limit exceeded\"}");
            return;
        }

        chain.doFilter(request, response);
    }

    private String extractClientIdentifier(HttpServletRequest request) {
        // Use JWT subject or API key or IP address
        String token = request.getHeader("Authorization");
        if (token != null) return jwtService.extractSubject(token);
        return request.getRemoteAddr();
    }
}
```

---

## 📖 API Versioning Strategies

```java
// Strategy 1: URL Path Versioning (most common)
@RestController
@RequestMapping("/api/v1/orders")
public class OrderControllerV1 {
    @GetMapping("/{id}")
    public OrderResponseV1 getOrder(@PathVariable String id) { /* v1 response */ }
}

@RestController
@RequestMapping("/api/v2/orders")
public class OrderControllerV2 {
    @GetMapping("/{id}")
    public OrderResponseV2 getOrder(@PathVariable String id) { /* v2 response with more fields */ }
}

// Strategy 2: Header Versioning
@GetMapping("/api/orders/{id}")
public ResponseEntity<?> getOrder(@PathVariable String id,
                                  @RequestHeader(value = "API-Version", defaultValue = "1") int version) {
    return switch (version) {
        case 1 -> ResponseEntity.ok(mapToV1(order));
        case 2 -> ResponseEntity.ok(mapToV2(order));
        default -> ResponseEntity.badRequest().body("Unsupported version");
    };
}

// Strategy 3: Content Negotiation
@GetMapping(value = "/api/orders/{id}", produces = "application/vnd.company.v2+json")
public OrderResponseV2 getOrderV2(@PathVariable String id) { /* v2 */ }
```

---

## Common Interview Questions:

### "How do you secure a microservices architecture?"
```
Layered security (Defense in Depth):

1. EDGE (API Gateway):
   - SSL/TLS termination
   - Rate limiting (per user/IP)
   - WAF (Web Application Firewall)
   - DDoS protection (AWS Shield, Cloudflare)

2. SERVICE-TO-SERVICE:
   - mTLS (mutual TLS) — both sides present certificates
   - OAuth2 Client Credentials flow
   - Service mesh (Istio) for automatic mTLS

3. APPLICATION:
   - JWT validation on every request
   - Role-based access control (RBAC)
   - Input validation (never trust user input)
   - SQL injection prevention (parameterized queries)

4. DATA:
   - Encryption at rest (AES-256)
   - Encryption in transit (TLS 1.3)
   - Database access control (least privilege)
   - PII masking in logs

5. INFRASTRUCTURE:
   - Network policies (K8s: only allow specific pod communication)
   - Secrets management (Vault, AWS Secrets Manager)
   - Container scanning (Snyk, Trivy)
   - Regular dependency updates (Dependabot)
```
