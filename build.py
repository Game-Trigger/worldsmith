"""Inlines three.js + CodeMirror into src.html.

Outputs:
  dist/page.html  fragment (no doctype/head/body), what gets published as an artifact
  dist/test.html  same page wrapped in a minimal HTML skeleton, open this locally
Team modules in web/<module>/*.css and *.js are inlined at <!-- WEB_MODULES -->
(before </body>, or at the end of the fragment, when the marker is missing). No web/ folder is fine.
Run `npm install` once first.
"""
import glob
import os
import re

root = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(root, *a)
read = lambda path: open(path, encoding="utf-8").read()
safe = lambda js: re.sub(r"</script", r"<\\/script", js, flags=re.I)
safe_css = lambda css: re.sub(r"</style", r"<\\/style", css, flags=re.I)
WEB_MARKER = "<!-- WEB_MODULES -->"


def web_modules(web_dir):
    """<style>/<script> tags for web/*/*.css and web/*/*.js, alphabetical by path. '' when there are none."""
    found = glob.glob(os.path.join(web_dir, "*", "*.css")) + glob.glob(os.path.join(web_dir, "*", "*.js"))
    names = sorted(os.path.relpath(f, web_dir).replace(os.sep, "/") for f in found)
    tags = []
    for name in names:
        body = read(os.path.join(web_dir, *name.split("/")))
        if name.endswith(".css"):
            tags.append(f'<style data-web-module="{name}">\n{safe_css(body)}\n</style>')
        else:
            tags.append(f'<script data-web-module="{name}">\n{safe(body)}\n</script>')
    return "\n".join(tags)


def inline_web_modules(html, web_dir):
    block = web_modules(web_dir)
    if WEB_MARKER in html:
        return html.replace(WEB_MARKER, block, 1)
    if not block:
        return html
    i = html.lower().rfind("</body>")
    return html[:i] + block + "\n" + html[i:] if i >= 0 else html + "\n" + block


def build():
    src = inline_web_modules(read(p("src.html")), p("web"))
    three = read(p("node_modules", "three", "build", "three.min.js"))
    cm_css = read(p("node_modules", "codemirror", "lib", "codemirror.css"))
    cm_js = "".join(read(p("node_modules", "codemirror", f)) + "\n" for f in [
        "lib/codemirror.js", "mode/javascript/javascript.js",
        "addon/edit/closebrackets.js", "addon/edit/matchbrackets.js"])

    strip_map = lambda js: re.sub(r"//# sourceMappingURL=.*", "", js)

    out = (src.replace("/*__CM_CSS__*/", cm_css)
              .replace("/*__THREE__*/", safe(strip_map(three)))
              .replace("/*__CM_JS__*/", safe(strip_map(cm_js))))

    os.makedirs(p("dist"), exist_ok=True)
    open(p("dist", "page.html"), "w", encoding="utf-8").write(out)
    test = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
            'body{margin:0;font:14px system-ui;background:#fafafa}img{max-width:100%}[hidden]{display:none!important}</style>'
            '</head><body>' + out + '</body></html>')
    open(p("dist", "test.html"), "w", encoding="utf-8").write(test)
    print(f"built dist/page.html ({len(out) // 1024} KB) and dist/test.html")


if __name__ == "__main__":
    build()
