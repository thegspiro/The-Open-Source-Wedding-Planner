"""Full-plan export and import.

This is the highest blast-radius code in the repository -- it is how a couple
moves their plan between installations, and how they get it back after a
mistake -- and none of it was executed by the suite: not the export, not the
import, not one of the parse helpers (_parse_dt, _parse_date, _parse_time,
_safe_int, _safe_float, _safe_bool, _serialize_model, _serialize_date).

Import merges into the wedding named in the URL rather than replacing it, and
it only reads the sections listed in its model_map. TestKnownAsymmetry pins the
sections the export writes but the import ignores, so the gap is visible in the
test output instead of being discovered by someone whose ceremony details
vanished.
"""

import json
import pytest
from io import BytesIO
from datetime import datetime, timedelta

from models import (db, Wedding, WeddingAccess, Guest, Task, TipItem,
                    GuestGroup, Vendor, VendorNote, SpeechToast)


EXPORT = "/wedding/{wid}/export/full"
IMPORT = "/wedding/{wid}/import/full"


def upload(client, wedding_id, payload, filename="plan.json"):
    """POST a file to the import endpoint. `payload` may be dict, str or bytes."""
    if isinstance(payload, dict):
        body = json.dumps(payload).encode("utf-8")
    elif isinstance(payload, str):
        body = payload.encode("utf-8")
    else:
        body = payload
    return client.post(
        IMPORT.format(wid=wedding_id),
        data={"file": (BytesIO(body), filename)},
        content_type="multipart/form-data",
        follow_redirects=True,
    )


@pytest.fixture
def empty_target(app, populated_wedding):
    """A second, empty wedding owned by the same user, to import into."""
    with app.app_context():
        wedding = Wedding(
            couple_names="Empty Target",
            wedding_date=datetime.utcnow() + timedelta(days=200),
            email="target@example.com",
        )
        db.session.add(wedding)
        db.session.flush()
        db.session.add(WeddingAccess(user_id=populated_wedding["user_id"],
                                     wedding_id=wedding.id, role="owner"))
        db.session.commit()
        target_id = wedding.id
    yield target_id


class TestExport:
    """The file has to be a real, complete, parseable export."""

    def test_export_is_json_and_offers_a_download(self, populated_client):
        client, populated = populated_client
        response = client.get(EXPORT.format(wid=populated["wedding_id"]))
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".json" in response.headers["Content-Disposition"]

    def test_export_parses_and_is_versioned(self, populated_client):
        client, populated = populated_client
        data = json.loads(
            client.get(EXPORT.format(wid=populated["wedding_id"])).get_data(as_text=True)
        )
        assert data["export_version"] == "1.0"
        assert data["wedding"]["couple_names"] == "Populated Couple"

    def test_export_carries_the_children_it_claims_to(self, populated_client):
        client, populated = populated_client
        data = json.loads(
            client.get(EXPORT.format(wid=populated["wedding_id"])).get_data(as_text=True)
        )
        assert len(data["guests"]) == 12
        assert len(data["tasks"]) == 2
        assert len(data["tips"]) == 2
        assert len(data["vendors"]) == 1
        assert data["ceremony"] is not None
        assert data["reception"] is not None
        assert data["budget"] is not None
        assert len(data["budget"]["expenses"]) == 3

    def test_export_omits_the_wedding_id(self, populated_client):
        """The importer assigns its own; a stale id in the file is a trap."""
        client, populated = populated_client
        data = json.loads(
            client.get(EXPORT.format(wid=populated["wedding_id"])).get_data(as_text=True)
        )
        assert "id" not in data["wedding"]
        for guest in data["guests"]:
            assert "wedding_id" not in guest

    def test_dates_are_serialised_as_strings(self, populated_client):
        client, populated = populated_client
        data = json.loads(
            client.get(EXPORT.format(wid=populated["wedding_id"])).get_data(as_text=True)
        )
        dated = [t for t in data["tasks"] if t.get("due_date")]
        assert dated, "the fixture has dated tasks; the export dropped them"
        for task in dated:
            assert isinstance(task["due_date"], str)


