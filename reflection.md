# Task 0 — Reflection: Agentic Incident Flow

## 1. What was the hardest part?

The hardest part by far was **navigating and integrating with ServiceNow under extreme time pressure** without prior ServiceNow platform experience. Specifically:

1. **The ServiceNow Basic Authentication Gate (`401 Unauthorized`)**:
   - When attempting the write-back via the Table API, ServiceNow repeatedly returned `401 Unauthorized` with `"Required to provide Auth information"`, despite credentials working in the browser.
   - Tracking down the root cause in the system logs revealed a hidden enterprise security gate: `SNCRestrictBasicAuthUserAuthenticationGate: denied basic-auth API call for interactive-login user [admin] under enforce=true`.
   - Diagnosing that ServiceNow blocks Basic Auth for interactive web users, and then solving it by creating a dedicated machine user (`agent`) with `web_service_access_only = true` and `admin` roles, was the most time-consuming and challenging obstacle.

2. **UI Password Field Restrictions**:
   - The ServiceNow UI locks the password field on user records and forces auto-generated passwords, preventing manual password updates.
   - We overcame this by using ServiceNow's `sys.scripts.do` (Background Scripts) to set the hashed password directly via `gr.user_password.setDisplayValue(...)`.

3. **Data Policy Choice Mismatch (`403 Forbidden`)**:
   - After resolving the authentication issue, setting `state = 6` (Resolved) threw a `403 Forbidden Data Policy Exception: Resolution code is mandatory`.
   - The guide suggested `"Solved (Permanently)"`, but this PDI instance's dictionary strictly required the choice value `"Solution provided"`. Inspecting the `sys_choice` table via the API revealed the exact valid choice and resolved the issue.

---

## 2. What would you improve with more time?

With additional time, the following architectural improvements would be prioritized for a production-grade system:

1. **Redis for Distributed Deduplication & State**:
   - *Current*: Deduplication is handled using an in-memory Python `set` within the single application process.
   - *Improvement*: Use a distributed Redis cache with TTLs (Time-To-Live) so multiple API replicas can scale horizontally without duplicate incident processing or state loss across server restarts.

2. **Correlation IDs Across the Full Lifecycle**:
   - *Current*: Logs are organized by the ServiceNow incident number (`INC...`).
   - *Improvement*: Generate a unique `X-Correlation-ID` header at the ServiceNow Business Rule level, propagate it through the FastAPI middleware, into Gemini calls, and back to the ServiceNow Table API. This allows single-trace distributed logging across all systems in APM tools like Datadog or OpenTelemetry.

3. **Exponential Backoff & Retry Logic**:
   - *Current*: Network failures or transient API errors immediately fall back to safe escalation.
   - *Improvement*: Implement resilient retry policies (using libraries like `tenacity`) with exponential backoff and jitter for transient failures (e.g., Gemini rate limits, temporary ServiceNow network latency) before resorting to human escalation.

4. **Durable Asynchronous Task Queue**:
   - Replace in-process FastAPI `BackgroundTasks` with a durable distributed broker (e.g., Celery or ARQ with Redis/RabbitMQ) featuring Dead Letter Queues (DLQ) to ensure zero message loss even if a worker crashes mid-triage.
