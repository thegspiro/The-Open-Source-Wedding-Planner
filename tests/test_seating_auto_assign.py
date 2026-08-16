"""The seating auto-assign algorithm.

188 lines of constraint solving -- union-find over "together" preferences,
household and plus-one merging, apart constraints gated on priority, social
affinity scoring, role-aware table selection -- and not one line of it was
executed by the suite. It is the most intricate code in the repository and the
easiest to break silently: a wrong answer here still returns 302 and still
flashes success.

These tests go through the endpoint rather than calling the algorithm directly,
because it is written inline in the handler. They assert on the resulting
database state, and they are written as invariants ("capacity is never
exceeded") rather than as a golden layout, so they keep their meaning if the
scoring is retuned.
"""

import pytest
from datetime import datetime, timedelta

from models import (db, User, Wedding, WeddingAccess, Reception, SeatingTable,
                    Guest, SeatingPreference, GuestGroup)


AUTO_ASSIGN = "/wedding/{wid}/seating-chart/auto-assign"


@pytest.fixture
def seating(app, database):
    """A wedding with a reception and nothing else. Tests add their own tables."""
    with app.app_context():
        owner = User(email="seating-owner@example.com", name="Owner",
                     user_type="self")
        owner.set_password("TestPassword1!")
        db.session.add(owner)
        db.session.flush()

        wedding = Wedding(
            couple_names="Seating Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="seating@example.com",
        )
        db.session.add(wedding)
        db.session.flush()
        db.session.add(WeddingAccess(user_id=owner.id, wedding_id=wedding.id,
                                     role="owner"))

        reception = Reception(wedding_id=wedding.id, venue_name="The Hall")
        db.session.add(reception)
        db.session.commit()

        data = {"user_id": owner.id, "wedding_id": wedding.id,
                "reception_id": reception.id}
    yield data


@pytest.fixture
def seated_client(client, seating):
    with client.session_transaction() as sess:
        sess["user_id"] = seating["user_id"]
    return client, seating


def add_tables(reception_id, specs):
    """specs: list of (number, capacity) or (number, capacity, role)."""
    made = []
    for spec in specs:
        number, capacity = spec[0], spec[1]
        role = spec[2] if len(spec) > 2 else None
        table = SeatingTable(reception_id=reception_id, table_number=str(number),
                             table_name=f"Table {number}", capacity=capacity,
                             table_role=role)
        db.session.add(table)
        made.append(table)
    db.session.flush()
    return made


def add_guests(wedding_id, count, **kwargs):
    """Guests named 'Guest NN', numbered from `start`, accepted by default."""
    start = kwargs.pop("start", 0)
    rsvp_status = kwargs.pop("rsvp_status", "accepted")
    made = []
    for i in range(count):
        guest = Guest(wedding_id=wedding_id, name=f"Guest {start + i:02d}",
                      rsvp_status=rsvp_status, **kwargs)
        db.session.add(guest)
        made.append(guest)
    db.session.flush()
    return made


def seating_state(app, wedding_id):
    """Every accepted guest's table, keyed by guest name."""
    with app.app_context():
        guests = Guest.query.filter_by(wedding_id=wedding_id).all()
        return {g.name: g.table_id for g in guests}


class TestGuardClauses:
    """The endpoint must refuse cleanly when it has nothing to work with."""

    def test_no_tables_redirects_without_assigning(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_guests(seating["wedding_id"], 4)
            db.session.commit()

        response = client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))
        assert response.status_code == 302
        assert set(seating_state(app, seating["wedding_id"]).values()) == {None}

    def test_no_accepted_guests_redirects_without_assigning(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 8)])
            add_guests(seating["wedding_id"], 4, rsvp_status="pending")
            db.session.commit()

        response = client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))
        assert response.status_code == 302
        assert set(seating_state(app, seating["wedding_id"]).values()) == {None}


