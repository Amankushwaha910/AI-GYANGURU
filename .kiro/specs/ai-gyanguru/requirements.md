# AI GyanGuru — Requirements

## Overview

AI GyanGuru is an AI-powered personal learning platform that helps students learn, revise, practice, and evaluate knowledge through artificial intelligence. It is not an LMS. It is a personal AI study companion that generates structured educational content on demand from topic input or uploaded study materials.

---

## 1. Functional Requirements

### 1.1 Authentication & User Management

#### FR-AUTH-01 — User Registration
- Users must be able to register with email and password
- Password must be validated for minimum strength (8 chars, mixed case, number)
- Email must be verified before full account access is granted
- Duplicate email registration must be rejected with a clear error

#### FR-AUTH-02 — Email/Password Login
- Users must be able to log in with registered email and password
- Invalid credentials must return a generic error (no user enumeration)
- Successful login must issue a JWT access token and refresh token
- Refresh token rotation must be implemented

#### FR-AUTH-03 — Google OAuth Login
- Users must be able to authenticate via Google OAuth 2.0
- On first Google login, a profile must be auto-created
- Existing accounts linked to the same email must be merged/linked

#### FR-AUTH-04 — Session Management
- JWT access tokens must expire in 15 minutes
- Refresh tokens must expire in 7 days
- Users must be able to explicitly log out, invalidating the refresh token
- Concurrent sessions must be supported

#### FR-AUTH-05 — User Profile
- Users must be able to view and update their profile (name, avatar, bio, exam target, education level)
- Users must be able to change their password
- Users must be able to delete their account with all associated data

#### FR-AUTH-06 — Role-Based Authorization
- Roles: `student`, `teacher`, `admin`
- Default role on registration: `student`
- Each API endpoint must enforce role-based access control

---

### 1.2 Dashboard

#### FR-DASH-01 — Overview Panel
- Dashboard must display a greeting with the user's name
- Must show total topics studied, total quizzes taken, total summaries generated, and overall quiz accuracy as summary cards

#### FR-DASH-02 — Recent Learning Activity
- Must display the last 5–10 learning activities (summaries, explanations, quizzes) with topic name, type, and timestamp
- Each item must be clickable to view the full content

#### FR-DASH-03 — Analytics Snapshot
- Dashboard must show a weekly activity chart (topics studied per day)
- Must show a quiz accuracy trend line for the last 7 days

#### FR-DASH-04 — Quick Actions
- Must provide one-click access to: Generate Summary, Get Explanation, Start Quiz, Upload File

---

### 1.3 Summary Module

#### FR-SUM-01 — Topic-Based Summary Generation
- Users must be able to input a topic name (free text) and select output types
- Users must be able to choose one or more of the following output sections:
  - Definition
  - Key Concepts
  - Important Facts
  - Formula Sheet
  - Mnemonics
  - Exam Tips
  - Revision Notes
  - Checklist

#### FR-SUM-02 — File-Based Summary Generation
- Users must be able to upload a file (PDF, DOCX, TXT, image) and generate a summary from its content
- The file processing pipeline must: Upload → Extract Text → OCR (if image/scanned) → Prompt Builder → AI → Return Result

#### FR-SUM-03 — Summary Display
- Summary must be rendered in a structured, readable format with clear section headings
- Each section must be individually collapsible

#### FR-SUM-04 — Summary Persistence
- Generated summaries must be saved to the user's history automatically
- Users must be able to view, re-read, and delete saved summaries

#### FR-SUM-05 — Summary Regeneration
- Users must be able to regenerate a summary with the same topic/file
- Regenerated content must not overwrite the original unless explicitly confirmed

---

### 1.4 Explanation Module

#### FR-EXP-01 — Topic Explanation Generation
- Users must be able to input a topic and request a full explanation
- The explanation must include all of the following sections:
  - Introduction
  - Step-by-step Explanation
  - Concept Breakdown
  - Real-world Examples
  - Analogies
  - Practical Applications
  - Common Mistakes
  - FAQs
  - Final Recap

