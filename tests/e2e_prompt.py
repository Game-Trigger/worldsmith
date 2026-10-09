"""Browser end-to-end test for Prompt mode: real server code + real page + headless Chromium.
The model is a scripted stand-in (provider "mock"), so this tests the plumbing, not the LLM.

    python tests/e2e_prompt.py        (needs: pip install playwright, `python build.py` done)
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import e2e_browser as base  # noqa: E402  (sets LLM_PROVIDER=mock and gives the coach stand-in)
import app  # noqa: E402
import model  # noqa: E402
import providers  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

GOOD = 'ground("#6a994e");\n// a row of trees\nfor (let i = 0; i < 5; i++) {\n  tree(i * 3 - 6, 0);\n}'
BROKEN = "for (let i = 0; i < 5; i++) {\n  tree(i * 30, 0);\n}"   # x out of range: fails in the worker, not on the server
SCRIPT = {"replies": [], "seen": [], "fail": False}


def scripted(system, user, timeout):
    if "You turn a beginner's wish" not in system:
        return base.scripted(system, user, timeout)
    SCRIPT["seen"].append(user)
    if SCRIPT.get("quota"):
        raise providers.ProviderError("quota", "HTTP 429 scripted quota")
    if SCRIPT["fail"]:
        raise providers.ProviderError("http", "HTTP 503 scripted outage")
    code = SCRIPT["replies"].pop(0) if SCRIPT["replies"] else GOOD
    return providers.Reply(json.dumps({"code": code, "explanation": "Five trees in a row; change 5 in the loop for more.",
                                       "uses": ["tree"]}), "mock", 100, 50)


providers.PROVIDERS["mock"] = scripted
results = base.results
check = base.check


def editor(page):
    return page.evaluate("document.querySelector('.CodeMirror').CodeMirror.getValue()")


def wait_idle(page):
    page.wait_for_function("!document.querySelector('#pmStatus').classList.contains('busy')", timeout=15000)


def main():
    srv = base.serve_app()
    app.model_service = model.ModelService(log_dir=os.path.join(base.ROOT, "tests", ".e2e_logs"))
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    static = base.serve_static_only()
    static_url = f"http://127.0.0.1:{static.server_address[1]}/test.html"

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        page = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        noise = ("favicon", "ERR_TUNNEL_CONNECTION_FAILED", "status of 503")
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and not any(n in m.text for n in noise) else None)
        page.goto(url)
        page.wait_for_function("document.querySelector('#srv').textContent.includes('ready')", timeout=8000)

        page.click("#tabPrompt")
        check("prompt tab: pane shown, code hidden", page.is_visible("#pmText") and not page.is_visible(".CodeMirror"))
        check("prompt tab: aria-selected follows", page.get_attribute("#tabPrompt", "aria-selected") == "true")
        check("prompt tab: enabled with the server, no off notice", page.is_enabled("#pmText") and not page.is_visible("#pmOff"))
        check("prompt tab: meaningful placeholder", "Example:" in (page.get_attribute("#pmText", "placeholder") or ""))
        check("prompt tab: unlocked commands of mission 1", page.inner_text("#pmCmds") == "Unlocked: ground, tree, rock", page.inner_text("#pmCmds"))

        page.click("#pmGo")
        check("empty prompt: specific message, no request", "Write what you want first" in page.inner_text("#pmStatus") and not SCRIPT["seen"])

        page.fill("#pmText", "x" * 450)
        check("prompt is capped at 400 characters", page.input_value("#pmText").__len__() == 400 and "400 / 400" in page.inner_text("#pmCount"))

        starter = editor(page)
        page.fill("#pmText", "five trees in a row")
        page.click("#pmGo")
        wait_idle(page)
        check("model: no confirm when the editor holds no own edits", not page.is_visible("#confirm"))
        check("model: generated code written to the editor", editor(page) == GOOD, editor(page))
        check("model: explanation and model tag shown", "Five trees in a row" in page.inner_text("#pmResult") and "Written by AI · mock" in page.inner_text("#pmResult"))
        check("model: status says the scene updated", "Scene updated" in page.inner_text("#pmStatus"), page.inner_text("#pmStatus"))
        page.wait_for_function("document.querySelector('#chips').textContent.includes('5')", timeout=5000)
        check("model: scene rebuilt by run() (5 trees in chips)", True)
        page.wait_for_function("document.querySelector('#msgs .msg:last-child') && !document.querySelector('#msgs .msg.pending')", timeout=8000)
        check("prompt code meets goals but earns no XP", page.inner_text("#xp").strip().startswith("0") and "earns no XP" in page.inner_text("#msgs"), page.inner_text("#xp"))
        check("prompt code does not unlock the next mission", not page.is_visible("#btnNext"))
        check("model: learner prompt sent inside its data block", "<learner_prompt>\nfive trees in a row" in SCRIPT["seen"][-1])
        page.screenshot(path=os.path.join(base.SHOTS, "05_prompt_desktop.png"))

        page.click("#pmUndo")
        check("undo: previous editor content restored", editor(page) == starter)
        check("undo: button hides after use", not page.is_visible("#pmUndo"))

        page.click("#tabCode")
        base.type_code(page, "tree(1, 1);\n// my own edit\n")
        page.click("#tabPrompt")
        page.fill("#pmText", "a row of trees")
        page.click("#pmGo")
        check("own edits: confirm bar appears before overwriting", page.is_visible("#confirm"))
        page.click("#confirmNo")
        check("own edits: cancel keeps the learner's code", "my own edit" in editor(page))
        page.click("#pmGo")
        page.click("#confirmYes")
        wait_idle(page)
        check("own edits: confirm yes writes the model code", editor(page) == GOOD)

        n = len(SCRIPT["seen"])
        SCRIPT["replies"] = [BROKEN, GOOD]
        page.fill("#pmText", "trees far away")
        page.click("#pmGo")
        if page.is_visible("#confirm"):
            page.click("#confirmYes")
        wait_idle(page)
        check("run error: page asks again with the error (2 model calls)", len(SCRIPT["seen"]) == n + 2 and "failed when the page ran it" in SCRIPT["seen"][-1])
        check("run error: only the fixed code reaches the editor", editor(page) == GOOD)

        before = editor(page)
        SCRIPT["replies"] = [BROKEN, BROKEN]
        page.click("#pmGo")
        if page.is_visible("#confirm"):
            page.click("#confirmYes")
        wait_idle(page)
        check("run error twice: specific message, editor untouched", "failed twice" in page.inner_text("#pmStatus") and editor(page) == before, page.inner_text("#pmStatus"))

        SCRIPT["fail"] = True
        t = time.time()
        page.click("#pmGo")
        if page.is_visible("#confirm"):
            page.click("#confirmYes")
        wait_idle(page)
        msg = page.inner_text("#pmStatus")
        check("model outage: specific message, no stuck spinner, button usable", "cannot be reached" in msg and page.is_enabled("#pmGo"), msg)
        check("model outage: answered in under 13 s", time.time() - t < 13)
        SCRIPT["fail"] = False
        SCRIPT["quota"] = True
        page.click("#pmGo")
        if page.is_visible("#confirm"):
            page.click("#confirmYes")
        wait_idle(page)
        msg = page.inner_text("#pmStatus")
        check("quota: says the per-minute quota is used up, no raw JSON", "Quota used up" in msg and "{" not in msg and page.is_enabled("#pmGo"), msg)
        SCRIPT["quota"] = False

        page.click("#tabCode")
        base.type_code(page, GOOD + "\ntree(2, 8);\n")   # the learner's own change counts
        page.keyboard.press("Control+Enter")
        page.wait_for_selector("#btnNext", state="visible", timeout=8000)
        check("learner-edited code earns XP and unlocks", "50 XP" in page.inner_text("#xp"), page.inner_text("#xp"))
        page.click("#btnNext")
        page.click("#tabPrompt")
        check("next mission: unlocked list grows (random)", "random" in page.inner_text("#pmCmds"), page.inner_text("#pmCmds"))
        page.click("#steps li:nth-child(1) button")
        if page.is_visible("#confirm"):
            page.click("#confirmYes")
        check("mission switch: prompt controls usable again", page.is_enabled("#pmGo") and page.is_enabled("#pmText"))

        page.click("#modeRules")
        check("rules mode: prompt off with a reason", page.is_visible("#pmOff") and "you chose Rules" in page.inner_text("#pmOff") and page.is_disabled("#pmText"))
        page.click("#modeAi")
        page.click("#langTr")
        check("TR: tab, button and placeholder translated", page.inner_text("#tabCode") == "Kod" and "Modelle" in page.inner_text("#pmGo")
              and "Örnek:" in (page.get_attribute("#pmText", "placeholder") or ""))
        check("no page errors (prompt scenario)", not errors, "; ".join(errors[:3]))

        mob = b.new_context(viewport={"width": 390, "height": 844}, locale="tr-TR", has_touch=True, is_mobile=True).new_page()
        mob.goto(url)
        mob.wait_for_function("document.querySelector('#srv').textContent.includes('hazır')", timeout=8000)
        mob.click("#tabPrompt")
        sw = mob.evaluate("document.documentElement.scrollWidth")
        check("mobile 390px: no horizontal scroll with the prompt pane", sw <= 390, f"scrollWidth={sw}")
        small = mob.evaluate("""[...document.querySelectorAll('#tabCode,#tabPrompt,#pmGo')].filter(e=>e.getBoundingClientRect().height<44).map(e=>e.id)""")
        check("mobile: prompt controls have 44px touch targets", not small, str(small))
        mob.fill("#pmText", "beş ağaç")
        mob.click("#pmGo")
        wait_idle(mob)
        check("mobile: undo has a 44px target", mob.evaluate("document.querySelector('#pmUndo').getBoundingClientRect().height") >= 44)
        mob.screenshot(path=os.path.join(base.SHOTS, "06_prompt_mobile.png"))

        off = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        off_err = []
        off.on("pageerror", lambda e: off_err.append(str(e)))
        off.goto(static_url)
        off.wait_for_function("document.querySelector('#srv').textContent.includes('No server')", timeout=8000)
        off.click("#tabPrompt")
        check("no server: prompt off and says why", "opened without the AI server" in off.inner_text("#pmOff") and off.is_disabled("#pmGo") and off.is_disabled("#pmText"))
        check("no server: no page errors", not off_err, "; ".join(off_err[:3]))
        off.screenshot(path=os.path.join(base.SHOTS, "07_prompt_no_server.png"))
        b.close()

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
