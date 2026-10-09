"""Browser end-to-end test for the site pages around the lessons: top bar, Workshop (Cloud Forge), and the others
as they are added. Real server code + real page + headless Chromium, scripted model (provider "mock").

    python tests/e2e_pages.py        (needs: pip install playwright, `python build.py` done)
Screenshots: tests/shots/30_*.png (desktop) and 31_*.png (390 px).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import e2e_forge as fz  # noqa: E402  (scripted Forge + coach stand-in, mock provider)
import app  # noqa: E402
import forge  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

base = fz.base
check, results = base.check, base.results
PAGES = [("#/", "#homeView", "home"), ("#/journey", "#journeyView", "journey"), ("#/workshop", "#workshopView", "workshop"),
         ("#/profile", "#profileView", "profile")]


def go(page, url, route, sel):
    page.goto(url + route)
    page.wait_for_selector(sel + ":not([hidden])", timeout=10000)


def workshop(page, url):
    go(page, url, "#/workshop", "#workshopView")
    check("workshop: top bar marks Workshop as current", page.get_attribute("[data-nav=workshop]", "aria-current") == "page")
    check("workshop: device, server and world nodes", all(page.is_visible(s) for s in ("#wsDeviceKv", "#wsServerKv", "#wsCanvas")))
    page.wait_for_function("document.querySelector('#wsServerKv').textContent.includes('ready')", timeout=8000)
    kv = page.inner_text("#wsServerKv")
    check("workshop: real status, nothing invented before a request", "mock" in kv and kv.count("no request yet") == 3, kv)
    check("workshop: empty gallery explains itself", page.is_visible("#wsNone") and "No models yet" in page.inner_text("#wsNone"))
    page.click("#wsGo")
    check("workshop: empty description gets a specific message", "Write what to model first" in page.inner_text("#wsStatus"), page.inner_text("#wsStatus"))
    page.fill("#wsText", "a wooden windmill")
    page.click("#wsGo")
    page.wait_for_function("!document.querySelector('#wsStatus').classList.contains('busy')", timeout=15000)
    check("workshop: object built, spawn line shown", page.is_visible("#wsResult") and page.inner_text("#wsLine") == 'spawn("windmill", 0, 0);', page.inner_text("#wsStatus"))
    kv = page.inner_text("#wsServerKv")
    check("workshop: measured latency, model and last request", " ms" in kv and "Workshop · ok" in kv and "no request yet" not in kv, kv)
    check("workshop: gallery lists the model, world caption names it", "Windmill" in page.inner_text("#wsList") and "Windmill" in page.inner_text("#wsWorldSub"))
    page.screenshot(path=os.path.join(base.SHOTS, "30_workshop.png"), full_page=True)
    page.click("#wsUse")
    page.wait_for_selector("#lessonView:not([hidden])", timeout=8000)
    code = page.evaluate("document.querySelector('.CodeMirror').CodeMirror.getValue()")
    check("workshop: 'Add to my lesson' places it with spawn()", 'spawn("windmill"' in code, code[-80:])
    page.go_back()
    page.wait_for_selector("#workshopView:not([hidden])", timeout=8000)
    check("browser back returns to the workshop", True)
    page.click("#wsList [data-wsdel=windmill]")
    check("workshop: delete asks first", page.is_visible("#confirm"))
    page.click("#confirmYes")
    check("workshop: deleted model leaves the gallery", page.is_visible("#wsNone"))
    fz.SCRIPT["fail"] = True
    page.fill("#wsText", "a stone well")
    page.click("#wsGo")
    page.wait_for_function("!document.querySelector('#wsStatus').classList.contains('busy')", timeout=15000)
    check("workshop: model outage gives a specific message", "cannot be reached" in page.inner_text("#wsStatus") and page.is_enabled("#wsGo"), page.inner_text("#wsStatus"))
    check("workshop: failed request is shown as failed", "failed" in page.inner_text("#wsServerKv"))
    fz.SCRIPT["fail"] = False


def profile(b, url):
    ctx = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
    page = ctx.new_page()
    go(page, url, "#/profile", "#profileView")
    check("profile: fresh browser shows zeros and an empty-badge message", page.inner_text("#pfXp") == "0" and page.is_visible("#pfNoBadge")
          and page.locator("#pfBadgeList .badge.earned").count() == 0)
    check("profile: says data stays in this browser", "stays in this browser" in page.inner_text("#profileView"))
    # earn a badge for real: finish lesson 1 through the lesson screen
    go(page, url, "#/lesson/first-tree", "#lessonView")
    base.type_code(page, 'ground("#6a994e");\ntree(4, -6);\n')
    page.keyboard.press("Control+Enter")
    page.wait_for_selector("#btnNext", state="visible", timeout=8000)
    page.click("[data-nav=profile]")
    page.wait_for_selector("#profileView:not([hidden])")
    check("profile: the finished lesson's badge is earned, others stay locked", page.locator("#pfBadgeList .badge.earned").count() == 1
          and "Locked" in page.inner_text("#pfBadgeList") and page.inner_text("#pfXp") == "50" and page.inner_text("#pfStreak") == "1")
    page.click("[data-pfengine=godot]")
    check("profile: engine choice applies everywhere", page.input_value("#engineSel") == "godot" and page.get_attribute("[data-pfengine=godot]", "aria-checked") == "true")
    page.click("#pfReset")
    check("profile: reset asks first", page.is_visible("#confirm"))
    page.click("#confirmNo")
    check("profile: cancel keeps progress", page.inner_text("#pfXp") == "50")
    page.click("#pfReset")
    page.click("#confirmYes")
    go(page, url, "#/profile", "#profileView")
    check("profile: reset clears XP, badges and streak", page.inner_text("#pfXp") == "0" and page.inner_text("#pfStreak") == "0" and page.is_visible("#pfNoBadge"))
    page.screenshot(path=os.path.join(base.SHOTS, "30_profile.png"), full_page=True)
    ctx.close()


def main():
    srv = base.serve_app()
    app.forge_service = forge.ForgeService(log_dir=os.path.join(base.ROOT, "tests", ".e2e_logs"))
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    static = base.serve_static_only()
    static_url = f"http://127.0.0.1:{static.server_address[1]}/test.html"
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"])
        page = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        workshop(page, url)
        profile(b, url)

        # top bar reaches every page, browser back walks back through them
        go(page, url, "#/", "#homeView")
        for route, sel, name in PAGES[1:]:
            page.click(f"[data-nav={name}]")
            page.wait_for_selector(sel + ":not([hidden])", timeout=8000)
        check("top bar: every page reachable", page.evaluate("location.hash") == PAGES[-1][0])
        for route, sel, name in reversed(PAGES[:-1]):
            page.go_back()
            page.wait_for_selector(sel + ":not([hidden])", timeout=8000)
        check("browser back walks the pages in reverse", page.evaluate("location.hash") in ("", "#/"))
        check("no page errors (pages scenario)", not errors, "; ".join(errors[:3]))

        # no server: the workshop says so and the lessons keep working
        off = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US").new_page()
        off_err = []
        off.on("pageerror", lambda e: off_err.append(str(e)))
        go(off, static_url, "#/workshop", "#workshopView")
        off.wait_for_function("!document.querySelector('#wsOff').hidden && document.querySelector('#wsOff').textContent.includes('cannot be reached')", timeout=8000)
        check("no server: workshop says why and points to the rule-based coach", "rule-based coach" in off.inner_text("#wsOff") and off.is_disabled("#wsGo") and off.is_disabled("#wsText"))
        check("no server: status says unreachable", "unreachable" in off.inner_text("#wsServerKv"))
        off.screenshot(path=os.path.join(base.SHOTS, "30_workshop_no_server.png"), full_page=True)
        check("no server: no page errors", not off_err, "; ".join(off_err[:3]))

        # broken storage on a page other than the lesson
        bc = b.new_context(viewport={"width": 1280, "height": 820}, locale="en-US")
        bc.add_init_script("if (!sessionStorage.getItem('s')) { localStorage.setItem('worldsmith.v1', '{oops'); localStorage.setItem('worldsmith.forge.v1', '[{\"name\":1}]'); sessionStorage.setItem('s', '1'); }")
        bp = bc.new_page()
        b_err = []
        bp.on("pageerror", lambda e: b_err.append(str(e)))
        go(bp, url, "#/workshop", "#workshopView")
        check("broken storage: workshop opens clean", not b_err and bp.is_visible("#wsNone"), "; ".join(b_err[:2]))
        bc.close()

        # 390 px: every page fits, top bar targets are 44 px
        mob = b.new_context(viewport={"width": 390, "height": 844}, locale="tr-TR", has_touch=True, is_mobile=True).new_page()
        for route, sel, name in PAGES:
            go(mob, url, route, sel)
            mob.wait_for_timeout(300)
            sw = mob.evaluate("document.documentElement.scrollWidth")
            small = mob.evaluate("""[...document.querySelectorAll('.topnav a, .topnav button, .topnav select, #wsGo, #wsList button, .pf button, .faq summary')]
                .filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => (e.id || e.textContent.trim()) + ':' + e.getBoundingClientRect().height.toFixed(0))""")
            check(f"390px {route}: no horizontal scroll, 44px targets", sw <= 390 and not small, f"scrollWidth={sw} small={small}")
            mob.screenshot(path=os.path.join(base.SHOTS, f"31_{name}_mobile.png"), full_page=True)
        check("TR: top bar translated", "Atölye" in mob.inner_text("#tnLinks"))
        b.close()

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)}/{len(results)} checks passed")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
