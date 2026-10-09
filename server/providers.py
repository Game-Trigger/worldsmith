"""One adapter per model provider. coach.py only ever calls `complete()`.

Swap the model by changing LLM_PROVIDER in .env (gemini | claude | mock).
Standard library only (urllib), so the server needs no pip install.
"""
import collections
import json
import os
import threading
import time
import urllib.error
import urllib.request


class ProviderError(Exception):
    """kind: config | timeout | http | quota | parse"""

    def __init__(self, kind, detail=""):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class Reply:
    def __init__(self, text, model, prompt_tokens=None, completion_tokens=None):
        self.text = text
        self.model = model
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


def _post(url, headers, body, timeout):
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=max(1.0, timeout)) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")[:300]
        kind = "quota" if e.code == 429 else "http"
        raise ProviderError(kind, f"HTTP {e.code} {raw}")
    except (TimeoutError, urllib.error.URLError) as e:
        reason = getattr(e, "reason", e)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            raise ProviderError("timeout", str(reason))
        raise ProviderError("http", f"network: {reason}")
    except json.JSONDecodeError:
        raise ProviderError("parse", "provider did not return JSON")


def gemini(system, user, timeout):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise ProviderError("config", "GEMINI_API_KEY is empty")
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    gen = {"responseMimeType": "application/json", "temperature": 0.4, "maxOutputTokens": 900}
    budget = os.environ.get("GEMINI_THINKING_BUDGET", "").strip()
    if budget.lstrip("-").isdigit():
        gen["thinkingConfig"] = {"thinkingBudget": int(budget)}
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": gen,
    }
    data = _post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
        {"Content-Type": "application/json", "x-goog-api-key": key},
        body, timeout)
    try:
        text = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
    except (KeyError, IndexError, TypeError):
        raise ProviderError("parse", "no candidate text in Gemini reply")
    use = data.get("usageMetadata", {})
    return Reply(text, model, use.get("promptTokenCount"), use.get("candidatesTokenCount"))


def claude(system, user, timeout):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        raise ProviderError("config", "ANTHROPIC_API_KEY is empty")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-5-5").strip()
    body = {
        "model": model, "max_tokens": 900, "temperature": 0.4,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    data = _post(
        "https://api.anthropic.com/v1/messages",
        {"Content-Type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"},
        body, timeout)
    try:
        text = "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
    except (KeyError, TypeError):
        raise ProviderError("parse", "no text block in Claude reply")
    use = data.get("usage", {})
    return Reply(text, model, use.get("input_tokens"), use.get("output_tokens"))


# --- test double -----------------------------------------------------------
# LLM_PROVIDER=mock returns whatever tests queue with mock_queue(). It exists
# so failure paths (bad JSON, leaks, timeouts) can be tested without a network.
# Its model id is "mock", so it can never be mistaken for a real reply.
_mock_script = []


def mock_queue(*items):
    """Each item: a str (returned as the reply), or an Exception (raised)."""
    _mock_script[:] = list(items)


def mock(system, user, timeout):
    if not _mock_script:
        raise ProviderError("config", "mock provider has nothing queued")
    item = _mock_script.pop(0)
    if isinstance(item, Exception):
        raise item
    return Reply(item, "mock", 100, 50)


PROVIDERS = {"gemini": gemini, "claude": claude, "mock": mock}


# One window for the whole server (coach, Prompt and Forge, every visitor): the Gemini free tier allows
# 15 calls per minute per model, so we stop at LLM_MAX_PER_MIN and answer "quota" ourselves instead of
# sending a call that Google would refuse. The page then shows "quota used up, try again in 1 minute".
_calls = collections.deque()
_calls_lock = threading.Lock()


def _take_call_slot():
    limit = int(os.environ.get("LLM_MAX_PER_MIN", "14"))
    now = time.monotonic()
    with _calls_lock:
        while _calls and now - _calls[0] > 60:
            _calls.popleft()
        if len(_calls) >= limit:
            raise ProviderError("quota", f"local limit: {limit} model calls per minute reached, wait {int(60 - (now - _calls[0])) + 1} s")
        _calls.append(now)


def complete(system, user, timeout):
    name = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    fn = PROVIDERS.get(name)
    if fn is None:
        raise ProviderError("config", f"unknown LLM_PROVIDER '{name}' (use gemini, claude or mock)")
    if name != "mock":
        _take_call_slot()
    return fn(system, user, timeout)
