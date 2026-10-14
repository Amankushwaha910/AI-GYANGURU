# AI GyanGuru Performance Audit — Baseline

**Status:** Partial baseline; audit is not complete.  
**Date:** 2026-10-10 (Asia/Kolkata)  
**Scope:** Read-only checks and measurements. No application source, dependency, environment, authentication, database, or user data was changed by this audit. The only new project file is this report.

## A. Environment

| Area | Observed configuration |
|---|---|
| Frontend | SvelteKit 2.70.1, Svelte 4.2.20, Vite 5.4.21, TypeScript 5.9.3 (lockfile); Node 24.19.0; Vite dev server on port 5173, PID 836 (`node`). |
| Backend | FastAPI 0.115.0, Uvicorn 0.30.6, SQLAlchemy 2.0.36, Pydantic 2.9.2; Python 3.13.15; server on port 8000, PID 12904 (`python`). |
| Database | PostgreSQL through `postgresql+asyncpg`, port 6543. Project documentation identifies the Supabase PgBouncer transaction pooler. Host and credentials intentionally omitted. `.env` leaves `DATABASE_POOL_MODE` unset, so the code default is `transaction`; `.env` has pool size 5 and max overflow 10. Transaction mode selects `NullPool` and disables asyncpg prepared statement caching in the existing code. No settings were changed. |
| Authentication | JWT Bearer access and refresh tokens. No token values were read or reported. |
| AI | `.env` selects Groq with `openai/gpt-oss-120b`. A Groq key is configured; OpenAI and Google keys are not configured. Key validity, quota, and provider latency were not tested. |
| Frontend API | `PUBLIC_API_URL=http://localhost:8000/api/v1`; Vite also proxies `/api` to `http://localhost:8000`. |
| Live status | Host PowerShell confirmed both listeners and successful HTTP 200 responses for frontend `/` and backend `/health`. Sandbox requests were denied local socket access; host-side PowerShell succeeded, so the sandbox error was not treated as an application outage. |

### Existing logging and timing

The backend returns `Server-Timing` and `X-Request-ID`; a live `/health` response confirmed both headers. Its observed `Server-Timing` value was `app;dur=2.3` ms. CORS exposes both headers to the frontend.

The timing implementation can report total app time, DB connection acquisition/release, aggregate SQL time and statement count, per-statement time/labels, gaps between SQL statements, AI duration when instrumented, and named application phases. Login adds user lookup, password verification, and token/response model phases. Dashboard adds handler, route pipeline/serialization, and JSON render phases. These values are available in response headers; values for the slow login/dashboard requests were not provided.

The project `.env` has `APP_DEBUG=false` and `LOG_LEVEL=INFO`. The request path/status/duration logger uses `logger.debug`, so that line is suppressed at the configured level. No request-correlated backend log output or log file was available during this audit.

## B. Performance measurements

All PowerShell samples were serial `Invoke-WebRequest` calls from the host environment. These are local HTTP request timings, **not browser navigation or rendering timings**.

| Operation | Samples | Individual results | Median | Min–max | Method / status |
|---|---:|---|---:|---:|---|
| Frontend `GET /` | 5 | 186.6, 79.5, 115.1, 142.6, 112.0 ms | 115.1 ms | 79.5–186.6 ms | Host PowerShell; HTTP 200 |
| Backend `GET /health` | 5 | 6.6, 7.2, 8.3, 9.7, 11.2 ms | 8.3 ms | 6.6–11.2 ms | Host PowerShell; HTTP 200 |
| Database connection + `SELECT 1` | 6 | See DB breakdown below | 5,089.5 ms total | 4,931.8–10,595.6 ms | Sequential, read-only probes through the project engine; PostgreSQL/NullPool |

### Database probe breakdown

Each sample separately measured entering `async with engine.connect()` and executing a read-only `SELECT 1`. This is a standalone connectivity probe; it is not the dashboard SQL and is not a substitute for browser/API measurements. The execute interval includes driver/network round-trip and server work; it is not a measure of PostgreSQL CPU alone.

| Sample | Connection acquisition | `SELECT 1` execute | Total |
|---:|---:|---:|---:|
| 1 | 8,325.0 ms | 1,472.0 ms | 9,797.0 ms |
| 2 | 9,032.5 ms | 1,563.1 ms | 10,595.6 ms |
| 3 | 3,935.1 ms | 1,162.7 ms | 5,097.8 ms |
| 4 | 3,831.2 ms | 1,130.9 ms | 4,962.1 ms |
| 5 | 3,918.4 ms | 1,162.8 ms | 5,081.2 ms |
| 6 | 3,806.1 ms | 1,125.7 ms | 4,931.8 ms |
| **Median** | **3,926.8 ms** | **1,162.8 ms** | **5,089.5 ms** |

Browser measurements previously supplied by the user (not independently captured or correlated in this run):

| Operation | Reported sample count | Reported timing/status | Missing evidence |
|---|---:|---|---|
| `POST /auth/login` | 1 | 8.66 s, HTTP 200 | Request ID, Server-Timing, response size, browser breakdown |
| Dashboard request | 1 | 7.16 s, HTTP 200 | Exact URL confirmation, Request ID, Server-Timing, response size/render timing |
| UUID-labelled requests | 3 successful, plus numerous 403s | 6.88 s, 10.96 s, 14.78 s successful; 403 durations reportedly ~5–14 ms | Full request URLs, methods, initiators, response bodies, IDs, timing headers, exact 403 count |
| CORS preflight | Not specified | HTTP 200 | Count and duration |

The UUID-labelled observations are not assigned to an endpoint based on the Network Name. No browser median is calculated from the supplied observations.

## C. API inventory and request behavior

Frontend/backend source inventory includes:

- Auth: `POST /auth/register`, `/auth/login`, `/auth/refresh`, `/auth/logout`, `/auth/google`; `GET /auth/me`; `PUT /auth/password`.
- Dashboard/analytics: `GET /dashboard`, `GET /analytics/dashboard`.
- Files: `POST /files`, `GET /files`, `GET /files/{upload_id}`, `DELETE /files/{upload_id}`.
- Summaries and explanations: collection generation/list, `/from-file` generation, get-by-ID, and delete-by-ID routes.
- Quizzes: generation/list, `/from-file`, `GET /quizzes/{quiz_id}`, `POST /quizzes/{quiz_id}/submit`, and `GET /quizzes/{quiz_id}/attempts/{attempt_id}`.
- History: collection read and delete-by-ID/delete-by-type routes. Users: `/users/me` read/update/delete. Models: `GET /models`.

No current Network URL or correlated request record identifies which route produced the UUID-named requests or 403s. The frontend client retries once only after HTTP 401; it does not retry HTTP 403.

The Upload page has a three-second interval for each pending/processing upload. Because the interval does not await the previous poll, slow calls can overlap. Rejected poll calls remain in the polling set, so a failed request can be retried on subsequent ticks until the page unmounts or that item later returns a terminal successful status. This is a confirmed code behavior but **not confirmed as the source of the observed UUID requests**.

The dashboard page fetches once per component mount. The global layout calls `/auth/me` on initial mount only when an access token exists; the login flow stores the user and tokens returned by login before navigating to the dashboard. These are code-path findings; actual browser request counts were not captured.

## D. API errors and authorization

No actual 403 URL or response body was available, so the reason for each observed 403 remains unknown. In this project, FastAPI `HTTPBearer(auto_error=True)` returns 403 `Not authenticated` when the Bearer header is missing or malformed. Authenticated requests can also return 403 for an inactive account. A role guard can return 403, but no current API route uses the role aliases. Resource ownership lookups generally return 404. These are possible code paths, not explanations attributed to the observed responses.

No login, dashboard, `/auth/me`, Summary, Explanation, Quiz, upload, History, Analytics, or model-list API requests were independently measured in this audit because browser authentication and request evidence were unavailable. The only backend HTTP route measured here was unauthenticated `/health`.

## E. Evidence-ranked bottlenecks

| Rank | Finding and evidence | Confidence | Potential impact | Risk / verification |
|---:|---|---|---|---|
| 1 | **Remote DB connection and round-trip latency.** The standalone probe measured 3.927 s median acquisition plus 1.163 s median `SELECT 1` execute, 5.090 s median total; two totals were 9.797–10.596 s. | High that the DB probe is slow; medium that it explains a specific API request. | If actual API `db_connect`/SQL fields are comparable, reducing this phase could recover seconds from DB-backed calls. | Pool changes carry high risk under PgBouncer; first correlate actual response headers and verify host/network/region effects. Do not change pool mode from this probe alone. |
| 2 | **Login and dashboard are slow at the browser boundary.** User-reported login 8.66 s and dashboard 7.16 s; no request IDs or timing headers supplied. | High for the reported durations; low for cause. | Potentially several seconds, but the addressable portion is unknown. | Source changes would be speculative. Capture five per-flow timing headers and compare same-account runs first. |
| 3 | **ID polling can overlap and repeat rejected requests.** Upload page uses a three-second interval without an in-flight guard; failed calls leave the ID in the set. The observed UUID route is not known. | High for the code behavior; low that it caused the browser observations. | Could remove redundant requests on `/upload`, but would not explain login/dashboard unless the request is correlated. | Low-to-medium if confirmed: test terminal failure behavior and poll-stop behavior without weakening authorization. First match URL and Initiator. |

