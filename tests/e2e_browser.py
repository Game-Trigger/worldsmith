"""Browser end-to-end test: real server code + real page + headless Chromium.
The model is replaced by a scripted stand-in (provider "mock"), so this tests our plumbing, not the LLM.

    python tests/e2e_browser.py            (needs: pip install playwright, `python build.py` done)
Screenshots go to tests/shots/.
"""
import http.server
import json
import os
import re
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "server"))
os.environ["LLM_PROVIDER"] = "mock"
os.environ["RATE_LIMIT_PER_MIN"] = "1000"

import app  # noqa: E402
import coach  # noqa: E402
import providers  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

SHOTS = os.path.join(HERE, "shots")
os.makedirs(SHOTS, exist_ok=True)
MODE = {"fail": False}
results = []


def check(name, cond, extra=""):
    results.append((name, bool(cond), extra))
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))


def scripted(system, user, timeout):
    if MODE["fail"]:
        raise providers.ProviderError("http", "HTTP 503 scripted outage")
    stage = re.search(r"^stage: (\w+)", user, re.M).group(1)
    met = "goals_met: true" in user
    r = {"stage": stage, "missing_concept": None, "message": "", "task": None, "hint": None, "verdict": None, "reveals_solution": False}
    if stage == "evaluate":
        r["verdict"] = "pass" if met else "fail"
        r["missing_concept"] = None if met else "calls need concrete numbers"
        r["message"] = "Your tree stands on the map. Try changing the numbers to move it." if met else "The tree line is still a comment, so nothing runs yet."
    elif stage == "teach":
        r["message"] = "Here is a nudge. Which line still starts with //?"
        r["hint"] = "Look at the comment line: what has to change so it becomes a real call?"
    elif stage == "showcase":
        r["verdict"] = "pass"
        r["message"] = "A lone tree on a green field; calm and quiet. Try a warmer sun to make it feel like evening."
    elif stage == "challenge":
        r["verdict"] = "pass"
        r["message"] = "Next: two trees, side by side."
        r["task"] = {"title": "A pair of trees", "goal": "Plant two trees with different x values.",
                     "starter_code": "ground(\"#6a994e\");\n// plant the first tree here\n// plant the second tree here\n",
                     "success_criteria": ["2 trees", "different x"]}
    return providers.Reply(json.dumps(r), "mock", 120, 60)


providers.PROVIDERS["mock"] = scripted


def serve_app():
    app.load_env()
    app.service = coach.CoachService(log_dir=os.path.join(ROOT, "tests", ".e2e_logs"))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), app.Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def serve_static_only():
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=os.path.join(ROOT, "dist"), **k)

        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def type_code(page, text):
    page.click(".CodeMirror")
    page.keyboard.press("Control+A")
    page.keyboard.press("Delete")
    page.keyboard.insert_text(text)


def last_msg(page):
    return page.locator("#msgs .msg").last


