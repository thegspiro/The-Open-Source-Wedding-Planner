"""Create, edit and delete for the modules people touch every day.

188 of the 334 handlers accept POST and none of their bodies had ever run. The
suite proved strangers could not reach them; nothing proved they did the right
thing for the person who could. These drive the four highest-traffic modules
through their forms and assert the database afterwards, with the
validation-failure case alongside each happy path.

TestUnscopedRoutesAreScoped is the important one. test_authorization.py derives
its cases from routes that carry a wedding_id, so a route without one is
invisible to it -- and task_toggle was exactly that: login_required and nothing
else, letting any signed-in user flip any task in anyone's wedding.
"""

import pytest
from datetime import datetime, timedelta

from app import app as flask_app
from models import db, Guest, Task, Vendor, Budget, BudgetExpense


def flash_text(response):
    return response.get_data(as_text=True)


class TestGuests:
    def test_adding_a_guest_stores_the_fields(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        response = client.post(f"/wedding/{wid}/guests/add", data={
            "name": "New Guest",
            "email": "new@example.com",
            "phone": "555-0100",
            "guest_type": "friend",
            "side": "partner1",
            "dietary_restrictions": "no shellfish",
            "household_group": "New Household",
        }, follow_redirects=True)
        assert response.status_code == 200

        with app.app_context():
            guest = Guest.query.filter_by(wedding_id=wid, name="New Guest").one()
            assert guest.email == "new@example.com"
            assert guest.dietary_restrictions == "no shellfish"
            assert guest.household_group == "New Household"

    def test_a_new_guest_gets_a_checkin_token(self, app, populated_client):
        """The token is what the guest's personal link is built from."""
        client, populated = populated_client
        wid = populated["wedding_id"]
        client.post(f"/wedding/{wid}/guests/add", data={"name": "Token Guest"})

        with app.app_context():
            guest = Guest.query.filter_by(wedding_id=wid, name="Token Guest").one()
            assert guest.guest_token, "guest has no check-in token"

    def test_tokens_are_not_shared_between_guests(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        client.post(f"/wedding/{wid}/guests/add", data={"name": "Guest A"})
        client.post(f"/wedding/{wid}/guests/add", data={"name": "Guest B"})

        with app.app_context():
            tokens = [g.guest_token for g in Guest.query.filter_by(wedding_id=wid).all()
                      if g.guest_token]
            assert len(tokens) == len(set(tokens)), "two guests share a token"

    def test_editing_a_guest_updates_the_row(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        guest_id = populated["guest_ids"][0]

        client.post(f"/wedding/{wid}/guests/{guest_id}/edit", data={
            "name": "Renamed Guest",
            "rsvp_status": "declined",
            "meal_choice": "vegetarian",
            "invitation_sent": "on",
        })

        with app.app_context():
            guest = Guest.query.get(guest_id)
            assert guest.name == "Renamed Guest"
            assert guest.rsvp_status == "declined"
            assert guest.invitation_sent is True

    def test_an_unchecked_box_clears_the_flag(self, app, populated_client):
        """Checkboxes are absent from the form when off, not sent as false."""
        client, populated = populated_client
        wid = populated["wedding_id"]
        guest_id = populated["guest_ids"][0]

        client.post(f"/wedding/{wid}/guests/{guest_id}/edit",
                    data={"name": "Guest", "invitation_sent": "on"})
        client.post(f"/wedding/{wid}/guests/{guest_id}/edit",
                    data={"name": "Guest"})

        with app.app_context():
            assert Guest.query.get(guest_id).invitation_sent is False

    def test_deleting_a_guest_removes_them(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        guest_id = populated["guest_ids"][5]

        client.post(f"/wedding/{wid}/guests/{guest_id}/delete")

        with app.app_context():
            assert Guest.query.get(guest_id) is None

    def test_a_guest_from_another_wedding_is_not_found(self, app, populated_client,
                                                      two_tenants):
        """The id exists, but not in this wedding: 404, not a silent edit."""
        client, populated = populated_client
        with app.app_context():
            stranger = Guest(wedding_id=two_tenants["victim_wedding_id"],
                             name="Someone Else")
            db.session.add(stranger)
            db.session.commit()
            stranger_id = stranger.id

        response = client.post(
            f"/wedding/{populated['wedding_id']}/guests/{stranger_id}/delete")
        assert response.status_code == 404

        with app.app_context():
            assert Guest.query.get(stranger_id) is not None


class TestTasks:
    def test_adding_a_task_stores_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        client.post(f"/wedding/{wid}/tasks/add", data={
            "title": "Order the cake",
            "description": "Vanilla, three tiers",
            "due_date": "2026-05-01",
            "priority": "high",
            "category": "catering",
        })

        with app.app_context():
            task = Task.query.filter_by(wedding_id=wid, title="Order the cake").one()
            assert task.priority == "high"
            assert task.due_date.date() == datetime(2026, 5, 1).date()

    def test_a_task_with_no_due_date_still_saves(self, app, populated_client):
        """due_date is NOT NULL; the handler falls back to today."""
        client, populated = populated_client
        wid = populated["wedding_id"]

        client.post(f"/wedding/{wid}/tasks/add", data={"title": "Undated task"})

        with app.app_context():
            task = Task.query.filter_by(wedding_id=wid, title="Undated task").one()
            assert task.due_date is not None

    def test_an_unparseable_due_date_does_not_500(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        response = client.post(f"/wedding/{wid}/tasks/add",
                               data={"title": "Bad date", "due_date": "not-a-date"})
        assert response.status_code in (200, 302)

        with app.app_context():
            task = Task.query.filter_by(wedding_id=wid, title="Bad date").one()
            assert task.due_date is not None

    def test_editing_a_task_updates_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        with app.app_context():
            task_id = Task.query.filter_by(wedding_id=wid,
                                           title="Book the DJ").one().id

        client.post(f"/wedding/{wid}/tasks/{task_id}/edit", data={
            "title": "Book the band instead",
            "priority": "low",
        })

        with app.app_context():
            task = Task.query.get(task_id)
            assert task.title == "Book the band instead"
            assert task.priority == "low"

    def test_toggling_flips_completion_both_ways(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        with app.app_context():
            task = Task.query.filter_by(wedding_id=wid, title="Book the DJ").one()
            task_id, before = task.id, task.completed

        client.post(f"/wedding/{wid}/tasks/{task_id}/toggle")
        with app.app_context():
            assert Task.query.get(task_id).completed is not before

        client.post(f"/wedding/{wid}/tasks/{task_id}/toggle")
        with app.app_context():
            assert Task.query.get(task_id).completed is before

    def test_deleting_a_task_removes_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        with app.app_context():
            task_id = Task.query.filter_by(wedding_id=wid,
                                           title="Book the DJ").one().id

        client.post(f"/wedding/{wid}/tasks/{task_id}/delete")

        with app.app_context():
            assert Task.query.get(task_id) is None


class TestUnscopedRoutesAreScoped:
    """A route without a wedding_id sits outside the structural access walk.

    task_toggle lived at /task/<task_id>/toggle with only login_required, so
    enforce_wedding_access -- which keys off wedding_id in the URL -- returned
    early and never ran. Any signed-in user could flip any task in anyone's
    wedding. It now carries wedding_id like every other write.
    """

    def test_no_login_only_route_takes_a_bare_object_id(self):
        """Structural guard: catch the next one when it is added."""
        import ast

        source = open("app.py").read()
        decorators = {}
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.FunctionDef):
                names = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        names.append(dec.id)
                    elif isinstance(dec, ast.Call):
                        func = dec.func
                        names.append(getattr(func, "id", getattr(func, "attr", "")))
                    elif isinstance(dec, ast.Attribute):
                        names.append(dec.attr)
                decorators[node.name] = names

        # Routes authenticated by an unguessable token in the URL instead of by
        # a wedding-scoped session.
        TOKEN_AUTHENTICATED = {
            "rsvp_portal", "rsvp_submit", "shared_view", "guest_identify",
            "guest_checkin", "guest_checkin_lookup",
        }

        offenders = []
        for rule in flask_app.url_map.iter_rules():
            if "wedding_id" in rule.arguments or not rule.arguments:
                continue
            if rule.endpoint in TOKEN_AUTHENTICATED:
                continue
            if "login_required" in decorators.get(rule.endpoint, []):
                offenders.append(f"{rule.endpoint} ({rule.rule})")

        assert not offenders, (
            "these routes take an object id but no wedding_id, so "
            "enforce_wedding_access() never runs for them and login_required is "
            "the only barrier -- any signed-in user can act on anyone's data: "
            + ", ".join(sorted(offenders))
        )

    def test_an_outsider_cannot_toggle_someone_elses_task(self, app,
                                                         outsider_client):
        client, tenants = outsider_client
        with app.app_context():
            task = Task(wedding_id=tenants["victim_wedding_id"],
                        title="Victim's task",
                        due_date=datetime.utcnow() + timedelta(days=5),
                        completed=False)
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.post(
            f"/wedding/{tenants['victim_wedding_id']}/tasks/{task_id}/toggle")
        assert response.status_code == 403

        with app.app_context():
            assert Task.query.get(task_id).completed is False

    def test_a_task_id_from_another_wedding_is_not_found(self, app,
                                                        populated_client,
                                                        two_tenants):
        """Even with a wedding you own in the URL, the task must be yours."""
        client, populated = populated_client
        with app.app_context():
            task = Task(wedding_id=two_tenants["victim_wedding_id"],
                        title="Not yours",
                        due_date=datetime.utcnow() + timedelta(days=5),
                        completed=False)
            db.session.add(task)
            db.session.commit()
            task_id = task.id

        response = client.post(
            f"/wedding/{populated['wedding_id']}/tasks/{task_id}/toggle")
        assert response.status_code == 404

        with app.app_context():
            assert Task.query.get(task_id).completed is False


class TestBudget:
    def test_adding_an_expense_stores_the_amounts(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        client.post(f"/wedding/{wid}/budget/expense/add", data={
            "category": "Music",
            "item_name": "String quartet",
            "estimated_cost": "1200.50",
            "actual_cost": "1150",
            "paid_amount": "300",
            "payment_due_date": "2026-04-01",
            "payment_status": "partial",
        })

        with app.app_context():
            expense = BudgetExpense.query.filter_by(item_name="String quartet").one()
            assert expense.estimated_cost == 1200.50
            assert expense.actual_cost == 1150.0
            assert expense.paid_amount == 300.0
            assert expense.payment_due_date == datetime(2026, 4, 1).date()

    def test_an_expense_with_no_amounts_is_accepted(self, app, populated_client):
        """A line item is often added before anyone knows the price."""
        client, populated = populated_client
        wid = populated["wedding_id"]

        response = client.post(f"/wedding/{wid}/budget/expense/add", data={
            "category": "Unknown", "item_name": "To be priced",
        })
        assert response.status_code in (200, 302)

        with app.app_context():
            expense = BudgetExpense.query.filter_by(item_name="To be priced").one()
            assert expense.estimated_cost is None
            assert expense.paid_amount == 0

    def test_the_first_expense_creates_a_budget(self, app, seed_data, client):
        """A wedding with no budget row yet must not 500 on its first expense."""
        with client.session_transaction() as sess:
            sess["user_id"] = seed_data["user_id"]
        wid = seed_data["wedding_id"]

        with app.app_context():
            assert Budget.query.filter_by(wedding_id=wid).first() is None

        response = client.post(f"/wedding/{wid}/budget/expense/add", data={
            "category": "Venue", "item_name": "Deposit",
            "estimated_cost": "500",
        })
        assert response.status_code in (200, 302)

        with app.app_context():
            budget = Budget.query.filter_by(wedding_id=wid).one()
            assert BudgetExpense.query.filter_by(budget_id=budget.id).count() == 1

    def test_editing_an_expense_updates_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        with app.app_context():
            expense_id = BudgetExpense.query.filter_by(item_name="Barn hire").one().id

        client.post(f"/wedding/{wid}/budget/expense/{expense_id}/edit", data={
            "category": "Venue", "item_name": "Barn hire",
            "estimated_cost": "9000", "actual_cost": "9500",
            "paid_amount": "9500", "payment_status": "paid",
        })

        with app.app_context():
            expense = BudgetExpense.query.get(expense_id)
            assert expense.actual_cost == 9500.0
            assert expense.payment_status == "paid"

    def test_deleting_an_expense_removes_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]
        with app.app_context():
            expense_id = BudgetExpense.query.filter_by(item_name="Barn hire").one().id

        client.post(f"/wedding/{wid}/budget/expense/{expense_id}/delete")

        with app.app_context():
            assert BudgetExpense.query.get(expense_id) is None


class TestVendors:
    def test_adding_a_vendor_stores_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        client.post(f"/wedding/{wid}/vendors/add", data={
            "category": "Photographer",
            "business_name": "Bright Light Photo",
            "contact_name": "Robin Vale",
            "email": "robin@example.com",
            "total_cost": "3400",
            "deposit_amount": "800",
        })

        with app.app_context():
            vendor = Vendor.query.filter_by(
                wedding_id=wid, business_name="Bright Light Photo").one()
            assert vendor.category == "Photographer"
            assert vendor.total_cost == 3400.0

    def test_deleting_a_vendor_removes_it(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        client.post(f"/wedding/{wid}/vendors/{populated['vendor_id']}/delete")

        with app.app_context():
            assert Vendor.query.get(populated["vendor_id"]) is None

    def test_the_vendors_page_still_renders_after_a_write(self, app,
                                                         populated_client):
        """The totals row on this page is what broke before; keep it exercised
        against a list that has just changed."""
        client, populated = populated_client
        wid = populated["wedding_id"]
        client.post(f"/wedding/{wid}/vendors/add", data={
            "category": "Baker", "business_name": "Second Vendor",
            "total_cost": "",
        })
        response = client.get(f"/wedding/{wid}/vendors")
        assert response.status_code == 200
        assert "Second Vendor" in flash_text(response)


class TestViewersCannotWrite:
    """Role enforcement on the routes this file exercises."""

    @pytest.fixture
    def viewer_client(self, client, roles):
        with client.session_transaction() as sess:
            sess["user_id"] = roles["viewer_id"]
        return client, roles

    @pytest.mark.parametrize("path,data", [
        ("guests/add", {"name": "Sneaky"}),
        ("tasks/add", {"title": "Sneaky task"}),
        ("budget/expense/add", {"category": "X", "item_name": "Sneaky"}),
        ("vendors/add", {"category": "X", "business_name": "Sneaky"}),
    ])
    def test_a_viewer_is_refused(self, viewer_client, path, data):
        client, roles = viewer_client
        response = client.post(f"/wedding/{roles['wedding_id']}/{path}", data=data)
        assert response.status_code == 403
