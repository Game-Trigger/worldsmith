"""Worldsmith promo video: records the REAL running app with a scripted tour, cinematic zooms, title cards and captions.

    python server/app.py            (in one terminal, with the real AI key in .env)
    python tests/promo_video.py     (in another)  ->  promo/worldsmith_promo.webm   (about 1.5 minutes)

Options: --url http://127.0.0.1:8765  --headless  --lang tr|en
Nothing is faked: the AI answers you see are the real server's. If an AI call fails, the tour carries on and says so in the log.
"""
import argparse
import os
import shutil
import sys
import time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1920, 1080

INIT_JS = r"""
(() => {
 const boot = () => {
  if (window.__promo) return; window.__promo = true;
  const css = document.createElement('style');
  css.textContent = `
  html{overflow-x:hidden}
  body{transition:transform 1.6s cubic-bezier(.65,0,.25,1);will-change:transform}
  #pcap{position:fixed;left:50%;bottom:7%;transform:translate(-50%,24px);max-width:78vw;padding:18px 34px;border:4px solid #e0702b;
    background:#14110fee;color:#fff;font:700 38px/1.25 "Press Start 2P",ui-monospace,monospace;letter-spacing:.5px;text-align:center;
    box-shadow:8px 8px 0 #000;opacity:0;transition:opacity .5s,transform .5s;z-index:99998;pointer-events:none;border-radius:2px}
  #pcap small{display:block;margin-top:12px;font:600 22px/1.3 Inter,system-ui,sans-serif;color:#f5b13d;letter-spacing:0}
  #pcap.on{opacity:1;transform:translate(-50%,0)}
  #pcard{position:fixed;inset:0;z-index:99999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;
    background:radial-gradient(ellipse at 50% 40%,#2a1d12 0,#14110f 70%);color:#fff;opacity:0;pointer-events:none;transition:opacity .9s}
  #pcard.on{opacity:1}
  #pcard h1{margin:0;font:900 96px/1.1 "Press Start 2P",ui-monospace,monospace;color:#f5b13d;text-shadow:6px 6px 0 #e0702b,12px 12px 0 #000;letter-spacing:2px}
  #pcard p{margin:0;font:600 34px/1.35 Inter,system-ui,sans-serif;color:#e8e0d0;text-align:center;max-width:70vw}
  #pcard small{font:600 24px/1 ui-monospace,monospace;color:#6fae3f}
  #pcur{position:fixed;left:0;top:0;width:34px;height:34px;z-index:100000;pointer-events:none;margin:-4px 0 0 -4px;
    background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='34' height='34' viewBox='0 0 24 24'><path d='M3 2l7 19 3-8 8-3z' fill='%23f5b13d' stroke='%23000' stroke-width='1.6' stroke-linejoin='round'/></svg>") no-repeat}
  .pspark{position:fixed;width:10px;height:10px;z-index:100000;pointer-events:none;background:#f5b13d}
  `;
  document.documentElement.appendChild(css);
  const mk = (id, tag='div') => { const e = document.createElement(tag); e.id = id; document.documentElement.appendChild(e); return e; };
  const cap = mk('pcap'), card = mk('pcard'), cur = mk('pcur');
  window.addEventListener('mousemove', e => { cur.style.transform = `translate(${e.clientX}px,${e.clientY}px)`; }, true);
  window.addEventListener('mousedown', e => window.__burst(e.clientX, e.clientY, 14), true);
  window.__cap = (t, s) => { cap.innerHTML = t + (s ? '<small>' + s + '</small>' : ''); cap.classList.add('on'); };
  window.__capOff = () => cap.classList.remove('on');
  window.__card = (h, p, s) => { card.innerHTML = '<h1>' + h + '</h1>' + (p ? '<p>' + p + '</p>' : '') + (s ? '<small>' + s + '</small>' : ''); card.classList.add('on'); };
  window.__cardOff = () => card.classList.remove('on');
  window.__cam = (sel, scale) => {
    const b = document.body;
    if (!sel) { b.style.transform = 'none'; return; }
    const el = document.querySelector(sel); if (!el) return;
    const r = el.getBoundingClientRect();
    b.style.transformOrigin = (r.left + r.width / 2 + scrollX) + 'px ' + (r.top + r.height / 2 + scrollY) + 'px';
    b.style.transform = 'scale(' + scale + ')';
  };
  window.__burst = (x, y, n) => {
    const cols = ['#f5b13d', '#e0702b', '#fff3c4', '#6fae3f'];
    for (let i = 0; i < n; i++) {
      const s = document.createElement('i'); s.className = 'pspark'; s.style.left = x + 'px'; s.style.top = y + 'px';
      s.style.background = cols[i % cols.length]; document.documentElement.appendChild(s);
      const a = Math.random() * Math.PI * 2, d = 40 + Math.random() * 120;
      s.animate([{ transform: 'translate(0,0) scale(1)', opacity: 1 }, { transform: `translate(${Math.cos(a) * d}px,${Math.sin(a) * d - 30}px) scale(.2)`, opacity: 0 }],
        { duration: 700 + Math.random() * 400, easing: 'ease-out' }).onfinish = () => s.remove();
    }
  };
 };
 if (document.documentElement && document.body) boot();
 else document.addEventListener('DOMContentLoaded', boot);
})();
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8765")
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--lang", default="en", choices=["tr", "en"])
    a = ap.parse_args()
    tr = a.lang == "tr"
    T = (lambda t, e: t if tr else e)
    out_dir = os.path.join(ROOT, "promo")
    tmp = os.path.join(out_dir, "_raw")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp, exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch(headless=a.headless, args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox", f"--window-size={W},{H + 120}"])
        ctx = b.new_context(viewport={"width": W, "height": H}, record_video_dir=tmp, record_video_size={"width": W, "height": H},
                            locale="tr-TR" if tr else "en-US")
        ctx.add_init_script(INIT_JS)
        page = ctx.new_page()
        page.on("dialog", lambda d: d.dismiss())
        wait = page.wait_for_timeout

        def js(code, arg=None):
            return page.evaluate(code, arg)

        def cap(t, s=""):
            js("([t,s]) => window.__cap(t,s)", [t, s])

        def capoff():
            js("() => window.__capOff()")

        def cam(sel, scale=1.5):
            js("([s,k]) => window.__cam(s,k)", [sel, scale])

        def move(sel, steps=40):
            box = page.locator(sel).first.bounding_box()
            if box:
                page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=steps)

        def click(sel):
            move(sel)
            wait(250)
            page.locator(sel).first.click()

        def route(h):
            js("h => { location.hash = h; }", h)

        def cm_type(text, delay=85):
            for ch in text:
                js("c => document.querySelector('.CodeMirror').CodeMirror.replaceSelection(c)", ch)
                wait(delay)

        page.goto(a.url + "/#/")
        page.wait_for_selector("#homeView:not([hidden])", timeout=15000)
        js("() => { try { localStorage.clear(); } catch (e) {} }")
        page.reload()
        page.wait_for_selector("#homeView:not([hidden])", timeout=15000)
        js("l => document.querySelector(l).click()", "#langEn" if not tr else "#langTr")   # force the site language, no mouse involved
        wait(600)
        page.mouse.move(W * 0.5, H * 0.6)

        # 1. title card
        js("([h,p,s]) => window.__card(h,p,s)", ["WORLDSMITH", T("Oyun yapmayı, yaparak öğren.", "Learn game development by building."), "AI Gaming"])
        wait(3600)
        js("() => window.__cardOff()")
        cam("#heroCanvas", 1.18)
        wait(1200)

        # 2. home
        cap(T("Güçlü bilgisayar yok. Oyun motoru kurulumu yok.", "No strong PC. No engine install."), T("Sadece tarayıcı.", "Just a browser."))
        wait(3600)
        cam(None)
        capoff()
        wait(900)
        for y in (700, 1500, 2300):
            js("y => window.scrollTo({top: y, behavior: 'smooth'})", y)
            wait(1500)
        cap(T("Herkes tek satır prompt ile oyun yaptırıyor.", "Everyone prompts a game into existence."), T("Kimse hiçbir şey öğrenmiyor.", "Nobody learns anything."))
        wait(3800)
        capoff()
        js("() => window.scrollTo({top: 0, behavior: 'smooth'})")
        wait(1400)

        # 3. roadmap
        click("#homeMap")
        page.wait_for_selector("#journeyView:not([hidden])", timeout=8000)
        wait(900)
        cap(T("Ünite ünite, biyom biyom ilerle.", "Unit by unit, biome by biome."), T("Çayır, Taş Ocağı, Mağara.", "Meadow, Quarry, Cave."))
        cam("[data-node='0']", 1.35)
        wait(3600)
        cam(None)
        capoff()
        wait(900)

        # 4. lesson: write code, see the world change
        click("[data-node='0']")
        page.wait_for_selector("#lessonView:not([hidden]) .CodeMirror", timeout=10000)
        wait(1200)
        cap(T("Üstte dünyan, altta kodun.", "Your world on top, your code below."))
        wait(2400)
        capoff()
        js("() => { const cm = document.querySelector('.CodeMirror').CodeMirror; cm.focus(); cm.setValue('ground(\"#6a994e\");\\n\\n'); cm.setCursor(cm.lineCount(), 0); }")
        move(".CodeMirror", 30)
        page.locator(".CodeMirror").first.click()
        js("() => { const cm = document.querySelector('.CodeMirror').CodeMirror; cm.setCursor(cm.lineCount(), 0); }")
        cm_type("tree(2, 3);")
        wait(500)
        click("#btnRun")
        wait(1800)
        cap(T("Kodu yaz, sahne anında değişir.", "Write code, the scene changes instantly."))
        cam("#scene", 1.3)
        wait(3000)
        cam(None)
        capoff()
        # a deliberate mistake to bring the Socratic coach in
        js("() => { const cm = document.querySelector('.CodeMirror').CodeMirror; cm.setValue('ground(\"#6a994e\");\\n\\ntree(x, z);'); }")
        wait(600)
        click("#btnRun")
        cap(T("Hata mı? Koç cevabı vermez.", "A bug? The coach won't hand you the answer."), T("Soru sorar, öğretir.", "It asks, you learn."))
        wait(7000)
        cam("#msgs", 1.25)
        wait(3600)
        cam(None)
        capoff()
        wait(700)

        # 5. Workshop: the cloud forge
        click("[data-nav=workshop]")
        page.wait_for_selector("#workshopView:not([hidden])", timeout=8000)
        wait(1500)
        cap(T("Ağır iş bizim sunucuda.", "The heavy lifting happens on our servers."), T("Senin cihazın sadece ekran.", "Your device is just a screen."))
        cam("#wsFlow", 1.2)
        wait(4200)
        cam(None)
        capoff()
        for prompt in (T("taş bir kule, tepesinde kırmızı bir bayrak", "a stone tower with a red flag on top"),
                       T("yel değirmeni", "a wooden windmill")):
            click("#wsText")
            page.keyboard.type(prompt, delay=70)
            wait(500)
            cap(T("Hayal et. AI parçalara bölsün.", "Imagine it. The AI builds it from parts."))
            click("#wsGo")
            try:
                page.wait_for_selector("#wsResult:not([hidden])", timeout=45000)
                cam("#wsCanvas", 1.45)
                wait(3800)
            except Exception as e:
                print("Forge call did not finish:", e, file=sys.stderr)
                wait(1500)
            cam(None)
            capoff()
            wait(900)
        cap(T("Gerçek gecikme. Gerçek sunucu. Gerçek AI.", "Real latency. Real server. Real AI."))
        cam("#wsServerKv", 1.6)
        wait(4200)
        cam(None)
        capoff()

        # 6. closing
        route("#/")
        page.wait_for_selector("#homeView:not([hidden])", timeout=8000)
        wait(800)
        js("([h,p,s]) => window.__card(h,p,s)", ["WORLDSMITH", T("Kod yaz. Dünyanı kur. AI koçla öğren.", "Write code. Build your world. Learn with an AI coach."),
                                                  "github.com/T1mmine/worldsmith"])
        wait(4800)

        path = page.video.path()
        ctx.close()
        b.close()

    final = os.path.join(out_dir, "worldsmith_promo.webm")
    shutil.copyfile(path, final)
    print("saved:", final)


if __name__ == "__main__":
    main()
