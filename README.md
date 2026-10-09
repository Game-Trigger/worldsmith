# Worldsmith

Browser-based game-development learning app. The learner writes code, sees a live 3D scene, and an AI coach reads the code and gives feedback. No install, no GPU needed on the learner's side.

## Run

```
npm install
python build.py
python server/app.py
```

Open http://localhost:8765. For the AI coach copy `.env.example` to `.env` and add a Gemini or Claude key; without one the page uses its built-in rule-based coach. The server needs only Python 3.10+, nothing to pip install.

`src.html` is the whole app (HTML + CSS + JS). `build.py` inlines three.js and CodeMirror into `dist/`.

## Deploy

One container serves the page at `/` and the API under `/api/*` on the same origin, so no CORS setup is needed. The `Dockerfile` builds in three stages (node only to install three.js and CodeMirror from the lockfile, Python to run `build.py`, then a `python:3.11-slim` runtime with the standard library only, running as a non-root user). The server reads `PORT` and binds `0.0.0.0` inside the container.

```
docker build -t worldsmith .
docker run -p 8765:8765 -e GEMINI_API_KEY=your-key worldsmith
```

**Render (free plan):** New > Blueprint > pick this repo; `render.yaml` describes the service (Docker, health check `/api/health`). Set these environment variables in the Render dashboard:

| Variable | Value |
|---|---|
| `GEMINI_API_KEY` | your key from Google AI Studio (Render asks for it; it is never stored in the repo) |
| `LLM_PROVIDER` | `gemini` |
| `RATE_LIMIT_PER_MIN` | `10` |
| `TRUST_PROXY` | `1` (Render is a proxy; without it all visitors share one rate-limit bucket) |

**Never put the key in the repo,** not in `render.yaml`, the `Dockerfile` or a committed `.env`. `.env` is git-ignored and `.dockerignore` keeps it out of the image.

Without a key, or when the key is wrong or the free-tier quota (15 requests per minute per model) runs out, the demo keeps working: the coach falls back to its rule-based feedback with a visible tag, and Prompt and Forge say what is wrong (no key, AI service unreachable, or quota used up) instead of hanging. `python tests/e2e_deploy.py <url> --expect ai|nokey|broken` checks a running deployment for exactly that.

The free plan sleeps after a period without traffic; the first request after that takes longer. Open the page once before a demo.

## How it works

- User code runs inside a Web Worker (`workerBody` in `src.html`). It can only call the scene API (`ground, tree, rock, house, sun, fog, random`) and returns plain command objects. Endless loops are killed after 1.5 s.
- The main thread validates the commands, builds the three.js scene, then `analyse()` + each mission's `goals / miss / pass` produce the coach feedback.
- Missions live in the `MISSIONS` array. Texts are bilingual (TR/EN).
- Progress and language persist in `localStorage` (`worldsmith.v1`).

## AI coach

`server/` builds a prompt from the learner's code, the scene summary and the lesson goals, asks the model, and only passes on replies that match `shared/coach-schema.json`, do not reveal the solution and agree with the page's own goal check. On any failure the page shows its rule-based feedback and says so. See `shared/api-contract.md`, `docs/TESTING.md`, `docs/DISCLOSURE.md`.

**Prompt mode.** The editor has a Code | Prompt tab. In Prompt the learner writes what they want ("twelve trees in a circle"), `POST /api/model` turns it into code using only the commands they have unlocked, the page runs it in the worker, writes it into the editor and rebuilds the scene, so the learner learns by reading the generated code. Undo restores the previous code. Without the server the tab is off and says why.
