import importlib.util
from pathlib import Path
import unittest


SCRIPT = Path(__file__).parents[1] / "scripts" / "lint_humanized_article.py"
SPEC = importlib.util.spec_from_file_location("lint_humanized_article", SCRIPT)
LINT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(LINT)


class HumanEdgeTests(unittest.TestCase):
    def test_recognizes_confirmed_author_edges(self):
        text = (
            "众所周知，Codex 一致是我的最佳 CP。\n"
            "跟随 AI的变化而变化。\n"
            "这个这个判断我还想再看看。"
        )
        hits = [
            (edge_type, match.group(0))
            for edge_type, pattern in LINT.EDGE_PATTERNS.items()
            for match in pattern.finditer(text)
        ]

        self.assertEqual(3, len(hits))
        self.assertEqual(3, len({edge_type for edge_type, _ in hits}))

    def test_ignores_edges_inside_fenced_code(self):
        text = "普通段落。\n\n```text\nAI的\n这个这个\n```\n\n结尾段落。"

        self.assertEqual([(1, "普通段落。"), (8, "结尾段落。")], LINT.visible_paragraphs(text))


if __name__ == "__main__":
    unittest.main()