#### FR-EXP-02 — File-Based Explanation
- Users must be able to upload a file and receive an explanation based on its content
- The same file processing pipeline applies as in FR-SUM-02

#### FR-EXP-03 — Explanation Display
- Explanation must be rendered section by section with smooth progressive reveal
- Each section must be labeled clearly

#### FR-EXP-04 — Explanation Persistence
- Generated explanations must be auto-saved to history
- Users must be able to view and delete saved explanations

---

### 1.5 Quiz Module

#### FR-QUIZ-01 — Quiz Generation
- Users must be able to generate a quiz by entering a topic or uploading a file
- Users must be able to specify:
  - Number of questions (5, 10, 15, 20)
  - Difficulty (Easy, Medium, Hard, Mixed)
  - Category/subject tag (optional)

#### FR-QUIZ-02 — Question Structure
- Every question must be a multiple-choice question (MCQ) with exactly 4 options
- Each question must include:
  - Question text
  - 4 answer options (labeled A–D)
  - Correct answer
  - Explanation for the correct answer
  - Difficulty tag
  - Category tag

#### FR-QUIZ-03 — Quiz Interface
- Users must be able to navigate questions using Previous / Next buttons
- A progress bar must show current question number vs total
- Selected answers must be visually highlighted
- Users must not be able to submit until at least one question is answered
- A Submit button must appear on the last question or be accessible from any question

#### FR-QUIZ-04 — Quiz Timer (Future)
- A countdown timer must be placeholded in the UI, disabled by default, activatable in a future release

#### FR-QUIZ-05 — Quiz Results
- After submission, the results page must show:
  - Total Score
  - Percentage
  - Number of correct answers
  - Number of wrong answers
  - For each question: user's answer, correct answer, explanation
  - Performance summary (e.g., "You scored well in X, struggled in Y")

#### FR-QUIZ-06 — Quiz Persistence
- Quiz attempts must be saved with all answers, score, and timestamp
- Users must be able to review past quiz attempts in full

---

### 1.6 File Upload & Processing

#### FR-FILE-01 — Supported File Types
- The system must accept: PDF, DOCX, TXT, PNG, JPG, JPEG, WEBP

#### FR-FILE-02 — File Size Limits
- Maximum file size: 20 MB per upload

#### FR-FILE-03 — Text Extraction
- PDF files must be processed using PyMuPDF
- DOCX files must be processed using python-docx
- TXT files must be read directly
- Image files must be processed using PaddleOCR (primary) or Tesseract OCR (fallback)

#### FR-FILE-04 — Processing Pipeline
- Upload → Validate → Store to Supabase Storage → Extract Text → OCR if needed → Return extracted text to calling service

#### FR-FILE-05 — Upload History
- Every uploaded file must be stored with: filename, file type, size, upload timestamp, extracted text reference, and user ID
- Users must be able to view and delete uploaded files

#### FR-FILE-06 — Reuse Uploaded Files
- Users must be able to select a previously uploaded file to generate a new summary, explanation, or quiz without re-uploading

---

### 1.7 Analytics Module

#### FR-ANA-01 — Learning Progress Tracking
- The system must track every topic studied, summary generated, explanation viewed, and quiz attempted
- Each event must record: user ID, action type, topic, timestamp, module

#### FR-ANA-02 — Analytics Dashboard Data
- The analytics page must display:
  - Total topics studied (all time)
  - Total quizzes taken (all time)
  - Overall quiz accuracy (percentage)
  - Topics studied per day (last 30 days) — bar chart
  - Quiz accuracy over time (last 30 days) — line chart
  - Weak areas (categories with lowest quiz accuracy)
  - Strong areas (categories with highest quiz accuracy)
  - Daily activity heatmap (GitHub-style, last 90 days)

#### FR-ANA-03 — Study History Timeline
- Must display a chronological feed of all learning activities with type, topic, and timestamp

