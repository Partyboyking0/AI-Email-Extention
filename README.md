# AI Email Automation Assistant

A Gmail Chrome Extension (Manifest V3) with a FastAPI backend and ML pipeline for email summarization, smart replies, task extraction, usage analytics, and future fine-tuned Hugging Face/ONNX models.

## Phase Status

| Phase | Status |
|-------|--------|
| Phase 0 | Complete — POC scripts and latency report |
| Phase 1 | Complete — Popup-driven MV3 extension, FastAPI backend, LangChain HF integration |
| Phase 2 | In Progress — Client-side classifier, ONNX export scaffold, demo seed data |

Phase 1 was completed in the popup-driven shape requested (not the original auto-injected Gmail toolbar shape). See `docs/phase1_completion.md` for details.

## Quick Start

### Backend

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8001 --reload
```

### Extension

```powershell
npm install
npm run build:extension
```

Load `extension/dist` as an unpacked extension in `chrome://extensions`. After every extension build:

1. Open `chrome://extensions`.
2. Reload **AI Email Automation Assistant**.
3. Refresh Gmail.

### Useful Backend URLs

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8001/` | Root |
| `http://127.0.0.1:8001/health` | Health check |
| `http://127.0.0.1:8001/docs` | Swagger UI |
| `http://127.0.0.1:8001/metrics` | Prometheus metrics |

> **Note:** The backend runs on port `8001`. If an older stored setting points to `8000`, it auto-migrates on first run.

## How It Works

The extension is fully popup-driven — there is no automatic Gmail toolbar injection or automatic classification.

1. Open an email in Gmail.
2. Open the extension popup.
3. Click an action button (**Summarize**, **Smart Reply**, **Tasks**, or **Classify**).
4. The popup reads the currently open email on demand and sends it to the background worker.
5. The background worker calls the backend when available; otherwise falls back to local services.
6. Results are displayed inside the popup.

## Popup Tabs

**Actions** — Summarize · Smart Reply · Tasks · Classify

**Dashboard** — Emails processed today · Estimated time saved · Most used feature · Backend status · Refresh · Reset local usage

**Settings** — Backend URL and preferences

> **Gmail clipping:** If a long email shows **View entire message**, click that first. The extension can only read what Gmail has loaded into the page.

## Environment

Copy `.env.example` to `.env` and fill in the values.

```env
JWT_SECRET=<generated local secret>
JWT_ALGORITHM=HS256
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=sqlite:///./backend/app.db
DEMO_AUTH_SUBJECT=phase-1-demo-user
ENVIRONMENT=local
SENTRY_DSN=
SENTRY_TRACES_SAMPLE_RATE=0.0

# Hugging Face — leave blank to use local heuristic fallbacks
HF_SUMMARIZER_ENDPOINT=
HF_REPLY_ENDPOINT=
HF_API_TOKEN=
HF_USE_PROVIDER=true
HF_LOCAL_ENABLED=true
HF_LOCAL_SUMMARIZER_MODEL=google/flan-t5-small
HF_LOCAL_REPLY_MODEL=google/flan-t5-small
```

> **Security:** Never commit your `HF_API_TOKEN` or `JWT_SECRET`. Both are in `.gitignore` via `.env`.

### Python environment note

The default `python` on this machine may point to Miniconda. Run backend commands and tests explicitly with:

```powershell
& "$env:LOCALAPPDATA\Python\pythoncore-3.14-64\python.exe" -m pytest backend\tests
```

## Backend

FastAPI with SQLite (default) or Postgres. Redis is supported for cache and rate limiting with automatic in-memory fallback.

### Inference Order

**Summarization:** HF dedicated endpoint → local HF via LangChain LCEL → HF provider → local extractive fallback

**Reply generation:** HF dedicated endpoint → HF provider → local HF via LangChain LCEL → local tone-aware fallback

**Classification:** Backend heuristic classifier → extension keyword classifier

### API Routes