No source fix is recommended until the first two API requests are correlated and the UUID/403 route is identified. Pooling, auth, and data-isolation behavior remain unchanged.

## F. Tests and measurement gaps

**Passed:** five frontend-root HTTP 200s; five backend-health HTTP 200s; six sequential read-only DB `SELECT 1` samples; runtime presence of `Server-Timing` and `X-Request-ID` on `/health`.

**Not run:** frontend typecheck/production build while the live dev server is using the generated workspace; no automated test suite was found in the source inventory. The existing `backend/scripts/smoke_test.py` was inspected but not run: it may register a user, call Summary/Explanation/Quiz generation, submit a quiz, create persistent records, and log out. The database-only `test_connection.py` was not needed; the probe used the existing engine and only `SELECT 1`.

**Not measured:** browser document/render/usable timings; login, dashboard, `/auth/me`, other authenticated API timings and counts; SQL counts and `Server-Timing` for those requests; response sizes; current dashboard data correctness; History/Analytics/Summary/Explanation/Quiz flows; file extraction/OCR; real AI provider calls, latency, retries, and output visibility; browser console errors; exact UUID and 403 routes/reasons; pool reuse/wait under application traffic; region/network attribution. No login or content generation was attempted, and no user data was changed.

## G. Baseline versus 1–2 second target

The local frontend root response (115 ms median) and backend health route (8 ms median) are within the target, but neither represents authenticated application flows. The database probe’s 5.090 s median total exceeds the target before a real application query is measured. The reported 8.66 s login and 7.16 s dashboard are also above target, but their components remain unknown. AI generation and OCR cannot be assessed without a safe, authorized browser workflow and controlled real-provider/file inputs.

### Five slowest observed values (different layers; not directly comparable)

1. UUID-labelled HTTP 200, user-reported: **14.78 s** (route unknown).
2. UUID-labelled HTTP 200, user-reported: **10.96 s** (route unknown).
3. Standalone DB probe, sample 2: **10.596 s** total.
4. Standalone DB probe, sample 1: **9.797 s** total.
5. `POST /auth/login`, user-reported: **8.66 s** (no backend breakdown).

The biggest **measured subsystem finding** is the slow standalone database connection/round trip. The biggest **application-flow observation** is the reported login duration, but its cause is not verified. The exact 403 reason and the source of UUID requests remain unknown.

### Next evidence and verification order

1. Capture five browser runs each for login and dashboard with URL/method/status, duration, size, `X-Request-ID`, and `Server-Timing`; record dashboard data-visible timing separately.
2. For one representative UUID 200 and 403, capture full route pattern (IDs redacted), method, Initiator, response error code/message, whether Authorization was present (yes/no only), and both timing/correlation headers. Do not share token/header values.
3. Use those request IDs to compare `db_connect`, SQL count/durations, auth phases, and app time. Only then rank an application or database fix and verify it with the same browser workflow.

**Audit status:** incomplete. No performance improvement is claimed.

## H. Follow-up — 2026-10-10 (Asia/Kolkata)

This follow-up preserves the original baseline. No application source, dependency, environment, authentication, or database settings were changed. The UI was returned to its original dark theme after a temporary theme toggle during navigation.

### Browser and behavior checks

| Item | Status | Evidence / method |
|---|---|---|
| Authenticated browser availability | **Measured** | Opened the running frontend in Codex In-app Browser. An existing authenticated test session was present. No credentials or token values were accessed or reported. This browser surface does not expose Chrome DevTools Network or raw response headers. |
| Dashboard visible content | **Measured, one page state** | Accessibility tree showed Topics Studied **7**, Summaries **7**, Quizzes Taken **2**, Quiz Accuracy **45%**, plus Recent Activity entries. This is an observation, not a correctness comparison against a known expected dataset. Weekly chart values and complete activity ordering were not available in the accessibility view. |
| History page | **Measured, page navigation only** | Route loaded; its accessible tree showed the page heading and filters, but no activity rows. History data behavior remains **unverified**. |
| Analytics page | **Measured, page navigation only** | Route loaded and exposed Daily Activity, Quiz Accuracy Trend, Weak Areas, Strong Areas, and Activity Heatmap sections. Series values were not exposed; trend correctness remains **unverified**. |
| Summary page and one provider generation | **Measured, one sample** | Entered the generic topic “Photosynthesis” and selected the configured Groq / GPT-OSS 120B model. A 4-section, 322-word result became visible; the UI labels the model `openai/gpt-oss-120b`. The generating state remained after a 10-second wait and the completed result was visible by the next check after a further 20-second wait (about **31.5 s maximum observed from click to result visibility**). This is UI elapsed time, not API/provider time. No `X-Request-ID`, `Server-Timing`, provider-only duration, or backend split was accessible. One summary was created in the test account as authorized by the follow-up request. No repeated provider call was made. |
| Dashboard after summary creation | **Unverified / incomplete render** | Returning to Dashboard showed skeleton placeholders for the four metric cards; they remained on the next accessibility check. This does not establish whether the dashboard API failed, was still pending, or the render was otherwise delayed. |
| Login request and request counts | **Unverified** | No login was performed: the in-app session was already authenticated, and no test credentials were available for a fresh login. No five-run login or dashboard sample set, request count, `/auth/me` count, API response duration, request ID, or timing header could be captured. |
| UUID and 403 requests | **Unverified** | The in-app browser provides no DevTools Network records. The actual paths, methods, initiators, response bodies, authorization-presence flags, statuses, and timings were not visible. Existing user-supplied durations remain uncorrelated. |
| File upload / extraction / OCR | **Unverified** | No suitable test file was supplied and no file was uploaded. |
| Explanation / Quiz | **Unverified** | Pages were not submitted or generated; no persistent content was created through these flows. |

### Backend correlation

**Unverified:** The accessible browser did not expose response headers, and the backend request logger is suppressed at the configured `INFO` level (see Section A). The Codex task has no attached app terminal session. Consequently, no request ID could be joined to backend `db_connect`, SQL count/duration, authentication/password verification, application phases, or serialization. Do not infer those components from the standalone database probe or the AI UI elapsed time.

### Repeat database probe

**Attempted, not measured:** A new standalone read-only `SELECT 1` probe was started through the project virtual environment. The Python process produced no connection-acquisition output within 60 seconds and was interrupted. It did not reach a reportable sample. This establishes only that this probe attempt stalled before emitting its first measurement; it does not establish whether the cause was database reachability, process startup, or another environmental delay. The six earlier samples in Section B remain the only successful database sample set. No pool or connection settings were changed and no load test was run.

### Existing tests and scope

**Code-inspected, not run:** `backend/scripts/test_connection.py` performs `SELECT 1` and queries `information_schema`; it also prints the configured database URL, so it was not run to avoid exposing connection details. `backend/scripts/smoke_test.py` registers/logs in a fixed account and creates Summary/Explanation/Quiz content; it was not run because it has persistent side effects. The test inventory showed these scripts but no discovered pytest or frontend test configuration. No automated test suite was run.

### Remaining blockers and smallest next actions

1. **Five login/dashboard API timings and correlation:** provide access to Chrome DevTools Network for the authenticated test browser (or capture the runs there). For each of five successful login and dashboard samples, record method, sanitized path, status, browser request duration, `X-Request-ID`, and `Server-Timing`; record the dashboard content-visible time separately. Include the login-triggered request list and `/auth/me` count. Never include credential/header values.
2. **UUID / 403 identification:** in the same Network view, capture one representative 200 and 403 with sanitized full path (UUID redacted), method, Initiator, status, duration, response error code/message, Authorization present yes/no, and correlation/timing headers. This is the minimum evidence to decide whether upload polling, quiz reads, or another route is responsible.
3. **Backend timing split:** once request IDs are captured, make the backend request logs available at a non-secret level or provide the corresponding safe timing records. Current INFO-level logging does not expose the debug request line, and no server terminal is attached here.
4. **Repeat database sample set:** rerun the read-only `SELECT 1` timing from a host shell that can reach the configured test database and return only per-sample acquisition/query/total milliseconds. The latest attempt stalled before connecting; do not change pool settings to address that observation.
5. **File / OCR behavior:** provide a small non-sensitive test file and an explicitly disposable test workflow, or leave this unmeasured. No upload was attempted.

**Follow-up status:** partial. One authorized AI generation and safe page navigation were observed, but browser request timing/correlation, fresh login, dashboard correctness, UUID/403 attribution, repeated database samples, file/OCR, Explanation, and Quiz remain unverified. No performance improvement is claimed.

## I. Follow-up — file-status 403 and accumulating polls (2026-10-10, Asia/Kolkata)

This section uses the user's supplied Chrome evidence for one confirmed request: `GET /api/v1/files/{file_id}`, HTTP 403, body `HTTP_ERROR / Not authenticated`, `Server-Timing: app;dur=1.9`. No token, cookie, or credential value was accessed. No source or configuration was changed.

### Verified request flow and call sites

**Code-inspected; one status-GET caller found:**