---

### 1.8 History Module

#### FR-HIS-01 — History Storage
- All generated summaries, explanations, quiz attempts, and uploaded files must be stored per user

#### FR-HIS-02 — History Browsing
- Users must be able to browse history filtered by type (Summary, Explanation, Quiz, Upload)
- Pagination must be supported (20 items per page)
- Search by topic name must be supported

#### FR-HIS-03 — History Detail View
- Each history item must be viewable in full detail
- Summaries and explanations must render the original structured output
- Quiz attempts must show full question/answer review

#### FR-HIS-04 — History Deletion
- Users must be able to delete individual history items
- Users must be able to clear all history of a specific type

---

### 1.9 AI Engine

#### FR-AI-01 — Provider Independence
- The AI layer must be fully abstracted behind a provider interface
- Swapping AI providers must not require changes to any service or route logic

#### FR-AI-02 — Supported Models (Groq)
- Llama 3.x (default)
- DeepSeek R1
- Gemma
- Mixtral

#### FR-AI-03 — Prompt Engine
- All prompts must be built via a centralized Prompt Builder using versioned templates
- Templates must be modular and separately defined per module (summary, explanation, quiz)
- Prompt templates must support variable injection (topic, extracted text, difficulty, output format)

#### FR-AI-04 — Structured Response Formatting
- All AI responses must be validated and parsed into structured JSON before being returned
- Malformed AI responses must trigger a retry (max 2 retries) before returning an error

#### FR-AI-05 — Streaming Responses
- Long-form AI responses (summaries, explanations) must support server-sent events (SSE) streaming to the frontend
- The frontend must render content progressively as chunks arrive

#### FR-AI-06 — Request/Response Logging
- Every AI request and response must be logged to the `ai_requests` and `ai_responses` tables
- Logs must include: user ID, model, prompt hash, token usage, latency, timestamp

---

## 2. Non-Functional Requirements

### 2.1 Performance

#### NFR-PERF-01
- API response time for non-AI endpoints must be under 300ms (p95)
- AI generation endpoints must return first token within 1.5 seconds (streaming)

#### NFR-PERF-02
- Database queries must use indexed columns for all filtering and sorting operations
- N+1 query patterns must be eliminated using SQLAlchemy eager loading

#### NFR-PERF-03
- Frontend bundles must be code-split per route using SvelteKit's native code splitting
- Lazy loading must be applied to all dashboard charts and heavy components

#### NFR-PERF-04
- File text extraction must run as a background task (FastAPI BackgroundTasks or Celery in future)

### 2.2 Security

#### NFR-SEC-01
- All API endpoints except `/auth/register`, `/auth/login`, and `/auth/google` must require a valid JWT
- JWT secrets must be stored in environment variables, never hardcoded

#### NFR-SEC-02
- File uploads must be validated for MIME type and file extension before storage
- Uploaded files must be scanned for size limits server-side

#### NFR-SEC-03
- All database queries must use parameterized statements via SQLAlchemy ORM
- Raw SQL must not be used except in reviewed migration scripts

#### NFR-SEC-04
- Rate limiting must be applied: 60 requests/minute per IP for general endpoints, 10 requests/minute for AI generation endpoints

#### NFR-SEC-05
- CORS must be configured to allow only the registered frontend origin
- CSRF tokens must be required for all state-mutating requests

#### NFR-SEC-06
- All secrets (DB URL, Groq API key, Supabase keys) must be loaded from environment variables using a secrets manager pattern

### 2.3 Scalability

#### NFR-SCALE-01
- Every backend service must be independently deployable as a module
- The architecture must support extraction into microservices without code rewrites

#### NFR-SCALE-02
- The AI provider adapter must implement a standard interface, allowing new providers to be added by implementing one class

#### NFR-SCALE-03
- The OCR engine must be swappable via configuration (PaddleOCR vs Tesseract)
- The storage provider must be swappable via a storage interface (Supabase → S3 without app changes)

