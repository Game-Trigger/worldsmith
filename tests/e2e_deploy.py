"""Smoke test for a deployed Worldsmith (local Docker container or Render), with the real configured model.

    python tests/e2e_deploy.py http://127.0.0.1:8765 --expect ai        # working key
    python tests/e2e_deploy.py http://127.0.0.1:8766 --expect nokey     # no GEMINI_API_KEY
    python tests/e2e_deploy.py http://127.0.0.1:8767 --expect broken    # key set but every model call fails (bad key, quota)

What must hold in every case: the page loads at /, the API answers on the same origin, Run always gives
feedback (AI or the tagged rule-based coach), Prompt and Forge never hang and either work or say why.
"""
import argparse
import json
import sys
import urllib.request

from playwright.sync_api import sync_playwright

results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond)))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))


def get(url):
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("base")
    ap.add_argument("--expect", choices=["ai", "nokey", "broken"], required=True)
    a = ap.parse_args()
    base = a.base.rstrip("/")

    st, ct, body = get(base + "/")
    check("GET / serves the page", st == 200 and ct.startswith("text/html") and b"CodeMirror" in body and b"<!doctype html>" in body[:40].lower(), f"{st} {ct}")
    st, ct, body = get(base + "/api/health")
    health = json.loads(body)
    check("GET /api/health on the same origin", st == 200 and health.get("ok") is True, str(health))
    check("health reports the key state", health.get("configured") is (a.expect != "nokey"), str(health))

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        page = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(base + "/")
        page.wait_for_function("!document.querySelector('#srv').textContent.includes('Looking')", timeout=10000)
        srv = page.inner_text("#srv")
        check("server label settles", srv in ("AI coach ready", "No API key · rule-based coach"), srv)

        page.click("#btnRun")
        page.wait_for_function("document.querySelectorAll('#msgs .msg').length >= 2 && !document.querySelector('#msgs .msg.pending')", timeout=16000)
        m = page.locator("#msgs .msg").last.inner_text()
        src = "ai" if "AI coach ·" in m else "rules" if ("Rule-based coach" in m or a.expect == "nokey") else "?"
        check("Run gives feedback, nothing left pending", len(m) > 20, m[:120])
        want = {"ai": "ai", "nokey": "rules", "broken": "rules"}[a.expect]
        check(f"coach source is {want}", src == want, m[:160])

        for tab, text_id, go, status, result, off, wish in (
                ("#tabPrompt", "#pmText", "#pmGo", "#pmStatus", "#pmResult", "#pmOff", "five trees in a row"),
                ("#tabForge", "#fgText", "#fgGo", "#fgStatus", "#fgResult", "#fgOff", "a wooden windmill")):
            name = tab[4:].lower()
            page.click(tab)
            if a.expect == "nokey":
                check(f"{name}: off and says why", page.is_visible(off) and len(page.inner_text(off)) > 30 and page.is_disabled(go), page.inner_text(off))
                continue
            page.fill(text_id, wish)
            page.click(go)
            if page.is_visible("#confirm"):
                page.click("#confirmYes")
            page.wait_for_function(f"!document.querySelector('{status}').classList.contains('busy')", timeout=30000)
            msg = page.inner_text(status)
            if a.expect == "ai":
                check(f"{name}: real model result shown", page.is_visible(result), msg)
            else:
                check(f"{name}: says the AI service is down (no raw JSON), no hang, button usable", "err" in page.get_attribute(status, "class")
                      and ("cannot be reached" in msg or "quota" in msg.lower()) and "{" not in msg and page.is_enabled(go) and not page.is_visible(result), msg)
        check("no page errors", not errors, "; ".join(errors[:3]))
        b.close()

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks passed ({a.expect})")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
