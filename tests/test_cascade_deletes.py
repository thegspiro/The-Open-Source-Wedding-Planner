"""Deleting a wedding takes its data with it, and nobody else's.

models.py reports near-total coverage, which means only that importing it runs
its 61 class bodies. Not one relationship was ever exercised. The schema
declares 59 delete-orphan cascades and nothing checked that any of them fire.

Two ways that hurts, both silent. Rows left behind after a delete are a privacy
problem -- guest names, dietary needs, home addresses, all still in the database
after the couple believed they had erased everything. And a cascade reaching one
row too far deletes another wedding's data with no error at all.

The walk over Wedding's relationships means a module added later is covered as
soon as its relationship is declared.
"""

import pytest
from datetime import datetime, timedelta

from sqlalchemy import inspect as sa_inspect

from models import (db, User, Wedding, WeddingAccess, Guest, Task, Vendor,
                    VendorNote, Budget, BudgetExpense, Reception, SeatingTable,
                    Ceremony, CeremonyTimelineItem, Honeymoon, PackingItem,
                    InventoryBin, InventoryItem, Comment)


def wedding_child_relationships():
    """Every relationship on Wedding that cascades deletes to its children."""
    mapper = sa_inspect(Wedding)
    out = []
    for rel in mapper.relationships:
        if "delete-orphan" in (rel.cascade or ""):
            out.append(rel)
    return out


CHILD_RELATIONSHIPS = wedding_child_relationships()


def row_count(model, **filters):
    return model.query.filter_by(**filters).count()


class TestTheWalkItself:
    def test_wedding_declares_cascading_children(self):
        assert len(CHILD_RELATIONSHIPS) > 30, (
            f"expected Wedding to own 30+ cascading relationships, found "
            f"{len(CHILD_RELATIONSHIPS)}; has the schema changed?"
        )


class TestTheSchemaCannotDeadlockItself:
    """A structural guard, not an example.

    When a child's foreign key is NOT NULL, the parent relationship must
    cascade the delete. Without a cascade SQLAlchemy's default is to NULL the
    column instead, the database refuses, and the delete fails outright -- so
    the parent row becomes undeletable. SeatingPreference shipped exactly that
    way on both of its guest foreign keys, which made a guest with any seating
    preference impossible to delete, and took the whole wedding down with it.

    This walks the mappers so a new relationship is checked the day it lands.
    """

    def test_every_not_null_child_relationship_cascades(self):
        import models

        offenders = []
        for name in dir(models):
            cls = getattr(models, name)
            if not hasattr(cls, "__mapper__"):
                continue
            try:
                mapper = sa_inspect(cls)
            except Exception:
                continue
            for rel in mapper.relationships:
                if rel.direction.name != "ONETOMANY":
                    continue
                if "delete" in (rel.cascade or ""):
                    continue
                for col in rel.remote_side:
                    if col.foreign_keys and not col.nullable:
                        offenders.append(f"{cls.__name__}.{rel.key} -> {col}")
                        break

        assert not offenders, (
            "these relationships point at a NOT NULL foreign key but do not "
            "cascade deletes, so deleting the parent will fail with an "
            "IntegrityError: " + "; ".join(sorted(set(offenders)))
        )


class TestDeletingAGuest:
    """The narrower case behind the wedding-level failure."""

    def test_a_guest_with_a_seating_preference_can_be_deleted(self, app,
                                                             populated_wedding):
        from models import SeatingPreference

        wid = populated_wedding["wedding_id"]
        guest_id = populated_wedding["guest_ids"][0]
        with app.app_context():
            assert SeatingPreference.query.filter_by(guest_id=guest_id).count() == 1
            db.session.delete(Guest.query.get(guest_id))
            db.session.commit()

            assert Guest.query.get(guest_id) is None
            assert SeatingPreference.query.filter_by(guest_id=guest_id).count() == 0

    def test_deleting_the_other_side_of_a_preference_also_works(self, app,
                                                               populated_wedding):
        from models import SeatingPreference

        other_id = populated_wedding["guest_ids"][1]
        with app.app_context():
            assert SeatingPreference.query.filter_by(
                other_guest_id=other_id).count() == 1
            db.session.delete(Guest.query.get(other_id))
            db.session.commit()
            assert SeatingPreference.query.filter_by(
                other_guest_id=other_id).count() == 0


class TestDeletingAWedding:
    """The populated fixture has a row in every major module, so this covers
    the whole schema rather than the handful of tables a test remembers."""

    def test_nothing_is_left_behind(self, app, populated_wedding):
        wid = populated_wedding["wedding_id"]

        with app.app_context():
            wedding = Wedding.query.get(wid)
            populated = {}
            for rel in CHILD_RELATIONSHIPS:
                value = getattr(wedding, rel.key)
                # Wedding owns both collections (guests) and scalars (ceremony).
                rows = list(value) if rel.uselist else ([value] if value else [])
                if rows:
                    populated[rel.key] = (rel.mapper.class_,
                                          [r.id for r in rows])
            db.session.delete(wedding)
            db.session.commit()

        assert len(populated) > 25, (
            f"only {len(populated)} relationships had data; the fixture is no "
            f"longer exercising the schema"
        )

        with app.app_context():
            orphans = {}
            for key, (model_cls, ids) in populated.items():
                left = model_cls.query.filter(model_cls.id.in_(ids)).count()
                if left:
                    orphans[key] = left
            assert not orphans, (
                f"deleting the wedding left rows behind in: {orphans}"
            )

    def test_the_wedding_itself_is_gone(self, app, populated_wedding):
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert Wedding.query.get(wid) is None

    def test_access_rows_go_too(self, app, populated_wedding):
        """Otherwise the wedding list shows an entry that opens nothing."""
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            assert row_count(WeddingAccess, wedding_id=wid) == 1
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert row_count(WeddingAccess, wedding_id=wid) == 0

    def test_the_owner_account_survives(self, app, populated_wedding):
        """Deleting a wedding is not deleting the person who planned it."""
        uid = populated_wedding["user_id"]
        with app.app_context():
            db.session.delete(Wedding.query.get(populated_wedding["wedding_id"]))
            db.session.commit()
            assert User.query.get(uid) is not None