def main():
    ai = serve_app()
    ai_url = f"http://127.0.0.1:{ai.server_address[1]}/"
    static = serve_static_only()
    static_url = f"http://127.0.0.1:{static.server_address[1]}/test.html"

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        ctx = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        # Ignored: Google Fonts is blocked in this sandbox, and the 503 is the outage this test causes on purpose.
        noise = ("favicon", "ERR_TUNNEL_CONNECTION_FAILED", "status of 503")
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and not any(n in m.text for n in noise) else None)

        # ---- 1. AI works -------------------------------------------------
        page.goto(ai_url)
        page.wait_for_function("document.querySelector('#srv').textContent.includes('ready')", timeout=8000)
        check("health probe marks the AI coach ready", True)
        check("AI toggle is on and enabled", page.get_attribute("#modeAi", "aria-pressed") == "true" and page.is_enabled("#modeAi"))
        check("privacy note shown in AI mode", "sent to a language model" in page.inner_text("#aiNote"))

        page.click("#btnRun")
        page.wait_for_selector("#msgs .msg .tag b:has-text('AI coach')", timeout=8000)
        m = last_msg(page).inner_text()
        check("miss: AI reply replaces the pending bubble", "still a comment" in m and "Thinking" not in m and "reading your code" not in m, m)
        check("miss: shows verdict and missing concept", "Not yet" in m and "calls need concrete numbers" in m, m)
        check("miss: tagged with the model", "AI coach · mock" in m, m)

        page.click("#btnHint")
        page.wait_for_selector("#msgs .msg.hint .tag b:has-text('AI coach')", timeout=8000)
        check("hint: AI hint arrives", "what has to change" in last_msg(page).inner_text())
        check("hint counter advanced", "Hint (1/3)" in page.inner_text("#btnHint"), page.inner_text("#btnHint"))

        type_code(page, 'ground("#6a994e");\ntree(4, -6);\n')
        page.keyboard.press("Control+Enter")
        page.wait_for_selector("#msgs .msg.success .tag b:has-text('AI coach')", timeout=8000)
        m = last_msg(page).inner_text()
        check("pass: AI explains and verdict is Passed", "Passed" in m and "Your tree stands" in m, m)
        check("pass: XP awarded by the page's own checks", "+50 XP" in m and "50 XP" in page.inner_text("#xp"), m)
        check("pass: next-mission button appears", page.is_visible("#btnNext"))
        check("pass: showcase and follow-up buttons appear", page.is_visible("#btnShow") and page.is_visible("#btnChallenge"))
        page.screenshot(path=os.path.join(SHOTS, "01_ai_pass_desktop.png"))

        page.click("#btnShow")
        page.wait_for_function("document.querySelector('#msgs .msg:last-child').textContent.includes('calm and quiet')", timeout=8000)
        check("showcase: scene description shown", True)

        page.click("#btnChallenge")
        page.wait_for_selector(".task", timeout=8000)
        check("challenge: task card with criteria", "A pair of trees" in page.inner_text(".task") and "different x" in page.inner_text(".task"))
        page.click("[data-act=loadTask]")
        check("challenge: loading task asks for confirmation first", page.is_visible("#confirm"))
        page.click("#confirmYes")
        code = page.evaluate("document.querySelector('.CodeMirror').CodeMirror.getValue()")
        check("challenge: skeleton loaded into the editor", "plant the first tree here" in code, code)

        # rules toggle
        page.click("#modeRules")
        check("rules mode: toggle flips", page.get_attribute("#modeRules", "aria-pressed") == "true")
        check("rules mode: note says nothing is sent", "nothing is sent" in page.inner_text("#aiNote"))
        n = page.locator("#msgs .msg").count()
        type_code(page, 'ground("#6a994e");\n')
        page.keyboard.press("Control+Enter")
        page.wait_for_function(f"document.querySelectorAll('#msgs .msg').length > {n}", timeout=4000)
        m = last_msg(page).inner_text()
        check("rules mode: instant local feedback, no AI tag, no pending", "AI coach" not in m and "reading" not in m, m)
        page.click("#modeAi")

        # ---- 2. AI breaks mid-session -> fallback -------------------------
        MODE["fail"] = True
        page.click("#steps li:nth-child(1) button")  # back to mission 1
        if page.is_visible("#confirm"):
            page.click("#confirmYes")
        page.click("#btnRun")
        page.wait_for_selector("#msgs .msg .tag.rules", timeout=8000)
        m = last_msg(page).inner_text()
        check("fallback: rule-based text still shown", "tree" in m.lower() and len(m) > 40, m)
        check("fallback: says why and offers retry", "Rule-based coach" in m and "cannot answer right now" in m and "Try again" in m, m)
        page.screenshot(path=os.path.join(SHOTS, "02_fallback_desktop.png"))
        MODE["fail"] = False
        page.click("[data-act=retry]")
        page.wait_for_selector("#msgs .msg .tag b:has-text('AI coach')", timeout=8000)
        check("fallback: retry works once the model is back", True)
        check("fallback: failed bubble was replaced, not duplicated", page.locator("#msgs .tag.rules").count() == 0)

        # no endless spinner: the pending bubble is never left behind
        check("no pending bubble left over", page.locator("#msgs .msg.pending").count() == 0)

        # ---- 3. Turkish ----------------------------------------------------
        page.click("#langTr")
        check("TR: server label and mode button translated", "hazır" in page.inner_text("#srv") and page.inner_text("#modeRules") == "Kural", page.inner_text("#srv"))
        check("TR: privacy note translated", "dil modeline" in page.inner_text("#aiNote"))

        check("no page errors / console errors (AI scenario)", not errors, "; ".join(errors[:3]))

        # ---- 4. mobile ----------------------------------------------------
        mob = b.new_context(viewport={"width": 390, "height": 844}, locale="tr-TR", has_touch=True, is_mobile=True)
        mp = mob.new_page()
        mp.goto(ai_url)
        mp.wait_for_function("document.querySelector('#srv').textContent.includes('hazır')", timeout=8000)
        mp.click("#btnRun")
        mp.wait_for_selector("#msgs .msg .tag b:has-text('AI koç')", timeout=8000)
        sw = mp.evaluate("document.documentElement.scrollWidth")
        check("mobile 390px: no horizontal scroll with the new controls", sw <= 390, f"scrollWidth={sw}")
        small = mp.evaluate("""[...document.querySelectorAll('#modeAi,#modeRules,#btnHint')].filter(e=>e.getBoundingClientRect().height<44).map(e=>e.id)""")
        check("mobile: coach controls have 44px touch targets", not small, str(small))
        mp.locator("#msgs").scroll_into_view_if_needed()
        mp.screenshot(path=os.path.join(SHOTS, "03_ai_mobile.png"))

        # ---- 5. no server at all (how the published artifact runs) ------------
        off = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        off_err = []
        off.on("pageerror", lambda e: off_err.append(str(e)))
        off.goto(static_url)
        off.wait_for_function("document.querySelector('#srv').textContent.includes('No server')", timeout=8000)
        check("no server: label explains it", True)
        check("no server: AI button disabled, rules active", off.is_disabled("#modeAi") and off.get_attribute("#modeRules", "aria-pressed") == "true")
        off.click("#btnRun")
        off.wait_for_function("document.querySelectorAll('#msgs .msg').length >= 2", timeout=4000)
        m = last_msg(off).inner_text()
        check("no server: Run still gives rule-based feedback instantly", len(m) > 30 and "reading" not in m, m)
        off.screenshot(path=os.path.join(SHOTS, "04_no_server_desktop.png"))
        check("no server: no page errors", not off_err, "; ".join(off_err[:3]))
        b.close()

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
