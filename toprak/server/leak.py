"""Decides whether a coach reply gives away the solution.

Two independent checks, both deterministic (no model involved):
  1. lesson-specific regexes (content/lessons.json -> leak_patterns), e.g. a
     tree() call with concrete numbers on the first mission;
  2. token n-gram overlap with the reference solution, ignoring everything the
     learner already has in their editor.

The model also has to set reveals_solution=false, but that flag is only a
promise; this module is the actual gate.
"""
import re

_TOKEN = re.compile(r"[A-Za-z_]\w*|\d+(?:\.\d+)?|\S")
_NGRAM = 5
_OVERLAP_LIMIT = 0.5
_MIN_REMAINING = 4


def _strip_comments(code):
    code = re.sub(r"/\*[\s\S]*?\*/", "", code)
    return re.sub(r"//.*$", "", code, flags=re.M)


def _tokens(text):
    out = []
    for t in _TOKEN.findall(text):
        out.append("N" if t[0].isdigit() else t)
    return out


def _grams(tokens, n=_NGRAM):
    return {tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


def _remove_learner_lines(text, learner_code):
    """A coach may quote the learner's own line back; that is not a leak."""
    for line in learner_code.splitlines():
        line = line.strip()
        if len(line) >= 6 and not line.startswith("//"):
            text = text.replace(line, " ")
            bare = line.rstrip(";").strip()   # quoted without its semicolon, e.g. "your sun(80) is high"
            if len(bare) >= 5:
                text = text.replace(bare, " ")
    return text


def collect_text(reply):
    """Every field of a reply that a learner can read."""
    parts = [reply.get("message") or "", reply.get("hint") or ""]
    task = reply.get("task")
    if isinstance(task, dict):
        parts += [task.get("title") or "", task.get("goal") or "", task.get("starter_code") or ""]
        parts += [c for c in task.get("success_criteria") or [] if isinstance(c, str)]
    return "\n".join(parts)


def find_leak(reply, lesson, learner_code=""):
    """Return None when the reply is clean, otherwise a short reason string."""
    text = _remove_learner_lines(collect_text(reply), learner_code)

    for pat in lesson.get("leak_patterns", []):
        m = re.search(pat, text)
        if m:
            return f"matches solution pattern: {m.group(0)[:60]!r}"

    ref = _grams(_tokens(_strip_comments(lesson.get("reference_solution", ""))))
    have = _grams(_tokens(_strip_comments(learner_code)))
    remaining = ref - have
    if len(remaining) >= _MIN_REMAINING:
        got = _grams(_tokens(_strip_comments(text)))
        share = len(remaining & got) / len(remaining)
        if share >= _OVERLAP_LIMIT:
            return f"{share:.0%} of the missing solution tokens appear in the reply"
    return None
