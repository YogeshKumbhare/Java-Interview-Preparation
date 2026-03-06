# 🔒 Advanced Security — Deep Dive (Theory + Code)
## Target: 12+ Years Experience

---

## 📖 What is Application Security?

Application security protects software applications from **threats and vulnerabilities**. For a senior Java developer, this means understanding OWASP Top 10, implementing defense-in-depth, and designing systems that are **secure by default**.

### OWASP Top 10 (2021):
```
1. Broken Access Control — users access things they shouldn't
2. Cryptographic Failures — weak encryption, exposed secrets
3. Injection (SQL, NoSQL, OS) — untrusted input interpreted as code
4. Insecure Design — fundamental design flaws
5. Security Misconfiguration — default passwords, open endpoints
6. Vulnerable Components — outdated libraries with known CVEs
7. Authentication Failures — weak login, no MFA
8. Data Integrity Failures — untrusted deserialization, unsigned updates
9. Logging Failures — not logging security events
10. SSRF — server-side request forgery
```

---

## 📖 SQL Injection — The #1 Classic Attack

### Theory:
SQL injection occurs when **untrusted user input** is directly embedded into a SQL query string, allowing attackers to **modify the query** and access, modify, or delete data.

```java
// ❌ VULNERABLE — String concatenation in SQL
public User findUser(String username) {
    String query = "SELECT * FROM users WHERE username = '" + username + "'";
    // If username = "admin' OR '1'='1" →
    // Query becomes: SELECT * FROM users WHERE username = 'admin' OR '1'='1'
    // Returns ALL users! Attacker bypasses authentication.

    // Even worse: username = "'; DROP TABLE users; --"
    // Query: SELECT * FROM users WHERE username = ''; DROP TABLE users; --'
    // Deletes entire table!
    return jdbcTemplate.queryForObject(query, userMapper);
}

// ✅ SECURE — Parameterized queries (PreparedStatement)
public User findUser(String username) {
    String query = "SELECT * FROM users WHERE username = ?";
    return jdbcTemplate.queryForObject(query, userMapper, username);
    // The ? placeholder NEVER interprets input as SQL
    // Input "admin' OR '1'='1" is treated as a literal string
}

// ✅ SECURE — JPA/Hibernate (parameterized by default)
@Query("SELECT u FROM User u WHERE u.username = :username")
Optional<User> findByUsername(@Param("username") String username);

// ❌ STILL VULNERABLE — JPQL with string concatenation
@Query("SELECT u FROM User u WHERE u.username = '" + username + "'")  // DON'T!
```

---

## 📖 Cross-Site Scripting (XSS)

### Theory:
XSS allows attackers to inject **malicious JavaScript** into web pages viewed by other users. The script runs in the victim's browser with the victim's session/cookies.

```
Types:
1. Stored XSS: Malicious script saved in DB (e.g., in a comment)
2. Reflected XSS: Script in URL parameter reflected in response
3. DOM XSS: Client-side JavaScript manipulates DOM with untrusted input
```

### Prevention in Spring Boot:
```java
// Spring Security automatically sets these headers:
// X-XSS-Protection: 1; mode=block
// X-Content-Type-Options: nosniff
// Content-Security-Policy: script-src 'self'

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .headers(headers -> headers
                .contentSecurityPolicy(csp -> csp
                    .policyDirectives("script-src 'self'; object-src 'none'; style-src 'self'"))
                .frameOptions(fo -> fo.deny())  // Prevent clickjacking
                .httpStrictTransportSecurity(hsts -> hsts
                    .includeSubDomains(true)
                    .maxAgeInSeconds(31536000)) // Force HTTPS for 1 year
            )
            .build();
    }
}

// Input sanitization
public class InputSanitizer {
    public static String sanitize(String input) {
        if (input == null) return null;
        return input
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll("\"", "&quot;")
            .replaceAll("'", "&#x27;")
            .replaceAll("/", "&#x2F;");
    }
}
```

---

## 📖 CSRF — Cross-Site Request Forgery

### Theory:
CSRF tricks an authenticated user's browser into sending **unwanted requests** to a site where they're already logged in. The browser automatically includes cookies (session), so the server thinks it's a legitimate request.

```
Attack scenario:
1. User logs into bank.com (browser stores session cookie)
2. User visits evil-site.com
3. evil-site.com has: <img src="https://bank.com/transfer?to=hacker&amount=10000">
4. Browser sends request to bank.com with session cookie → transfer happens!
```

### Prevention:
```java
// Spring Security enables CSRF protection by DEFAULT for form-based apps
// For REST APIs (stateless JWT), CSRF is typically DISABLED because
// there are no cookies to exploit

@Configuration
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            // Stateless APIs with JWT → disable CSRF
            .csrf(csrf -> csrf.disable())
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))

            // OR: For traditional web apps → use CSRF token
            // .csrf(csrf -> csrf
            //     .csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse())
            //     .ignoringRequestMatchers("/api/webhooks/**") // Exclude webhooks
            // )
            .build();
    }
}
```

---

## 📖 CORS — Cross-Origin Resource Sharing

### Theory:
**CORS** is a security mechanism that controls which **domains** can access your API. By default, browsers block requests from a different origin (domain/port/protocol) than the server.

