"""Tiny JSON Schema checker for shared/coach-schema.json.

Only the keywords that file uses are supported: type, enum, const, required,
properties, additionalProperties (false), minLength, maxLength, minItems,
maxItems, items. Standard library only, so the server has no install step.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "shared", "coach-schema.json")

_TYPES = {
    "string": lambda v: isinstance(v, str),
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "null": lambda v: v is None,
    "boolean": lambda v: isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
}


def load_schema(path=SCHEMA_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(value, schema, path="$"):
    """Return a list of human-readable problems. Empty list means valid."""
    errs = []

    if "const" in schema:
        want = schema["const"]
        if value != want or type(value) is not type(want):
            errs.append(f"{path}: must be {json.dumps(want)}")
            return errs

    if "type" in schema:
        kinds = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_TYPES[k](value) for k in kinds):
            errs.append(f"{path}: expected {'|'.join(kinds)}, got {type(value).__name__}")
            return errs

    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {json.dumps(value, ensure_ascii=False)} is not one of {schema['enum']}")

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']} characters")
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errs.append(f"{path}: longer than {schema['maxLength']} characters ({len(value)})")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, item in enumerate(value):
                errs += validate(item, schema["items"], f"{path}[{i}]")

    if isinstance(value, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errs.append(f"{path}: missing required '{key}'")
        if schema.get("additionalProperties") is False:
            for key in value:
                if key not in props:
                    errs.append(f"{path}: unexpected key '{key}'")
        for key, sub in props.items():
            if key in value:
                errs += validate(value[key], sub, f"{path}.{key}")

    return errs
