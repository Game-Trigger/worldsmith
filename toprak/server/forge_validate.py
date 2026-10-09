"""Checks for AI Forge replies (a game object built from primitives) before the page sees them.

The schema (shared/forge-schema.json) covers shape and types; this file covers what that
checker cannot: number ranges, colours, names, and whether the result is a real object.
The page also clamps everything it draws, so this is the second line, not the only one.
"""
import math
import re

# commands that already exist in the engine, plus the spawn command itself
RESERVED = frozenset({"ground", "tree", "rock", "house", "sun", "fog", "random", "spawn", "math", "undefined", "null"})
NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,19}$")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
XZ, Y_MAX, SIZE_LO, SIZE_HI = 3.0, 6.0, 0.05, 4.0


def _nums(v):
    return all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in v)


def unique_name(name, existing):
    """name, name_2, name_3 ... so a second 'lantern' never replaces the first."""
    taken = set(existing) | RESERVED
    if name not in taken:
        return name
    i = 2
    while True:
        suffix = f"_{i}"
        cand = name[: 20 - len(suffix)] + suffix
        if cand not in taken:
            return cand
        i += 1


def extent(parts):
    """(width, height, depth) of the whole object, ignoring rotation."""
    lo = [min(p["position"][i] - p["size"][i] / 2 for p in parts) for i in range(3)]
    hi = [max(p["position"][i] + p["size"][i] / 2 for p in parts) for i in range(3)]
    return hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]


def check_asset(obj):
    """Return '' when the object is fine, else a short reason (fed back to the model on retry)."""
    name = obj.get("name", "")
    if not NAME_RE.match(name):
        return "name: use 3 to 20 characters, lowercase a-z, digits and underscore, starting with a letter (for example windmill or stone_tower)"
    if name in RESERVED:
        return f"name: '{name}' is already an engine command; pick another name"
    parts = obj.get("parts", [])
    for i, p in enumerate(parts):
        where = f"parts[{i}]"
        if not COLOR_RE.match(p["color"]):
            return f"{where}.color: '{p['color']}' is not a #rrggbb colour"
        if not _nums(p["position"]) or not _nums(p["size"]):
            return f"{where}: position and size must be finite numbers"
        x, y, z = p["position"]
        if abs(x) > XZ or abs(z) > XZ or not (0 <= y <= Y_MAX):
            return f"{where}.position: x and z must be within -{XZ:g}..{XZ:g}, y within 0..{Y_MAX:g} (got {x:g}, {y:g}, {z:g})"
        if any(s < SIZE_LO or s > SIZE_HI for s in p["size"]):
            return f"{where}.size: each of width, height, depth must be {SIZE_LO:g}..{SIZE_HI:g} (got {p['size']})"
        r = p.get("rotation_y", 0)
        if not _nums([r]) or abs(r) > 360:
            return f"{where}.rotation_y: degrees between -360 and 360"
    w, h, d = extent(parts)
    if max(w, h, d) < 0.5:
        return "tiny: the whole object is smaller than 0.5 units; make it bigger"
    if len({(p["shape"], p["color"], tuple(p["position"]), tuple(p["size"])) for p in parts}) < 2:
        return "parts: the parts are identical copies in one place; build a real object from different shapes"
    if len({p["color"].lower() for p in parts}) < 2:
        return "colours: use at least two colours so the object reads as made of different materials"
    return ""


def clean(obj, existing):
    """Round numbers, make the name unique. Call only after check_asset returned ''."""
    out = dict(obj)
    out["name"] = unique_name(obj["name"], existing)
    out["parts"] = [
        {"shape": p["shape"], "color": p["color"].lower(),
         "position": [round(float(n), 3) for n in p["position"]],
         "size": [round(float(n), 3) for n in p["size"]],
         "rotation_y": round(float(p.get("rotation_y", 0)), 1)}
        for p in obj["parts"]
    ]
    return out
