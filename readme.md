# AI GyanGuru

> AI-powered personal learning platform — Learn, Revise, Practice, Evaluate.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-FF3E00?style=flat&logo=svelte&logoColor=white)](https://kit.svelte.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

**AI GyanGuru** is an enterprise-grade AI learning platform. Upload study material or enter any topic — the AI instantly generates summaries, detailed explanations, and custom quizzes. Track your progress, identify weak areas, and learn smarter.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit + TypeScript + TailwindCSS |
| Backend | FastAPI + SQLAlchemy (async) + Alembic + Pydantic v2 |
| Database | PostgreSQL via Supabase (PgBouncer transaction pooler) |
| Auth | JWT (access + refresh tokens) + bcrypt |
| Storage | Supabase Storage |
| AI | Groq (default) · OpenAI (optional) · Google Gemini (optional) |
| OCR | Tesseract (default) · PaddleOCR (optional) |
| Docs | PyMuPDF + python-docx |

---

## Features

### Core Learning Tools
- **Smart Summaries** — Structured revision notes with key concepts, formulas, mnemonics, and exam tips; select which sections to include
- **Deep Explanations** — Step-by-step breakdowns across 9 sections: Introduction, Step-by-step, Concept breakdown, Examples, Analogies, Applications, Mistakes, FAQs, Recap
- **AI Quizzes** — Auto-generated MCQs (5–20 questions, Easy/Medium/Hard/Mixed difficulty) with per-question explanations
- **File Upload** — Upload PDFs, DOCX, TXT, or images; the backend extracts the actual text (and runs OCR on images/scanned PDFs); AI works from the real content, not the filename

### Multi-Provider AI Model Selection
- Select provider and model from a dropdown on every generation page
- Available providers load dynamically based on which API keys are configured
- Default: **Groq** (Llama 3.3 70B, Llama 3.1 8B, GPT-OSS 120B/20B, Qwen 3.6 27B, Gemma 2 9B)
- Optional: **OpenAI** (GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo)
- Optional: **Google Gemini** (Gemini 2.0 Flash, Gemini 1.5 Pro, Gemini 1.5 Flash)
- Selected model is saved to `localStorage` and persists across Summary / Explanation / Quiz

### Upload → Generate Workflow
1. Upload a file on `/upload`
2. Backend extracts actual text content (PDF text layers, DOCX paragraphs/tables, TXT, OCR for images)
3. File status progresses: **Pending → Processing → Ready**
4. Click **Generate Summary**, **Generate Explanation**, or **Generate Quiz** — the module opens pre-loaded with that file's extracted content
5. AI receives the actual document text, not just the filename

### Analytics & Tracking
- Progress dashboard — topics studied, quizzes taken, overall accuracy
- Activity heatmap (last 90 days, GitHub-style)
- Weak / strong area detection based on quiz category accuracy
- Learning history with search and type filters (Summary / Explanation / Quiz / Upload)

### Architecture Highlights
- **Provider-independent AI** — swap Groq / OpenAI / Gemini without touching generation logic
- **Fast auth middleware** — `CurrentUserFast` dependency skips the profile join on high-frequency endpoints (file polling, AI generation), saving one DB round-trip per request
- **Background task extraction** — file text extraction runs after the HTTP 201 response; uses direct SQL `UPDATE` statements per atomic session (compatible with PgBouncer NullPool)
- **Async everything** — SQLAlchemy async, FastAPI async, Supabase async
- **JWT + refresh tokens** — 15-minute access tokens, 7-day refresh tokens with rotation
- **Rate limiting** — 60 req/min general, 10 req/min AI endpoints

---

## Project Structure

```
ai-gyanguru/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST API routes
│   │   │   ├── auth.py
│   │   │   ├── files.py      # Upload + background extraction
│   │   │   ├── summaries.py
│   │   │   ├── explanations.py
│   │   │   ├── quizzes.py
│   │   │   ├── dashboard.py
│   │   │   ├── analytics.py
│   │   │   ├── history.py
│   │   │   ├── users.py
│   │   │   └── models.py     # GET /models — available providers/models
│   │   ├── services/         # Business logic
│   │   │   ├── auth_service.py
│   │   │   ├── file_service.py   # Upload + text extraction pipeline
│   │   │   ├── summary_service.py
│   │   │   ├── explanation_service.py
│   │   │   ├── quiz_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── history_service.py
│   │   │   └── user_service.py
│   │   ├── ai/               # Provider-independent AI engine
│   │   │   ├── base.py       # BaseAIProvider abstract class
│   │   │   ├── dispatcher.py # Routes to correct provider + model
│   │   │   ├── providers/
│   │   │   │   ├── groq_provider.py
│   │   │   │   ├── openai_provider.py
│   │   │   │   └── google_provider.py
│   │   │   ├── prompt_builder.py
│   │   │   ├── response_formatter.py
│   │   │   └── templates/    # Summary / Explanation / Quiz prompts
│   │   ├── ocr/
│   │   │   ├── base.py
│   │   │   ├── engine.py     # Factory (tesseract or paddleocr)
│   │   │   ├── tesseract_engine.py
│   │   │   └── paddleocr_engine.py
│   │   ├── storage/
│   │   │   └── supabase_storage.py
│   │   ├── repositories/     # Data access layer
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   └── core/
│   │       ├── config.py
│   │       ├── database.py   # Async engine, NullPool, AsyncSessionLocal proxy
│   │       ├── dependencies.py  # CurrentUser / CurrentUserFast
│   │       ├── security.py
│   │       └── exceptions.py
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── +layout.svelte    # Auth guard, sidebar, theme init
│   │   │   ├── +page.svelte      # Root → redirects to /login or /dashboard
│   │   │   ├── login/            # Split-screen login (gradient left, form right)
│   │   │   ├── register/
│   │   │   ├── dashboard/
│   │   │   ├── summary/          # Full-width vertical layout + file mode
│   │   │   ├── explanation/      # Full-width vertical layout + file mode
│   │   │   ├── quiz/             # Full-width vertical layout + file mode
│   │   │   │   └── [id]/play/ + results/
│   │   │   ├── upload/           # Status polling, progress bar, action buttons
│   │   │   ├── analytics/
│   │   │   ├── history/
│   │   │   └── profile/
│   │   └── lib/
│   │       ├── api/              # API client modules (all support provider+model)
│   │       ├── stores/
│   │       │   ├── auth.ts
│   │       │   ├── theme.ts
│   │       │   ├── toast.ts
│   │       │   └── modelSelector.ts  # Persistent AI model preference
│   │       ├── components/ui/
│   │       │   ├── ModelSelector.svelte  # Provider/model dropdown
│   │       │   └── ...
│   │       └── types/
│   ├── static/               # favicon.ico, favicon.png, favicon.svg
│   ├── svelte.config.js
│   └── vite.config.ts        # cacheDir → %TEMP% (avoids OneDrive file-lock issue)
│
├── .gitignore
├── docker-compose.yml
└── DEPLOYMENT.md
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project (free tier is fine)
- A [Groq](https://console.groq.com) API key (free)
- Tesseract OCR installed (optional — only needed for image/scanned-PDF uploads)
  - Windows: https://github.com/UB-Mannheim/tesseract/wiki
  - macOS: `brew install tesseract`
  - Ubuntu: `sudo apt install tesseract-ocr`

### Backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — fill in DATABASE_URL, Supabase keys, GROQ_API_KEY

# Run database migrations
alembic upgrade head

# Start the development server
python -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env — PUBLIC_API_URL should point to backend

# Start the development server
npm run dev
# (or if npm is blocked by PowerShell execution policy:)
node node_modules/vite/bin/vite.js dev
```

App: http://localhost:5173

### Fix npm in PowerShell (Windows one-time setup)

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Application
APP_NAME=AI GyanGuru
APP_ENV=development
APP_DEBUG=true
APP_SECRET_KEY=<random-32-char-string>
FRONTEND_URL=http://localhost:5173

# Database — Supabase Transaction Pooler (port 6543, NOT direct 5432)
DATABASE_URL=postgresql+asyncpg://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres

# Supabase
SUPABASE_URL=https://<ref>.supabase.co
SUPABASE_ANON_KEY=<anon-key>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=gyanguru-uploads

# JWT
JWT_SECRET_KEY=<random-32-char-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI Providers — add keys to enable providers
GROQ_API_KEY=<groq-key>           # required (free at console.groq.com)
GROQ_DEFAULT_MODEL=openai/gpt-oss-120b
AI_PROVIDER=groq
AI_MAX_RETRIES=2
AI_REQUEST_TIMEOUT=60

OPENAI_API_KEY=                   # optional — leave empty to disable OpenAI models
GOOGLE_API_KEY=                   # optional — leave empty to disable Gemini models

# OCR
OCR_ENGINE=tesseract
TESSERACT_CMD=C:/Program Files/Tesseract-OCR/tesseract.exe  # Windows path

# File Upload
MAX_FILE_SIZE_MB=20
ALLOWED_EXTENSIONS=pdf,docx,txt,png,jpg,jpeg,webp

# Rate Limiting
RATE_LIMIT_GENERAL=60/minute
RATE_LIMIT_AI=10/minute

# Logging
LOG_LEVEL=INFO
```

### Frontend (`frontend/.env`)

```env
PUBLIC_API_URL=http://localhost:8000/api/v1
PUBLIC_SUPABASE_URL=https://<ref>.supabase.co
PUBLIC_SUPABASE_ANON_KEY=<anon-key>
```

---

## Adding AI Providers

The dispatcher auto-loads any provider whose API key is non-empty in `.env`.

| Provider | Key | Install |
|----------|-----|---------|
| Groq | `GROQ_API_KEY` | included in `requirements.txt` |
| OpenAI | `OPENAI_API_KEY` | `pip install openai>=1.0` |
| Google Gemini | `GOOGLE_API_KEY` | `pip install google-generativeai>=0.8` |

After adding a key (and installing the package if needed), restart the backend. The new provider appears automatically in the model selector dropdown.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new account |
| POST | `/auth/login` | Login → access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| POST | `/auth/logout` | Invalidate refresh token |
| GET | `/auth/me` | Current user info |
| GET | `/models` | Available AI providers and models |
| POST | `/files` | Upload file (text extraction runs in background) |
| GET | `/files` | List uploaded files |
| GET | `/files/{id}` | Get file status + metadata |
| DELETE | `/files/{id}` | Delete file |
| POST | `/summaries` | Generate summary from topic |
| POST | `/summaries/from-file` | Generate summary from uploaded file |
| POST | `/explanations` | Generate explanation from topic |
| POST | `/explanations/from-file` | Generate explanation from uploaded file |
| POST | `/quizzes` | Generate quiz from topic |
| POST | `/quizzes/from-file` | Generate quiz from uploaded file |
| POST | `/quizzes/{id}/submit` | Submit quiz answers → get scored results |
| GET | `/dashboard` | Home dashboard data |
| GET | `/analytics/dashboard` | Full analytics |
| GET | `/history` | Learning history (paginated, filterable) |

Full interactive docs: http://localhost:8000/docs

---

## Database Schema

12 tables managed by Alembic migrations:

| Table | Purpose |
|-------|---------|
| `users` | User accounts (email, hashed password, role) |
| `profiles` | Extended profile (name, bio, education level, exam target) |
| `uploads` | File uploads with extraction status and extracted text |
| `summaries` | Generated summaries (topic, sections, content, model used) |
| `explanations` | Generated explanations (topic, 9-section content, model used) |
| `quizzes` | Quiz metadata (topic, difficulty, question count) |
| `quiz_questions` | Individual questions with options and correct answer |
| `quiz_attempts` | Submission records with score and performance summary |
| `quiz_answers` | Per-question answer records |
| `analytics_events` | Activity log for analytics computation |
| `history_items` | Unified learning history entries |
| `ai_requests` / `ai_responses` | AI audit trail |

---

## Known Issues & Notes

| Issue | Status | Notes |
|-------|--------|-------|
| Tesseract not installed | OCR skipped | Image/scanned-PDF uploads will fail with a clear error message. Install Tesseract to enable OCR. |
| PaddleOCR | Disabled | Commented out in `requirements.txt` — heavy dependency. Switch `OCR_ENGINE=paddleocr` and install manually if preferred. |
| OneDrive + Vite cache | Fixed | `vite.config.ts` redirects Vite's cache to `%TEMP%` to avoid Windows file-lock errors. |
| Background tasks + PgBouncer | Fixed | `file_service.py` uses direct SQL `UPDATE` in separate sessions instead of ORM flush/refresh, which was incompatible with PgBouncer's NullPool transaction mode. |

---

## Security

- JWT access tokens expire in 15 minutes; refresh tokens in 7 days with rotation
- Passwords hashed with bcrypt (72-byte truncation)
- API keys stay in backend `.env` — never exposed to the frontend
- CORS restricted to `FRONTEND_URL` in production
- Rate limiting: 60 req/min general, 10 req/min on AI endpoints
- File upload validation: type whitelist + 20 MB size limit + MIME check
- SQL injection protection via SQLAlchemy ORM

---

## Production Checklist

- [ ] Set `APP_ENV=production` in backend `.env`
- [ ] Generate strong random values for `APP_SECRET_KEY` and `JWT_SECRET_KEY` (32+ chars)
- [ ] Set `FRONTEND_URL` to your production domain
- [ ] Enable HTTPS via reverse proxy (Nginx / Caddy)
- [ ] Use Supabase Transaction Pooler connection string (port 6543)
- [ ] Configure rate limits for production traffic
- [ ] Monitor Groq API quota and token usage
- [ ] Set up error tracking (Sentry recommended)
- [ ] Switch `@sveltejs/adapter-auto` to `adapter-node` or `adapter-static` in `svelte.config.js`

---

## License

Proprietary — all rights reserved.

---

*Built for learners everywhere.*
