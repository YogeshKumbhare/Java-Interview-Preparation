# 💻 Frontend Basics for Backend Devs (React/Angular)
## Target: 12+ Years Experience (Java Full Stack)

---

## 📖 Introduction: Why should a Backend Lead know Frontend?

As a Senior/Lead Full Stack Developer, you are expected to design end-to-end features. Even if you spend 80% of your time in Java/Spring Boot, you must understand how your APIs are consumed by Modern Frontend Frameworks (React, Angular, Vue).

You need to know how state is managed, how CORS works, how authentication tokens are stored securely in the browser, and the basic architecture of Single Page Applications (SPAs).

---

## 📖 Single Page Applications (SPA) Architecture

Traditional web apps (like JSP or Thymeleaf) render HTML on the server and send a fresh page for every click. This is slow and consumes backend computing power.

An **SPA** downloads a single HTML file and a large JavaScript bundle (React/Angular) on the first load. After that, it only sends JSON data back and forth via REST or GraphQL APIs. The rendering happens on the user's powerful device (Client-Side Rendering).

---

## 📖 React Basics (The most common frontend framework)

React is a JavaScript library for building user interfaces using **components**.

### 1. The Virtual DOM
React does not update the real browser DOM directly (which is slow). It maintains a lightweight copy in memory called the **Virtual DOM**. When data changes, React calculates the difference (diffing) between the old Virtual DOM and the new one, and updates ONLY the exact HTML nodes that changed in the real DOM (reconciliation).

### 2. Components, Props, and State
*   **Component:** A reusable piece of UI (like a Button, Navbar, or ProductCard).
*   **Props (Properties):** Read-only data passed from a parent component to a child component. (Like method arguments).
*   **State:** Mutable data maintained *inside* a component. When state changes, the component automatically re-renders.

### Code Example: A React Component fetching a Spring Boot API
```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios'; // HTTP client

function ProductList() {
    // State: [currentValue, setterFunction]
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);

    // useEffect runs side effects (like API calls) when the component mounts
    useEffect(() => {
        // Fetch data from backend
        axios.get('http://api.company.com/v1/products', {
            headers: { Authorization: `Bearer ${localStorage.getItem('jwt')}` }
        })
        .then(response => {
            setProducts(response.data); // Update state! Triggers re-render.
            setLoading(false);
        })
        .catch(error => {
            console.error("Error fetching products", error);
            setLoading(false);
        });
    }, []); // Empty array = run only once on load

    if (loading) return <div>Loading...</div>;

    return (
        <div className="product-grid">
            <h2>Available Products</h2>
            {/* Loop through state and render child components */}
            {products.map(product => (
                <ProductCard key={product.id} data={product} /> // Passing Props
            ))}
        </div>
    );
}
export default ProductList;
```

---

## 📖 Authentication & Security in the Browser

Backend developers generate JWTs, but frontend developers must store them. This is a crucial full-stack security topic.

### Where should the Frontend store the JWT?

#### 1. LocalStorage / SessionStorage
*   **How it works:** `localStorage.setItem('token', jwt)`
*   **Pros:** Very easy to use. Sent via the `Authorization: Bearer <token>` header in JS code.
*   **Cons (Security Risk):** Vulnerable to **Cross-Site Scripting (XSS)**. Any malicious JavaScript loaded on the page (from a bad third-party ad or a compromised NPM package) can instantly read LocalStorage and steal the token.

#### 2. HttpOnly Cookies (The Secure Way)
*   **How it works:** The Backend Spring Boot app sets a `Set-Cookie` header in the login response: `Set-Cookie: jwt=abc123token; HttpOnly; Secure; SameSite=Strict`.
*   **Pros:** The browser automatically attaches the cookie to every subsequent API request. **HttpOnly** means JavaScript *cannot* read the cookie. It is immune to XSS token theft!
*   **Cons:** Vulnerable to **CSRF (Cross-Site Request Forgery)**. If a user visits an evil site, the evil site can send a request to your API, and the browser will automatically attach the HttpOnly cookie.

#### Full-Stack Security Solution for SPAs
1.  Store the **JWT Access Token** in memory (a React variable) for extreme security, or LocalStorage if short-lived (e.g., 5 mins).
2.  Store a long-lived **Refresh Token** in an **HttpOnly Cookie**.
3.  Protect against CSRF by configuring Spring Security to expect an Anti-CSRF Token Header on all `POST/PUT/DELETE` requests.

---

## 📖 CORS (Cross-Origin Resource Sharing)

If a React app is running on `http://localhost:3000` and tries to call a Spring Boot API on `http://localhost:8080`, the browser will automatically BLOCK the request due to the **Same-Origin Policy**.

### The Preflight Request (OPTIONS)
Before sending the actual `GET` or `POST`, the browser sends an invisible `OPTIONS` request to the backend, asking for permission.

```http
OPTIONS /api/products HTTP/1.1
Origin: http://localhost:3000
Access-Control-Request-Method: GET
```

### The Spring Boot Backend Response
If permitted, the backend responds:

```http
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST
Access-Control-Allow-Headers: Authorization, Content-Type
```
After receiving this, the browser finally sends the real `GET` request.

---

## Common Interview Questions (Cross-Questioning)

### Q: "As a backend lead orchestrating an SPA refactor, should we do Server-Side Rendering (SSR) or Client-Side Rendering (CSR)?"
**Answer:**
*   "CSR (pure React SPA) is best for highly interactive dashboards, admin panels, and internal tools where initial load time is less critical than snappiness and rich interactions."
*   "SSR (Next.js, Thymeleaf) is mandatory if **SEO is critical** (like an e-commerce site). Web crawlers struggle to index pure CSR sites. SSR guarantees the crawler sees fully populated HTML, improving PageRank and Time-to-First-Byte metrics for users on slow connections."

### Q: "Our frontend team complains that fetching a list of users, their related posts, and the post comments requires 3 separate REST round-trips to your Spring Boot server, making the app slow. How do you solve this from the backend?"
**Answer:**
*   "The easiest immediate fix is implementing the **Backend-For-Frontend (BFF)** pattern. We create a specialized REST endpoint (`/api/v1/desktop-users-view`) that aggregates the 3 calls server-side and returns exactly one JSON object tailored for the UI."
*   "The robust, long-term solution is implementing **GraphQL**. This allows the React app to define its own data requirements via queries, resolving the underfetching issue natively."

### Q: "A user is complaining that their browser is frozen when clicking 'Generate Report'. Your backend takes 30 seconds to generate the massive PDF. The React dev just wrote a standard `await axios.get(...)`. How do you fix the terrible UX?"
**Answer:**
*   "A traditional blocking HTTP call that takes 30 seconds is an anti-pattern. First, the browser might timeout. Second, it blocks the user's flow."
*   "I would redesign the API to be asynchronous. The React dev calls `POST /api/reports`. The backend immediately returns an HTTP 202 Accepted with a `jobId`."
*   "The backend delegates the heavy lifting to an async thread or a separate Kafka worker."
*   "The React dev then uses either **Long Polling** (`GET /api/reports/status/{jobId}` every 3 seconds), or connects via **WebSockets/Server-Sent Events** to receive an immediate push notification the instant the backend finishes."
