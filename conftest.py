"""Shared pytest fixtures for the wedding planner test suite."""

import pytest
from datetime import datetime, timedelta

from sqlalchemy.pool import StaticPool

from app import app as flask_app, seed_default_emergency_kit
from models import (
    db as _db, User, Wedding, WeddingAccess,
    Accommodation, AccessibilityItem, ActivityLog, Attire, BridalPartyMember,
    Budget, BudgetCategoryLimit, BudgetExpense, Ceremony, CeremonyReading,
    CeremonyTimelineItem, Comment, ContingencyPlan, CustomRsvpAnswer,
    CustomRsvpQuestion, DayOfContact, DayOfTask, DayOfTimelineItem,
    EmergencyKitItem, FloralItem, Gift, Guest, GuestGroup, HairMakeup,
    Honeymoon, HoneymoonItinerary, InventoryBin, InventoryItem, Invitation,
    MarriageLicense, MenuItem, NameChangeTask, PackingItem, PackingListItem,
    Person, PhotoShot, PreWeddingEvent, Reception, ReceptionTimelineItem,
    RegistryItem, RehearsalDinner, SeatingPreference, SeatingTable, SignageItem,
    SocialMediaSettings, Song, SpeechToast, Task, TipItem, TraditionalElement,
    VendorNote, VendorQuote, Vendor, VenueFixture, WeddingBranding,
    WeddingElement, WeddingFavor, WeddingParticipant,
)


@pytest.fixture(scope="session")
def app():
    """Create a Flask application configured for testing."""
    flask_app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        # Every new connection to sqlite:///:memory: gets its own empty database.
        # StaticPool pins the whole app to a single connection so tables created
        # in a fixture are still there when the request handler runs.
        SQLALCHEMY_ENGINE_OPTIONS={
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
        SECRET_KEY="test-secret-key",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )
    # Disable CSRF validation during tests by monkey-patching
    import security
    security._original_validate_csrf = security.validate_csrf_token
    security.validate_csrf_token = lambda: True

    yield flask_app


@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """Clear the in-memory rate limiter between tests.

    The limiter is a module-level singleton, so without this its hit counts
    accumulate across every test in the process. Enough requests to /login or
    /register in one run and later tests start getting 429s for reasons that
    have nothing to do with what they are asserting.
    """
    import security
    security._rate_limiter._hits.clear()
    yield
    security._rate_limiter._hits.clear()


@pytest.fixture(scope="function")
def database(app):
    """Create fresh database tables for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()


@pytest.fixture(scope="function")
def client(app, database):
    """A Flask test client with fresh database."""
    return app.test_client()


@pytest.fixture(scope="function")
def seed_data(app, database):
    """Create a test user, wedding, and wedding access record.

    Returns a dict with the created objects and their ids.
    """
    with app.app_context():
        user = User(
            email="test@example.com",
            name="Test User",
            user_type="self",
        )
        user.set_password("TestPassword1!")
        _db.session.add(user)
        _db.session.flush()

        wedding = Wedding(
            couple_names="Alice & Bob",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="couple@example.com",
        )
        _db.session.add(wedding)
        _db.session.flush()

        access = WeddingAccess(
            user_id=user.id,
            wedding_id=wedding.id,
            role="owner",
        )
        _db.session.add(access)
        _db.session.commit()

        data = {
            "user": user,
            "user_id": user.id,
            "wedding": wedding,
            "wedding_id": wedding.id,
        }
        yield data


@pytest.fixture(scope="function")
def auth_client(app, client, seed_data):
    """A test client that is already logged in as the test user."""
    with client.session_transaction() as sess:
        sess["user_id"] = seed_data["user_id"]
    return client, seed_data


def _make_user(email, name, user_type="self"):
    user = User(email=email, name=name, user_type=user_type)
    user.set_password("TestPassword1!")
    _db.session.add(user)
    _db.session.flush()
    return user


@pytest.fixture(scope="function")
def two_tenants(app, database):
    """Two unrelated users, each owning their own wedding.

    Used to prove tenant isolation: the 'outsider' has a valid account but no
    WeddingAccess row for the victim's wedding, so every wedding-scoped route
    must refuse them.
    """
    with app.app_context():
        victim = _make_user("victim@example.com", "Victim")
        outsider = _make_user("outsider@example.com", "Outsider")

        victim_wedding = Wedding(
            couple_names="Victim Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="victim-couple@example.com",
        )
        outsider_wedding = Wedding(
            couple_names="Outsider Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="outsider-couple@example.com",
        )
        _db.session.add_all([victim_wedding, outsider_wedding])
        _db.session.flush()

        _db.session.add_all([
            WeddingAccess(user_id=victim.id, wedding_id=victim_wedding.id, role="owner"),
            WeddingAccess(user_id=outsider.id, wedding_id=outsider_wedding.id, role="owner"),
        ])
        _db.session.commit()

        yield {
            "victim_id": victim.id,
            "victim_wedding_id": victim_wedding.id,
            "outsider_id": outsider.id,
            "outsider_wedding_id": outsider_wedding.id,
        }


@pytest.fixture(scope="function")
def outsider_client(client, two_tenants):
    """A logged-in client with no access to the victim's wedding."""
    with client.session_transaction() as sess:
        sess["user_id"] = two_tenants["outsider_id"]
    return client, two_tenants


