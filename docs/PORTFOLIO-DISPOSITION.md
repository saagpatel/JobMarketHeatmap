# Job Market Heatmap — Portfolio Disposition

**Status:** Active (Tauri 2 + Python sidecar prep arc) — macOS
desktop app built with **Tauri 2 (Rust shell) + Python FastAPI
sidecar + React TypeScript frontend** on `origin/feat/full-build`
(operator's canonical default — **feat-branch-as-default trap**,
same shape as Terroir). Features shipped: Tauri 2 scaffold +
FastAPI sidecar with ingestion pipeline + API routers + Tauri
sidecar lifecycle + credential store + 5 interactive
visualizations + filter panel polish. **Active (not Release
Frozen)** because no v1.0.0 release closeout cadence (.dmg deps /
v1.0.0 bump / baseline tests / Cargo.lock) visible on canonical
default. **30th signing cluster candidate, but Active state.**

**Introduces new sub-pattern**: **Tauri 2 + Python sidecar**
hybrid architecture. Distinct from pure Tauri (Rust-only backend),
hybrid signing+extension (APIReverse), and local-LLM-dependent
(thought-trails — external user-run process, not bundled sidecar).

> Disposition uses strict `origin/HEAD` verification.
> **Two pre-existing trap shapes** apply: feat-branch-as-default
> (origin/HEAD → feat/full-build) + Active state (no v1.0
> closeout).

---

## Verification posture

Only `origin` (`saagpatel/JobMarketHeatmap`). Clean migration
state. **`origin/HEAD → refs/heads/feat/full-build`** —
feat-branch-as-default trap (same shape as Terroir).

`origin/feat/full-build`:

- Tip: `2f694da` chore: add initial CHANGELOG
- OSS scaffolding wave on tip
- Substantive feat commits (earlier in branch history):
  - `012123d` feat: add 5 interactive visualizations with filter
    panel and polish
  - `4babd50` feat: wire Tauri sidecar lifecycle and credential
    store
  - `432b42e` feat: add FastAPI sidecar with ingestion pipeline and
    API routers
  - `46164a3` chore: scaffold Tauri 2 + React TS project
- **MISSING**: v1.0.0 version bump, Cargo.lock-for-v1.0.0, .dmg
  distribution build deps, baseline Rust tests, CSP hardening
  (none of the standard Tauri 2 v1.0 release closeout cadence
  signatures present)
- Default branch (per `origin/HEAD`): `feat/full-build`

---

## Current state in one paragraph

Job Market Heatmap is a macOS Tauri 2 + Rust + Python FastAPI
sidecar + React TypeScript desktop app that ingests job postings
from the **Adzuna API**, extracts skills with **spaCy NLP**,
normalizes job titles to canonical roles via **ESCO taxonomy**,
and renders five interactive visualizations: Leaflet geographic
heatmap, ranked skill frequency chart, salary box plots,
**vis-network** skill co-occurrence graph, and demand-trend time
series. **APScheduler runs nightly Adzuna sync at 2 AM**. Per
memory: Phase 0 — but canonical commit history shows 5
visualizations + sidecar lifecycle + credential store all
shipped. **Memory drift correction**: the app is meaningfully
beyond Phase 0; the architectural backbone (Tauri 2 + sidecar +
ingestion pipeline + visualizations) is complete. Active state is
about **release-closeout readiness** (no v1.0 cadence yet), not
feature gaps.

---

## Why "Active (Tauri 2 + Python sidecar)" — distinct from cluster Release Frozen state

| Signal | Other Tauri 2 cluster Release Frozen members | **Job Market Heatmap** |
|---|---|---|
| v1.0.0 version bump | All ✓ | **MISSING** |
| Cargo.lock for v1.0.0 | All ✓ | **MISSING** |
| .dmg distribution build deps | All ✓ | **MISSING** |
| Baseline Rust tests | All ✓ | **MISSING** |
| CSP hardened | All ✓ | **MISSING** |
| Substantive features | All ✓ | ✓ (full architectural backbone) |
| Default branch | `main` (mostly) | **`feat/full-build`** |

Active is correct. The arc to Release Frozen is **release-closeout
cadence** (bump version, lock Cargo, wire .dmg deps, add CSP, add
tests). Operator may also want to merge `feat/full-build` → `main`
and set `main` as the canonical default before announcing.

This parallels **Terroir** (R14.5): also feat-branch-as-default,
also Active state, also blocked on operator-side branch
consolidation + closeout cadence. Pattern: **operator's "full
build" feat branches are habitually the canonical state, but
release closeout work hasn't started**.

---

## New sub-pattern: Tauri 2 + Python sidecar

This is the first portfolio app with this architecture:

| Aspect | Pure Tauri (NetworkDecoder, IRS) | Tauri + browser extension (APIReverse) | **Tauri + Python sidecar (Job Market Heatmap)** |
|---|---|---|---|
| Rust backend | Yes | Yes | Yes |
| Python runtime | None | None | **Bundled FastAPI sidecar** |
| External user process | None | None | None (sidecar bundled) |
| External user runtime | None | None | None (Python bundled in build) |
| NLP / heavy compute | Rust | Rust | **Python (spaCy)** — leverages mature Python NLP ecosystem |
| Sidecar packaging concern | n/a | n/a | **Python deps + spaCy model bundling for DMG** |

Operator concerns introduced by the sidecar:
- **Sidecar binary packaging** — Tauri's sidecar binary feature
  needs to ship a Python interpreter + venv + spaCy model files.
  DMG bloats significantly (Python + en_core_web_sm = ~30-50 MB).
