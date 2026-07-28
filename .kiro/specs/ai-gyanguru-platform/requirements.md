# Requirements Document

## Introduction

AI GyanGuru is an enterprise-grade, AI-powered personal learning platform designed to help students, competitive exam aspirants, teachers, and self-learners study smarter. The platform enables users to learn any topic, generate AI-powered revision notes and detailed explanations, take adaptive quizzes, upload and analyze study materials, and track their learning progress — all from a single unified interface.

This is NOT a Learning Management System. AI GyanGuru is an intelligent personal learning assistant that combines AI-driven content generation, document processing, assessment, analytics, and progress tracking into one cohesive experience. The system is designed for production-grade scale, targeting millions of concurrent users, and follows clean architecture principles with a fully modular, provider-independent AI engine.

The platform is structured around four architectural layers:
- **Presentation Layer**: SvelteKit frontend with TailwindCSS and shadcn-svelte
- **Application Layer**: FastAPI backend with service-layer and repository patterns
- **AI Engine Layer**: Modular prompt engine, AI dispatcher, provider adapters, and response formatter
- **Data Layer**: Supabase (PostgreSQL + Auth + Storage), OCR engines, document processors

---

## Glossary

- **Platform**: The AI GyanGuru application as a whole
- **User**: Any authenticated individual using the Platform (Student, Aspirant, Teacher, Self-Learner)
- **Student**: A college or university student using the Platform for academic study
- **Aspirant**: A competitive exam aspirant using the Platform for exam preparation
- **Teacher**: An educator using the Platform to generate teaching materials
- **Guest**: An unauthenticated visitor to the Platform
- **Auth_Service**: The backend service responsible for user registration, login, OAuth, JWT issuance, and session management
- **User_Service**: The backend service responsible for user profile management
- **Summary_Service**: The backend service that generates AI-powered summaries, revision notes, and study aids
- **Explanation_Service**: The backend service that generates detailed, structured topic explanations
- **Quiz_Service**: The backend service that generates, delivers, and scores AI-powered quizzes
- **Analytics_Service**: The backend service that tracks, computes, and exposes learning analytics
- **History_Service**: The backend service that stores and retrieves user activity history
- **File_Service**: The backend service that manages file uploads, text extraction, and OCR pipelines
- **OCR_Service**: The backend service responsible for optical character recognition on images and scanned documents
- **Prompt_Service**: The backend service responsible for building structured prompts from templates and user inputs
- **AI_Orchestrator**: The backend component that dispatches prompts to AI providers and returns formatted responses
- **AI_Dispatcher**: The component within the AI Engine that routes requests to the configured AI provider adapter
- **Provider_Adapter**: A pluggable interface that wraps a specific AI provider (Groq, OpenAI, etc.)
- **Response_Formatter**: The component that normalizes and structures raw AI output into API-ready responses
- **Prompt_Template**: A versioned, parameterized prompt structure used by the Prompt_Service
- **Dashboard**: The main authenticated landing page showing overview, analytics, recent activity, and quick actions
- **Summary**: An AI-generated structured study aid including definitions, key concepts, facts, formulas, mnemonics, exam tips, and checklists
- **Explanation**: An AI-generated detailed breakdown of a topic including introduction, steps, examples, analogies, applications, mistakes, FAQs, and recap
- **Quiz**: A set of AI-generated multiple-choice questions with options, correct answers, explanations, difficulty, and category
- **Quiz_Attempt**: A single user session of answering a Quiz, including responses, score, and performance summary
- **Upload**: A user-submitted file (PDF, DOCX, TXT, or image) processed by the File_Service
- **Extracted_Text**: Raw text content obtained from an Upload via direct parsing or OCR
- **Analytics_Record**: A persisted data point tracking user learning activity, quiz accuracy, topic engagement, and study streaks
- **History_Record**: A persisted log entry linking a User to a past Summary, Explanation, Quiz_Attempt, or Upload
- **JWT**: JSON Web Token used for stateless authentication between the frontend and backend
- **OAuth**: Open Authorization protocol used for Google Login
- **RBAC**: Role-Based Access Control governing what each User role may access
- **Rate_Limiter**: The backend component that enforces per-user and per-IP request limits
- **API_Gateway**: The entry point for all client requests, responsible for routing, rate limiting, and authentication verification
- **OpenAPI_Spec**: The auto-generated REST API documentation served by the backend
- **Dark_Mode**: A UI theme variant using dark background colors
- **Light_Mode**: A UI theme variant using light background colors
- **Streaming_Response**: An AI response delivered incrementally via server-sent events rather than as a single payload

---

## Requirements

### Requirement 1: User Registration

**User Story:** As a Guest, I want to register for an account using my email and password, so that I can access personalized AI learning features.

#### Acceptance Criteria

1. WHEN a Guest submits a registration form with a valid email address, a password meeting minimum security criteria, and a display name, THE Auth_Service SHALL create a new User account and send an email verification link to the provided address.
2. WHEN a Guest submits a registration form with an email address already associated with an existing account, THE Auth_Service SHALL return an error response with HTTP status 409 and a message indicating the email is already registered.
3. WHEN a Guest submits a registration form with a password shorter than 8 characters or lacking at least one uppercase letter, one lowercase letter, and one digit, THE Auth_Service SHALL return a validation error with HTTP status 422 listing each violated constraint.
4. WHEN a Guest submits a registration form with a malformed email address, THE Auth_Service SHALL return a validation error with HTTP status 422 before any database operation is performed.
5. IF the email delivery service is unavailable during registration, THEN THE Auth_Service SHALL still create the User account, queue the verification email for retry, and return HTTP status 201 with a message advising the User to check their email within 15 minutes.
6. WHEN a User clicks a valid email verification link, THE Auth_Service SHALL mark the account as verified and redirect the User to the login page with a success notification.
7. WHEN a User clicks an email verification link that has expired (older than 24 hours), THE Auth_Service SHALL return an error page with an option to request a new verification link.

---

### Requirement 2: User Login

**User Story:** As a registered User, I want to log in using my email and password, so that I can access my personalized learning dashboard.

#### Acceptance Criteria