@pytest.fixture(scope="function")
def populated_wedding(app, database):
    """A wedding carrying realistic data in every major module.

    The rest of the suite runs against weddings with no children at all, which
    means every list page, every total and every ``{% if items %}`` branch is
    only ever tested in its empty state. Three separate 500s have hidden there:
    two templates that only render their totals row once a record exists, and a
    calendar that only formats a date once something is dated.

    This fixture exists so those branches get exercised. When you add a module,
    add a row for it here.
    """
    with app.app_context():
        user = _make_user("populated@example.com", "Populated Owner")
        wedding = Wedding(
            couple_names="Populated Couple",
            wedding_date=datetime.utcnow() + timedelta(days=120),
            email="populated@example.com",
        )
        _db.session.add(wedding)
        _db.session.flush()
        _db.session.add(WeddingAccess(user_id=user.id, wedding_id=wedding.id, role="owner"))

        wid = wedding.id
        today = datetime.utcnow().date()
        soon = datetime.utcnow() + timedelta(days=14)

        ceremony = Ceremony(wedding_id=wid, venue_name="St Mary's", duration_minutes=45)
        reception = Reception(wedding_id=wid, venue_name="The Old Barn", venue_capacity=120)
        budget = Budget(wedding_id=wid, total_budget=32000.0)
        honeymoon = Honeymoon(wedding_id=wid, destination="Lisbon")
        _db.session.add_all([ceremony, reception, budget, honeymoon])
        _db.session.flush()

        # Ceremony / reception children
        _db.session.add_all([
            CeremonyTimelineItem(ceremony_id=ceremony.id, order=1, item_name="Processional"),
            CeremonyReading(ceremony_id=ceremony.id),
            ReceptionTimelineItem(reception_id=reception.id, order=1, item_name="First dance"),
            MenuItem(reception_id=reception.id, name="Roast chicken", course="main"),
            VenueFixture(reception_id=reception.id, fixture_type="dance_floor",
                         width_inches=180, height_inches=180),
        ])

        # Seating and guests. Half the guests are seated so both the assigned
        # and unassigned branches of the seating pages render.
        table_a = SeatingTable(reception_id=reception.id, table_number="1",
                               table_name="Table 1", capacity=8)
        table_b = SeatingTable(reception_id=reception.id, table_number="2",
                               table_name="Table 2", capacity=8)
        group = GuestGroup(wedding_id=wid, name="College Friends", seat_together=True)
        _db.session.add_all([table_a, table_b, group])
        _db.session.flush()

        guests = []
        for i in range(12):
            guest = Guest(
                wedding_id=wid,
                name=f"Guest {i:02d}",
                email=f"guest{i:02d}@example.com",
                rsvp_status="accepted" if i % 3 else "pending",
                meal_choice="chicken" if i % 2 else "fish",
                table_id=table_a.id if i < 6 else None,
                dietary_restrictions="vegetarian" if i == 4 else None,
            )
            guests.append(guest)
        _db.session.add_all(guests)
        _db.session.flush()

        # Budget: a mix of paid, part-paid and unpriced lines, so the None
        # branches of the money totals are covered too.
        _db.session.add_all([
            BudgetExpense(budget_id=budget.id, category="Venue", item_name="Barn hire",
                          estimated_cost=9000.0, actual_cost=9250.0, paid_amount=4000.0,
                          payment_due_date=today + timedelta(days=30),
                          payment_status="partial"),
            BudgetExpense(budget_id=budget.id, category="Catering", item_name="Dinner service",
                          estimated_cost=7000.0, actual_cost=None, paid_amount=0.0),
            BudgetExpense(budget_id=budget.id, category="Photography", item_name="Photographer",
                          estimated_cost=3200.0, actual_cost=3200.0, paid_amount=3200.0,
                          payment_status="paid"),
            BudgetCategoryLimit(budget_id=budget.id, category="Venue", limit_amount=10000.0),
        ])

        vendor = Vendor(wedding_id=wid, category="Florist", business_name="Acme Flowers",
                        contact_name="Sam Reed", email="sam@acme.example",
                        total_cost=2400.0, deposit_amount=600.0,
                        final_payment_date=today + timedelta(days=45),
                        contract_signed=True)
        _db.session.add(vendor)
        _db.session.flush()
        _db.session.add_all([
            VendorNote(vendor_id=vendor.id),
            VendorQuote(wedding_id=wid, category="Florist", vendor_name="Rival Blooms"),
        ])

        inventory_bin = InventoryBin(wedding_id=wid, label="Bin A", area="ceremony")
        _db.session.add(inventory_bin)
        _db.session.flush()
        _db.session.add(InventoryItem(wedding_id=wid, name="Candles", quantity=24,
                                      bin_id=inventory_bin.id))

        element = TraditionalElement(category="unity", name="Handfasting")
        _db.session.add(element)
        _db.session.flush()
        _db.session.add(WeddingElement(wedding_id=wid, element_id=element.id))

        _db.session.add_all([
            Person(wedding_id=wid, name="Alex Rivera"),
            Task(wedding_id=wid, title="Book the DJ", due_date=soon, category="vendors"),
            Task(wedding_id=wid, title="Send invitations", due_date=soon + timedelta(days=7),
                 completed=True),
            BridalPartyMember(wedding_id=wid, name="Jordan Lee", role="Maid of Honor"),
            WeddingParticipant(wedding_id=wid, name="Casey Kim"),
            WeddingBranding(wedding_id=wid),
            Attire(wedding_id=wid),
            RegistryItem(wedding_id=wid, item_name="Dutch oven", price=120.0),
            DayOfTimelineItem(wedding_id=wid, title="Hair and makeup", order=1),
            DayOfContact(wedding_id=wid, name="Riley Chen", role="Coordinator"),
            DayOfTask(wedding_id=wid, task="Set out place cards"),
            PhotoShot(wedding_id=wid, description="Couple with grandparents"),
            Song(wedding_id=wid, title="First Dance Song", moment="first_dance"),
            FloralItem(wedding_id=wid, item_type="bouquet"),
            Invitation(wedding_id=wid, item_type="save_the_date"),
            RehearsalDinner(wedding_id=wid),
            Accommodation(wedding_id=wid, accommodation_type="hotel", name="The Grand"),
            MarriageLicense(wedding_id=wid, county="Fairfax", state="VA"),
            HairMakeup(wedding_id=wid, person_name="Jordan Lee"),
            ContingencyPlan(wedding_id=wid, category="weather", title="Rain plan"),
            TipItem(wedding_id=wid, recipient="DJ", suggested_amount=150.0,
                    actual_amount=None),
            TipItem(wedding_id=wid, recipient="Officiant", suggested_amount=100.0,
                    actual_amount=100.0),
            Gift(wedding_id=wid, event="shower", from_name="Aunt Marta",
                 estimated_value=75.0),
            SpeechToast(wedding_id=wid, speaker_name="Jordan Lee", order=1),
            WeddingFavor(wedding_id=wid, description="Honey jars", quantity=120),
            PreWeddingEvent(wedding_id=wid, event_type="rehearsal_dinner",
                            name="Rehearsal Dinner"),
            SignageItem(wedding_id=wid, name="Welcome sign"),
            PackingListItem(wedding_id=wid, item_name="Vows notebook"),
            NameChangeTask(wedding_id=wid, task_name="Update passport"),
            AccessibilityItem(wedding_id=wid, item_name="Step-free entrance"),
            SocialMediaSettings(wedding_id=wid),
            EmergencyKitItem(wedding_id=wid, item_name="Safety pins"),
            ActivityLog(wedding_id=wid, action="created the wedding"),
            Comment(wedding_id=wid, user_id=user.id, entity_type="task", entity_id=1,
                    content="Chasing this one."),
        ])
        _db.session.flush()

        _db.session.add_all([
            HoneymoonItinerary(honeymoon_id=honeymoon.id, day_number=1, location="Lisbon"),
            PackingItem(honeymoon_id=honeymoon.id, item_name="Passport"),
            SeatingPreference(wedding_id=wid, guest_id=guests[0].id,
                              other_guest_id=guests[1].id, preference_type="together"),
        ])

        question = CustomRsvpQuestion(wedding_id=wid, question_text="Song request?")
        _db.session.add(question)
        _db.session.flush()
        _db.session.add(CustomRsvpAnswer(question_id=question.id, guest_id=guests[0].id))

        _db.session.commit()

        yield {
            "user_id": user.id,
            "wedding_id": wid,
            "guest_ids": [g.id for g in guests],
            "table_ids": [table_a.id, table_b.id],
            "vendor_id": vendor.id,
        }


