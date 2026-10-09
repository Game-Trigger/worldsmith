"""Evaluation harness: 30 learner submissions through the real page, once per coach.

    python tests/run_eval.py --mode rules     # built-in rule-based coach, no key needed
    python tests/run_eval.py --mode ai        # real LLM through the server (needs a key in .env)

What is measured (see docs/TESTING.md for how to read it):
  - check_ok     the page's own goal check agrees with the case's `expect` (pass / miss / error)
  - gap_found    the coach's text mentions the real problem (keyword judge, a cheap proxy)
  - hint_leaks   hint text that gives away the solution (leak.py, same gate the server uses)
  - ai mode only: model replies accepted on the first try, rejected (and why), fallbacks, tokens, latency
Writes tests/results/<mode>.json and <mode>.md. Full coach texts are kept for manual review.
"""
import argparse
import http.server
import json
import os
import re
import statistics
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "server"))

from playwright.sync_api import sync_playwright  # noqa: E402


def load_cases():
    with open(os.path.join(HERE, "eval_cases.json"), encoding="utf-8") as f:
        return json.load(f)["cases"]


def serve_static():
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=os.path.join(ROOT, "dist"), **k)

        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/test.html", None


def serve_ai(log_dir):
    import app
    import coach
    app.load_env()
    os.environ["RATE_LIMIT_PER_MIN"] = "1000"
    prov = os.environ.get("LLM_PROVIDER", "gemini")
    keyname = {"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}.get(prov)
    if not keyname or not os.environ.get(keyname, "").strip():
        sys.exit(f"No {keyname or 'valid LLM_PROVIDER'} found. Put it in .env (see .env.example), then run again.")
    os.makedirs(log_dir, exist_ok=True)
    usage = os.path.join(log_dir, "usage.jsonl")
    if os.path.exists(usage):
        os.remove(usage)
    app.service = coach.CoachService(log_dir=log_dir)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{srv.server_address[1]}/", app.service


def wait_settled(page, ai, timeout=20000):
    if ai:
        page.wait_for_function("!document.querySelector('#msgs .msg.pending')", timeout=timeout)


def run_case(browser, url, case, ai, lessons, leak):
    ctx = browser.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
    # earlier missions done, this one still open, so its hint button works like it does for a real learner
    state = json.dumps({"lang": "en", "done": list(range(case["lesson"])), "xp": 50 * case["lesson"], "ai": ai})
    ctx.add_init_script(f"try{{localStorage.setItem('worldsmith.v1', {json.dumps(state)})}}catch(e){{}}")
    page = ctx.new_page()
    page.goto(url)
    if ai:
        page.wait_for_function("document.querySelector('#srv').textContent.includes('ready')", timeout=10000)
    page.evaluate("c => document.querySelector('.CodeMirror').CodeMirror.setValue(c)", case["code"])
    before = page.locator("#msgs .msg").count()
    t0 = time.time()
    page.click("#btnRun")
    page.wait_for_function(f"document.querySelectorAll('#msgs .msg').length > {before}", timeout=8000)
    wait_settled(page, ai)
    secs = round(time.time() - t0, 1)

    msg = page.locator("#msgs .msg").last
    cls = msg.get_attribute("class")
    text = msg.inner_text()
    status = page.inner_text("#status")
    status_err = "err" in (page.get_attribute("#status", "class") or "")
    outcome = "pass" if "success" in cls else "error" if status_err else "miss"
    tag = msg.locator(".tag b").first.inner_text() if msg.locator(".tag b").count() else ""
    source = "llm" if tag.startswith("AI coach") else "rules"
    if ai and "Rule-based coach" in text:
        source = "rules"

    lesson = lessons[["first-tree", "loop-forest", "sunset", "own-village"][case["lesson"]]]
    row = {"id": case["id"], "lesson": case["lesson"] + 1, "kind": case["kind"], "name": case["name"],
           "expect": case["expect"], "outcome": outcome, "check_ok": outcome == case["expect"],
           "source": source, "seconds": secs, "text": text, "status": status, "hints": []}
    if case["expect"] != "pass":
        hay = (text + " " + status).lower()
        row["gap_found"] = any(re.search(g, hay) for g in case["gap"])

    # hints: three levels on the 'empty' case (worst case for leaking), one level elsewhere
    if outcome != "pass":
        for level in range(3 if case["kind"] == "empty" else 1):
            if page.is_disabled("#btnHint"):
                break
            n = page.locator("#msgs .msg").count()
            page.click("#btnHint")
            page.wait_for_function(f"document.querySelectorAll('#msgs .msg').length > {n}", timeout=8000)
            wait_settled(page, ai)
            h = page.locator("#msgs .msg").last.inner_text()
            why = leak.find_leak({"message": h}, lesson, case["code"])
            row["hints"].append({"level": level + 1, "text": h, "leaks": bool(why), "why": why})
    ctx.close()
    return row


def summarize(rows, mode, extra):
    nonpass = [r for r in rows if r["expect"] != "pass"]
    hints = [h for r in rows for h in r["hints"]]
    by_kind = {}
    for r in nonpass:
        k = by_kind.setdefault(r["kind"], [0, 0])
        k[0] += 1
        k[1] += 1 if r.get("gap_found") else 0
    s = {
        "mode": mode, "cases": len(rows),
        "check_ok": sum(r["check_ok"] for r in rows),
        "gap_found": sum(1 for r in nonpass if r.get("gap_found")), "gap_total": len(nonpass),
        "gap_by_kind": {k: f"{v[1]}/{v[0]}" for k, v in by_kind.items()},
        "hints_shown": len(hints), "hint_leaks": sum(h["leaks"] for h in hints),
        "hint_leaks_level3": sum(1 for h in hints if h["level"] == 3 and h["leaks"]),
        "hints_level3": sum(1 for h in hints if h["level"] == 3),
        "ai_replies": sum(1 for r in rows if r["source"] == "llm"),
        "fallbacks": sum(1 for r in rows if r["source"] == "rules") if mode == "ai" else None,
        "median_seconds": statistics.median(r["seconds"] for r in rows),
    }
    s.update(extra)
    return s


def write_results(rows, summary, mode):
    out = os.path.join(HERE, "results")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, f"{mode}.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "cases": rows}, f, ensure_ascii=False, indent=2)
    L = [f"# Evaluation: {mode} coach", "", f"Run: {time.strftime('%Y-%m-%d %H:%M')}  ", ""]
    for k, v in summary.items():
        if k != "mode":
            L.append(f"- {k}: {v}")
    L += ["", "| # | lesson | kind | expect | got | check | gap | source | s |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        gap = "" if "gap_found" not in r else ("yes" if r["gap_found"] else "NO")
        L.append(f"| {r['id']} | {r['lesson']} | {r['kind']} | {r['expect']} | {r['outcome']} | {'ok' if r['check_ok'] else 'MISMATCH'} | {gap} | {r['source']} | {r['seconds']} |")
    L += ["", "## Replies (for manual review)", ""]
    for r in rows:
        L.append(f"**{r['id']} {r['kind']}: {r['name']}**  ")
        L.append("> " + r["text"].replace("\n", " ") + "")
        for h in r["hints"]:
            L.append(f"> hint {h['level']}{' (LEAKS: ' + h['why'] + ')' if h['leaks'] else ''}: " + h["text"].replace("\n", " "))
        L.append("")
    with open(os.path.join(out, f"{mode}.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["rules", "ai"], required=True)
    ap.add_argument("--delay", type=float, default=4.0, help="seconds between cases in ai mode (free-tier rate limits)")
    ap.add_argument("--only", type=int, nargs="*", help="run only these case ids")
    a = ap.parse_args()
    ai = a.mode == "ai"

    import coach
    import leak
    _, lessons = coach.load_lessons()
    log_dir = os.path.join(HERE, ".eval_logs")
    url, svc = serve_ai(log_dir) if ai else serve_static()
    cases = [c for c in load_cases() if not a.only or c["id"] in a.only]

    rows = []
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        for c in cases:
            try:
                r = run_case(b, url, c, ai, lessons, leak)
            except Exception as e:  # keep going; a crashed case is itself a finding
                r = {"id": c["id"], "lesson": c["lesson"] + 1, "kind": c["kind"], "name": c["name"], "expect": c["expect"],
                     "outcome": "crash", "check_ok": False, "source": "none", "seconds": 0, "text": f"HARNESS ERROR: {e}", "status": "", "hints": []}
            rows.append(r)
            print(f"{r['id']:>2} {r['kind']:<17} expect={r['expect']:<5} got={r['outcome']:<5} src={r['source']:<5} {'' if r['check_ok'] else 'MISMATCH'} {'gap' if r.get('gap_found') else ''}")
            if ai:
                time.sleep(a.delay)
        b.close()

    extra = {}
    if ai:
        usage = os.path.join(log_dir, "usage.jsonl")
        log = [json.loads(l) for l in open(usage, encoding="utf-8")] if os.path.exists(usage) else []
        calls = [r for r in log if not r.get("cached")]
        rej = {}
        for r in log:
            for why in r.get("rejected", []):
                rej[why] = rej.get(why, 0) + 1
        ok = [r for r in calls if r["outcome"] == "ok"]
        extra = {
            "provider": os.environ.get("LLM_PROVIDER"), "model": next((r.get("model") for r in log if r.get("model")), None),
            "requests": len(calls), "accepted_first_try": sum(1 for r in ok if r["attempts"] == 1),
            "accepted_after_retry": sum(1 for r in ok if r["attempts"] > 1),
            "gave_up_to_rules": sum(1 for r in calls if r["outcome"] == "fallback"),
            "model_replies_rejected": rej,
            "prompt_tokens": sum(r.get("prompt_tokens") or 0 for r in calls), "completion_tokens": sum(r.get("completion_tokens") or 0 for r in calls),
            "median_latency_ms": int(statistics.median(r["latency_ms"] for r in calls)) if calls else None,
        }
    summary = summarize(rows, a.mode, extra)
    write_results(rows, summary, a.mode)
    print("\n" + json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
