# Job Market Heatmap — Implementation Roadmap

## Architecture

### System Overview
```
[Tauri 2 Shell (Rust)]
    │
    ├── spawns/manages → [FastAPI Sidecar (Python, :8008)]
    │                         │
    │                         ├── [APScheduler] → nightly Adzuna ingestion
    │                         ├── [spaCy NLP pipeline] → skill extraction
    │                         ├── [Role Normalizer] → title → canonical role
    │                         ├── [Salary Resolver] → BLS fallback for vague listings
    │                         └── [SQLite DB] ~/.job-market-heatmap/data.db
    │
    └── renders → [React 18 + TypeScript frontend]
                      │
                      ├── HTTP fetch → FastAPI /api/v1/* endpoints
                      ├── [Leaflet + react-leaflet] → Geographic heatmap
                      ├── [Recharts] → Skill bar chart, Salary box plots, Trend lines
                      └── [vis-network] → Skill co-occurrence graph
```

### File Structure
```
job-market-heatmap/
├── frontend/                          # React + TypeScript frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── GeoHeatmap.tsx         # Leaflet geographic heatmap
│   │   │   ├── SkillBarChart.tsx      # Recharts bar: skills ranked by frequency
│   │   │   ├── SalaryBoxPlot.tsx      # Recharts box: salary distribution by role
│   │   │   ├── CoOccurrenceGraph.tsx  # vis-network: skill cluster graph
│   │   │   ├── TrendLines.tsx         # Recharts line: skill demand over time
│   │   │   ├── FilterPanel.tsx        # Role/location/date range filters
│   │   │   ├── StatusBar.tsx          # Last sync time, job count, sync button
│   │   │   └── SettingsModal.tsx      # API key entry, schedule config
│   │   ├── hooks/
│   │   │   ├── useJobData.ts          # React Query hooks for all API calls
│   │   │   └── useSyncStatus.ts       # Polling sidecar /health for sync state
│   │   ├── types/
│   │   │   └── index.ts               # All shared TypeScript interfaces
│   │   ├── lib/
│   │   │   └── api.ts                 # Typed axios wrapper for FastAPI endpoints
│   │   ├── App.tsx                    # Root: tab nav (Map/Skills/Salary/Graph/Trends)
│   │   └── main.tsx                   # Vite entry point
│   ├── index.html
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── sidecar/                           # Python FastAPI backend
│   ├── main.py                        # FastAPI app entry + APScheduler setup
│   ├── routers/
│   │   ├── jobs.py                    # GET /api/v1/jobs/* — filtered job queries
│   │   ├── skills.py                  # GET /api/v1/skills/* — skill demand/co-occurrence
│   │   ├── salaries.py                # GET /api/v1/salaries/* — salary distributions
│   │   ├── geo.py                     # GET /api/v1/geo/* — location density data
│   │   ├── trends.py                  # GET /api/v1/trends/* — time-series demand
│   │   └── sync.py                    # POST /api/v1/sync/trigger, GET /api/v1/sync/status
│   ├── core/
│   │   ├── db.py                      # SQLite connection pool, get_db() dependency
│   │   ├── config.py                  # Pydantic settings (DB path, port, schedule time)
│   │   └── scheduler.py               # APScheduler job definitions
│   ├── services/
│   │   ├── adzuna_client.py           # Adzuna API wrapper — all requests go here
│   │   ├── nlp_pipeline.py            # spaCy skill extraction + ESCO normalization
│   │   ├── role_normalizer.py         # Rule-based title → canonical role mapping
│   │   └── salary_resolver.py        # Vague salary → BLS estimate lookup
│   ├── data/
│   │   ├── role_taxonomy.json         # Canonical roles + keyword/regex rules
│   │   ├── esco_skills_subset.json    # ~500 IT skills with synonyms from ESCO
│   │   └── bls_wages_2024.json        # BLS mean wages by SOC code (static snapshot)
│   ├── migrations/
│   │   └── 001_initial.sql            # Full schema DDL
│   ├── requirements.txt
│   └── build_sidecar.sh               # PyInstaller build script → outputs to src-tauri/binaries/
│
├── src-tauri/                         # Rust/Tauri desktop shell
│   ├── src/
│   │   ├── main.rs                    # Tauri app entry, sidecar spawn/shutdown
│   │   └── lib.rs                     # Tauri commands (get_credentials, set_credentials)
│   ├── binaries/                      # PyInstaller output goes here (gitignored)
│   │   └── .gitkeep
│   ├── capabilities/
│   │   └── default.json               # Tauri permissions: sidecar, shell, store
│   └── tauri.conf.json               # App config, externalBin, bundle settings
│
├── package.json                       # Workspace root: scripts for dev + build
└── CLAUDE.md
```

