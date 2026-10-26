#!/usr/bin/env python3
"""Keep the self-contained index.html assets synchronized with source files.

This optional maintainer tool uses only the Python standard library. The core
application has no build step: index.html already contains the generated data.

Usage:
    python3 tools/update-index-assets.py
    python3 tools/update-index-assets.py --check
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SCHEMA = ROOT / "skill" / "schemas" / "coordinate-image-v1.schema.json"
PROMPT = ROOT / "skill" / "MASTER_PROMPT.md"
EXAMPLES_DIR = ROOT / "skill" / "examples"

EXAMPLE_ORDER = [
    "simple-landscape",
    "futuristic-robot",
    "abstract-art",
    "app-icon",
    "poster-cover",
    "simple-diagram",
    "stylized-architecture",
]

BLOCKS = {
    "protocol-schema": "protocol-schema",
    "example-bundle": "example-bundle",
    "master-prompt": "master-prompt",
}


def safe_script_json(value: object, *, compact: bool = False) -> str:
    if compact:
        text = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(value, ensure_ascii=False, indent=2)
    # A literal closing script tag would terminate the inline data block.
    # <\/ is valid inside JSON strings and is parsed back to </ by JSON.parse.
    return text.replace("</", "<\\/")


def safe_script_text(text: str) -> str:
    # script elements are raw-text elements; only a closing script tag is special.
    return re.sub(r"(?i)</\s*script", r"<\\/script", text.rstrip())


def generated_block(name: str) -> str:
    begin = f"<!-- BEGIN AUTO-GENERATED: {name} -->"
    end = f"<!-- END AUTO-GENERATED: {name} -->"
    if name == "protocol-schema":
        data = json.loads(SCHEMA.read_text(encoding="utf-8"))
        body = safe_script_json(data)
        return f'{begin}\n  <script type="application/json" id="protocol-schema">\n{body}\n  </script>\n{end}'
    if name == "example-bundle":
        examples: dict[str, object] = {}
        files = sorted(EXAMPLES_DIR.glob("*.json"), key=lambda p: EXAMPLE_ORDER.index(p.stem) if p.stem in EXAMPLE_ORDER else 999)
        for file in files:
            examples[file.stem] = json.loads(file.read_text(encoding="utf-8"))
        missing = [key for key in EXAMPLE_ORDER if key not in examples]
        if missing:
            raise SystemExit("Missing expected examples: " + ", ".join(missing))
        body = safe_script_json(examples, compact=True)
        return f'{begin}\n  <script type="application/json" id="example-bundle">\n{body}\n  </script>\n{end}'
    if name == "master-prompt":
        body = safe_script_text(PROMPT.read_text(encoding="utf-8"))
        return f'{begin}\n  <script type="text/plain" id="master-prompt">\n{body}\n  </script>\n{end}'
    raise ValueError(name)


def rebuild(html: str) -> str:
    for name in BLOCKS.values():
        pattern = re.compile(
            r"<!-- BEGIN AUTO-GENERATED: " + re.escape(name) + r" -->.*?<!-- END AUTO-GENERATED: " + re.escape(name) + r" -->",
            re.DOTALL,
        )
        replacement = generated_block(name)
        html, count = pattern.subn(lambda _: replacement, html, count=1)
        if count != 1:
            raise SystemExit(f"Could not find exactly one generated block for {name}.")
    return html


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="exit non-zero if index.html is out of date")
    args = parser.parse_args()
    original = INDEX.read_text(encoding="utf-8")
    updated = rebuild(original)
    if args.check:
        if original == updated:
            print("index.html generated assets are up to date.")
            return 0
        print("index.html generated assets are out of date. Run: python3 tools/update-index-assets.py", file=sys.stderr)
        diff = difflib.unified_diff(original.splitlines(), updated.splitlines(), "index.html", "expected", lineterm="")
        for line in list(diff)[:80]:
            print(line, file=sys.stderr)
        return 1
    if original != updated:
        INDEX.write_text(updated, encoding="utf-8")
        print("Updated generated assets in index.html.")
    else:
        print("index.html is already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