1. WHEN a User submits valid credentials (verified email and correct password), THE Auth_Service SHALL issue a signed JWT access token with a 1-hour expiry and a refresh token with a 7-day expiry, returning HTTP status 200.
2. WHEN a User submits an incorrect password, THE Auth_Service SHALL return HTTP status 401 and increment a failed-attempt counter for that account.
3. WHEN a User accumulates 5 consecutive failed login attempts within a 15-minute window, THE Auth_Service SHALL lock the account for 15 minutes and return HTTP status 429 with a message indicating the lockout duration.
4. WHEN a User submits credentials for an unverified account, THE Auth_Service SHALL return HTTP status 403 and offer to resend the verification email.
5. WHEN an authenticated User's JWT access token expires, THE Auth_Service SHALL accept the refresh token and issue a new access token without requiring the User to log in again.
6. WHEN a User submits an expired or invalid refresh token, THE Auth_Service SHALL return HTTP status 401 and require the User to log in again.
7. WHEN a logged-in User requests logout, THE Auth_Service SHALL invalidate the refresh token server-side and return HTTP status 200.

---

### Requirement 3: Google OAuth Login

**User Story:** As a Guest, I want to sign in using my Google account, so that I can access the platform without creating a separate password.

#### Acceptance Criteria

1. WHEN a Guest initiates Google OAuth login and grants consent, THE Auth_Service SHALL exchange the authorization code for tokens, create or retrieve the associated User account, and return a JWT access token and refresh token with HTTP status 200.
2. WHEN a Guest completes Google OAuth login for the first time, THE Auth_Service SHALL automatically create a User profile using the name and email provided by Google and redirect the User to a profile completion page.
3. WHEN a User with an existing email-password account initiates Google OAuth using the same email, THE Auth_Service SHALL link the Google identity to the existing account without creating a duplicate.
4. IF Google's OAuth endpoint returns an error or the User denies consent, THEN THE Auth_Service SHALL redirect the User to the login page with an informative error message and return HTTP status 400.
5. WHEN a Google OAuth session token is revoked on Google's side, THE Auth_Service SHALL detect the invalidity on the next API call and require the User to re-authenticate.

---

### Requirement 4: Session Management and JWT Security

**User Story:** As a User, I want my session to remain secure and automatically renewed, so that I am not interrupted during active learning sessions.

#### Acceptance Criteria

1. THE Auth_Service SHALL sign all JWT access tokens using RS256 asymmetric signing with a minimum 2048-bit key.
2. THE Auth_Service SHALL embed the User's role, user_id, and token expiry in the JWT payload.
3. WHEN an API request is received with a JWT, THE API_Gateway SHALL validate the token signature, expiry, and issuer before forwarding the request to any backend service.
4. WHEN an API request is received without a JWT or with a malformed JWT, THE API_Gateway SHALL return HTTP status 401 before forwarding the request.
5. THE Auth_Service SHALL rotate refresh tokens on each use, invalidating the previous refresh token immediately.
6. WHEN a User logs in from a new device or browser, THE Auth_Service SHALL record the new session and send a security notification email to the User's registered address.
7. THE Auth_Service SHALL maintain a server-side denylist for revoked tokens and check incoming tokens against it on each request.

---

### Requirement 5: User Profile Management

**User Story:** As a User, I want to manage my profile including avatar, display name, and learning preferences, so that the platform can personalize my experience.

#### Acceptance Criteria

1. WHEN a User submits a profile update with a new display name, THE User_Service SHALL validate that the name is between 2 and 60 characters, persist the change, and return HTTP status 200 with the updated profile.
2. WHEN a User uploads a profile avatar image, THE User_Service SHALL validate that the file is JPEG, PNG, or WebP format, does not exceed 5 MB, resize it to a maximum of 512x512 pixels, store it in Supabase Storage, and update the User's avatar URL.
3. WHEN a User submits a profile update with an invalid avatar format or size exceeding the limit, THE User_Service SHALL return HTTP status 422 with a descriptive error message without modifying any data.
4. WHEN a User updates their learning preferences (preferred topics, difficulty level, daily study goal in minutes), THE User_Service SHALL persist the preferences and return HTTP status 200.
5. THE User_Service SHALL expose a GET endpoint that returns the authenticated User's full profile including display name, avatar URL, email (masked), role, account creation date, and learning preferences.
6. WHEN a User requests account deletion, THE User_Service SHALL anonymize all personally identifiable information, retain anonymized analytics data, and return HTTP status 200 with a confirmation message.

---

### Requirement 6: Dashboard

**User Story:** As a User, I want a central dashboard showing my learning overview, recent activity, and quick action shortcuts, so that I can immediately continue or start learning upon login.

#### Acceptance Criteria

1. WHEN an authenticated User navigates to the Dashboard, THE Platform SHALL display the User's display name, total topics studied, cumulative quiz accuracy percentage, current study streak in days, and total study time in minutes within 2 seconds.
2. WHEN an authenticated User navigates to the Dashboard, THE Platform SHALL display the 5 most recent History_Records including type (Summary, Explanation, Quiz_Attempt, or Upload), topic name, and timestamp.
3. WHEN an authenticated User navigates to the Dashboard and has no History_Records, THE Platform SHALL display an onboarding prompt with suggested starter topics and quick-action buttons for generating a first Summary or Explanation.
4. THE Dashboard SHALL provide quick-action buttons that navigate the User to the Summary Module, Explanation Module, Quiz Module, and File Upload interface.
5. WHEN an authenticated User navigates to the Dashboard, THE Platform SHALL display a weekly activity chart showing daily study minutes for the past 7 days, rendered using Chart.js.
6. WHEN an authenticated User navigates to the Dashboard and has at least one Quiz_Attempt, THE Platform SHALL display top 3 strong subject areas and top 3 weak subject areas derived from the User's Analytics_Records.
7. THE Dashboard SHALL render correctly on desktop (≥1024px), tablet (768px–1023px), and mobile (320px–767px) viewports without horizontal scrolling.

---

### Requirement 7: AI-Powered Summary Generation

**User Story:** As a User, I want to enter a topic and receive a structured AI-generated summary, so that I can quickly revise key concepts without reading lengthy notes.

#### Acceptance Criteria

