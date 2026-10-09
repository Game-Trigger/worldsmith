"""Browser end-to-end test for the app shell (home, roadmap, lesson routes) and the engine styles.

    python tests/e2e_shell.py        (needs: pip install playwright, `python build.py` done)
Screenshots: tests/shots/11_home.png, 12_roadmap.png, 13..15_lesson_<engine>.png, 16_roadmap_mobile.png
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import e2e_browser as base  # noqa: E402  (mock provider, serve_app, check)
from playwright.sync_api import sync_playwright  # noqa: E402

check, results = base.check, base.results
WINDMILL = {"name": "windmill", "label": "Windmill", "parts": [
    {"shape": "cylinder", "color": "#8b5a2b", "position": [0, 1.5, 0], "size": [1.6, 3, 1.6], "rotation_y": 0},
    {"shape": "cone", "color": "#a33b2b", "position": [0, 3.6, 0], "size": [2, 1.2, 2], "rotation_y": 0},
    {"shape": "box", "color": "#e8e0c8", "position": [0, 2.6, 0.9], "size": [3, 0.3, 0.1], "rotation_y": 0}]}
PASS_CODE = 'ground("#6a994e");\ntree(4, -6);\n'


def editor(page):
    return page.evaluate("document.querySelector('.CodeMirror').CodeMirror.getValue()")


def visible_view(page):
    return page.evaluate("['homeView','journeyView','lessonView'].find(id => !document.getElementById(id).hidden)")


def main():
    srv = base.serve_app()
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    shots = base.SHOTS
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        ctx = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
        page = ctx.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))

        # ---- fresh start: home -> lesson -> back ---------------------------
        page.goto(url)
        page.wait_for_selector("#homeView:not([hidden])")
        check("home: shown at /, with promise and Start", "Write code, build your world" in page.inner_text("#homeView") and page.inner_text("#homeGo") == "Start")
        check("home: three engine cards with our own icons", page.locator("#engineCards [data-engine] svg").count() == 3)
        check("home: not-affiliated note visible", "not affiliated" in page.inner_text("#homeView"))
        page.screenshot(path=os.path.join(shots, "11_home.png"))
        page.click("#homeGo")
        page.wait_for_selector("#lessonView:not([hidden])")
        check("Start opens the first lesson route", page.evaluate("location.hash") == "#/lesson/first-tree" and "Plant your first tree" in page.inner_text("#mTitle"))
        page.click("#toJourney")
        page.wait_for_selector("#journeyView:not([hidden])")
        check("lesson: back-to-roadmap button works", visible_view(page) == "journeyView")
        page.go_back()
        page.wait_for_selector("#lessonView:not([hidden])")
        check("browser back: roadmap -> lesson", visible_view(page) == "lessonView")
        page.go_back()
        page.wait_for_selector("#homeView:not([hidden])")
        check("browser back: lesson -> home", visible_view(page) == "homeView")
        page.go_forward()
        page.wait_for_selector("#lessonView:not([hidden])")
        check("browser forward returns to the lesson", visible_view(page) == "lessonView")

        # ---- roadmap states -----------------------------------------------
        page.goto(url + "#/journey")
        page.wait_for_selector("#journeyView:not([hidden])")
        nodes = page.locator("#units .node")
        check("roadmap: Level 1 with 4 lesson nodes in Unit 1", "Level 1" in page.inner_text("#jTitle") and nodes.count() == 4)
        check("roadmap: first open, others locked with a reason", "open" in nodes.nth(0).get_attribute("class")
              and "locked" in nodes.nth(1).get_attribute("class") and 'finish "First tree" first' in nodes.nth(1).inner_text(), nodes.nth(1).inner_text())
        soon = page.locator("#units .unit.soon")
        check("roadmap: Units 2 and 3 say coming soon with an empty-state text", soon.count() == 2
              and "Movement and input" in soon.nth(0).inner_text() and "Collision" in soon.nth(1).inner_text() and "being prepared" in soon.nth(1).inner_text())
        nodes.nth(2).locator("button").click(force=True)   # aria-disabled: Playwright would wait, a learner can still tap it
        check("roadmap: tapping a locked node explains why", page.is_visible("#jFlash") and "still locked" in page.inner_text("#jFlash") and visible_view(page) == "journeyView")
        page.goto(url + "#/lesson/sunset")
        page.wait_for_selector("#journeyView:not([hidden])")
        check("locked lesson URL redirects to the roadmap with the reason", "still locked" in page.inner_text("#jFlash"))
        page.goto(url + "#/lesson/no-such-lesson")
        page.wait_for_selector("#journeyView:not([hidden])")
        check("unknown lesson URL redirects with a message", "no lesson at that address" in page.inner_text("#jFlash"))

        # ---- completing lesson 1 unlocks lesson 2 -------------------------
        nodes.nth(0).locator("button").click()
        page.wait_for_selector("#lessonView:not([hidden])")
        base.type_code(page, PASS_CODE)
        page.keyboard.press("Control+Enter")
        page.wait_for_selector("#btnNext", state="visible", timeout=8000)
        page.click("#toJourney")
        page.wait_for_selector("#journeyView:not([hidden])")
        check("roadmap: finished lesson is done, next one opens", "done" in nodes.nth(0).get_attribute("class") and "open" in nodes.nth(1).get_attribute("class"))
        check("roadmap: progress bar and XP", page.get_attribute("#jBar", "aria-valuenow") == "25" and "50 XP" in page.inner_text("#jXp"))
        page.screenshot(path=os.path.join(shots, "12_roadmap.png"), full_page=True)
        page.click("#jHome")
        page.wait_for_selector("#homeView:not([hidden])")
        check("home: button becomes Continue with the next lesson", page.inner_text("#homeGo").startswith("Continue") and "Forest" in page.inner_text("#homeGo"), page.inner_text("#homeGo"))

        # ---- engine styles: the look changes, the lesson does not --------
        page.evaluate("m => localStorage.setItem('worldsmith.forge.v1', JSON.stringify([m]))", WINDMILL)
        page.goto(url + "#/lesson/first-tree")
        page.reload()   # a hash-only goto keeps the document; the stored Forge model is read on load
        page.wait_for_selector("#lessonView:not([hidden])")
        base.type_code(page, PASS_CODE + 'spawn("windmill", -4, 3);\n')
        page.keyboard.press("Control+Enter")
        page.wait_for_function("document.querySelector('#chips').textContent.includes('Models')", timeout=8000)
        before = {"title": page.inner_text("#mTitle"), "goals": page.inner_text("#goals"), "code": editor(page), "xp": page.inner_text("#xp"),
                  "chips": page.inner_text("#chips"), "path": page.inner_text("#steps")}
        seen = {}
        for i, e in enumerate(("unity", "unreal", "godot")):
            page.select_option("#engineSel", e)
            page.wait_for_timeout(700)
            now = {"title": page.inner_text("#mTitle"), "goals": page.inner_text("#goals"), "code": editor(page), "xp": page.inner_text("#xp"),
                   "chips": page.inner_text("#chips"), "path": page.inner_text("#steps")}
            seen[e] = (page.text_content("#pvTitle"), page.inner_text("#edFile"))
            check(f"{e}: mission, goals, code, XP and Forge model unchanged", now == before, json.dumps(now)[:200])
            page.screenshot(path=os.path.join(shots, f"1{3 + i}_lesson_{e}.png"))
        check("engine labels change per style", seen["unity"][0].startswith("Unity Lite") and seen["unreal"][0].startswith("Unreal Lite")
              and seen["godot"][1] == "res://world.js" and seen["unity"][1] != seen["unreal"][1], str(seen))
        page.click("#btnHint") if page.is_visible("#btnHint") and page.is_enabled("#btnHint") else None
        page.reload()
        page.wait_for_selector("#lessonView:not([hidden])")
        check("engine choice survives a reload", page.input_value("#engineSel") == "godot" and page.text_content("#pvTitle").startswith("Godot Lite"))
        page.goto(url + "#/")
        page.wait_for_selector("#homeView:not([hidden])")
        check("home card shows the same engine as the lesson bar", page.get_attribute("#engineCards [data-engine=godot]", "aria-checked") == "true")
        page.click("#engineCards [data-engine=unreal]")
        page.goto(url + "#/lesson/first-tree")
        page.wait_for_selector("#lessonView:not([hidden])")
        check("choosing on home applies in the lesson", page.input_value("#engineSel") == "unreal")
        check("no page errors (shell scenario)", not errors, "; ".join(errors[:3]))

        # ---- broken localStorage -----------------------------------------
        for raw in ("{not json", "[1,2,3]", '"just a string"', '{"done":"x","xp":"lots","lang":7,"engine":"cryengine"}'):
            c2 = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
            c2.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ localStorage.setItem('worldsmith.v1', {json.dumps(raw)}); sessionStorage.setItem('seeded', '1'); }}")
            pg = c2.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url + "#/journey")
            pg.wait_for_selector("#journeyView:not([hidden])")
            ok = not errs and pg.locator("#units .node").count() == 4 and "0 XP" in pg.inner_text("#jXp")
            pg.click("#units .node:first-child button")
            pg.wait_for_selector("#lessonView:not([hidden])")
            check(f"broken store {raw[:18]!r}: starts clean, no errors", ok and pg.input_value("#engineSel") == "unity" and not errs, "; ".join(errs[:2]))
            c2.close()

        # ---- 390 px ------------------------------------------------------
        mob = b.new_context(viewport={"width": 390, "height": 844}, locale="tr-TR", has_touch=True, is_mobile=True).new_page()
        for route, sel in (("#/", "#homeView"), ("#/journey", "#journeyView"), ("#/lesson/first-tree", "#lessonView")):
            mob.goto(url + route)
            mob.wait_for_selector(sel + ":not([hidden])")
            mob.wait_for_timeout(300)
            sw = mob.evaluate("document.documentElement.scrollWidth")
            small = mob.evaluate("""[...document.querySelectorAll('#homeGo,#homeMap,.engine,.node button,#jHome,#toJourney,#engineSel,[data-lang]')]
                .filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => (e.id || e.className || e.textContent) + ':' + e.getBoundingClientRect().height.toFixed(1))""")
            check(f"390px {route}: no horizontal scroll, 44px targets", sw <= 390 and not small, f"scrollWidth={sw} small={small}")
            if route == "#/journey":
                mob.screenshot(path=os.path.join(shots, "16_roadmap_mobile.png"), full_page=True)
        check("TR: roadmap texts translated", "Seviye 1" in mob.evaluate("document.getElementById('jTitle').textContent"))
        b.close()

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
