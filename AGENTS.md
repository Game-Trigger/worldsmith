# AGENTS.md

The rules for this repo live in `CLAUDE.md`. Read it first, then `PROGRESS.md`.

The five most critical rules:
1. Never commit secrets. API keys live only in `.env` (git-ignored); the browser never sees a key.
2. Touch only your own area (see "File ownership" in `CLAUDE.md`). Work on a branch, enter `main` through a PR.
3. Run the tests after every change (`python -m unittest discover -s tests -v`, `python tests/e2e_browser.py`) and do not propose a merge until they pass.
4. Write only measured numbers. Every test and failure goes into `docs/TESTING.md`; every model, library, dataset and AI assistant goes into `docs/DISCLOSURE.md` in the same commit.
5. Coach and model output must validate against the schemas in `shared/`; `reveals_solution` is always false, and the page's goal checks, not the AI, decide pass/fail.
