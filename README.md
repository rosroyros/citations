# Citation Validator - AI Engineering Context

## Identity
APA 7th edition citation validator using dual LLM providers (GPT-5-mini-med + Gemini-2.5-Flash A/B testing) with Async Polling architecture and Static Site Generation (PSEO) for SEO.

Important: connect to the server via `ssh deploy@178.156.161.140`

## Test Job Indicator
**Purpose**: Automatically detect and flag test submissions to separate them from production analytics.

**Usage**: Include `"testtesttest"` anywhere in your citation text to mark it as a test job.

**Benefits**:
- Test jobs are automatically excluded from dashboard metrics
- Helps maintain clean analytics data
- Prevents test traffic from skewing production statistics

**Example**:
```
Smith, J. (2023). testtesttest: A study on validation methods. Journal of Testing, 45(2), 123-145.
```

## Tech Stack
- **Backend**: Python 3.x, FastAPI, Uvicorn, Pydantic, Dotenv.
- **Frontend**: React 19, Vite 7, React Router 7, Tiptap (Rich Text), Tailwind (inferred/standard).
  - **Key Components**: `ValidationLoadingState` (Progressive Reveal), `ValidationTable` (Results).
- **Testing**: Pytest (Backend), Vitest (Frontend Unit), Playwright (E2E).
- **Infrastructure**: VPS (Ubuntu), Nginx (Reverse Proxy + Static), Systemd.
- **Services**: OpenAI + Google Gemini (LLM A/B Testing), Polar SDK (Payments/Webhooks).
- **Tooling**: `bd` (Beads Issue Tracker), `pip` (Python deps), `npm` (Node deps).

## Architecture
- **Async Polling**: `POST /api/validate/async` -> Job ID -> `GET /api/jobs/{job_id}` (2s poll) -> Results.
- **Job Storage**: In-memory with 30min TTL.
- **PSEO**: Static site generator (`backend/pseo`) builds `cite-{source}-apa` pages with inline mini-checker.
- **Gating**: Free tier limit (10), Polar integration for credits.

### Async Flow
```
User → Frontend → POST /api/validate/async → Background Worker
                          ↓                          ↓
                       Job ID                  LLM Processing
                          ↓                          ↓
                   Polling Loop ← GET /api/jobs/{job_id} ← Job Storage
                          ↓
                      Results
```

### API Payloads
**Request**: `POST /api/validate/async`
```json
{ "citations": ["Smith, J. (2020). Book title. Publisher."] }
```
**Response**:
```json
{ "job_id": "uuid", "status": "processing" }
```
**Poll**: `GET /api/jobs/{job_id}` -> `200 OK`
```json
{ "status": "completed", "results": [...], "partial": false }
```
**Upgrade Event**: `POST /api/upgrade-event` -> `200 OK`
```json
{ "event": "clicked_upgrade|modal_proceed|success_page", "job_id": "uuid" }
```

## Dashboard
- **Purpose**: Operational monitoring (Jobs, Stats, Citation Logging, A/B Testing).
- **Stack**: FastAPI (Port 4646), SQLite (`dashboard/data/validations.db`).
- **Ingestion**: Cron jobs parse `app.log` and `citations.log` -> SQLite.
- **Frontend**: Static HTML served by FastAPI (`dashboard/static/`).
- **Provider Column**: Displays which AI model handled each request (GPT-5-mini-med or Gemini-2.5-Flash).
- **Access**: Internal tool, no auth (dev), firewall protected (prod).

## Upgrade Funnel
Tracks conversion (Locked->Checkout) via log parsing + event endpoints.
- **Flow**: "Partial results" log sets `upgrade_state="locked"`. Frontend POSTs `clicked_upgrade`/`modal_proceed` -> `UPGRADE_WORKFLOW` log.
- **Parser**: Appends events to DB `upgrade_state` CSV (e.g. `"locked,clicked"`).
- **UI**: 4 fixed icons (🔒🛒💳✅), inactive=grey.