---

## Data Model

```sql
-- migrations/001_initial.sql

CREATE TABLE raw_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    adzuna_id       TEXT NOT NULL UNIQUE,          -- Adzuna's own job ID (dedup key)
    title           TEXT NOT NULL,
    company         TEXT,
    location_city   TEXT,
    location_region TEXT,
    location_lat    REAL,
    location_lon    REAL,
    salary_min      REAL,                          -- NULL if not provided
    salary_max      REAL,                          -- NULL if not provided
    salary_is_estimated INTEGER DEFAULT 0,        -- 1 = BLS fallback was used
    description     TEXT NOT NULL,
    canonical_role  TEXT,                          -- output of role_normalizer
    source          TEXT DEFAULT 'adzuna',
    fetched_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_raw_jobs_canonical_role ON raw_jobs(canonical_role);
CREATE INDEX idx_raw_jobs_location_city ON raw_jobs(location_city);
CREATE INDEX idx_raw_jobs_fetched_at ON raw_jobs(fetched_at);
CREATE INDEX idx_raw_jobs_salary_min ON raw_jobs(salary_min);

CREATE TABLE job_skills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER NOT NULL REFERENCES raw_jobs(id) ON DELETE CASCADE,
    skill_raw   TEXT NOT NULL,                     -- extracted token before normalization
    skill_norm  TEXT NOT NULL,                     -- ESCO canonical skill name
    confidence  REAL DEFAULT 1.0                  -- spaCy pattern match confidence
);
CREATE INDEX idx_job_skills_skill_norm ON job_skills(skill_norm);
CREATE INDEX idx_job_skills_job_id ON job_skills(job_id);

CREATE TABLE skill_cooccurrence (
    skill_a     TEXT NOT NULL,
    skill_b     TEXT NOT NULL,
    count       INTEGER DEFAULT 0,
    updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (skill_a, skill_b)
);
-- Materialized after each ingest run; rebuilt from scratch each time

CREATE TABLE sync_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at    DATETIME,
    jobs_fetched    INTEGER DEFAULT 0,
    jobs_inserted   INTEGER DEFAULT 0,
    jobs_skipped    INTEGER DEFAULT 0,   -- dedup hits
    status          TEXT DEFAULT 'running', -- running | success | error
    error_message   TEXT
);
```

---

## Type Definitions

```typescript
// frontend/src/types/index.ts

export interface Job {
  id: number;
  adzuna_id: string;
  title: string;
  company: string | null;
  location_city: string | null;
  location_region: string | null;
  location_lat: number | null;
  location_lon: number | null;
  salary_min: number | null;
  salary_max: number | null;
  salary_is_estimated: boolean;
  canonical_role: string | null;
  fetched_at: string; // ISO 8601
}

export interface SkillDemand {
  skill_norm: string;
  count: number;
  pct_of_postings: number; // count / total_jobs_in_filter * 100
}

export interface CoOccurrencePair {
  skill_a: string;
  skill_b: string;
  count: number;
  weight: number; // normalized 0–1 for edge thickness
}

export interface GeoPoint {
  lat: number;
  lon: number;
  city: string;
  count: number; // job density for heatmap intensity
}

export interface SalaryBucket {
  role: string;
  p25: number;
  median: number;
  p75: number;
  min: number;
  max: number;
  sample_size: number;
}

export interface TrendPoint {
  week: string;    // ISO week string e.g. "2025-W12"
  skill: string;
  count: number;
}

export interface SyncStatus {
  status: 'idle' | 'running' | 'error';
  last_sync: string | null; // ISO 8601
  last_jobs_fetched: number;
  error_message: string | null;
}

export interface FilterState {
  canonical_role: string | null;
  location_region: string | null;
  date_from: string | null;  // ISO 8601
  date_to: string | null;
}
```

