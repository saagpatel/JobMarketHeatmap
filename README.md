# Job Market Heatmap

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](https://github.com/saagpatel/JobMarketHeatmap)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tauri](https://img.shields.io/badge/Tauri-2-24C8DB?logo=tauri&logoColor=white)](https://tauri.app/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)

A macOS desktop app that ingests job postings from the Adzuna API, extracts skills with spaCy NLP, normalizes job titles into canonical roles, and renders five interactive visualizations — a geographic heatmap, skill frequency chart, salary box plots, skill co-occurrence graph, and demand trend lines.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop shell | Tauri 2 (Rust) |
| Frontend | React 18 + TypeScript, Vite |
| Maps | Leaflet + react-leaflet + leaflet.heat |
| Charts | Recharts, vis-network |
| Backend sidecar | FastAPI + uvicorn (Python 3.11) |
| NLP | spaCy 3 (`en_core_web_sm`) + ESCO skill taxonomy |
| Scheduler | APScheduler (nightly 2 AM sync) |
| Storage | SQLite at `~/.job-market-heatmap/data.db` |
| Credentials | macOS Keychain via tauri-plugin-store |
| Data source | [Adzuna Jobs API](https://developer.adzuna.com/) |

---

## Prerequisites

- macOS (Apple Silicon or Intel)
- Node.js 18+ and pnpm
- Python 3.11+
- Rust toolchain (`rustup`)
- An [Adzuna API account](https://developer.adzuna.com/) (free tier, ~250 req/day)

---

## Getting Started

### 1. Install dependencies

```bash
# Frontend
pnpm install

# Python sidecar
cd sidecar
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cd ..
```

### 2. Build the sidecar binary

The FastAPI backend is bundled as a PyInstaller binary that Tauri spawns on launch.

```bash
cd sidecar
./build_sidecar.sh
cd ..
```

This places the binary at `src-tauri/binaries/main-aarch64-apple-darwin` (or the appropriate target triple for your machine).

### 3. Run in development mode

```bash
pnpm tauri dev
```

The app window opens and spawns the sidecar automatically. The sidecar shuts down when the app closes.

### 4. Enter your Adzuna credentials

Open **Settings** in the app, enter your Adzuna `app_id` and `app_key`, and save. Credentials are stored in the macOS Keychain — never written to disk as plaintext.

### 5. Sync job data

Click **Sync Now** in the status bar. The sidecar fetches job postings from Adzuna, runs spaCy skill extraction, normalizes role titles, and writes to the local SQLite database. Subsequent syncs run automatically at 2 AM nightly.

---

## Project Structure

```
job-market-heatmap/
├── src/                    # React + TypeScript frontend
│   ├── components/         # Chart and UI components
│   ├── hooks/              # React Query data hooks
│   ├── lib/                # Typed API client
│   └── types/              # Shared TypeScript interfaces
├── sidecar/                # Python FastAPI backend
│   ├── routers/            # API endpoint handlers
│   ├── services/           # Adzuna client, NLP pipeline, salary resolver
│   ├── core/               # DB connection, config, scheduler
│   ├── data/               # Role taxonomy, ESCO skills subset, BLS wages
│   ├── migrations/         # SQLite schema DDL
│   └── tests/              # pytest test suite
├── src-tauri/              # Rust/Tauri shell
│   ├── src/                # main.rs (sidecar spawn) + lib.rs (Tauri commands)
│   └── tauri.conf.json     # App config and bundle settings
└── package.json
```

---

## Visualizations

- **Geographic Heatmap** — job posting density by city, rendered with Leaflet
- **Skill Bar Chart** — top 20 skills ranked by frequency across filtered postings
- **Salary Box Plots** — p25 / median / p75 distribution per canonical role, with BLS-estimated salary indicators
- **Skill Co-occurrence Graph** — force-directed vis-network graph showing which skills appear together
- **Demand Trend Lines** — week-over-week skill demand over time

All five views respond to a shared filter panel: canonical role, location region, and date range.

---

## Screenshot

> _Screenshot placeholder — run `pnpm tauri dev` and sync data to see the app._

---

## Running Tests

```bash
pytest sidecar/tests/ -v
```

---

## License

MIT — see [LICENSE](LICENSE).
