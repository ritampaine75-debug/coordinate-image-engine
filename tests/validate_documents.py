#!/usr/bin/env python3
"""Validate coordinate-image-v1 examples and negative cases for CI.

Requires the free, open-source Python package `jsonschema`:

    python3 -m pip install jsonschema

No application runtime or npm dependency is required.
"""
from __future__ import annotations

import copy
import json
import math
import re
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError:
    sys.exit("Missing jsonschema. Install it with: python3 -m pip install jsonschema")

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "skill" / "schemas" / "coordinate-image-v1.schema.json"
EXAMPLES_DIR = ROOT / "skill" / "examples"

MAX_CANVAS_PIXELS = 16_000_000
MAX_TOTAL_ELEMENTS = 1_000
MAX_NESTING = 8
MAX_COMPLEXITY = 50_000
MAX_PATH_COMMANDS_TOTAL = 4_096
MAX_PATH_COMMANDS_EACH = 256
MAX_TEXT_LINES = 32

PATH_COMMANDS = "MmLlHhVvCcQqZz"
PATH_TOKEN_RE = re.compile(r"[MmLlHhVvCcQqZz]|[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?")
PATH_ALLOWED_RE = re.compile(r"^[MmLlHhVvCcQqZz0-9eE+\-., \t\r\n]+$")
PATH_ARITY = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "Q": 4, "Z": 0,
              "m": 2, "l": 2, "h": 1, "v": 1, "c": 6, "q": 4, "z": 0}


