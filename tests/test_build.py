"""build.py web-module inlining. Run: python -m unittest discover -s tests -v"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import build  # noqa: E402


class WebModuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.web = os.path.join(self.tmp, "web")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def put(self, rel, text):
        path = os.path.join(self.web, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def test_missing_web_dir_keeps_page_and_removes_marker(self):
        self.assertEqual(build.inline_web_modules("<p>a</p>", self.web), "<p>a</p>")
        self.assertEqual(build.inline_web_modules("<p>a</p>" + build.WEB_MARKER, self.web), "<p>a</p>")

    def test_files_inlined_alphabetically_at_marker(self):
        self.put("journey/b.js", "window.b = 1;")
        self.put("journey/a.css", ".a{color:red}")
        self.put("alpha/z.js", "window.z = 1;")
        self.put("journey/notes.md", "ignored")
        out = build.inline_web_modules("<p>x</p>" + build.WEB_MARKER + "<p>y</p>", self.web)
        order = [out.index(s) for s in ("alpha/z.js", "journey/a.css", "journey/b.js")]
        self.assertEqual(order, sorted(order))
        self.assertIn('<style data-web-module="journey/a.css">', out)
        self.assertNotIn("ignored", out)
        self.assertNotIn(build.WEB_MARKER, out)
        self.assertTrue(out.startswith("<p>x</p>") and out.endswith("<p>y</p>"))

    def test_no_marker_goes_before_body_end_or_at_end(self):
        self.put("journey/a.js", "1;")
        out = build.inline_web_modules("<body><p>x</p></body>", self.web)
        self.assertLess(out.index("journey/a.js"), out.index("</body>"))
        self.assertTrue(build.inline_web_modules("<p>x</p>", self.web).rstrip().endswith("</script>"))

    def test_closing_script_tag_in_module_is_escaped(self):
        self.put("journey/a.js", 'const s = "</script>";')
        out = build.inline_web_modules(build.WEB_MARKER, self.web)
        self.assertEqual(out.lower().count("</script"), 1)


if __name__ == "__main__":
    unittest.main()
