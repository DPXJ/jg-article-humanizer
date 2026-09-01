#!/usr/bin/env python3
"""Check formatting in flow, long-form, or strict humanized rewrites."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(\s*#{1,6})\s+", re.M)
LIST_RE = re.compile(r"^(\s*)([-+*]|\d+[.)])\s+")
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
HTML_TAG_RE = re.compile(r"<[^>]+>")
RESOURCE_ATTR_RE = re.compile(r"\b(?:src|href)\s*=\s*(['\"])(.*?)\1", re.I)
EMOJI_RE = re.compile(
    "["
    "\U0001F1E6-\U0001F1FF"
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "]"
)
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")


def line_kind(line: str) -> str:
    if line == "":
        return "blank"
    if line == "\u3000":
        return "fullwidth-gap"
    fence = FENCE_RE.match(line)
    if fence:
        return f"fence:{fence.group(1)[0]}:{len(fence.group(1))}:{fence.group(2).strip()}"
    heading = HEADING_RE.match(line)
    if heading:
        return f"heading:{heading.group(1).count('#')}"
    if re.fullmatch(r"\s*(?:---+|___+|\*\*\*+)\s*", line):
        return "rule"
    if re.match(r"^\s*>\s?", line):
        return "quote"
    item = LIST_RE.match(line)
    if item:
        marker = "ordered" if item.group(2)[0].isdigit() else item.group(2)
        return f"list:{len(item.group(1))}:{marker}"
    if re.fullmatch(r"\s*!\[[^\]]*\]\([^)]+\)\s*", line):
        return "image"
    if re.fullmatch(r"\s*(?:<[^>]+>\s*)+", line):
        return "html-only"
    return "prose"


def skeleton(text: str) -> list[str]:
    return [line_kind(line) for line in text.splitlines()]


def protected_values(text: str) -> dict[str, list[str]]:
    return {
        "images": IMAGE_RE.findall(text),
        "links": LINK_RE.findall(text),
        "html_tags": HTML_TAG_RE.findall(text),
        "resource_attrs": [match[1] for match in RESOURCE_ATTR_RE.findall(text)],
    }


def fence_signature(text: str) -> list[str]:
    signatures: list[str] = []
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if match:
            signatures.append(
                f"{match.group(1)[0]}:{len(match.group(1))}:{match.group(2).strip()}"
            )
    return signatures


def is_outer_fenced(text: str) -> bool:
    lines = text.splitlines()
    return (
        len(lines) >= 2
        and FENCE_RE.match(lines[0]) is not None
        and FENCE_RE.match(lines[-1]) is not None
        and len(fence_signature(text)) == 2
    )


def detect_mode(text: str) -> str:
    if is_outer_fenced(text) and "\u3000" in text:
        return "flow"
    if HEADING_RE.search(text) and len(CJK_RE.findall(text)) >= 1200:
        return "longform"
    return "strict"


def validate_protected(original: str, rewritten: str, errors: list[str]) -> None:
    before = protected_values(original)
    after = protected_values(rewritten)
    for key in before:
        if before[key] != after[key]:
            errors.append(f"protected {key} changed")


def validate_strict(original: str, rewritten: str, errors: list[str]) -> None:
    if skeleton(original) != skeleton(rewritten):
        errors.append("line/paragraph formatting skeleton changed")
    validate_protected(original, rewritten, errors)


def longform_nodes(text: str) -> list[str]:
    """Return protected block nodes while allowing ordinary prose reflow."""
    nodes: list[str] = []
    in_fence = False
    for line in text.splitlines():
        fence = FENCE_RE.match(line)
        if fence:
            in_fence = not in_fence
            nodes.append(f"fence:{line}")
            continue
        if in_fence:
            nodes.append(f"code:{line}")
            continue
        kind = line_kind(line)
        if kind.startswith("heading:"):
            nodes.append(f"{kind}:{line.strip()}")
        elif kind in {"image", "rule", "html-only"}:
            nodes.append(f"{kind}:{line.strip()}")
        elif kind == "quote":
            nodes.append(kind)
        elif kind.startswith("list:"):
            nodes.append(kind)
    return nodes


def validate_longform(original: str, rewritten: str, errors: list[str]) -> None:
    if longform_nodes(original) != longform_nodes(rewritten):
        errors.append("long-form protected headings/media/list structure changed")
    validate_protected(original, rewritten, errors)


def validate_flow(original: str, rewritten: str, errors: list[str]) -> None:
    if not is_outer_fenced(original):
        errors.append("flow mode requires an original outer fenced code block")
        return
    if not is_outer_fenced(rewritten):
        errors.append("rewritten flow output must contain one outer fenced code block only")
        return
    if fence_signature(original) != fence_signature(rewritten):
        errors.append("outer fence type or language marker changed")

    body = rewritten.splitlines()[1:-1]
    if any(line == "" for line in body):
        errors.append("ordinary blank lines are not allowed in flow output")
    if any(line.strip() == "" and line != "\u3000" for line in body):
        errors.append("paragraph gaps must contain one fullwidth space only")

    for line in body:
        if line == "\u3000":
            continue
        if HEADING_RE.match(line) or LIST_RE.match(line) or re.match(r"^\s*>\s?", line):
            errors.append("Markdown heading, list, or quote added in flow output")
            break
        if any(token in line for token in ("**", "__", "==", "![")):
            errors.append("Markdown rich-text syntax added in flow output")
            break
    if EMOJI_RE.search("\n".join(body)):
        errors.append("Emoji added in flow output")

    validate_protected(original, rewritten, errors)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify formatting in flow, long-form, or strict rewrites."
    )
    parser.add_argument("original", type=Path)
    parser.add_argument("rewritten", type=Path)
    parser.add_argument(
        "--mode",
        choices=("auto", "flow", "longform", "strict"),
        default="auto",
        help="auto detects fullwidth-gap flow content or 1200+ CJK Markdown long-form content",
    )
    args = parser.parse_args()

    original = args.original.read_text(encoding="utf-8")
    rewritten = args.rewritten.read_text(encoding="utf-8")
    errors: list[str] = []

    mode = detect_mode(original) if args.mode == "auto" else args.mode
    if mode == "flow":
        validate_flow(original, rewritten, errors)
    elif mode == "longform":
        validate_longform(original, rewritten, errors)
    else:
        validate_strict(original, rewritten, errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(f"OK: {mode} formatting checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
