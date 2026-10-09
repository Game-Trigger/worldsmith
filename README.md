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

## How it works

- User code runs inside a Web Worker (`workerBody` in `src.html`). It can only call the scene API (`ground, tree, rock, house, sun, fog, random`) and returns plain command objects. Endless loops are killed after 1.5 s.
- The main thread validates the commands, builds the three.js scene, then `analyse()` + each mission's `goals / miss / pass` produce the coach feedback.
- Missions live in the `MISSIONS` array. Texts are bilingual (TR/EN).
- Progress and language persist in `localStorage` (`worldsmith.v1`).

## AI coach

`server/` builds a prompt from the learner's code, the scene summary and the lesson goals, asks the model, and only passes on replies that match `shared/coach-schema.json`, do not reveal the solution and agree with the page's own goal check. On any failure the page shows its rule-based feedback and says so. See `shared/api-contract.md`, `docs/TESTING.md`, `docs/DISCLOSURE.md`.

**Prompt mode.** The editor has a Code | Prompt tab. In Prompt the learner writes what they want ("twelve trees in a circle"), `POST /api/model` turns it into code using only the commands they have unlocked, the page runs it in the worker, writes it into the editor and rebuilds the scene, so the learner learns by reading the generated code. Undo restores the previous code. Without the server the tab is off and says why.
