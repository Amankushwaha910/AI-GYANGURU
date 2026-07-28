# AI GyanGuru

> AI-powered personal learning platform — Learn, Revise, Practice, Evaluate.

[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SvelteKit](https://img.shields.io/badge/SvelteKit-FF3E00?style=flat&logo=svelte&logoColor=white)](https://kit.svelte.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

**AI GyanGuru** is an enterprise-grade AI learning platform built from scratch with production-ready architecture. Enter any topic or upload study materials — AI instantly generates summaries, detailed explanations, and custom quizzes. Track your progress, identify weak areas, and learn smarter.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | SvelteKit + TypeScript + TailwindCSS + shadcn-svelte |
| Backend | FastAPI + SQLAlchemy + Alembic + Pydantic |
| Database | PostgreSQL (Supabase) |
| Auth | Supabase Auth + JWT + Google OAuth |
| Storage | Supabase Storage |
| AI | Groq API (provider-independent) |
| OCR | PaddleOCR / Tesseract |
| Docs | PyMuPDF + python-docx |

## ✨ Features

### 🎯 Core Learning Tools
- **Smart Summaries** — Generate structured revision notes with key concepts, formulas, mnemonics, exam tips
- **Deep Explanations** — Step-by-step concept breakdowns with real examples and analogies
- **AI Quizzes** — Auto-generated MCQs with detailed explanations for every answer
- **File Upload** — Upload PDFs, DOCX, images; AI extracts text via OCR and processes them

### 📊 Analytics & Tracking
- **Progress Dashboard** — Visual analytics showing topics studied, quiz performance, and trends
- **Weak Area Detection** — AI identifies subjects where you need more practice
- **Learning History** — Browse all past summaries, explanations, and quiz attempts
- **Activity Heatmap** — GitHub-style visualization of your daily learning activity

### 🏗️ Enterprise Architecture
- **Provider-Independent AI** — Swap Groq for OpenAI/Anthropic without code changes
- **Clean Architecture** — Layered design: Routes → Services → Repositories → Models
- **Repository Pattern** — Database abstraction layer for testability and flexibility
- **Async Everything** — SQLAlchemy async, FastAPI async, Supabase async
- **JWT + Refresh Tokens** — Secure session management with token rotation
- **Rate Limiting** — Per-IP and per-endpoint limits to prevent abuse
- **OpenAPI Docs** — Auto-generated API documentation via FastAPI

## Project Structure

```
ai-gyanguru/
├── backend/          # FastAPI application
│   ├── app/
│   │   ├── api/      # Route handlers
│   │   ├── services/ # Business logic
│   │   ├── repositories/ # Data access layer
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic schemas
│   │   ├── ai/       # AI engine (provider-independent)
│   │   ├── ocr/      # OCR engine abstraction
│   │   ├── storage/  # Storage provider abstraction
│   │   └── core/     # Config, security, dependencies
│   ├── alembic/      # Database migrations
│   └── tests/
├── frontend/         # SvelteKit application
│   ├── src/
│   │   ├── routes/   # SvelteKit pages
│   │   ├── lib/
│   │   │   ├── components/ # UI components
│   │   │   ├── stores/     # Svelte stores
│   │   │   ├── api/        # API client
│   │   │   └── types/      # TypeScript types
│   └── static/
└── docker-compose.yml
```

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env        # Fill in your secrets
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env        # Fill in your secrets
npm run dev
```

### Docker (Full Stack)
```bash
docker-compose up --build
```

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all required variables.

## API Documentation

FastAPI auto-generates OpenAPI docs at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📁 Project Structure (Complete)

```
ai-gyanguru/
├── backend/
│   ├── app/
│   │   ├── api/v1/           # REST API routes
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── summaries.py  # Summary generation
│   │   │   ├── explanations.py
│   │   │   ├── quizzes.py
│   │   │   ├── files.py
│   │   │   ├── analytics.py
│   │   │   ├── history.py
│   │   │   ├── users.py
│   │   │   └── dashboard.py
│   │   ├── services/         # Business logic layer
│   │   │   ├── auth_service.py
│   │   │   ├── summary_service.py
│   │   │   ├── explanation_service.py
│   │   │   ├── quiz_service.py
│   │   │   ├── file_service.py
│   │   │   ├── analytics_service.py
│   │   │   ├── history_service.py
│   │   │   └── user_service.py
│   │   ├── repositories/     # Data access layer
│   │   │   ├── base_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── summary_repository.py
│   │   │   ├── quiz_repository.py
│   │   │   └── analytics_repository.py
│   │   ├── models/           # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── summary.py
│   │   │   ├── explanation.py
│   │   │   ├── quiz.py
│   │   │   ├── upload.py
│   │   │   ├── analytics.py
│   │   │   ├── history.py
│   │   │   └── ai_log.py
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── ai/               # AI engine (provider-independent)
│   │   │   ├── base.py       # Abstract provider interface
│   │   │   ├── dispatcher.py # Routes to correct provider
│   │   │   ├── providers/
│   │   │   │   └── groq_provider.py
│   │   │   ├── templates/    # Prompt templates
│   │   │   │   ├── summary_templates.py
│   │   │   │   ├── explanation_templates.py
│   │   │   │   └── quiz_templates.py
│   │   │   ├── prompt_builder.py
│   │   │   └── response_formatter.py
│   │   ├── ocr/              # OCR engine abstraction
│   │   │   ├── base.py
│   │   │   ├── paddleocr_engine.py
│   │   │   └── tesseract_engine.py
│   │   ├── storage/          # Storage provider abstraction
│   │   │   ├── base.py
│   │   │   └── supabase_storage.py
│   │   ├── core/             # Config, security, dependencies
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── security.py
│   │   │   ├── dependencies.py
│   │   │   └── exceptions.py
│   │   └── main.py           # FastAPI app entry point
│   ├── alembic/              # Database migrations
│   │   ├── versions/
│   │   │   └── 001_initial_schema.py
│   │   └── env.py
│   ├── requirements.txt
│   ├── alembic.ini
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── routes/           # SvelteKit pages
│   │   │   ├── +layout.svelte
│   │   │   ├── +page.svelte  # Landing page
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   ├── dashboard/
│   │   │   ├── summary/
│   │   │   ├── explanation/
│   │   │   ├── quiz/
│   │   │   │   ├── +page.svelte
│   │   │   │   └── [id]/
│   │   │   │       ├── play/
│   │   │   │       └── results/
│   │   │   ├── analytics/
│   │   │   ├── history/
│   │   │   ├── upload/
│   │   │   └── profile/
│   │   ├── lib/
│   │   │   ├── components/   # Reusable UI components
│   │   │   │   ├── ui/       # Base components
│   │   │   │   │   ├── Button.svelte
│   │   │   │   │   ├── Input.svelte
│   │   │   │   │   ├── Card.svelte
│   │   │   │   │   ├── Modal.svelte
│   │   │   │   │   ├── Toast.svelte
│   │   │   │   │   └── ...
│   │   │   │   └── layout/   # Layout components
│   │   │   │       ├── Sidebar.svelte
│   │   │   │       ├── TopBar.svelte
│   │   │   │       └── PageLayout.svelte
│   │   │   ├── api/          # API client modules
│   │   │   │   ├── client.ts
│   │   │   │   ├── auth.ts
│   │   │   │   ├── summaries.ts
│   │   │   │   ├── quizzes.ts
│   │   │   │   └── ...
│   │   │   ├── stores/       # Svelte stores
│   │   │   │   ├── auth.ts
│   │   │   │   ├── theme.ts
│   │   │   │   └── toast.ts
│   │   │   ├── types/        # TypeScript types
│   │   │   │   └── index.ts
│   │   │   └── utils.ts
│   │   ├── app.html
│   │   └── app.css
│   ├── package.json
│   ├── svelte.config.js
│   ├── tailwind.config.ts
│   ├── vite.config.ts
│   └── Dockerfile
│
├── docker-compose.yml
├── .gitignore
├── readme.md
└── DEPLOYMENT.md
```

## 🚀 Production Deployment Checklist

- [ ] Set `APP_ENV=production` in backend `.env`
- [ ] Use strong secrets (32+ chars) for `JWT_SECRET_KEY` and `APP_SECRET_KEY`
- [ ] Configure CORS to allow only your production frontend URL
- [ ] Enable HTTPS via reverse proxy (Nginx/Caddy)
- [ ] Set up database backups (Supabase auto-backups)
- [ ] Configure rate limiting thresholds
- [ ] Monitor Groq API quota and token usage
- [ ] Set up error tracking (Sentry recommended)
- [ ] Configure CDN for static assets
- [ ] Test Google OAuth with production redirect URLs

## 📊 Database Schema

**12 Tables:**
- `users` — User accounts
- `profiles` — Extended user profiles
- `uploads` — File uploads with OCR status
- `summaries` — Generated summaries
- `explanations` — Generated explanations
- `quizzes` — Quiz metadata
- `quiz_questions` — Individual questions
- `quiz_attempts` — Quiz submissions
- `quiz_answers` — Answer records
- `analytics_events` — Learning activity log
- `history_items` — Unified history view
- `ai_requests` / `ai_responses` — AI audit logs

All migrations managed by **Alembic**.

## 🎨 Design System

- **Colors**: Brand (indigo-600), Success (green), Warning (yellow), Danger (red)
- **Typography**: Inter font family
- **Components**: shadcn-svelte compatible, fully accessible
- **Dark Mode**: System preference detection + manual toggle
- **Responsive**: Mobile-first, breakpoints: 640px, 768px, 1024px, 1280px

## 🔐 Security Features

- JWT access tokens (15 min expiry)
- Refresh tokens (7 day expiry) with rotation
- Bcrypt password hashing
- Google OAuth 2.0 integration
- CORS protection
- Rate limiting (60 req/min general, 10 req/min AI)
- Input validation (Pydantic)
- SQL injection protection (ORM)
- XSS protection (content sanitization)
- File upload validation (type, size, MIME)

## 🧪 Testing

```bash
# Backend tests (pytest)
cd backend
pytest

# Frontend tests (vitest + testing-library)
cd frontend
npm run test
```

## 📈 Scalability

The architecture supports:
- **Horizontal scaling** — Stateless API design
- **Provider swapping** — Abstract interfaces for AI, OCR, Storage
- **Microservices** — Service layer can be extracted without refactoring
- **Caching** — Redis ready for session/response caching
- **CDN** — Static assets served separately
- **Queue workers** — Background tasks (file processing, email)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary. All rights reserved.

## 🙏 Acknowledgments

- **Groq** for lightning-fast AI inference
- **Supabase** for managed PostgreSQL and Auth
- **FastAPI** for the best Python web framework
- **SvelteKit** for the smoothest frontend DX

---

**Built with ❤️ for learners everywhere.**
