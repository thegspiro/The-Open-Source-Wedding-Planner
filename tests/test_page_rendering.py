"""Every wedding page renders, on an empty wedding and on a populated one.

This is the counterpart to test_authorization.py. That file walks app.url_map
and proves every wedding-scoped route *refuses the wrong user*; because the
access check runs before the handler, it never executes a single line of the
handler body. 295 of 334 handlers were reached only that far, so the suite
could be entirely green while a page raised a 500 for its owner.

Three did:

  * /ceremony raised NameError because WeddingElement was used in app.py but
    never imported there.
  * /vendors and /print/budget raised TypeError from `|sum(attribute=...,
    default=0)`; Jinja's sum filter has no `default` argument. Both sit behind
    an `{% if %}` guard, so they returned 200 until the wedding had a vendor
    or a budget line.
  * /calendar raised UndefinedError because the route formatted each date into
    a string and the template then called .strftime() on it.

So the walk runs twice. The empty pass catches the first kind, the populated
pass catches the other two, and the split is the point: a page that only works
before you use it is the failure mode the old fixtures could not see.

New routes are covered the moment they are registered.
"""

import pytest

from app import app as flask_app


def _renderable_rules():
    """Every GET route whose only variable is wedding_id.

    Routes taking a sub-resource id are excluded: a placeholder id would only
    prove the 404 path, which is not what this file is for.
    """
    rules = [
        rule for rule in flask_app.url_map.iter_rules()
        if rule.arguments == {"wedding_id"} and "GET" in rule.methods
    ]
    return sorted(rules, key=lambda r: r.rule)


RENDERABLE_RULES = _renderable_rules()

# A handful of pages stream a file rather than render HTML. They are still
# fetched — a 200 is a 200 — this set just documents why they look different.
BINARY_ENDPOINTS = {"calendar_export_ical"}


def _ids(rule):
    return rule.rule


def test_renderable_rules_were_found():
    """Guard against the walk silently matching nothing."""
    assert len(RENDERABLE_RULES) > 150, (
        f"expected the wedding UI to expose 150+ single-argument GET pages, "
        f"found {len(RENDERABLE_RULES)}"
    )


def _assert_renders(client, rule, wedding_id):
    url = rule.build({"wedding_id": wedding_id}, append_unknown=False)[1]
    response = client.get(url)
    assert response.status_code in (200, 302), (
        f"{url} returned {response.status_code}; "
        f"expected a page or a redirect"
    )


@pytest.mark.parametrize("rule", RENDERABLE_RULES, ids=_ids)
def test_page_renders_for_an_empty_wedding(auth_client, rule):
    """A brand new wedding has no children. Every page must still render."""
    client, seed = auth_client
    _assert_renders(client, rule, seed["wedding_id"])


@pytest.mark.parametrize("rule", RENDERABLE_RULES, ids=_ids)
def test_page_renders_for_a_populated_wedding(populated_client, rule):
    """The same pages, once the wedding actually has data in it."""
    client, populated = populated_client
    _assert_renders(client, rule, populated["wedding_id"])