1. `frontend/src/routes/upload/+page.svelte:32-33` calls `loadUploads()` from `onMount` and calls `stopPolling()` from `onDestroy`.
2. `loadUploads()` at `:37-48` calls the list endpoint and then registers every upload whose state is `pending` or `processing` (`:53-62`). A newly uploaded file is also registered at `:136-145`.
3. `ensurePollTimer()` starts one component-local `setInterval` at **3,000 ms** (`:64-67`). `pollInProgress()` snapshots the set and calls `filesApi.get(id)` for each ID in `Promise.allSettled` (`:77-86`).
4. The only frontend call site found for `filesApi.get(id)` is this poll at `frontend/src/routes/upload/+page.svelte:85`. `frontend/src/lib/api/files.ts:19` maps it to `GET /files/${id}`; `api.get` maps to `apiFetch` in `frontend/src/lib/api/client.ts:113-116`, which issues `fetch` at `:73`.
5. Other UI callers of `filesApi.list()` request the collection `/files?...`, not `/files/{id}`. They do not explain this confirmed status endpoint.

**Polling behavior confirmed by code:** the 3-second `setInterval` does not wait for the preceding `pollInProgress()` call. Each tick can start another batch while earlier per-ID requests remain unresolved. With one slow ID, 25–28-second request durations permit roughly 8–10 overlapping ticks for that ID. `Promise.allSettled` allows one rejected request not to reject the whole batch. On rejection, `:88-91` immediately returns without removing the ID. Thus a 403 remains eligible for the next tick indefinitely while the route stays mounted. A successful response removes the ID only when its status is no longer `pending` or `processing` (`:95-110`); an empty set stops the interval (`:113-116`); unmount clears the interval and set (`:69-75`).

The `Set` prevents duplicate entries for one ID within one Upload page instance, and `ensurePollTimer()` prevents two intervals within that instance. Only one `filesApi.get` call site was found. Ordinary routing has one Upload page instance; a destroyed instance stops future ticks, although requests already in flight are not aborted. Therefore same-page interval overlap is confirmed; simultaneous duplicate component instances are not evidenced.

### Authentication and exact 403 interpretation

**Runtime evidence plus source establish the rejection branch:** `backend/app/core/dependencies.py:17` configures `HTTPBearer(auto_error=True)`. The installed FastAPI 0.115.0 implementation checks the incoming `Authorization` scheme/credentials and returns HTTP 403 with detail `Not authenticated` when the header or usable Bearer credentials are absent. The project's handler at `backend/app/core/exceptions.py:86-96` maps that detail to the observed JSON shape and `HTTP_ERROR` code. The user's `Server-Timing` contains only `app;dur=1.9`; it is consistent with this early dependency rejection before file lookup/database timings are added.

This 403 is **not evidence of a file ownership denial**. The endpoint in `backend/app/api/v1/files.py:76-97` requires `CurrentUserFast` at `:79`. If authentication succeeds, `backend/app/services/file_service.py:113-117` asks for a user-owned upload, and `backend/app/repositories/upload_repository.py:18-27` filters by both upload ID and `Upload.user_id`. A missing or other user's upload then becomes 404, preserving user isolation.

The browser's actual `Authorization` header presence was **not supplied**, so the precise client-side reason it was absent/unusable is unverified. In `frontend/src/lib/api/client.ts:57-66`, each call reads `localStorage.access_token` and adds `Authorization: Bearer …` only when that value is truthy. `filesApi.get` supplies no alternative header. Therefore, if this request traveled directly through this client, a missing/empty access-token value at call time yields exactly this no-header path. A malformed header or an intermediary stripping it cannot be excluded until Network request headers are inspected.

An expired but syntactically valid Bearer token does **not** match the observed FastAPI message: it passes `HTTPBearer` parsing, then JWT validation in `backend/app/core/dependencies.py:20-38` returns 401 `Could not validate credentials`. The client retries once after 401 (`client.ts:76-87`) by refreshing, and clears auth/navigates to login if refresh fails. The observed 403 bypasses that 401 refresh branch and `pollInProgress` treats it as an ignored rejection, so neither token refresh nor poll removal occurs for this response. The source does not establish whether auth was previously cleared by another flow; `clearAuth` removes both stored tokens at `frontend/src/lib/stores/auth.ts:40-46`, and layout session restoration can call it after `/auth/me` failure at `frontend/src/routes/+layout.svelte:24-35`.

### Why the UUID-labelled timings differ

Only one full URL has been confirmed. The other UUID-labelled 200 and 403 requests must not be assigned to this route from their Network Name. For the confirmed file-status 403, the 1.9 ms app time is consistent with an early authentication rejection, not a slow file query. The reported 25–28-second 200 requests were not provided with full paths, request IDs, or their timing headers; they cannot yet be attributed to the same endpoint or split into connection, SQL, and application time. If they are file-status GETs, they passed authentication and may be spending time later in the path, but that remains a hypothesis.

### Correlation and backend logs

**Instrumentation code-inspected; request correlation unavailable:** `backend/app/main.py:53-61` exposes `Server-Timing` and `X-Request-ID` through CORS; `:72-109` adds the timing and request ID. `backend/app/core/performance.py:56-74` emits database connection/query phases when present. `frontend/src/lib/api/client.ts:92-99` logs request duration, server timing, and request ID without logging Authorization values. The supplied 403 has a Server-Timing value but no request ID. No request-correlated server log was accessible; the request log is `logger.debug` at `main.py:80-87`, while the prior audit found the configured level is INFO and no app terminal is attached.

### Finding and smallest safe fix to evaluate

**Confirmed immediate causes:** (1) the reported 403 is the HTTP Bearer dependency rejecting a request that reached the backend without usable Bearer credentials; (2) the Upload poller overlaps slow requests and retries rejected IDs every three seconds. **Unverified underlying trigger:** whether `localStorage.access_token` was empty at each failing fetch, the header was malformed/stripped, or auth state was cleared by another flow. The expired-token hypothesis is not consistent with the exact 403 body under this dependency path.

Smallest safe fix to evaluate after confirming Network headers: if the access token is absent but a refresh token exists, refresh before making the protected request and attach the returned access token; if refresh is unavailable or fails, take the normal logged-out path. Do not retry every 403, because other 403 responses may represent real authorization denials. Separately, serialize polls per ID (or skip a tick while that ID is in flight) and retire an ID / surface an auth error after a permanent 401/403 so it cannot poll forever. Keep the backend bearer check and owner filter unchanged.

### Evidence still needed to close the root-cause gap

For one failing 403 and one slow 200, capture from Chrome Network: sanitized full path (UUID redacted), method, **Authorization present yes/no and scheme only** (never its value), Initiator, status, response body, browser duration, `X-Request-ID`, and complete `Server-Timing`. For the 403, this will distinguish a missing client token from a malformed/stripped header. For the slow 200, the path and timing header are required before attributing its 25–28 seconds to this endpoint or the database. If a request ID is present, provide the matching safe backend timing/log record; do not include credentials.

**Status:** source explains the confirmed 403 response and why it repeats in the poller, but the reason the browser request lacked usable Bearer credentials and the identity/timing of the UUID-labelled 200 requests remain unverified. No fix was implemented.

## J. Follow-up — dashboard database acquisition timing (2026-10-10, Asia/Kolkata)

No application source, environment, dependency, authentication, schema, or database-pool settings were changed. The browser timing below is the user's latest Chrome DevTools evidence; source mappings are code-inspected. No new database connection probe or load test was run in this follow-up because the previous standalone probe stalled before producing its first sample (Section H).

### Measured dashboard request (user-supplied Chrome evidence)

| Measurement | Value | Status |
|---|---:|---|
| `GET /api/v1/dashboard` | HTTP 200; browser total about **7,140 ms** | **Measured**, one user-supplied browser sample |
| `app` | **7,061.5 ms** | **Measured**, supplied `Server-Timing` |
| `db` total / statement count | **2,288.6 ms / 2** | **Measured**, supplied header |
| User query | **1,137.6 ms** | **Measured**, supplied header label |
| Analytics/dashboard query | **1,151.1 ms** | **Measured**, supplied header label |
| `db_connect` | **3,870.9 ms** | **Measured**, supplied header |
| `dbgap` | **88.7 ms** | **Measured**, supplied header |
| `db_release` | **0.1 ms** | **Measured**, supplied header |

The listed database buckets total about **6,248.3 ms**. That is a partition-like view of some measured intervals, not an additive decomposition of `app`: the app timer is the outer request elapsed time and contains the nested database, route, and response work. The browser total exceeds the reported app time by about **78.5 ms**, consistent with browser/network overhead and rounded supplied values. The approximately 3.87-second connection bucket is the largest single reported interval. This is one browser request, not a new five-sample comparison.

### What the connection timer measures

**Code-inspected:** `backend/app/core/database.py:162-176` calls `get_session_factory()` and enters the session context before starting `db_connect`; then it times `await session.connection()` and records `db_connect` before yielding the database session to endpoint dependencies/handlers. Thus the reported interval covers the session's request to acquire an active SQLAlchemy connection, including driver/network/database handshake work required to establish it. It excludes lazy engine/session-factory creation, which happens before the timer at `:167` (engine construction at `:40-96`). It is not a measurement of SQL execution.

**Code-inspected:** the active transaction-pooling branch at `backend/app/core/database.py:61-75` uses SQLAlchemy `NullPool`, disables asyncpg's statement cache, and creates a new client connection for each checkout/use rather than reusing an application-side pool connection. Therefore this path has no QueuePool checkout queue to account for the 3.87 seconds. The timer does not identify how much is DNS, TCP, TLS, PostgreSQL/asyncpg startup, authentication, PgBouncer proxy work, or transaction setup. It also does not prove which of those subphases is slow.

