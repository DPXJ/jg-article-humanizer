#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "verify_format_preservation.py"
SPEC = importlib.util.spec_from_file_location("verify_format_preservation", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LongformValidationTests(unittest.TestCase):
    def test_longform_allows_prose_reflow(self) -> None:
        original = "# 标题\n\n第一段很长。\n\n![图](a.png)\n\n## 章节\n\n第二段。\n"
        rewritten = "# 标题\n\n第一段。\n\n补一段自然过渡。\n\n![图](a.png)\n\n## 章节\n\n第二段。\n"
        errors: list[str] = []
        MODULE.validate_longform(original, rewritten, errors)
        self.assertEqual(errors, [])

    def test_longform_rejects_media_reordering(self) -> None:
        original = "# 标题\n\n第一段。\n\n![图](a.png)\n\n## 章节\n\n第二段。\n"
        rewritten = "# 标题\n\n第一段。\n\n## 章节\n\n![图](a.png)\n\n第二段。\n"
        errors: list[str] = []
        MODULE.validate_longform(original, rewritten, errors)
        self.assertTrue(errors)

    def test_auto_detects_longform(self) -> None:
        article = "# 标题\n\n" + "文" * 1200
        self.assertEqual(MODULE.detect_mode(article), "longform")


if __name__ == "__main__":
    unittest.main()