```python
# sidecar/core/config.py — Pydantic settings

from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    db_path: Path = Path.home() / ".job-market-heatmap" / "data.db"
    port: int = 8008
    sync_hour: int = 2      # 2 AM nightly
    sync_minute: int = 0
    adzuna_results_per_page: int = 50
    adzuna_max_pages_per_run: int = 20   # 1000 jobs/run = 20 pages × 50 results
    adzuna_country: str = "us"

    class Config:
        env_file = ".env"   # Dev only — credentials are NOT in .env in prod

settings = Settings()
```

---

## API Contracts

### External APIs

| Service | Endpoint | Method | Auth | Rate Limit | Pagination | Purpose |
|---|---|---|---|---|---|---|
| Adzuna | `https://api.adzuna.com/v1/api/jobs/{country}/search/{page}` | GET | Query params `app_id` + `app_key` | ~250 req/day free tier | `page` param (1-indexed), `results_per_page` max 50 | Fetch job postings |
| Adzuna | `https://api.adzuna.com/v1/api/jobs/{country}/histogram` | GET | Same | Same | None | Salary histogram by search |
| BLS (static) | n/a — offline JSON snapshot | n/a | None | None | None | Fallback salary estimates |

### Internal FastAPI Endpoints

```
GET  /health                          → { status: "ok", db_connected: bool }
GET  /api/v1/jobs                     → Job[] (paginated, filter params)
GET  /api/v1/skills/demand            → SkillDemand[] (filter: role, region, date range)
GET  /api/v1/skills/cooccurrence      → CoOccurrencePair[] (top 200 pairs by count)
GET  /api/v1/geo/density              → GeoPoint[] (filter: role, date range)
GET  /api/v1/salaries/distribution    → SalaryBucket[] (filter: role, region)
GET  /api/v1/trends/skills            → TrendPoint[] (filter: skills[], date range)
GET  /api/v1/roles                    → string[] (all canonical role names)
GET  /api/v1/regions                  → string[] (all distinct location_region values)
POST /api/v1/sync/trigger             → { job_id: string } (kicks off background ingest)
GET  /api/v1/sync/status              → SyncStatus
```

---

## Role Taxonomy (rule-based, locked for v1)

```json
// sidecar/data/role_taxonomy.json — abbreviated
{
  "Software Engineer": {
    "keywords": ["software engineer", "software developer", "swe", "backend engineer", "frontend engineer", "full stack engineer", "fullstack"],
    "exclude": ["senior", "staff", "principal", "lead"]
  },
  "Senior Software Engineer": {
    "keywords": ["senior software engineer", "staff engineer", "principal engineer", "senior swe"]
  },
  "DevOps / Platform Engineer": {
    "keywords": ["devops", "platform engineer", "sre", "site reliability", "infrastructure engineer", "cloud engineer"]
  },
  "Data Engineer": {
    "keywords": ["data engineer", "analytics engineer", "etl engineer"]
  },
  "Data Scientist": {
    "keywords": ["data scientist", "ml engineer", "machine learning engineer", "ai engineer"]
  },
  "Security Engineer": {
    "keywords": ["security engineer", "appsec", "application security", "devsecops", "penetration tester", "pentester"]
  },
  "IT Support / SysAdmin": {
    "keywords": ["it support", "help desk", "sysadmin", "system administrator", "it specialist", "desktop support", "it engineer"]
  },
  "Engineering Manager": {
    "keywords": ["engineering manager", "vp engineering", "director of engineering", "head of engineering"]
  },
  "Product Manager": {
    "keywords": ["product manager", "product owner", "pm", "technical product manager", "tpm"]
  },
  "UNKNOWN": {
    "keywords": [],
    "description": "Fallback for unmatched titles"
  }
}
```

Normalization algorithm:
1. Lowercase the raw title
2. Strip seniority prefixes ("junior", "senior", "lead", "staff", "principal") for initial matching
3. Iterate taxonomy entries in order, check if any keyword is a substring of the title
4. First match wins. If no match → "UNKNOWN"
5. Re-apply seniority suffix if the base role has a seniority variant

---

## Dependencies

