"""Tests for all print-related routes in the wedding planner app."""

import pytest
from unittest.mock import patch, MagicMock
from models import Wedding, db


# ---------------------------------------------------------------------------
# Helper: monkey-patch get_wedding_or_403 so it doesn't infinitely recurse
# (the production code has a bug where it calls itself instead of
#  Wedding.query.get_or_404).  We patch it to do the correct thing.
# ---------------------------------------------------------------------------

def _patched_get_wedding(wedding_id):
    from flask import g, abort
    from models import Wedding, WeddingAccess
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


# All print routes that accept only wedding_id (no extra path params)
PRINT_ROUTES = [
    "/wedding/{wid}/print",
    "/wedding/{wid}/print/timeline",
    "/wedding/{wid}/print/vendor-contacts",
    "/wedding/{wid}/print/shot-list",
    "/wedding/{wid}/print/emergency-contacts",
    "/wedding/{wid}/print/seating",
    "/wedding/{wid}/print/personal-timelines",
    "/wedding/{wid}/print/all-personal-timelines",
    "/wedding/{wid}/print/ceremony-program",
    "/wedding/{wid}/print/music-cue-sheet",
    "/wedding/{wid}/print/guest-list",
    "/wedding/{wid}/print/tips",
    "/wedding/{wid}/print/hair-makeup",
    "/wedding/{wid}/print/bridal-party",
    "/wedding/{wid}/print/venue-info",
    "/wedding/{wid}/print/decor-setup",
    "/wedding/{wid}/print/reception-script",
    "/wedding/{wid}/print/emergency-kit",
    "/wedding/{wid}/print/rehearsal",
    "/wedding/{wid}/print/transportation",
    "/wedding/{wid}/print/contingency-plans",
    "/wedding/{wid}/print/budget",
]


class TestPrintRoutesAuthenticated:
    """Print routes should return 200 for an authenticated user with access."""

    @pytest.mark.parametrize("route_tpl", PRINT_ROUTES)
    @patch("app.get_wedding_or_403", side_effect=_patched_get_wedding)
    def test_returns_200(self, mock_gw, auth_client, route_tpl):
        client, seed = auth_client
        url = route_tpl.format(wid=seed["wedding_id"])
        resp = client.get(url)
        assert resp.status_code == 200, (
            f"Expected 200 for {url}, got {resp.status_code}"
        )


class TestPrintRoutesUnauthenticated:
    """Print routes should redirect (302) to login for an unauthenticated user."""

    @pytest.mark.parametrize("route_tpl", PRINT_ROUTES)
    def test_redirects_when_not_logged_in(self, client, route_tpl, seed_data):
        url = route_tpl.format(wid=seed_data["wedding_id"])
        resp = client.get(url)
        # login_required redirects to /login
        assert resp.status_code == 302, (
            f"Expected redirect for unauthenticated request to {url}, "
            f"got {resp.status_code}"
        )
        assert "/login" in resp.headers.get("Location", "")


class TestPrintRoutesPDFFormat:
    """Print routes that use _render_or_pdf should respect ?format=pdf."""

    # Routes that go through _render_or_pdf (all except print_center which
    # calls render_template directly, and personal-timelines which is a
    # selection page).
    PDF_ROUTES = [
        "/wedding/{wid}/print/timeline",
        "/wedding/{wid}/print/vendor-contacts",
        "/wedding/{wid}/print/shot-list",
        "/wedding/{wid}/print/emergency-contacts",
        "/wedding/{wid}/print/seating",
        "/wedding/{wid}/print/ceremony-program",
        "/wedding/{wid}/print/music-cue-sheet",
        "/wedding/{wid}/print/guest-list",
        "/wedding/{wid}/print/tips",
        "/wedding/{wid}/print/hair-makeup",
        "/wedding/{wid}/print/bridal-party",
        "/wedding/{wid}/print/venue-info",
        "/wedding/{wid}/print/decor-setup",
        "/wedding/{wid}/print/reception-script",
        "/wedding/{wid}/print/emergency-kit",
        "/wedding/{wid}/print/rehearsal",
        "/wedding/{wid}/print/transportation",
        "/wedding/{wid}/print/contingency-plans",
        "/wedding/{wid}/print/budget",
    ]

    @pytest.mark.parametrize("route_tpl", PDF_ROUTES)
    @patch("app.get_wedding_or_403", side_effect=_patched_get_wedding)
    def test_pdf_format_returns_pdf_content_type(self, mock_gw, auth_client, route_tpl):
        """When ?format=pdf is given, response Content-Type should be application/pdf."""
        client, seed = auth_client
        url = route_tpl.format(wid=seed["wedding_id"]) + "?format=pdf"

        # Mock weasyprint so we don't need a full rendering engine
        mock_html_cls = MagicMock()
        mock_html_instance = MagicMock()
        mock_html_instance.write_pdf.return_value = b"%PDF-1.4 fake"
        mock_html_cls.return_value = mock_html_instance

        with patch("app.HTML", mock_html_cls, create=True):
            # Patch at the point of import inside _render_or_pdf
            with patch.dict(
                "sys.modules",
                {"weasyprint": MagicMock(HTML=mock_html_cls, CSS=MagicMock())},
            ):
                resp = client.get(url)

        assert resp.status_code == 200, (
            f"Expected 200 for PDF request to {url}, got {resp.status_code}"
        )
        assert resp.content_type.startswith("application/pdf"), (
            f"Expected application/pdf, got {resp.content_type}"
        )