### Timing overlap and statement attribution

**Code-inspected:** `backend/app/core/performance.py:34-53` brackets SQLAlchemy cursor execution using engine `before_cursor_execute` / `after_cursor_execute` hooks registered in `backend/app/core/database.py:77-88`. The SQL bucket represents that cursor-execution interval; it does not split server execution from network round-trip or result transfer. `dbgap` is elapsed time from the end of one such cursor interval to the start of the next. Connection acquisition occurs before the first SQL timer, so it does not overlap either dashboard SQL interval. The two query intervals and the measured inter-query gap are sequential in this request. `app;dur` contains them; route/handler phase timers may be nested and should not be summed with `app` or with their parent phases.

**Code-inspected:** the dashboard API's fast-user dependency is declared before the endpoint's `db` parameter at `backend/app/api/v1/dashboard.py:72-86`; it uses the same cached `get_db` dependency. It authenticates the bearer token and reads the user row before calling the dashboard repository. The `user`-labelled query is consistent with that user lookup; the other query is the combined dashboard read. Both together explain the reported count of two SQL statements.

### Dashboard SQL review

**Code-inspected:** `backend/app/repositories/dashboard_repository.py:19-178` issues one SQLAlchemy `SELECT` for dashboard payload data. It composes scalar aggregate subqueries for event summary totals, daily activity, quiz accuracy, seven-day quiz trend, and the ten newest history items; it returns the existing summary/activity/trend fields. The repository therefore already combines those dashboard reads into one database round trip. The second request-level statement is the authenticated-user lookup, not another dashboard repository call.

No query plan, table cardinalities, index inventory, cache state, or comparable database-side execution breakdown was available. The SQL source alone does not establish a safe rewrite or index change: each aggregate has distinct filtering/grouping/order semantics, and any change needs correctness comparison on the populated account plus a plan under representative data. No SQL optimization is recommended from this single timing. The most useful next SQL evidence is a sanitized `EXPLAIN (ANALYZE, BUFFERS)` for the combined dashboard `SELECT` on the test account, only if the database owner permits that read-only diagnostic and it can be run once without competing traffic; compare its server execution time with the approximately 1.15-second client-observed query interval.

### Supabase/PgBouncer and initialization assessment

**Confirmed by current source/configuration:** transaction mode selects `NullPool`; prepared-statement caches are disabled for compatibility with transaction pooling. The code comment in `database.py:62-70` explains that PgBouncer may reuse backend sessions and therefore the app disables caches and uses unique prepared statement names. `DATABASE_POOL_MODE` defaults to `transaction` in `backend/app/core/config.py:29-35`; this source default and the reported current configuration identify the active connection strategy, without exposing the database URL or host.

**Measured:** the current dashboard's connection-acquisition timer is 3,870.9 ms. Earlier successful standalone read-only probes in Section B also measured slow acquisition and `SELECT 1` round trips. Together, those establish repeated slowness around fresh database connections/round trips, but they do not isolate network location, DNS, TLS, server authentication, PgBouncer queueing, or asyncpg startup. A separate probe attempt in Section H stalled before its first sample, which is not diagnostic of any particular phase.

**Hypothesis, not established:** making a fresh client-to-pooler connection for each request under `NullPool` can make connection setup visible on every request. The supplied values and earlier probes are compatible with connection establishment through the remote pooler being expensive. They do not show that PgBouncer itself, TLS, geographic latency, or the asyncpg driver is specifically responsible. SQLAlchemy's lazy engine initialization is outside `db_connect` and does not explain this measured request's 3,870.9 ms bucket. No measurement currently proves how much of this interval is PostgreSQL authentication versus network/client initialization.

### Login route (not measured in this follow-up)

**Code-inspected:** `POST /api/v1/auth/login` in `backend/app/api/v1/auth.py:36-44` depends on `get_db`. `backend/app/services/auth_service.py:64-83` times user lookup as `auth_user_lookup`, password verification as `bcrypt_verify`, checks account state, then creates tokens. `_issue_tokens` at `:157-178` times JWT creation and auth response-model work as `jwt_and_auth_response_model`; it updates the refresh-token hash on the user and the dependency commits when the endpoint succeeds (`database.py:176-180`). The outer middleware emits `app` timing for the request (`main.py:72-98`).

There is no login `Server-Timing` sample or correlated `X-Request-ID` in the latest evidence, so none of these phases has a measured value here. The dashboard connection finding must not be presented as a measured login breakdown. A fresh login request would need its full timing header and request ID before attributing any login delay to connection acquisition, SQL, password verification, token work, or commit.

### Log access and limitations

The middleware emits `X-Request-ID` in `backend/app/main.py:101-109` and safe request metadata at debug level in `:80-87`; the timing header is constructed at `:72-79`. No request ID was included in the supplied dashboard details, and no correlated backend log/terminal record was available in this task. Even with an ID, the current debug line contains only route/status/overall elapsed time; detailed SQL and phase values are available in the response's `Server-Timing`, not in that log line. No credentials, database URL, token, or secret values were read or reported.

### Safest next experiment

Use a single controlled, read-only diagnostic from the same backend host and network path: collect a small bounded set of fresh `NullPool` connection samples, each with a hard timeout, and separately measure connection establishment and one `SELECT 1` on that connection. Instrument phases without printing the DSN or credentials; report individual values, median, min, max, and failures. If feasible, split DNS/TCP/TLS/driver/PostgreSQL handshake with driver or socket-level timing, while keeping the existing pool configuration unchanged. Stop on timeout rather than retrying indefinitely. In parallel, capture one fresh login request's complete sanitized `Server-Timing` and request ID, and one dashboard request's request ID plus header. This will determine whether login shares the same connection delay and whether the 1.15-second combined dashboard SQL interval is server execution or client/network/result time. A single, permitted plan capture for the combined dashboard query is the next SQL-level check; do not rewrite SQL or tune pooling until those measurements and dashboard-data correctness are compared.

**Status:** Dashboard connection acquisition is the dominant measured subphase in the supplied request; the mechanism beneath that timer is **unverified**. Dashboard SQL is already one combined read, and no safe optimization is justified by the available plan-free sample. Login timing, connection subphase attribution, and SQL server-side execution remain **unverified**. No improvement is claimed.

## K. Follow-up — bounded connection diagnostic attempt (2026-10-10, Asia/Kolkata)

No application source, dependency, environment, database setting, schema, or data was changed. Configuration source was inspected without displaying values. The temporary diagnostic included a guard requiring transaction mode and `NullPool`, then would use the existing engine and asyncpg/SQLAlchemy driver without changing pooling; because its output was buffered, it is unknown whether that guard completed or whether any connection attempt began. The existing `backend/scripts/test_connection.py` was not run because it prints the Supabase URL and queries/lists schema tables, neither of which is needed for this measurement. The smoke test was not run because it can create persistent content.

### Result

**Attempted, not measured:** a temporary standalone diagnostic process was launched from `backend/`. It included a check that the active configuration selected transaction mode and `NullPool`, and was set to a 13-second internal timeout with a 14-second external process limit. Its output was redirected and buffered. The process had not exited at the external limit, so it was terminated and waited on; temporary script and output files were removed. No phase timing was captured before termination.

Because no output was flushed, it is **unknown** whether the process stalled during Python/configuration startup, engine initialization, connection acquisition, cancellation handling, or another stage. This result is not a connection-acquisition timeout and not a `SELECT 1` failure. No connection/query sample, sanitized exception, or phase duration can be reported. The process was terminated by the external safety guard rather than exiting cleanly from its own timeout handler; no background diagnostic process was intentionally left running.

### Status and next action

The previously supplied dashboard `db_connect` and SQL timings remain the only evidence for the current application request. The lower-level connection-versus-query split is still **unverified**. The safest next step is to repair the diagnostic harness so it emits unbuffered stage markers before configuration loading and each phase, has a process-level watchdog that reliably terminates and reaps the child, and runs only after validating startup independently without opening a database connection. Then perform at most three sequential attempts under a hard 15-second cap, stopping on the first connection timeout/error or repeated slow acquisition. Do not infer a query failure unless a connection was successfully acquired and the `SELECT 1` phase itself failed.

**Status:** no timing samples; the diagnostic harness did not meet the clean-timeout requirement. No optimization or configuration change was made.

## L. Follow-up — repaired harness validation and bounded run (2026-10-10, Asia/Kolkata)

No application source, dependencies, environment files, database settings, schema, or data were edited. Temporary diagnostic scripts and redirected output files were created only under the OS temporary directory and removed after each run. Git status shows the same pre-existing project modifications as before this follow-up, plus this audit file; no reset or cleanup was performed.

### Safe startup checks (measured, no database connection opened)

- A bounded interpreter startup probe completed and emitted its flushed monotonic marker.
- A bounded import probe completed `asyncio`, application settings, and the database module imports. Its first version exposed a harness path issue (`app` was not on `sys.path` when the script lived in the temporary directory); the probe was corrected to add the backend working directory explicitly. Settings values were never printed.
- A separate bounded engine-setup probe completed; the active engine object reported `NullPool`. It created no connection and ran no SQL.
- The existing `test_connection.py` and smoke test were not run; the former prints configuration and queries schema metadata, while the latter can write persistent content.