### 2.4 Reliability

#### NFR-REL-01
- AI generation failures must return structured error responses, not raw exceptions
- Retry logic (max 2 attempts) must exist for transient AI provider errors

#### NFR-REL-02
- File processing failures must not silently drop data; errors must be stored and surfaced to the user

#### NFR-REL-03
- Database migrations must be managed via Alembic with versioned migration files

### 2.5 Maintainability

#### NFR-MAINT-01
- All backend code must follow Clean Architecture with separated layers: routes → services → repositories → models
- No business logic in route handlers

#### NFR-MAINT-02
- All API endpoints must be documented via OpenAPI (auto-generated by FastAPI)
- All Pydantic schemas must include field descriptions

#### NFR-MAINT-03
- Frontend components must be atomic and reusable
- No inline business logic in Svelte components; all data fetching via dedicated API client modules

### 2.6 Accessibility & UX

#### NFR-UX-01
- The UI must support Light Mode and Dark Mode with system preference detection
- Mode toggle must be available from the navigation bar

#### NFR-UX-02
- All interactive elements must be keyboard-navigable
- Color contrast must meet WCAG AA standards

#### NFR-UX-03
- The UI must be fully responsive across Desktop (1280px+), Tablet (768px–1279px), and Mobile (< 768px)

#### NFR-UX-04
- Loading states must be shown for all async operations
- Skeleton loaders must be used instead of spinners for content areas

---

## 3. Constraints

- **AI Provider**: Groq API is the default; the architecture must allow replacement without code changes
- **Database**: PostgreSQL via Supabase; no other database engine is currently supported
- **Authentication**: Supabase Auth is the identity provider; custom auth is not in scope
- **File Size**: Maximum 20 MB per upload
- **Language**: Backend in Python 3.11+, Frontend in TypeScript (strict mode)
- **Deployment**: Must be deployable on any cloud platform supporting Docker containers
- **API Versioning**: All backend routes must be prefixed with `/api/v1/`

---

## 4. User Stories

### Authentication
- As a new user, I want to register with my email and password so I can create an account
- As a returning user, I want to log in with Google so I don't need to remember a password
- As a user, I want my session to remain active so I don't get logged out mid-session
- As a user, I want to update my profile with my exam target so the platform can personalize content

### Summary
- As a student, I want to enter a topic and get a structured revision summary so I can study efficiently
- As a student, I want to upload my PDF textbook and get key concepts extracted so I don't have to read the whole chapter
- As a student, I want to see mnemonics and exam tips so I remember the content better during exams

### Explanation
- As a student, I want a step-by-step explanation of a concept with real examples so I can understand it deeply
- As a student, I want to see common mistakes explained so I can avoid them in exams

### Quiz
- As a student, I want to generate a 10-question MCQ quiz on any topic so I can test my knowledge
- As a student, I want to see the explanation for each answer after submitting so I learn from my mistakes
- As a student, I want to see my quiz score and performance breakdown so I know which areas to improve

### File Upload
- As a student, I want to upload a scanned image of my handwritten notes and have the AI process them
- As a student, I want to reuse a previously uploaded file without uploading it again

### Analytics
- As a student, I want to see how many topics I've studied this week on a chart
- As a student, I want to see my weak areas so I can focus my revision

### History
- As a student, I want to browse all my past summaries and explanations so I can review them before an exam
- As a student, I want to search my history by topic name to find specific content quickly

---

## 5. Out of Scope (Current Version)

The following features are acknowledged and architecturally prepared for but not implemented in v1:

- AI Tutor Chat (real-time conversational tutor)
- Flashcard generation and spaced repetition
- Voice learning and speech recognition
- Study Planner with daily goals and reminders
- Teacher Dashboard and class management
- Admin Dashboard
- Collaboration features
- Mobile native app
- Offline mode
- Recommendation Engine
- Quiz timer
- Notifications system (infrastructure ready, UI deferred)