class TestGrandchildren:
    """Rows hanging off a child, not off the wedding. These are the ones a
    hand-written cascade test forgets."""

    def test_vendor_notes_go_with_the_vendor(self, app, populated_wedding):
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            vendor = Vendor.query.filter_by(wedding_id=wid).one()
            note_id = VendorNote.query.filter_by(vendor_id=vendor.id).one().id
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert VendorNote.query.get(note_id) is None

    def test_budget_expenses_go_with_the_budget(self, app, populated_wedding):
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            budget = Budget.query.filter_by(wedding_id=wid).one()
            expense_ids = [e.id for e in
                           BudgetExpense.query.filter_by(budget_id=budget.id).all()]
            assert len(expense_ids) == 3
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert BudgetExpense.query.filter(
                BudgetExpense.id.in_(expense_ids)).count() == 0

    def test_seating_tables_go_with_the_reception(self, app, populated_wedding):
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            reception = Reception.query.filter_by(wedding_id=wid).one()
            table_ids = [t.id for t in
                         SeatingTable.query.filter_by(reception_id=reception.id).all()]
            assert table_ids
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert SeatingTable.query.filter(
                SeatingTable.id.in_(table_ids)).count() == 0

    def test_ceremony_timeline_items_go_with_the_ceremony(self, app,
                                                         populated_wedding):
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            ceremony = Ceremony.query.filter_by(wedding_id=wid).one()
            item_ids = [i.id for i in CeremonyTimelineItem.query.filter_by(
                ceremony_id=ceremony.id).all()]
            assert item_ids
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert CeremonyTimelineItem.query.filter(
                CeremonyTimelineItem.id.in_(item_ids)).count() == 0

    def test_packing_items_go_with_the_honeymoon(self, app, populated_wedding):
        wid = populated_wedding["wedding_id"]
        with app.app_context():
            honeymoon = Honeymoon.query.filter_by(wedding_id=wid).one()
            item_ids = [p.id for p in
                        PackingItem.query.filter_by(honeymoon_id=honeymoon.id).all()]
            assert item_ids
            db.session.delete(Wedding.query.get(wid))
            db.session.commit()
            assert PackingItem.query.filter(
                PackingItem.id.in_(item_ids)).count() == 0


class TestTheCascadeStopsAtTheBoundary:
    """A cascade that reaches one row too far is worse than one that leaks."""

    @pytest.fixture
    def bystander(self, app, populated_wedding):
        """A second wedding, with its own data, that must survive untouched."""
        with app.app_context():
            other = Wedding(
                couple_names="Bystander Couple",
                wedding_date=datetime.utcnow() + timedelta(days=300),
                email="bystander@example.com",
            )
            db.session.add(other)
            db.session.flush()
            db.session.add(WeddingAccess(user_id=populated_wedding["user_id"],
                                         wedding_id=other.id, role="owner"))
            db.session.add_all([
                Guest(wedding_id=other.id, name="Bystander Guest"),
                Task(wedding_id=other.id, title="Bystander task",
                     due_date=datetime.utcnow() + timedelta(days=30)),
                Vendor(wedding_id=other.id, category="Baker",
                       business_name="Bystander Cakes"),
            ])
            bin_ = InventoryBin(wedding_id=other.id, label="Bystander bin")
            db.session.add(bin_)
            db.session.flush()
            db.session.add(InventoryItem(wedding_id=other.id, name="Bystander item",
                                         bin_id=bin_.id))
            db.session.commit()
            yield other.id

    def test_the_other_wedding_is_untouched(self, app, populated_wedding, bystander):
        with app.app_context():
            db.session.delete(Wedding.query.get(populated_wedding["wedding_id"]))
            db.session.commit()

        with app.app_context():
            assert Wedding.query.get(bystander) is not None
            assert row_count(Guest, wedding_id=bystander) == 1
            assert row_count(Task, wedding_id=bystander) == 1
            assert row_count(Vendor, wedding_id=bystander) == 1
            assert row_count(InventoryItem, wedding_id=bystander) == 1
            assert row_count(InventoryBin, wedding_id=bystander) == 1
            assert row_count(WeddingAccess, wedding_id=bystander) == 1


class TestDeletingThroughTheEndpoint:
    """The same thing, driven the way a user actually triggers it."""

    def test_the_route_removes_the_children_too(self, app, populated_client):
        client, populated = populated_client
        wid = populated["wedding_id"]

        response = client.post(f"/wedding/{wid}/delete")
        assert response.status_code == 302

        with app.app_context():
            assert Wedding.query.get(wid) is None
            assert row_count(Guest, wedding_id=wid) == 0
            assert row_count(Task, wedding_id=wid) == 0
            assert row_count(Comment, wedding_id=wid) == 0
