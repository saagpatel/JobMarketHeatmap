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
- macOS (Apple Silicon or Intel)
- Node.js 18+, pnpm, Python 3.11+, Rust toolchain
- [Adzuna API account](https://developer.adzuna.com/) (free tier)

### Installation
```bash
pnpm install
pip install -r sidecar/requirements.txt
python -m spacy download en_core_web_sm
```

### Usage
```bash
pnpm tauri dev
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Desktop shell | Tauri 2 (Rust) |
| Frontend | React 18 + TypeScript, Vite |
| Maps | Leaflet + react-leaflet + leaflet.heat |
| Charts | Recharts, vis-network |
| Backend sidecar | FastAPI + uvicorn (Python 3.11) |
| NLP | spaCy 3 (en_core_web_sm) + ESCO taxonomy |
| Scheduler | APScheduler (nightly 2 AM) |
| Storage | SQLite at ~/.job-market-heatmap/data.db |

## License

MIT
