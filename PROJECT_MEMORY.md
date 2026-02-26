# Project Memory

## Tech Stack & Architecture
- **Frontend**: Next.js 16 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Python FastAPI + SQLAlchemy + Alembic (PostgreSQL)
- **Port**: 3522 (frontend dev), 8000 (backend)
- **Design**: Plus Jakarta Sans (headings) + Work Sans (body), Lucide icons
- **Auth**: JWT-based (httpOnly cookies), protected routes via middleware
- **API prefix**: /api (all backend routes)

## File Structure
### Frontend (Next.js App Router)
- `src/app/layout.tsx` — Root layout with fonts
- `src/app/(auth)/` — Auth pages (login, register)
- `src/components/auth/` — login-form, register-form, protected-route
- `src/components/layout/` — dashboard-layout, sidebar
- `src/hooks/` — use-auth, use-theme
- `src/lib/` — auth.ts, theme.ts, utils.ts
- `src/types/` — auth.ts, index.ts, navigation.ts

### Backend (FastAPI)
- `backend/main.py` — App entry, CORS, router includes
- `backend/app/core/` — config, auth, security, constants
- `backend/app/models/models.py` — SQLAlchemy models
- `backend/app/routers/` — auth, scraping, competitors, platforms, api_keys, ai_generation
- `backend/app/schemas/` — Pydantic schemas (ai_generation, competitor, schemas)
- `backend/app/services/` — ai_service, competitor_service, twitter_scraper
- `backend/app/db/database.py` — DB connection, engine, Base

## Patterns & Conventions
- Frontend: App Router file-based routing, (auth) route group
- Backend: Router → Schema → Service → Model layered architecture
- Theme: localStorage-based dark/light/system toggle
- Protected routes: `protected-route.tsx` wrapper component
- API: RESTful, /api prefix, JSON responses

## Completed Stories
### US-001: Project Setup & Design Tokens [skipped — scaffolded by setup step]
- Initial Next.js + Tailwind + shadcn/ui setup
- Design tokens, fonts, eslint config

### US-002: Database Schema & Auth Models [verified]
- SQLAlchemy models for users, competitors, platforms, content
- Alembic migrations, JWT auth endpoints
- Files: backend/app/models/models.py, backend/app/routers/auth.py, backend/app/core/security.py

### US-003: Competitor Profile Management [verified]
- CRUD for competitor profiles
- Files: backend/app/routers/competitors.py, backend/app/schemas/competitor.py, backend/app/services/competitor_service.py

### US-004: Twitter Scraping Integration [skipped]
- Scrapling-based Twitter scraping service
- Files: backend/app/services/twitter_scraper.py, backend/app/routers/scraping.py

### US-005: AI Content Generation Service [verified]
- AI-powered content generation with templates
- Files: backend/app/services/ai_service.py, backend/app/routers/ai_generation.py, backend/app/schemas/ai_generation.py

### US-006: Smart Scheduler Backend [running]
### US-007: Analytics Backend [running]
### US-008: Frontend - Authentication & Layout [running]
- Auth pages, dashboard layout, sidebar, protected routes
- Files: src/app/(auth)/, src/components/auth/, src/components/layout/