1. WHEN a User submits a topic name (minimum 3 characters, maximum 200 characters) to the Summary Module, THE Summary_Service SHALL build a structured prompt via the Prompt_Service, dispatch it to the AI_Orchestrator, and return a formatted Summary within 15 seconds.
2. THE Summary_Service SHALL return a Summary containing all of the following sections: Definitions, Key Concepts, Important Facts, Formula Sheet (where applicable), Mnemonics, Exam Tips, Revision Notes, and a Checklist of subtopics.
3. WHEN a User submits a topic with fewer than 3 characters, THE Summary_Service SHALL return HTTP status 422 with a validation error before invoking the AI_Orchestrator.
4. IF the AI_Orchestrator returns an error or times out after 30 seconds, THEN THE Summary_Service SHALL return HTTP status 503 with a user-friendly error message and log the failure with the request metadata.
5. WHEN the Summary_Service returns a successful response, THE Summary_Service SHALL persist the Summary to the database, create a corresponding History_Record, and update the User's Analytics_Record with the topic and timestamp.
6. WHEN a User requests a Summary for a topic they have studied before, THE Summary_Service SHALL return the previously generated Summary from the database within 1 second, with an option to regenerate using fresh AI output.
7. THE Summary_Service SHALL support streaming the AI response to the frontend via server-sent events so that content appears incrementally rather than after a full generation delay.
8. WHERE a User has set a preferred difficulty level in their profile, THE Summary_Service SHALL include the difficulty preference as a parameter in the Prompt_Template to adjust content complexity.

---

### Requirement 8: AI-Powered Explanation Generation

**User Story:** As a User, I want to enter a topic and receive a detailed, structured explanation with examples and analogies, so that I can deeply understand concepts rather than just memorize them.

#### Acceptance Criteria

1. WHEN a User submits a topic name (minimum 3 characters, maximum 200 characters) to the Explanation Module, THE Explanation_Service SHALL build a structured prompt via the Prompt_Service, dispatch it to the AI_Orchestrator, and return a formatted Explanation within 20 seconds.
2. THE Explanation_Service SHALL return an Explanation containing all of the following sections: Introduction, Step-by-Step Explanation, Concept Breakdown, Real-World Examples, Analogies, Practical Applications, Common Mistakes, FAQs (minimum 3 questions), and Final Recap.
3. WHEN a User submits a topic with fewer than 3 characters, THE Explanation_Service SHALL return HTTP status 422 with a validation error before invoking the AI_Orchestrator.
4. IF the AI_Orchestrator returns an error or times out after 30 seconds, THEN THE Explanation_Service SHALL return HTTP status 503 with a user-friendly error message and log the failure.
5. WHEN the Explanation_Service returns a successful response, THE Explanation_Service SHALL persist the Explanation to the database, create a corresponding History_Record, and update the User's Analytics_Record.
6. THE Explanation_Service SHALL support streaming the AI response via server-sent events so that each section renders progressively on the frontend.
7. WHEN a User requests an Explanation for a topic already in their History_Records, THE Explanation_Service SHALL surface the cached version within 1 second with an option to regenerate.
8. WHERE a User's profile specifies a target exam (e.g., GATE, UPSC, JEE), THE Explanation_Service SHALL include the exam context in the Prompt_Template to tailor examples and depth accordingly.

---

### Requirement 9: AI Quiz Generation

**User Story:** As a User, I want to generate a topic-specific quiz with multiple-choice questions, so that I can test my understanding and identify knowledge gaps.

#### Acceptance Criteria

1. WHEN a User submits a topic name and a requested question count (between 5 and 50) to the Quiz Module, THE Quiz_Service SHALL generate a Quiz via the AI_Orchestrator and return it within 20 seconds.
2. THE Quiz_Service SHALL ensure each generated quiz question contains: a question stem, exactly 4 answer options labeled A through D, the correct option identifier, a detailed explanation of the correct answer, a difficulty level (Easy, Medium, or Hard), and a subject category.
3. WHEN the AI_Orchestrator returns fewer questions than requested, THE Quiz_Service SHALL log a warning, return the available questions, and notify the User of the reduced count in the response metadata.
4. WHEN a User submits a question count below 5 or above 50, THE Quiz_Service SHALL return HTTP status 422 with a descriptive validation error.
5. IF the AI_Orchestrator fails or times out generating a Quiz, THEN THE Quiz_Service SHALL return HTTP status 503 and log the failure with full request context.
6. THE Quiz_Service SHALL persist each generated Quiz and its questions to the database, associating them with the requesting User and topic.
7. WHERE a User has previous Quiz_Attempts on the same topic, THE Quiz_Service SHALL bias question generation toward the User's previously identified weak areas by including weak category data in the Prompt_Template.

---

### Requirement 10: Quiz Interface and Navigation

**User Story:** As a User, I want an interactive quiz interface with navigation controls, progress tracking, and the ability to review answers, so that I can complete assessments efficiently.

#### Acceptance Criteria

1. WHEN a User starts a Quiz, THE Platform SHALL display one question at a time with the question stem, four labeled options, a progress indicator showing current question number and total, an elapsed timer, and Previous/Next navigation buttons.
2. WHEN a User selects an answer option, THE Platform SHALL visually highlight the selected option and enable the Next button without submitting the answer immediately.
3. WHEN a User clicks Previous, THE Platform SHALL navigate to the prior question and retain the User's previously selected answer for that question.
4. WHEN a User reaches the final question and clicks Submit, THE Platform SHALL require confirmation before submitting the Quiz_Attempt.
5. WHEN a User confirms submission, THE Quiz_Service SHALL score the attempt, persist the Quiz_Attempt record with all responses, and return a results payload within 3 seconds.
6. THE Quiz_Service SHALL calculate and return: total score, percentage correct, count of correct answers, count of incorrect answers, count of skipped questions, a per-question breakdown showing the User's answer, the correct answer, and the explanation, and an overall performance summary label (Excellent ≥80%, Good 60–79%, Needs Improvement <60%).
7. WHEN a User views Quiz results, THE Platform SHALL display all of the above metrics in a structured results page with an option to retake the quiz or return to the Dashboard.
8. THE Platform SHALL allow a User to flag any quiz question for review during the quiz, and THE Quiz_Service SHALL include flagged question IDs in the Quiz_Attempt record.

---

### Requirement 11: File Upload and Processing Pipeline

**User Story:** As a User, I want to upload study materials in PDF, DOCX, TXT, or image formats, so that the AI can analyze the content and generate summaries or explanations from my own documents.

#### Acceptance Criteria

