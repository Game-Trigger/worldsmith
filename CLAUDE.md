# Worldsmith: project brief for Claude Code

## What this is
A browser-based game-development learning app, built for the Starnest Academy AI Hackathon 2026 (48 hours, team "Deviltrigger", 3 people, track: **AI Gaming**).

Problem: many people want to get into game development but cannot afford the hardware and engine setup. Worldsmith runs in the browser, needs no powerful computer, teaches by coding along learning paths, and an AI coach reads the learner's code and gives feedback.

Inspiration: *The Farmer Was Replaced*. The learner programs a bot, progress unlocks new commands, and the score is efficiency. Keep it simple: paths, one topic at a time.

Longer-term business ideas (pitch only, do not build): sell as a training set, paid showcase deals with engine/tool companies, community asset marketplace with a commission.

## Judging rubric (design every decision against this)
- 25 value for the user: a specific user and problem, a clear outcome
- 30 prototype and use of AI: a working core scenario, and what the AI actually contributes
- 20 quality testing: tests, examples of failures, comparison with the current approach
- 15 feasibility: data needs, running cost, a clear next step
- 10 originality

Track text (AI Gaming): "Change how a game is played, made or operated, and show the scenario running. A trailer and a slide deck are not a prototype." Relevant examples: procedural content that stays playable, not merely varied; a studio pipeline task cut from a day to an hour.

## Current state
`src.html` is the whole page: live three.js scene on top, CodeMirror editor below, mission card and coach on the right, 4 missions (first tree, loop forest, sunset, own village), TR/EN. User code runs in a Web Worker. See README.md.

**The AI coach exists** (added during the hackathon): `server/` (Python standard library, no pip install) asks Gemini or Claude, validates every reply against `shared/coach-schema.json`, rejects any reply that leaks the solution (`server/leak.py`) or contradicts the page's own goal check, retries once, then answers 503. The page then falls back to its built-in rule-based coach with a visible tag, so it also works with no server at all (the published artifact). Page has an AI / Rules toggle. Contract: `shared/api-contract.md`.

**Not done yet:** the coach has never been run against a real model (no key tested). Model ids in `.env.example` are unverified. Tested so far: 36 server tests, 33 browser checks, 30-case evaluation of the rule-based coach. Numbers and failures are in `docs/TESTING.md`.

## Next steps, in priority order
1. **Run the AI coach against a real model.** Put a key in `.env`, start `python server/app.py`, try all four missions by hand, then `python tests/run_eval.py --mode ai` and paste the numbers into `docs/TESTING.md`. Fix the prompt in `server/coach.py` where replies are rejected or wrong. (The backend itself is built: adapter in `server/providers.py`, cache, rate limit, usage log, fallback.)
2. **Solver-verified challenge generation.** The LLM proposes a new challenge (goal + parameters); a reference solver runs it in the same worker sandbox and the challenge is only shown if it is solvable. This is the "procedural content that stays playable" story.
3. **Farmer-style bot missions.** A bot the learner programs (`move`, `plant`, `build`...) with an efficiency score (steps taken) and commands that unlock as missions are completed.
4. **Evaluation harness** (20 points): about 30 deliberately wrong submissions with known problems; measure whether the LLM hint is correct and does not leak the full solution; compare against the static hints. Also log what fraction of generated challenges pass the solver versus raw LLM output, and time-to-first-working-scene for a few real testers versus following a text tutorial. Report only measured numbers.
5. Polish for the demo: a recorded fallback video, no endless spinners, specific error messages.

## Scope rules
- One learning path only ("environment design"), done well. No marketplace, accounts, payments, or real Unity/Unreal embedding (not possible in a browser).
- "AI modelling" means the AI writes or edits scene code that builds objects from primitives. It does not generate neural 3D meshes.
- Hackathon Terms ask to list every model, library, dataset, template and AI assistant used. Keep `ATTRIBUTIONS` up to date: three.js (MIT), CodeMirror 5 (MIT), the LLM(s) used, Claude Code / Gemini as assistants.

## Working agreements
- Every library, model, dataset, template and AI assistant goes into `docs/DISCLOSURE.md` in the same commit that adds it.
- Every test and every failure goes into `docs/TESTING.md` as it happens. Only measured numbers.
- Never commit secrets. API keys live only in `.env` (git-ignored), the browser never sees a key.
- Coach output must validate against `shared/coach-schema.json`; `reveals_solution` is always false. `shared/` changes only by agreement of the owners below.
- Ownership: `src.html` (UI) / `server/` (API + coach) / `content/`, `tests/`, `docs/` (lessons, tests, submission text) / `shared/` (contracts).
- Working style: plan in 5 lines, one task at a time, no unrequested dependencies, run the code before saying it works.
- `main` is protected: work on a branch and open a PR.

## The owner's standing quality checklist (apply to every UI change)
Meaningful empty states; a deliberate, non-uniform palette; dark mode fully styled; touch targets large enough; nothing under the notch or safe area; smooth transitions; specific error messages (never "a problem occurred"); no stuck spinners; the keyboard must not cover inputs; back navigation works; no placeholder text; multi-language (currently TR/EN); confirmation before destructive actions; permissions explained and requested in context. **Test everything before calling it done.**

## Working notes
- **Session continuity:** at the start of every session read `PROGRESS.md` and summarize where we left off. Update it when a significant piece of work finishes and before the session closes.
- Run: `npm install`, `python build.py`, then `python server/app.py` and open http://localhost:8765 (serves the page and the API). Copy `.env.example` to `.env` first for the AI coach; without a key the page uses the rule-based coach.
- Tests: `python -m unittest discover -s tests -v` (server), `python tests/e2e_browser.py` (browser, needs `pip install playwright`), `python tests/run_eval.py --mode rules|ai` (30-case evaluation).
- After code changes, test in a real browser (Playwright with Chromium works headlessly; WebGL needs `--use-gl=swiftshader --enable-unsafe-swiftshader`).
