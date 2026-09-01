#!/usr/bin/env python3
"""Lint a Chinese humanized article for recurring style regressions."""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
HEADING_RE = re.compile(r"^#{1,6}\s+")
IMAGE_RE = re.compile(r"^\s*!\[[^]]*]\([^)]+\)\s*$")
HTML_ONLY_RE = re.compile(r"^\s*(?:<[^>]+>\s*)+$")
STARTERS = (
    "说实话",
    "其实",
    "当然",
    "你看",
    "大家都知道",
    "这里就不得不提",
    "不管怎么说",
)
DISCOURAGED = {
    "跑通": "优先改为测试成功、完成验证或拿到结果",
    "拿任务去跑": "优先改为拿真实任务测试",
    "拉通": "说明具体连接了哪些步骤",
    "形成闭环": "说明具体交付结果",
}
ABRUPT_OPENERS = (
    "把这",
    "综上",
    "总体来看",
    "整体来看",
    "总结一下",
)
EDGE_PATTERNS = (
    re.compile(r"我我|这个这个|就就|再再|其实其实|然后然后|所以所以"),
    re.compile(r"以经|时侯|觉的"),
)


def visible_paragraphs(text: str) -> list[tuple[int, str]]:
    paragraphs: list[tuple[int, str]] = []
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if (
            not line
            or HEADING_RE.match(line)
            or IMAGE_RE.match(line)
            or HTML_ONLY_RE.match(line)
            or line.startswith((">", "<!--", "```", "~~~"))
        ):
            continue
        paragraphs.append((lineno, re.sub(r"<[^>]+>", "", line)))
    return paragraphs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("article", type=Path)
    args = parser.parse_args()
    text = args.article.read_text(encoding="utf-8")
    paragraphs = visible_paragraphs(text)
    warnings: list[str] = []

    for lineno, paragraph in paragraphs:
        cjk_len = len(CJK_RE.findall(paragraph))
        if cjk_len > 180:
            warnings.append(f"line {lineno}: paragraph has {cjk_len} CJK characters")
        for term, suggestion in DISCOURAGED.items():
            if term in paragraph:
                warnings.append(f"line {lineno}: discouraged term '{term}'; {suggestion}")

    starts = []
    for lineno, paragraph in paragraphs:
        starter = next((item for item in STARTERS if paragraph.startswith(item)), None)
        if starter:
            starts.append((lineno, starter))
    counts = Counter(item for _, item in starts)
    for starter, count in counts.items():
        if count >= 3:
            warnings.append(f"repeated paragraph starter '{starter}' appears {count} times")

    lines = text.splitlines()
    for index, line in enumerate(lines):
        if not HEADING_RE.match(line):
            continue
        for following in lines[index + 1 :]:
            candidate = following.strip()
            if not candidate or IMAGE_RE.match(candidate):
                continue
            if candidate.startswith(ABRUPT_OPENERS):
                warnings.append(
                    f"line {index + 1}: heading may enter a summary too abruptly: '{candidate[:18]}'"
                )
            break

    recognizable_edges = sum(
        len(pattern.findall("\n".join(paragraph for _, paragraph in paragraphs)))
        for pattern in EDGE_PATTERNS
    )
    if recognizable_edges != 3:
        warnings.append(
            "recognizable intentional edges: "
            f"{recognizable_edges}; manually verify the required exact total of 3"
        )

    if warnings:
        for warning in warnings:
            print(f"WARN: {warning}")
        return 0

    print("OK: no humanizer style warnings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