def load_json(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def json_path(parts) -> str:
    result = "$"
    for part in parts:
        result += f"[{part}]" if isinstance(part, int) else f".{part}"
    return result


def parse_path_commands(data: str) -> int:
    """Return the command count while enforcing the documented SVG subset."""
    if not isinstance(data, str) or not PATH_ALLOWED_RE.fullmatch(data):
        raise ValueError("path contains a character outside the restricted grammar")
    if len(data) > 8192:
        raise ValueError("path exceeds 8192 characters")
    compact = re.sub(r"[\s,]", "", data)
    tokens = PATH_TOKEN_RE.findall(data)
    if "".join(tokens) != compact:
        raise ValueError("path contains malformed numbers or unsupported commands")
    if not tokens or tokens[0] not in ("M", "m"):
        raise ValueError("path must begin with M or m")
    index = 0
    count = 0
    while index < len(tokens):
        command = tokens[index]
        index += 1
        if command not in PATH_ARITY:
            raise ValueError("expected an explicit command letter; implicit repetition is not supported")
        for _ in range(PATH_ARITY[command]):
            if index >= len(tokens):
                raise ValueError(f"command {command} is missing numeric arguments")
            token = tokens[index]
            if token in PATH_ARITY:
                raise ValueError(f"command {command} is missing numeric arguments")
            number = float(token)
            if not math.isfinite(number) or abs(number) > 1_000_000:
                raise ValueError("path number is non-finite or too large")
            index += 1
        count += 1
        if count > MAX_PATH_COMMANDS_EACH:
            raise ValueError("path has too many commands")
    return count


def check_finite(value, path: str, errors: list[str]) -> None:
    if isinstance(value, bool):
        return
    if isinstance(value, (int, float)) and not math.isfinite(float(value)):
        errors.append(f"{path}: number must be finite")
    elif isinstance(value, dict):
        for key, child in value.items():
            check_finite(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            check_finite(child, f"{path}[{index}]", errors)


def semantic_errors(doc) -> list[str]:
    """Mirror the cross-field runtime checks that JSON Schema cannot express."""
    errors: list[str] = []
    check_finite(doc, "$", errors)
    if not isinstance(doc, dict):
        return errors + ["$: document root must be an object"]
    canvas = doc.get("canvas", {})
    if isinstance(canvas, dict):
        width, height = canvas.get("width"), canvas.get("height")
        if isinstance(width, (int, float)) and isinstance(height, (int, float)) and width * height > MAX_CANVAS_PIXELS:
            errors.append("$.canvas: canvas area exceeds 16000000 logical pixels")

    gradients = doc.get("gradients", {})
    if not isinstance(gradients, dict):
        gradients = {}
    gradient_names = set(gradients.keys())
    units = 0
    for name, definition in gradients.items():
        stops = definition.get("stops", []) if isinstance(definition, dict) else []
        units += 2 + (len(stops) * 2 if isinstance(stops, list) else 0)

    def check_paint(paint, path: str) -> None:
        if isinstance(paint, dict) and "gradient" in paint and paint["gradient"] not in gradient_names:
            errors.append(f"{path}: gradient reference {paint['gradient']!r} is not defined")

    if isinstance(canvas, dict):
        check_paint(canvas.get("background"), "$.canvas.background")

    ids: set[str] = set()
    total = 0
    path_commands_total = 0

    def walk(elements, path: str, depth: int) -> None:
        nonlocal total, units, path_commands_total
        if depth > MAX_NESTING:
            errors.append(f"{path}: group nesting exceeds {MAX_NESTING} levels")
            return
        if not isinstance(elements, list):
            return
        for index, element in enumerate(elements):
            element_path = f"{path}[{index}]"
            total += 1
            units += 1
            if not isinstance(element, dict):
                continue
            element_id = element.get("id")
            if element_id in ids:
                errors.append(f"{element_path}.id: duplicate element id {element_id!r}")
            ids.add(element_id)
            check_paint(element.get("fill"), f"{element_path}.fill")
            check_paint(element.get("stroke"), f"{element_path}.stroke")
            points = element.get("points")
            if isinstance(points, list):
                units += len(points) * 2
            dash = element.get("dash")
            if isinstance(dash, list):
                units += len(dash)
            if "transform" in element:
                units += 2
            if element.get("type") == "path":
                try:
                    commands = parse_path_commands(element.get("d", ""))
                    path_commands_total += commands
                    units += commands * 8
                except ValueError as error:
                    errors.append(f"{element_path}.d: {error}")
            if element.get("type") == "text" and isinstance(element.get("text"), str):
                lines = len(re.split(r"\r?\n", element["text"]))
                units += lines * 6
                if lines > MAX_TEXT_LINES:
                    errors.append(f"{element_path}.text: text exceeds {MAX_TEXT_LINES} lines")
            if element.get("type") == "group":
                walk(element.get("children", []), f"{element_path}.children", depth + 1)

    walk(doc.get("elements", []), "$.elements", 1)
    if total > MAX_TOTAL_ELEMENTS:
        errors.append(f"$.elements: recursive element count exceeds {MAX_TOTAL_ELEMENTS}")
    if path_commands_total > MAX_PATH_COMMANDS_TOTAL:
        errors.append(f"$.elements: total path commands exceed {MAX_PATH_COMMANDS_TOTAL}")
    if units > MAX_COMPLEXITY:
        errors.append(f"$: complexity budget exceeds {MAX_COMPLEXITY}")
    return errors


def combined_errors(validator: Draft202012Validator, doc) -> list[str]:
    schema_errors = []
    for error in validator.iter_errors(doc):
        if error.validator == "maxItems" and isinstance(error.instance, list):
            message = f"array has {len(error.instance)} items; maximum is {error.validator_value}"
        else:
            message = error.message[:240]
        schema_errors.append(f"{json_path(error.absolute_path)}: {message}")
    if schema_errors:
        return schema_errors
    return semantic_errors(doc)



def expect_invalid(validator: Draft202012Validator, label: str, doc, needle: str | None = None) -> None:
    errors = combined_errors(validator, doc)
    assert errors, f"{label}: expected rejection but document was accepted"
    if needle:
        assert any(needle.lower() in error.lower() for error in errors), (
            f"{label}: expected diagnostic containing {needle!r}; got: {[error[:240] for error in errors[:5]]}"
        )
    print(f"  rejected: {label}")


def main() -> int:
    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")
    schema = json.loads(schema_text)
    Draft202012Validator.check_schema(schema)
    references = re.findall(r'"\$ref"\s*:\s*"([^"]+)"', schema_text)
    assert all(reference.startswith("#/") for reference in references), "Schema must use local references only"
    validator = Draft202012Validator(schema)
    print("Schema itself is valid and uses local references only.")

    examples = {}
    for path in sorted(EXAMPLES_DIR.glob("*.json")):
        doc = load_json(path)
        examples[path.stem] = doc
        errors = combined_errors(validator, doc)
        assert not errors, f"Example {path.name} failed:\n" + "\n".join(errors[:10])
        print(f"  valid: {path.name}")
    assert len(examples) >= 7, "Expected at least seven example documents"

    base = copy.deepcopy(examples["simple-diagram"])

    def mutate(fn):
        doc = copy.deepcopy(base)
        fn(doc)
        return doc

    expect_invalid(validator, "missing required canvas", mutate(lambda d: d.pop("canvas")), "canvas")
    expect_invalid(validator, "wrong protocol", mutate(lambda d: d.update(protocol="other-v9")), "coordinate-image-v1")
    expect_invalid(validator, "unsupported element type", mutate(lambda d: d["elements"][0].update(type="iframe")))
    expect_invalid(validator, "invalid color", mutate(lambda d: d["canvas"].update(background="rebeccapurple")), "not valid under any")
    expect_invalid(validator, "out-of-range dimensions", mutate(lambda d: d["canvas"].update(width=9000)), "9000")
    expect_invalid(validator, "canvas area", mutate(lambda d: d["canvas"].update(width=4096, height=4096)), "canvas area")
    expect_invalid(validator, "unknown root property", mutate(lambda d: d.update(unexpected=True)), "additional properties")
    expect_invalid(validator, "dangling gradient", mutate(lambda d: d["canvas"].update(background={"gradient": "missing"})), "not defined")
    expect_invalid(validator, "duplicate ids", mutate(lambda d: (d["elements"][0].update(id="same"), d["elements"][1].update(id="same"))), "duplicate element id")

    too_many = mutate(lambda d: d.update(elements=[
        {"id": f"r{i}", "type": "rectangle", "x": 0, "y": 0, "width": 1, "height": 1, "fill": "#000"}
        for i in range(1001)
    ]))
    expect_invalid(validator, "excessive element count", too_many, "maximum is 1000")

    bad_path = mutate(lambda d: d.update(elements=[
        {"id": "bad-path", "type": "path", "d": "M 0 0 L 10 10 20 20", "stroke": "#fff", "strokeWidth": 1}
    ]))
    expect_invalid(validator, "implicit path repetition", bad_path, "explicit command letter")

    arc_path = mutate(lambda d: d.update(elements=[
        {"id": "arc", "type": "path", "d": "M 0 0 A 10 10 0 0 1 20 20", "stroke": "#fff", "strokeWidth": 1}
    ]))
    expect_invalid(validator, "unsupported SVG arc", arc_path, "not valid under any")

    def deep_groups(d):
        node = {"id": "leaf", "type": "rectangle", "x": 0, "y": 0, "width": 1, "height": 1, "fill": "#000"}
        for i in range(9):
            node = {"id": f"group-{i}", "type": "group", "children": [node]}
        d["elements"] = [node]
    expect_invalid(validator, "excessive group nesting", mutate(deep_groups), "nesting exceeds")

    def too_many_lines(d):
        d["elements"] = [{"id": "long-text", "type": "text", "x": 0, "y": 0,
                          "text": "\n".join(["line"] * 33), "fill": "#000"}]
    expect_invalid(validator, "excessive text lines", mutate(too_many_lines), "exceeds 32 lines")

    try:
        json.loads('{"protocol": "coordinate-image-v1",')
        raise AssertionError("Malformed JSON should raise JSONDecodeError")
    except json.JSONDecodeError:
        print("  rejected: malformed JSON")

    minimal = {
        "protocol": "coordinate-image-v1",
        "canvas": {"width": 16, "height": 16, "background": "#fff"},
        "elements": []
    }
    assert not combined_errors(validator, minimal), "Minimal valid document should pass"
    print("  valid: minimal document")

    print(f"Validation checks passed: {len(examples)} examples, schema, semantics, and negative cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