class TestCoreInvariants:
    """Whatever the scoring does, these must hold."""

    def test_every_accepted_guest_is_seated_when_there_is_room(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 8), (2, 8)])
            add_guests(seating["wedding_id"], 12)
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        unseated = [name for name, tid in state.items() if tid is None]
        assert not unseated, f"{len(unseated)} guests left unseated with room to spare"

    def test_table_capacity_is_never_exceeded(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 4), (2, 4), (3, 4)])
            add_guests(seating["wedding_id"], 12)
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        with app.app_context():
            tables = SeatingTable.query.filter_by(
                reception_id=seating["reception_id"]).all()
            for table in tables:
                seated = Guest.query.filter_by(table_id=table.id).count()
                assert seated <= table.capacity, (
                    f"table {table.table_number} holds {table.capacity} but was "
                    f"given {seated} guests"
                )

    def test_guests_who_have_not_accepted_are_never_seated(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 20)])
            add_guests(seating["wedding_id"], 3, start=0)
            add_guests(seating["wedding_id"], 3, start=10, rsvp_status="declined")
            add_guests(seating["wedding_id"], 3, start=20, rsvp_status="pending")
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        with app.app_context():
            for guest in Guest.query.filter_by(wedding_id=seating["wedding_id"]).all():
                if guest.rsvp_status != "accepted":
                    assert guest.table_id is None, (
                        f"{guest.name} has not accepted but was seated"
                    )

    def test_overflow_is_reported_rather_than_dropped(self, app, seated_client):
        """More guests than seats: seat what fits, say so, lose nobody silently."""
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 4)])
            add_guests(seating["wedding_id"], 10)
            db.session.commit()

        response = client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]),
                               follow_redirects=True)
        body = response.get_data(as_text=True)
        assert "could not be placed" in body

        state = seating_state(app, seating["wedding_id"])
        seated = [t for t in state.values() if t is not None]
        assert len(seated) == 4, "the one table seats four; it should be full"

    def test_the_same_input_produces_the_same_layout(self, app, seated_client):
        """A re-run must not reshuffle everyone's seat for no reason."""
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 6), (2, 6)])
            add_guests(seating["wedding_id"], 10, side="partner1")
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))
        first = seating_state(app, seating["wedding_id"])
        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))
        second = seating_state(app, seating["wedding_id"])

        assert first == second


class TestGroupingRules:
    """The whole point of the algorithm: people who belong together, sit together."""

    def _table_of(self, state, name):
        return state[name]

    # The household members below are interleaved with unrelated guests on
    # purpose. Created consecutively they would land on the same table by sheer
    # fill order, and the test would pass even with the grouping removed.

    def test_a_household_is_seated_together(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 4), (2, 4)])
            for i in range(4):
                add_guests(seating["wedding_id"], 1, start=i * 2,
                           household_group="Kim Family")
                add_guests(seating["wedding_id"], 1, start=i * 2 + 1)
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        household = {state[f"Guest {i * 2:02d}"] for i in range(4)}
        assert len(household) == 1, "the Kim family was split across tables"
        assert None not in household

    def test_household_matching_ignores_case_and_padding(self, app, seated_client):
        client, seating = seated_client
        spellings = ["Kim Family", "  kim family  ", "KIM FAMILY", "kim FAMILY"]
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 4), (2, 4)])
            for i, spelling in enumerate(spellings):
                add_guests(seating["wedding_id"], 1, start=i * 2,
                           household_group=spelling)
                add_guests(seating["wedding_id"], 1, start=i * 2 + 1)
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        household = {state[f"Guest {i * 2:02d}"] for i in range(len(spellings))}
        assert len(household) == 1, "the same household spelled differently was split"

    def test_a_together_preference_is_honoured(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 4), (2, 4)])
            guests = add_guests(seating["wedding_id"], 8)
            db.session.add(SeatingPreference(
                wedding_id=seating["wedding_id"],
                guest_id=guests[0].id, other_guest_id=guests[7].id,
                preference_type="together", priority=5,
            ))
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        assert state["Guest 00"] == state["Guest 07"] is not None

    def test_a_plus_one_sits_with_their_host(self, app, seated_client):
        """The host is created first and the date last, with six guests in
        between, so fill order alone would put them at different tables."""
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 4), (2, 4)])
            db.session.add(Guest(wedding_id=seating["wedding_id"], name="Host Person",
                                 rsvp_status="accepted"))
            db.session.flush()
            add_guests(seating["wedding_id"], 6, start=10)
            db.session.add(Guest(wedding_id=seating["wedding_id"], name="Their Date",
                                 rsvp_status="accepted", is_plus_one=True,
                                 plus_one_of="host person"))
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        assert state["Host Person"] == state["Their Date"] is not None

    def test_a_high_priority_apart_preference_separates_guests(self, app, seated_client):
        """Priority 3 and above is a hard separation, per can_place()."""
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 6), (2, 6)])
            guests = add_guests(seating["wedding_id"], 4)
            db.session.add(SeatingPreference(
                wedding_id=seating["wedding_id"],
                guest_id=guests[0].id, other_guest_id=guests[1].id,
                preference_type="apart", priority=5,
            ))
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        assert state["Guest 00"] != state["Guest 01"], (
            "a priority-5 apart preference was ignored"
        )

    def test_kids_are_seated_at_the_kids_table(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 8, None), (2, 8, "kids")])
            add_guests(seating["wedding_id"], 4, start=0, guest_type="child")
            add_guests(seating["wedding_id"], 6, start=10, guest_type="friend")
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        with app.app_context():
            kids_table = SeatingTable.query.filter_by(
                reception_id=seating["reception_id"], table_role="kids").one()
            state = seating_state(app, seating["wedding_id"])
            for i in range(4):
                assert state[f"Guest {i:02d}"] == kids_table.id, (
                    f"Guest {i:02d} is a child but was not seated at the kids table"
                )