### Full diagnostic result (not measured)

The temporary full diagnostic was configured to use the existing application settings, transaction-mode `NullPool`, and SQLAlchemy/asyncpg; it included flushed monotonic stage markers, a 9-second internal deadline, and an external process supervisor. On each full-harness run the child did not exit within its external deadline. The supervisor killed the process tree and waited for the Python process to exit; temporary files were then removed. No output file contained a stage marker or sanitized error, so it is unknown whether the full script reached configuration loading, engine/session setup, connection acquisition, or `SELECT 1`. Consequently, there are **zero reportable connection-acquisition or query timings**. This is not evidence of a connection timeout or query failure, and no per-attempt status can be assigned.

The full-harness attempts were each capped at no more than three sequential attempts (the final simplified run at one); because no stage output survived, the number of actual connection attempts cannot be established from this run. No further database attempt was made after this uncertainty. The diagnostic process was reaped after supervisor termination; the short no-database probes exited normally. No child process was intentionally left running.

### Interpretation and next action

The successful import and engine-setup probes show that Python startup, configuration import, and `NullPool` engine construction can complete in isolation. They do not identify why the supervised full harness emitted no stage output, and they provide no evidence about DNS, TCP/TLS, driver handshake, PostgreSQL authentication, PgBouncer, or query execution. The dashboard request measurements from Section J remain the only usable database timing evidence.

**Blocker:** this execution environment did not provide a trustworthy completed supervised run of the full harness. The smallest next step is to run a minimal, single-attempt diagnostic in an interactive backend-host terminal where unbuffered stdout can be observed live, with the same hard process watchdog and sanitized stage markers. Do not repeat database attempts here until that supervision/output path is verified. No optimization is justified by this result.

**Status:** diagnostic harness validated only through imports and engine construction; database phase measurements remain unverified.

## M. Follow-up — interactive PTY supervised diagnostic (2026-10-10, Asia/Kolkata)

No application source, environment, dependency, pool setting, schema, or data was changed. The previously existing working-tree modifications were preserved. The diagnostic used one temporary script under the OS temporary directory and the existing backend Python executable; the script was removed after the run.

### Live supervised run

**One diagnostic process launched; no database measurement obtained.** The process ran under a PTY-backed PowerShell supervisor. Child stdout was read line-by-line and forwarded to the terminal; the diagnostic used unbuffered Python and explicit flushes. The supervisor used a monotonic clock and enforced a **14,000 ms** hard deadline, below the requested 15-second maximum.

- Last visible stage: **none**. The child emitted no marker, including no `configuration_load started` marker.
- Connection acquisition: **not established as started**. No connection-acquisition duration, connection timeout, query timing, or database error can be reported.
- `SELECT 1`: **not attempted as far as visible evidence establishes**; no query result or query failure is claimed.
- Timeout behavior: the external supervisor reached 14,000 ms and requested process-tree termination.
- Cleanup: the supervisor reported the child exited and was reaped, with exit code `-1`; stderr was empty. The temporary script was removed. No second diagnostic was launched.

This is a supervised **process-level timeout before any observable application stage**, not a database connection timeout. Earlier separate no-database probes had confirmed Python startup, configuration imports, and `NullPool` engine construction, but that does not establish what blocked this child before its first marker. The underlying stage remains unknown. No further attempt is appropriate in this session because the requested single attempt has been consumed and it produced no observable stage evidence.

**Status:** zero database timings. The smallest next action is to inspect why the backend Python process launched under the PTY supervisor emitted no first-line output (for example, verify the exact child command and script path in a no-database interactive check) before authorizing another database attempt. Do not infer a database or query failure from this run.

## N. Follow-up — existing request timing and log coverage (2026-10-10, Asia/Kolkata)

No standalone diagnostic, database probe, source change, environment change, or pool change was made. Existing working-tree modifications remain intact. The backend terminal tool reports that no app terminal is attached to this thread, and the backend tree contains no `.log` or `.out` log files. No request-correlated backend log record was available to inspect.

### Confirmed timing boundaries

**Code-inspected:** in `backend/app/core/database.py:167-175`, `get_db()` obtains the session factory and enters the `AsyncSession` context before starting `db_connect`. The timer starts immediately before `await session.connection()` and is recorded immediately after that await completes. Thus it measures the total wait for SQLAlchemy to make the session's connection available. It excludes `get_session_factory()` / lazy `create_async_engine()` setup at `database.py:40-96`, and excludes SQL execution. On the active transaction-pool branch, `database.py:61-75` uses `NullPool`; there is no SQLAlchemy QueuePool checkout queue for this path.

The timer currently fails to record a `db_connect` value if `session.connection()` raises, because `add_timing()` is after the await. `db_release` at `database.py:181-187` measures `session.close()` only; the successful-request commit at `:177` is outside that bucket. The overall `app` timer at `backend/app/main.py:72-98` contains connection acquisition, route execution, dependency teardown/commit, response work, and release.

**Code-inspected:** SQL timers are registered around SQLAlchemy cursor execution in `database.py:77-88`; `backend/app/core/performance.py:34-53` measures from `before_cursor_execute` to `after_cursor_execute`. It includes the client-side cursor execution round trip and does not split PostgreSQL server execution from transport/result transfer. `dbgap` is the elapsed interval between cursor-operation end and the next cursor-operation start. The reported SQL/connect/gap intervals are within the outer app duration; phases such as `auth_user_lookup` also wrap database work and overlap their corresponding SQL timer.

### What existing instrumentation can and cannot show

- **Driver/connection creation:** not separately timed. Under `NullPool`, a fresh client connection is created for each session use. The current `db_connect` bucket includes whatever connection creation and driver setup is needed during `session.connection()`, but cannot distinguish it from SQLAlchemy acquisition overhead.
- **PostgreSQL authentication, DNS, TCP, TLS, or PgBouncer:** no separate phase exists. These may be parts of driver connection creation, but current timings cannot attribute time to any one of them.
- **Application login authentication:** code timers already exist in `backend/app/services/auth_service.py:64-83` for `auth_user_lookup` and `bcrypt_verify`, and `:157-178` for token/auth response-model work. `auth_user_lookup` includes the user query, so its duration overlaps the relevant `dbq` duration. These are response-header phase candidates, not database-password/authentication-network metrics.
- **Dashboard SQL:** supplied browser evidence for the dashboard remains one request with approximately 7,061.5 ms app time, 3,870.9 ms `db_connect`, two SQL statements totaling 2,288.6 ms, an 88.7 ms gap, and 0.1 ms release. These are user-supplied measurements; there is no request ID in the supplied evidence to join to server logs.
- **Login:** source provides phase timers, but no request-correlated login `Server-Timing` header or backend timing record is available in this investigation. The earlier browser total alone cannot allocate login time to connection setup, user lookup, bcrypt, token generation, commit, or response work.

**Code-inspected:** `backend/app/main.py:53-61` exposes `Server-Timing` and `X-Request-ID` to browser clients. Request IDs are generated and returned at `:101-109`. A request summary containing request ID, method, raw path, status, and total duration is logged at DEBUG at `:80-87`. Logging level is selected at `:28-30`; its source default is INFO in `backend/app/core/config.py:106-107`, so that DEBUG request line is normally suppressed at the default level. No captured backend log or attached app terminal was available here. The exact active process log level was not read from `.env` or printed.

### Smallest safe instrumentation-only proposal (not implemented)

Keep the existing `db_connect`, SQL, route, and authentication timers unchanged. Add a per-physical-connection `driver_connect` duration around SQLAlchemy's dialect connection creation using paired SQLAlchemy engine/pool events: record a monotonic start immediately before the DBAPI connect call, then record elapsed time on the pool `connect` event after the asyncpg connection has been established. Emit only that duration into the existing request timing context and `Server-Timing`; never log connect arguments, DSNs, exception strings, or user identifiers. Validate that the timing context propagates correctly through SQLAlchemy's async greenlet event bridge before relying on the metric. Because `db_connect` is the outer acquisition interval, `driver_connect` is a nested measure and must not be added to it.

That pair would separate SQLAlchemy's overall session connection acquisition from the entire asyncpg connection-creation phase. It still would **not** distinguish DNS, TCP, TLS, PostgreSQL credential authentication, PgBouncer handling, or asyncpg protocol initialization inside the driver call. No safe existing hook in the inspected code exposes those internal subphases. If the driver-connect span accounts for most of `db_connect`, a later, separately approved driver/network diagnostic would be needed to split those causes.

For request correlation during normal traffic, the smallest safe log improvement would be to emit the existing request summary at INFO using the route template (not raw path/query), request ID, method, status, and already-sanitized timing metrics. This is optional if the browser captures the response headers; current code already sends both headers. Do not change log level or code in this investigation phase.

### Next evidence-gathering step

First capture one successful Chrome login and dashboard request with sanitized route, status, `X-Request-ID`, and complete `Server-Timing`; share the IDs and timing headers only. If backend-side correlation is still required, attach the running backend terminal or provide log lines filtered to those IDs with method, route template, status, duration, and timing phase names/durations only. Then, if authorized, add only the `driver_connect` instrumentation described above and capture the next normal login/dashboard requests. Do not infer network, PostgreSQL authentication, or PgBouncer cause from the existing aggregate `db_connect` duration.

