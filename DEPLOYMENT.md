# AI GyanGuru — Deployment Guide

## Quick Start (Development)

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL (via Supabase)
- Redis (optional for rate limiting)
- Groq API key

---

## Backend Setup

### 1. Install Dependencies
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
```bash
cp .env.example .env
```

Edit `.env` and fill in all required values:
- `DATABASE_URL` — Supabase PostgreSQL connection string
- `SUPABASE_URL` — Your Supabase project URL
- `SUPABASE_ANON_KEY` — Supabase anon key
- `SUPABASE_SERVICE_ROLE_KEY` — Supabase service role key
- `JWT_SECRET_KEY` — Generate with `openssl rand -hex 32`
- `GROQ_API_KEY` — Get from https://console.groq.com
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` (optional for OAuth)

### 3. Database Migration
```bash
# Create all tables
alembic upgrade head
```

### 4. Run Backend
```bash
uvicorn app.main:app --reload --port 8000
```

Backend will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Frontend Setup

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Environment Configuration
```bash
cp .env.example .env
```

Edit `.env`:
```
PUBLIC_API_URL=http://localhost:8000/api/v1
PUBLIC_SUPABASE_URL=https://your-project.supabase.co
PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Run Frontend
```bash
npm run dev
```

Frontend will be available at `http://localhost:5173`

---

## Docker Deployment (Full Stack)

### Run Everything with Docker Compose
```bash
# Copy env files first
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit both .env files with your secrets

# Start all services
docker-compose up --build
```

Services:
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- Redis: `localhost:6379`

---

## Production Deployment

### Backend (Docker)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend (Static Build)
```bash
npm run build
# Deploy the 'build/' directory to any static host
```

### Environment Variables (Production)
- Set `APP_ENV=production` in backend `.env`
- Update `CORS_ORIGINS` to your production frontend URL
- Use strong secrets (32+ character random strings)
- Enable HTTPS (use reverse proxy like Nginx)

---

## Supabase Setup

### 1. Create Project
- Go to https://supabase.com
- Create a new project
- Note down the connection string, URL, and keys

### 2. Storage Bucket
- Go to Storage → Create bucket
- Name: `gyanguru-uploads`
- Make it **private** (authenticated access only)

### 3. Auth Configuration (Optional)
- Enable Google OAuth in Authentication → Providers
- Add your Google Client ID and Secret
- Set redirect URL to `http://localhost:8000/api/v1/auth/google/callback`

---

## Groq AI Setup

1. Sign up at https://console.groq.com
2. Create an API key
3. Add to `GROQ_API_KEY` in `.env`

**Supported Models (Developer Plan):**
- `openai/gpt-oss-120b` (default — best quality, 120B params)
- `openai/gpt-oss-20b` (faster, lighter)
- `qwen/qwen3.8-27b` (multilingual)

> Note: `llama-3.3-70b-versatile` and `llama-3.1-8b-instant` require an Enterprise Groq account and will return 404 on standard Developer accounts.

---

## OCR Setup

### PaddleOCR (Recommended)
```bash
pip install paddleocr paddlepaddle
```
Set `OCR_ENGINE=paddleocr` in `.env`

### Tesseract (Alternative)
```bash
# Windows: Download installer from https://github.com/UB-Mannheim/tesseract/wiki
# macOS: brew install tesseract
# Linux: apt install tesseract-ocr
```
Set `OCR_ENGINE=tesseract` and `TESSERACT_CMD=/path/to/tesseract` in `.env`

---

## Troubleshooting

### Backend won't start
- Check database connection: `psql $DATABASE_URL`
- Verify all `.env` variables are set
- Check Python version: `python --version` (must be 3.11+)

### Frontend build errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (must be 20+)

### Database migration errors
- Reset database: `alembic downgrade base && alembic upgrade head`
- Check DATABASE_URL format: `postgresql+asyncpg://user:pass@host:5432/db`

### AI requests failing
- Verify Groq API key is valid
- Check API quota: https://console.groq.com
- Use a Developer-plan model: `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, or `qwen/qwen3.8-27b`
- Enterprise-only models (`llama-3.3-70b-versatile`) will return 404 on standard accounts

### File uploads failing
- Verify Supabase Storage bucket exists
- Check `SUPABASE_SERVICE_ROLE_KEY` has storage permissions
- Ensure `MAX_FILE_SIZE_MB` is reasonable (default: 20MB)

---

## Architecture Overview

```
┌─────────────┐
│   Browser   │
│  (SvelteKit)│
└──────┬──────┘
       │ HTTP/REST
       │
┌──────▼──────────────────────┐
│   FastAPI Backend           │
│  ┌──────────────────────┐  │
│  │  API Routes (v1)     │  │
│  └──────┬───────────────┘  │
│         │                   │
│  ┌──────▼───────────────┐  │
│  │  Service Layer       │  │
│  │  (Business Logic)    │  │
│  └──────┬───────────────┘  │
│         │                   │
│  ┌──────▼───────────────┐  │
│  │  Repository Layer    │  │
│  │  (Data Access)       │  │
│  └──────┬───────────────┘  │
│         │                   │
│  ┌──────▼───────────────┐  │
│  │  AI Engine           │  │
│  │  • Groq Provider     │  │
│  │  • Prompt Templates  │  │
│  │  • Response Parser   │  │
│  └──────────────────────┘  │
└─────────────────────────────┘
       │              │
       │              │
┌──────▼──────┐ ┌────▼─────────┐
│  PostgreSQL │ │   Supabase   │
│  (Supabase) │ │   Storage    │
└─────────────┘ └──────────────┘
```

---

## Tech Stack Summary

| Layer | Technology |
|-------|-----------|
| **Frontend** | SvelteKit + TypeScript + TailwindCSS |
| **Backend** | FastAPI + SQLAlchemy + Pydantic |
| **Database** | PostgreSQL (Supabase) |
| **Auth** | Supabase Auth + JWT |
| **Storage** | Supabase Storage |
| **AI** | Groq API (provider-independent) |
| **OCR** | PaddleOCR / Tesseract |
| **Cache** | Redis |
| **Migrations** | Alembic |

---

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` — Create account
- `POST /api/v1/auth/login` — Email/password login
- `POST /api/v1/auth/google` — Google OAuth
- `POST /api/v1/auth/refresh` — Refresh access token
- `POST /api/v1/auth/logout` — Invalidate session

### Content Generation
- `POST /api/v1/summaries` — Generate summary
- `POST /api/v1/summaries/from-file` — Summary from file
- `POST /api/v1/explanations` — Generate explanation
- `POST /api/v1/quizzes` — Generate quiz
- `POST /api/v1/quizzes/{id}/submit` — Submit answers

### User Data
- `GET /api/v1/dashboard` — Home dashboard
- `GET /api/v1/analytics/dashboard` — Full analytics
- `GET /api/v1/history` — Learning history
- `GET /api/v1/users/me` — Current user profile

### File Management
- `POST /api/v1/files` — Upload file
- `GET /api/v1/files` — List uploads
- `DELETE /api/v1/files/{id}` — Delete file

---

## Next Steps

1. **Set up Supabase project** and get credentials
2. **Get Groq API key** from console.groq.com
3. **Configure environment files** (`.env` for both backend and frontend)
4. **Run database migrations** with Alembic
5. **Start backend** with `uvicorn app.main:app --reload`
6. **Start frontend** with `npm run dev`
7. **Create a user account** and start testing!

---

## Support

- Report issues: https://github.com/your-repo/issues
- Email: support@gyanguru.com
- Documentation: See `readme.md` and inline code comments