class TestRoundTrip:
    """Export then import must not quietly lose or mangle anything."""

    def _round_trip(self, app, client, source_id, target_id):
        payload = client.get(EXPORT.format(wid=source_id)).get_data()
        response = upload(client, target_id, payload)
        assert response.status_code == 200
        return response

    def test_guests_survive_the_trip(self, app, populated_client, empty_target):
        client, populated = populated_client
        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            source = Guest.query.filter_by(
                wedding_id=populated["wedding_id"]).order_by(Guest.name).all()
            landed = Guest.query.filter_by(
                wedding_id=empty_target).order_by(Guest.name).all()
            assert len(landed) == len(source) == 12
            assert [g.name for g in landed] == [g.name for g in source]
            assert [g.rsvp_status for g in landed] == [g.rsvp_status for g in source]
            assert [g.meal_choice for g in landed] == [g.meal_choice for g in source]

    def test_a_task_keeps_its_due_date_and_done_flag(self, app, populated_client,
                                                     empty_target):
        client, populated = populated_client
        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            source = {t.title: t for t in Task.query.filter_by(
                wedding_id=populated["wedding_id"]).all()}
            landed = {t.title: t for t in Task.query.filter_by(
                wedding_id=empty_target).all()}
            assert set(landed) == set(source)
            for title, task in landed.items():
                assert task.due_date is not None, f"{title} lost its due date"
                assert task.due_date.date() == source[title].due_date.date()
                assert task.completed == source[title].completed

    def test_money_survives_as_a_number(self, app, populated_client, empty_target):
        client, populated = populated_client
        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            landed = {t.recipient: t for t in TipItem.query.filter_by(
                wedding_id=empty_target).all()}
            assert landed["DJ"].suggested_amount == 150.0
            assert landed["Officiant"].actual_amount == 100.0

    def test_booleans_survive_as_booleans(self, app, populated_client, empty_target):
        client, populated = populated_client
        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            group = GuestGroup.query.filter_by(wedding_id=empty_target).one()
            assert group.name == "College Friends"
            assert group.seat_together is True

    def test_a_vendor_brings_its_communication_log(self, app, populated_client,
                                                  empty_target):
        client, populated = populated_client
        with app.app_context():
            vendor = Vendor.query.filter_by(
                wedding_id=populated["wedding_id"]).one()
            note = VendorNote.query.filter_by(vendor_id=vendor.id).one()
            note.subject = "Confirmed the delivery window"
            db.session.commit()

        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            landed = Vendor.query.filter_by(wedding_id=empty_target).one()
            assert landed.business_name == "Acme Flowers"
            assert landed.total_cost == 2400.0
            notes = VendorNote.query.filter_by(vendor_id=landed.id).all()
            assert len(notes) == 1
            assert notes[0].subject == "Confirmed the delivery window"

    def test_importing_twice_merges_rather_than_replaces(self, app, populated_client,
                                                        empty_target):
        """Import is documented as a merge. Two imports means two copies."""
        client, populated = populated_client
        self._round_trip(app, client, populated["wedding_id"], empty_target)
        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            assert Guest.query.filter_by(wedding_id=empty_target).count() == 24

    def test_the_import_never_touches_the_source(self, app, populated_client,
                                                empty_target):
        client, populated = populated_client
        with app.app_context():
            before = Guest.query.filter_by(
                wedding_id=populated["wedding_id"]).count()

        self._round_trip(app, client, populated["wedding_id"], empty_target)

        with app.app_context():
            after = Guest.query.filter_by(
                wedding_id=populated["wedding_id"]).count()
        assert after == before


class TestZeroIsAValue:
    """A zero amount means "nothing", not "unknown"; it must survive."""

    def test_a_zero_amount_is_not_turned_into_null(self, app, populated_client,
                                                  empty_target):
        client, populated = populated_client
        with app.app_context():
            db.session.add(TipItem(wedding_id=populated["wedding_id"],
                                   recipient="Cousin who helped",
                                   suggested_amount=0.0, actual_amount=0.0))
            db.session.commit()

        payload = client.get(
            EXPORT.format(wid=populated["wedding_id"])).get_data()
        upload(client, empty_target, payload)

        with app.app_context():
            landed = TipItem.query.filter_by(
                wedding_id=empty_target, recipient="Cousin who helped").one()
            assert landed.suggested_amount == 0.0, (
                "a deliberate zero came back as unknown"
            )

    def test_a_zero_count_is_not_turned_into_null(self, app, populated_client,
                                                 empty_target):
        """duration_minutes has no column default, so this really does test the
        converter rather than the schema filling the gap back in."""
        client, populated = populated_client
        with app.app_context():
            db.session.add(SpeechToast(wedding_id=populated["wedding_id"],
                                       speaker_name="Brief Speaker",
                                       duration_minutes=0))
            db.session.commit()

        payload = client.get(
            EXPORT.format(wid=populated["wedding_id"])).get_data()
        upload(client, empty_target, payload)

        with app.app_context():
            landed = SpeechToast.query.filter_by(
                wedding_id=empty_target, speaker_name="Brief Speaker").one()
            assert landed.duration_minutes == 0


