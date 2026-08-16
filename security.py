"""
Security middleware and utilities for the Wedding Planner application.

Provides:
- CSRF protection for all forms
- Rate limiting for auth and public endpoints
- HTTP security headers
- Input validation and sanitization
- Session security hardening
"""

import hmac
import re
import secrets
import time
from functools import wraps

from flask import abort, request, session


# ============================================
# CSRF PROTECTION
# ============================================

def generate_csrf_token():
    """Generate a CSRF token and store it in the session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_hex(32)
    return session['_csrf_token']


def validate_csrf_token():
    """Validate the CSRF token from the request against the session token."""
    if request.method in ('GET', 'HEAD', 'OPTIONS'):
        return True

    token = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
    session_token = session.get('_csrf_token')

    if not token or not session_token:
        return False

    return hmac.compare_digest(token, session_token)


# Endpoints that are intentionally public and don't use session auth.
#
# This is keyed by endpoint *name*, so renaming one of these handlers silently
# removes its exemption and starts rejecting real guests. test_csrf.py pins the
# set and asserts every name still resolves to a registered route.
CSRF_EXEMPT_ENDPOINTS = {
    'rsvp_portal', 'rsvp_submit', 'shared_view',
    'guest_identify', 'guest_checkin', 'guest_checkin_lookup',
    'static',
}


def init_csrf(app):
    """Initialize CSRF protection on the app.

    - Injects csrf_token() into all templates.
    - Validates CSRF tokens on all state-changing requests.
    - Exempts public endpoints that don't use session auth (RSVP, shared views).
    """
    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    @app.before_request
    def csrf_protect():
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return
        if request.endpoint in CSRF_EXEMPT_ENDPOINTS:
            return
        if not validate_csrf_token():
            abort(403, description='CSRF token missing or invalid.')


# ============================================
# RATE LIMITING
# ============================================

class RateLimiter:
    """Simple in-memory rate limiter using a sliding window.

    For production, replace with Redis-backed rate limiting.
    """

    def __init__(self):
        # key -> list of timestamps
        self._hits = {}
        self._last_cleanup = time.time()

    def _cleanup(self):
        """Remove expired entries periodically."""
        now = time.time()
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        cutoff = now - 3600  # keep 1 hour of data
        keys_to_delete = []
        for key, timestamps in self._hits.items():
            self._hits[key] = [t for t in timestamps if t > cutoff]
            if not self._hits[key]:
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self._hits[key]

    def is_rate_limited(self, key, max_requests, window_seconds):
        """Check if a key has exceeded its rate limit.

        Returns (is_limited, remaining, retry_after).
        """
        self._cleanup()
        now = time.time()
        cutoff = now - window_seconds

        if key not in self._hits:
            self._hits[key] = []

        # Remove old timestamps
        self._hits[key] = [t for t in self._hits[key] if t > cutoff]

        if len(self._hits[key]) >= max_requests:
            oldest = self._hits[key][0]
            retry_after = int(oldest + window_seconds - now) + 1
            return True, 0, retry_after

        self._hits[key].append(now)
        remaining = max_requests - len(self._hits[key])
        return False, remaining, 0


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limit(max_requests, window_seconds, key_func=None, methods=None):
    """Decorator to apply rate limiting to a route.

    Args:
        max_requests: Maximum number of requests allowed in the window.
        window_seconds: Time window in seconds.
        key_func: Optional function to compute the rate limit key.
                  Defaults to IP address + endpoint.
        methods: Optional collection of HTTP methods to count. Views that
                 serve a form on GET and process it on POST should pass
                 ('POST',), otherwise merely reloading the page burns the
                 budget and locks the visitor out of the form entirely.
                 Defaults to counting every method, which is what a GET-only
                 public endpoint wants.
    """
    counted_methods = {m.upper() for m in methods} if methods else None

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if counted_methods is not None and request.method not in counted_methods:
                return f(*args, **kwargs)

            if key_func:
                key = key_func()
            else:
                ip = request.remote_addr or 'unknown'
                key = f"rate:{ip}:{request.endpoint}"

            is_limited, remaining, retry_after = _rate_limiter.is_rate_limited(
                key, max_requests, window_seconds
            )

            if is_limited:
                abort(429, description=f'Too many requests. Please try again in {retry_after} seconds.')

            response = f(*args, **kwargs)
            return response
        return decorated_function
    return decorator


# ============================================
# SECURITY HEADERS
# ============================================

def init_security_headers(app):
    """Add security headers to all responses."""

    @app.after_request
    def set_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'

        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # Referrer policy - don't leak full URL to external sites
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Permissions policy - disable unnecessary browser features
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # Content Security Policy - restrict resource loading
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp

        # HSTS - enforce HTTPS (only effective over HTTPS)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response


# ============================================
# SESSION SECURITY
# ============================================

def init_session_security(app):
    """Harden session configuration."""
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Enable Secure flag when not in debug mode
    if not app.debug:
        app.config['SESSION_COOKIE_SECURE'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours


# ============================================
# INPUT VALIDATION
# ============================================

# Pre-compiled patterns
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
_PHONE_RE = re.compile(r'^[\d\s\-\+\(\)\.]{7,20}$')
_TIME_RE = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')
_TIME_AMPM_RE = re.compile(r'^([01]?\d):([0-5]\d)\s*(AM|PM|am|pm)$')


def sanitize_string(value, max_length=500):
    """Sanitize a string input: strip whitespace, enforce max length."""
    if not value:
        return ''
    value = str(value).strip()
    if len(value) > max_length:
        value = value[:max_length]
    return value


def validate_email(email):
    """Validate an email address format. Returns True if valid."""
    if not email:
        return False
    return bool(_EMAIL_RE.match(email))


def validate_phone(phone):
    """Validate a phone number format. Returns True if valid."""
    if not phone:
        return True  # phone is optional in most places
    return bool(_PHONE_RE.match(phone))


def validate_time_string(time_str):
    """Validate a time string in HH:MM or HH:MM AM/PM format.

    Returns a datetime.time object if valid, or None if invalid.
    Empty/None input returns None (time fields are optional).
    """
    if not time_str:
        return None
    time_str = str(time_str).strip()
    if not time_str:
        return None

    from datetime import datetime as _dt

    # Try 24-hour format first (HTML time inputs send HH:MM)
    m = _TIME_RE.match(time_str)
    if m:
        try:
            return _dt.strptime(time_str, '%H:%M').time()
        except ValueError:
            return None

    # Try 12-hour AM/PM format
    m = _TIME_AMPM_RE.match(time_str)
    if m:
        try:
            return _dt.strptime(time_str, '%I:%M %p').time()
        except ValueError:
            return None

    return None


def validate_name_pronunciation(text):
    """Validate and sanitize a name pronunciation field.

    Returns (is_valid, sanitized_value).
    Empty input is valid (field is optional).
    """
    if not text:
        return True, ''
    text = str(text).strip()
    if len(text) > 200:
        return False, ''
    # Strip HTML tags and control characters, keep letters, digits,
    # spaces, hyphens, apostrophes, periods, parentheses, slashes
    sanitized = re.sub(r'[<>&;]', '', text)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', sanitized)
    return True, sanitized


def validate_text_field(text, max_length=500, field_name='Field'):
    """Generic text field validator with length check and sanitization.

    Returns (is_valid, sanitized_value, error_message).
    Empty input is valid (returns empty string).
    """
    if not text:
        return True, '', ''
    text = str(text).strip()
    if len(text) > max_length:
        return False, '', f'{field_name} must be {max_length} characters or fewer.'
    # Strip HTML tags and control characters
    sanitized = re.sub(r'[<>&;]', '', text)
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', sanitized)
    return True, sanitized, ''


def validate_password_strength(password):
    """Validate password meets minimum security requirements.

    Returns (is_valid, error_message).
    """
    if not password:
        return False, 'Password is required.'
    if len(password) < 10:
        return False, 'Password must be at least 10 characters.'
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter.'
    if not re.search(r'[0-9]', password):
        return False, 'Password must contain at least one number.'
    return True, ''


# ============================================
# AUTHORIZATION
# ============================================

# Collaborator roles, least to most privileged. A user may act on a wedding when
# their role ranks at or above the level the endpoint requires.
#
#   viewer  - read the wedding
#   planner - read and edit everything under the wedding
#   owner   - additionally: delete the wedding, manage collaborators, and
#             publish it via RSVP/share links
#
# Enforcement lives in app.enforce_wedding_access(), a before_request hook that
# covers every route carrying a wedding_id. It is deliberately not a per-route
# decorator: a decorator has to be remembered on each of 300+ handlers, and the
# ones it was forgotten on are exactly where tenant isolation broke.
ROLE_HIERARCHY = {'viewer': 0, 'planner': 1, 'owner': 2}


# ============================================
# PUBLIC ENDPOINT SECURITY
# ============================================

def validate_rsvp_submission(wedding, form_data):
    """Validate RSVP form submission data.

    Returns (is_valid, errors, sanitized_data).
    """
    errors = []
    guest_name = sanitize_string(form_data.get('guest_name', ''), max_length=200)
    rsvp_status = form_data.get('rsvp_status', '')
    meal_choice = sanitize_string(form_data.get('meal_choice', ''), max_length=200)
    dietary = sanitize_string(form_data.get('dietary_restrictions', ''), max_length=500)
    rsvp_notes = sanitize_string(form_data.get('rsvp_notes', ''), max_length=1000)
    plus_one_name = sanitize_string(form_data.get('plus_one_name', ''), max_length=200)

    if not guest_name:
        errors.append('Guest name is required.')
    if rsvp_status not in ('accepted', 'declined', 'tentative'):
        errors.append('Invalid RSVP status.')
    if wedding.rsvp_deadline:
        from datetime import date
        if date.today() > wedding.rsvp_deadline:
            errors.append('The RSVP deadline has passed.')

    sanitized = {
        'guest_name': guest_name,
        'rsvp_status': rsvp_status,
        'meal_choice': meal_choice,
        'dietary': dietary,
        'rsvp_notes': rsvp_notes,
        'plus_one_name': plus_one_name,
    }

    return len(errors) == 0, errors, sanitized


# ============================================
# INITIALIZATION
# ============================================

def init_security(app):
    """Initialize all security features on the Flask app."""
    init_csrf(app)
    init_security_headers(app)
    init_session_security(app)

    # Warn if using default secret key
    secret_key = app.config.get('SECRET_KEY', '')
    if secret_key == 'dev-secret-key-change-in-production':
        import warnings
        warnings.warn(
            'WARNING: Using default SECRET_KEY. Set the SECRET_KEY environment '
            'variable to a secure random value in production.',
            stacklevel=2,
        )