## Key Paths
- **Root**: `/Users/roy/Documents/Projects/citations`
- **Backend**: `backend/`
  - App Entry: `backend/app.py`
  - Config: `backend/.env`
  - PSEO Builder: `backend/pseo/`
- **Frontend**: `frontend/frontend/`
  - Config: `frontend/frontend/package.json`
  - Build Output: `frontend/frontend/dist`
- **Docs**: `README.md`.
- **Logs**: `backend/logs/`, `backend/test_output/`.

## User Flow
1. **Entry**: User lands on Home or PSEO page (e.g., `cite-youtube-apa`).
2. **Action**: Input text (Manual/Copy-Paste) -> Click "Check Citation".
3. **Process**:
   - Frontend: `POST /api/validate/async`.
   - Backend: Queues job (In-Memory).
   - Poll: Frontend checks `/api/jobs/{job_id}` every 2s.
4. **Core Logic**:
   - **LLM Providers**: `backend/providers/openai_provider.py` (GPT-5-mini-med) + `backend/providers/gemini_provider.py` (Gemini-2.5-Flash). Frontend randomly assigns users to model_a or model_b for A/B testing.
   - **System Prompt**: `backend/prompts/validator_prompt_optimized.txt` defines APA 7 rules and output format.
   - Consistency tests ensure deterministic output.
5. **UX**: Progressive Reveal + Status Rotator (Simulates detailed analysis).
6. **Result**: Structured feedback (Correct/Incorrect + specific rule violations).
7. **Gating**:
   - **Free User Limit**: 10 validations per session/user.
   - **Over Limit**: Citations are still processed, but results are **hidden (locked)** in the UI.
   - **Unlock**: Free users must click to reveal results (engagement tracking).
   - **Polar Integration**: Handles paywall/credits for paid tiers.

## Data Persistence
- **Volatile**: Job status/results (In-memory `jobs` dict in `app.py`). **Restarting backend clears active jobs.**
- **Persistent**:
   - **Dashboard Logs**: `dashboard/data/validations.db` (SQLite) - Stores parsed validation metadata.
    - `upgrade_state` column: CSV of upgrade funnel events (locked,clicked,modal,success)
   - **Citation Logs**: `/opt/citations/logs/citations.log` (Parsed by Cron) - Stores raw citation text (if enabled).
   - **Application Logs**: `/opt/citations/logs/app.log` - General application events.

## Workflows
- **Dev**:
  1. `bd show <id>` & `bd update <id> --status in_progress`.
  2. Backend: `cd backend && python3 -m uvicorn app:app --reload`.
  3. Frontend: `cd frontend/frontend && npm run dev`.
- **Test**:
  - Backend: `python3 -m pytest`.
  - Frontend: `npm test` (Unit), `npm run test:e2e` (Playwright).
  - **Production E2E**: `deploy_prod.sh` (runs Hybrid E2E suite).
- **Deploy**:
  1. `git commit -am "feat: description"`.
  2. `git push origin main`.
  3. `./deploy_prod.sh [user@host]` (Deploy + Verify).
     - Default host: `deploy@178.156.161.140`.
  4. PSEO: `python3 regenerate_cite_specific_pages.py` -> SCP to `/dist`.

## Environment
- **Local**: Backend `:8000`, Frontend `:5173`.
- **Prod**: `178.156.161.140`, `/opt/citations`.
  - **SSH**: `ssh deploy@178.156.161.140`
  - username: deploy
- **Public URL**: `https://citationformatchecker.com`
- **Env Vars**: `OPENAI_API_KEY`, `GEMINI_API_KEY`, `CITATION_LOGGING_ENABLED`, `MOCK_LLM`, `BASE_URL`.
- **Dashboard**: `http://100.98.211.49:4646` (Internal IP/VPN only).
  - **Note**: Public access (`/dashboard` on main domain) is blocked by Nginx.

## Critical Context
- **Do NOT use**: `pseo/templates/layout.html` (Old). Use `pseo/builder/templates/layout.html`.
- **Commit Style**: `<type>: <description>` (e.g., `feat: add parser`).
- **Issues**: Use `bd` CLI. Do not use Markdown TODOs.