**Status:** the current timer's exact bounds are confirmed; existing source can report aggregate connection acquisition, SQL cursor intervals, login bcrypt and application-auth phases, and outer app time. Driver/network/auth subphases and request-correlated backend logs remain unavailable. No root cause beneath `db_connect` is established.

## O. Follow-up — per-connection driver timing instrumentation (2026-10-10, Asia/Kolkata)

Added an instrumentation-only `driver_connect` metric. No route, response body, SQL, authentication, environment value, schema, database data, dependency, or pool setting was changed. The active `NullPool` configuration remains intact. Existing unrelated working-tree edits were preserved.

### Method and compatibility evidence

**Code-inspected / installed versions:** the backend environment has SQLAlchemy **2.0.36** and asyncpg **0.30.0**. SQLAlchemy 2.0.36 exposes `DialectEvents.do_connect(dialect, conn_rec, cargs, cparams)` and documents that a listener may return a DBAPI connection. The installed default creator in `sqlalchemy/engine/create.py:631-643` invokes each `do_connect` listener and, when it returns a connection, uses that value instead of its default `dialect.connect(*cargs, **cparams)` call. The new listener makes that same call with the original arguments, wrapped in a `try/finally`; this records both successful and failed/cancelled driver calls without exception text or connection arguments. It does not change connection options or install another creator.

The event is installed on `AsyncEngine.sync_engine`, the documented synchronous event target for async engines. Installed SQLAlchemy source at `ext/asyncio/engine.py:273` shows async connection acquisition runs through `greenlet_spawn(self.sync_engine.connect)`, and `_concurrency_py3k.py:74-83` copies the parent greenlet context. Existing real-request SQL timings also show the same request `ContextVar` timing dictionary is updated from sync-engine cursor events and read when `Server-Timing` is emitted. The new callback records through that same context-aware `add_timing` path. No connection event logs arguments or user/request payload data.

The metric measures only the duration of the asyncpg DBAPI `dialect.connect()` call. It is a nested phase inside `db_connect`; it must not be added to `db_connect`. It does not separate DNS, TCP, TLS, PostgreSQL authentication, PgBouncer processing, or later SQLAlchemy connection initialization.

### Source changes

- `backend/app/core/database.py`: registers the `do_connect` wrapper when the existing engine is created.
- `backend/app/core/performance.py`: aggregates and emits `driver_connect;dur=...` in the existing `Server-Timing` header.
- `backend/tests/test_connection_timing.py`: adds focused success and failure tests, including checking that exception text does not appear in the timing header.

### Validation

- **Passed:** focused backend tests: `2 passed` (`backend/venv/Scripts/python.exe -m pytest tests/test_connection_timing.py -q`).
- **Passed:** Python compilation for `app/core/database.py` and `app/core/performance.py`.
- **Passed:** `npm run check` — Svelte reported 0 errors and 0 warnings.
- **Failed:** `npm run build`. Vite emitted dependency export warnings (`untrack`, `fork`, `settled`) and then failed with `EPERM` while creating `frontend/.svelte-kit/output/server/entries/pages`. No dependency change or retry was made; the frontend was not edited by this task.
- **Not run:** no live DB connection or application request was made, so no new `driver_connect` duration is available yet.

**Status:** instrumentation is ready for the next normal login/dashboard request. Capture `X-Request-ID` and the complete `Server-Timing` header from that request. Compare nested `driver_connect` with `db_connect` to see how much of acquisition is inside the asyncpg DBAPI connect call. The underlying network/authentication/PgBouncer cause remains unverified.

## P. Master audit continuation — environment and validation (2026-10-10, Asia/Kolkata)

### Pre-change checklist (reviewed before this phase)

**Code-inspected existing feature areas:** login/register and token-based auth; dashboard with combined repository query; History; Analytics; Summary; Explanation; Quiz generation/play/results; upload, extraction/status polling, and file listing; provider/model selection (Groq, OpenAI, Gemini); OCR/file processing; route guards and shared API client. Relevant routes are under `frontend/src/routes/`; backend API modules are under `backend/app/api/v1/`, with provider, service, and repository implementations under `backend/app/`.

**Known issues carried forward:** historical slow login/dashboard/History/files/AI timings are not fresh samples; dashboard database acquisition remains unexplained; driver-connect instrumentation has not been observed in a live request; upload polling fix has unit coverage but no live-browser verification; a previous unauthorized file request returned 403 (`Not authenticated`) with token cause unresolved; frontend build previously failed intermittently with `EPERM`; SvelteKit/Svelte export warnings remain. No source fix beyond the already implemented polling and timing instrumentation was made during this phase.

### Environment/build investigation

**Measured/confirmed:** the current `npm run build` first failed at Rollup output creation with `EPERM: operation not permitted, mkdir 'D:\AI GyanGuru\frontend\.svelte-kit\output\client\_app\immutable'`. A previous attempt recorded in Section O failed at a different generated `server/entries/pages` path. Directory inspection found inherited ACLs, eight rules, and no deny rule on the generated paths; `.svelte-kit` had the Windows `ReadOnly` directory attribute. A pre-build `Get-Process -Name node` query found no visible Node process. CIM process/port enumeration was denied (`Access to a CIM resource was not available to the client`); `tasklist` could not enumerate due its Windows logon error. These observations do not establish machine-wide absence of another writer or a file-system filter.

**Measured:** without clearing attributes or deleting output, a second sequential `npm run build` completed successfully (exit 0; Vite reported client build 25.06 s and server build 46.56 s). Both attempts emitted the existing `untrack`, `fork`, and `settled` export warnings. Installed frontend versions observed by `npm ls --depth=0`: SvelteKit 2.70.1, Svelte 4.2.20, and Svelte Vite plugin 3.1.2. The warning names concern exports absent from the installed Svelte SSR/index modules; no version change was made. The successful retry proves the build can complete in this checkout, but the exact reason for the earlier transient EPERM remains **unverified** (lock, concurrent writer, antivirus/filter, sandbox/filesystem behavior, and generated-directory race were not distinguished). The `ReadOnly` attribute alone is not established as the cause.

### Checks run

- **Passed:** `node --test tests/upload-polling.test.mjs` — 5 passed, 0 failed. These are polling behavior tests, not real upload/OCR flows.
- **Passed:** `backend/venv/Scripts/python.exe -m pytest tests -q` — 2 passed (connection-timing focused tests). Pytest emitted the existing `pytest-asyncio` default fixture-loop-scope deprecation warning.
- **Passed:** `backend/venv/Scripts/python.exe -m compileall -q app`.
- **Passed:** `npm run check` — Svelte diagnostics: 0 errors, 0 warnings.
- **Passed:** second `npm run build` — exit 0. Existing Svelte export warnings and adapter-auto's “could not detect a supported production environment” informational warning remain.
- **Passed:** `git diff --check` (only existing LF-to-CRLF notices for the two `.env.example` files).
- **Not run:** `npm run lint`. No ESLint config file was found in the project scan; the package script exists, but a successful lint result cannot be claimed without a config.

The first `npm run check` invocation was stopped after it remained at “Getting Svelte diagnostics...” without further output for about 30 seconds. A subsequent serial run completed successfully. Only the check/build processes launched in this phase were stopped/reaped or exited; no server was launched or terminated.

### Runtime/browser and data checks

**Unverified due environment restriction:** this execution shell could not reach either local service. `Invoke-WebRequest` to `127.0.0.1:5173/` and `127.0.0.1:8000/health` failed with Windows `HttpRequestException: An attempt was made to access a socket in a way forbidden by its access permissions`. CIM socket/process enumeration was denied as above. This does not contradict the user-supplied host-side confirmation; it means this execution environment cannot independently use those listeners. No duplicate server was started.

Chrome has an AI GyanGuru sign-in tab (`localhost:5173`) in addition to the current Codex page, but computer-use tab switching failed on two attempts; per the UI recovery instruction no further browser input was attempted. No login credentials or session data were entered. Therefore no fresh browser Network measurements, X-Request-ID/Server-Timing correlation, request counts, dashboard render timing, login request count, populated-account dashboard totals/trends/Recent Activity checks, or History/Analytics/Summary real flows were obtained. No persistent content was created, no files were uploaded, and no paid AI requests were made. Explanation, Quiz, and Upload/OCR remain unverified end-to-end.

The historical 9.530-second dashboard median and earlier login/dashboard breakdowns remain historical references only. There are zero comparable fresh browser samples in this phase; **no browser improvement claim is made**. The `driver_connect` metric still has no fresh live request measurement. Database tests in this phase were unit tests only; no connection probe, query benchmark, or user data read was run.

### Findings and smallest next actions

1. **Build EPERM — exact cause unresolved.** The build now succeeds on a sequential retry without cleanup or configuration changes. If EPERM recurs, capture the failing path and concurrently collect an authorized Windows file-handle/antivirus event trace for that exact path; the current ACL/process evidence is insufficient to name a root cause. Do not remove `.svelte-kit` or alter ACLs based only on this record.
2. **Live app/browser evidence — blocked here.** The smallest next step is a host-side Chrome Network capture from the already-running app: one login and dashboard request with sanitized URL path, status, total duration, `X-Request-ID`, and complete `Server-Timing`; do not include request credentials/cookies. For data validation, use the existing authorized test-account session and capture only dashboard aggregates/activity ordering. This shell cannot take those measurements because localhost sockets are denied and browser tab switching failed.
3. **Other feature flows — unverified.** Use existing account data/read-only pages for History and Analytics, and verify Summary only if an existing generated record can be opened without generating new content. Leave Explanation, Quiz, and Upload/OCR untested unless a safe non-persistent fixture or explicit upload/generation authorization is available.