```bash
# === Frontend (from /frontend) ===
npm install react@18 react-dom@18
npm install @tanstack/react-query@5
npm install react-leaflet@4 leaflet@1.9 leaflet.heat@0.2
npm install recharts@2
npm install vis-network@9 vis-data@7
npm install axios@1.7
npm install -D @types/react@18 @types/leaflet@1 typescript@5 vite@5 @vitejs/plugin-react@4

# === Python sidecar (from /sidecar) ===
pip install fastapi==0.115 uvicorn[standard]==0.30
pip install pydantic-settings==2.5
pip install spacy==3.8
python -m spacy download en_core_web_sm
pip install apscheduler==3.10
pip install httpx==0.27     # async HTTP for Adzuna calls
pip install pyinstaller==6  # sidecar build only, not bundled

# === Tauri Rust plugins ===
# In src-tauri/Cargo.toml:
# tauri-plugin-store = "2"   (for macOS Keychain credential storage)
```

---

## Scope Boundaries

**In scope (v1):**
- Adzuna API as the single job data source (US market, `country=us`)
- Rule-based title normalization via role_taxonomy.json
- spaCy NLP skill extraction against ESCO subset
- 5 visualizations: geo heatmap, skill bar chart, salary box plots, co-occurrence graph, trend lines
- Nightly cron (2 AM) + manual sync trigger
- API credentials in macOS Keychain via tauri-plugin-store
- Filter panel: canonical role, location region, date range
- SQLite local storage at `~/.job-market-heatmap/data.db`

**Out of scope (never in v1):**
- USAJobs or The Muse API integration
- Claude API-based fuzzy role clustering
- Multi-user or cloud sync
- Export to CSV/Excel
- Natural language querying

**Deferred (v2+):**
- Salary trend over time (Phase 4 stretch goal, not Phase 2)
- Skill emergence alerts ("React Native up 34% this week")
- Company-specific breakdowns
- Leaflet heatmap → choropleth by metro area

---

## Security & Credentials

- **Adzuna `app_id` + `app_key`**: Stored in macOS Keychain via `tauri-plugin-store`. Set once in SettingsModal. Rust reads from Keychain and passes to sidecar via secure IPC at startup — never written to disk as plaintext, never in `.env`.
- **Data boundaries**: Nothing leaves the machine except outbound requests to `api.adzuna.com`. SQLite DB is local only.
- **Encryption at rest**: No additional encryption for the DB (personal tool). Keychain handles credential encryption.
- **PyInstaller binary**: Contains no credentials — credentials are injected at runtime from Keychain.
- **`.env` in dev**: A `.env` file with real keys is acceptable in local dev only. Must be in `.gitignore`. Never committed.

---

## Phase 0: Foundation (Week 1)

**Objective:** Project scaffolded, SQLite schema initialized, FastAPI sidecar boots and Tauri shell spawns it, basic health check works end-to-end.

**Tasks:**
1. Scaffold Tauri 2 project using `create-tauri-app` with React + TypeScript template — **Acceptance:** `pnpm tauri dev` opens a window showing "Hello Tauri"
2. Create `/sidecar/` directory, write `main.py` with FastAPI app and single `GET /health` route returning `{ status: "ok" }` — **Acceptance:** `uvicorn main:app --port 8008` and `curl localhost:8008/health` returns `{"status":"ok"}`
3. Wire Tauri sidecar: configure `tauri.conf.json` `externalBin`, write `main.rs` to spawn/kill sidecar on app open/close — **Acceptance:** `pnpm tauri dev` shows window AND sidecar process is visible in Activity Monitor; closing app kills sidecar
4. Write `migrations/001_initial.sql` and `core/db.py` — `get_db()` creates DB + runs migration on first boot — **Acceptance:** `python -c "from core.db import get_db; db = get_db()"` creates `~/.job-market-heatmap/data.db` with all 4 tables visible in DB Browser
5. Create `/sidecar/data/role_taxonomy.json` with all 9 canonical roles above — **Acceptance:** File validates as JSON with all required keys
6. Download ESCO IT skills subset: filter ESCO concept list for `http://data.europa.eu/esco/skill/` URIs in the IT/tech domain, export ~500 skills + altLabels to `esco_skills_subset.json` — **Acceptance:** File contains ≥400 entries, each with `preferred_label` and `alt_labels[]` array
7. Write `build_sidecar.sh` — runs PyInstaller in one-file mode, copies output to `src-tauri/binaries/main-aarch64-apple-darwin` — **Acceptance:** Script runs without error, binary exists at correct path

