"""Tests for the emergency kit seeding functionality."""

import pytest
from unittest.mock import patch
from models import db, EmergencyKitItem, Wedding, WeddingAccess
from app import seed_default_emergency_kit, DEFAULT_EMERGENCY_KIT_ITEMS


# ---------------------------------------------------------------------------
# Patch helper (same as in test_print_routes)
# ---------------------------------------------------------------------------

def _patched_get_wedding(wedding_id):
    from flask import g, abort
    wedding = db.session.get(Wedding, wedding_id)
    if wedding is None:
        abort(404)
    user = g.get("user")
    if not user:
        abort(401)
    access = WeddingAccess.query.filter_by(
        user_id=user.id, wedding_id=wedding_id
    ).first()
    if not access:
        abort(403, description="You do not have access to this wedding.")
    g.wedding_role = access.role
    return wedding


EXPECTED_CATEGORIES = {"fashion", "health", "beauty", "tools", "food", "documents"}


class TestSeedDefaultEmergencyKit:
    """Tests for the seed_default_emergency_kit function."""

    def test_creates_items_in_all_categories(self, app, seed_data):
        """Seeding should create items across all 6 categories."""
        with app.app_context():
            wedding_id = seed_data["wedding_id"]
            seed_default_emergency_kit(wedding_id)

            items = EmergencyKitItem.query.filter_by(wedding_id=wedding_id).all()
            categories = {item.category for item in items}
            assert categories == EXPECTED_CATEGORIES

    def test_creates_expected_number_of_items(self, app, seed_data):
        """Seeding should create ~86 items (the sum of all default lists)."""
        with app.app_context():
            wedding_id = seed_data["wedding_id"]
            seed_default_emergency_kit(wedding_id)

            count = EmergencyKitItem.query.filter_by(wedding_id=wedding_id).count()
            expected = sum(
                len(items) for items in DEFAULT_EMERGENCY_KIT_ITEMS.values()
            )
            assert count == expected
            assert count == 86

    def test_items_have_correct_fields(self, app, seed_data):
        """Each seeded item should have item_name, category, and packed=False."""
        with app.app_context():
            wedding_id = seed_data["wedding_id"]
            seed_default_emergency_kit(wedding_id)

            items = EmergencyKitItem.query.filter_by(wedding_id=wedding_id).all()
            for item in items:
                assert item.item_name is not None and len(item.item_name) > 0
                assert item.category in EXPECTED_CATEGORIES
                assert item.packed is False

    def test_items_match_default_list(self, app, seed_data):
        """Seeded item names should match the DEFAULT_EMERGENCY_KIT_ITEMS dict."""
        with app.app_context():
            wedding_id = seed_data["wedding_id"]
            seed_default_emergency_kit(wedding_id)

            items = EmergencyKitItem.query.filter_by(wedding_id=wedding_id).all()
            # Build a set of (category, name) tuples from the DB
            db_pairs = {(item.category, item.item_name) for item in items}
            # Build the expected set from the constant
            expected_pairs = set()
            for category, names in DEFAULT_EMERGENCY_KIT_ITEMS.items():
                for name in names:
                    expected_pairs.add((category, name))
            assert db_pairs == expected_pairs

    def test_category_counts(self, app, seed_data):
        """Each category should have the correct number of items."""
        with app.app_context():
            wedding_id = seed_data["wedding_id"]
            seed_default_emergency_kit(wedding_id)

            for category, expected_items in DEFAULT_EMERGENCY_KIT_ITEMS.items():
                count = EmergencyKitItem.query.filter_by(
                    wedding_id=wedding_id, category=category
                ).count()
                assert count == len(expected_items), (
                    f"Category '{category}': expected {len(expected_items)}, got {count}"
                )


class TestEmergencyKitAutoSeed:
    """Test auto-seeding when viewing the emergency kit print page."""

    @patch("app.get_wedding_or_403", side_effect=_patched_get_wedding)
    def test_auto_seeds_on_first_view(self, mock_gw, app, auth_client):
        """Visiting the emergency-kit print page should auto-seed if no items exist."""
        client, seed = auth_client
        wedding_id = seed["wedding_id"]

        # Verify no items exist yet
        with app.app_context():
            assert EmergencyKitItem.query.filter_by(wedding_id=wedding_id).count() == 0

        # Visit the emergency kit page
        resp = client.get(f"/wedding/{wedding_id}/print/emergency-kit")
        assert resp.status_code == 200

        # Now items should have been created
        with app.app_context():
            count = EmergencyKitItem.query.filter_by(wedding_id=wedding_id).count()
            assert count == 86

    @patch("app.get_wedding_or_403", side_effect=_patched_get_wedding)
    def test_does_not_double_seed(self, mock_gw, app, auth_client):
        """Visiting the page twice should not duplicate items."""
        client, seed = auth_client
        wedding_id = seed["wedding_id"]

        # Visit twice
        client.get(f"/wedding/{wedding_id}/print/emergency-kit")
        client.get(f"/wedding/{wedding_id}/print/emergency-kit")

        with app.app_context():
            count = EmergencyKitItem.query.filter_by(wedding_id=wedding_id).count()
            assert count == 86
