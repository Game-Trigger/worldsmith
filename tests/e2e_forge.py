"""Browser end-to-end test for AI Forge: real server code + real page + headless Chromium.
The model is a scripted stand-in (provider "mock"), so this tests the plumbing, not the LLM.

    python tests/e2e_forge.py        (needs: pip install playwright, `python build.py` done)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import e2e_browser as base  # noqa: E402  (sets LLM_PROVIDER=mock and gives the coach stand-in)
import app  # noqa: E402
import forge  # noqa: E402
import providers  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

WINDMILL = {
    "name": "windmill", "label": "Windmill",
    "parts": [
        {"shape": "cylinder", "color": "#d8c6a0", "position": [0, 1.0, 0], "size": [1.4, 2.0, 1.4]},
        {"shape": "cone", "color": "#8a3b2e", "position": [0, 2.4, 0], "size": [1.7, 0.9, 1.7]},
        {"shape": "box", "color": "#6b4a30", "position": [0, 2.0, 0.8], "size": [0.2, 0.2, 0.3]},
        {"shape": "box", "color": "#e8e0d0", "position": [0, 2.0, 1.0], "size": [0.2, 2.6, 0.06]},
        {"shape": "box", "color": "#e8e0d0", "position": [0, 2.0, 1.0], "size": [2.6, 0.2, 0.06]},
    ],
    "explanation": "A windmill with four sails. Place it with spawn(\"windmill\", 3, 3).",
}
SCRIPT = {"replies": [], "seen": [], "fail": False}


def scripted(system, user, timeout):
    if "3D modeller inside Worldsmith" not in system:
        return base.scripted(system, user, timeout)
    SCRIPT["seen"].append((system, user))
    if SCRIPT["fail"]:
        raise providers.ProviderError("http", "HTTP 503 scripted outage")
    obj = SCRIPT["replies"].pop(0) if SCRIPT["replies"] else WINDMILL
    return providers.Reply(json.dumps(obj), "mock", 100, 50)


providers.PROVIDERS["mock"] = scripted
results = base.results
check = base.check


def editor(page):
    return page.evaluate("document.querySelector('.CodeMirror').CodeMirror.getValue()")


def wait_idle(page):
    page.wait_for_function("!document.querySelector('#fgStatus').classList.contains('busy')", timeout=15000)


def stored(page):
    return page.evaluate("JSON.parse(localStorage.getItem('worldsmith.forge.v1') || '[]')")


def main():
    srv = base.serve_app()
    app.forge_service = forge.ForgeService(log_dir=os.path.join(base.ROOT, "tests", ".e2e_logs"))
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    static = base.serve_static_only()
    static_url = f"http://127.0.0.1:{static.server_address[1]}/test.html"

    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        ctx = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        noise = ("favicon", "ERR_TUNNEL_CONNECTION_FAILED", "status of 503")
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" and not any(n in m.text for n in noise) else None)
        page.goto(url)
        page.wait_for_function("document.querySelector('#srv').textContent.includes('ready')", timeout=8000)

        page.click("#tabForge")
        check("forge tab: pane shown, code hidden", page.is_visible("#fgText") and not page.is_visible(".CodeMirror"))
        check("forge tab: aria-selected follows", page.get_attribute("#tabForge", "aria-selected") == "true"
              and page.get_attribute("#tabPrompt", "aria-selected") == "false")
        check("forge tab: enabled with the server, no off notice", page.is_enabled("#fgText") and not page.is_visible("#fgOff"))
        check("forge tab: meaningful placeholder and empty state", "Example:" in (page.get_attribute("#fgText", "placeholder") or "")
              and "No models yet" in page.inner_text("#fgNone"))

        page.click("#fgGo")
        check("empty description: specific message, no request", "Write what to model first" in page.inner_text("#fgStatus") and not SCRIPT["seen"])
        page.fill("#fgText", "x" * 150)
        check("description is capped at 120 characters", len(page.input_value("#fgText")) == 120 and "120 / 120" in page.inner_text("#fgCount"))

        starter = editor(page)
        page.fill("#fgText", "a wooden windmill")
        page.click("#fgGo")
        wait_idle(page)
        check("forge: status names the object and its parts", '"Windmill" is ready: 5 parts' in page.inner_text("#fgStatus"), page.inner_text("#fgStatus"))
        check("forge: spawn line appended to the learner's code, not replacing it",
              editor(page).startswith(starter.rstrip()) and editor(page).rstrip().endswith('spawn("windmill", 0, 0);'), editor(page)[-80:])
        check("forge: result card shows explanation, the line and the model tag",
              "four sails" in page.inner_text("#fgResult") and 'spawn("windmill", 0, 0);' in page.inner_text("#fgLine") and "Modelled by AI · mock" in page.inner_text("#fgTag"))
        page.wait_for_function("document.querySelector('#chips').textContent.includes('Models')", timeout=5000)
        check("forge: scene ran the code, the Models chip counts 1", "Models1" in page.inner_text("#chips").replace("\n", "").replace(" ", ""), page.inner_text("#chips"))
        check("forge: description sent inside its data block", "<description>\na wooden windmill" in SCRIPT["seen"][-1][1])
        check("forge: model list shows it", "Windmill" in page.inner_text("#fgList") and not page.is_visible("#fgNone"))
        check("forge: saved in this browser", [m["name"] for m in stored(page)] == ["windmill"], str(stored(page)))
        page.screenshot(path=os.path.join(base.SHOTS, "08_forge_desktop.png"))

        page.click("#fgUndo")
        check("undo: previous editor content restored, button hides", editor(page) == starter and not page.is_visible("#fgUndo"))
        page.wait_for_function("!document.querySelector('#chips').textContent.includes('Models')", timeout=5000)
        check("undo: scene rebuilt without the model", True)

        page.click("#fgList [data-use=windmill]")
        page.click("#fgList [data-use=windmill]")
        check("click on a model places another one at the next free spot",
              'spawn("windmill", 0, 0);' in editor(page) and 'spawn("windmill", 7, 4);' in editor(page), editor(page)[-100:])
        page.wait_for_function("document.querySelector('#chips').textContent.includes('2')", timeout=5000)

        SCRIPT["replies"] = [dict(WINDMILL)]
        page.fill("#fgText", "another windmill")
        page.click("#fgGo")
        wait_idle(page)
        names = [m["name"] for m in stored(page)]
        check("same name again: kept as a second model, nothing replaced", names == ["windmill", "windmill_2"], str(names))
        check("same name again: the page told the server the existing names", "existing names: windmill." in SCRIPT["seen"][-1][0], SCRIPT["seen"][-1][0][-900:-700])

        page.click("#tabCode")
        base.type_code(page, '\nspawn("castle", 0, 0);')
        page.click("#btnRun")
        page.wait_for_function("document.querySelector('#status').textContent.includes('castle')", timeout=5000)
        msg = page.inner_text("#status")
        check("unknown model name: specific error that lists the learner's models",
              'no model called "castle"' in msg and "windmill, windmill_2" in msg, msg)
        page.click("#btnReset")
        page.click("#confirmYes")
        base.type_code(page, "\nspawn(5, 0, 0);")
        page.click("#btnRun")
        page.wait_for_function("document.querySelector('#status').textContent.includes('spawn()')", timeout=5000)
        check("spawn with a number as the name: says the name must be text", "must be text in quotes" in page.inner_text("#status"), page.inner_text("#status"))
        page.click("#btnReset")
        page.click("#confirmYes")
        base.type_code(page, '\nfor (let i = 0; i < 70; i++) { spawn("windmill", 0, 0, 0.3); }')
        page.click("#btnRun")
        page.wait_for_function("document.querySelector('#status').textContent.includes('60')", timeout=5000)
        check("more than 60 spawns: stopped with a clear limit message", "at most 60 custom models" in page.inner_text("#status"), page.inner_text("#status"))
        page.click("#btnReset")
        page.click("#confirmYes")

        page.reload()
        page.wait_for_function("document.querySelector('#srv').textContent.includes('ready')", timeout=8000)
        base.type_code(page, '\nspawn("windmill", 4, 4);')
        page.click("#btnRun")
        page.wait_for_function("document.querySelector('#chips').textContent.includes('Models')", timeout=5000)
        check("after a reload the models are still there and spawn works", True)

        page.click("#tabForge")
        page.click("#fgList [data-del=windmill_2]")
        check("delete: confirm bar before removing", page.is_visible("#confirm"))
        page.click("#confirmNo")
        check("delete: cancel keeps the model", len(stored(page)) == 2)
        page.click("#fgList [data-del=windmill_2]")
        page.click("#confirmYes")
        check("delete: confirm removes it from list and storage", [m["name"] for m in stored(page)] == ["windmill"] and "windmill_2" not in page.inner_text("#fgList"))

        before = editor(page)
        SCRIPT["fail"] = True
        page.fill("#fgText", "a tower")
        page.click("#fgGo")
        wait_idle(page)
        msg = page.inner_text("#fgStatus")
        check("model outage: specific message, button usable, code untouched",
              "cannot be reached" in msg and page.is_enabled("#fgGo") and editor(page) == before, msg)
        SCRIPT["fail"] = False

        bad = dict(WINDMILL, name="Bad Name")
        SCRIPT["replies"] = [bad, bad]
        page.click("#fgGo")
        wait_idle(page)
        check("invalid object twice: rejected with the reason, nothing added", "name:" in page.inner_text("#fgStatus") and len(stored(page)) == 1, page.inner_text("#fgStatus"))

        page.click("#modeRules")
        check("rules mode: forge off with a reason", page.is_visible("#fgOff") and "Rules mode" in page.inner_text("#fgOff") and page.is_disabled("#fgText"))
        page.click("#modeAi")
        page.click("#langTr")
        check("TR: tab, button, placeholder and list header translated", page.inner_text("#tabForge") == "Atölye" and "Modelle" in page.inner_text("#fgGo")
              and "Örnek:" in (page.get_attribute("#fgText", "placeholder") or "") and "Modellerin" in page.inner_text("#fgHead"))
        check("no page errors (forge scenario)", not errors, "; ".join(errors[:3]))

        # a damaged or hostile store must not reach three.js unchecked
        hostile = [
            {"name": "ok_thing", "label": "Fine <b>x</b>", "parts": [
                {"shape": "box", "color": "javascript:alert(1)", "position": [99, -5, 0], "size": [900, 0, "a"]},
                {"shape": "sphere", "color": "#abc", "position": [0, 1, 0], "size": [1, 1, 1], "rotation_y": 1e9}]},
            {"name": "BAD NAME", "label": "x", "parts": []},
            {"name": "toosmall", "label": "x", "parts": [{"shape": "box", "color": "#111111", "position": [0, 0, 0], "size": [1, 1, 1]}]},
            "not an object", None,
        ]
        h = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        herr = []
        h.on("pageerror", lambda e: herr.append(str(e)))
        h.add_init_script("localStorage.setItem('worldsmith.forge.v1', %s)" % json.dumps(json.dumps(hostile)))
        h.goto(url)
        h.wait_for_function("document.querySelector('#srv').textContent.includes('ready')", timeout=8000)
        h.click("#tabForge")
        items = h.inner_text("#fgList")
        check("hostile store: only the repairable model is kept, label shown as text", "Fine <b>x</b>" in items and items.count("×") == 1, items)
        h.click("#tabCode")
        base.type_code(h, '\nspawn("ok_thing", 0, 0);')
        h.click("#btnRun")
        h.wait_for_function("document.querySelector('#chips').textContent.includes('Models')", timeout=5000)
        check("hostile store: clamped model still renders, no page errors", not herr, "; ".join(herr[:3]))

        mob = b.new_context(viewport={"width": 390, "height": 844}, locale="tr-TR", has_touch=True, is_mobile=True).new_page()
        mob.goto(url)
        mob.wait_for_function("document.querySelector('#srv').textContent.includes('hazır')", timeout=8000)
        mob.click("#tabForge")
        mob.fill("#fgText", "taş bir kule")
        mob.click("#fgGo")
        wait_idle(mob)
        sw = mob.evaluate("document.documentElement.scrollWidth")
        check("mobile 390px: no horizontal scroll with the forge pane", sw <= 390, f"scrollWidth={sw}")
        small = mob.evaluate("""[...document.querySelectorAll('#tabCode,#tabPrompt,#tabForge,#fgGo,#fgUndo,#fgList button')].filter(e=>e.getBoundingClientRect().height>0&&(e.getBoundingClientRect().height<44||e.getBoundingClientRect().width<44)).map(e=>e.id||e.textContent)""")
        check("mobile: forge controls have 44px touch targets", not small, str(small))
        mob.screenshot(path=os.path.join(base.SHOTS, "09_forge_mobile.png"))

        off = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        off_err = []
        off.on("pageerror", lambda e: off_err.append(str(e)))
        off.goto(static_url)
        off.wait_for_function("document.querySelector('#srv').textContent.includes('No server')", timeout=8000)
        off.click("#tabForge")
        check("no server: forge off and says why", "opened without the AI server" in off.inner_text("#fgOff") and off.is_disabled("#fgGo") and off.is_disabled("#fgText"))
        check("no server: no page errors", not off_err, "; ".join(off_err[:3]))
        off.screenshot(path=os.path.join(base.SHOTS, "10_forge_no_server.png"))
        b.close()

    bad_checks = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad_checks)}/{len(results)} checks passed")
    sys.exit(1 if bad_checks else 0)


if __name__ == "__main__":
    main()
