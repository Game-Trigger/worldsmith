"""Static checks on prompt-mode code before the page ever runs it.

The page runs the code in a Web Worker that only exposes the engine API, so this is
the second line, not the first. It keeps out what the learner has not unlocked yet,
anything that is not a plain scene program, and code that disagrees with `uses`.
"""
import re

API = ("ground", "tree", "rock", "house", "sun", "fog", "random")
# words a scene program never needs; the worker would block most of them anyway
FORBIDDEN = ("fetch", "import", "eval", "Function", "constructor", "prototype", "__proto__", "globalThis", "self",
             "window", "document", "postMessage", "XMLHttpRequest", "WebSocket", "Worker", "setTimeout", "setInterval",
             "require", "process", "async", "await", "class", "this", "new")
KEYWORDS = ("for", "if", "while", "switch", "return", "function", "catch")
MATH_OK = ("floor", "round", "ceil", "abs", "min", "max", "sin", "cos", "sqrt", "PI")

_word = re.compile(r"[A-Za-z_$][\w$]*")
_call = re.compile(r"(?<![\w$.])([A-Za-z_$][\w$]*)\s*\(")
_dot = re.compile(r"([A-Za-z_$][\w$]*)\s*\.\s*([A-Za-z_$][\w$]*)")


def _strip(code):
    """Code with comments and string contents blanked, so words in them do not count."""
    code = re.sub(r"/\*.*?\*/", " ", code, flags=re.S)
    code = re.sub(r"//[^\n]*", " ", code)
    return re.sub(r"(['\"`])(?:\\.|(?!\1).)*\1", '""', code)


def calls(code):
    """Engine commands the code calls, in API order."""
    found = set(_call.findall(_strip(code)))
    return [name for name in API if name in found]


def check_code(code, uses, unlocked):
    """Return '' when fine, else a short reason (fed back to the model on retry)."""
    body = _strip(code)
    words = set(_word.findall(body))
    bad = sorted(w for w in FORBIDDEN if w in words)
    if bad:
        return f"forbidden: code uses {', '.join(bad)}; only plain loops, variables, Math and the scene commands are allowed"
    for obj, prop in _dot.findall(body):
        if obj != "Math" or prop not in MATH_OK:
            return f"forbidden: '{obj}.{prop}' is not allowed; only Math.{'/'.join(MATH_OK)}"
    used = calls(code)
    if not used:
        return "no_scene: code calls no scene command, so the world would not change"
    locked = [name for name in used if name not in unlocked]
    if locked:
        return f"locked: {', '.join(locked)} is not unlocked yet; use only {', '.join(unlocked)}"
    defined = set(re.findall(r"\bfunction\s+([A-Za-z_$][\w$]*)", body)) | set(
        re.findall(r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>", body))
    unknown = sorted(n for n in set(_call.findall(body)) if n not in API and n not in KEYWORDS and n not in defined)
    if unknown:
        return f"unknown: {', '.join(unknown)} does not exist in the engine"
    if sorted(set(uses)) != sorted(used):
        return f"uses: 'uses' says {sorted(set(uses))} but the code calls {used}"
    if body.count("(") != body.count(")") or body.count("{") != body.count("}"):
        return "syntax: brackets do not balance"
    return ""
