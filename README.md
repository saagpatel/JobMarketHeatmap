# Job Market Heatmap

[![Python](https://img.shields.io/badge/Python-3776ab?style=flat-square&logo=python)](#) [![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](#)

> See the job market as a map — where skills cluster, salaries land, and demand trends are moving.

A macOS desktop app that ingests job postings from the Adzuna API, extracts skills with spaCy NLP, normalizes job titles into canonical roles, and renders five interactive visualizations: a geographic heatmap, skill frequency chart, salary box plots, skill co-occurrence graph, and demand trend lines. Data syncs nightly at 2 AM automatically.

## Features

- **Geographic heatmap** — job density by city on an interactive Leaflet map
- **Skill frequency chart** — ranked skill demand extracted via spaCy + ESCO taxonomy
- **Salary box plots** — salary distribution by role with outlier detection
- **Skill co-occurrence graph** — vis-network graph of which skills appear together
- **Demand trend lines** — time-series view of skill and role demand shifts
- **Nightly sync** — APScheduler runs Adzuna API sync at 2 AM without intervention

## Quick Start

### Prerequisites
- macOS (Apple Silicon or Intel) for the desktop app
- Node.js 18+ supported by Vite 6, and pnpm (the frozen-lockfile checks below were run with pnpm 12)
- Python 3.12 for the pinned sidecar environment: `numpy==2.5.3` requires Python >=3.12
- Rust and Xcode command-line tools for the separate desktop/Rust build lane
- An [Adzuna API account](https://developer.adzuna.com/) for live ingestion only; fixture tests need no account or credentials

### Installation

Run from the repository root. Keep Python dependencies in the ignored environment expected by `sidecar/build_sidecar.sh`:

```bash
pnpm install --frozen-lockfile --ignore-scripts
python3.12 -m venv sidecar/.venv
sidecar/.venv/bin/python -m pip install -r sidecar/requirements.txt
```

Installation downloads dependencies. The requirements already include the hash-pinned `en_core_web_sm` model; a separate `spacy download` is unnecessary. Use that environment's Python for every Python check.

### Verification

Run these commands from the repository root after installation:

```bash
# Focused deterministic role-normalization tests
sidecar/.venv/bin/python -m pytest sidecar/tests/test_role_normalizer.py -q

# Broader sidecar fixture suite and dependency compatibility
sidecar/.venv/bin/python -m pytest sidecar/tests/ -q
sidecar/.venv/bin/python -m pip check

# Frontend typecheck and production bundle (package.json: tsc && vite build)
pnpm build

# Rust formatting check; does not compile or launch the desktop app
cargo fmt --manifest-path src-tauri/Cargo.toml -- --check
```

The existing Python tests use synthetic jobs, an in-memory SQLite fixture, local taxonomy/salary/model files, mocked Adzuna HTTP responses, and mocked sync credentials/fetches. They do not start `sidecar/main.py`, its scheduler, or the desktop app, and do not use the personal database. Frontend build output is written to ignored `dist/`; it does not start a server. A formatting failure reports existing Rust formatting differences; do not run a rewriting formatter just to verify a change.

Python lint/format/typecheck tooling and frontend unit/browser test runners are not configured in the checked-in manifests. Record those checks as unavailable rather than inventing `pnpm test` or lint commands. The CodeQL workflow targets `feat/full-build` for push/PR events plus scheduled/manual runs; it does not establish that the above checks ran for a `main` PR. Record local commands and GitHub check results separately.

For a UI/chart change, additionally inspect the changed view and empty/error states in a browser using synthetic data. A separate frontend can be served with `pnpm dev --host 127.0.0.1 --port 1422 --strictPort`. Before loading it, intercept every `http://localhost:8008/**` request with fixture responses and block or mock external map tiles. Keep the real sidecar stopped, avoid credentials/Sync Now/Test connection, and use a dedicated free test port. The repository has no checked-in browser mock harness, so arranging those interceptions is a prerequisite; otherwise record browser verification as unavailable. Browser checks are unnecessary for pure documentation changes.

### Desktop run (separate integration lane)

On macOS, with the Rust/Xcode prerequisites and installed sidecar environment, the host-specific binary configured by `src-tauri/tauri.conf.json` must be built before desktop development:

```bash
bash sidecar/build_sidecar.sh
pnpm tauri dev
```

The packaging script writes generated sidecar build files and copies the binary into `src-tauri/binaries/`. Desktop startup launches the sidecar, creates or opens `~/.job-market-heatmap/data.db`, and starts its scheduler. Treat this as a deliberate integration run, not a fixture smoke check. Live sync and Test connection can call Adzuna. Do not delete or replace the personal database to simulate a fresh install; database, scheduler, provider, and desktop acceptance require separate deliberate validation.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Desktop shell | Tauri 2 (Rust) |
| Frontend | React 18 + TypeScript, Vite |
| Maps | Leaflet + react-leaflet + leaflet.heat |
| Charts | Recharts, vis-network |
| Backend sidecar | FastAPI + uvicorn (Python 3.12) |
| NLP | spaCy 3 (en_core_web_sm) + ESCO taxonomy |
| Scheduler | APScheduler (nightly 2 AM) |
| Storage | SQLite at ~/.job-market-heatmap/data.db |

## License

MIT
