"""Regression checks for plain-text grade comments in both HTML templates."""
from html import unescape
from pathlib import Path
import unittest

from jinja2 import Environment, FileSystemLoader, select_autoescape


class CommentRenderingTests(unittest.TestCase):
    def setUp(self):
        self.templates = Environment(
            loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
            autoescape=select_autoescape(),
        )
        self.templates.globals["url_for"] = lambda endpoint, **values: "/" + endpoint

    def check_comment(self, comment, escaped):
        for template_name in ("dashboard.html", "teacher.html"):
            with self.subTest(template=template_name):
                page = self.templates.get_template(template_name).render(
                    notes=[{
                        "id": 1, "class_name": "Mathematics", "grade": 16.2,
                        "student": "alice", "comment": comment,
                    }],
                    classes=[], students=[], session={}, token=None,
                )
                self.assertIn(f"<td>{escaped}</td>", page)
                self.assertNotIn(f"<td>{comment}</td>", page)
                self.assertEqual(unescape(escaped), comment)

    def test_html_markup_is_rendered_as_text(self):
        self.check_comment("<em>Review</em>", "&lt;em&gt;Review&lt;/em&gt;")

    def test_ordinary_feedback_preserves_special_characters(self):
        self.check_comment(
            "Score < 10 on parts 1 & 2, aim for > 10 next time.",
            "Score &lt; 10 on parts 1 &amp; 2, aim for &gt; 10 next time.",
        )