1. WHEN a User uploads a file, THE File_Service SHALL accept PDF, DOCX, TXT, JPEG, PNG, and WebP formats with a maximum individual file size of 25 MB.
2. WHEN a User uploads a file in an unsupported format or exceeding the size limit, THE File_Service SHALL return HTTP status 422 with a clear error message specifying the constraint violated, without storing any file data.
3. WHEN a User uploads a valid PDF or DOCX file, THE File_Service SHALL extract raw text using PyMuPDF (for PDF) or python-docx (for DOCX) and store the Extracted_Text linked to the Upload record.
4. WHEN a User uploads an image file (JPEG, PNG, or WebP), THE File_Service SHALL pass the image to the OCR_Service, which SHALL use PaddleOCR to extract text, and store the Extracted_Text linked to the Upload record.
5. IF the OCR_Service fails to extract any text from an uploaded image, THEN THE File_Service SHALL fall back to Tesseract OCR, and IF both OCR engines fail, THEN THE File_Service SHALL return HTTP status 422 with a message indicating that no readable text was found.
6. WHEN text extraction succeeds, THE File_Service SHALL pass the Extracted_Text to the Prompt_Service to build a content-analysis prompt, dispatch it to the AI_Orchestrator, and return an AI-generated Summary of the uploaded document to the User within 60 seconds of upload.
7. WHEN a file upload and processing pipeline completes successfully, THE File_Service SHALL persist the Upload record (filename, file type, storage URL, extracted text length, processing status), create a History_Record, and update the User's Analytics_Record.
8. WHEN a User requests a list of their uploaded files, THE File_Service SHALL return a paginated list of Upload records sorted by upload date descending, with 20 items per page by default.
9. THE File_Service SHALL store uploaded files in Supabase Storage with a unique path per User and per Upload to prevent collisions.
10. WHILE a file is being processed, THE Platform SHALL display a real-time processing status indicator showing the current pipeline stage (Uploading, Extracting Text, Analyzing, Complete).

---

### Requirement 12: AI Engine — Prompt Building and Template Management

**User Story:** As a platform operator, I want the AI prompt construction to be fully modular and template-driven, so that prompt quality can be improved independently of application logic.

#### Acceptance Criteria

1. THE Prompt_Service SHALL construct all AI prompts from versioned Prompt_Templates parameterized with user-provided inputs (topic, difficulty, exam target, extracted text, weak areas) without embedding prompt logic in service-layer code.
2. THE Prompt_Service SHALL maintain separate Prompt_Templates for each module: Summary, Explanation, Quiz, and Document Analysis.
3. WHEN a new Prompt_Template version is deployed, THE Prompt_Service SHALL use the new version for all subsequent requests without requiring a service restart, and SHALL log which template version was used for each AI request.
4. THE Prompt_Service SHALL validate that all required template parameters are present before dispatching a prompt, returning a 500-level internal error if required parameters are missing.
5. FOR ALL AI requests processed by the Prompt_Service, the built prompt, template version, and final token count estimate SHALL be stored in the AI_Requests table for auditability.

---

### Requirement 13: AI Engine — Provider Independence and Dispatching

**User Story:** As a platform operator, I want the AI provider to be swappable without changing application logic, so that I can adopt the best model or provider as the market evolves.

#### Acceptance Criteria

1. THE AI_Dispatcher SHALL route all prompt requests to the currently configured Provider_Adapter without any service-layer code referencing a specific provider directly.
2. THE Platform SHALL ship with a Groq Provider_Adapter supporting the Llama 3.x, DeepSeek R1, Gemma, and Mixtral model families as the default configuration.
3. WHEN the configured AI provider's API returns a rate-limit error (HTTP 429), THE AI_Dispatcher SHALL implement exponential backoff with a maximum of 3 retries before returning an error to the calling service.
4. WHEN a new Provider_Adapter is registered in the configuration, THE AI_Dispatcher SHALL use the new adapter for all subsequent requests without modifying any other component.
5. THE Response_Formatter SHALL normalize all provider-specific response structures into a single internal schema before returning results to the calling service, ensuring service-layer code is never exposed to provider-specific formats.
6. WHEN the AI_Orchestrator completes a request, THE AI_Orchestrator SHALL persist the raw provider response, model name, token usage, latency in milliseconds, and final formatted output to the AI_Responses table.
7. IF the primary AI provider is unavailable and a fallback provider is configured, THEN THE AI_Dispatcher SHALL automatically retry the request using the fallback Provider_Adapter and log the failover event.

---

### Requirement 14: Learning Analytics

**User Story:** As a User, I want to view detailed analytics about my study habits, quiz performance, and knowledge gaps, so that I can make informed decisions about where to focus my study time.

#### Acceptance Criteria

1. WHEN an authenticated User accesses the Analytics page, THE Analytics_Service SHALL return the following metrics computed from the User's Analytics_Records: total topics studied, total quiz questions answered, overall quiz accuracy percentage, daily study activity for the past 30 days, top 5 most-studied topics, and top 5 weakest topics by quiz accuracy.
2. THE Analytics_Service SHALL update a User's Analytics_Records in real time upon completion of any Summary generation, Explanation generation, Quiz_Attempt, or file upload processing.
3. WHEN an authenticated User views the Analytics page, THE Platform SHALL render a bar chart of daily study activity, a pie chart of topic distribution, and a line chart of quiz accuracy trend over the past 30 days using Chart.js.
4. THE Analytics_Service SHALL compute a study streak (consecutive days with at least one learning activity) and expose it in the analytics response.
5. WHEN a User has a study streak of 7 days or more, THE Platform SHALL display a streak badge on the Dashboard.
6. THE Analytics_Service SHALL classify each studied topic into strong (≥80% quiz accuracy) or weak (<60% quiz accuracy) areas and expose these classifications in the analytics response.
7. WHEN an authenticated User has no analytics data, THE Analytics_Service SHALL return an empty analytics payload with HTTP status 200 rather than an error, and THE Platform SHALL display an encouraging prompt to begin studying.
8. THE Analytics_Service SHALL expose a history timeline endpoint returning a paginated list of all learning events (Summaries, Explanations, Quiz_Attempts, Uploads) sorted by timestamp descending with 20 items per page.

---

### Requirement 15: Learning History

**User Story:** As a User, I want to browse my complete history of summaries, explanations, quizzes, and uploaded files, so that I can revisit and reuse previously generated content.

#### Acceptance Criteria

1. WHEN an authenticated User accesses the History page, THE History_Service SHALL return a paginated list of all History_Records for that User sorted by creation timestamp descending, with 20 records per page by default.
2. WHEN a User requests a History_Record of type Summary or Explanation, THE History_Service SHALL return the full persisted content of that record within 1 second.
3. WHEN a User requests a History_Record of type Quiz_Attempt, THE History_Service SHALL return the quiz topic, score, percentage, date, and a link to the detailed results page.
4. WHEN a User requests a History_Record of type Upload, THE History_Service SHALL return the filename, upload date, file type, processing status, and the AI-generated analysis result.
5. WHEN a User deletes a History_Record, THE History_Service SHALL remove the record and its associated AI-generated content from the User's visible history within 2 seconds and return HTTP status 200.
6. THE History_Service SHALL support filtering History_Records by type (Summary, Explanation, Quiz_Attempt, Upload) and by date range.
7. THE History_Service SHALL support full-text search across stored Summary and Explanation content for the authenticated User, returning matching records ranked by relevance.

