"""Worldsmith server: serves the built page and the coach API on one origin.

    python server/app.py            # http://localhost:8765
Config comes from .env (repo root or server/), see .env.example. Keys never reach the browser.
"""
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import coach  # noqa: E402
import model  # noqa: E402
import providers  # noqa: E402

DIST = os.path.join(ROOT, "dist")
MAX_BODY = 20_000
STATIC = {"/": "test.html", "/index.html": "test.html", "/test.html": "test.html", "/page.html": "page.html"}


def load_env():
    """Minimal .env reader (no python-dotenv). Real environment variables win."""
    for path in (os.path.join(ROOT, ".env"), os.path.join(HERE, ".env")):
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
        except FileNotFoundError:
            pass


service = None
model_service = None


class Handler(BaseHTTPRequestHandler):
    server_version = "Worldsmith"

    def log_message(self, fmt, *args):  # quieter, and never prints bodies
        sys.stderr.write("%s %s\n" % (self.command, self.path.split("?")[0]))

    def _send(self, status, body, ctype="application/json; charset=utf-8", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _ip(self):
        if os.environ.get("TRUST_PROXY") == "1":
            fwd = self.headers.get("X-Forwarded-For", "")
            if fwd:
                return fwd.split(",")[0].strip()
        return self.client_address[0]

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            prov = os.environ.get("LLM_PROVIDER", "gemini").lower()
            has_key = bool(os.environ.get({"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}.get(prov, "_"), "").strip()) or prov == "mock"
            return self._send(200, {"ok": True, "provider": prov, "configured": has_key})
        if path.startswith("/api/lessons/"):
            lesson = service.lessons.get(path.rsplit("/", 1)[1])
            if not lesson:
                return self._send(404, {"error": {"code": "not_found", "message": "No such lesson."}})
            return self._send(200, coach.public_lesson(lesson))
        name = STATIC.get(path)
        if name:
            try:
                with open(os.path.join(DIST, name), "rb") as f:
                    return self._send(200, f.read(), "text/html; charset=utf-8")
            except FileNotFoundError:
                return self._send(404, {"error": {"code": "not_built", "message": "dist/ is missing. Run: python build.py"}})
        self._send(404, {"error": {"code": "not_found", "message": "Nothing here."}})

    def do_POST(self):
        path = urlparse(self.path).path
        if path not in ("/api/coach", "/api/model"):
            return self._send(404, {"error": {"code": "not_found", "message": "Nothing here."}})
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            n = -1
        if n <= 0 or n > MAX_BODY:
            return self._send(413 if n > MAX_BODY else 400,
                              {"error": {"code": "bad_request", "message": f"Send a JSON body of 1 to {MAX_BODY} bytes."}})
        try:
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._send(400, {"error": {"code": "bad_request", "message": "Body is not valid JSON."}})
        if path == "/api/model":
            status, body = model_service.handle_model(payload, self._ip())
        else:
            status, body = service.handle(payload, self._ip())
        extra = {"Retry-After": str(body["error"]["retry_after"])} if status == 429 else None
        self._send(status, body, extra=extra)


def main():
    global service, model_service
    load_env()
    service = coach.CoachService()
    model_service = model.ModelService()
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "127.0.0.1")
    srv = ThreadingHTTPServer((host, port), Handler)
    prov = os.environ.get("LLM_PROVIDER", "gemini")
    print(f"Worldsmith on http://{host}:{port}  coach provider: {prov}")
    if prov != "mock" and not os.environ.get({"gemini": "GEMINI_API_KEY", "claude": "ANTHROPIC_API_KEY"}.get(prov, "_"), "").strip():
        print("  No API key set for this provider; the page will use the rule-based coach. See .env.example.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nbye")


if __name__ == "__main__":
    main()