**Verification checklist:**
- [ ] `pnpm tauri dev` → window opens, Activity Monitor shows `main-aarch64-apple-darwin` process
- [ ] `curl localhost:8008/health` → `{"status":"ok","db_connected":true}`
- [ ] `sqlite3 ~/.job-market-heatmap/data.db ".tables"` → `raw_jobs job_skills skill_cooccurrence sync_log`
- [ ] `ls src-tauri/binaries/` → `main-aarch64-apple-darwin` present
- [ ] Closing app window → sidecar process disappears from Activity Monitor within 5 seconds

**Risks:**
- PyInstaller binary + spaCy model size: en_core_web_sm adds ~12MB but PyInstaller one-file bundles can be 80–150MB total. Acceptable for a desktop app — just slow to first-launch. Mitigation: use `--exclude-module` to strip unused spaCy components (tok2vec, ner) if size is a blocker. Fallback: ship spaCy model separately and reference it from a fixed path.
- Tauri sidecar triple naming: binary must be named `main-aarch64-apple-darwin` exactly. Easy to miss on first build. Mitigation: `rustc -Vv | grep host` to get correct triple, bake into build script.

---

## Phase 1: Data Ingestion Pipeline (Week 2)

**Objective:** Adzuna API → NLP → normalized records written to SQLite. Manual sync trigger works. Role normalization and skill extraction producing reasonable output on real data.

**Tasks:**
1. Install `tauri-plugin-store`, implement `set_credentials` and `get_credentials` Tauri commands in `lib.rs` — **Acceptance:** From browser devtools console, `invoke('set_credentials', { appId: 'test', appKey: 'test' })` persists to Keychain; `invoke('get_credentials')` retrieves them
2. Build `SettingsModal.tsx` — input fields for app_id/app_key, Save button calls Tauri commands — **Acceptance:** Entering and saving creds shows success toast; re-opening modal shows fields populated
3. Write `services/adzuna_client.py` — `fetch_jobs(query, location, page)` using `httpx` async client, returns typed `AdzunaJob` list — **Acceptance:** `python -m pytest tests/test_adzuna_client.py` with real credentials fetches ≥10 jobs for query "software engineer" in "san francisco"
4. Write `services/role_normalizer.py` — loads `role_taxonomy.json`, `normalize(title: str) → str` — **Acceptance:** Unit test: `normalize("Senior DevOps Engineer")` → `"DevOps / Platform Engineer"`, `normalize("Senior Site Reliability Engineer")` → `"DevOps / Platform Engineer"`, `normalize("VP of Engineering")` → `"Engineering Manager"` (≥15 test cases, ≥12 pass)
5. Write `services/nlp_pipeline.py` — loads `en_core_web_sm`, adds custom `EntityRuler` from `esco_skills_subset.json`, `extract_skills(text: str) → list[SkillMatch]` — **Acceptance:** `extract_skills("Looking for Python developer with Kubernetes and Terraform experience")` → returns skill_norm values `["Python", "Kubernetes", "Terraform"]`
6. Write `services/salary_resolver.py` — `resolve_salary(salary_min, salary_max, canonical_role) → (float, float, bool)` — returns (min, max, is_estimated). If both null, look up BLS mean wage for role and return (bls_mean * 0.8, bls_mean * 1.2, True) — **Acceptance:** `resolve_salary(None, None, "Software Engineer")` returns tuple where is_estimated=True and values are in $80k–$200k range
7. Write ingest orchestrator in `routers/sync.py` — `POST /api/v1/sync/trigger` kicks off background task: fetch pages → normalize role → extract skills → upsert to DB (by `adzuna_id`) → rebuild `skill_cooccurrence` table → write sync_log — **Acceptance:** Trigger sync, wait 60s, `sqlite3 ~/.job-market-heatmap/data.db "SELECT COUNT(*) FROM raw_jobs"` returns ≥50 rows; `skill_cooccurrence` has ≥20 rows
8. Set up `APScheduler` in `main.py` — `CronTrigger(hour=2, minute=0)` runs the same ingest job nightly — **Acceptance:** Set schedule to 1 minute from now in test config, observe sync_log entry created automatically