**Files changed in this phase:** this append to `PERFORMANCE_AUDIT.md`; the production build also wrote generated output under `frontend/.svelte-kit/`, which was left intact. No tracked application source, dependency, environment, authentication, database, or data file was changed. Existing user working-tree modifications remain present.

## Q. Login round-trip reduction and timing interpretation (2026-10-10, Asia/Kolkata)

### Findings

**Measured (user-supplied Chrome request, historical to this code change):** login returned 200 in about 11.52 s (`app` 11,507.5 ms; `db_connect` 5,250.7 ms; `driver_connect` 3,324.1 ms; three cursor statements 4,221.9 ms total; `SELECT users` 1,365.0 ms; `SELECT profiles` 1,481.2 ms; `UPDATE users` 1,375.4 ms; `auth_user_lookup` 2,934.6 ms; `bcrypt_verify` 617.5 ms; token/response phase 39.6 ms; release 0.2 ms). Request ID supplied: `f7ce533b-353d-4e86-844d-bd1a679f8283`. These are not independent durations: `driver_connect` is nested inside `db_connect`; `auth_user_lookup` wraps and overlaps the two SELECT timings; SQL, bcrypt, and token spans are in the overall app span. No fresh post-change browser result was available.

**Code-inspected:** `backend/app/repositories/user_repository.py` used `selectinload(User.profile)` in `get_by_email()`. That creates one `SELECT users` followed by a separate `SELECT profiles`. The profile is needed: `AuthService.login()` returns `TokenResponse.user`, whose `UserResponse` includes optional `ProfileResponse` (`backend/app/services/auth_service.py:64-83, 154-178`; `backend/app/schemas/auth.py:36-41`; `backend/app/schemas/user.py:25-35`). `User.profile` is `uselist=False`, and `profiles.user_id` is non-null and unique (`backend/app/models/user.py:51-70`), so an outer joined load preserves the optional relation while fetching it in the same SELECT.

**Code-inspected:** the third statement is required. `_issue_tokens()` creates a new refresh token, stores its SHA-256 hash in `users.refresh_token_hash`, and the request-scoped `get_db()` commits it. Refresh validates the stored hash against the presented token; logout clears it (`backend/app/services/auth_service.py:85-115, 154-178`). `TimestampMixin.updated_at` is also updated on ORM updates (`backend/app/models/base.py:19-25`). There is no explicit `last_login` field or separate last-login write. The refresh-token hash update and its timestamp side effect were retained.

**Code-inspected:** the frontend login handler consumes the user in the login response and sets tokens/user directly (`frontend/src/routes/login/+page.svelte:15-39`). `/auth/me` is called by the shared layout on mount when it finds an existing token (`frontend/src/routes/+layout.svelte:18-32`); SPA login navigation does not remount that root layout. The dashboard page has one `getHomeDashboard()` call in `onMount` (`frontend/src/routes/dashboard/+page.svelte:19-24`; API wrapper at `frontend/src/lib/api/analytics.ts:6`). Therefore the reviewed flow contains no `/auth/me` call after login and one dashboard call on dashboard mount. Network request counts remain **unverified** without a browser capture.

### Timing interpretation and limits

**Code-inspected:** `driver_connect` measures the `dialect.connect(*cargs, **cparams)` call; `db_connect` measures the full `await session.connection()` (`backend/app/core/database.py:79-102, 181-190`; `backend/app/core/performance.py:36-43`). The supplied sample leaves 1,926.6 ms between those nested measurements. SQLAlchemy creates the connection, then invokes pool `connect` listeners; its asyncpg dialect `on_connect` hook configures JSON and JSONB codecs (`backend/venv/Lib/site-packages/sqlalchemy/pool/base.py:894-915`; `backend/venv/Lib/site-packages/sqlalchemy/engine/create.py:713-724`; `backend/venv/Lib/site-packages/sqlalchemy/dialects/postgresql/asyncpg.py:1246-1262`). Those post-driver steps are inside `db_connect` but outside `driver_connect` and are a **code-inspected candidate** for some of the difference, not a measured attribution. SQLAlchemy adapter/pool setup is also within the broader boundary. The current instrumentation does not time each post-connect hook separately.

The 3,324.1 ms driver span cannot identify DNS, TCP, TLS, PostgreSQL authentication, or PgBouncer contribution. The three SQL cursor durations cover client-side cursor execution/round trip and result handling; they do not prove server execution time. Because `get_db()` establishes the connection before yielding the session, SQL execution occurs after `db_connect` completes; do not subtract/add SQL values to explain that connection interval. No live PostgreSQL plan or fresh dashboard `driver_connect` value was available. Dashboard timings (7.67 s user-supplied latest request; earlier separate 7.06 s app/3.87 s `db_connect` sample) are distinct observations and do not establish the same driver breakdown.

### Targeted change and validation

Changed `backend/app/repositories/user_repository.py` so `get_by_email()` uses `joinedload(User.profile)` for the existing one-to-one optional profile. This preserves returned user/profile fields, null-profile behavior, password verification, authentication rules, refresh-token rotation, and the database update. It reduces the login lookup from two sequential SELECTs to one joined SELECT in the generated query shape; the refresh-token UPDATE remains, so expected statement count is two. This is a code/query-shape result, **not a measured latency improvement**. Google account lookup also uses `get_by_email()` and retains the same loaded profile data.

Added `backend/tests/test_user_repository.py` to compile and assert the one-statement outer-join query and normalized email predicate. Added `backend/tests/test_auth_login.py` to exercise mocked login success (user/profile response and refresh-hash side effect) and wrong-password rejection (no token update). An async test using pytest's event loop could not start in this sandbox: faulthandler showed Windows asyncio blocked creating its self-pipe socket with the same socket-access restriction. The focused tests therefore use synchronous query compilation and immediate mocked service coroutines; they do not constitute a database or browser integration test.

- **Passed:** `backend\\venv\\Scripts\\python.exe -m pytest tests -q` — 5 passed.
- **Passed:** `backend\\venv\\Scripts\\python.exe -m compileall -q app tests`.
- **Passed:** `git diff --check` after the source/test edits (existing `.env.example` CRLF notices only).
- **Previously passed, frontend unchanged in this phase:** `npm run check`; production build succeeded on the sequential retry with the warnings recorded in Section P; upload polling tests 5/5.
- **Unverified:** actual PostgreSQL `EXPLAIN`, live login/dashboard after the joined load, response-body equality against populated data, and browser request counts. No DB probe or user data access was run.

**Files changed in this section:** `backend/app/repositories/user_repository.py` (login email lookup loader strategy), `backend/tests/test_user_repository.py` (query shape regression test), and `backend/tests/test_auth_login.py` (login success/failure regression tests). No pool, connection option, route, response schema, authentication rule, environment, dependency, schema, or data change was made.

### Next evidence

Capture five post-change login and dashboard requests from the authorized host-side browser, recording sanitized route, status, total duration, `X-Request-ID`, and full `Server-Timing`. Confirm login issues one login request, no `/auth/me`, and exactly one dashboard request. Compare the new login request's statement count and timings to the supplied 11.52-second sample, not to dashboard samples. To explain the 1,926.6 ms post-driver interval, add a narrowly scoped timer around the SQLAlchemy post-connect initialization path or obtain safe backend instrumentation for the pool `connect` hook; do not disable asyncpg codecs or change pooling based on the current aggregate. If query-plan validation is required before wider rollout, capture a read-only plan for the generated joined SELECT on the test account's existing database using an authorized host-side diagnostic.

## R. Login query and regression-validation follow-up (2026-10-10, Asia/Kolkata)

### Existing change and confirmed code facts

**Code-inspected:** `backend/app/repositories/user_repository.py` keeps the existing `get_by_email()` lookup as one `SELECT users LEFT OUTER JOIN profiles`, with email lowercasing, via `joinedload(User.profile)`. The one-to-one relationship is optional at the ORM level (`User.profile`, `uselist=False`), and `Profile.user_id` is unique and non-null. The outer join preserves a user row when no profile exists. `get_with_profile()` still uses `selectinload`; its behavior was not changed.

The login service still verifies the password, checks account activity, issues the same token pair, and saves the SHA-256 hash of the refresh token (`backend/app/services/auth_service.py`). The session commit persists that refresh-token rotation. Refresh still checks the stored hash before rotating; logout still clears it. The update is part of the existing revocation/rotation behavior and was not removed. The login path is expected from code shape to issue one joined lookup SELECT plus the refresh-token hash UPDATE. **No current live request captured the actual statement count**, so two statements are a code-derived expectation, not a fresh runtime measurement.

### Added focused regression coverage

Added an in-memory SQLite ORM test in `backend/tests/test_user_repository.py` that executes the joined statement shape with a user that has a profile and a user without one. It verifies both users load and the absent profile remains `None`. The database exists only in memory and is disposed after the test. Added refresh tests in `backend/tests/test_auth_login.py` for successful hash rotation and rejection of a previously rotated token without changing the current hash. Existing login tests continue to cover success/profile serialization/hash storage and wrong-password rejection.