class TestBadUploads:
    """A malformed file must be refused, not half-applied."""

    def _guest_count(self, app, wedding_id):
        with app.app_context():
            return Guest.query.filter_by(wedding_id=wedding_id).count()

    def test_no_file_is_refused(self, app, populated_client, empty_target):
        client, _ = populated_client
        response = client.post(IMPORT.format(wid=empty_target),
                               data={}, content_type="multipart/form-data",
                               follow_redirects=True)
        assert "No file uploaded" in response.get_data(as_text=True)
        assert self._guest_count(app, empty_target) == 0

    def test_a_non_json_filename_is_refused(self, app, populated_client, empty_target):
        client, _ = populated_client
        response = upload(client, empty_target, {"export_version": "1.0"},
                          filename="plan.exe")
        assert "Please upload a JSON file" in response.get_data(as_text=True)
        assert self._guest_count(app, empty_target) == 0

    def test_malformed_json_is_refused(self, app, populated_client, empty_target):
        client, _ = populated_client
        response = upload(client, empty_target, '{"export_version": "1.0", ')
        assert "Invalid JSON file" in response.get_data(as_text=True)
        assert self._guest_count(app, empty_target) == 0

    def test_a_truncated_export_is_refused(self, app, populated_client, empty_target):
        client, populated = populated_client
        payload = client.get(EXPORT.format(wid=populated["wedding_id"])).get_data()
        response = upload(client, empty_target, payload[: len(payload) // 2])
        assert "Invalid JSON file" in response.get_data(as_text=True)
        assert self._guest_count(app, empty_target) == 0

    def test_json_without_a_version_is_refused(self, app, populated_client,
                                              empty_target):
        """Some other application's JSON must not be treated as a plan."""
        client, _ = populated_client
        response = upload(client, empty_target,
                          {"guests": [{"name": "Should not land"}]})
        assert "does not appear to be a valid" in response.get_data(as_text=True)
        assert self._guest_count(app, empty_target) == 0

    def test_undecodable_bytes_are_refused(self, app, populated_client, empty_target):
        client, _ = populated_client
        response = upload(client, empty_target, b"\xff\xfe\x00\x01not utf-8")
        assert "Invalid JSON file" in response.get_data(as_text=True)
        assert self._guest_count(app, empty_target) == 0

    def test_a_valid_file_with_no_recognised_sections_says_so(self, app,
                                                             populated_client,
                                                             empty_target):
        client, _ = populated_client
        response = upload(client, empty_target, {"export_version": "1.0"})
        assert "No data was imported" in response.get_data(as_text=True)


class TestImportCannotBeAimedElsewhere:
    """The file supplies content; the URL supplies the destination."""

    def test_ids_in_the_file_are_ignored(self, app, populated_client, empty_target):
        """A hand-edited file naming another wedding must not reach it."""
        client, populated = populated_client
        payload = {
            "export_version": "1.0",
            "guests": [{"name": "Injected", "wedding_id": populated["wedding_id"],
                        "id": 1}],
        }
        upload(client, empty_target, payload)

        with app.app_context():
            assert Guest.query.filter_by(wedding_id=empty_target,
                                         name="Injected").count() == 1
            assert Guest.query.filter_by(wedding_id=populated["wedding_id"],
                                         name="Injected").count() == 0

    def test_markup_in_an_imported_name_cannot_reach_the_page(self, app,
                                                             populated_client,
                                                             empty_target):
        """An import file is untrusted input: it arrives by email or off a USB
        stick, and nothing about it has been through the app's forms.

        sanitize_string only trims and truncates -- stripping markup is
        validate_text_field's job -- so the raw string does land in the column.
        What matters is that it cannot become markup again on the way out, which
        is Jinja's autoescaping. Assert the rendered page, not the column.
        """
        client, _ = populated_client
        payload = {
            "export_version": "1.0",
            "guests": [{"name": "<script>alert(1)</script>Mallory"}],
        }
        upload(client, empty_target, payload)

        response = client.get(f"/wedding/{empty_target}/guests")
        assert response.status_code == 200
        body = response.get_data(as_text=True)
        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;" in body, (
            "the name should render escaped; if it is missing entirely, this "
            "test is no longer proving anything"
        )


class TestKnownAsymmetry:
    """The export writes sections the import does not read.

    This is a real gap, not a nitpick: a couple who exports, reinstalls and
    imports gets their guests and vendors back but silently loses their
    ceremony, reception, budget and honeymoon. It is pinned here so the
    asymmetry is visible, and so whoever closes it has a test to update.
    """

    NOT_IMPORTED = ["ceremony", "reception", "budget", "honeymoon", "branding",
                    "rehearsal_dinner", "marriage_license", "people",
                    "inventory_items", "inventory_bins", "vendor_quotes"]

    def test_the_export_writes_these_sections(self, populated_client):
        client, populated = populated_client
        data = json.loads(
            client.get(EXPORT.format(wid=populated["wedding_id"])).get_data(as_text=True)
        )
        for section in self.NOT_IMPORTED:
            assert section in data, f"the export no longer writes {section}"

    def test_but_the_import_drops_them(self, app, populated_client, empty_target):
        client, populated = populated_client
        payload = client.get(EXPORT.format(wid=populated["wedding_id"])).get_data()
        upload(client, empty_target, payload)

        with app.app_context():
            target = Wedding.query.get(empty_target)
            assert target.ceremony is None
            assert target.reception is None
            assert target.budget is None
            assert target.honeymoon is None
            assert len(target.people) == 0