**Verification checklist:**
- [ ] Settings modal: enter real Adzuna creds → save → reopen → fields populated
- [ ] `POST localhost:8008/api/v1/sync/trigger` → status 202, sync_log shows new 'running' entry
- [ ] After sync: `SELECT COUNT(*) FROM raw_jobs` → ≥50
- [ ] After sync: `SELECT COUNT(*) FROM job_skills` → ≥200
- [ ] After sync: `SELECT COUNT(*) FROM skill_cooccurrence` → ≥20
- [ ] `SELECT canonical_role, COUNT(*) FROM raw_jobs GROUP BY canonical_role` → no more than 30% "UNKNOWN" rows

**Risks:**
- Adzuna daily rate limit (250 req/day free tier): 20 pages × 10 search queries = 200 requests/run. That's tight. Mitigation: start with 3 targeted search queries per run (e.g., "software engineer", "devops engineer", "data engineer") — 60 requests/run. Add more queries only if limit isn't hit. Fallback: cache raw API responses as JSON files before writing to DB so a failed run can be replayed without re-fetching.
- spaCy model not found in PyInstaller bundle: `en_core_web_sm` must be explicitly included in PyInstaller spec. Mitigation: add `--add-data "$(python -c 'import en_core_web_sm; print(en_core_web_sm.__path__[0])'):en_core_web_sm"` to PyInstaller command. Fallback: ship model as separate file next to binary.

---

## Phase 2: Core Visualizations (Weeks 3–4)

**Objective:** All 5 visualizations render with real data. Filter panel wired. This is the first phase where the tool is actually useful to open.

**Tasks:**
1. Build `FilterPanel.tsx` — dropdowns for Canonical Role (from `/api/v1/roles`), Region (from `/api/v1/regions`), date range picker — **Acceptance:** Selecting "DevOps / Platform Engineer" in role dropdown updates all charts to show filtered data
2. Build `StatusBar.tsx` — shows last sync time, total job count, manual "Sync Now" button that calls `POST /api/v1/sync/trigger` and polls `GET /api/v1/sync/status` until status ≠ 'running' — **Acceptance:** Click "Sync Now", button shows spinner, status bar shows "Syncing..." then updates to new last-sync timestamp on completion
3. Build `SkillBarChart.tsx` — horizontal bar chart (Recharts), top 20 skills by posting frequency, color-coded by role filter, tooltip shows count + % of postings — **Acceptance:** Chart renders with ≥10 bars; filtering by role updates data within 500ms
4. Build `GeoHeatmap.tsx` — Leaflet map centered on US, `leaflet.heat` layer rendering job density by city lat/lon, intensity = job count — **Acceptance:** Map shows heat concentrations in SF Bay Area, NYC, Seattle, Austin; clicking a city shows tooltip with "N jobs"
5. Build `SalaryBoxPlot.tsx` — custom Recharts box plot (using ComposedChart + custom shape) showing p25/median/p75/min/max per canonical role, asterisk indicator on estimated salaries — **Acceptance:** Box plot shows ≥5 roles with visible distribution; tooltip shows p25/median/p75 values; estimated-salary indicator visible
6. Build `CoOccurrenceGraph.tsx` — vis-network force graph, nodes = skills, edge thickness = co-occurrence count, node size = total appearances, top 50 skills + their edges — **Acceptance:** Graph renders with ≥30 nodes; dragging nodes works; clicking a node shows "Skill: X, appears in N jobs"
7. Build `TrendLines.tsx` — Recharts LineChart, X-axis = week (ISO), Y-axis = job count, one line per skill, filterable to show top 5 by default — **Acceptance:** Trend chart shows ≥4 weeks of data (requires 4 sync runs — use seed script for testing)
8. Write seed script `sidecar/scripts/seed_fake_data.py` — inserts 6 weeks of plausible job data so trend lines and box plots render meaningfully in dev — **Acceptance:** After running seed script, all 5 visualizations render with visible, non-empty data