- **Sidecar lifecycle on app quit** — orphaned Python processes
  are a known Tauri sidecar pain point. `4babd50 feat: wire Tauri
  sidecar lifecycle and credential store` suggests this was
  handled, but verify under crash conditions.
- **APScheduler nightly job** — runs even when the app is
  closed? Or only when the app is open? UX clarity matters.
- **Adzuna API rate limits + credential storage**.

Future portfolio apps with Tauri + Python (or Tauri + Node, Tauri
+ Go) sidecar architectures batch in this sub-pattern.

---

## Cluster taxonomy update

| Cluster | Count | Notes |
|---|---|---|
| **Signing (Apple desktop)** | **30** | 28 Release Frozen + 1 IRS local-state-pending + **1 Active (Job Market Heatmap)** + sub-patterns visible |

The signing cluster now has its first Active member (matching the
PyPI cluster's MCPAudit-RF + mcpforge-Active pattern, and iOS
App Store's 10 RF + 1 Active pattern).

---

## Unblock trigger (operator)

1. **Decide canonical branch** — merge `feat/full-build` → `main`
   and set `main` as `origin/HEAD`, OR explicitly keep
   `feat/full-build` as canonical and update tooling accordingly.
2. **v1.0 release closeout cadence** (apply the established Tauri
   2 v1.0 signature):
   - Add CSP to Tauri webview
   - Add baseline Rust tests
   - Bump version to 1.0.0
   - Update Cargo.lock
   - Add .dmg distribution build dependencies
3. **Python sidecar packaging** — verify Tauri sidecar binary
   correctly bundles Python interpreter + spaCy `en_core_web_sm`
   model + Python deps. DMG size will grow significantly.
4. **APScheduler-when-closed posture** — decide if nightly sync
   runs only when app is open (simpler) or via launchd background
   agent (more complex; pattern from ReturnRadar).
5. **Adzuna API credential storage** — `4babd50` mentions
   credential store; verify it's using macOS Keychain, not
   plaintext.
6. **Apple Developer ID + notarization credentials.**

Estimated operator time once branch consolidation done: ~5-7
hours (sidecar packaging is the dominant unknown cost).

---

## Portfolio operating system instructions

| Aspect | Posture |
|---|---|
| Portfolio status | `Active (Tauri 2 + Python sidecar prep arc)` |
| Distribution channel | **DMG via Apple Developer ID** (planned; not yet release-closeout-cadenced) |
| Current default | **`feat/full-build`** (feat-branch-as-default trap) |
| Review cadence | Active — driven by branch consolidation + release closeout |
| Resurface conditions | (a) Branch consolidation + release closeout cadence applied, then transition to Release Frozen, (b) Adzuna API breaking change, (c) v1.1 scope, (d) sidecar packaging discoveries |
| Co-batch with | Signing cluster — **now 30 repos** (29 Release Frozen + 1 Active) |
| Sub-pattern | **Tauri 2 + Python sidecar** (first in portfolio) |
| Special concern | **Python sidecar packaging cost.** DMG bloat (Python interpreter + spaCy model = ~30-50 MB extra). |
| Special concern | **Sidecar lifecycle on app quit / crash.** Known Tauri sidecar pain point — verify under crash conditions. |
| Special concern | **APScheduler-when-app-closed UX.** Decide bundling vs launchd agent posture. |
| Special concern | **Adzuna credential storage** — verify macOS Keychain, not plaintext. |
| Special concern | **Memory drift correction**: "Phase 0" → architectural backbone shipped. |
| Special concern | **feat-branch-as-default trap** (same shape as Terroir). Operator may want to consolidate to `main`. |

---

## Reactivation procedure

1. **Re-confirm `origin/HEAD`** — may change if operator updates
   default branch.
2. Review stash `r15-jmh-stash` (CLAUDE.md + .claude/ + .codex/ +
   AGENTS.md + pnpm-workspace.yaml).
3. **Decide branch consolidation** before further work.
4. **Apply Tauri 2 v1.0 release closeout cadence** (CSP / tests /
   version bump / Cargo.lock / .dmg deps).
5. **Test Python sidecar packaging** in a `pnpm tauri build`
   DMG and verify orphan-process behavior on app quit.
6. **Test Adzuna nightly sync** at 2 AM (or simulate via
   APScheduler injection).
7. Run `cargo test` + `pytest` (sidecar tests) + `pnpm test`.

---

## Last known reference

| Field | Value |
|---|---|
| `origin/HEAD` | `refs/heads/feat/full-build` |
| `origin/feat/full-build` tip | `2f694da` chore: add initial CHANGELOG |
| Last substantive feat | `012123d` feat: add 5 interactive visualizations with filter panel and polish |
| Default branch | **`feat/full-build`** (NOT `main`) |
| Build system | Tauri 2 + Rust + React + TypeScript + **Python FastAPI sidecar (spaCy + APScheduler)** |
| Architecture | **Hybrid: Tauri DMG primary + Python FastAPI sidecar bundled** |
| API dependency | **Adzuna API** (Adzuna developer account + free tier credential) |
| Phases shipped | Architectural backbone (Tauri 2 scaffold + FastAPI sidecar + 5 visualizations + sidecar lifecycle + credential store + filter panel polish). **No v1.0 release closeout cadence yet.** |
| Visualization tech | Leaflet (geographic heatmap) + chart library (skill frequency / salary box plots / demand trend lines) + vis-network (skill co-occurrence graph) |
| Migration state | No `legacy-origin` remote |
| Distinguishing feature | **30th signing cluster member. First Active state in signing cluster. Introduces Tauri 2 + Python sidecar sub-pattern.** Combines feat-branch-as-default trap + Active state, parallel to Terroir's pattern. |