```java
// Spring Boot CORS Configuration
@Configuration
public class CorsConfig {

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of(
            "https://www.mycompany.com",
            "https://admin.mycompany.com"
        ));
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE", "PATCH"));
        config.setAllowedHeaders(List.of("Authorization", "Content-Type", "X-Trace-Id"));
        config.setExposedHeaders(List.of("X-Request-Id"));
        config.setAllowCredentials(true);
        config.setMaxAge(3600L); // Browser caches CORS response for 1 hour

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return source;
    }
}

// Controller-level CORS (fine-grained)
@RestController
@CrossOrigin(origins = "https://frontend.mycompany.com", maxAge = 3600)
public class PaymentController { /* ... */ }
```

---

## 📖 JWT Security — Token-Based Authentication

### Theory:
**JWT (JSON Web Token)** is a compact, URL-safe token for securely transmitting claims between parties. It consists of three parts: Header.Payload.Signature

```
Header:     {"alg": "RS256", "typ": "JWT"}
Payload:    {"sub": "user123", "role": "ADMIN", "exp": 1700000000}
Signature:  RSASHA256(base64(header) + "." + base64(payload), privateKey)

Token: eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIn0.signature_here
```

### Secure JWT Implementation:
```java
@Service
public class JwtService {

    @Value("${jwt.secret}")
    private String secret;

    private static final long ACCESS_TOKEN_EXPIRY = 15 * 60 * 1000;    // 15 minutes
    private static final long REFRESH_TOKEN_EXPIRY = 7 * 24 * 3600000; // 7 days

    public String generateAccessToken(UserDetails user) {
        return Jwts.builder()
            .setSubject(user.getUsername())
            .claim("roles", user.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList()))
            .setIssuedAt(new Date())
            .setExpiration(new Date(System.currentTimeMillis() + ACCESS_TOKEN_EXPIRY))
            .setIssuer("payment-service")
            .signWith(getSigningKey(), SignatureAlgorithm.HS256)
            .compact();
    }

    public Claims validateAndExtract(String token) {
        try {
            return Jwts.parserBuilder()
                .setSigningKey(getSigningKey())
                .requireIssuer("payment-service") // Verify issuer
                .build()
                .parseClaimsJws(token)
                .getBody();
        } catch (ExpiredJwtException ex) {
            throw new TokenExpiredException("Token expired", ex);
        } catch (JwtException ex) {
            throw new InvalidTokenException("Invalid token", ex);
        }
    }

    private Key getSigningKey() {
        return Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret));
    }
}
```

---

## 📖 Zero Trust Architecture

### Theory:
**Zero Trust** = "Never trust, always verify." Unlike traditional security (trust everything inside the network), Zero Trust assumes the network is **already compromised**.

```
Traditional (Castle & Moat):
  Firewall → Inside network = trusted
  Problem: If attacker gets inside → they have full access

Zero Trust:
  Every request must be authenticated and authorized
  Even internal service-to-service calls need credentials
  Least privilege: give minimum required access
  Continuous verification: don't just check at login

Implementation in Microservices:
1. Service-to-service mTLS (mutual TLS)
2. OAuth2 Client Credentials for internal APIs
3. Network policies (only allow specific service connections)
4. Short-lived tokens (15-min JWTs, not session cookies)
5. Secrets management (Vault, AWS Secrets Manager)
```

### Spring Boot Secret Management:
```java
// ❌ NEVER: Hardcode secrets
private String apiKey = "sk_live_abc123";    // Leaked in Git!
// ❌ NEVER: Store in application.properties in Git
spring.datasource.password=production123     // Visible in repo!

// ✅ Environment Variables
spring.datasource.password=${DB_PASSWORD}    # Set at deployment time

// ✅ Vault Integration
@Configuration
public class VaultConfig {
    @Value("${vault.payment.api-key}")
    private String paymentApiKey; // Fetched from HashiCorp Vault at startup
}

// ✅ AWS Secrets Manager
@Bean
public DataSource dataSource() {
    String secret = secretsManagerClient.getSecretValue("prod/payment-db");
    // Parse JSON → extract password → configure DataSource
}
```

---

## Common Security Interview Questions:

### "How do you prevent brute force attacks on login?"
```java
// Rate limiting + account lockout
@Service
public class LoginService {
    private final Cache<String, AtomicInteger> failedAttempts =
        Caffeine.newBuilder().expireAfterWrite(30, TimeUnit.MINUTES).build();

    public AuthResponse login(LoginRequest req) {
        AtomicInteger attempts = failedAttempts.get(req.getUsername(),
            k -> new AtomicInteger(0));

        if (attempts.get() >= 5) {
            throw new AccountLockedException("Account locked for 30 minutes");
        }

        try {
            Authentication auth = authenticate(req); // Actual authentication
            failedAttempts.invalidate(req.getUsername()); // Reset on success
            return new AuthResponse(jwtService.generateToken(auth));
        } catch (BadCredentialsException ex) {
            attempts.incrementAndGet();
            log.warn("Failed login attempt {} for user {}",
                attempts.get(), req.getUsername());
            throw ex;
        }
    }
}
```

### "How do you store passwords securely?"
```java
// NEVER: Plain text, MD5, SHA-1
// ALWAYS: BCrypt (adaptive hashing, includes salt, configurable cost)
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder(12); // Cost factor 12 (2^12 iterations)
    // Each password has UNIQUE salt → same password = different hash
    // Increasing cost factor = exponentially slower → resistant to brute force
}

// Argon2 (even more secure — memory-hard)
@Bean
public PasswordEncoder passwordEncoder() {
    return new Argon2PasswordEncoder(16, 32, 1, 65536, 3);
}
```