@pytest.fixture(scope="function")
def populated_client(client, populated_wedding):
    """A logged-in client owning a wedding that has data in every module."""
    with client.session_transaction() as sess:
        sess["user_id"] = populated_wedding["user_id"]
    return client, populated_wedding


@pytest.fixture(scope="function")
def roles(app, database):
    """One wedding with an owner, a planner, and a viewer collaborator."""
    with app.app_context():
        owner = _make_user("owner@example.com", "Owner")
        planner = _make_user("planner@example.com", "Planner", "professional")
        viewer = _make_user("viewer@example.com", "Viewer")

        wedding = Wedding(
            couple_names="Role Test Couple",
            wedding_date=datetime.utcnow() + timedelta(days=90),
            email="roles@example.com",
        )
        _db.session.add(wedding)
        _db.session.flush()

        _db.session.add_all([
            WeddingAccess(user_id=owner.id, wedding_id=wedding.id, role="owner"),
            WeddingAccess(user_id=planner.id, wedding_id=wedding.id, role="planner"),
            WeddingAccess(user_id=viewer.id, wedding_id=wedding.id, role="viewer"),
        ])
        _db.session.commit()

        yield {
            "wedding_id": wedding.id,
            "owner_id": owner.id,
            "planner_id": planner.id,
            "viewer_id": viewer.id,
        }