---

### Requirement 16: Role-Based Access Control

**User Story:** As a platform operator, I want different user roles to have distinct permissions, so that access to features is appropriate to each role.

#### Acceptance Criteria

1. THE Platform SHALL support the following roles: Student, Aspirant, Teacher, and Admin, each with a defined permission set enforced at the API_Gateway level.
2. WHILE a User holds the Student or Aspirant role, THE API_Gateway SHALL permit access to Summary, Explanation, Quiz, Analytics, History, and File Upload endpoints.
3. WHILE a User holds the Teacher role, THE API_Gateway SHALL permit all Student permissions plus access to bulk content generation endpoints (generating multiple Summaries or Quizzes in a single request).
4. WHILE a User holds the Admin role, THE API_Gateway SHALL permit all Teacher permissions plus access to user management, platform analytics, prompt template management, and AI provider configuration endpoints.
5. WHEN a User attempts to access an endpoint outside their role's permission set, THE API_Gateway SHALL return HTTP status 403 with a message indicating insufficient permissions.
6. THE Auth_Service SHALL default all newly registered Users to the Student role.
7. WHEN an Admin changes a User's role, THE Auth_Service SHALL invalidate all active sessions for that User, requiring re-login to receive a JWT with the updated role claim.

---

### Requirement 17: API Design and Documentation

**User Story:** As a developer integrating with AI GyanGuru, I want a well-structured REST API with OpenAPI documentation, so that I can understand and consume all endpoints reliably.

#### Acceptance Criteria

1. THE Platform SHALL expose all backend functionality through versioned REST API endpoints under the path prefix `/api/v1/`.
2. THE Platform SHALL serve an interactive OpenAPI specification at `/api/v1/docs` generated automatically from FastAPI route definitions and Pydantic models.
3. THE Platform SHALL return consistent error response bodies with the fields: `error_code` (machine-readable string), `message` (human-readable string), `details` (array of field-level errors when applicable), and `request_id` (UUID for tracing) for all 4xx and 5xx responses.
4. THE Platform SHALL support pagination on all list endpoints via `page` and `page_size` query parameters, returning a response envelope with `data`, `total`, `page`, `page_size`, and `total_pages` fields.
5. THE Platform SHALL support filtering on list endpoints via query parameters specific to each resource (e.g., `type`, `from_date`, `to_date`, `topic`).
6. THE Platform SHALL return appropriate HTTP status codes: 200 for successful reads, 201 for successful creates, 204 for successful deletes, 400 for bad requests, 401 for unauthenticated requests, 403 for forbidden requests, 404 for not found, 409 for conflicts, 422 for validation errors, 429 for rate limit exceeded, and 503 for service unavailable.
7. THE Platform SHALL include a `request_id` header in every API response for distributed tracing.

---

### Requirement 18: Rate Limiting

**User Story:** As a platform operator, I want per-user and per-IP rate limits enforced on all API endpoints, so that the platform remains available for all users and abuse is prevented.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce a maximum of 60 API requests per authenticated User per minute across all endpoints.
2. THE Rate_Limiter SHALL enforce a maximum of 20 AI-generation requests (Summary, Explanation, Quiz) per authenticated User per hour.
3. THE Rate_Limiter SHALL enforce a maximum of 10 API requests per minute per unauthenticated IP address on public endpoints.
4. WHEN a User exceeds a rate limit, THE Rate_Limiter SHALL return HTTP status 429 with a `Retry-After` header specifying the number of seconds until the limit resets.
5. THE Rate_Limiter SHALL include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers in all API responses for authenticated Users.
6. WHERE a User holds the Admin role, THE Rate_Limiter SHALL apply a separate, higher limit tier of 200 requests per minute and 100 AI-generation requests per hour.

---

### Requirement 19: Security — Input Validation and Injection Protection

**User Story:** As a platform operator, I want all user inputs sanitized and validated before processing, so that the platform is protected against injection attacks and malicious payloads.

#### Acceptance Criteria

1. THE Platform SHALL validate all incoming request bodies and query parameters against Pydantic schemas before any business logic is executed, returning HTTP status 422 for any schema violation.
2. THE Platform SHALL use parameterized SQL queries through SQLAlchemy ORM for all database operations, never constructing SQL strings via string interpolation.
3. THE Platform SHALL sanitize all user-submitted text inputs (topic names, display names, free-text fields) by stripping HTML tags and null bytes before storage or prompt injection.
4. WHEN a User submits a file upload, THE File_Service SHALL validate the file's MIME type by inspecting file headers (magic bytes), not only the filename extension, before processing.
5. THE Platform SHALL enforce a maximum payload size of 10 MB for all non-file API requests and return HTTP status 413 for oversized payloads.
6. THE Platform SHALL set the following HTTP security headers on all responses: `Content-Security-Policy`, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, and `Referrer-Policy: no-referrer`.

---

### Requirement 20: Security — Secrets and Configuration Management

**User Story:** As a platform operator, I want all secrets and credentials managed securely, so that sensitive configuration is never exposed in source code or logs.

#### Acceptance Criteria

1. THE Platform SHALL load all secrets (database URLs, API keys, JWT signing keys, OAuth client secrets) exclusively from environment variables or a secrets manager, never from hardcoded values in source code.
2. THE Platform SHALL never log secret values, JWT tokens, passwords, or OAuth tokens at any log level.
3. THE Platform SHALL use separate environment configurations for development, staging, and production environments with no shared secrets between environments.
4. WHEN an AI provider API key is rotated, THE Platform SHALL support updating the key via environment variable reload or secrets manager without a full application restart.
5. THE Platform SHALL validate that all required environment variables are present at startup and SHALL refuse to start if any required secret is missing, logging a descriptive error message.

---

### Requirement 21: Performance — Response Times and Caching

**User Story:** As a User, I want the platform to respond quickly to all interactions, so that my learning flow is never interrupted by slow load times.

#### Acceptance Criteria

