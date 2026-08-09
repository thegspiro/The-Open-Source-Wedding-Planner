"""Tenant isolation and role enforcement.

The tests here are deliberately structural rather than per-feature. Access
control used to be applied by hand in each route handler, and it was missing
from 63 of them; a test that names individual routes would have had the same
blind spot. Instead these walk app.url_map, so a new route with a wedding_id is
covered the moment it is registered.
"""

import pytest

from app import app as flask_app, OWNER_ONLY_ENDPOINTS, required_wedding_role
from models import db, Wedding, Guest, InventoryItem, Comment, WeddingAccess


# ---------------------------------------------------------------------------
# Route enumeration
# ---------------------------------------------------------------------------

def _wedding_rules():
    """Every URL rule that carries a wedding_id, with a concrete method."""
    out = []
    for rule in flask_app.url_map.iter_rules():
        if 'wedding_id' not in rule.arguments:
            continue
        methods = rule.methods - {'HEAD', 'OPTIONS'}
        for method in sorted(methods):
            out.append((rule, method))
    return out


WEDDING_RULES = _wedding_rules()

# Placeholder values for path params other than wedding_id. The access check
# runs before the handler, so these are never dereferenced on a refused request.
# Keyed by werkzeug converter class name.
_PLACEHOLDERS = {
    'IntegerConverter': 999999,
    'FloatConverter': 1.0,
    'UUIDConverter': '00000000-0000-0000-0000-000000000000',
}


def _placeholder_for(converter):
    """A value that satisfies a path converter without naming a real record."""
    name = type(converter).__name__
    if name in _PLACEHOLDERS:
        return _PLACEHOLDERS[name]
    # AnyConverter only accepts one of its declared options
    items = getattr(converter, 'items', None)
    if items:
        return sorted(items)[0]
    return 'placeholder'


def _build_url(rule, wedding_id):
    values = {}
    for arg in rule.arguments:
        if arg == 'wedding_id':
            values[arg] = wedding_id
        else:
            values[arg] = _placeholder_for(rule._converters.get(arg))
    return rule.build(values, append_unknown=False)[1]


def _ids(param):
    rule, method = param
    return f"{method} {rule.rule}"





# ---------------------------------------------------------------------------
# Sanity: the enumeration itself
# ---------------------------------------------------------------------------

def test_wedding_rules_were_found():
    """Guard against the walk silently matching nothing."""
    assert len(WEDDING_RULES) > 250, (
        f"Only found {len(WEDDING_RULES)} wedding-scoped rules; the url_map "
        "walk is probably broken and every test below is vacuous."
    )


def test_owner_only_endpoints_all_exist():
    """A typo in OWNER_ONLY_ENDPOINTS would silently downgrade a route."""
    registered = {r.endpoint for r in flask_app.url_map.iter_rules()}
    unknown = OWNER_ONLY_ENDPOINTS - registered
    assert not unknown, f"OWNER_ONLY_ENDPOINTS names routes that don't exist: {unknown}"


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rule_method", WEDDING_RULES, ids=_ids)
def test_outsider_is_refused_on_every_wedding_route(outsider_client, rule_method):
    """A logged-in user with no WeddingAccess row must be refused, always.

    This is the regression test for the 63 routes that checked only that a
    child entity belonged to the wedding, never that the caller did.
    """
    rule, method = rule_method
    client, tenants = outsider_client
    url = _build_url(rule, tenants['victim_wedding_id'])

    resp = client.open(url, method=method)

    assert resp.status_code == 403, (
        f"{method} {url} returned {resp.status_code} for a user with no access "
        f"to wedding {tenants['victim_wedding_id']} (expected 403)"
    )


def test_anonymous_is_refused_on_wedding_routes(client, two_tenants):
    """No session at all should never reach a wedding route."""
    url = f"/wedding/{two_tenants['victim_wedding_id']}/guests"
    resp = client.get(url, follow_redirects=False)
    assert resp.status_code in (302, 401)
    if resp.status_code == 302:
        assert '/login' in resp.headers.get('Location', '')


def test_owner_still_reaches_their_own_wedding(client, two_tenants):
    """The check must not be so strict that legitimate access breaks."""
    with client.session_transaction() as sess:
        sess['user_id'] = two_tenants['victim_id']
    resp = client.get(f"/wedding/{two_tenants['victim_wedding_id']}")
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Concrete exploits from the review — these each previously succeeded
# ---------------------------------------------------------------------------

