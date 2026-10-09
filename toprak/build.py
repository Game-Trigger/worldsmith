"""Inlines three.js + CodeMirror into src.html.

Outputs:
  dist/page.html  fragment (no doctype/head/body), what gets published as an artifact
  dist/test.html  same page wrapped in a minimal HTML skeleton, open this locally
Run `npm install` once first.
"""
import os
import re

root = os.path.dirname(os.path.abspath(__file__))
p = lambda *a: os.path.join(root, *a)
read = lambda path: open(path, encoding="utf-8").read()

src = read(p("src.html"))
three = read(p("node_modules", "three", "build", "three.min.js"))
cm_css = read(p("node_modules", "codemirror", "lib", "codemirror.css"))
cm_js = "".join(read(p("node_modules", "codemirror", f)) + "\n" for f in [
    "lib/codemirror.js", "mode/javascript/javascript.js",
    "addon/edit/closebrackets.js", "addon/edit/matchbrackets.js"])

strip_map = lambda js: re.sub(r"//# sourceMappingURL=.*", "", js)
safe = lambda js: re.sub(r"</script", r"<\\/script", js, flags=re.I)

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