1. THE Platform SHALL serve all non-AI static pages (Dashboard, History, Analytics) with a Time to First Byte (TTFB) of under 200ms under normal load (up to 1,000 concurrent users).
2. THE Platform SHALL serve previously cached AI-generated content (Summaries, Explanations) from the database within 1 second without invoking the AI_Orchestrator.
3. THE Platform SHALL implement database query result caching for Analytics_Service endpoints with a cache TTL of 60 seconds to reduce repeated identical queries.
4. THE Platform SHALL use database indexes on all foreign key columns, timestamp columns, and user_id columns used in frequent query patterns.
5. THE Platform SHALL implement lazy loading and code splitting in the SvelteKit frontend so that the initial JavaScript bundle size does not exceed 200 KB gzipped.
6. THE Platform SHALL support HTTP response compression (gzip or Brotli) for all text-based API responses exceeding 1 KB.

---

### Requirement 22: Performance — Background Tasks and Streaming

**User Story:** As a User, I want long-running AI tasks to not block the UI, and I want to see AI-generated content streaming in progressively, so that I have continuous visual feedback.

#### Acceptance Criteria

1. THE Platform SHALL process file upload OCR and AI analysis as a background task, returning an immediate HTTP 202 Accepted response with a task_id and a polling endpoint.
2. WHEN a User polls the task status endpoint with a valid task_id, THE Platform SHALL return the current processing stage and estimated completion time.
3. WHEN a background processing task completes, THE Platform SHALL deliver a browser notification (if the User has granted permission) and update the UI status without requiring a page refresh.
4. THE Summary_Service and Explanation_Service SHALL deliver AI-generated text to the frontend via server-sent events, with each event containing an incremental text chunk, so the User begins reading content within 2 seconds of submission.
5. WHEN a Streaming_Response connection is dropped before completion, THE Platform SHALL log the disconnection and make the partial content retrievable from the History_Service if at least 50% of the content was delivered.

---

### Requirement 23: UI — Theming, Responsiveness, and Accessibility

**User Story:** As a User, I want the platform to be visually consistent, responsive across devices, and accessible, so that I can study comfortably regardless of my device or accessibility needs.

#### Acceptance Criteria

1. THE Platform SHALL support Dark_Mode and Light_Mode with a toggle control accessible from every page, persisting the User's theme preference in local storage and their profile.
2. THE Platform SHALL render all pages without layout breakage on viewport widths from 320px (mobile) to 2560px (large desktop).
3. THE Platform SHALL achieve a Lighthouse accessibility score of 90 or above on all major pages (Dashboard, Summary, Explanation, Quiz, Analytics, History).
4. THE Platform SHALL ensure all interactive elements (buttons, inputs, links, modals) are keyboard-navigable with visible focus indicators.
5. THE Platform SHALL provide ARIA labels for all icon-only buttons and non-decorative images.
6. THE Platform SHALL render all text content with a minimum contrast ratio of 4.5:1 (WCAG AA) in both Light_Mode and Dark_Mode.
7. THE Platform SHALL display loading skeleton screens during data fetch operations rather than empty states, to reduce perceived latency.
8. THE Platform SHALL use smooth CSS transitions (duration 150ms–300ms) for page navigations, modal appearances, and theme switches without causing layout shifts.

---

### Requirement 24: Database Schema Integrity

**User Story:** As a platform operator, I want the database to enforce referential integrity and include all necessary tables for current and near-future features, so that data remains consistent as the platform grows.

#### Acceptance Criteria

1. THE Platform SHALL manage all database schema changes via Alembic migrations, with no manual schema alterations applied directly to the database.
2. THE Platform's database schema SHALL include the following tables at launch: Users, Profiles, Uploads, Summaries, Explanations, Quiz, Quiz_Questions, Quiz_Attempts, Analytics, History, AI_Requests, AI_Responses.
3. THE Platform's database schema SHALL include the following tables provisioned but empty for future use: Flashcards, Study_Plans, Goals, Chat_History, Notifications.
4. THE Platform SHALL enforce foreign key constraints between all related tables (e.g., Summaries.user_id references Users.id).
5. THE Platform SHALL use UUIDs as primary keys for all tables to support future horizontal sharding.
6. THE Platform SHALL store all timestamps in UTC using the TIMESTAMPTZ PostgreSQL type.
7. THE Platform SHALL implement soft deletes on User-owned content (Summaries, Explanations, Quiz_Attempts, Uploads) by setting a `deleted_at` timestamp rather than removing rows.

---

### Requirement 25: Scalability and Modularity

**User Story:** As a platform operator, I want every module and integration point to be independently replaceable, so that the platform can scale from thousands to millions of users without architectural rewrites.

#### Acceptance Criteria

1. THE Platform's AI Engine components (Prompt_Service, AI_Dispatcher, Provider_Adapter, Response_Formatter) SHALL each be independently testable and deployable without modifying any other component.
2. THE Platform SHALL support swapping the OCR engine (PaddleOCR or Tesseract) via configuration without modifying service-layer code.
3. THE Platform SHALL support swapping the file storage provider (Supabase Storage or any S3-compatible service) via a storage adapter interface without modifying service-layer code.
4. THE Platform SHALL support swapping the database backend via SQLAlchemy's dialect abstraction without modifying repository-layer code.
5. THE Platform SHALL expose health-check endpoints at `/health` (liveness) and `/health/ready` (readiness) that verify connectivity to the database, storage, and AI provider, returning HTTP status 200 when all dependencies are healthy or HTTP status 503 with a dependency list when any are unavailable.
6. THE Platform's backend services SHALL be structured so that each service (Auth_Service, Summary_Service, etc.) can be extracted into an independent microservice in a future phase without modifying the domain logic.

---

### Requirement 26: Error Handling and Observability

**User Story:** As a platform operator, I want comprehensive error handling, structured logging, and request tracing, so that issues can be diagnosed and resolved quickly in production.

#### Acceptance Criteria

1. THE Platform SHALL catch all unhandled exceptions in the backend, return a generic HTTP 500 response to the client, and log the full stack trace with the request_id, user_id, endpoint, and timestamp.
2. THE Platform SHALL use structured JSON logging for all backend log output, including fields: timestamp, level, service, request_id, user_id, message, and duration_ms where applicable.
3. THE Platform SHALL log all AI provider requests and responses at DEBUG level, redacting any personally identifiable information from log entries.
4. THE Platform SHALL generate a unique UUID request_id for every inbound API request, propagate it through all service calls, include it in all log entries for that request, and return it in the API response header.
5. THE Platform SHALL track and expose a `/metrics` endpoint (Prometheus-compatible format) with counters for: total requests, error rates by status code, AI generation latency histograms, and active sessions.
6. IF a database query exceeds 1 second, THEN THE Platform SHALL log a slow-query warning with the query duration and the endpoint that triggered it.

---

### Requirement 27: Personalized Learning Recommendations