**Verification checklist:**
- [ ] All 5 visualizations render without console errors
- [ ] Filter panel: changing role → all charts update
- [ ] Skill bar chart: ≥10 bars, percentages shown in tooltip
- [ ] Geo heatmap: heat visible in SF, NYC, Seattle
- [ ] Salary box plots: ≥5 roles, estimated salary asterisk visible
- [ ] Co-occurrence graph: ≥30 nodes, edges draggable
- [ ] Trend lines: ≥4 weeks, ≥4 skill lines
- [ ] Manual sync button: spinner during sync, timestamp updates on completion

**Risks:**
- Recharts box plot: Recharts doesn't have a native BoxPlot component. Must build using ComposedChart with custom SVG shapes. Budget an extra 3-4 hours for this specifically. Fallback: render as a simple min/median/max bar with whisker lines using ReferenceLine — less precise but shippable.
- Leaflet SSR/hydration in Tauri webview: react-leaflet may throw if window is not defined during init. Mitigation: lazy-load the map component with `React.lazy` and `Suspense`. Fallback: use `react-simple-maps` choropleth instead of Leaflet if Leaflet proves incompatible.
- vis-network bundle size: vis-network + vis-data together are ~2MB minified. Acceptable in a desktop app — just be aware it bloats the bundle. No mitigation needed unless load time is >3s.

---

## Phase 3: Polish + Scheduler UX (Week 5)

**Objective:** App is daily-drivable. Settings persist, sync schedule is configurable, error states handled, app feels intentional not janky.

**Tasks:**
1. Persist filter state to localStorage equivalent — use Tauri `tauri-plugin-store` to persist last-used FilterState so reopening the app restores previous view — **Acceptance:** Set filters, close app, reopen, filters are restored
2. Add sync schedule configuration to SettingsModal — hour/minute input, "Test connection" button that calls Adzuna with a single request and reports success/error — **Acceptance:** Changing sync time to 03:30 → APScheduler reschedules; test connection shows "Connected: 247 jobs found" or error message
3. Empty states for all 5 visualizations — "No data yet. Click Sync Now to fetch jobs." — **Acceptance:** Fresh DB shows helpful empty state instead of blank charts
4. Error boundary in React root — catch API errors, show inline error banner with retry button — **Acceptance:** Kill FastAPI sidecar while app is open, click any chart → error banner appears with "Backend unavailable — restart app"
5. App icon + window title — "Job Market Heatmap" — **Acceptance:** App appears with correct name and icon in Dock and ⌘+Tab switcher
6. End-to-end smoke test: fresh install simulation — delete `~/.job-market-heatmap/`, launch app, enter creds, trigger sync, all 5 charts populate — **Acceptance:** Full flow completes in <5 minutes with no manual intervention

**Verification checklist:**
- [ ] Cold launch: DB missing → app creates it and shows empty states
- [ ] Settings → enter creds → test connection → "Connected" message
- [ ] Sync Now → all 5 charts populate
- [ ] Close app → reopen → filters restored, sync history intact
- [ ] App in Dock: shows correct icon and name
- [ ] Kill sidecar manually → app shows error banner, not white screen

---

## Phase 4: Stretch Goals (Week 6, if time permits)

Only start Phase 4 if Phase 3 passes all verification checks.

- **Skill emergence alerts**: compute week-over-week % change per skill; surface skills with >20% growth in a "Trending Skills" badge on the skill bar chart
- **Search query config**: allow user to add/remove Adzuna search queries from Settings (instead of hardcoded "software engineer", "devops", "data engineer")
- **Export to CSV**: `GET /api/v1/export/jobs` endpoint + frontend download button
- **Salary trend line**: add salary_median over time as a secondary trend chart

---

## Testing Strategy

**Phase 0:** Manual verification only — file existence, process spawning, DB creation
**Phase 1:** Python unit tests for `role_normalizer`, `nlp_pipeline`, `salary_resolver` (15+ test cases each). Integration test: trigger sync, assert ≥50 rows in DB.
**Phase 2:** Visual smoke test for each chart. Seed data script for repeatable rendering tests.
**Phase 3:** Manual end-to-end flow on fresh DB. Error state testing by killing sidecar.

Test files live in `/sidecar/tests/`. Run with `pytest sidecar/tests/ -v`.
