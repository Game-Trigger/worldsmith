# Disclosure

Everything used to build Worldsmith. Update it in the same commit that adds anything new.

## Existed before the hackathon

| What | Details |
|---|---|
| Single-page demo: `src.html`, `build.py`, `package.json`, `README.md` | Built on 2026-10-08, the day before the hackathon, with Claude (chat). Live 3D scene, code editor, 4 missions, TR/EN, **rule-based** coach, code runs in a Web Worker. The repository's first commit is labelled "pre-existing visual prototype". |
| Published preview of that demo | A private Claude artifact built from the same files. |

## Added during the hackathon

| What | Where |
|---|---|
| AI coach server: prompt, model adapters, schema validation, leak gate, retry, cache, rate limit, usage log | `server/` |
| Coach output contract and API contract | `shared/` |
| Lesson content for the coach (goals, typical gaps, reference solutions for the leak gate) | `content/lessons.json` |
| AI coach client in the page: AI/Rules toggle, server probe, fallback with a visible tag, showcase, follow-up task | `src.html` (the coach client section) |
| Tests, 30-case evaluation set, harness | `tests/` |
| AI Forge: the model builds a game object from primitive shapes, the learner places it with `spawn()`; endpoint `POST /api/forge`, schema, validator, Forge tab in the page, tests | `server/forge.py`, `server/forge_validate.py`, `shared/forge-schema.json`, `src.html` (Forge section), `tests/test_forge.py`, `tests/e2e_forge.py`, `docs/FORGE.md` |
| Docs | `docs/`, `CLAUDE.md`, `PROGRESS.md` |

## Models

| Model | Used for | Notes |
|---|---|---|
| Google Gemini `gemini-3.5-flash-lite` (default; can be changed with `GEMINI_MODEL`) | At runtime, default provider: the AI coach, Prompt mode (`/api/model`) and AI Forge (`/api/forge`) | Free-tier API key from Google AI Studio (15 requests per minute per model). Verified against the live API on 2026-10-09 (see `docs/TESTING.md`); `gemini-2.5-flash` was tried first and returned HTTP 429. Free-tier inputs may be used by Google to improve its products. |
| Anthropic Claude (id set in `ANTHROPIC_MODEL`) | Optional alternative coach provider behind the same adapter | Needs a separately billed API key. Not used unless `LLM_PROVIDER=claude`. |
| Claude (chat and Claude Code) | Development assistant: wrote and edited code and docs under the team's direction | Not part of the shipped product. |

`LLM_PROVIDER=mock` is a test double. It never contacts a model and reports its model id as "mock".

## Data

| Data | Source | Notes |
|---|---|---|
| Training or evaluation datasets | none | No dataset is used. |
| Evaluation cases (`tests/eval_cases.json`) | written by the team | 30 invented learner submissions. |
| Learner code | typed by the learner | Sent to the coach model only in AI mode, not stored by us. `server/logs/usage.jsonl` keeps token counts, timings and a hash prefix of the code, never the code itself. |

## Components

| Component | Version | License |
|---|---|---|
| three.js | 0.149.0 | MIT |
| CodeMirror | 5.65.16 | MIT |
| Python standard library (server) | 3.10+ | PSF |
| Playwright (tests only, not shipped) | latest at install | Apache-2.0 |
| Bricolage Grotesque, IBM Plex Sans, JetBrains Mono | via Google Fonts | SIL Open Font License |
| Docker base image `python:3.11-slim` (runtime) | 3.11 | PSF + Debian packages under their own licenses |
| Docker base image `node:20-slim` (build stage only, not in the final image) | 20 | MIT + Debian packages |
| Render (hosting, free plan, via `render.yaml`) | service | Render terms of service |