```
GET  /health
GET  /metrics
POST /api/auth/demo-token
POST /api/summarize
POST /api/reply
POST /api/classify
POST /api/tasks
POST /api/feedback
GET  /api/users/me/usage
POST /api/users/me/usage
GET  /api/users/me/preferences
DELETE /api/users/me   (GDPR delete)
```

### LangChain Integration

Prompts use LangChain Core `PromptTemplate` as the single source of truth, formatted through `PromptEngine` and chained via LCEL (`PromptTemplate | RunnableLambda | StrOutputParser`). Key files:

```
backend/app/services/prompt_templates.py
backend/app/services/prompt_engine.py
backend/app/services/local_hf.py
backend/app/services/hf_client.py
```

## ML Pipeline

Scaffold scripts exist in `ml/` for classifier, summarizer, reply generation, NER, and RLHF training. ML dependencies are **not** required for the current demo.

```
ml/configs/
ml/training/train_classifier.py
ml/training/train_summarizer.py
ml/training/train_reply_gen.py
ml/training/train_ner.py
ml/training/rlhf/reward_model.py
ml/training/rlhf/ppo_trainer.py
ml/evaluation/
ml/export/
```

RLHF safety gate: training requires at least 200 feedback examples.

### Phase 2 Classifier (In Progress)

- Extension-side keyword classifier: `extension/src/shared/classifier.ts`
- Backend heuristic classifier: `backend/app/services/classifier.py` (`heuristic-classifier-v3`)
- Demo seed data (24 examples including `opportunity` label): `ml/data/raw/classifier_demo.jsonl`
- Baseline macro F1 on seed data: **1.000**
- ONNX model slot: `extension/public/models/classifier/model.onnx` (not yet exported)

When training is ready, wire tokenization and `onnxruntime-web` inference into `extension/src/shared/classifier.ts`.

## Project Structure

```
extension/          MV3 Chrome extension
backend/            FastAPI application
ml/                 Training, evaluation, and export scripts
infra/              Docker Compose, Prometheus config
docs/               Phase docs, API docs, privacy data flow
.github/workflows/  CI pipeline
README.md
.env.example
.gitignore
PROJECT_CONTEXT.md
```

## Tests

```powershell
# Backend tests (24 passing)
backend\.venv\Scripts\python.exe -m pytest backend\tests

# Extension lint
npm --prefix extension run lint

# ML dry runs
backend\.venv\Scripts\python.exe ml\training\train_classifier.py --dry-run
backend\.venv\Scripts\python.exe ml\evaluation\eval_classifier.py
backend\.venv\Scripts\python.exe ml\export\export_onnx.py --dry-run

# Local HF smoke test
backend\.venv\Scripts\python.exe backend\scripts\check_local_hf.py --generate
```

> `PytestCacheWarning: could not create cache path ... Access is denied` is a known Windows sandbox issue and does not block tests.

## Infrastructure

`infra/docker-compose.yml` includes the FastAPI service, Redis, and Postgres with pgvector. The backend defaults to SQLite locally for ease of demo.

```powershell
# Full stack
docker compose -f infra/docker-compose.yml up
```

## Known Limitations

- Summarizer and reply generator are local heuristic fallbacks, not fine-tuned models yet.
- Gmail DOM extraction is best-effort and can be limited by Gmail clipping or collapsed quoted content.
- Demo auth is not real Google OAuth — it uses a local JWT for development only.
- Redis and Postgres are structurally supported but SQLite/memory fallback is the current default.
- Chrome Web Store publication requires privacy review, OAuth hardening, and permission audit.
- Backend usage sync should be rechecked after production auth is added.

## Next Steps

1. Continue Phase 2: train the classifier and wire real ONNX browser inference.
2. Configure Hugging Face endpoints via `docs/huggingface_setup.md` (`HF_SUMMARIZER_ENDPOINT`, `HF_REPLY_ENDPOINT`, `HF_API_TOKEN`).
3. Add real Google OAuth token exchange to replace demo JWT auth.
4. Replace SQLite with Postgres in Docker Compose for local dev parity with production.
5. Add a manual **Read selected text** fallback in popup for Gmail clipping edge cases.
6. Start classifier fine-tuning and ONNX export from the ML scaffold.