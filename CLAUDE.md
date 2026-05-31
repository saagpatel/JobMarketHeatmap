# Job Market Heatmap

Local Tauri 2 desktop app — ingests job postings from Adzuna API, extracts skills via spaCy NLP, renders 5 interactive visualizations. All data stays local in SQLite. Personal research tool, not a product.

## Stack

- **Tauri 2** — desktop shell, sidecar lifecycle, OS keychain for API credentials
- **React 18 + TypeScript** — frontend (strict mode, hooks only)
- **Vite 5** — frontend build
- **Recharts 3** — bar charts, box plots, trend lines
- **Leaflet.js 1.9 + react-leaflet 4** — geographic heatmap
- **vis-network 10** — skill co-occurrence force graph (locked: not D3)
- **FastAPI 0.115** — Python HTTP API, PyInstaller sidecar on `localhost:8008`
- **SQLite 3** — Python `sqlite3` stdlib; DB at `~/.job-market-heatmap/data.db`
- **spaCy 3.8 + en_core_web_sm** — NLP skill extraction
- **APScheduler 3.11** — in-process nightly cron inside FastAPI
- **PyInstaller 6** — bundles Python + deps into single binary
- **tauri-plugin-store** — API key storage (credentials.json in app data dir); hydrated to sidecar at startup

## Build / Test / Run

```bash
pnpm tauri dev          # full dev (frontend + Rust + sidecar)
pnpm build              # tsc && vite build (frontend only)
python -m pytest tests/ -v   # Python sidecar tests
ruff check src/ tests/       # Python lint
```

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| NLP | spaCy `en_core_web_sm` + custom patterns | Fast, local, no API cost |
| Taxonomy | ESCO open skills (~500 IT skills) | Structured synonyms, free |
| Title normalization | Rule-based regex + keyword match | Deterministic, auditable, ~80% accuracy |
| Salary inference | BLS Occupational Wage data | Transparent, labeled as estimate |
| Sidecar comm | HTTP on `localhost:8008` (not Tauri IPC) | Debuggable with curl |
| Scheduling | APScheduler inside FastAPI | No OS cron dependency |
| Graph viz | vis-network (not D3 force) | 10x less code for this use case |
| Geo tiles | OpenStreetMap via Leaflet | Zero rate limit, offline-capable |

## Conventions

- TypeScript strict — `unknown` + narrowing; no `any`, no `// @ts-ignore`
- Kebab-case files, PascalCase components, snake_case Python
- Conventional commits: `feat:`, `fix:`, `chore:`, `data:`
- Python: Black formatting, type hints on all signatures
- All FastAPI routes return typed Pydantic response models
- Parameterized queries only — no raw SQL string concatenation

## Constraints

- **API credentials**: store Adzuna `app_id` / `app_key` via `tauri-plugin-store` backed by macOS Keychain; never in `.env` files or source code
- **Scope gate**: implement only phases defined in IMPLEMENTATION-ROADMAP.md; no scope additions without updating it first
- **FastAPI calls**: gate behind button or scheduler callback — do not call from `useEffect` on mount without user action
- **Data use**: personal use only per Adzuna ToS; no commercial aggregation or distribution

## Status

Phases 0–2 complete (scaffold, ingestion, 5 visualizations + filter panel). Release-closeout (v1.0, CSP hardening, .dmg) not yet started. See IMPLEMENTATION-ROADMAP.md.

<!-- portfolio-context:start -->
# Portfolio Context

## What This Project Is

A local Tauri 2 desktop app that ingests job postings from the Adzuna API, normalizes them
against a rule-based role taxonomy, extracts skills using spaCy NLP, and renders 5 interactive
visualizations: geographic heatmap, skill demand bar chart, salary box plots, skill co-occurrence
network graph, and trend lines. All data stays local in SQLite. This is a personal research tool,
not a distributed product.

## Current State

**Phases 0–2 complete** (scaffold, ingestion pipeline, 5 visualizations + filter panel). Release-closeout cadence (v1.0 bump, CSP hardening, baseline Rust tests, .dmg packaging) not yet started.
See IMPLEMENTATION-ROADMAP.md for full phase details and acceptance criteria.

## Stack

- **Tauri 2** — desktop shell, sidecar lifecycle management, OS keychain for API credentials
- **React 18 + TypeScript** — frontend (strict mode, hooks only, no class components)
- **Vite 5** — frontend build tooling
- **Recharts 3** — bar charts, box plots, trend lines
- **Leaflet.js 1.9 + react-leaflet 4** — geographic heatmap
- **vis-network 10** — skill co-occurrence force graph (NOT D3 — vis-network is simpler for this use case)
- **FastAPI 0.115** — Python HTTP API, runs as PyInstaller sidecar on localhost:8008
- **SQLite 3** — via Python `sqlite3` stdlib, single DB file at `~/.job-market-heatmap/data.db`
- **spaCy 3.8 + en_core_web_sm** — NLP pipeline for skill extraction
- **APScheduler 3.11** — in-process nightly cron inside FastAPI sidecar
- **PyInstaller 6** — bundles Python + all deps into single binary for Tauri sidecar
- **tauri-plugin-store** — API key storage via Tauri store (credentials.json in app data dir); hydrated to sidecar memory at startup

## How To Run

```bash
pnpm tauri dev
```

## Known Risks

- Do not store Adzuna `app_id` or `app_key` in `.env` files or source code — use `tauri-plugin-store` backed by macOS Keychain
- Do not add features outside the current phase in IMPLEMENTATION-ROADMAP.md
- Do not use class components — hooks only in React
- Do not call FastAPI from `useEffect` on mount without user action — gate behind button or scheduler callback
- Do not use D3 for the co-occurrence graph — vis-network is the locked choice
- Do not aggregate data for commercial use or distribution — personal use only per Adzuna ToS

## Next Recommended Move

Use this context plus the README and supporting docs to resume the next active task, then promote the repo beyond minimum-viable by capturing a dedicated handoff, roadmap, or discovery artifact.

<!-- portfolio-context:end -->