**User Story:** As a User, I want to receive topic recommendations based on my study history and quiz performance, so that I am guided toward the most impactful areas for improvement.

#### Acceptance Criteria

1. WHEN an authenticated User has at least 5 History_Records, THE Analytics_Service SHALL derive and return a list of up to 5 recommended next topics based on the User's studied topics, weak areas (quiz accuracy <60%), and the time since each topic was last studied.
2. THE Analytics_Service SHALL surface recommendations on the Dashboard immediately below the quick-action buttons.
3. WHEN a User dismisses a recommendation, THE Analytics_Service SHALL mark it as dismissed and not resurface it for 7 days.
4. WHEN a User has fewer than 5 History_Records, THE Dashboard SHALL display a curated list of popular starter topics rather than personalized recommendations.
5. THE Analytics_Service SHALL refresh recommendations at most once per hour per User to avoid excessive computation, serving cached recommendations between refreshes.

---

### Requirement 28: Notification Service

**User Story:** As a User, I want to receive relevant notifications about completed background tasks, security events, and study reminders, so that I am kept informed without having to actively check the platform.

#### Acceptance Criteria

1. WHEN a file upload background task completes, THE Notification_Service SHALL deliver a browser push notification (if permission is granted) and an in-app notification within 5 seconds of task completion.
2. WHEN a security event occurs (new device login, password change, account lock), THE Notification_Service SHALL send an email notification to the User's registered address within 2 minutes.
3. WHERE a User has set a daily study reminder in their profile preferences, THE Notification_Service SHALL deliver a browser push notification at the User's configured time if they have not yet completed any learning activity that day.
4. WHEN a User marks an in-app notification as read, THE Notification_Service SHALL update the notification status to read and return HTTP status 200.
5. THE Notification_Service SHALL maintain an in-app notification inbox accessible from the navigation bar, displaying unread count as a badge.
6. WHEN a User has more than 100 unread notifications, THE Notification_Service SHALL cap the badge display at "99+" to prevent overflow.

---

### Requirement 29: Document Parsing — Round-Trip Integrity

**User Story:** As a platform operator, I want the document processing pipeline to reliably extract and preserve text content through the full upload-to-analysis cycle, so that AI responses are based on accurate document content.

#### Acceptance Criteria

1. THE File_Service SHALL parse uploaded PDF documents using PyMuPDF and produce Extracted_Text that preserves the logical reading order of the source document.
2. THE File_Service SHALL parse uploaded DOCX documents using python-docx and produce Extracted_Text that includes all paragraph and heading content in document order.
3. FOR ALL valid uploaded text documents (PDF or DOCX), extracting text and re-encoding it to UTF-8 SHALL produce a string with no data loss compared to direct character inspection of the source file's text layer (round-trip integrity property).
4. WHEN a PDF contains no text layer (scanned document), THE File_Service SHALL detect the absence of text, route the document page images to the OCR_Service, and produce Extracted_Text from the OCR output.
5. WHEN an uploaded document contains mixed content (some pages with text layer, some scanned), THE File_Service SHALL extract text from text-layer pages directly and OCR-process image-only pages, merging results in page order.
6. IF Extracted_Text from any document exceeds 50,000 characters, THEN THE File_Service SHALL truncate to 50,000 characters, append a truncation notice to the Extracted_Text, and log the original character count.

---

### Requirement 30: Study Planner Service (Foundation)

**User Story:** As a User, I want to set daily study goals and see my progress toward them, so that I can build consistent study habits.

#### Acceptance Criteria

1. WHEN a User sets a daily study goal (minimum 15 minutes, maximum 480 minutes) in their profile, THE User_Service SHALL persist the goal and THE Analytics_Service SHALL track daily progress toward it.
2. WHEN a User completes learning activities totaling their daily study goal in minutes within a calendar day (UTC), THE Analytics_Service SHALL mark the day as a goal-completion day in the Analytics_Records.
3. WHEN an authenticated User accesses the Dashboard, THE Platform SHALL display a progress bar showing minutes studied today versus the daily goal.
4. THE Analytics_Service SHALL compute and expose the User's goal completion rate as a percentage of days with completed goals over the past 30 days.
5. WHEN a User has not set a daily study goal, THE Dashboard SHALL display a prompt encouraging the User to set one, linked to the profile settings page.

---

### Requirement 31: Frontend Architecture and SvelteKit Conventions

**User Story:** As a frontend developer, I want the frontend to follow SvelteKit conventions with proper routing, layout hierarchies, and loading patterns, so that the application is maintainable and performant.

#### Acceptance Criteria

1. THE Frontend SHALL use SvelteKit file-based routing with a protected layout wrapping all authenticated routes that redirects unauthenticated users to the login page.
2. THE Frontend SHALL use SvelteKit load functions for server-side data fetching on Dashboard, History, and Analytics pages to enable progressive enhancement.
3. THE Frontend SHALL implement TypeScript strict mode across all `.svelte`, `.ts`, and `.svelte.ts` files with zero type errors at build time.
4. THE Frontend SHALL use shadcn-svelte components as the primary UI component library for all form controls, modals, cards, badges, and navigation elements.
5. THE Frontend SHALL use Lucide Icons exclusively for all iconography, with each icon accompanied by an appropriate ARIA label or title.
6. THE Frontend SHALL implement a global error boundary that catches unhandled component errors and displays a user-friendly fallback UI without crashing the entire application.
7. WHEN the frontend makes an API request and receives HTTP status 401, THE Frontend SHALL automatically clear the stored JWT, redirect the User to the login page, and display a session-expired notification.

---

### Requirement 32: Admin Capabilities

**User Story:** As an Admin, I want tools to monitor platform health, manage users, and configure AI providers, so that I can maintain the platform without engineering intervention for routine operations.

#### Acceptance Criteria

1. WHILE a User holds the Admin role, THE Platform SHALL expose an admin dashboard displaying: total registered users, daily active users for the past 7 days, total AI requests in the past 24 hours, AI provider latency averages, and error rates by endpoint.
2. WHEN an Admin searches for a user by email or user_id, THE Platform SHALL return the user's profile, role, account status, and summary counts within 2 seconds.
3. WHEN an Admin changes a User's role, THE Auth_Service SHALL invalidate that User's active sessions and return HTTP status 200 with the updated role.
4. WHEN an Admin suspends a User account, THE Auth_Service SHALL reject all API requests from that User's JWT with HTTP status 403 and a suspension message until the suspension is lifted.
5. WHEN an Admin updates the active AI provider configuration, THE AI_Dispatcher SHALL apply the new configuration for all subsequent requests within 60 seconds without a service restart.
6. THE Admin dashboard SHALL display a real-time log stream of AI_Requests and AI_Responses for monitoring model quality, accessible only to Admin role users.

