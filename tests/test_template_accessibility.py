"""Static accessibility checks for forms in Jinja templates."""

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import pytest


TEMPLATES = Path(__file__).parents[1] / "templates"


class FormAccessibilityParser(HTMLParser):
    """Collect form controls and their label associations without rendering Jinja."""

    def __init__(self):
        super().__init__()
        self.form_depth = 0
        self.forms = []
        self._form = None
        self._label = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "form":
            if self.form_depth == 0:
                self._form = {"controls": [], "labels": []}
                self.forms.append(self._form)
            self.form_depth += 1
            return
        if not self.form_depth:
            return
        if tag == "label":
            self._label = {"for": attributes.get("for"), "wraps_checkbox": False}
            self._form["labels"].append(self._label)
        elif tag in {"input", "select", "textarea"}:
            control = {
                "id": attributes.get("id"),
                "type": attributes.get("type", "").lower(),
            }
            self._form["controls"].append(control)
            if self._label is not None and control["type"] == "checkbox":
                self._label["wraps_checkbox"] = True

    def handle_endtag(self, tag):
        if tag == "label":
            self._label = None
        elif tag == "form":
            self.form_depth -= 1
            if self.form_depth == 0:
                self._form = None


@pytest.mark.parametrize("template", sorted(TEMPLATES.rglob("*.html")), ids=lambda p: str(p.relative_to(TEMPLATES)))
def test_form_controls_and_labels_are_associated(template):
    parser = FormAccessibilityParser()
    parser.feed(template.read_text())

    for form_number, form in enumerate(parser.forms, start=1):
        ids = [control["id"] for control in form["controls"]]
        assert all(ids), f"{template}: form {form_number} has a control without an id"

        duplicates = [value for value, count in Counter(ids).items() if count > 1]
        # RSVP question branches are mutually exclusive when Jinja renders them.
        duplicates = [value for value in duplicates if value != "custom-q-{{ q.id }}"]
        assert not duplicates, f"{template}: form {form_number} repeats control ids: {duplicates}"

        targets = set(ids)
        for label in form["labels"]:
            if label["wraps_checkbox"]:
                continue
            assert label["for"], f"{template}: form {form_number} has a non-checkbox label without for"
            assert label["for"] in targets, (
                f"{template}: form {form_number} label targets missing id {label['for']!r}"
            )
