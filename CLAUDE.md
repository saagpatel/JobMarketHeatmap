# Job Market Heatmap

## Overview
A local Tauri 2 desktop app that ingests job postings from the Adzuna API, normalizes them
against a rule-based role taxonomy, extracts skills using spaCy NLP, and renders 5 interactive
visualizations: geographic heatmap, skill demand bar chart, salary box plots, skill co-occurrence
network graph, and trend lines. All data stays local in SQLite. This is a personal research tool,
not a distributed product.

## Tech Stack
- **Tauri 2** — desktop shell, sidecar lifecycle management, OS keychain for API credentials
- **React 18 + TypeScript** — frontend (strict mode, hooks only, no class components)
- **Vite 5** — frontend build tooling
- **Recharts 2** — bar charts, box plots, trend lines
- **Leaflet.js 1.9 + react-leaflet 4** — geographic heatmap
- **vis-network 9** — skill co-occurrence force graph (NOT D3 — vis-network is simpler for this use case)
- **FastAPI 0.115** — Python HTTP API, runs as PyInstaller sidecar on localhost:8008
- **SQLite 3** — via Python `sqlite3` stdlib, single DB file at `~/.job-market-heatmap/data.db`
- **spaCy 3.8 + en_core_web_sm** — NLP pipeline for skill extraction
- **APScheduler 3.10** — in-process nightly cron inside FastAPI sidecar
- **PyInstaller 6** — bundles Python + all deps into single binary for Tauri sidecar
- **keytar (Rust tauri-plugin-store)** — API key storage in macOS Keychain, never plaintext

## Development Conventions
- TypeScript strict mode — no `any` types, no `// @ts-ignore`
- Kebab-case for files, PascalCase for React components, snake_case for Python
- Conventional commits: `feat:`, `fix:`, `chore:`, `data:`
- Python: Black formatting, type hints on all function signatures
- All FastAPI routes return typed Pydantic response models
- No raw SQL string concatenation — use parameterized queries only

## Current Phase
**Phase 0: Foundation**
See IMPLEMENTATION-ROADMAP.md for full phase details and acceptance criteria.

## Key Decisions
| Decision | Choice | Rationale |
|---|---|---|
| NLP skill extraction | spaCy `en_core_web_sm` + custom skill patterns | Fast, local, no API cost |
| Skill taxonomy | ESCO open skills taxonomy (subset, ~500 IT skills) | Structured synonyms, free |
| Title normalization | Rule-based taxonomy (regex + keyword match) | Deterministic, auditable, ~80% accuracy |
| Salary inference | BLS Occupational Wage data for "competitive" listings | Transparent, labeled as estimate |
| Sidecar comm | HTTP on localhost:8008 (not Tauri IPC) | Simpler, debuggable with curl |
| Scheduling | APScheduler inside FastAPI process | No OS cron dependency |
| Graph viz | vis-network (not D3 force) | 10x less code for this use case |
| Geo tile provider | OpenStreetMap via Leaflet (no API key needed) | Zero rate limit, offline-capable |

## Do NOT
- Do not store Adzuna `app_id` or `app_key` in `.env` files or source code — use `tauri-plugin-store` backed by macOS Keychain
- Do not add features outside the current phase in IMPLEMENTATION-ROADMAP.md
- Do not use class components — hooks only in React
- Do not call FastAPI from `useEffect` on mount without user action — gate behind button or scheduler callback
- Do not use D3 for the co-occurrence graph — vis-network is the locked choice
- Do not aggregate data for commercial use or distribution — personal use only per Adzuna ToS

<!-- portfolio-context:start -->
# Portfolio Context

## What This Project Is

A local Tauri 2 desktop app that ingests job postings from the Adzuna API, normalizes them
against a rule-based role taxonomy, extracts skills using spaCy NLP, and renders 5 interactive
visualizations: geographic heatmap, skill demand bar chart, salary box plots, skill co-occurrence
network graph, and trend lines. All data stays local in SQLite. This is a personal research tool,
not a distributed product.

## Current State

**Phase 0: Foundation**
See IMPLEMENTATION-ROADMAP.md for full phase details and acceptance criteria.

## Stack

- **Tauri 2** — desktop shell, sidecar lifecycle management, OS keychain for API credentials
- **React 18 + TypeScript** — frontend (strict mode, hooks only, no class components)
- **Vite 5** — frontend build tooling
- **Recharts 2** — bar charts, box plots, trend lines
- **Leaflet.js 1.9 + react-leaflet 4** — geographic heatmap
- **vis-network 9** — skill co-occurrence force graph (NOT D3 — vis-network is simpler for this use case)
- **FastAPI 0.115** — Python HTTP API, runs as PyInstaller sidecar on localhost:8008
- **SQLite 3** — via Python `sqlite3` stdlib, single DB file at `~/.job-market-heatmap/data.db`
- **spaCy 3.8 + en_core_web_sm** — NLP pipeline for skill extraction
- **APScheduler 3.10** — in-process nightly cron inside FastAPI sidecar
- **PyInstaller 6** — bundles Python + all deps into single binary for Tauri sidecar
- **keytar (Rust tauri-plugin-store)** — API key storage in macOS Keychain, never plaintext

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
