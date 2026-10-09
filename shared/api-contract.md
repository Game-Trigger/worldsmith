# API contract

Server: `python server/app.py` (Python standard library only). Serves the built page and the API on one origin, so there is no CORS. Changing this file needs agreement between whoever owns `web` (src.html) and `server/`.

Reply shape is defined by [`coach-schema.json`](coach-schema.json). The server checks every model reply against it before the page sees it.

## `GET /api/health`
`200 {"ok": true, "provider": "gemini", "configured": true}`. `configured` is false when the provider has no key. The page calls this once on load: not ready means AI mode is disabled and the rule-based coach is used. A page served without this server (for example the published artifact) gets no JSON back and does the same.

## `GET /api/lessons/:id`
Public lesson fields: `id, index, title, concept, goals`. Never the reference solution. `404` for an unknown id.

## `POST /api/coach`
Request (JSON, at most 20 000 bytes):

| field | type | notes |
|---|---|---|
| `lesson_id` | string | `first-tree`, `loop-forest`, `sunset`, `own-village` |
| `stage` | string | `diagnose`, `teach`, `challenge`, `evaluate`, `showcase` |
| `lang` | `"tr"` or `"en"` | language of the reply |
| `code` | string | at most 6000 characters |
| `run_output` | object or null | scene summary from the page: counts, `sunH`, `fogA`, `hasLoop`, `spread`, ... |
| `error` | object or null | `{code, line, message}` when the learner's code failed |
| `goals` | array | `{label, done, now}` from the page's own goal checks (these decide pass or fail) |
| `hints_used` | integer 0..3 | hint levels already used, for the `teach` stage |
| `history` | array | last 6 `{role: "coach"\|"learner", text}` |

Responses:

| status | body | when |
|---|---|---|
| 200 | CoachResponse, `source: "llm"` | accepted reply |
| 400 | `{"error": {"code": "bad_request", "message"}}` | malformed request |
| 413 | same | body too large |
| 429 | `{"error": {"code": "rate_limited", "retry_after"}}` + `Retry-After` | per-IP limit (`RATE_LIMIT_PER_MIN`, default 20) |
| 503 | `{"error": {"code": "llm_unavailable", "reason"}, "fallback": "rules"}` | no key, quota, timeout, bad JSON twice, or leaking twice |

A model reply is accepted only if it is valid JSON, matches the schema, has the requested stage, `reveals_solution` is false, `server/leak.py` finds no solution in it (skipped once the goals are met), and for `evaluate` its `verdict` agrees with `goals`. Otherwise one retry with the reason appended, then 503. Total budget `COACH_TIMEOUT_MS` (default 12 000). Identical requests are served from a 1-hour cache.

## `POST /api/model` (Prompt mode)
The learner describes a scene in words; the model writes scene code for it. Reply shape: [`model-schema.json`](model-schema.json).

Request (JSON, at most 20 000 bytes):

| field | type | notes |
|---|---|---|
| `lesson_id` | string | as for `/api/coach` |
| `lang` | `"tr"` or `"en"` | language of comments and `explanation` |
| `prompt` | string | 1 to 400 characters |
| `current_code` | string | at most 6000 characters, the editor content (the model builds on it for "add ..." wishes) |
| `unlocked` | array | engine commands this learner may use, from `ground, tree, rock, house, sun, fog, random` |
| `error` | object or null | `{line, message}` when the page ran the previous reply and it failed |
| `attempt` | 1 or 2 | 2 when `error` is set |

Responses: `200` ModelResponse (`code` <= 1500, `explanation` <= 300, `uses`, `source: "llm"`, `model`); `400`, `413`, `429` as above; `503 {"error": {"code": "llm_unavailable", "reason"}}`.

A reply is accepted only if it is valid JSON, matches the schema, and `server/model_validate.py` passes the code: only unlocked commands, no unknown functions, nothing outside plain loops/variables/`Math`, at least one scene command. `uses` is recomputed from the code. One retry with the reason, then 503. There is no rule-based fallback for this endpoint: without a model the page keeps the Prompt tab off and says why.

The page runs the reply in its Web Worker before writing it to the editor. If that run fails, it asks once more with `error` and `attempt: 2`; if that fails too, nothing is written. A good reply replaces the editor content (after the confirm bar if the learner had their own edits), runs through the normal `run()`, and the page's goal checks decide pass or fail. Undo restores the previous code and scene. Page-side timeout 13 s.

## Fallback is on the page
On any non-200 or network failure the page shows its built-in rule-based feedback (`source: "rules"`) with a visible "Rule-based coach" tag, the reason, and a retry link. This also covers having no server at all, which is why the fallback lives in the page and not in the server.

## Differences from the first plan
- No separate `/api/showcase`: it is `stage: "showcase"` on `/api/coach`, so one validated path covers everything.
- Rule-based fallback is client-side, not server-side.

## Usage log
`server/logs/usage.jsonl`, one JSON line per request: time, provider, model, stage, lesson, outcome, attempts, rejected reasons, token counts, latency, and the first 10 hex characters of the code's hash. Never the code. The folder is git-ignored.
