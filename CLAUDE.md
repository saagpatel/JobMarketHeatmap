# Job Market Heatmap

Local Tauri 2 desktop app — ingests job postings from Adzuna API, extracts skills via spaCy NLP, renders 5 interactive visualizations. All data stays local in SQLite. Personal research tool, not a product.

## Stack

See [README Tech Stack](README.md#tech-stack) for manifest/lockfile versions. The frontend uses React 18, TypeScript 7, and Vite 6; the desktop shell is Tauri 2. The FastAPI sidecar uses the pinned packages in `sidecar/requirements.txt`.

Use pnpm with `pnpm-lock.yaml`; no Node or pnpm version is enforced. Python 3.12 is the documented setup convention, not an enforced runtime pin. Create `sidecar/.venv` with that interpreter as shown in the README; the packaging script uses this environment.

## Build / Test / Run

See [README verification](README.md#verification) for repository-root fixture tests, frontend build/typecheck, Rust formatting, prerequisites, and conditional browser checks. Use the documented `sidecar/.venv` environment. [Desktop development](README.md#desktop-run-separate-integration-lane) starts the sidecar/database/scheduler and is a separate integration lane.

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
- Python: type hints on all signatures; Black is a style preference, but no formatter/linter/typecheck tooling is configured in the manifests
- All FastAPI routes return typed Pydantic response models
- Parameterized queries only — no raw SQL string concatenation

## Constraints

- **API credentials**: store Adzuna `app_id` / `app_key` via `tauri-plugin-store` in credentials.json in the app data directory; never in `.env` files or source code
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

See [README Tech Stack](README.md#tech-stack) for current dependency versions and [README prerequisites](README.md#prerequisites) for Node, pnpm, and Python setup policy.

## How To Run

Follow [README installation](README.md#installation) first, then [desktop development](README.md#desktop-run-separate-integration-lane), including building the host-specific sidecar binary before running the desktop app.

## Known Risks

- Do not store Adzuna `app_id` or `app_key` in `.env` files or source code — use `tauri-plugin-store` in the app data directory
- Do not add features outside the current phase in IMPLEMENTATION-ROADMAP.md
- Do not use class components — hooks only in React
- Do not call FastAPI from `useEffect` on mount without user action — gate behind button or scheduler callback
- Do not use D3 for the co-occurrence graph — vis-network is the locked choice
- Do not aggregate data for commercial use or distribution — personal use only per Adzuna ToS

## Next Recommended Move

Use this context plus the README and supporting docs to resume the next active task, then promote the repo beyond minimum-viable by capturing a dedicated handoff, roadmap, or discovery artifact.

<!-- portfolio-context:end -->
