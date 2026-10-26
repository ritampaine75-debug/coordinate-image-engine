#!/usr/bin/env python3
"""Check internal anchors and relative file links in all Markdown files.

Uses only the Python standard library, so it runs on Termux and in CI with no
extra packages. GitHub generates heading anchors from the rendered heading
text, which is why numbered headings such as "## 1. The problem" produce
"#1-the-problem" rather than "#the-problem".

Usage:
    python3 tests/check_markdown_links.py
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FENCE_RE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$", re.MULTILINE)
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
REF_DEF_RE = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)


def github_slug(heading: str) -> str:
    """Approximate GitHub's heading anchor algorithm."""
    text = heading.strip()
    text = re.sub(r"`([^`]*)`", r"\1", text)          # inline code keeps its text
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)   # images inline
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)  # links keep their label
    text = re.sub(r"<[^>]+>", "", text)                # inline HTML tags
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] not in ("M", "P") or ch in "-_")
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s", "-", text)
    return text


def heading_anchors(text: str) -> set[str]:
    body = FENCE_RE.sub("", text)
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    for match in HEADING_RE.finditer(body):
        base = github_slug(match.group(2))
        if base in seen:
            seen[base] += 1
            anchors.add(f"{base}-{seen[base]}")
        else:
            seen[base] = 0
            anchors.add(base)
        anchors.add(base)
    return anchors


def strip_fences(text: str) -> str:
    return FENCE_RE.sub("", text)


def check_file(path: Path, cache: dict[Path, set[str]]) -> list[str]:
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []
    body = strip_fences(text)
    links = LINK_RE.findall(body) + REF_DEF_RE.findall(body)

    for raw in links:
        link = raw.strip().strip("<>")
        if not link or link.startswith(("http://", "https://", "mailto:", "data:", "tel:")):
            continue

        target, _, anchor = link.partition("#")

        if not target:
            if anchor not in heading_anchors(text):
                problems.append(f"{path.relative_to(ROOT)}: dead anchor #{anchor}")
            continue

        resolved = (path.parent / target).resolve()
        if not resolved.exists():
            # README-style links may be written from the repository root.
            alt = (ROOT / target.lstrip("./")).resolve()
            if alt.exists():
                resolved = alt
            else:
                problems.append(f"{path.relative_to(ROOT)}: missing file {target}")
                continue

        if anchor and resolved.suffix.lower() == ".md":
            if resolved not in cache:
                cache[resolved] = heading_anchors(resolved.read_text(encoding="utf-8"))
            if anchor not in cache[resolved]:
                problems.append(f"{path.relative_to(ROOT)}: dead cross-file anchor {link}")

    return problems


def main() -> int:
    files = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts)
    if not files:
        print("No Markdown files found.", file=sys.stderr)
        return 1
    cache: dict[Path, set[str]] = {}
    problems: list[str] = []
    for path in files:
        problems.extend(check_file(path, cache))

    if problems:
        print(f"Markdown link check failed with {len(problems)} problem(s):", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1

    print(f"Markdown links OK: {len(files)} files, all anchors and relative paths resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
