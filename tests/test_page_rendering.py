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
from models import Budget, BudgetExpense, db


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


@pytest.mark.parametrize(
    ("category", "message", "accessibility_attributes"),
    [
        ("success", "Wedding saved successfully.",
         'role="status" aria-live="polite"'),
        ("error", "Wedding could not be saved.", 'role="alert"'),
    ],
)
def test_flash_messages_have_category_appropriate_live_regions(
        client, category, message, accessibility_attributes):
    """Routine feedback is polite while failures interrupt immediately."""
    with client.session_transaction() as session:
        session["_flashes"] = [(category, message)]

    page = client.get("/login").get_data(as_text=True)

    assert (
        f'class="alert alert-{category}" {accessibility_attributes}' in page
    )
    assert message in page


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


@pytest.mark.parametrize(
    ("total_budget", "spent", "expected_width", "expected_raw_percentage"),
    [
        pytest.param(1000, 500, "50.0%", "50.0", id="partially-spent"),
        pytest.param(1000, 1000, "100.0%", "100.0", id="exactly-spent"),
        pytest.param(1000, 1500, "100%", "150.0", id="over-budget"),
    ],
)
def test_dashboard_budget_progress_is_clamped(
        auth_client, app, total_budget, spent, expected_width,
        expected_raw_percentage):
    """The raw percentage remains accurate while the visual never exceeds 100%."""
    client, seed = auth_client
    with app.app_context():
        budget = Budget(wedding_id=seed["wedding_id"], total_budget=total_budget)
        db.session.add(budget)
        db.session.flush()
        db.session.add(BudgetExpense(
            budget_id=budget.id,
            category="venue",
            item_name="Venue",
            paid_amount=spent,
        ))
        db.session.commit()

    html = client.get(f'/wedding/{seed["wedding_id"]}').get_data(as_text=True)

    assert f'aria-valuenow="{expected_raw_percentage}"' in html
    assert f'style="width: {expected_width}"' in html
    if spent > total_budget:
        assert 'class="progress-fill progress-fill-danger"' in html
        assert 'class="budget-over-state"' in html
        assert "Over budget by $500" in html
        assert "50.0% over" in html
    else:
        assert "budget-over-state" not in html
        assert "progress-fill-danger" not in html


def test_dashboard_handles_a_zero_budget(auth_client, app):
    """A zero budget avoids division and does not claim an over-budget state."""
    client, seed = auth_client
    with app.app_context():
        db.session.add(Budget(wedding_id=seed["wedding_id"], total_budget=0))
        db.session.commit()

    response = client.get(f'/wedding/{seed["wedding_id"]}')
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'aria-label="Budget spent"' not in html
    assert "budget-over-state" not in html