### Validation results

- **Passed:** `backend\venv\Scripts\python.exe -m pytest tests -q` — **8 passed in 3.56s**. Pytest emitted the existing `pytest-asyncio` unset fixture-loop-scope deprecation warning.
- **Passed:** `backend\venv\Scripts\python.exe -m compileall -q app tests` — exit code 0.
- **Passed:** `node --test tests/upload-polling.test.mjs` — **5 passed, 0 failed**.
- **Passed:** `npm run check` — Svelte check found **0 errors and 0 warnings**.
- **Failed:** `npm run build` — Vite failed during output rendering after transforming 1,617 modules with `EPERM: operation not permitted, mkdir 'D:\AI GyanGuru\frontend\.svelte-kit\output\server\entries\pages\quiz'` (18.93s). No output cleanup, ACL change, process termination, or retry was performed. The build blocker is the write failure at that output path; its cause is not established by this run. Existing SvelteKit/Svelte export warnings also appeared before the failure.
- **Passed:** `git diff --check` — exit code 0; Git printed existing LF-to-CRLF notices for the two modified `.env.example` files.

### Runtime comparison and limitations

The attached in-app browser could open the frontend at `http://127.0.0.1:5173/`, but it was a fresh unauthenticated tab, not the user's existing authenticated Chrome session. No credentials were entered. Thus there are **zero fresh authenticated login or dashboard samples** in this follow-up: no browser total, current `X-Request-ID` / `Server-Timing`, SQL count, or request-count verification was obtained. No live PostgreSQL request, connection probe, query plan, or production data read was run.

Historical login values in prior sections remain historical: one supplied 11.52-second browser request showed 5,250.7 ms `db_connect` (including a nested 3,324.1 ms `driver_connect`), 4,221.9 ms over three SQL cursor spans, and 617.5 ms bcrypt verification. Those overlapping phases are not summed. The code change removes the second profile SELECT from the login lookup query shape, but no post-change runtime sample establishes whether the expected count is now two or whether latency improved. Existing `db_connect`/`driver_connect` gaps and cursor timings still cannot isolate database server execution, transport, or PgBouncer phases. No claim of faster login is made.

### Smallest next evidence

1. Resolve the build output-path `EPERM` by collecting a host-side file-handle/antivirus or filesystem trace for the exact `.svelte-kit\output\server\entries\pages\quiz` path on a subsequent authorized build attempt. Do not delete generated output or alter ACLs without that evidence.
2. From the already-authorized host Chrome session, capture one fresh login and dashboard Network entry with sanitized path, status, total duration, `X-Request-ID`, and complete `Server-Timing`; also confirm login produces no `/auth/me` request and one dashboard request. This execution has no access to that authenticated session.

**Files changed in this follow-up:** `backend/tests/test_user_repository.py`, `backend/tests/test_auth_login.py`, and this appended section in `PERFORMANCE_AUDIT.md`. No application source, dependency, environment, route, authentication, database setting, schema, or database content was changed in this follow-up. All prior working-tree modifications were preserved.

## S. Build EPERM investigation and runtime-capture preparation (2026-10-10, Asia/Kolkata)

### Build output path investigation

The prior Vite failure was `EPERM` while attempting `mkdir` for `frontend\\.svelte-kit\\output\\server\\entries\\pages\\quiz`. This follow-up inspected that exact target and each existing ancestor without changing generated files:

- `.svelte-kit`, `output`, `server`, `entries`, and `pages` all exist as directories; the target `pages\\quiz` does not currently exist as either a file or directory.
- The top `.svelte-kit` directory has the Windows `ReadOnly` attribute; its descendants inspected did not. Each existing ancestor showed zero explicit deny ACL entries. This is not a proof of effective process write access or evidence that the ReadOnly attribute caused the failure.
- `Get-Process node,npm` returned no matching processes in this execution context. CIM process inspection failed with “Access to a CIM resource was not available”; `tasklist` failed with “The user name or password is incorrect.” Therefore duplicate/out-of-scope Vite processes cannot be ruled out.
- `handle.exe` / `handle64.exe` were unavailable. Windows `openfiles /query` reported the local open-object list is not enabled and then “Access is denied.” `fltmc filters` also failed with access denied. No file-handle owner, antivirus/filter event, or process lock was identified.

**Conclusion:** the exact failed operation/path is known, but the cause of `EPERM` is **not established**. Existing directory types and ACL inspection did not reveal a specific blocker, and the ReadOnly attribute alone is not sufficient evidence. No build retry was made because no justified resolution was found. No `.svelte-kit`/`node_modules` deletion, permission change, security-software change, or process termination was performed.

### Login query verification for future measurement

**Code-inspected:** `backend/app/repositories/user_repository.py:20-31` builds the login lookup as one normalized-email `SELECT` with `joinedload(User.profile)` (outer join). `backend/app/services/auth_service.py:64-83,157-170` then verifies the password and assigns the newly issued refresh-token hash to the user; the request-scoped DB session commits that update. Refresh validates the stored hash and rotates it (`auth_service.py:85-111`), and logout clears it (`:113-115`). Therefore a successful login should issue one joined user/profile lookup plus the necessary refresh-token hash `UPDATE`, i.e. **two SQL statements expected by code inspection**. Actual runtime statement count remains unmeasured after this optimization.

### Browser capture checklist (user-operated authorized Chrome session)

1. Open the app in the already-authorized Chrome profile and open DevTools → **Network**. Enable **Preserve log**; clear the list before starting. Do not export a HAR or copy request payloads, cookies, authorization values, or credentials.
2. Submit one normal successful login. Select `POST /api/v1/auth/login`; record status and Chrome’s total **Duration**. In **Headers → Response Headers**, copy only `X-Request-ID` and the complete `Server-Timing` value. Do not copy Request Headers or request/response bodies.
3. Select the resulting `GET /api/v1/dashboard`; record status, total Duration, `X-Request-ID`, and full `Server-Timing` the same way. Record whether exactly one dashboard request occurred and whether an `/auth/me` request occurred between login and dashboard.
4. If timing copies are provided for correlation, retain each request’s own ID alongside its own metrics. Do not add nested `driver_connect` to `db_connect`; do not combine SQL/client timing with backend or browser time as though they were disjoint. Browser total duration and dashboard-visible render time are separate observations.

No authentication was attempted in this execution and no fresh browser timing or improvement claim is made.

### Validation in this follow-up

- **Passed:** `backend\\venv\\Scripts\\python.exe -m pytest tests -q` — **8 passed in 1.31s**; one existing `pytest-asyncio` loop-scope deprecation warning.
- **Passed:** `node --test tests/upload-polling.test.mjs` — **5 passed, 0 failed**.
- **Passed:** `git diff --check` — exit code 0; existing `.env.example` LF-to-CRLF notices only.
- **Not run:** Vite production build, because the inspected failure had no identified safe resolution to justify a retry.

No application source, dependencies, environment, auth, SQL, pool/database configuration, generated output, or persistent data were changed in this follow-up. The only file edited here is this appended audit section; prior working-tree modifications remain intact.

## T. Follow-up Windows resource-lock query (2026-10-10, Asia/Kolkata)

A new read-only Windows Restart Manager API query was attempted against the existing `frontend\\.svelte-kit\\output\\server\\entries\\pages` directory (the parent of the previously failed `quiz` directory). `RmStartSession` returned Win32 error code **29** before resource registration or process enumeration. The session was ended; no process was queried, stopped, or changed. This API path therefore produced no lock-owner evidence. Earlier checks already documented in Section S remain the available evidence; this follow-up did not repeat CIM, `tasklist`, `openfiles`, or `fltmc` checks.

The root cause remains unconfirmed, and no corrective action is justified. The Vite build was not retried. No generated files, permissions, dependencies, or processes were changed. The most useful next action is a host-side authorized Windows lock/handle trace (for example, an already-installed Process Explorer/handle diagnostic) taken while the exact failure is reproducible; absent access to that diagnostic, leave the build untouched. The existing Chrome Network capture checklist remains in Section S; no browser measurements were collected here.

- **Passed:** `git diff --check` — exit code 0; only the previously observed `.env.example` LF-to-CRLF notices.
- **Not run:** application tests; this follow-up changed no application code, and the relevant backend/polling test results are already recorded in Section S.

## U. Authenticated Chrome availability check (2026-10-10, Asia/Kolkata)

The browser inventory for this task exposed only the Codex in-app browser and Codex MCP Apps, both with zero open tabs; no Chrome browser/session was available to inspect. I did not open an unauthenticated replacement session, enter credentials, or interact with the application. Accordingly, this follow-up yielded **zero fresh login or dashboard samples** and no request-count, `/auth/me`, status, duration, `X-Request-ID`, or `Server-Timing` evidence. Use the user-operated capture steps already listed in Section S when the authorized Chrome profile is available.

The build cause remains unresolved from Section T; no build retry or repeated lock diagnostic was attempted. No source, generated output, environment, dependency, authentication, SQL, or database settings were changed. Application tests were not rerun because this follow-up changed no application code.

- **Passed:** `git diff --check` — exit code 0; existing `.env.example` LF-to-CRLF notices only.
- **Next evidence:** provide an available authorized Chrome session or capture the two Network entries manually using Section S. Do not include credentials, request bodies, cookies, or authorization values.
