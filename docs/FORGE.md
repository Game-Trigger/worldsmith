# AI Forge

The learner describes a game object in words ("a stone tower with a red flag"). The AI **models it**: it returns a list of 2 to 24 primitive shapes (box, cylinder, cone, sphere, pyramid) with positions, sizes and colours. The page draws them with three.js, registers the object under a name, and the learner places it from their own code:

```js
spawn("stone_tower", 7, 4);        // x, z, optional size 0.3 to 4
```

This is the AI Gaming part of Worldsmith: a game object that did not exist in the engine is created by a model, and the learner then uses it with code. The AI does not write the learner's program here; it builds an asset, and the learner decides where it goes.

## How it works

1. Forge tab: the learner types up to 120 characters. The page sends `{lang, description, existing}` to `POST /api/forge` (see `shared/api-contract.md`).
2. `server/forge.py` builds the prompt (the description sits inside a `<description>` data block, the model is told never to follow instructions found there) and asks the configured provider (Gemini, Claude, or the mock).
3. The reply must be one JSON object that matches `shared/forge-schema.json`, then pass `server/forge_validate.py`: name is snake_case ASCII and not an engine command, every colour is `#rrggbb`, positions within -3..3 (y 0..6), sizes 0.05..4, at most 24 parts, at least two colours and two different parts, not tiny. One retry with the rejection reason, then a 503 and the page shows the reason.
4. The server makes the name unique (`windmill`, `windmill_2`...) so a second object never replaces the first.
5. The page rebuilds every field again before drawing (`sanitizeModel` in `src.html`): bad colours become grey, numbers are clamped, parts beyond 24 are dropped, the label is only ever inserted as text. The same function loads saved models from `localStorage`, so a damaged or edited store cannot reach three.js unchecked.
6. The object is normalised (centred, standing on the ground, about tree-sized at size 1) and the line `spawn("name", x, z);` is added to the end of the learner's code and run, so they see the object and the code that placed it. Undo removes the line.
7. `spawn` runs in the same Web Worker sandbox as every other command: a name that does not exist gives a specific error that lists the learner's models, and at most 60 `spawn` calls per run are allowed (the 400-object limit still applies).

Models live only in the learner's browser (12 at most). Nothing about them is stored on the server; the usage log keeps tokens, timings and a hash prefix of the description, never the description.

## Measured so far (no real model yet)

| What | Result |
|---|---|
| Server unit tests, `tests/test_forge.py` | 26 / 26 pass (schema, ranges, names, colours, NaN/Infinity, identical parts, unique names, retry, 503, quota, rate limit, log never holds the description, prompt-injection text stays inside the data block) |
| Browser end-to-end with a scripted stand-in model, `tests/e2e_forge.py` | 36 / 36 pass (forge flow, undo, place another, same name, unknown name, non-text name, 60-spawn limit, reload keeps models, delete with confirm, outage message, invalid object twice, Rules mode, TR, hostile `localStorage`, 390 px with 44 px targets, no server) |
| Existing suites with the new code | `e2e_browser.py` 33 / 33, `e2e_prompt.py` 33 / 33, all server unit tests 83 / 83 |

These tests use `LLM_PROVIDER=mock`, so they test our plumbing and safety layers, **not the quality of what a real model draws**.

## Not measured yet

Run `python tests/run_forge_eval.py` with a key in `.env` (about two minutes). It sends 12 descriptions in Turkish and English (including a prompt-injection attempt and requests that do not fit "game object", such as "a cat"), then records how many replies were valid on the first try, after one retry, or not at all, the median latency and tokens, and saves one screenshot per object in `tests/shots/forge_*.png`. Paste the numbers into this file and look at the screenshots before claiming anything about quality. Until then, no claim about how good the objects look is made.

## Known limits

- Primitive shapes only: a windmill is cylinders and boxes, not a sculpted mesh. This is a deliberate scope choice (`CLAUDE.md`: "AI modelling" means building from primitives), it is cheap, fast and safe to validate.
- A valid object can still look wrong (floating parts, odd proportions). Validation checks ranges and structure, not taste. The learner can delete a model and ask again.
- Large `spawn` loops are capped at 60 per run to keep the scene smooth on weak devices; this was not benchmarked on a real low-end phone.