---

### Requirement 33: Teacher Bulk Content Generation

**User Story:** As a Teacher, I want to generate multiple summaries or quizzes in a single request for a list of topics, so that I can prepare teaching materials for an entire curriculum efficiently.

#### Acceptance Criteria

1. WHILE a User holds the Teacher role, THE Summary_Service SHALL accept a bulk generation request with a list of up to 20 topics and return a list of generated Summaries, processing each topic via the AI_Orchestrator sequentially.
2. WHILE a User holds the Teacher role, THE Quiz_Service SHALL accept a bulk generation request with a list of up to 10 topics and return a list of generated Quizzes.
3. WHEN a bulk generation request is received, THE Platform SHALL process it as a background task and return HTTP status 202 Accepted with a task_id immediately.
4. WHEN a bulk generation background task completes, THE Notification_Service SHALL deliver an in-app notification with links to each generated resource.
5. WHEN one or more topics in a bulk request fail AI generation, THE Platform SHALL still return successful results for the remaining topics, flagging failed topics in the response with their error reasons.
6. THE Platform SHALL enforce a maximum of 3 concurrent bulk generation tasks per Teacher account at any time, returning HTTP status 429 if the limit is exceeded.

---

### Requirement 34: Data Privacy and Compliance

**User Story:** As a User, I want my personal data handled according to privacy standards, so that I can trust the platform with my study information.

#### Acceptance Criteria

1. THE Platform SHALL store all User passwords exclusively as bcrypt hashes with a minimum work factor of 12, never storing plaintext passwords.
2. THE Platform SHALL encrypt all data at rest in Supabase Storage and PostgreSQL using provider-managed AES-256 encryption.
3. WHEN a User requests a data export, THE Platform SHALL generate a ZIP archive containing all of that User's Summaries, Explanations, Quiz_Attempt results, and profile data in JSON format and make it available for download within 24 hours.
4. THE Platform SHALL retain deleted (soft-deleted) User content for a maximum of 30 days before permanent purging via a scheduled cleanup job.
5. WHEN a User submits uploaded document content to the AI_Orchestrator, THE Prompt_Service SHALL not include any other User's personal data in the prompt, ensuring complete data isolation between User sessions.
6. THE Platform SHALL log all data export and account deletion requests with timestamp, user_id, and request_id for compliance auditing.

---

### Requirement 35: Deployment Readiness and Environment Configuration

**User Story:** As a platform operator, I want the platform to be deployable across development, staging, and production environments with environment-specific configuration, so that changes can be validated before reaching production.

#### Acceptance Criteria

1. THE Platform SHALL provide a `docker-compose.yml` for local development that starts the FastAPI backend, SvelteKit frontend (dev server), and PostgreSQL database with a single command.
2. THE Platform SHALL include separate `.env.example` files for the frontend and backend documenting every required environment variable with placeholder values and descriptions.
3. THE Platform SHALL run all database migrations automatically on backend startup in development and staging environments, with migration execution in production requiring an explicit CLI command.
4. WHEN the backend starts without a required environment variable, THE Platform SHALL print a descriptive error message to stderr listing all missing variables and exit with a non-zero code.
5. THE Platform SHALL expose a `/health` liveness endpoint returning `{"status": "ok"}` with HTTP status 200 when the service is running.
6. THE Platform SHALL expose a `/health/ready` readiness endpoint that checks database connectivity, storage connectivity, and AI provider reachability, returning HTTP status 200 with all dependency statuses when all are healthy, or HTTP status 503 with a list of failing dependencies when any are unavailable.

---

### Requirement 36: Future Feature Scaffolding — AI Tutor Chat

**User Story:** As a platform architect, I want the data schema and API contracts for the AI Tutor Chat feature stubbed out at launch, so that the feature can be activated without schema migrations when prioritized.

#### Acceptance Criteria

1. THE Platform's database schema SHALL include the `Chat_History` table at launch with columns: id (UUID), user_id (UUID FK), session_id (UUID), role (enum: user/assistant), content (text), created_at (TIMESTAMPTZ), and deleted_at (TIMESTAMPTZ nullable).
2. THE Platform SHALL expose a stub `/api/v1/chat` POST endpoint at launch that returns HTTP status 501 Not Implemented with a message indicating the feature is coming soon.
3. THE AI_Dispatcher SHALL include a reserved interface method `stream_chat(session_id, messages)` in the Provider_Adapter abstract class, returning a not-implemented exception at launch.

---

### Requirement 37: Future Feature Scaffolding — Flashcards

**User Story:** As a platform architect, I want the data schema for the Flashcards feature prepared at launch, so that the feature can be built incrementally on an existing foundation.

#### Acceptance Criteria

1. THE Platform's database schema SHALL include the `Flashcards` table at launch with columns: id (UUID), user_id (UUID FK), topic (varchar 200), front_content (text), back_content (text), difficulty (enum: Easy/Medium/Hard), review_count (integer default 0), last_reviewed_at (TIMESTAMPTZ nullable), created_at (TIMESTAMPTZ), and deleted_at (TIMESTAMPTZ nullable).
2. THE Platform SHALL expose a stub `/api/v1/flashcards` endpoint at launch that returns HTTP status 501 Not Implemented.

---

### Requirement 38: Concurrent User Load and Reliability

**User Story:** As a platform operator, I want the platform to remain responsive and reliable under high concurrent user load, so that the learning experience is uninterrupted during peak usage.

#### Acceptance Criteria

1. THE Platform's backend SHALL handle a minimum of 500 concurrent authenticated users without response time degradation beyond 2x the baseline (p95 latency under 400ms for non-AI endpoints).
2. THE Platform SHALL implement connection pooling for database connections with a minimum pool size of 10 and a maximum pool size of 100 per backend instance.
3. WHEN the AI_Orchestrator's request queue exceeds 50 pending requests, THE Platform SHALL return HTTP status 503 with a `Retry-After` header of 30 seconds rather than queuing additional requests indefinitely.
4. THE Platform SHALL implement idempotency keys on Summary and Explanation generation endpoints so that duplicate requests within a 60-second window return the same in-progress or completed result without triggering a second AI call.
5. IF the Supabase PostgreSQL database becomes unreachable, THEN THE Platform SHALL return HTTP status 503 for all data-dependent endpoints and continue serving static assets and the login page.
