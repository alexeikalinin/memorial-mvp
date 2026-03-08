# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Memorial MVP is a digital memory preservation service with AI avatars. Users create memorial pages for deceased people, upload media (photos/videos/audio), add text memories, and chat with an AI avatar that responds based on those memories using RAG.

## Architecture

**Backend** (`backend/`): Python 3.11 + FastAPI + SQLAlchemy + SQLite (dev) / PostgreSQL (prod)

**Frontend** (`frontend/`): React 18 + Vite + React Router + Axios

**Key external services:**
- **OpenAI** — LLM (gpt-4-turbo-preview) + embeddings (text-embedding-3-small)
- **D-ID** or **HeyGen** — photo animation (controlled by `USE_HEYGEN` env var)
- **ElevenLabs** — TTS + custom voice cloning
- **Qdrant** (default) or **Pinecone** — vector DB for RAG (controlled by `VECTOR_DB_PROVIDER`)
- **Redis + Celery** — background task queue (with synchronous fallback when Redis unavailable)
- **AWS S3** (optional) — media storage (controlled by `USE_S3`)

**Data flow for avatar chat (RAG):**
1. User adds text memories → embeddings created via OpenAI → stored in Qdrant/Pinecone
2. User asks question → question embedded → similar memories retrieved → OpenAI generates response
3. Optional: ElevenLabs TTS generates audio response

**Media serving:** Files stored locally under `backend/uploads/`. Served via `/api/v1/media/{id}` endpoint. For D-ID animation, the backend needs a public URL (`PUBLIC_API_URL` in .env), typically via ngrok in development.

## Backend Structure

```
backend/app/
  main.py          # FastAPI app, CORS, router registration
  config.py        # Settings via pydantic-settings, reads from .env
  db.py            # SQLAlchemy engine/session setup
  models.py        # DB models: User, Memorial, Media, Memory, FamilyRelationship
  schemas.py       # Pydantic request/response schemas
  api/
    memorials.py   # Memorial CRUD + media upload + memories CRUD
    ai.py          # Photo animation, avatar chat, voice upload
    media.py       # Media file serving
    embeddings.py  # Embedding management endpoints
    family.py      # Family tree relationships
    s3.py          # S3 presigned URLs
    health.py      # Health check
  services/
    ai_tasks.py    # All AI integrations: D-ID, HeyGen, OpenAI, ElevenLabs, Qdrant, Pinecone
    media_service.py  # Image validation, optimization, thumbnail generation (Pillow)
    video_service.py  # Video validation, thumbnail generation (ffmpeg)
    s3_service.py     # AWS S3 operations
  workers/
    worker.py          # Celery tasks (animate_photo_task, create_memory_embedding_task)
    worker_simple.py   # Polling-based worker, no Redis required
```

**Important pattern:** When Redis/Celery is unavailable, endpoints fall back to synchronous execution of the same AI tasks. This fallback is scattered through `memorials.py` and `ai.py`.

**No authentication yet** — `owner_id` is hardcoded to `1` in memorials endpoints. Auth is a planned TODO.

## Frontend Structure

```
frontend/src/
  api/client.js          # Axios instance + all API methods (memorialsAPI, aiAPI, mediaAPI, embeddingsAPI, familyAPI)
  App.jsx                # Router: /, /memorials/new, /memorials/:id
  pages/
    Home.jsx             # Memorial list/creation entry point
    MemorialCreate.jsx   # Creation form
    MemorialDetail.jsx   # Tabbed view: media, memories, chat, family tree
  components/
    MediaGallery.jsx     # Photo/video gallery with animation controls
    MemoryList.jsx       # Memory CRUD UI
    AvatarChat.jsx       # Chat UI with audio playback
    FamilyTree.jsx       # Family relationships visualization
    Layout.jsx           # App shell/nav
```

Vite dev server proxies `/api` requests to `http://localhost:8000`.

## Development Commands

### Backend

```bash
cd backend
source .venv/bin/activate

# Run dev server (auto-reload)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest

# Run single test file
pytest tests/test_memorials.py

# Run Celery worker (requires Redis)
celery -A app.workers.worker worker --loglevel=info

# Run simple worker (no Redis)
python -m app.workers.worker_simple
```

### Frontend

```bash
cd frontend
npm install
npm run dev      # Dev server at http://localhost:5173
npm run build    # Production build
npm run lint     # ESLint
```

### Full stack startup

```bash
# Ensure Redis is running, then:
./start_all.sh
# Frontend must be started separately: cd frontend && npm run dev
```

## Environment Setup

Copy `backend/.env.example` to `backend/.env`. Minimum for local development without AI features:

```env
DATABASE_URL=sqlite:///./memorial.db
SECRET_KEY=dev-secret-key-change-in-production-min-32-chars
DEBUG=true
USE_S3=false
REDIS_URL=redis://localhost:6379/0
```

For AI features, add: `OPENAI_API_KEY`, `DID_API_KEY` or `HEYGEN_API_KEY`, `ELEVENLABS_API_KEY`.

For D-ID/HeyGen photo animation in dev, set `PUBLIC_API_URL` to an ngrok URL (D-ID needs a publicly accessible image URL ending in `.jpg`/`.png`).

DB tables are auto-created on startup via `Base.metadata.create_all()` — no migrations needed for dev.

## Key Design Notes

- **Vector DB choice:** Set `VECTOR_DB_PROVIDER=qdrant` (default) or `pinecone`. Qdrant runs locally at `http://localhost:6333`.
- **Photo animation provider:** Set `USE_HEYGEN=true` for HeyGen, otherwise D-ID is used.
- **Media thumbnails:** Generated automatically on upload for photos (small/medium/large) and videos (ffmpeg preview). Stored in `uploads/thumbnails/`.
- **Tests use SQLite in-memory** (`test.db`), overriding the DB dependency via FastAPI's `dependency_overrides`.