class TestOnlyUnassigned:
    """The 'only unassigned' switch is the difference between topping up a
    seating plan and throwing the whole thing away."""

    def test_existing_assignments_are_preserved(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            tables = add_tables(seating["reception_id"], [(1, 6), (2, 6)])
            guests = add_guests(seating["wedding_id"], 8)
            # Pin two guests to the second table by hand.
            guests[0].table_id = tables[1].id
            guests[1].table_id = tables[1].id
            db.session.commit()
            pinned_table = tables[1].id

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]),
                    data={"only_unassigned": "on"})

        state = seating_state(app, seating["wedding_id"])
        assert state["Guest 00"] == pinned_table
        assert state["Guest 01"] == pinned_table

    def test_a_full_run_clears_seats_it_cannot_reassign(self, app, seated_client):
        """A full run starts from a blank plan, so a guest it cannot seat must
        come back unseated rather than keeping last run's table.

        Six guests are pinned to a two-seat table, then re-run against four
        seats total. Without the reset the two it cannot place stay pointed at
        their old table, and the seating chart shows four people sitting at a
        table for two.
        """
        client, seating = seated_client
        with app.app_context():
            tables = add_tables(seating["reception_id"], [(1, 2), (2, 2)])
            guests = add_guests(seating["wedding_id"], 6)
            for guest in guests:
                guest.table_id = tables[0].id
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        seated = [t for t in state.values() if t is not None]
        assert len(seated) == 4, (
            f"four seats exist but {len(seated)} guests are shown as seated"
        )

        with app.app_context():
            for table in SeatingTable.query.filter_by(
                    reception_id=seating["reception_id"]).all():
                occupancy = Guest.query.filter_by(table_id=table.id).count()
                assert occupancy <= table.capacity, (
                    f"table {table.table_number} shows {occupancy} guests in "
                    f"{table.capacity} seats"
                )

    def test_only_unassigned_still_respects_capacity(self, app, seated_client):
        """Seats already taken by pinned guests must count against the table."""
        client, seating = seated_client
        with app.app_context():
            tables = add_tables(seating["reception_id"], [(1, 4), (2, 4)])
            guests = add_guests(seating["wedding_id"], 8)
            for guest in guests[:3]:
                guest.table_id = tables[0].id
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]),
                    data={"only_unassigned": "on"})

        with app.app_context():
            for table in SeatingTable.query.filter_by(
                    reception_id=seating["reception_id"]).all():
                seated = Guest.query.filter_by(table_id=table.id).count()
                assert seated <= table.capacity, (
                    f"table {table.table_number} overfilled: {seated} in "
                    f"{table.capacity} seats"
                )


class TestSocialAffinity:
    """Shared social tags pull a group toward the table its friends are at.

    Affinity is only observable when it makes a *later* table win over an
    earlier one that still has room -- ties go to the first table with space, so
    in most layouts everyone piles into table 1 regardless and a naive test
    passes with the scoring ripped out.

    This builds the discriminating case: an apart constraint pushes the first
    club member onto table 2, and the question is where the second one goes.
    Table 1 has room and comes first, so only affinity can send it to table 2.
    """

    def test_a_group_follows_its_friends_to_a_later_table(self, app, seated_client):
        client, seating = seated_client
        with app.app_context():
            add_tables(seating["reception_id"], [(1, 8), (2, 8)])
            db.session.add(GuestGroup(wedding_id=seating["wedding_id"],
                                      name="Rowing Club", seat_together=True,
                                      priority=9))
            outsider = Guest(wedding_id=seating["wedding_id"], name="Outsider",
                             rsvp_status="accepted")
            rower_one = Guest(wedding_id=seating["wedding_id"], name="Rower One",
                              rsvp_status="accepted", social_groups="Rowing Club")
            filler = Guest(wedding_id=seating["wedding_id"], name="Filler",
                           rsvp_status="accepted")
            rower_two = Guest(wedding_id=seating["wedding_id"], name="Rower Two",
                              rsvp_status="accepted", social_groups="Rowing Club")
            db.session.add_all([outsider, rower_one, filler, rower_two])
            db.session.flush()
            # Forces Rower One off table 1, where Outsider is already sitting.
            db.session.add(SeatingPreference(
                wedding_id=seating["wedding_id"],
                guest_id=rower_one.id, other_guest_id=outsider.id,
                preference_type="apart", priority=5,
            ))
            db.session.commit()

        client.post(AUTO_ASSIGN.format(wid=seating["wedding_id"]))

        state = seating_state(app, seating["wedding_id"])
        assert state["Rower Two"] == state["Rower One"], (
            "Rower Two took the emptier table instead of joining their club"
        )
        assert state["Rower One"] != state["Outsider"]