class TestKnownExploits:

    def test_cannot_delete_another_weddings_guest(self, app, outsider_client):
        client, tenants = outsider_client
        with app.app_context():
            guest = Guest(wedding_id=tenants['victim_wedding_id'], name='Secret Guest')
            db.session.add(guest)
            db.session.commit()
            guest_id = guest.id

        resp = client.post(
            f"/wedding/{tenants['victim_wedding_id']}/guests/{guest_id}/delete"
        )
        assert resp.status_code == 403

        with app.app_context():
            assert db.session.get(Guest, guest_id) is not None

    def test_cannot_read_another_weddings_inventory(self, app, outsider_client):
        client, tenants = outsider_client
        with app.app_context():
            db.session.add(InventoryItem(
                wedding_id=tenants['victim_wedding_id'],
                name='Victim Heirloom Ring', quantity=1,
            ))
            db.session.commit()

        resp = client.get(f"/wedding/{tenants['victim_wedding_id']}/inventory")
        assert resp.status_code == 403
        assert b'Victim Heirloom Ring' not in resp.data

    def test_cannot_export_another_weddings_inventory(self, app, outsider_client):
        client, tenants = outsider_client
        with app.app_context():
            db.session.add(InventoryItem(
                wedding_id=tenants['victim_wedding_id'],
                name='Victim Heirloom Ring', quantity=1,
            ))
            db.session.commit()

        resp = client.get(f"/wedding/{tenants['victim_wedding_id']}/inventory/export")
        assert resp.status_code == 403
        assert b'Victim Heirloom Ring' not in resp.data

    def test_cannot_inject_comment_into_another_wedding(self, app, outsider_client):
        client, tenants = outsider_client
        resp = client.post(
            f"/wedding/{tenants['victim_wedding_id']}/comment/add",
            data={'entity_type': 'task', 'entity_id': '1', 'content': 'INJECTED'},
        )
        assert resp.status_code == 403
        with app.app_context():
            count = Comment.query.filter_by(
                wedding_id=tenants['victim_wedding_id']
            ).count()
            assert count == 0


# ---------------------------------------------------------------------------
# Role enforcement
# ---------------------------------------------------------------------------

class TestRoleEnforcement:

    def test_viewer_can_read(self, client, roles):
        with client.session_transaction() as sess:
            sess['user_id'] = roles['viewer_id']
        resp = client.get(f"/wedding/{roles['wedding_id']}")
        assert resp.status_code == 200

    def test_viewer_cannot_write(self, app, client, roles):
        with client.session_transaction() as sess:
            sess['user_id'] = roles['viewer_id']
        resp = client.post(
            f"/wedding/{roles['wedding_id']}/guests/add",
            data={'name': 'Uninvited Plus One'},
        )
        assert resp.status_code == 403
        with app.app_context():
            assert Guest.query.filter_by(name='Uninvited Plus One').count() == 0

    def test_viewer_cannot_delete_the_wedding(self, app, client, roles):
        """The headline role bypass: a read-only collaborator deleting everything."""
        with client.session_transaction() as sess:
            sess['user_id'] = roles['viewer_id']
        resp = client.post(f"/wedding/{roles['wedding_id']}/delete")
        assert resp.status_code == 403
        with app.app_context():
            assert db.session.get(Wedding, roles['wedding_id']) is not None

    def test_planner_can_write(self, app, client, roles):
        with client.session_transaction() as sess:
            sess['user_id'] = roles['planner_id']
        resp = client.post(
            f"/wedding/{roles['wedding_id']}/guests/add",
            data={'name': 'Invited Guest'},
        )
        assert resp.status_code in (200, 302)
        with app.app_context():
            assert Guest.query.filter_by(name='Invited Guest').count() == 1

    def test_planner_cannot_delete_the_wedding(self, app, client, roles):
        with client.session_transaction() as sess:
            sess['user_id'] = roles['planner_id']
        resp = client.post(f"/wedding/{roles['wedding_id']}/delete")
        assert resp.status_code == 403
        with app.app_context():
            assert db.session.get(Wedding, roles['wedding_id']) is not None

    def test_planner_cannot_manage_collaborators(self, app, client, roles):
        with client.session_transaction() as sess:
            sess['user_id'] = roles['planner_id']
        resp = client.post(
            f"/wedding/{roles['wedding_id']}/collaborators/add",
            data={'email': 'outsider@example.com', 'role': 'planner'},
        )
        assert resp.status_code == 403

    def test_planner_cannot_publish_the_wedding(self, app, client, roles):
        """Turning on the public RSVP portal is an owner decision."""
        with client.session_transaction() as sess:
            sess['user_id'] = roles['planner_id']
        resp = client.post(f"/wedding/{roles['wedding_id']}/rsvp/enable")
        assert resp.status_code == 403
        with app.app_context():
            assert not db.session.get(Wedding, roles['wedding_id']).rsvp_enabled

    def test_owner_can_delete_the_wedding(self, app, client, roles):
        with client.session_transaction() as sess:
            sess['user_id'] = roles['owner_id']
        resp = client.post(f"/wedding/{roles['wedding_id']}/delete")
        assert resp.status_code in (200, 302)
        with app.app_context():
            assert db.session.get(Wedding, roles['wedding_id']) is None


class TestRequiredRoleMapping:
    """The method-derived default, stated as a test so a change is deliberate."""

    def test_safe_methods_need_viewer(self):
        assert required_wedding_role('guests_view', 'GET') == 'viewer'

    def test_unsafe_methods_need_planner(self):
        assert required_wedding_role('guests_view', 'POST') == 'planner'

    def test_listed_endpoints_need_owner(self):
        for endpoint in OWNER_ONLY_ENDPOINTS:
            assert required_wedding_role(endpoint, 'POST') == 'owner'
