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

## Fallback is on the page
On any non-200 or network failure the page shows its built-in rule-based feedback (`source: "rules"`) with a visible "Rule-based coach" tag, the reason, and a retry link. This also covers having no server at all, which is why the fallback lives in the page and not in the server.

## Differences from the first plan
- No separate `/api/showcase`: it is `stage: "showcase"` on `/api/coach`, so one validated path covers everything.
- Rule-based fallback is client-side, not server-side.

## Usage log
`server/logs/usage.jsonl`, one JSON line per request: time, provider, model, stage, lesson, outcome, attempts, rejected reasons, token counts, latency, and the first 10 hex characters of the code's hash. Never the code. The folder is git-ignored.
