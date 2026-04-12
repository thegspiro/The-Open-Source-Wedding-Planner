from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g, Response, make_response, abort
from models import (
    db, Wedding, Person, Task, Ceremony, CeremonyTimelineItem, CeremonyReading,
    Reception, ReceptionTimelineItem, MenuItem, SeatingTable, SeatingPreference, GuestGroup,
    Honeymoon, HoneymoonItinerary, PackingItem,
    WeddingBranding, BridalPartyMember, Guest,
    Budget, BudgetExpense, BudgetCategoryLimit, Vendor, RegistryItem, Attire, TraditionalElement,
    User, WeddingAccess,
    DayOfTimelineItem, PhotoShot, Song, FloralItem, Invitation,
    RehearsalDinner, Accommodation, MarriageLicense, HairMakeup,
    WeddingParticipant, timeline_assignments,
    ContingencyPlan, TipItem, Gift,
    VendorNote, VendorQuote, SpeechToast, WeddingFavor,
    ActivityLog, Comment,
    InventoryItem, InventoryBin, EmergencyKitItem,
    PreWeddingEvent, SignageItem, DayOfContact, DayOfTask,
    PackingListItem, NameChangeTask, CustomRsvpQuestion, CustomRsvpAnswer,
    AccessibilityItem, SocialMediaSettings,
    BUDGET_TEMPLATES, POST_WEDDING_TASKS, INVITATION_WORDING_TEMPLATES,
    TABLE_SIZE_REFERENCE, TABLE_ROLES, SUGGESTED_GROUP_TYPES, VenueFixture, VENUE_FIXTURE_TYPES,
    INVENTORY_CATEGORIES, INVENTORY_AREAS,
    PRE_WEDDING_EVENT_TYPES, DEFAULT_SIGNAGE_ITEMS, DEFAULT_DAY_OF_TASKS,
    DEFAULT_PACKING_LIST, DEFAULT_NAME_CHANGE_TASKS,
    HIDDEN_COST_REMINDERS, DEFAULT_ACCESSIBILITY_CHECKLIST,
    UNPLUGGED_CEREMONY_TEMPLATES, SOCIAL_SHARING_POLICIES
)
from flask_migrate import Migrate
from dotenv import load_dotenv
load_dotenv()

from datetime import datetime, timedelta, date
import os
import csv
import io
import logging
import secrets
from email_service import send_reminder_email, send_guest_email, send_pdf_email
import re
import threading
import time as time_module
import json
import math
from functools import wraps

logger = logging.getLogger(__name__)
from security import init_security, rate_limit, sanitize_string, validate_email, validate_phone, validate_password_strength, validate_rsvp_submission, validate_time_string, validate_name_pronunciation, validate_text_field

__version__ = '2.10.0'

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///wedding_organizer.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if app.config['SECRET_KEY'] in ('dev-secret-key-change-in-production', 'your-secret-key-change-in-production', 'change-me-to-a-random-secret-key'):
    import logging
    logging.warning(
        '*** WARNING: Using default SECRET_KEY. This is insecure for production! ***\n'
        '    Generate a key:  python3 -c "import secrets; print(secrets.token_hex(32))"\n'
        '    Then set it:     Copy .env.example to .env and update SECRET_KEY'
    )

db.init_app(app)
migrate = Migrate(app, db)

# Initialize security: CSRF protection, security headers, session hardening
init_security(app)


# Custom error handlers to prevent information leakage
@app.errorhandler(403)
def forbidden(e):
    flash(str(e.description) if hasattr(e, 'description') else 'Access denied.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(429)
def too_many_requests(e):
    flash(str(e.description) if hasattr(e, 'description') else 'Too many requests.', 'error')
    return redirect(request.referrer or url_for('index'))

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

# Health check endpoint for monitoring and container orchestration
@app.route('/health')
def health_check():
    try:
        db.session.execute(db.text('SELECT 1'))
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'database': str(e)}), 503


# Initialize database and seed traditional elements
# Note: db.create_all() is kept for initial setup / development convenience.
# For production schema changes, use Flask-Migrate: flask db migrate / flask db upgrade
with app.app_context():
    try:
        db.create_all()
    except Exception:
        pass

    # Seed traditional elements if none exist
    if TraditionalElement.query.count() == 0:
        traditional_elements = [
            # Ceremony Elements
            TraditionalElement(
                category='ceremony', subcategory='unity', name='Unity Candle',
                description='Two individual candles are lit by mothers, then bride and groom light a single unity candle together',
                origin='Christian tradition', typical_timing='During or after vows',
                what_you_need='Three candles (2 taper, 1 pillar), candle lighter, table',
                how_to_do_it='Mothers light taper candles at start. After vows, couple uses tapers to light unity candle together.'
            ),
            TraditionalElement(
                category='ceremony', subcategory='unity', name='Sand Ceremony',
                description='Two different colored sands are poured into one vessel, symbolizing two lives becoming one',
                origin='Hawaiian/Native American tradition', typical_timing='During or after vows',
                what_you_need='Three vessels, two different colored sands, small table',
                how_to_do_it='Couple simultaneously pours their individual sand into unity vessel, creating layered pattern.'
            ),
            TraditionalElement(
                category='ceremony', subcategory='ritual', name='Handfasting',
                description='Hands are tied together with cord or ribbon, symbolizing the binding of two lives',
                origin='Celtic/Pagan tradition', typical_timing='During vows',
                what_you_need='Cord, ribbon, or rope (often in wedding colors)',
                how_to_do_it='Officiant wraps cord around joined hands in figure-eight pattern while blessing the union.'
            ),
            TraditionalElement(
                category='ceremony', subcategory='ritual', name='Breaking the Glass',
                description='Groom breaks glass wrapped in cloth, symbolizing the fragility of relationships',
                origin='Jewish tradition', typical_timing='End of ceremony',
                what_you_need='Wine glass, cloth napkin',
                how_to_do_it='Glass wrapped in napkin, placed on ground, groom stomps on it. Guests shout "Mazel Tov!"'
            ),
            TraditionalElement(
                category='ceremony', subcategory='blessing', name='Rose Ceremony',
                description='Couple exchanges roses and makes personal promises',
                origin='Contemporary tradition', typical_timing='During ceremony',
                what_you_need='Two roses',
                how_to_do_it='Each person gives other a rose and speaks personal vows or promises.'
            ),
            
            # Reception Elements
            TraditionalElement(
                category='reception', subcategory='dance', name='First Dance',
                description='Newlyweds share their first dance as a married couple',
                origin='Universal tradition', typical_timing='After grand entrance or dinner',
                what_you_need='Selected song, cleared dance floor',
                how_to_do_it='DJ announces the dance, couple dances alone, then others join partway through.'
            ),
            TraditionalElement(
                category='reception', subcategory='dance', name='Parent Dances',
                description='Special dances with parents or important family members',
                origin='Western tradition', typical_timing='After first dance',
                what_you_need='Selected songs for each dance',
                how_to_do_it='Each person getting married dances with their chosen parent, guardian, or special person. Can be done simultaneously or one at a time. Customize to honor whoever is meaningful to you.'
            ),
            TraditionalElement(
                category='reception', subcategory='ritual', name='Cake Cutting',
                description='Couple cuts first slice of wedding cake together',
                origin='Roman tradition', typical_timing='During or after dinner',
                what_you_need='Wedding cake, cake knife, plates',
                how_to_do_it='Couple places hands on knife together, cuts first slice, feeds each other small bites.'
            ),
            TraditionalElement(
                category='reception', subcategory='ritual', name='Bouquet Toss',
                description='Tossing bouquet to assembled guests',
                origin='Medieval England', typical_timing='Late reception',
                what_you_need='Tossing bouquet (often smaller/separate)',
                how_to_do_it='Gather interested guests, person tosses bouquet backwards. Can be adapted to any guests regardless of gender or relationship status - whoever wants to participate!'
            ),
            TraditionalElement(
                category='reception', subcategory='ritual', name='Garter Toss',
                description='Removing and tossing garter to assembled guests',
                origin='French tradition', typical_timing='After bouquet toss',
                what_you_need='Wedding garter',
                how_to_do_it='One person removes garter, tosses to gathered guests. Traditional version was gendered, but can be adapted to any configuration or skipped entirely.'
            ),
            TraditionalElement(
                category='reception', subcategory='speech', name='Honor Attendant Toast',
                description='Special attendant gives speech honoring the couple',
                origin='Ancient Roman tradition', typical_timing='During dinner',
                what_you_need='Microphone, champagne for toasting',
                how_to_do_it='Honor attendant (best man, maid of honor, or any special person) shares stories, jokes, and well-wishes. Ends with raising glass for toast.'
            ),
            TraditionalElement(
                category='reception', subcategory='speech', name='Second Toast',
                description='Another special person gives toast',
                origin='Contemporary tradition', typical_timing='During dinner',
                what_you_need='Microphone, champagne for toasting',
                how_to_do_it='Second honor attendant or special person shares memories and sentiments. Ends with toast to the couple. Order and number of toasts is completely flexible!'
            ),
            TraditionalElement(
                category='reception', subcategory='ritual', name='Money Dance',
                description='Guests pin money to couple while dancing with them',
                origin='Various cultures (Dollar Dance)', typical_timing='Mid to late reception',
                what_you_need='Pins, collection bag, designated helpers',
                how_to_do_it='Guests pay to dance briefly with bride or groom. Money pinned to attire or placed in bag.'
            ),
            TraditionalElement(
                category='reception', subcategory='ritual', name='Grand Entrance',
                description='Wedding party and couple are announced entering reception',
                origin='Contemporary tradition', typical_timing='Start of reception',
                what_you_need='DJ/MC, upbeat music',
                how_to_do_it='Wedding party enters in pairs or however you prefer. Couple enters last to biggest applause. Make it your own - dance, walk, skip, whatever feels right!'
            ),
            
            # Cultural Traditions
            TraditionalElement(
                category='cultural', subcategory='ceremony', name='Tea Ceremony',
                description='Couple serves tea to elders to show respect',
                origin='Chinese tradition', typical_timing='Morning before ceremony or during reception',
                what_you_need='Tea set, special tea, small table',
                how_to_do_it='Couple kneels and serves tea to parents and elders. Recipients give red envelopes.'
            ),
            TraditionalElement(
                category='cultural', subcategory='ceremony', name='Jumping the Broom',
                description='Couple jumps over broom to symbolize sweeping away the past',
                origin='African American tradition', typical_timing='End of ceremony',
                what_you_need='Decorated broom',
                how_to_do_it='Broom laid on ground, couple joins hands and jumps over together as final ceremony act.'
            ),
            TraditionalElement(
                category='cultural', subcategory='ceremony', name='Lasso Ceremony',
                description='Rope or rosary placed around couple in figure-eight',
                origin='Mexican/Filipino tradition', typical_timing='During ceremony',
                what_you_need='Lasso (rope, rosary, or floral garland)',
                how_to_do_it='Sponsors place lasso around couple\'s shoulders during blessing, forming infinity symbol.'
            ),
            TraditionalElement(
                category='cultural', subcategory='reception', name='Hora Dance',
                description='Circle dance where couple is lifted on chairs',
                origin='Jewish tradition', typical_timing='Early reception',
                what_you_need='Sturdy chairs, strong dancers, napkin',
                how_to_do_it='Guests form circles, couple lifted on chairs holding napkin between them while circles dance.'
            ),
        ]
        
        db.session.bulk_save_objects(traditional_elements)
        db.session.commit()

# ============================================
# AUTH HELPERS
# ============================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)


@app.template_filter('from_json')
def from_json_filter(value):
    """Parse a JSON string into a Python object for use in templates."""
    if not value:
        return []
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return []


@app.context_processor
def inject_user():
    user = g.get('user')
    user_theme = user.theme if user and user.theme else 'rose'
    user_dark_mode = user.dark_mode if user else False
    return dict(current_user=user, user_theme=user_theme, user_dark_mode=user_dark_mode)


def log_activity(wedding_id, action, entity_type, entity_name='', details=''):
    """Log an activity for the audit trail."""
    user = g.get('user')
    entry = ActivityLog(
        wedding_id=wedding_id,
        user_id=user.id if user else None,
        user_name=user.name if user else 'System',
        action=action,
        entity_type=entity_type,
        entity_name=entity_name,
        details=details
    )
    db.session.add(entry)


def generate_token():
    """Generate a secure random token."""
    return secrets.token_urlsafe(32)


def get_user_weddings(user):
    """Get weddings accessible to the current user."""
    access_records = WeddingAccess.query.filter_by(user_id=user.id).all()
    wedding_ids = [a.wedding_id for a in access_records]
    return Wedding.query.filter(Wedding.id.in_(wedding_ids)).order_by(Wedding.wedding_date).all()


def get_wedding_or_403(wedding_id):
    """Get a wedding, checking that the current user has access.

    Aborts with 403 if the user does not have access.
    """
    wedding = Wedding.query.get_or_404(wedding_id)
    user = g.get('user')
    if not user:
        abort(401)
    access = WeddingAccess.query.filter_by(user_id=user.id, wedding_id=wedding_id).first()
    if not access:
        abort(403, description='You do not have access to this wedding.')
    g.wedding_role = access.role
    return wedding


def get_entity_or_404(model, entity_id, wedding_id):
    """Get a child entity by ID, verifying it belongs to the given wedding.

    Aborts with 404 if the entity does not exist or does not belong to the wedding.
    """
    entity = model.query.get_or_404(entity_id)
    if hasattr(entity, 'wedding_id') and entity.wedding_id != wedding_id:
        abort(404)
    return entity


def safe_strptime(value, fmt, default=None):
    """Safely parse a datetime string, returning default on failure."""
    if not value:
        return default
    try:
        return datetime.strptime(value, fmt)
    except (ValueError, TypeError):
        return default


# ============================================
# DEFAULT EMERGENCY KIT ITEMS
# ============================================

DEFAULT_EMERGENCY_KIT_ITEMS = {
    'fashion': [
        'Safety pins (assorted sizes)',
        'Sewing kit (needle, white & black thread)',
        'Fashion tape (double-sided)',
        'Stain remover pen',
        'Static guard spray',
        'Lint roller',
        'Wrinkle release spray',
        'Extra buttons (matching attire)',
        'Shoe insoles / heel protectors',
        'Clear nail polish (stop stocking runs)',
        'Hem tape',
        'Shoe polish / white shoe touch-up',
    ],
    'health': [
        'Pain relievers (ibuprofen, acetaminophen)',
        'Antacid tablets',
        'Anti-nausea medication',
        'Allergy medication (antihistamines)',
        'Band-aids (assorted sizes)',
        'Blister pads / moleskin',
        'Eye drops',
        'Breath mints / gum',
        'Throat lozenges',
        'Tissues (travel packs)',
        'Hand sanitizer',
        'Sunscreen (SPF 30+)',
        'Bug spray',
        'Tampons / pads',
        'Deodorant',
        'Tweezers',
        'Nail clippers',
        'Contact lens solution / spare contacts',
        'Hydrocortisone cream',
        'Electrolyte packets',
    ],
    'beauty': [
        'Bobby pins & hair pins',
        'Hair ties & clips',
        'Hairspray (travel size)',
        'Dry shampoo',
        'Makeup blotting papers',
        'Lipstick / lip gloss (matching shade)',
        'Powder compact / setting spray',
        'Concealer',
        'Cotton swabs & cotton pads',
        'Makeup remover wipes',
        'Perfume / cologne (travel size)',
        'Nail file & nail glue',
        'Eyelash glue',
        'Compact mirror',
        'Disposable razor',
    ],
    'tools': [
        'Scissors',
        'Super glue',
        'Duct tape / gaffer tape',
        'White chalk (for scuff marks)',
        'Pen and notepad',
        'Permanent marker',
        'Phone charger / portable battery',
        'Extension cord / power strip',
        'Umbrella(s)',
        'Flashlight',
        'Zip ties',
        'Rubber bands',
        'Command strips / hooks',
        'Floral wire & floral tape',
        'Trash bags',
        'Paper towels',
        'Baby wipes',
        'Lighter or matches',
        'Batteries (AA / AAA)',
    ],
    'food': [
        'Water bottles',
        'Granola bars / protein bars',
        'Straws (to drink without smudging lipstick)',
        'Mints for the couple',
        'Ginger chews (for nausea)',
        'Electrolyte drinks',
    ],
    'documents': [
        'Marriage license',
        'Vendor contact list',
        'Day-of timeline copies',
        'Rings',
        'Vow cards / notes',
        'Cash for tips (labeled envelopes)',
        'ID / wallet',
        'Insurance cards',
        'Hotel room key',
        'Emergency contact list',
        'Copies of vendor contracts',
        'Seating chart copy',
        'Spare car keys',
        'Checkbook (final vendor payments)',
    ],
}


def seed_default_emergency_kit(wedding_id):
    """Create default emergency kit items for a wedding."""
    for category, items in DEFAULT_EMERGENCY_KIT_ITEMS.items():
        for item_name in items:
            kit_item = EmergencyKitItem(
                wedding_id=wedding_id,
                item_name=item_name,
                category=category,
                packed=False
            )
            db.session.add(kit_item)
    db.session.commit()


# ============================================
# AUTH ROUTES
# ============================================

@app.route('/register', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window_seconds=3600)
def register():
    if g.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        user_type = request.form.get('user_type', '')

        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        pw_valid, pw_error = validate_password_strength(password)
        if not pw_valid:
            errors.append(pw_error)
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if user_type not in ('professional', 'friend', 'self'):
            errors.append('Please select how you will use the app.')

        if User.query.filter_by(email=email).first():
            errors.append('An account with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html',
                                   name=name, email=email, user_type=user_type)

        user = User(name=name, email=email, user_type=user_type)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id
        flash(f'Welcome, {user.name}! Your account has been created.', 'success')
        return redirect(url_for('index'))

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
@rate_limit(max_requests=10, window_seconds=300)
def login():
    if g.get('user'):
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash('Invalid email or password.', 'error')
            return render_template('auth/login.html', email=email)

        session['user_id'] = user.id
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('index'))

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


# ============================================
# USER SETTINGS
# ============================================

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def user_settings():
    user = g.user
    if request.method == 'POST':
        # Theme color
        theme = request.form.get('theme', 'rose')
        if theme in ('rose', 'sage', 'ocean', 'lavender'):
            user.theme = theme

        # Dark mode
        user.dark_mode = request.form.get('dark_mode') == 'on'

        # Profile fields
        name = request.form.get('name', '').strip()
        if name:
            user.name = name

        db.session.commit()
        flash('Settings saved!', 'success')
        return redirect(url_for('user_settings'))

    return render_template('settings.html', user=user)


# ============================================
# MAIN ROUTES
# ============================================

@app.route('/version')
def app_version():
    return {'version': __version__}

@app.route('/')
@login_required
def index():
    user = g.user
    weddings = get_user_weddings(user)

    # Self-planners with exactly one wedding go straight to dashboard
    if user.user_type == 'self' and len(weddings) == 1:
        return redirect(url_for('wedding_dashboard', wedding_id=weddings[0].id))

    return render_template('index.html', weddings=weddings, user=user)

@app.route('/wedding/new', methods=['GET', 'POST'])
@login_required
def new_wedding():
    user = g.user

    # Self-planners can only have one wedding
    if user.user_type == 'self':
        existing = get_user_weddings(user)
        if existing:
            flash('You already have a wedding set up!', 'info')
            return redirect(url_for('wedding_dashboard', wedding_id=existing[0].id))

    if request.method == 'POST':
        num_people = int(request.form.get('num_people', 2))
        names = []
        for i in range(num_people):
            name = request.form.get(f'person_{i}_name', '').strip()
            if name:
                names.append(name)

        # Auto-generate couple_names display string from individual names
        if len(names) == 2:
            couple_names = f'{names[0]} & {names[1]}'
        else:
            couple_names = ', '.join(names[:-1]) + f' & {names[-1]}' if len(names) > 1 else names[0] if names else 'Wedding'

        wedding_date = safe_strptime(request.form.get('wedding_date'), '%Y-%m-%d')
        if not wedding_date:
            flash('Please provide a valid wedding date.', 'error')
            return redirect(request.referrer or url_for('index'))
        email = request.form['email']

        wedding = Wedding(
            couple_names=couple_names,
            wedding_date=wedding_date,
            email=email,
            onboarding_completed=False
        )
        db.session.add(wedding)
        db.session.commit()

        # Create Person records from names collected at creation
        for i, name in enumerate(names):
            person = Person(
                wedding_id=wedding.id,
                name=name,
                display_order=i + 1
            )
            db.session.add(person)
        db.session.commit()

        # Give the current user owner access
        access = WeddingAccess(user_id=user.id, wedding_id=wedding.id, role='owner')
        db.session.add(access)
        db.session.commit()

        # Pre-populate emergency kit with common items
        seed_default_emergency_kit(wedding.id)

        flash(f'Wedding created! Let\'s set up some details.', 'success')
        return redirect(url_for('onboarding_step2', wedding_id=wedding.id))

    return render_template('new_wedding.html')

# ============================================
# ONBOARDING FLOW
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/step1', methods=['GET', 'POST'])
@login_required
def onboarding_step1(wedding_id):
    """Step 1: Redirect to step 2 - people are now created at wedding creation."""
    get_wedding_or_403(wedding_id)
    return redirect(url_for('onboarding_step2', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/onboarding/step2', methods=['GET', 'POST'])
@login_required
def onboarding_step2(wedding_id):
    """Step 2: Collect additional details for each person (names already set at creation)"""
    wedding = get_wedding_or_403(wedding_id)

    people = Person.query.filter_by(wedding_id=wedding_id).order_by(Person.display_order).all()

    if request.method == 'POST':
        # Update existing Person records with additional details
        for i, person in enumerate(people):
            title = request.form.get(f'person_{i}_title')
            pronouns = request.form.get(f'person_{i}_pronouns')
            side_label = request.form.get(f'person_{i}_side_label')

            person.title = title if title != 'other' else request.form.get(f'person_{i}_title_custom')
            person.preferred_pronouns = pronouns if pronouns != 'other' else request.form.get(f'person_{i}_pronouns_custom')
            person.side_label = side_label

        db.session.commit()

        # Mark people module as complete
        modules = json.loads(wedding.modules_completed or '[]')
        if 'people' not in modules:
            modules.append('people')
            wedding.modules_completed = json.dumps(modules)
            db.session.commit()

        return redirect(url_for('onboarding_step3', wedding_id=wedding_id))

    return render_template('onboarding/step2.html', wedding=wedding, people=people)

@app.route('/wedding/<int:wedding_id>/onboarding/step3', methods=['GET', 'POST'])
@login_required
def onboarding_step3(wedding_id):
    """Step 3: Customize terminology and preferences"""
    wedding = get_wedding_or_403(wedding_id)
    people = Person.query.filter_by(wedding_id=wedding_id).order_by(Person.display_order).all()
    
    if request.method == 'POST':
        # Store preferences
        wedding_party_term = request.form.get('wedding_party_term', 'Wedding Party')
        processional_term = request.form.get('processional_term', 'Processional')
        
        # Save to preferences
        prefs = {
            'wedding_party_term': wedding_party_term,
            'processional_term': processional_term
        }
        wedding.onboarding_preferences = json.dumps(prefs)
        db.session.commit()
        
        # Initialize modules
        if not wedding.ceremony:
            ceremony = Ceremony(wedding_id=wedding.id)
            db.session.add(ceremony)
        if not wedding.reception:
            reception = Reception(wedding_id=wedding.id)
            db.session.add(reception)
        if not wedding.honeymoon:
            honeymoon = Honeymoon(wedding_id=wedding.id)
            db.session.add(honeymoon)
        if not wedding.branding:
            branding = WeddingBranding(wedding_id=wedding.id)
            db.session.add(branding)
        if not wedding.budget:
            budget = Budget(wedding_id=wedding.id, total_budget=0)
            db.session.add(budget)
        
        db.session.commit()
        
        flash('Initial setup complete! Now let\'s set up your wedding modules.', 'success')
        return redirect(url_for('onboarding_hub', wedding_id=wedding_id))
    
    return render_template('onboarding/step3.html', wedding=wedding, people=people)

# ============================================
# ONBOARDING HUB
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/hub')
@login_required
def onboarding_hub(wedding_id):
    """Central hub for module-by-module onboarding"""
    wedding = get_wedding_or_403(wedding_id)
    modules_completed = json.loads(wedding.modules_completed or '[]')
    return render_template('onboarding/hub.html', wedding=wedding, modules_completed=modules_completed)

# ============================================
# CEREMONY ONBOARDING
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/start', methods=['GET', 'POST'])
@login_required
def onboarding_ceremony_start(wedding_id):
    """Ceremony onboarding - choose ceremony type"""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('onboarding/modules/ceremony_start.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/templates', methods=['GET', 'POST'])
@login_required
def onboarding_ceremony_templates(wedding_id):
    """Show ceremony templates based on type selected"""
    wedding = get_wedding_or_403(wedding_id)
    ceremony_type = request.form.get('ceremony_type') or request.args.get('ceremony_type')
    
    # Save preference
    prefs = json.loads(wedding.onboarding_preferences or '{}')
    prefs['ceremony_type'] = ceremony_type
    wedding.onboarding_preferences = json.dumps(prefs)
    db.session.commit()
    
    # Import templates
    from templates_data import CEREMONY_TEMPLATES
    
    # Filter templates by type
    filtered_templates = {k: v for k, v in CEREMONY_TEMPLATES.items() 
                         if v.get('category') == ceremony_type or 
                         (ceremony_type == 'civil' and k == 'courthouse') or
                         (ceremony_type == 'spiritual' and v.get('category') in ['secular', 'religious'])}
    
    return render_template('onboarding/modules/ceremony_templates.html', 
                         wedding=wedding, 
                         ceremony_type=ceremony_type,
                         templates=filtered_templates)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/template/<template_key>/preview')
@login_required
def onboarding_ceremony_template_preview(wedding_id, template_key):
    """Preview a specific ceremony template"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import CEREMONY_TEMPLATES
    
    template = CEREMONY_TEMPLATES.get(template_key)
    if not template:
        flash('Template not found', 'error')
        return redirect(url_for('onboarding_ceremony_start', wedding_id=wedding_id))
    
    return render_template('onboarding/modules/ceremony_template_preview.html',
                         wedding=wedding,
                         template_key=template_key,
                         template=template)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/template/<template_key>/apply', methods=['POST'])
@login_required
def onboarding_ceremony_template_apply(wedding_id, template_key):
    """Apply a ceremony template"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import CEREMONY_TEMPLATES
    
    template = CEREMONY_TEMPLATES.get(template_key)
    if not template:
        flash('Template not found', 'error')
        return redirect(url_for('onboarding_ceremony_start', wedding_id=wedding_id))
    
    ceremony = wedding.ceremony
    
    # Apply template data
    ceremony.ceremony_style = template.get('category', 'secular')
    ceremony.duration_minutes = template.get('typical_duration', 30)
    
    # Apply timeline
    if 'timeline' in template:
        # Clear existing timeline items
        CeremonyTimelineItem.query.filter_by(ceremony_id=ceremony.id).delete()
        
        for item in template['timeline']:
            timeline_item = CeremonyTimelineItem(
                ceremony_id=ceremony.id,
                order=item['order'],
                item_name=item['name'],
                duration_seconds=item.get('duration', 0),
                description=item.get('description', '')
            )
            db.session.add(timeline_item)
    
    # Apply music suggestions
    if 'music_suggestions' in template and template['music_suggestions']:
        ceremony.processional_song = template['music_suggestions'].get('processional', '')
        ceremony.recessional_song = template['music_suggestions'].get('recessional', '')
    
    # Apply unity ceremony if specified
    if 'unity_ceremony' in template:
        ceremony.has_unity_ceremony = True
        ceremony.unity_ceremony_type = template['unity_ceremony']
    
    db.session.commit()
    
    flash('Template applied! Now you can customize it.', 'success')
    return redirect(url_for('onboarding_ceremony_customize', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/custom')
@login_required
def onboarding_ceremony_custom(wedding_id):
    """Start custom ceremony setup with questions"""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('onboarding/modules/ceremony_custom_start.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/customize', methods=['GET', 'POST'])
@login_required
def onboarding_ceremony_customize(wedding_id):
    """Customize ceremony details after template or custom setup"""
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    
    if request.method == 'POST':
        # Save basic ceremony details
        ceremony.venue_name = request.form.get('venue_name')
        ceremony.venue_address = request.form.get('venue_address')
        
        # Parse time
        if request.form.get('start_time'):
            ceremony.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        
        ceremony.duration_minutes = request.form.get('duration_minutes', type=int)
        ceremony.officiant_name = request.form.get('officiant_name')
        ceremony.officiant_type = request.form.get('officiant_type')
        
        db.session.commit()
        
        # Mark ceremony as complete
        modules = json.loads(wedding.modules_completed or '[]')
        if 'ceremony' not in modules:
            modules.append('ceremony')
            wedding.modules_completed = json.dumps(modules)
            db.session.commit()
        
        flash('Ceremony setup complete!', 'success')
        return redirect(url_for('onboarding_hub', wedding_id=wedding_id))
    
    timeline_items = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony else []
    
    return render_template('onboarding/modules/ceremony_customize.html',
                         wedding=wedding,
                         ceremony=ceremony,
                         timeline_items=timeline_items)

@app.route('/wedding/<int:wedding_id>/onboarding/people', methods=['GET', 'POST'])
@login_required
def onboarding_people(wedding_id):
    """Quick people setup from hub"""
    wedding = get_wedding_or_403(wedding_id)
    
    # If people already exist, just mark as complete and redirect
    if wedding.people:
        modules = json.loads(wedding.modules_completed or '[]')
        if 'people' not in modules:
            modules.append('people')
            wedding.modules_completed = json.dumps(modules)
            db.session.commit()
        return redirect(url_for('people_view', wedding_id=wedding_id))
    
    # Otherwise redirect to step 1
    return redirect(url_for('onboarding_step1', wedding_id=wedding_id))

# ============================================
# RECEPTION ONBOARDING
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/reception/start', methods=['GET', 'POST'])
@login_required
def onboarding_reception_start(wedding_id):
    """Reception onboarding - choose a reception style"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import RECEPTION_TEMPLATES

    if request.method == 'POST':
        template_key = request.form.get('template_key')
        template = RECEPTION_TEMPLATES.get(template_key)
        if not template:
            flash('Please select a reception style.', 'error')
            return redirect(url_for('onboarding_reception_start', wedding_id=wedding_id))

        reception = wedding.reception
        if template_key == 'no_reception':
            prefs = json.loads(wedding.onboarding_preferences or '{}')
            prefs['reception_style'] = 'none'
            wedding.onboarding_preferences = json.dumps(prefs)
            modules = json.loads(wedding.modules_completed or '[]')
            if 'reception' not in modules:
                modules.append('reception')
                wedding.modules_completed = json.dumps(modules)
            db.session.commit()
            flash('Got it - no formal reception. You can always add one later!', 'success')
            return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

        if 'timeline' in template:
            ReceptionTimelineItem.query.filter_by(reception_id=reception.id).delete()
            for item in template['timeline']:
                timeline_item = ReceptionTimelineItem(
                    reception_id=reception.id,
                    order=item['order'],
                    item_name=item['name'],
                    duration_seconds=item.get('duration', 0),
                    description=item.get('description', '')
                )
                db.session.add(timeline_item)

        prefs = json.loads(wedding.onboarding_preferences or '{}')
        prefs['reception_style'] = template_key
        wedding.onboarding_preferences = json.dumps(prefs)
        db.session.commit()

        return redirect(url_for('onboarding_reception_customize', wedding_id=wedding_id))

    return render_template('onboarding/modules/reception_start.html',
                         wedding=wedding, templates=RECEPTION_TEMPLATES)


@app.route('/wedding/<int:wedding_id>/onboarding/reception/customize', methods=['GET', 'POST'])
@login_required
def onboarding_reception_customize(wedding_id):
    """Customize reception details after choosing a style"""
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception

    if request.method == 'POST':
        reception.venue_name = request.form.get('venue_name')
        reception.venue_address = request.form.get('venue_address')
        if request.form.get('expected_guest_count'):
            reception.expected_guest_count = int(request.form.get('expected_guest_count'))
        if request.form.get('start_time'):
            reception.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()

        db.session.commit()

        modules = json.loads(wedding.modules_completed or '[]')
        if 'reception' not in modules:
            modules.append('reception')
            wedding.modules_completed = json.dumps(modules)
            db.session.commit()

        flash('Reception setup complete!', 'success')
        return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

    timeline_items = sorted(reception.timeline_items, key=lambda x: x.order) if reception else []
    return render_template('onboarding/modules/reception_customize.html',
                         wedding=wedding, reception=reception, timeline_items=timeline_items)


# ============================================
# BUDGET ONBOARDING
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/budget/start', methods=['GET', 'POST'])
@login_required
def onboarding_budget_start(wedding_id):
    """Budget onboarding - pick a budget tier or set custom"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import BUDGET_TEMPLATES

    if request.method == 'POST':
        template_key = request.form.get('template_key')
        custom_budget = request.form.get('custom_budget')

        budget = wedding.budget

        if template_key and template_key != 'custom':
            template = BUDGET_TEMPLATES.get(template_key)
            if template:
                budget.total_budget = template['total']
                BudgetExpense.query.filter_by(budget_id=budget.id).delete()
                for exp in template.get('expenses', []):
                    expense = BudgetExpense(
                        budget_id=budget.id,
                        item_name=exp['category'] + ' (estimated)',
                        estimated_cost=exp['amount'],
                        category=exp['category'],
                        payment_status='unpaid'
                    )
                    db.session.add(expense)

                prefs = json.loads(wedding.onboarding_preferences or '{}')
                prefs['budget_tier'] = template_key
                wedding.onboarding_preferences = json.dumps(prefs)
        elif custom_budget:
            try:
                budget.total_budget = float(custom_budget)
            except ValueError:
                flash('Please enter a valid number for your budget.', 'error')
                return redirect(url_for('onboarding_budget_start', wedding_id=wedding_id))
            prefs = json.loads(wedding.onboarding_preferences or '{}')
            prefs['budget_tier'] = 'custom'
            wedding.onboarding_preferences = json.dumps(prefs)

        modules = json.loads(wedding.modules_completed or '[]')
        if 'budget' not in modules:
            modules.append('budget')
            wedding.modules_completed = json.dumps(modules)

        db.session.commit()
        flash('Budget setup complete!', 'success')
        return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

    return render_template('onboarding/modules/budget_start.html',
                         wedding=wedding, templates=BUDGET_TEMPLATES)


# ============================================
# GUEST LIST ONBOARDING
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/guests/start', methods=['GET', 'POST'])
@login_required
def onboarding_guests_start(wedding_id):
    """Guest list quick-setup - estimate count and add key guests"""
    wedding = get_wedding_or_403(wedding_id)

    if request.method == 'POST':
        estimated_count = request.form.get('estimated_count')
        prefs = json.loads(wedding.onboarding_preferences or '{}')
        prefs['estimated_guest_count'] = int(estimated_count) if estimated_count else 0
        wedding.onboarding_preferences = json.dumps(prefs)

        guest_names = request.form.getlist('guest_name')
        guest_sides = request.form.getlist('guest_side')
        for i, name in enumerate(guest_names):
            name = name.strip()
            if name:
                side = guest_sides[i] if i < len(guest_sides) else ''
                guest = Guest(
                    wedding_id=wedding_id,
                    name=name,
                    side=side,
                    rsvp_status='pending'
                )
                db.session.add(guest)

        modules = json.loads(wedding.modules_completed or '[]')
        if 'guests' not in modules:
            modules.append('guests')
            wedding.modules_completed = json.dumps(modules)

        db.session.commit()
        flash('Guest list started! You can add more guests anytime.', 'success')
        return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

    people = wedding.people
    return render_template('onboarding/modules/guests_start.html',
                         wedding=wedding, people=people)


# ============================================
# AUTO-GENERATE PLANNING TASKS
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/generate-tasks', methods=['GET', 'POST'])
@login_required
def onboarding_generate_tasks(wedding_id):
    """Generate planning milestone tasks based on wedding date"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import PLANNING_MILESTONE_TASKS

    if request.method == 'POST':
        selected_tasks = request.form.getlist('task_ids')
        wedding_date = wedding.wedding_date
        today_dt = date.today()
        count = 0

        for idx_str in selected_tasks:
            idx = int(idx_str)
            if idx < len(PLANNING_MILESTONE_TASKS):
                title, description, category, priority, months_before = PLANNING_MILESTONE_TASKS[idx]
                due_date = wedding_date - timedelta(days=months_before * 30)
                if due_date.date() < today_dt:
                    due_date = datetime.combine(today_dt + timedelta(days=7), datetime.min.time())

                task = Task(
                    wedding_id=wedding_id,
                    title=title,
                    description=description,
                    due_date=due_date,
                    priority=priority,
                    category=category,
                    months_before=months_before,
                    is_milestone=True
                )
                db.session.add(task)
                count += 1

        prefs = json.loads(wedding.onboarding_preferences or '{}')
        prefs['tasks_generated'] = True
        wedding.onboarding_preferences = json.dumps(prefs)

        db.session.commit()
        flash(f'{count} planning tasks added to your task list!', 'success')
        return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

    wedding_date = wedding.wedding_date
    today_dt = date.today()
    months_until = max(0, (wedding_date.year - today_dt.year) * 12 + wedding_date.month - today_dt.month)

    task_groups = {}
    period_order = ['12+ Months Before', '10-11 Months Before', '8-9 Months Before',
                    '6-7 Months Before', '4-5 Months Before', '2-3 Months Before', 'Final Month']
    for idx, (title, description, category, priority, months_before) in enumerate(PLANNING_MILESTONE_TASKS):
        if months_before <= 1:
            period = 'Final Month'
        elif months_before <= 3:
            period = '2-3 Months Before'
        elif months_before <= 5:
            period = '4-5 Months Before'
        elif months_before <= 7:
            period = '6-7 Months Before'
        elif months_before <= 9:
            period = '8-9 Months Before'
        elif months_before <= 11:
            period = '10-11 Months Before'
        else:
            period = '12+ Months Before'

        if period not in task_groups:
            task_groups[period] = []

        due_date = wedding_date - timedelta(days=months_before * 30)
        is_overdue = due_date.date() < today_dt

        task_groups[period].append({
            'idx': idx,
            'title': title,
            'description': description,
            'category': category,
            'priority': priority,
            'months_before': months_before,
            'is_overdue': is_overdue,
        })

    existing_milestones = Task.query.filter_by(wedding_id=wedding_id, is_milestone=True).count()

    return render_template('onboarding/modules/generate_tasks.html',
                         wedding=wedding,
                         task_groups=task_groups,
                         period_order=period_order,
                         months_until=months_until,
                         existing_milestones=existing_milestones)

@app.route('/wedding/<int:wedding_id>/onboarding/reset', methods=['POST'])
def onboarding_reset(wedding_id):
    """Reset onboarding progress so user can redo setup modules"""
    wedding = get_wedding_or_403(wedding_id)
    wedding.modules_completed = json.dumps([])
    db.session.commit()
    flash('Onboarding progress has been reset. You can set up modules again.', 'info')
    return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>')
@login_required
def wedding_dashboard(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    
    # Get summary statistics
    stats = {
        'total_tasks': len(wedding.tasks),
        'pending_tasks': len([t for t in wedding.tasks if not t.completed]),
        'total_guests': len(wedding.guests),
        'rsvp_yes': len([g for g in wedding.guests if g.rsvp_status == 'accepted']),
        'total_vendors': len(wedding.vendors),
        'bridal_party_count': len(wedding.bridal_party),
    }
    
    # Budget summary (includes module costs)
    if wedding.budget:
        total_spent = sum([e.paid_amount or 0 for e in wedding.budget.expenses])
        # Add module-sourced paid amounts
        module_paid = sum(v.deposit_amount or 0 for v in wedding.vendors if v.deposit_paid)
        module_paid += sum(a.price or 0 for a in wedding.attire if a.purchased)
        module_paid += sum(bp.gift_cost or 0 for bp in wedding.bridal_party if bp.gift_purchased)
        stats['budget_total'] = wedding.budget.total_budget
        stats['budget_spent'] = total_spent + module_paid
    else:
        stats['budget_total'] = 0
        stats['budget_spent'] = 0
    
    return render_template('wedding_dashboard.html', wedding=wedding, stats=stats,
                         today=datetime.utcnow().date())

@app.route('/wedding/<int:wedding_id>/delete', methods=['POST'])
@login_required
def delete_wedding(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    db.session.delete(wedding)
    db.session.commit()
    flash('Wedding deleted successfully!', 'success')
    return redirect(url_for('index'))

# More Modules Page
@app.route('/wedding/<int:wedding_id>/more')
@login_required
def more_modules(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    return render_template('more_modules.html', wedding=wedding)

# Traditional Elements Library
@app.route('/traditional-elements')
def traditional_elements():
    elements = TraditionalElement.query.order_by(TraditionalElement.category, TraditionalElement.name).all()

    # Group by category
    grouped = {}
    for elem in elements:
        if elem.category not in grouped:
            grouped[elem.category] = []
        grouped[elem.category].append(elem)

    # If logged in, find their wedding for "Include" buttons
    wedding = None
    if 'user_id' in session:
        access = WeddingAccess.query.filter_by(user_id=session['user_id']).first()
        if access:
            wedding = Wedding.query.get(access.wedding_id)

    return render_template('traditional_elements.html', grouped_elements=grouped, wedding=wedding)

# ============================================
# PEOPLE ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/people')
@login_required
def people_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    people = Person.query.filter_by(wedding_id=wedding_id).order_by(Person.display_order).all()
    return render_template('people/view.html', wedding=wedding, people=people)

@app.route('/wedding/<int:wedding_id>/people/<int:person_id>/edit', methods=['GET', 'POST'])
@login_required
def person_edit(wedding_id, person_id):
    wedding = get_wedding_or_403(wedding_id)
    person = get_entity_or_404(Person, person_id, wedding_id)

    if request.method == 'POST':
        person.name = request.form.get('name')
        person.title = request.form.get('title')
        person.preferred_pronouns = request.form.get('preferred_pronouns')
        person.side_label = request.form.get('side_label')
        person.email = request.form.get('email')
        person.phone = request.form.get('phone')

        # Validate and save name pronunciation
        pron_valid, pron_value = validate_name_pronunciation(request.form.get('name_pronunciation'))
        if not pron_valid:
            flash('Name pronunciation must be 200 characters or fewer.', 'danger')
            return render_template('people/edit.html', wedding=wedding, person=person)
        person.name_pronunciation = pron_value or None

        # Validate and save getting ready fields
        getting_ready_time_str = request.form.get('getting_ready_time')
        if getting_ready_time_str:
            parsed_time = validate_time_string(getting_ready_time_str)
            if parsed_time is None:
                flash('Invalid getting ready time format. Use HH:MM.', 'danger')
                return render_template('people/edit.html', wedding=wedding, person=person)
            person.getting_ready_time = parsed_time
        else:
            person.getting_ready_time = None

        addr_valid, addr_value, addr_err = validate_text_field(
            request.form.get('getting_ready_address'), max_length=1000, field_name='Getting ready address')
        if not addr_valid:
            flash(addr_err, 'danger')
            return render_template('people/edit.html', wedding=wedding, person=person)
        person.getting_ready_address = addr_value or None

        person.getting_ready_location = sanitize_string(request.form.get('getting_ready_location', ''), max_length=200) or None

        db.session.commit()
        flash('Person updated!', 'success')
        return redirect(url_for('people_view', wedding_id=wedding_id))

    return render_template('people/edit.html', wedding=wedding, person=person)

# ============================================
# CEREMONY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/ceremony')
@login_required
def ceremony_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    timeline_items = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony else []
    readings = sorted(ceremony.readings, key=lambda x: x.order or 999) if ceremony else []
    included_elements = WeddingElement.query.filter_by(wedding_id=wedding_id).all()
    return render_template('ceremony/view.html', wedding=wedding, ceremony=ceremony,
                         timeline_items=timeline_items, readings=readings,
                         included_elements=included_elements)

@app.route('/wedding/<int:wedding_id>/ceremony/edit', methods=['GET', 'POST'])
@login_required
def ceremony_edit(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    
    if request.method == 'POST':
        ceremony.venue_name = request.form.get('venue_name')
        ceremony.venue_address = request.form.get('venue_address')
        ceremony.venue_contact = request.form.get('venue_contact')
        ceremony.venue_phone = request.form.get('venue_phone')
        if request.form.get('start_time'):
            ceremony.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        ceremony.duration_minutes = request.form.get('duration_minutes', type=int)
        ceremony.officiant_name = request.form.get('officiant_name')
        ceremony.officiant_contact = request.form.get('officiant_contact')
        ceremony.officiant_phone = request.form.get('officiant_phone')
        ceremony.officiant_type = request.form.get('officiant_type')
        ceremony.ceremony_style = request.form.get('ceremony_style')
        ceremony.vow_type = request.form.get('vow_type')
        ceremony.processional_song = request.form.get('processional_song')
        ceremony.recessional_song = request.form.get('recessional_song')
        ceremony.unity_ceremony_song = request.form.get('unity_ceremony_song')
        ceremony.has_unity_ceremony = request.form.get('has_unity_ceremony') == 'on'
        ceremony.unity_ceremony_type = request.form.get('unity_ceremony_type')
        ceremony.has_special_readings = request.form.get('has_special_readings') == 'on'

        # Validate and save venue load-in time
        load_in_str = request.form.get('venue_load_in_time')
        if load_in_str:
            parsed_time = validate_time_string(load_in_str)
            if parsed_time is None:
                flash('Invalid venue load-in time format. Use HH:MM.', 'danger')
                return render_template('ceremony/edit.html', wedding=wedding, ceremony=ceremony)
            ceremony.venue_load_in_time = parsed_time
        else:
            ceremony.venue_load_in_time = None

        db.session.commit()
        flash('Ceremony details updated!', 'success')
        return redirect(url_for('ceremony_view', wedding_id=wedding_id))
    return render_template('ceremony/edit.html', wedding=wedding, ceremony=ceremony)

@app.route('/wedding/<int:wedding_id>/ceremony/timeline/add', methods=['POST'])
@login_required
def ceremony_timeline_add(wedding_id):
    ceremony = get_wedding_or_403(wedding_id).ceremony
    item = CeremonyTimelineItem(
        ceremony_id=ceremony.id,
        order=request.form.get('order', type=int),
        item_name=request.form.get('item_name'),
        duration_seconds=request.form.get('duration_seconds', type=int),
        description=request.form.get('description'),
        participants=request.form.get('participants')
    )
    db.session.add(item)
    db.session.commit()
    flash('Timeline item added!', 'success')
    return redirect(url_for('ceremony_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/ceremony/ideas')
@login_required
def ceremony_ideas(wedding_id):
    """Browse traditional elements and include them in the wedding"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import CEREMONY_ELEMENT_TASKS
    elements = TraditionalElement.query.order_by(TraditionalElement.category, TraditionalElement.name).all()
    included_ids = {we.element_id for we in WeddingElement.query.filter_by(wedding_id=wedding_id).all()}
    # Group by category
    grouped = {}
    for el in elements:
        grouped.setdefault(el.category, []).append(el)
    return render_template('ceremony/ideas.html', wedding=wedding, grouped=grouped,
                         included_ids=included_ids, element_tasks=CEREMONY_ELEMENT_TASKS,
                         onboarding=False)

@app.route('/wedding/<int:wedding_id>/ceremony/ideas/<int:element_id>/include', methods=['POST'])
@login_required
def ceremony_idea_include(wedding_id, element_id):
    """Include a traditional element and generate tasks"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import CEREMONY_ELEMENT_TASKS

    element = TraditionalElement.query.get_or_404(element_id)

    # Check if already included
    existing = WeddingElement.query.filter_by(wedding_id=wedding_id, element_id=element_id).first()
    if existing:
        flash(f'{element.name} is already included!', 'info')
        return redirect(request.referrer or url_for('ceremony_ideas', wedding_id=wedding_id))

    # Create the WeddingElement record
    we = WeddingElement(wedding_id=wedding_id, element_id=element_id)
    db.session.add(we)

    # Generate tasks from template
    tasks = CEREMONY_ELEMENT_TASKS.get(element.name, [])
    today_dt = date.today()
    count = 0
    for title, description, category, priority, months_before in tasks:
        due_date = wedding.wedding_date - timedelta(days=months_before * 30)
        if due_date.date() < today_dt:
            due_date = datetime.combine(today_dt + timedelta(days=7), datetime.min.time())
        task = Task(
            wedding_id=wedding_id,
            title=title,
            description=description,
            due_date=due_date,
            priority=priority,
            category=category,
            months_before=months_before,
            assigned_to=f'[{element.name}]'
        )
        db.session.add(task)
        count += 1

    db.session.commit()
    if count > 0:
        flash(f'{element.name} included! {count} tasks added to your task list.', 'success')
    else:
        flash(f'{element.name} included!', 'success')
    return redirect(request.referrer or url_for('ceremony_ideas', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/ceremony/ideas/<int:element_id>/remove', methods=['POST'])
@login_required
def ceremony_idea_remove(wedding_id, element_id):
    """Remove an included element, optionally deleting associated tasks"""
    wedding = get_wedding_or_403(wedding_id)
    element = TraditionalElement.query.get_or_404(element_id)

    we = WeddingElement.query.filter_by(wedding_id=wedding_id, element_id=element_id).first()
    if we:
        db.session.delete(we)

    delete_tasks = request.form.get('delete_tasks') == 'true'
    if delete_tasks:
        # Delete tasks that were auto-generated for this element
        Task.query.filter_by(wedding_id=wedding_id, assigned_to=f'[{element.name}]').delete()

    db.session.commit()
    flash(f'{element.name} removed from your ceremony.', 'info')
    return redirect(request.referrer or url_for('ceremony_ideas', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/ideas')
@login_required
def onboarding_ceremony_ideas(wedding_id):
    """Browse ceremony ideas during onboarding"""
    wedding = get_wedding_or_403(wedding_id)
    from templates_data import CEREMONY_ELEMENT_TASKS
    elements = TraditionalElement.query.order_by(TraditionalElement.category, TraditionalElement.name).all()
    included_ids = {we.element_id for we in WeddingElement.query.filter_by(wedding_id=wedding_id).all()}
    grouped = {}
    for el in elements:
        grouped.setdefault(el.category, []).append(el)
    return render_template('ceremony/ideas.html', wedding=wedding, grouped=grouped,
                         included_ids=included_ids, element_tasks=CEREMONY_ELEMENT_TASKS,
                         onboarding=True)

# ============================================
# RECEPTION ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/reception')
@login_required
def reception_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    timeline_items = sorted(reception.timeline_items, key=lambda x: x.order) if reception else []
    menu_items = reception.menu_items if reception else []
    tables = reception.seating_tables if reception else []
    return render_template('reception/view.html', wedding=wedding, reception=reception,
                         timeline_items=timeline_items, menu_items=menu_items, tables=tables)

@app.route('/wedding/<int:wedding_id>/reception/edit', methods=['GET', 'POST'])
@login_required
def reception_edit(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    
    if request.method == 'POST':
        reception.venue_name = request.form.get('venue_name')
        reception.venue_address = request.form.get('venue_address')
        reception.venue_contact = request.form.get('venue_contact')
        reception.venue_phone = request.form.get('venue_phone')
        reception.venue_capacity = request.form.get('venue_capacity', type=int)
        if request.form.get('start_time'):
            reception.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        if request.form.get('end_time'):
            reception.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        reception.catering_style = request.form.get('catering_style')
        reception.bar_service = request.form.get('bar_service')
        reception.cake_flavor = request.form.get('cake_flavor')
        reception.cake_design = request.form.get('cake_design')
        reception.cocktail_menu = request.form.get('cocktail_menu')
        reception.cocktail_entertainment = request.form.get('cocktail_entertainment')
        reception.cocktail_hour_notes = request.form.get('cocktail_hour_notes')
        reception.music_type = request.form.get('music_type')
        reception.first_dance_song = request.form.get('first_dance_song')
        reception.dance_floor_size = request.form.get('dance_floor_size')
        reception.theme = request.form.get('theme')
        reception.centerpiece_description = request.form.get('centerpiece_description')
        reception.lighting_notes = request.form.get('lighting_notes')
        reception.kids_activities = request.form.get('kids_activities')
        reception.kids_sitter_name = request.form.get('kids_sitter_name')
        reception.kids_sitter_phone = request.form.get('kids_sitter_phone')
        reception.expected_guest_count = request.form.get('expected_guest_count', type=int)

        # Validate and save venue load-in time
        load_in_str = request.form.get('venue_load_in_time')
        if load_in_str:
            parsed_time = validate_time_string(load_in_str)
            if parsed_time is None:
                flash('Invalid venue load-in time format. Use HH:MM.', 'danger')
                return render_template('reception/edit.html', wedding=wedding, reception=reception)
            reception.venue_load_in_time = parsed_time
        else:
            reception.venue_load_in_time = None

        # Validate and save after-party fields
        ap_time_str = request.form.get('after_party_start_time')
        if ap_time_str:
            parsed_time = validate_time_string(ap_time_str)
            if parsed_time is None:
                flash('Invalid after-party start time format. Use HH:MM.', 'danger')
                return render_template('reception/edit.html', wedding=wedding, reception=reception)
            reception.after_party_start_time = parsed_time
        else:
            reception.after_party_start_time = None

        venue_valid, venue_value, venue_err = validate_text_field(
            request.form.get('after_party_venue'), max_length=200, field_name='After-party venue')
        if not venue_valid:
            flash(venue_err, 'danger')
            return render_template('reception/edit.html', wedding=wedding, reception=reception)
        reception.after_party_venue = venue_value or None

        addr_valid, addr_value, addr_err = validate_text_field(
            request.form.get('after_party_address'), max_length=1000, field_name='After-party address')
        if not addr_valid:
            flash(addr_err, 'danger')
            return render_template('reception/edit.html', wedding=wedding, reception=reception)
        reception.after_party_address = addr_value or None

        db.session.commit()
        flash('Reception details updated!', 'success')
        return redirect(url_for('reception_view', wedding_id=wedding_id))
    return render_template('reception/edit.html', wedding=wedding, reception=reception)

# ============================================
# GUESTS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/guests')
@login_required
def guests_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    guests = wedding.guests
    stats = {
        'total': len(guests),
        'rsvp_yes': len([g for g in guests if g.rsvp_status == 'accepted']),
        'rsvp_no': len([g for g in guests if g.rsvp_status == 'declined']),
        'rsvp_pending': len([g for g in guests if g.rsvp_status == 'pending' or not g.rsvp_status]),
    }
    return render_template('guests/view.html', wedding=wedding, guests=guests, stats=stats)

@app.route('/wedding/<int:wedding_id>/guests/add', methods=['GET', 'POST'])
@login_required
def guest_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        name = sanitize_string(request.form.get('name'), max_length=200)
        if not name:
            flash('Guest name is required.', 'error')
            return render_template('guests/add.html', wedding=wedding)
        email = request.form.get('email', '').strip()
        if email and not validate_email(email):
            flash('Please provide a valid email address.', 'error')
            return render_template('guests/add.html', wedding=wedding)
        phone = request.form.get('phone', '').strip()
        if phone and not validate_phone(phone):
            flash('Please provide a valid phone number.', 'error')
            return render_template('guests/add.html', wedding=wedding)
        guest = Guest(
            wedding_id=wedding_id,
            name=name,
            email=email,
            phone=phone,
            address=sanitize_string(request.form.get('address'), max_length=500),
            guest_type=request.form.get('guest_type'),
            side=request.form.get('side'),
            dietary_restrictions=sanitize_string(request.form.get('dietary_restrictions'), max_length=500),
            accessibility_needs=sanitize_string(request.form.get('accessibility_needs'), max_length=500),
            household_group=request.form.get('household_group'),
            social_groups=request.form.get('social_groups'),
            guest_token=generate_token()
        )
        db.session.add(guest)
        db.session.commit()
        flash('Guest added!', 'success')
        return redirect(url_for('guests_view', wedding_id=wedding_id))
    return render_template('guests/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/guests/<int:guest_id>/edit', methods=['GET', 'POST'])
@login_required
def guest_edit(wedding_id, guest_id):
    wedding = get_wedding_or_403(wedding_id)
    guest = get_entity_or_404(Guest, guest_id, wedding_id)
    if request.method == 'POST':
        guest.name = request.form.get('name')
        guest.email = request.form.get('email')
        guest.phone = request.form.get('phone')
        guest.address = request.form.get('address')
        guest.guest_type = request.form.get('guest_type')
        guest.side = request.form.get('side')
        guest.dietary_restrictions = request.form.get('dietary_restrictions')
        guest.accessibility_needs = request.form.get('accessibility_needs')
        guest.rsvp_status = request.form.get('rsvp_status')
        guest.meal_choice = request.form.get('meal_choice')
        guest.invitation_sent = request.form.get('invitation_sent') == 'on'
        guest.attending_ceremony = request.form.get('attending_ceremony') == 'on'
        guest.attending_reception = request.form.get('attending_reception') == 'on'
        guest.is_plus_one = request.form.get('is_plus_one') == 'on'
        guest.plus_one_of = request.form.get('plus_one_of')
        guest.gift_received = request.form.get('gift_received') == 'on'
        guest.gift_description = request.form.get('gift_description')
        guest.thank_you_sent = request.form.get('thank_you_sent') == 'on'
        guest.household_group = request.form.get('household_group')
        guest.social_groups = request.form.get('social_groups')
        # Generate token if guest doesn't have one yet
        if not guest.guest_token:
            guest.guest_token = generate_token()
        db.session.commit()
        flash('Guest updated!', 'success')
        return redirect(url_for('guests_view', wedding_id=wedding_id))

    # Ensure token exists for display
    if not guest.guest_token:
        guest.guest_token = generate_token()
        db.session.commit()

    guest_link = url_for('guest_identify', token=guest.guest_token, _external=True)
    return render_template('guests/edit.html', wedding=wedding, guest=guest, guest_link=guest_link)

@app.route('/wedding/<int:wedding_id>/guests/<int:guest_id>/regenerate-token', methods=['POST'])
@login_required
def guest_regenerate_token(wedding_id, guest_id):
    """Regenerate a guest's check-in token (invalidates old link)."""
    wedding = get_wedding_or_403(wedding_id)
    guest = get_entity_or_404(Guest, guest_id, wedding_id)
    guest.guest_token = generate_token()
    db.session.commit()
    flash(f'Check-in link regenerated for {guest.name}.', 'success')
    return redirect(url_for('guest_edit', wedding_id=wedding_id, guest_id=guest_id))


@app.route('/wedding/<int:wedding_id>/guests/<int:guest_id>/delete', methods=['POST'])
@login_required
def guest_delete(wedding_id, guest_id):
    guest = get_entity_or_404(Guest, guest_id, wedding_id)
    db.session.delete(guest)
    db.session.commit()
    flash('Guest removed.', 'success')
    return redirect(url_for('guests_view', wedding_id=wedding_id))

# ============================================
# BRIDAL PARTY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/bridal-party')
@login_required
def bridal_party_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    members = wedding.bridal_party
    return render_template('bridal_party/view.html', wedding=wedding, members=members)

@app.route('/wedding/<int:wedding_id>/bridal-party/add', methods=['GET', 'POST'])
@login_required
def bridal_party_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        # Validate name pronunciation
        pron_valid, pron_value = validate_name_pronunciation(request.form.get('name_pronunciation'))
        if not pron_valid:
            flash('Name pronunciation must be 200 characters or fewer.', 'danger')
            return render_template('bridal_party/add.html', wedding=wedding)

        member = BridalPartyMember(
            wedding_id=wedding_id,
            name=request.form.get('name'),
            role=request.form.get('role'),
            side=request.form.get('side'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            processional_order=request.form.get('processional_order', type=int),
            name_pronunciation=pron_value or None
        )
        db.session.add(member)
        db.session.commit()
        flash('Wedding party member added!', 'success')
        return redirect(url_for('bridal_party_view', wedding_id=wedding_id))
    return render_template('bridal_party/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/bridal-party/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def bridal_party_edit(wedding_id, member_id):
    wedding = get_wedding_or_403(wedding_id)
    member = get_entity_or_404(BridalPartyMember, member_id, wedding_id)
    if request.method == 'POST':
        member.name = request.form.get('name')
        member.role = request.form.get('role')
        member.side = request.form.get('side')
        member.email = request.form.get('email')
        member.phone = request.form.get('phone')
        member.processional_order = request.form.get('processional_order', type=int)
        member.dress_size = request.form.get('dress_size')
        member.suit_size = request.form.get('suit_size')
        member.shoe_size = request.form.get('shoe_size')
        member.height = request.form.get('height')
        member.gift_idea = request.form.get('gift_idea')
        member.gift_cost = request.form.get('gift_cost', type=float)
        member.gift_purchased = request.form.get('gift_purchased') == 'on'
        member.gift_given = request.form.get('gift_given') == 'on'
        member.has_plus_one = request.form.get('has_plus_one') == 'on'
        member.plus_one_name = request.form.get('plus_one_name')
        member.responsibilities = request.form.get('responsibilities')

        # Validate name pronunciation
        pron_valid, pron_value = validate_name_pronunciation(request.form.get('name_pronunciation'))
        if not pron_valid:
            flash('Name pronunciation must be 200 characters or fewer.', 'danger')
            return render_template('bridal_party/edit.html', wedding=wedding, member=member)
        member.name_pronunciation = pron_value or None

        db.session.commit()
        flash('Wedding party member updated!', 'success')
        return redirect(url_for('bridal_party_view', wedding_id=wedding_id))
    return render_template('bridal_party/edit.html', wedding=wedding, member=member)

@app.route('/wedding/<int:wedding_id>/bridal-party/<int:member_id>/delete', methods=['POST'])
@login_required
def bridal_party_delete(wedding_id, member_id):
    member = get_entity_or_404(BridalPartyMember, member_id, wedding_id)
    db.session.delete(member)
    db.session.commit()
    flash('Wedding party member removed.', 'success')
    return redirect(url_for('bridal_party_view', wedding_id=wedding_id))

# ============================================
# BUDGET ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/budget')
@login_required
def budget_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    budget = wedding.budget
    expenses = budget.expenses if budget else []

    total_estimated = sum([e.estimated_cost or 0 for e in expenses])
    total_actual = sum([e.actual_cost or 0 for e in expenses])
    total_paid = sum([e.paid_amount or 0 for e in expenses])

    # Aggregate costs from other modules
    module_costs = []

    # Vendors
    for v in wedding.vendors:
        if v.total_cost:
            module_costs.append({
                'source': 'Vendors',
                'item': v.business_name,
                'cost': v.total_cost,
                'paid': v.deposit_amount or 0 if v.deposit_paid else 0,
                'link': url_for('vendors_view', wedding_id=wedding_id)
            })

    # Attire
    for a in wedding.attire:
        if a.price:
            module_costs.append({
                'source': 'Attire',
                'item': '{} - {}'.format(a.person_name or 'Unknown', a.garment_type or 'Outfit'),
                'cost': a.price,
                'paid': a.price if a.purchased else 0,
                'link': url_for('attire_view', wedding_id=wedding_id)
            })

    # Flowers & Decor
    for f in wedding.floral_items:
        if f.cost:
            module_costs.append({
                'source': 'Flowers',
                'item': '{} (x{})'.format(f.item_type, f.quantity or 1),
                'cost': f.cost * (f.quantity or 1),
                'paid': 0,
                'link': url_for('flowers_view', wedding_id=wedding_id)
            })

    # Hair & Makeup
    for hm in wedding.hair_makeup:
        if hm.cost:
            module_costs.append({
                'source': 'Hair & Makeup',
                'item': '{} - {}'.format(hm.person_name, hm.service_type or 'Service'),
                'cost': hm.cost,
                'paid': 0,
                'link': url_for('hair_makeup_view', wedding_id=wedding_id)
            })

    # Invitations
    for inv in wedding.invitations:
        if inv.cost:
            module_costs.append({
                'source': 'Stationery',
                'item': inv.item_type.replace('_', ' ').title() if inv.item_type else 'Invitation',
                'cost': inv.cost,
                'paid': 0,
                'link': url_for('invitations_view', wedding_id=wedding_id)
            })

    # Marriage License
    if wedding.marriage_license and wedding.marriage_license.cost:
        module_costs.append({
            'source': 'Legal',
            'item': 'Marriage License',
            'cost': wedding.marriage_license.cost,
            'paid': wedding.marriage_license.cost if wedding.marriage_license.filed else 0,
            'link': url_for('license_view', wedding_id=wedding_id)
        })

    # Bridal Party Gifts
    for bp in wedding.bridal_party:
        if bp.gift_cost:
            module_costs.append({
                'source': 'Gifts',
                'item': 'Gift for {}'.format(bp.name),
                'cost': bp.gift_cost,
                'paid': bp.gift_cost if bp.gift_purchased else 0,
                'link': url_for('bridal_party_view', wedding_id=wedding_id)
            })

    module_total_cost = sum(m['cost'] for m in module_costs)
    module_total_paid = sum(m['paid'] for m in module_costs)

    stats = {
        'budget_total': budget.total_budget if budget else 0,
        'estimated': total_estimated,
        'actual': total_actual,
        'paid': total_paid,
        'remaining': (budget.total_budget if budget else 0) - total_paid - module_total_paid,
        'module_total_cost': module_total_cost,
        'module_total_paid': module_total_paid,
        'all_costs': total_estimated + module_total_cost,
        'all_paid': total_paid + module_total_paid,
    }

    # Category spending for limits comparison
    category_limits = budget.category_limits if budget else []
    category_spending = {}
    for e in expenses:
        cat = e.category
        if cat not in category_spending:
            category_spending[cat] = 0
        category_spending[cat] += e.estimated_cost or 0

    # Build limit warnings
    limit_warnings = []
    for cl in category_limits:
        spent = category_spending.get(cl.category, 0)
        if spent > cl.limit_amount:
            limit_warnings.append({
                'category': cl.category,
                'limit': cl.limit_amount,
                'spent': spent,
                'over': spent - cl.limit_amount
            })

    # Hidden cost reminders - check which ones aren't budgeted
    existing_categories = set(e.category.lower() for e in expenses)
    existing_items = set(e.item_name.lower() for e in expenses)
    hidden_cost_suggestions = []
    for name, category, description, typical_cost in HIDDEN_COST_REMINDERS:
        # Only suggest if not already in budget
        if name.lower() not in existing_items and not any(name.lower() in item for item in existing_items):
            hidden_cost_suggestions.append({
                'name': name,
                'category': category,
                'description': description,
                'typical_cost': typical_cost
            })

    return render_template('budget/view.html', wedding=wedding, budget=budget,
                         expenses=expenses, stats=stats, module_costs=module_costs,
                         category_limits=category_limits, category_spending=category_spending,
                         limit_warnings=limit_warnings,
                         hidden_cost_suggestions=hidden_cost_suggestions)

@app.route('/wedding/<int:wedding_id>/budget/update', methods=['POST'])
@login_required
def budget_update(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.budget:
        budget = Budget(wedding_id=wedding_id, total_budget=0)
        db.session.add(budget)
        db.session.commit()
    wedding.budget.total_budget = request.form.get('total_budget', type=float) or 0
    db.session.commit()
    flash('Budget updated!', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/budget/expense/add', methods=['POST'])
@login_required
def budget_expense_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.budget:
        budget = Budget(wedding_id=wedding_id, total_budget=0)
        db.session.add(budget)
        db.session.commit()
    expense = BudgetExpense(
        budget_id=wedding.budget.id,
        category=request.form.get('category'),
        item_name=request.form.get('item_name'),
        estimated_cost=request.form.get('estimated_cost', type=float),
        actual_cost=request.form.get('actual_cost', type=float),
        paid_amount=request.form.get('paid_amount', type=float) or 0,
        payment_status=request.form.get('payment_status', 'unpaid'),
        covered_by=request.form.get('covered_by'),
        notes=request.form.get('notes')
    )
    if request.form.get('payment_due_date'):
        expense.payment_due_date = datetime.strptime(request.form.get('payment_due_date'), '%Y-%m-%d').date()
    db.session.add(expense)
    db.session.commit()
    flash('Expense added!', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/budget/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def budget_expense_edit(wedding_id, expense_id):
    wedding = get_wedding_or_403(wedding_id)
    expense = get_entity_or_404(BudgetExpense, expense_id, wedding_id)
    if request.method == 'POST':
        expense.category = request.form.get('category')
        expense.item_name = request.form.get('item_name')
        expense.estimated_cost = request.form.get('estimated_cost', type=float)
        expense.actual_cost = request.form.get('actual_cost', type=float)
        expense.paid_amount = request.form.get('paid_amount', type=float)
        if request.form.get('payment_due_date'):
            expense.payment_due_date = datetime.strptime(request.form.get('payment_due_date'), '%Y-%m-%d').date()
        expense.payment_status = request.form.get('payment_status')
        expense.covered_by = request.form.get('covered_by')
        expense.notes = request.form.get('notes')
        db.session.commit()
        flash('Expense updated!', 'success')
        return redirect(url_for('budget_view', wedding_id=wedding_id))
    return render_template('budget/edit.html', wedding=wedding, expense=expense)

@app.route('/wedding/<int:wedding_id>/budget/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def budget_expense_delete(wedding_id, expense_id):
    expense = get_entity_or_404(BudgetExpense, expense_id, wedding_id)
    db.session.delete(expense)
    db.session.commit()
    flash('Expense removed.', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

# ============================================
# VENDORS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/vendors')
@login_required
def vendors_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    vendors = wedding.vendors
    return render_template('vendors/view.html', wedding=wedding, vendors=vendors)

@app.route('/wedding/<int:wedding_id>/vendors/add', methods=['GET', 'POST'])
@login_required
def vendor_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        vendor = Vendor(
            wedding_id=wedding_id,
            category=request.form.get('category'),
            business_name=request.form.get('business_name'),
            contact_name=request.form.get('contact_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            total_cost=request.form.get('total_cost', type=float),
            deposit_amount=request.form.get('deposit_amount', type=float),
            setup_instructions=request.form.get('setup_instructions'),
            meals_needed=request.form.get('meals_needed', type=int),
            notes=request.form.get('notes')
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor added!', 'success')
        return redirect(url_for('vendors_view', wedding_id=wedding_id))
    return render_template('vendors/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/vendors/<int:vendor_id>/edit', methods=['GET', 'POST'])
@login_required
def vendor_edit(wedding_id, vendor_id):
    wedding = get_wedding_or_403(wedding_id)
    vendor = get_entity_or_404(Vendor, vendor_id, wedding_id)
    if request.method == 'POST':
        vendor.category = request.form.get('category')
        vendor.business_name = request.form.get('business_name')
        vendor.contact_name = request.form.get('contact_name')
        vendor.email = request.form.get('email')
        vendor.phone = request.form.get('phone')
        vendor.website = request.form.get('website')
        vendor.total_cost = request.form.get('total_cost', type=float)
        vendor.deposit_amount = request.form.get('deposit_amount', type=float)
        vendor.deposit_paid = request.form.get('deposit_paid') == 'on'
        vendor.balance_due = request.form.get('balance_due', type=float)
        vendor.contract_signed = request.form.get('contract_signed') == 'on'
        if request.form.get('contract_date'):
            vendor.contract_date = datetime.strptime(request.form.get('contract_date'), '%Y-%m-%d').date()
        vendor.cancellation_policy = request.form.get('cancellation_policy')
        vendor.contract_notes = request.form.get('contract_notes')
        vendor.backup_contact = request.form.get('backup_contact')

        # Validate backup phone
        backup_phone_val = request.form.get('backup_phone', '').strip()
        if backup_phone_val and not validate_phone(backup_phone_val):
            flash('Invalid backup phone number format.', 'danger')
            return render_template('vendors/edit.html', wedding=wedding, vendor=vendor)
        vendor.backup_phone = backup_phone_val or None

        if request.form.get('final_payment_date'):
            vendor.final_payment_date = datetime.strptime(request.form.get('final_payment_date'), '%Y-%m-%d').date()
        if request.form.get('service_date'):
            vendor.service_date = datetime.strptime(request.form.get('service_date'), '%Y-%m-%d').date()
        if request.form.get('service_time'):
            vendor.service_time = datetime.strptime(request.form.get('service_time'), '%H:%M').time()

        # Validate and save arrival time
        arrival_str = request.form.get('arrival_time')
        if arrival_str:
            parsed_time = validate_time_string(arrival_str)
            if parsed_time is None:
                flash('Invalid arrival time format. Use HH:MM.', 'danger')
                return render_template('vendors/edit.html', wedding=wedding, vendor=vendor)
            vendor.arrival_time = parsed_time
        else:
            vendor.arrival_time = None

        # Validate overtime rate
        ot_valid, ot_value, ot_err = validate_text_field(
            request.form.get('overtime_rate'), max_length=100, field_name='Overtime rate')
        if not ot_valid:
            flash(ot_err, 'danger')
            return render_template('vendors/edit.html', wedding=wedding, vendor=vendor)
        vendor.overtime_rate = ot_value or None

        vendor.service_location = request.form.get('service_location')
        vendor.setup_instructions = request.form.get('setup_instructions')
        vendor.meals_needed = request.form.get('meals_needed', type=int)
        vendor.rating = request.form.get('rating', type=int)
        vendor.review_notes = request.form.get('review_notes')
        vendor.notes = request.form.get('notes')
        db.session.commit()
        flash('Vendor updated!', 'success')
        return redirect(url_for('vendors_view', wedding_id=wedding_id))
    return render_template('vendors/edit.html', wedding=wedding, vendor=vendor)

@app.route('/wedding/<int:wedding_id>/vendors/<int:vendor_id>/delete', methods=['POST'])
@login_required
def vendor_delete(wedding_id, vendor_id):
    vendor = get_entity_or_404(Vendor, vendor_id, wedding_id)
    db.session.delete(vendor)
    db.session.commit()
    flash('Vendor removed.', 'success')
    return redirect(url_for('vendors_view', wedding_id=wedding_id))

# ============================================
# TASKS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/tasks')
@login_required
def tasks_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    pending = [t for t in wedding.tasks if not t.completed]
    completed = [t for t in wedding.tasks if t.completed]
    return render_template('tasks/view.html', wedding=wedding,
                         pending_tasks=pending, completed_tasks=completed)

@app.route('/wedding/<int:wedding_id>/tasks/add', methods=['GET', 'POST'])
@login_required
def task_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        task = Task(
            wedding_id=wedding_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            due_date=safe_strptime(request.form.get('due_date'), '%Y-%m-%d') or date.today(),
            priority=request.form.get('priority', 'medium'),
            category=request.form.get('category'),
            assigned_to=request.form.get('assigned_to')
        )
        db.session.add(task)
        log_activity(wedding_id, 'created', 'task', task.title)
        db.session.commit()
        flash('Task added!', 'success')
        return redirect(url_for('tasks_view', wedding_id=wedding_id))
    return render_template('tasks/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/tasks/<int:task_id>/edit', methods=['GET', 'POST'])
@login_required
def task_edit(wedding_id, task_id):
    wedding = get_wedding_or_403(wedding_id)
    task = get_entity_or_404(Task, task_id, wedding_id)
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.due_date = safe_strptime(request.form.get('due_date'), '%Y-%m-%d') or task.due_date
        task.priority = request.form.get('priority', 'medium')
        task.category = request.form.get('category')
        task.assigned_to = request.form.get('assigned_to')
        log_activity(wedding_id, 'updated', 'task', task.title)
        db.session.commit()
        flash('Task updated!', 'success')
        return redirect(url_for('tasks_view', wedding_id=wedding_id))
    return render_template('tasks/edit.html', wedding=wedding, task=task)

@app.route('/wedding/<int:wedding_id>/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def task_delete(wedding_id, task_id):
    task = get_entity_or_404(Task, task_id, wedding_id)
    db.session.delete(task)
    db.session.commit()
    flash('Task deleted.', 'success')
    return redirect(url_for('tasks_view', wedding_id=wedding_id))

@app.route('/task/<int:task_id>/toggle', methods=['POST'])
@login_required
def task_toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    flash(f'Task {"completed" if task.completed else "reopened"}!', 'success')
    return redirect(url_for('tasks_view', wedding_id=task.wedding_id))

# ============================================
# REGISTRY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/registry')
@login_required
def registry_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = wedding.registry_items
    return render_template('registry/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/registry/add', methods=['GET', 'POST'])
@login_required
def registry_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = RegistryItem(
            wedding_id=wedding_id,
            item_name=request.form.get('item_name'),
            store=request.form.get('store'),
            url=request.form.get('url'),
            price=request.form.get('price', type=float),
            quantity_requested=request.form.get('quantity_requested', type=int) or 1
        )
        db.session.add(item)
        db.session.commit()
        flash('Registry item added!', 'success')
        return redirect(url_for('registry_view', wedding_id=wedding_id))
    return render_template('registry/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/registry/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def registry_edit(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = get_entity_or_404(RegistryItem, item_id, wedding_id)
    if request.method == 'POST':
        item.item_name = request.form.get('item_name')
        item.store = request.form.get('store')
        item.url = request.form.get('url')
        item.price = request.form.get('price', type=float)
        item.quantity_requested = request.form.get('quantity_requested', type=int) or 1
        item.quantity_purchased = request.form.get('quantity_purchased', type=int) or 0
        item.purchased_by = request.form.get('purchased_by')
        db.session.commit()
        flash('Registry item updated!', 'success')
        return redirect(url_for('registry_view', wedding_id=wedding_id))
    return render_template('registry/edit.html', wedding=wedding, item=item)

@app.route('/wedding/<int:wedding_id>/registry/<int:item_id>/delete', methods=['POST'])
@login_required
def registry_delete(wedding_id, item_id):
    item = get_entity_or_404(RegistryItem, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Registry item removed.', 'success')
    return redirect(url_for('registry_view', wedding_id=wedding_id))

# ============================================
# ATTIRE ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/attire')
@login_required
def attire_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = wedding.attire
    return render_template('attire/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/attire/add', methods=['GET', 'POST'])
@login_required
def attire_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = Attire(
            wedding_id=wedding_id,
            person_name=request.form.get('person_name'),
            person_type=request.form.get('person_type'),
            garment_type=request.form.get('garment_type'),
            designer=request.form.get('designer'),
            style_number=request.form.get('style_number'),
            color=request.form.get('color'),
            size=request.form.get('size'),
            store=request.form.get('store'),
            price=request.form.get('price', type=float),
            notes=request.form.get('notes')
        )
        db.session.add(item)
        db.session.commit()
        flash('Attire item added!', 'success')
        return redirect(url_for('attire_view', wedding_id=wedding_id))
    return render_template('attire/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/attire/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def attire_edit(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = get_entity_or_404(Attire, item_id, wedding_id)
    if request.method == 'POST':
        item.person_name = request.form.get('person_name')
        item.person_type = request.form.get('person_type')
        item.garment_type = request.form.get('garment_type')
        item.designer = request.form.get('designer')
        item.style_number = request.form.get('style_number')
        item.color = request.form.get('color')
        item.size = request.form.get('size')
        item.store = request.form.get('store')
        item.price = request.form.get('price', type=float)
        item.purchased = request.form.get('purchased') == 'on'
        if request.form.get('purchase_date'):
            item.purchase_date = datetime.strptime(request.form.get('purchase_date'), '%Y-%m-%d').date()
        if request.form.get('first_fitting_date'):
            item.first_fitting_date = datetime.strptime(request.form.get('first_fitting_date'), '%Y-%m-%d').date()
        if request.form.get('final_fitting_date'):
            item.final_fitting_date = datetime.strptime(request.form.get('final_fitting_date'), '%Y-%m-%d').date()
        if request.form.get('pickup_date'):
            item.pickup_date = datetime.strptime(request.form.get('pickup_date'), '%Y-%m-%d').date()
        item.accessories = request.form.get('accessories')
        item.notes = request.form.get('notes')
        db.session.commit()
        flash('Attire item updated!', 'success')
        return redirect(url_for('attire_view', wedding_id=wedding_id))
    return render_template('attire/edit.html', wedding=wedding, item=item)

@app.route('/wedding/<int:wedding_id>/attire/<int:item_id>/delete', methods=['POST'])
@login_required
def attire_delete(wedding_id, item_id):
    item = get_entity_or_404(Attire, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Attire item removed.', 'success')
    return redirect(url_for('attire_view', wedding_id=wedding_id))

# ============================================
# HONEYMOON ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/honeymoon')
@login_required
def honeymoon_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    honeymoon = wedding.honeymoon
    itinerary = sorted(honeymoon.itinerary_items, key=lambda x: x.day_number) if honeymoon else []
    packing = honeymoon.packing_items if honeymoon else []
    return render_template('honeymoon/view.html', wedding=wedding, honeymoon=honeymoon,
                         itinerary=itinerary, packing=packing)

@app.route('/wedding/<int:wedding_id>/honeymoon/edit', methods=['GET', 'POST'])
@login_required
def honeymoon_edit(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    honeymoon = wedding.honeymoon
    if not honeymoon:
        honeymoon = Honeymoon(wedding_id=wedding_id)
        db.session.add(honeymoon)
        db.session.commit()
    if request.method == 'POST':
        honeymoon.destination = request.form.get('destination')
        if request.form.get('start_date'):
            honeymoon.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        if request.form.get('end_date'):
            honeymoon.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        honeymoon.budget = request.form.get('budget', type=float)
        honeymoon.flight_confirmation = request.form.get('flight_confirmation')
        honeymoon.airline = request.form.get('airline')
        db.session.commit()
        flash('Honeymoon details updated!', 'success')
        return redirect(url_for('honeymoon_view', wedding_id=wedding_id))
    return render_template('honeymoon/edit.html', wedding=wedding, honeymoon=honeymoon)

@app.route('/wedding/<int:wedding_id>/honeymoon/packing/add', methods=['POST'])
@login_required
def honeymoon_packing_add(wedding_id):
    honeymoon = get_wedding_or_403(wedding_id).honeymoon
    item = PackingItem(
        honeymoon_id=honeymoon.id,
        item_name=request.form.get('item_name'),
        category=request.form.get('category')
    )
    db.session.add(item)
    db.session.commit()
    flash('Packing item added!', 'success')
    return redirect(url_for('honeymoon_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/honeymoon/packing/<int:item_id>/toggle', methods=['POST'])
@login_required
def honeymoon_packing_toggle(wedding_id, item_id):
    item = PackingItem.query.get_or_404(item_id)
    item.packed = not item.packed
    db.session.commit()
    return redirect(url_for('honeymoon_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/honeymoon/packing/<int:item_id>/delete', methods=['POST'])
@login_required
def honeymoon_packing_delete(wedding_id, item_id):
    item = PackingItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('honeymoon_view', wedding_id=wedding_id))

# ============================================
# BRANDING ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/branding')
@login_required
def branding_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    branding = wedding.branding
    return render_template('branding/view.html', wedding=wedding, branding=branding)

@app.route('/wedding/<int:wedding_id>/branding/edit', methods=['GET', 'POST'])
@login_required
def branding_edit(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    branding = wedding.branding
    if not branding:
        branding = WeddingBranding(wedding_id=wedding_id)
        db.session.add(branding)
        db.session.commit()
    if request.method == 'POST':
        branding.primary_color = request.form.get('primary_color')
        branding.secondary_color = request.form.get('secondary_color')
        branding.accent_color = request.form.get('accent_color')
        branding.primary_font = request.form.get('primary_font')
        branding.secondary_font = request.form.get('secondary_font')
        branding.monogram_text = request.form.get('monogram_text')
        branding.overall_style = request.form.get('overall_style')
        branding.mood = request.form.get('mood')
        db.session.commit()
        flash('Branding updated!', 'success')
        return redirect(url_for('branding_view', wedding_id=wedding_id))
    return render_template('branding/edit.html', wedding=wedding, branding=branding)

# ============================================
# RECEPTION SUB-ITEMS (TIMELINE, MENU, SEATING)
# ============================================

@app.route('/wedding/<int:wedding_id>/reception/timeline/add', methods=['POST'])
@login_required
def reception_timeline_add(wedding_id):
    reception = get_wedding_or_403(wedding_id).reception
    item = ReceptionTimelineItem(
        reception_id=reception.id,
        order=request.form.get('order', type=int) or 0,
        item_name=request.form.get('item_name'),
        duration_seconds=request.form.get('duration_seconds', type=int),
        description=request.form.get('description')
    )
    if request.form.get('scheduled_time'):
        item.scheduled_time = datetime.strptime(request.form.get('scheduled_time'), '%H:%M').time()
    db.session.add(item)
    db.session.commit()
    flash('Timeline item added!', 'success')
    return redirect(url_for('reception_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/reception/timeline/<int:item_id>/delete', methods=['POST'])
@login_required
def reception_timeline_delete(wedding_id, item_id):
    item = ReceptionTimelineItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Timeline item removed.', 'success')
    return redirect(url_for('reception_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/reception/menu/add', methods=['POST'])
@login_required
def reception_menu_add(wedding_id):
    reception = get_wedding_or_403(wedding_id).reception
    item = MenuItem(
        reception_id=reception.id,
        course=request.form.get('course'),
        name=request.form.get('name'),
        description=request.form.get('description'),
        dietary_tags=request.form.get('dietary_tags')
    )
    db.session.add(item)
    db.session.commit()
    flash('Menu item added!', 'success')
    return redirect(url_for('reception_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/reception/menu/<int:item_id>/delete', methods=['POST'])
@login_required
def reception_menu_delete(wedding_id, item_id):
    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Menu item removed.', 'success')
    return redirect(url_for('reception_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/reception/table/add', methods=['POST'])
@login_required
def reception_table_add(wedding_id):
    reception = get_wedding_or_403(wedding_id).reception
    table = SeatingTable(
        reception_id=reception.id,
        table_number=request.form.get('table_number'),
        capacity=request.form.get('capacity', type=int) or 8,
        table_shape=request.form.get('table_shape'),
        notes=request.form.get('notes')
    )
    db.session.add(table)
    db.session.commit()
    flash('Table added!', 'success')
    return redirect(url_for('reception_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/reception/table/<int:table_id>/delete', methods=['POST'])
@login_required
def reception_table_delete(wedding_id, table_id):
    table = get_entity_or_404(SeatingTable, table_id, wedding_id)
    db.session.delete(table)
    db.session.commit()
    flash('Table removed.', 'success')
    return redirect(url_for('reception_view', wedding_id=wedding_id))

# ============================================
# CEREMONY READINGS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/ceremony/reading/add', methods=['POST'])
@login_required
def ceremony_reading_add(wedding_id):
    ceremony = get_wedding_or_403(wedding_id).ceremony
    reading = CeremonyReading(
        ceremony_id=ceremony.id,
        title=request.form.get('title'),
        author=request.form.get('author'),
        reader_name=request.form.get('reader_name'),
        text_content=request.form.get('text_content'),
        order=request.form.get('order', type=int)
    )
    db.session.add(reading)
    db.session.commit()
    flash('Reading added!', 'success')
    return redirect(url_for('ceremony_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/ceremony/reading/<int:reading_id>/delete', methods=['POST'])
@login_required
def ceremony_reading_delete(wedding_id, reading_id):
    reading = CeremonyReading.query.get_or_404(reading_id)
    db.session.delete(reading)
    db.session.commit()
    flash('Reading removed.', 'success')
    return redirect(url_for('ceremony_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/ceremony/timeline/<int:item_id>/delete', methods=['POST'])
@login_required
def ceremony_timeline_delete(wedding_id, item_id):
    item = CeremonyTimelineItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Timeline item removed.', 'success')
    return redirect(url_for('ceremony_view', wedding_id=wedding_id))

# ============================================
# PERSON DELETE ROUTE
# ============================================

@app.route('/wedding/<int:wedding_id>/people/<int:person_id>/delete', methods=['POST'])
@login_required
def person_delete(wedding_id, person_id):
    person = get_entity_or_404(Person, person_id, wedding_id)
    db.session.delete(person)
    db.session.commit()
    flash('Person removed.', 'success')
    return redirect(url_for('people_view', wedding_id=wedding_id))

# ============================================
# DAY-OF TIMELINE ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/day-of')
@login_required
def day_of_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    participants = wedding.participants
    return render_template('day_of/view.html', wedding=wedding, items=items, participants=participants)

@app.route('/wedding/<int:wedding_id>/day-of/add', methods=['GET', 'POST'])
@login_required
def day_of_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    participants = wedding.participants
    if request.method == 'POST':
        item = DayOfTimelineItem(
            wedding_id=wedding_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            location=request.form.get('location'),
            who=request.form.get('who'),
            category=request.form.get('category'),
            order=request.form.get('order', type=int) or 0
        )
        if request.form.get('time'):
            item.time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        db.session.add(item)
        db.session.flush()
        # Assign participants
        participant_ids = request.form.getlist('participants')
        for pid in participant_ids:
            participant = WeddingParticipant.query.get(int(pid))
            if participant:
                item.assigned_participants.append(participant)
        db.session.commit()
        flash('Timeline item added!', 'success')
        return redirect(url_for('day_of_view', wedding_id=wedding_id))
    return render_template('day_of/add.html', wedding=wedding, participants=participants)

@app.route('/wedding/<int:wedding_id>/day-of/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def day_of_edit(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = get_entity_or_404(DayOfTimelineItem, item_id, wedding_id)
    participants = wedding.participants
    if request.method == 'POST':
        item.title = request.form.get('title')
        item.description = request.form.get('description')
        item.location = request.form.get('location')
        item.who = request.form.get('who')
        item.category = request.form.get('category')
        item.order = request.form.get('order', type=int) or 0
        if request.form.get('time'):
            item.time = datetime.strptime(request.form.get('time'), '%H:%M').time()
        else:
            item.time = None
        # Update participant assignments
        item.assigned_participants.clear()
        participant_ids = request.form.getlist('participants')
        for pid in participant_ids:
            participant = WeddingParticipant.query.get(int(pid))
            if participant:
                item.assigned_participants.append(participant)
        db.session.commit()
        flash('Timeline item updated!', 'success')
        return redirect(url_for('day_of_view', wedding_id=wedding_id))
    return render_template('day_of/edit.html', wedding=wedding, item=item, participants=participants)

@app.route('/wedding/<int:wedding_id>/day-of/<int:item_id>/delete', methods=['POST'])
@login_required
def day_of_delete(wedding_id, item_id):
    item = get_entity_or_404(DayOfTimelineItem, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Timeline item removed.', 'success')
    return redirect(url_for('day_of_view', wedding_id=wedding_id))

# ============================================
# INDIVIDUAL ITINERARY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/itinerary')
@login_required
def itinerary_participants(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    participants = wedding.participants
    # Group by role_category
    categories = {}
    for p in participants:
        cat = p.role_category or 'other'
        categories.setdefault(cat, []).append(p)
    return render_template('itinerary/participants.html', wedding=wedding,
                           participants=participants, categories=categories)

@app.route('/wedding/<int:wedding_id>/itinerary/add-participant', methods=['GET', 'POST'])
@login_required
def itinerary_add_participant(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        # Validate name pronunciation
        pron_valid, pron_value = validate_name_pronunciation(request.form.get('name_pronunciation'))
        if not pron_valid:
            flash('Name pronunciation must be 200 characters or fewer.', 'danger')
            return render_template('itinerary/add_participant.html', wedding=wedding,
                                   people=wedding.people, bridal_party=wedding.bridal_party)

        participant = WeddingParticipant(
            wedding_id=wedding_id,
            name=request.form.get('name'),
            role=request.form.get('role'),
            role_category=request.form.get('role_category'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            notes=request.form.get('notes'),
            name_pronunciation=pron_value or None
        )
        # Link to existing Person if selected
        person_id = request.form.get('person_id', type=int)
        if person_id:
            participant.person_id = person_id
        # Link to bridal party member if selected
        bp_id = request.form.get('bridal_party_id', type=int)
        if bp_id:
            participant.bridal_party_id = bp_id
        db.session.add(participant)
        db.session.commit()
        flash('Participant added!', 'success')
        return redirect(url_for('itinerary_participants', wedding_id=wedding_id))
    return render_template('itinerary/add_participant.html', wedding=wedding,
                           people=wedding.people, bridal_party=wedding.bridal_party)

@app.route('/wedding/<int:wedding_id>/itinerary/participant/<int:participant_id>/edit', methods=['GET', 'POST'])
@login_required
def itinerary_edit_participant(wedding_id, participant_id):
    wedding = get_wedding_or_403(wedding_id)
    participant = get_entity_or_404(WeddingParticipant, participant_id, wedding_id)
    if request.method == 'POST':
        participant.name = request.form.get('name')
        participant.role = request.form.get('role')
        participant.role_category = request.form.get('role_category')
        participant.phone = request.form.get('phone')
        participant.email = request.form.get('email')
        participant.notes = request.form.get('notes')
        person_id = request.form.get('person_id', type=int)
        participant.person_id = person_id if person_id else None
        bp_id = request.form.get('bridal_party_id', type=int)
        participant.bridal_party_id = bp_id if bp_id else None

        # Validate name pronunciation
        pron_valid, pron_value = validate_name_pronunciation(request.form.get('name_pronunciation'))
        if not pron_valid:
            flash('Name pronunciation must be 200 characters or fewer.', 'danger')
            return render_template('itinerary/edit_participant.html', wedding=wedding,
                                   participant=participant, people=wedding.people,
                                   bridal_party=wedding.bridal_party)
        participant.name_pronunciation = pron_value or None

        db.session.commit()
        flash('Participant updated!', 'success')
        return redirect(url_for('itinerary_participants', wedding_id=wedding_id))
    return render_template('itinerary/edit_participant.html', wedding=wedding,
                           participant=participant, people=wedding.people,
                           bridal_party=wedding.bridal_party)

@app.route('/wedding/<int:wedding_id>/itinerary/participant/<int:participant_id>/delete', methods=['POST'])
@login_required
def itinerary_delete_participant(wedding_id, participant_id):
    participant = get_entity_or_404(WeddingParticipant, participant_id, wedding_id)
    db.session.delete(participant)
    db.session.commit()
    flash('Participant removed.', 'success')
    return redirect(url_for('itinerary_participants', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/itinerary/participant/<int:participant_id>')
@login_required
def itinerary_individual(wedding_id, participant_id):
    wedding = get_wedding_or_403(wedding_id)
    participant = get_entity_or_404(WeddingParticipant, participant_id, wedding_id)
    # Get this person's timeline items, sorted by time
    items = sorted(participant.timeline_items,
                   key=lambda x: (x.order, x.time or datetime.min.time()))
    return render_template('itinerary/individual.html', wedding=wedding,
                           participant=participant, items=items)

@app.route('/wedding/<int:wedding_id>/itinerary/handler-view')
@login_required
def itinerary_handler_view(wedding_id):
    """Handler view showing all participants and where they should be at each time."""
    wedding = get_wedding_or_403(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    participants = wedding.participants
    return render_template('itinerary/handler_view.html', wedding=wedding,
                           items=items, participants=participants)

@app.route('/wedding/<int:wedding_id>/itinerary/import-people', methods=['POST'])
@login_required
def itinerary_import_people(wedding_id):
    """Quickly import people and bridal party members as participants."""
    wedding = get_wedding_or_403(wedding_id)
    imported = 0
    # Import people getting married
    for person in wedding.people:
        existing = WeddingParticipant.query.filter_by(
            wedding_id=wedding_id, person_id=person.id).first()
        if not existing:
            participant = WeddingParticipant(
                wedding_id=wedding_id,
                name=person.name,
                role=person.title or 'Partner',
                role_category='couple',
                email=person.email,
                phone=person.phone,
                person_id=person.id
            )
            db.session.add(participant)
            imported += 1
    # Import bridal party
    for bp in wedding.bridal_party:
        existing = WeddingParticipant.query.filter_by(
            wedding_id=wedding_id, bridal_party_id=bp.id).first()
        if not existing:
            participant = WeddingParticipant(
                wedding_id=wedding_id,
                name=bp.name,
                role=bp.role or 'Wedding Party',
                role_category='wedding_party',
                email=bp.email,
                phone=bp.phone,
                bridal_party_id=bp.id
            )
            db.session.add(participant)
            imported += 1
    db.session.commit()
    flash(f'{imported} participant(s) imported!', 'success')
    return redirect(url_for('itinerary_participants', wedding_id=wedding_id))

# ============================================
# PHOTOGRAPHY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/photos')
@login_required
def photos_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    shots = wedding.photo_shots
    return render_template('photos/view.html', wedding=wedding, shots=shots)

@app.route('/wedding/<int:wedding_id>/photos/add', methods=['GET', 'POST'])
@login_required
def photos_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        shot = PhotoShot(
            wedding_id=wedding_id,
            category=request.form.get('category'),
            description=request.form.get('description'),
            people=request.form.get('people'),
            priority=request.form.get('priority', 'nice_to_have'),
            notes=request.form.get('notes')
        )
        db.session.add(shot)
        db.session.commit()
        flash('Shot added to list!', 'success')
        return redirect(url_for('photos_view', wedding_id=wedding_id))
    return render_template('photos/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/photos/<int:shot_id>/delete', methods=['POST'])
@login_required
def photos_delete(wedding_id, shot_id):
    shot = get_entity_or_404(PhotoShot, shot_id, wedding_id)
    db.session.delete(shot)
    db.session.commit()
    flash('Shot removed.', 'success')
    return redirect(url_for('photos_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/photos/<int:shot_id>/toggle', methods=['POST'])
@login_required
def photos_toggle(wedding_id, shot_id):
    shot = get_entity_or_404(PhotoShot, shot_id, wedding_id)
    shot.captured = not shot.captured
    db.session.commit()
    return redirect(url_for('photos_view', wedding_id=wedding_id))

# ============================================
# MUSIC & PLAYLIST ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/music')
@login_required
def music_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    songs = wedding.songs
    return render_template('music/view.html', wedding=wedding, songs=songs)

@app.route('/wedding/<int:wedding_id>/music/add', methods=['GET', 'POST'])
@login_required
def music_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        song = Song(
            wedding_id=wedding_id,
            title=request.form.get('title'),
            artist=request.form.get('artist'),
            moment=request.form.get('moment'),
            duration_minutes=request.form.get('duration_minutes', type=float),
            spotify_url=request.form.get('spotify_url'),
            notes=request.form.get('notes')
        )
        db.session.add(song)
        db.session.commit()
        flash('Song added!', 'success')
        return redirect(url_for('music_view', wedding_id=wedding_id))
    return render_template('music/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/music/<int:song_id>/delete', methods=['POST'])
@login_required
def music_delete(wedding_id, song_id):
    song = get_entity_or_404(Song, song_id, wedding_id)
    db.session.delete(song)
    db.session.commit()
    flash('Song removed.', 'success')
    return redirect(url_for('music_view', wedding_id=wedding_id))

# ============================================
# FLOWERS & DECOR ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/flowers')
@login_required
def flowers_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = wedding.floral_items
    return render_template('flowers/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/flowers/add', methods=['GET', 'POST'])
@login_required
def flowers_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = FloralItem(
            wedding_id=wedding_id,
            item_type=request.form.get('item_type'),
            recipient=request.form.get('recipient'),
            flowers=request.form.get('flowers'),
            colors=request.form.get('colors'),
            quantity=request.form.get('quantity', type=int) or 1,
            cost=request.form.get('cost', type=float),
            notes=request.form.get('notes')
        )
        db.session.add(item)
        db.session.commit()
        flash('Floral item added!', 'success')
        return redirect(url_for('flowers_view', wedding_id=wedding_id))
    return render_template('flowers/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/flowers/<int:item_id>/delete', methods=['POST'])
@login_required
def flowers_delete(wedding_id, item_id):
    item = get_entity_or_404(FloralItem, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Floral item removed.', 'success')
    return redirect(url_for('flowers_view', wedding_id=wedding_id))

# ============================================
# INVITATIONS & STATIONERY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/invitations')
@login_required
def invitations_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = wedding.invitations
    return render_template('invitations/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/invitations/add', methods=['GET', 'POST'])
@login_required
def invitations_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = Invitation(
            wedding_id=wedding_id,
            item_type=request.form.get('item_type'),
            designer=request.form.get('designer'),
            quantity=request.form.get('quantity', type=int),
            cost=request.form.get('cost', type=float),
            status=request.form.get('status', 'not_started'),
            notes=request.form.get('notes')
        )
        if request.form.get('send_by_date'):
            item.send_by_date = datetime.strptime(request.form.get('send_by_date'), '%Y-%m-%d').date()
        db.session.add(item)
        db.session.commit()
        flash('Stationery item added!', 'success')
        return redirect(url_for('invitations_view', wedding_id=wedding_id))
    return render_template('invitations/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/invitations/<int:item_id>/delete', methods=['POST'])
@login_required
def invitations_delete(wedding_id, item_id):
    item = get_entity_or_404(Invitation, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Stationery item removed.', 'success')
    return redirect(url_for('invitations_view', wedding_id=wedding_id))

# ============================================
# REHEARSAL DINNER ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/rehearsal')
@login_required
def rehearsal_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    rehearsal = wedding.rehearsal_dinner
    return render_template('rehearsal/view.html', wedding=wedding, rehearsal=rehearsal)

@app.route('/wedding/<int:wedding_id>/rehearsal/edit', methods=['GET', 'POST'])
@login_required
def rehearsal_edit(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    rehearsal = wedding.rehearsal_dinner
    if not rehearsal:
        rehearsal = RehearsalDinner(wedding_id=wedding_id)
        db.session.add(rehearsal)
        db.session.commit()
    if request.method == 'POST':
        if request.form.get('date'):
            rehearsal.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        if request.form.get('start_time'):
            rehearsal.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
        if request.form.get('end_time'):
            rehearsal.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
        rehearsal.venue_name = request.form.get('venue_name')
        rehearsal.venue_address = request.form.get('venue_address')
        rehearsal.venue_contact = request.form.get('venue_contact')
        rehearsal.venue_phone = request.form.get('venue_phone')
        rehearsal.expected_guest_count = request.form.get('expected_guest_count', type=int)
        rehearsal.menu_notes = request.form.get('menu_notes')
        rehearsal.notes = request.form.get('notes')
        db.session.commit()
        flash('Rehearsal dinner updated!', 'success')
        return redirect(url_for('rehearsal_view', wedding_id=wedding_id))
    return render_template('rehearsal/edit.html', wedding=wedding, rehearsal=rehearsal)

# ============================================
# ACCOMMODATIONS & TRANSPORTATION ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/accommodations')
@login_required
def accommodations_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = wedding.accommodations
    return render_template('accommodations/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/accommodations/add', methods=['GET', 'POST'])
@login_required
def accommodations_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = Accommodation(
            wedding_id=wedding_id,
            accommodation_type=request.form.get('accommodation_type'),
            name=request.form.get('name'),
            address=request.form.get('address'),
            phone=request.form.get('phone'),
            website=request.form.get('website'),
            block_code=request.form.get('block_code'),
            rate=request.form.get('rate'),
            rooms_reserved=request.form.get('rooms_reserved', type=int),
            welcome_bag=request.form.get('welcome_bag') == 'on',
            welcome_bag_items=request.form.get('welcome_bag_items'),
            notes=request.form.get('notes')
        )
        if request.form.get('deadline'):
            item.deadline = datetime.strptime(request.form.get('deadline'), '%Y-%m-%d').date()
        db.session.add(item)
        db.session.commit()
        flash('Accommodation added!', 'success')
        return redirect(url_for('accommodations_view', wedding_id=wedding_id))
    return render_template('accommodations/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/accommodations/<int:item_id>/delete', methods=['POST'])
@login_required
def accommodations_delete(wedding_id, item_id):
    item = get_entity_or_404(Accommodation, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Accommodation removed.', 'success')
    return redirect(url_for('accommodations_view', wedding_id=wedding_id))

# ============================================
# MARRIAGE LICENSE ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/license')
@login_required
def license_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    license_info = wedding.marriage_license
    return render_template('license/view.html', wedding=wedding, license_info=license_info)

@app.route('/wedding/<int:wedding_id>/license/edit', methods=['GET', 'POST'])
@login_required
def license_edit(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    license_info = wedding.marriage_license
    if not license_info:
        license_info = MarriageLicense(wedding_id=wedding_id)
        db.session.add(license_info)
        db.session.commit()
    if request.method == 'POST':
        license_info.county = request.form.get('county')
        license_info.state = request.form.get('state')
        if request.form.get('application_date'):
            license_info.application_date = datetime.strptime(request.form.get('application_date'), '%Y-%m-%d').date()
        if request.form.get('pickup_date'):
            license_info.pickup_date = datetime.strptime(request.form.get('pickup_date'), '%Y-%m-%d').date()
        if request.form.get('expiration_date'):
            license_info.expiration_date = datetime.strptime(request.form.get('expiration_date'), '%Y-%m-%d').date()
        if request.form.get('filing_deadline'):
            license_info.filing_deadline = datetime.strptime(request.form.get('filing_deadline'), '%Y-%m-%d').date()
        license_info.filed = request.form.get('filed') == 'on'
        if request.form.get('filed_date'):
            license_info.filed_date = datetime.strptime(request.form.get('filed_date'), '%Y-%m-%d').date()
        license_info.documents_needed = request.form.get('documents_needed')
        license_info.cost = request.form.get('cost', type=float)
        license_info.waiting_period_days = request.form.get('waiting_period_days', type=int)
        license_info.notes = request.form.get('notes')
        db.session.commit()
        flash('Marriage license info updated!', 'success')
        return redirect(url_for('license_view', wedding_id=wedding_id))
    return render_template('license/edit.html', wedding=wedding, license_info=license_info)

# ============================================
# HAIR & MAKEUP ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/hair-makeup')
@login_required
def hair_makeup_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    appointments = wedding.hair_makeup
    return render_template('hair_makeup/view.html', wedding=wedding, appointments=appointments)

@app.route('/wedding/<int:wedding_id>/hair-makeup/add', methods=['GET', 'POST'])
@login_required
def hair_makeup_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        appt = HairMakeup(
            wedding_id=wedding_id,
            person_name=request.form.get('person_name'),
            service_type=request.form.get('service_type'),
            stylist_name=request.form.get('stylist_name'),
            style_notes=request.form.get('style_notes'),
            cost=request.form.get('cost', type=float),
            notes=request.form.get('notes')
        )
        if request.form.get('appointment_time'):
            appt.appointment_time = datetime.strptime(request.form.get('appointment_time'), '%H:%M').time()
        if request.form.get('trial_date'):
            appt.trial_date = datetime.strptime(request.form.get('trial_date'), '%Y-%m-%d').date()
        db.session.add(appt)
        db.session.commit()
        flash('Appointment added!', 'success')
        return redirect(url_for('hair_makeup_view', wedding_id=wedding_id))
    return render_template('hair_makeup/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/hair-makeup/<int:appt_id>/delete', methods=['POST'])
@login_required
def hair_makeup_delete(wedding_id, appt_id):
    appt = get_entity_or_404(HairMakeup, appt_id, wedding_id)
    db.session.delete(appt)
    db.session.commit()
    flash('Appointment removed.', 'success')
    return redirect(url_for('hair_makeup_view', wedding_id=wedding_id))

# ============================================
# PLANNING MILESTONES ROUTES
# ============================================

MILESTONE_TEMPLATES = [
    (12, 'Set your total budget', 'budget', 'high'),
    (12, 'Book your ceremony venue', 'ceremony', 'high'),
    (12, 'Book your reception venue', 'reception', 'high'),
    (11, 'Hire a wedding planner/coordinator', 'planning', 'medium'),
    (10, 'Book photographer and videographer', 'vendors', 'high'),
    (10, 'Start building guest list', 'guests', 'high'),
    (9, 'Book caterer', 'vendors', 'high'),
    (9, 'Choose wedding party members', 'bridal_party', 'medium'),
    (8, 'Book florist', 'vendors', 'medium'),
    (8, 'Book DJ or band', 'vendors', 'medium'),
    (8, 'Shop for wedding attire', 'attire', 'high'),
    (7, 'Book officiant', 'ceremony', 'high'),
    (7, 'Create wedding website', 'planning', 'medium'),
    (6, 'Order invitations and stationery', 'stationery', 'high'),
    (6, 'Book hair and makeup artists', 'vendors', 'medium'),
    (6, 'Plan honeymoon and book travel', 'honeymoon', 'medium'),
    (5, 'Register for gifts', 'registry', 'medium'),
    (5, 'Book transportation', 'transportation', 'medium'),
    (5, 'Reserve hotel room blocks', 'accommodations', 'medium'),
    (4, 'Schedule dress/suit fittings', 'attire', 'medium'),
    (4, 'Plan rehearsal dinner', 'reception', 'medium'),
    (3, 'Send invitations', 'stationery', 'high'),
    (3, 'Order wedding cake', 'vendors', 'medium'),
    (3, 'Purchase wedding party gifts', 'gifts', 'medium'),
    (3, 'Write personal vows (if applicable)', 'ceremony', 'medium'),
    (2, 'Final dress/suit fitting', 'attire', 'high'),
    (2, 'Finalize seating chart', 'reception', 'high'),
    (2, 'Apply for marriage license', 'legal', 'high'),
    (2, 'Confirm all vendor details', 'vendors', 'high'),
    (2, 'Plan contingency/backup plans', 'planning', 'medium'),
    (1, 'Create day-of timeline', 'planning', 'high'),
    (1, 'Prepare tip envelopes for vendors', 'tips', 'high'),
    (1, 'Prepare welcome bags for hotel guests', 'accommodations', 'low'),
    (1, 'Final guest count to caterer', 'guests', 'high'),
    (1, 'Confirm honeymoon reservations', 'honeymoon', 'medium'),
    (1, 'Break in wedding shoes', 'attire', 'low'),
    (0, 'Pack emergency kit', 'planning', 'medium'),
    (0, 'Delegate day-of responsibilities', 'planning', 'medium'),
]

@app.route('/wedding/<int:wedding_id>/milestones/generate', methods=['POST'])
@login_required
def generate_milestones(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    wedding_date = wedding.wedding_date

    # Check if milestones already exist
    existing = Task.query.filter_by(wedding_id=wedding_id, is_milestone=True).count()
    if existing > 0:
        flash('Milestones already generated. Delete existing milestones first to regenerate.', 'warning')
        return redirect(url_for('tasks_view', wedding_id=wedding_id))

    from dateutil.relativedelta import relativedelta
    for months, title, category, priority in MILESTONE_TEMPLATES:
        due = wedding_date - relativedelta(months=months)
        # Don't create milestones in the past
        if due.date() < datetime.utcnow().date():
            due = datetime.utcnow()
        task = Task(
            wedding_id=wedding_id,
            title=title,
            due_date=due,
            priority=priority,
            category=category,
            is_milestone=True,
            months_before=months
        )
        db.session.add(task)
    db.session.commit()
    flash('Planning milestones generated based on your wedding date!', 'success')
    return redirect(url_for('tasks_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/milestones/clear', methods=['POST'])
@login_required
def clear_milestones(wedding_id):
    Task.query.filter_by(wedding_id=wedding_id, is_milestone=True).delete()
    db.session.commit()
    flash('All milestones cleared.', 'success')
    return redirect(url_for('tasks_view', wedding_id=wedding_id))

# ============================================
# CONTINGENCY PLAN ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/contingency')
@login_required
def contingency_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    plans = wedding.contingency_plans
    return render_template('contingency/view.html', wedding=wedding, plans=plans)

@app.route('/wedding/<int:wedding_id>/contingency/add', methods=['GET', 'POST'])
@login_required
def contingency_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        plan = ContingencyPlan(
            wedding_id=wedding_id,
            category=request.form.get('category'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            contact_name=request.form.get('contact_name'),
            contact_phone=request.form.get('contact_phone'),
            notes=request.form.get('notes')
        )
        db.session.add(plan)
        db.session.commit()
        flash('Contingency plan added!', 'success')
        return redirect(url_for('contingency_view', wedding_id=wedding_id))
    return render_template('contingency/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/contingency/<int:plan_id>/delete', methods=['POST'])
@login_required
def contingency_delete(wedding_id, plan_id):
    plan = get_entity_or_404(ContingencyPlan, plan_id, wedding_id)
    db.session.delete(plan)
    db.session.commit()
    flash('Contingency plan removed.', 'success')
    return redirect(url_for('contingency_view', wedding_id=wedding_id))

# ============================================
# BUDGET CATEGORY LIMIT ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/budget/category-limit', methods=['POST'])
@login_required
def budget_category_limit_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.budget:
        budget = Budget(wedding_id=wedding_id, total_budget=0)
        db.session.add(budget)
        db.session.commit()
    limit = BudgetCategoryLimit(
        budget_id=wedding.budget.id,
        category=request.form.get('category'),
        limit_amount=request.form.get('limit_amount', type=float)
    )
    db.session.add(limit)
    db.session.commit()
    flash('Category limit set!', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/budget/category-limit/<int:limit_id>/delete', methods=['POST'])
@login_required
def budget_category_limit_delete(wedding_id, limit_id):
    limit = get_entity_or_404(BudgetCategoryLimit, limit_id, wedding_id)
    db.session.delete(limit)
    db.session.commit()
    flash('Category limit removed.', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

# ============================================
# TIPPING TRACKER ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/tips')
@login_required
def tips_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    tips = wedding.tips
    total_suggested = sum(t.suggested_amount or 0 for t in tips)
    total_actual = sum(t.actual_amount or 0 for t in tips)
    envelopes_ready = sum(1 for t in tips if t.envelope_prepared)
    tips_given = sum(1 for t in tips if t.given)
    stats = {
        'total_suggested': total_suggested,
        'total_actual': total_actual,
        'envelopes_ready': envelopes_ready,
        'tips_given': tips_given,
        'total_tips': len(tips)
    }
    return render_template('tips/view.html', wedding=wedding, tips=tips, stats=stats)

@app.route('/wedding/<int:wedding_id>/tips/add', methods=['GET', 'POST'])
@login_required
def tips_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        tip = TipItem(
            wedding_id=wedding_id,
            recipient=request.form.get('recipient'),
            service_category=request.form.get('service_category'),
            suggested_amount=request.form.get('suggested_amount', type=float),
            actual_amount=request.form.get('actual_amount', type=float),
            payment_method=request.form.get('payment_method'),
            notes=request.form.get('notes')
        )
        db.session.add(tip)
        db.session.commit()
        flash('Tip added!', 'success')
        return redirect(url_for('tips_view', wedding_id=wedding_id))
    return render_template('tips/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/tips/<int:tip_id>/toggle-envelope', methods=['POST'])
@login_required
def tips_toggle_envelope(wedding_id, tip_id):
    tip = get_entity_or_404(TipItem, tip_id, wedding_id)
    tip.envelope_prepared = not tip.envelope_prepared
    db.session.commit()
    return redirect(url_for('tips_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/tips/<int:tip_id>/toggle-given', methods=['POST'])
@login_required
def tips_toggle_given(wedding_id, tip_id):
    tip = get_entity_or_404(TipItem, tip_id, wedding_id)
    tip.given = not tip.given
    db.session.commit()
    return redirect(url_for('tips_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/tips/<int:tip_id>/delete', methods=['POST'])
@login_required
def tips_delete(wedding_id, tip_id):
    tip = get_entity_or_404(TipItem, tip_id, wedding_id)
    db.session.delete(tip)
    db.session.commit()
    flash('Tip removed.', 'success')
    return redirect(url_for('tips_view', wedding_id=wedding_id))

# ============================================
# GIFT TRACKING ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/gifts')
@login_required
def gifts_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    gifts = wedding.gifts
    # Group by event
    shower_gifts = [g for g in gifts if g.event == 'shower']
    wedding_gifts = [g for g in gifts if g.event == 'wedding']
    engagement_gifts = [g for g in gifts if g.event == 'engagement']
    other_gifts = [g for g in gifts if g.event == 'other']
    thank_yous_pending = sum(1 for g in gifts if not g.thank_you_sent)
    total_value = sum(g.estimated_value or 0 for g in gifts)
    stats = {
        'total_gifts': len(gifts),
        'thank_yous_pending': thank_yous_pending,
        'total_value': total_value
    }
    return render_template('gifts/view.html', wedding=wedding, gifts=gifts,
                         shower_gifts=shower_gifts, wedding_gifts=wedding_gifts,
                         engagement_gifts=engagement_gifts, other_gifts=other_gifts,
                         stats=stats)

@app.route('/wedding/<int:wedding_id>/gifts/add', methods=['GET', 'POST'])
@login_required
def gifts_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        gift = Gift(
            wedding_id=wedding_id,
            event=request.form.get('event'),
            from_name=request.form.get('from_name'),
            description=request.form.get('description'),
            estimated_value=request.form.get('estimated_value', type=float),
            notes=request.form.get('notes')
        )
        if request.form.get('date_received'):
            gift.date_received = datetime.strptime(request.form.get('date_received'), '%Y-%m-%d').date()
        db.session.add(gift)
        db.session.commit()
        flash('Gift recorded!', 'success')
        return redirect(url_for('gifts_view', wedding_id=wedding_id))
    return render_template('gifts/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/gifts/<int:gift_id>/thank-you', methods=['POST'])
@login_required
def gifts_toggle_thank_you(wedding_id, gift_id):
    gift = get_entity_or_404(Gift, gift_id, wedding_id)
    gift.thank_you_sent = not gift.thank_you_sent
    if gift.thank_you_sent:
        gift.thank_you_sent_date = datetime.utcnow().date()
    else:
        gift.thank_you_sent_date = None
    db.session.commit()
    return redirect(url_for('gifts_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/gifts/<int:gift_id>/delete', methods=['POST'])
@login_required
def gifts_delete(wedding_id, gift_id):
    gift = get_entity_or_404(Gift, gift_id, wedding_id)
    db.session.delete(gift)
    db.session.commit()
    flash('Gift removed.', 'success')
    return redirect(url_for('gifts_view', wedding_id=wedding_id))

# ============================================
# GUEST RSVP PORTAL (PUBLIC - NO LOGIN REQUIRED)
# ============================================

@app.route('/rsvp/<token>')
def rsvp_portal(token):
    """Public RSVP portal - no login required."""
    wedding = Wedding.query.filter_by(rsvp_token=token).first_or_404()
    if not wedding.rsvp_enabled:
        return render_template('rsvp/disabled.html', wedding=wedding)
    guests = Guest.query.filter_by(wedding_id=wedding.id).order_by(Guest.name).all()
    menu_items = []
    if wedding.reception and wedding.reception.menu_items:
        menu_items = [m for m in wedding.reception.menu_items if m.course == 'entree']
    custom_questions = CustomRsvpQuestion.query.filter_by(wedding_id=wedding.id, active=True).order_by(CustomRsvpQuestion.order).all()
    return render_template('rsvp/portal.html', wedding=wedding, guests=guests,
                         menu_items=menu_items, token=token, custom_questions=custom_questions)

@app.route('/rsvp/<token>/submit', methods=['POST'])
@rate_limit(max_requests=20, window_seconds=3600)
def rsvp_submit(token):
    """Process RSVP submission from public portal."""
    wedding = Wedding.query.filter_by(rsvp_token=token).first_or_404()

    # Validate and sanitize all input
    is_valid, errors, data = validate_rsvp_submission(wedding, request.form)
    if not is_valid:
        for error in errors:
            flash(error, 'error')
        return redirect(url_for('rsvp_portal', token=token))

    guest_name = data['guest_name']
    rsvp_status = data['rsvp_status']
    meal_choice = data['meal_choice']
    dietary = data['dietary']
    rsvp_notes = data['rsvp_notes']
    plus_one_name = data['plus_one_name']

    guest = Guest.query.filter_by(wedding_id=wedding.id, name=guest_name).first()
    if not guest:
        # Allow new guests to RSVP (they type their name)
        guest = Guest(wedding_id=wedding.id, name=guest_name, guest_token=generate_token())
        db.session.add(guest)

    # Ensure guest has a check-in token
    if not guest.guest_token:
        guest.guest_token = generate_token()

    guest.rsvp_status = rsvp_status
    guest.rsvp_date = datetime.utcnow().date()
    guest.meal_choice = meal_choice if meal_choice else guest.meal_choice
    guest.dietary_restrictions = dietary if dietary else guest.dietary_restrictions
    guest.rsvp_notes = rsvp_notes
    if plus_one_name:
        guest.is_plus_one = False
        guest.plus_one_of = ''
        # Create plus one guest if doesn't exist
        existing_po = Guest.query.filter_by(wedding_id=wedding.id, name=plus_one_name).first()
        if not existing_po:
            po = Guest(wedding_id=wedding.id, name=plus_one_name, is_plus_one=True,
                       plus_one_of=guest_name, rsvp_status='accepted',
                       guest_token=generate_token())
            db.session.add(po)

    # Save custom RSVP question answers
    custom_questions = CustomRsvpQuestion.query.filter_by(wedding_id=wedding.id, active=True).all()
    for q in custom_questions:
        answer_text = request.form.get(f'custom_q_{q.id}', '').strip()
        if answer_text:
            existing_answer = CustomRsvpAnswer.query.filter_by(question_id=q.id, guest_id=guest.id).first()
            if existing_answer:
                existing_answer.answer_text = answer_text
            else:
                answer = CustomRsvpAnswer(question_id=q.id, guest_id=guest.id, answer_text=answer_text)
                db.session.add(answer)

    db.session.commit()

    # Set cookie so this guest is recognized at venue check-in
    response = make_response(render_template('rsvp/thank_you.html', wedding=wedding, guest=guest, token=token))
    response.set_cookie(
        f'guest_{wedding.id}',
        guest.guest_token,
        max_age=60 * 60 * 24 * 90,
        httponly=True,
        samesite='Lax',
    )
    return response

@app.route('/wedding/<int:wedding_id>/rsvp/enable', methods=['POST'])
@login_required
def rsvp_enable(wedding_id):
    """Enable/disable RSVP portal and generate token."""
    wedding = get_wedding_or_403(wedding_id)
    wedding.rsvp_enabled = not wedding.rsvp_enabled
    if wedding.rsvp_enabled and not wedding.rsvp_token:
        wedding.rsvp_token = generate_token()
    if request.form.get('rsvp_deadline'):
        parsed = safe_strptime(request.form.get('rsvp_deadline'), '%Y-%m-%d')
        if parsed:
            wedding.rsvp_deadline = parsed.date()
    if request.form.get('rsvp_message'):
        wedding.rsvp_message = request.form.get('rsvp_message')
    db.session.commit()
    status = 'enabled' if wedding.rsvp_enabled else 'disabled'
    flash(f'RSVP portal {status}!', 'success')
    return redirect(url_for('guests_view', wedding_id=wedding_id))

# ============================================
# GUEST CHECK-IN (PUBLIC - COOKIE-BASED)
# ============================================

@app.route('/g/<token>')
@rate_limit(max_requests=30, window_seconds=60)
def guest_identify(token):
    """Guest clicks personalized link (from email). Sets a cookie and shows their info."""
    guest = Guest.query.filter_by(guest_token=token).first_or_404()
    wedding = Wedding.query.get(guest.wedding_id)
    if not wedding:
        abort(404)

    table_name = None
    table_number = None
    if guest.seating_table:
        table_name = guest.seating_table.table_name
        table_number = guest.seating_table.table_number

    response = make_response(render_template('checkin/welcome.html',
        guest=guest, wedding=wedding,
        table_name=table_name, table_number=table_number))

    # Set a long-lived cookie so they're recognized at the venue
    response.set_cookie(
        f'guest_{wedding.id}',
        token,
        max_age=60 * 60 * 24 * 90,  # 90 days
        httponly=True,
        samesite='Lax',
    )
    return response


@app.route('/checkin/<rsvp_token>')
@rate_limit(max_requests=30, window_seconds=60)
def guest_checkin(rsvp_token):
    """QR code at the venue points here. Reads guest cookie to identify them."""
    wedding = Wedding.query.filter_by(rsvp_token=rsvp_token).first_or_404()

    # Try to identify the guest from their cookie
    guest_token = request.cookies.get(f'guest_{wedding.id}')
    guest = None
    if guest_token:
        guest = Guest.query.filter_by(guest_token=guest_token, wedding_id=wedding.id).first()

    table_name = None
    table_number = None
    if guest and guest.seating_table:
        table_name = guest.seating_table.table_name
        table_number = guest.seating_table.table_number

    return render_template('checkin/table.html',
        guest=guest, wedding=wedding,
        table_name=table_name, table_number=table_number,
        rsvp_token=rsvp_token)


@app.route('/checkin/<rsvp_token>/lookup', methods=['POST'])
@rate_limit(max_requests=10, window_seconds=60)
def guest_checkin_lookup(rsvp_token):
    """Fallback: guest types their name to find their table."""
    wedding = Wedding.query.filter_by(rsvp_token=rsvp_token).first_or_404()
    name = sanitize_string(request.form.get('name', ''), max_length=200)

    guest = Guest.query.filter(
        Guest.wedding_id == wedding.id,
        db.func.lower(Guest.name) == name.lower()
    ).first()

    table_name = None
    table_number = None
    if guest and guest.seating_table:
        table_name = guest.seating_table.table_name
        table_number = guest.seating_table.table_number

    # If found and guest has a token, set the cookie for next time
    response = make_response(render_template('checkin/table.html',
        guest=guest, wedding=wedding,
        table_name=table_name, table_number=table_number,
        rsvp_token=rsvp_token, searched_name=name))

    if guest and guest.guest_token:
        response.set_cookie(
            f'guest_{wedding.id}',
            guest.guest_token,
            max_age=60 * 60 * 24 * 90,
            httponly=True,
            samesite='Lax',
        )
    return response


@app.route('/wedding/<int:wedding_id>/guest-links')
@login_required
def guest_links(wedding_id):
    """Planner view: generate tokens and see personalized links for all guests."""
    wedding = get_wedding_or_403(wedding_id)
    guests = Guest.query.filter_by(wedding_id=wedding_id).order_by(Guest.name).all()

    # Auto-generate tokens for any guests that don't have one
    generated = 0
    for guest in guests:
        if not guest.guest_token:
            guest.guest_token = generate_token()
            generated += 1
    if generated:
        db.session.commit()

    checkin_url = None
    if wedding.rsvp_token:
        checkin_url = url_for('guest_checkin', rsvp_token=wedding.rsvp_token, _external=True)

    return render_template('checkin/guest_links.html',
        wedding=wedding, guests=guests, checkin_url=checkin_url)


@app.route('/wedding/<int:wedding_id>/guest-links/generate', methods=['POST'])
@login_required
def guest_links_generate(wedding_id):
    """Generate tokens for all guests that don't have one yet."""
    wedding = get_wedding_or_403(wedding_id)
    guests = Guest.query.filter_by(wedding_id=wedding_id).all()
    count = 0
    for guest in guests:
        if not guest.guest_token:
            guest.guest_token = generate_token()
            count += 1
    # Also ensure the wedding has an RSVP token for the check-in QR code
    if not wedding.rsvp_token:
        wedding.rsvp_token = generate_token()
    db.session.commit()
    flash(f'Generated links for {count} guests.', 'success')
    return redirect(url_for('guest_links', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/guests/<int:guest_id>/send-email', methods=['POST'])
@login_required
def guest_send_email(wedding_id, guest_id):
    """Send a single guest their personalized check-in link via email."""
    wedding = get_wedding_or_403(wedding_id)
    guest = get_entity_or_404(Guest, guest_id, wedding_id)

    if not guest.email:
        flash(f'No email address on file for {guest.name}.', 'error')
        return redirect(url_for('guest_links', wedding_id=wedding_id))

    if not guest.guest_token:
        guest.guest_token = generate_token()
        db.session.commit()

    guest_link = url_for('guest_identify', token=guest.guest_token, _external=True)
    email_type = request.form.get('email_type', 'checkin')
    custom_message = sanitize_string(request.form.get('message', ''), max_length=2000)

    if email_type == 'day_of':
        subject = f'Day-Of Details - {wedding.couple_names}'
        message = custom_message or (
            f"The big day is almost here! Here are your details for our wedding."
        )
        if guest.seating_table:
            table_info = guest.seating_table.table_name or f"Table {guest.seating_table.table_number}"
            message += f"\n\nYour table: {table_info}"
        if guest.meal_choice:
            message += f"\nYour meal: {guest.meal_choice}"
    else:
        subject = f'Your Check-In Link - {wedding.couple_names}'
        message = custom_message or (
            f"We're so excited to celebrate with you! "
            f"Click the link below to save your details. "
            f"At the venue, just scan the QR code to find your table."
        )

    send_guest_email(
        to_email=guest.email,
        guest_name=guest.name,
        couple_names=wedding.couple_names,
        wedding_date=wedding.wedding_date,
        subject=subject,
        message=message,
        guest_link=guest_link,
    )
    flash(f'Email sent to {guest.name}.', 'success')
    return redirect(url_for('guest_links', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/guests/send-day-of-emails', methods=['GET', 'POST'])
@login_required
def guest_send_day_of_emails(wedding_id):
    """Send day-of details to all accepted guests with email addresses."""
    wedding = get_wedding_or_403(wedding_id)

    eligible_guests = [
        g for g in wedding.guests
        if g.email and g.rsvp_status == 'accepted'
    ]

    if request.method == 'POST':
        custom_message = sanitize_string(request.form.get('message', ''), max_length=2000)
        sent_count = 0
        for guest in eligible_guests:
            if not guest.guest_token:
                guest.guest_token = generate_token()

            guest_link = url_for('guest_identify', token=guest.guest_token, _external=True)

            message = custom_message or (
                f"The big day is almost here! Here are your details for our wedding."
            )
            guest_message = message
            if guest.seating_table:
                table_info = guest.seating_table.table_name or f"Table {guest.seating_table.table_number}"
                guest_message += f"\n\nYour table: {table_info}"
            if guest.meal_choice:
                guest_message += f"\nYour meal: {guest.meal_choice}"

            send_guest_email(
                to_email=guest.email,
                guest_name=guest.name,
                couple_names=wedding.couple_names,
                wedding_date=wedding.wedding_date,
                subject=f'Day-Of Details - {wedding.couple_names}',
                message=guest_message,
                guest_link=guest_link,
            )
            sent_count += 1

        db.session.commit()
        flash(f'Day-of details sent to {sent_count} guests.', 'success')
        return redirect(url_for('guest_links', wedding_id=wedding_id))

    return render_template('checkin/send_day_of.html',
        wedding=wedding, eligible_guests=eligible_guests)


# ============================================
# GUEST MEAL COUNT SUMMARY
# ============================================

@app.route('/wedding/<int:wedding_id>/guests/meal-summary')
@login_required
def guest_meal_summary(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    guests = [g for g in wedding.guests if g.rsvp_status == 'accepted']
    meal_counts = {}
    dietary_counts = {}
    for g in guests:
        mc = g.meal_choice or 'Not Selected'
        meal_counts[mc] = meal_counts.get(mc, 0) + 1
        if g.dietary_restrictions:
            for d in g.dietary_restrictions.split(','):
                d = d.strip()
                if d:
                    dietary_counts[d] = dietary_counts.get(d, 0) + 1
    return render_template('guests/meal_summary.html', wedding=wedding,
                         meal_counts=meal_counts, dietary_counts=dietary_counts,
                         total_accepted=len(guests))

# ============================================
# SHAREABLE READ-ONLY LINK
# ============================================

@app.route('/wedding/<int:wedding_id>/share/enable', methods=['POST'])
@login_required
def share_enable(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.share_token:
        wedding.share_token = generate_token()
    db.session.commit()
    flash('Shareable link generated!', 'success')
    return redirect(url_for('wedding_dashboard', wedding_id=wedding_id))

@app.route('/shared/<token>')
def shared_view(token):
    """Public read-only view of wedding details."""
    wedding = Wedding.query.filter_by(share_token=token).first_or_404()
    stats = {
        'total_tasks': len(wedding.tasks),
        'pending_tasks': len([t for t in wedding.tasks if not t.completed]),
        'total_guests': len(wedding.guests),
        'rsvp_yes': len([g for g in wedding.guests if g.rsvp_status == 'accepted']),
        'total_vendors': len(wedding.vendors),
        'bridal_party_count': len(wedding.bridal_party),
    }
    return render_template('shared/dashboard.html', wedding=wedding, stats=stats, token=token)

# ============================================
# VENDOR COMMUNICATION LOG ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/vendors/<int:vendor_id>/notes')
@login_required
def vendor_notes_view(wedding_id, vendor_id):
    wedding = get_wedding_or_403(wedding_id)
    vendor = get_entity_or_404(Vendor, vendor_id, wedding_id)
    notes = VendorNote.query.filter_by(vendor_id=vendor_id).order_by(VendorNote.date.desc()).all()
    return render_template('vendors/notes.html', wedding=wedding, vendor=vendor, notes=notes)

@app.route('/wedding/<int:wedding_id>/vendors/<int:vendor_id>/notes/add', methods=['POST'])
@login_required
def vendor_note_add(wedding_id, vendor_id):
    note = VendorNote(
        vendor_id=vendor_id,
        note_type=request.form.get('note_type'),
        subject=request.form.get('subject'),
        content=request.form.get('content')
    )
    db.session.add(note)
    log_activity(wedding_id, 'created', 'vendor_note', request.form.get('subject'))
    db.session.commit()
    flash('Note added!', 'success')
    return redirect(url_for('vendor_notes_view', wedding_id=wedding_id, vendor_id=vendor_id))

@app.route('/wedding/<int:wedding_id>/vendors/<int:vendor_id>/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def vendor_note_delete(wedding_id, vendor_id, note_id):
    note = VendorNote.query.get_or_404(note_id)
    db.session.delete(note)
    db.session.commit()
    flash('Note removed.', 'success')
    return redirect(url_for('vendor_notes_view', wedding_id=wedding_id, vendor_id=vendor_id))

# ============================================
# VENDOR QUOTE COMPARISON ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/vendor-quotes')
@login_required
def vendor_quotes_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    quotes = VendorQuote.query.filter_by(wedding_id=wedding_id).order_by(VendorQuote.category).all()
    # Group by category
    grouped = {}
    for q in quotes:
        grouped.setdefault(q.category, []).append(q)
    return render_template('vendors/quotes.html', wedding=wedding, grouped_quotes=grouped)

@app.route('/wedding/<int:wedding_id>/vendor-quotes/add', methods=['GET', 'POST'])
@login_required
def vendor_quote_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        quote = VendorQuote(
            wedding_id=wedding_id,
            category=request.form.get('category'),
            vendor_name=request.form.get('vendor_name'),
            contact_info=request.form.get('contact_info'),
            quote_amount=request.form.get('quote_amount', type=float),
            package_details=request.form.get('package_details'),
            pros=request.form.get('pros'),
            cons=request.form.get('cons'),
            notes=request.form.get('notes')
        )
        if request.form.get('date_received'):
            quote.date_received = datetime.strptime(request.form.get('date_received'), '%Y-%m-%d').date()
        db.session.add(quote)
        log_activity(wedding_id, 'created', 'vendor_quote', request.form.get('vendor_name'))
        db.session.commit()
        flash('Quote added!', 'success')
        return redirect(url_for('vendor_quotes_view', wedding_id=wedding_id))
    return render_template('vendors/quote_add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/vendor-quotes/<int:quote_id>/select', methods=['POST'])
@login_required
def vendor_quote_select(wedding_id, quote_id):
    quote = VendorQuote.query.get_or_404(quote_id)
    quote.is_selected = not quote.is_selected
    db.session.commit()
    return redirect(url_for('vendor_quotes_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/vendor-quotes/<int:quote_id>/delete', methods=['POST'])
@login_required
def vendor_quote_delete(wedding_id, quote_id):
    quote = VendorQuote.query.get_or_404(quote_id)
    db.session.delete(quote)
    db.session.commit()
    flash('Quote removed.', 'success')
    return redirect(url_for('vendor_quotes_view', wedding_id=wedding_id))

# ============================================
# SPEECHES & TOASTS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/speeches')
@login_required
def speeches_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    speeches = SpeechToast.query.filter_by(wedding_id=wedding_id).order_by(SpeechToast.order).all()
    return render_template('speeches/view.html', wedding=wedding, speeches=speeches)

@app.route('/wedding/<int:wedding_id>/speeches/add', methods=['GET', 'POST'])
@login_required
def speeches_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        speech = SpeechToast(
            wedding_id=wedding_id,
            speaker_name=request.form.get('speaker_name'),
            speech_type=request.form.get('speech_type'),
            order=request.form.get('order', type=int) or 0,
            duration_minutes=request.form.get('duration_minutes', type=int),
            notes=request.form.get('notes')
        )
        db.session.add(speech)
        db.session.commit()
        flash('Speech/toast added!', 'success')
        return redirect(url_for('speeches_view', wedding_id=wedding_id))
    return render_template('speeches/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/speeches/<int:speech_id>/toggle-reviewed', methods=['POST'])
@login_required
def speeches_toggle_reviewed(wedding_id, speech_id):
    speech = get_entity_or_404(SpeechToast, speech_id, wedding_id)
    speech.reviewed = not speech.reviewed
    db.session.commit()
    return redirect(url_for('speeches_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/speeches/<int:speech_id>/delete', methods=['POST'])
@login_required
def speeches_delete(wedding_id, speech_id):
    speech = get_entity_or_404(SpeechToast, speech_id, wedding_id)
    db.session.delete(speech)
    db.session.commit()
    flash('Speech removed.', 'success')
    return redirect(url_for('speeches_view', wedding_id=wedding_id))

# ============================================
# WEDDING FAVORS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/favors')
@login_required
def favors_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    favors = WeddingFavor.query.filter_by(wedding_id=wedding_id).all()
    total_cost = sum(f.total_cost or 0 for f in favors)
    assembled_count = sum(1 for f in favors if f.assembled)
    return render_template('favors/view.html', wedding=wedding, favors=favors,
                         total_cost=total_cost, assembled_count=assembled_count)

@app.route('/wedding/<int:wedding_id>/favors/add', methods=['GET', 'POST'])
@login_required
def favors_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        qty = request.form.get('quantity', type=int) or 0
        cost_per = request.form.get('cost_per_item', type=float) or 0
        favor = WeddingFavor(
            wedding_id=wedding_id,
            description=request.form.get('description'),
            quantity=qty,
            cost_per_item=cost_per,
            total_cost=qty * cost_per,
            vendor=request.form.get('vendor'),
            assembly_notes=request.form.get('assembly_notes'),
            notes=request.form.get('notes')
        )
        if request.form.get('order_date'):
            favor.order_date = datetime.strptime(request.form.get('order_date'), '%Y-%m-%d').date()
        db.session.add(favor)
        db.session.commit()
        flash('Favor added!', 'success')
        return redirect(url_for('favors_view', wedding_id=wedding_id))
    return render_template('favors/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/favors/<int:favor_id>/toggle', methods=['POST'])
@login_required
def favors_toggle(wedding_id, favor_id):
    favor = get_entity_or_404(WeddingFavor, favor_id, wedding_id)
    favor.assembled = not favor.assembled
    db.session.commit()
    return redirect(url_for('favors_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/favors/<int:favor_id>/delete', methods=['POST'])
@login_required
def favors_delete(wedding_id, favor_id):
    favor = get_entity_or_404(WeddingFavor, favor_id, wedding_id)
    db.session.delete(favor)
    db.session.commit()
    flash('Favor removed.', 'success')
    return redirect(url_for('favors_view', wedding_id=wedding_id))

# ============================================
# CEREMONY VOW WRITING & SCRIPT ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/ceremony/vows', methods=['GET', 'POST'])
@login_required
def ceremony_vows(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    if not ceremony:
        ceremony = Ceremony(wedding_id=wedding_id)
        db.session.add(ceremony)
        db.session.commit()
    if request.method == 'POST':
        ceremony.vow_draft_person1 = request.form.get('vow_draft_person1')
        ceremony.vow_draft_person2 = request.form.get('vow_draft_person2')
        db.session.commit()
        flash('Vows saved!', 'success')
        return redirect(url_for('ceremony_vows', wedding_id=wedding_id))
    people = Person.query.filter_by(wedding_id=wedding_id).order_by(Person.display_order).all()
    return render_template('ceremony/vows.html', wedding=wedding, ceremony=ceremony, people=people)

@app.route('/wedding/<int:wedding_id>/ceremony/script', methods=['GET', 'POST'])
@login_required
def ceremony_script(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    if not ceremony:
        ceremony = Ceremony(wedding_id=wedding_id)
        db.session.add(ceremony)
        db.session.commit()
    if request.method == 'POST':
        ceremony.ceremony_script = request.form.get('ceremony_script')
        db.session.commit()
        flash('Script saved!', 'success')
        return redirect(url_for('ceremony_script', wedding_id=wedding_id))
    return render_template('ceremony/script.html', wedding=wedding, ceremony=ceremony)

# ============================================
# BUDGET TEMPLATE & ENHANCED ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/budget/apply-template', methods=['POST'])
@login_required
def budget_apply_template(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    template_key = request.form.get('template')
    template = BUDGET_TEMPLATES.get(template_key)
    if not template:
        flash('Template not found.', 'error')
        return redirect(url_for('budget_view', wedding_id=wedding_id))
    if not wedding.budget:
        budget = Budget(wedding_id=wedding_id, total_budget=template['total'])
        db.session.add(budget)
        db.session.commit()
    else:
        wedding.budget.total_budget = template['total']
    # Create category limits from template
    for cat, amount in template['categories'].items():
        existing = BudgetCategoryLimit.query.filter_by(
            budget_id=wedding.budget.id, category=cat).first()
        if not existing:
            limit = BudgetCategoryLimit(
                budget_id=wedding.budget.id, category=cat, limit_amount=amount)
            db.session.add(limit)
    db.session.commit()
    flash(f'Budget template "{template["name"]}" applied!', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/budget/payment-schedule')
@login_required
def budget_payment_schedule(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    budget = wedding.budget
    expenses = budget.expenses if budget else []
    # Get all items with due dates, sorted by date
    upcoming = sorted(
        [e for e in expenses if e.payment_due_date and e.payment_status != 'paid'],
        key=lambda x: x.payment_due_date
    )
    # Also get vendor payment dates
    vendor_payments = sorted(
        [v for v in wedding.vendors if v.final_payment_date and not (v.deposit_paid and v.balance_due == 0)],
        key=lambda x: x.final_payment_date
    )
    return render_template('budget/payment_schedule.html', wedding=wedding,
                         upcoming=upcoming, vendor_payments=vendor_payments)

# ============================================
# SEATING CHART & BUILDER ROUTES
# ============================================

# ============================================
# GUEST SOCIAL GROUPS
# ============================================

@app.route('/wedding/<int:wedding_id>/guest-groups')
@login_required
def guest_groups_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    groups = GuestGroup.query.filter_by(wedding_id=wedding_id).order_by(GuestGroup.name).all()
    attending = [g for g in wedding.guests if g.rsvp_status == 'accepted']

    # Build a summary of how many guests are in each group
    group_counts = {}
    for grp in groups:
        count = 0
        for guest in attending:
            if guest.social_groups:
                tags = [t.strip() for t in guest.social_groups.split(',')]
                if grp.name in tags:
                    count += 1
        group_counts[grp.id] = count

    # Find all unique tags currently in use
    all_tags = set()
    for guest in wedding.guests:
        if guest.social_groups:
            for tag in guest.social_groups.split(','):
                tag = tag.strip()
                if tag:
                    all_tags.add(tag)

    return render_template('guests/groups.html', wedding=wedding, groups=groups,
                         group_counts=group_counts, all_tags=sorted(all_tags),
                         suggested=SUGGESTED_GROUP_TYPES, guests=attending)


@app.route('/wedding/<int:wedding_id>/guest-groups/add', methods=['POST'])
@login_required
def guest_group_add(wedding_id):
    name = request.form.get('name', '').strip()
    if not name:
        flash('Group name is required.', 'warning')
        return redirect(url_for('guest_groups_view', wedding_id=wedding_id))

    existing = GuestGroup.query.filter_by(wedding_id=wedding_id, name=name).first()
    if existing:
        flash(f'Group "{name}" already exists.', 'warning')
        return redirect(url_for('guest_groups_view', wedding_id=wedding_id))

    group = GuestGroup(
        wedding_id=wedding_id,
        name=name,
        color=request.form.get('color', ''),
        seat_together=request.form.get('seat_together') != 'off',
        priority=request.form.get('priority', 5, type=int),
        notes=request.form.get('notes', '')
    )
    db.session.add(group)
    db.session.commit()
    log_activity(wedding_id, 'added', 'guest_group', name)
    flash(f'Group "{name}" created!', 'success')
    return redirect(url_for('guest_groups_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/guest-groups/<int:group_id>/delete', methods=['POST'])
@login_required
def guest_group_delete(wedding_id, group_id):
    group = get_entity_or_404(GuestGroup, group_id, wedding_id)
    name = group.name
    db.session.delete(group)
    db.session.commit()
    flash(f'Group "{name}" deleted.', 'success')
    return redirect(url_for('guest_groups_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/guest-groups/<int:group_id>/assign', methods=['POST'])
@login_required
def guest_group_bulk_assign(wedding_id, group_id):
    """Add a social group tag to multiple guests at once."""
    group = get_entity_or_404(GuestGroup, group_id, wedding_id)
    guest_ids = request.form.getlist('guest_ids')
    count = 0
    for gid in guest_ids:
        guest = Guest.query.get(int(gid))
        if guest:
            existing_tags = [t.strip() for t in (guest.social_groups or '').split(',') if t.strip()]
            if group.name not in existing_tags:
                existing_tags.append(group.name)
                guest.social_groups = ', '.join(existing_tags)
                count += 1
    db.session.commit()
    flash(f'Added {count} guests to "{group.name}".', 'success')
    return redirect(url_for('guest_groups_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/guest-groups/<int:group_id>/remove-guest/<int:guest_id>', methods=['POST'])
@login_required
def guest_group_remove_guest(wedding_id, group_id, guest_id):
    """Remove a social group tag from a single guest."""
    group = get_entity_or_404(GuestGroup, group_id, wedding_id)
    guest = get_entity_or_404(Guest, guest_id, wedding_id)
    if guest.social_groups:
        tags = [t.strip() for t in guest.social_groups.split(',') if t.strip()]
        tags = [t for t in tags if t != group.name]
        guest.social_groups = ', '.join(tags) if tags else None
        db.session.commit()
    flash(f'{guest.name} removed from "{group.name}".', 'success')
    return redirect(url_for('guest_groups_view', wedding_id=wedding_id))


def compute_table_pixel_size(table, scale=1.4):
    """Return (width_px, height_px) for a table at the given scale."""
    ref = TABLE_SIZE_REFERENCE.get(table.table_size)
    shape = table.table_shape or 'round'
    cap = table.capacity
    if ref:
        if shape in ('round', 'oval'):
            tw = ref.get('diameter', 60) * scale
            th = tw if shape == 'round' else tw * 0.67
        elif shape == 'rectangular':
            tw = ref.get('length', 72) * scale
            th = ref.get('width', 30) * scale
        elif shape == 'square':
            tw = ref.get('side', 48) * scale
            th = tw
        else:
            tw = ref.get('length', 96) * scale
            th = ref.get('width', 30) * scale
    else:
        if shape in ('round', 'oval'):
            diameter = 24 + cap * 5
            tw = diameter * scale
            th = tw if shape == 'round' else tw * 0.67
        elif shape in ('rectangular', 'serpentine'):
            tw = (48 + max(0, cap - 4) * 12) * scale
            th = 30 * scale
        elif shape == 'square':
            side = 24 + cap * 6
            tw = side * scale
            th = tw
        else:
            diameter = 24 + cap * 5
            tw = diameter * scale
            th = tw
    return (round(tw), round(th))


# Real-world spacing constants (inches)
CHAIR_PUSHBACK_INCHES = 24   # space from table edge to back of pushed-out chair
AISLE_CLEARANCE_INCHES = 42  # comfortable aisle between chair backs


def compute_grid_position(index, table, scale=1.4, cols=4, offset_x=50, offset_y=50):
    """Compute (x, y) position for a table in a grid layout with proper spacing.

    Spacing accounts for table size + chair pushback + aisle clearance
    so tables don't overlap on the canvas.
    """
    tw, th = compute_table_pixel_size(table, scale)
    # Edge-to-edge clearance in pixels
    clearance = (CHAIR_PUSHBACK_INCHES * 2 + AISLE_CLEARANCE_INCHES) * scale
    # Cell size = table + surrounding clearance
    cell_w = tw + clearance
    cell_h = th + clearance
    col = index % cols
    row = index // cols
    x = offset_x + col * cell_w
    y = offset_y + row * cell_h
    return (round(x), round(y))


def compute_table_floor_data(tables, scale=1.4):
    """Compute SVG floor plan rendering data for a list of tables.

    Returns a dict keyed by table.id with dimensions, center point,
    and chair positions (with filled/empty status).
    """
    CHAIR_GAP = 14
    PAD = 22

    result = {}
    for table in tables:
        ref = TABLE_SIZE_REFERENCE.get(table.table_size)
        shape = table.table_shape or 'round'
        cap = table.capacity
        assigned_count = len(table.assigned_guests)

        if ref:
            if shape in ('round', 'oval'):
                tw = ref.get('diameter', 60) * scale
                th = tw if shape == 'round' else tw * 0.67
            elif shape == 'rectangular':
                tw = ref.get('length', 72) * scale
                th = ref.get('width', 30) * scale
            elif shape == 'square':
                tw = ref.get('side', 48) * scale
                th = tw
            else:
                tw = ref.get('length', 96) * scale
                th = ref.get('width', 30) * scale
        else:
            # Fallback: estimate from capacity using real-world table sizes
            # Round: 2→36", 4→48", 6→48", 8→60", 10→72", 12→84"
            # Rectangular: width ~30", length scales with capacity
            if shape in ('round', 'oval'):
                diameter = 24 + cap * 5  # inches, matches industry standards
                tw = diameter * scale
                th = tw if shape == 'round' else tw * 0.67
            elif shape in ('rectangular', 'serpentine'):
                tw = (48 + max(0, cap - 4) * 12) * scale  # length grows with seats
                th = 30 * scale  # standard banquet width
            elif shape == 'square':
                side = 24 + cap * 6  # inches
                tw = side * scale
                th = tw
            else:
                diameter = 24 + cap * 5
                tw = diameter * scale
                th = tw

        tw = round(tw)
        th = round(th)
        svg_w = tw + PAD * 2
        svg_h = th + PAD * 2
        cx = svg_w / 2
        cy = svg_h / 2

        chairs = []
        one_sided = ref.get('one_sided', False) if ref else False

        if shape in ('round', 'oval'):
            rx = tw / 2 + CHAIR_GAP
            ry = th / 2 + CHAIR_GAP
            for i in range(cap):
                angle = (2 * math.pi * i / cap) - math.pi / 2
                x = round(cx + rx * math.cos(angle), 1)
                y = round(cy + ry * math.sin(angle), 1)
                chairs.append({'x': x, 'y': y, 'filled': i < assigned_count})
        elif shape == 'square':
            # Square: distribute evenly around all 4 sides
            perimeter = 4 * tw
            spacing = perimeter / cap if cap > 0 else perimeter
            for i in range(cap):
                dist = spacing * i + spacing / 2
                if dist < tw:
                    x, y = PAD + dist, PAD - CHAIR_GAP
                elif dist < 2 * tw:
                    x, y = PAD + tw + CHAIR_GAP, PAD + (dist - tw)
                elif dist < 3 * tw:
                    x, y = PAD + tw - (dist - 2 * tw), PAD + tw + CHAIR_GAP
                else:
                    x, y = PAD - CHAIR_GAP, PAD + tw - (dist - 3 * tw)
                chairs.append({'x': round(x, 1), 'y': round(y, 1), 'filled': i < assigned_count})
        else:
            # Rectangular/serpentine: chairs along long sides only
            if one_sided:
                # Head table: all chairs on one side (front, facing audience)
                spacing = tw / cap if cap > 0 else tw
                for i in range(cap):
                    x = PAD + spacing * i + spacing / 2
                    y = PAD + th + CHAIR_GAP
                    chairs.append({'x': round(x, 1), 'y': round(y, 1), 'filled': i < assigned_count})
            else:
                # Standard banquet: split chairs between top and bottom long sides
                top_count = cap // 2
                bottom_count = cap - top_count
                # Top side (left to right)
                if top_count > 0:
                    spacing = tw / top_count
                    for i in range(top_count):
                        x = PAD + spacing * i + spacing / 2
                        y = PAD - CHAIR_GAP
                        chairs.append({'x': round(x, 1), 'y': round(y, 1), 'filled': len(chairs) < assigned_count})
                # Bottom side (left to right)
                if bottom_count > 0:
                    spacing = tw / bottom_count
                    for i in range(bottom_count):
                        x = PAD + spacing * i + spacing / 2
                        y = PAD + th + CHAIR_GAP
                        chairs.append({'x': round(x, 1), 'y': round(y, 1), 'filled': len(chairs) < assigned_count})

        # Apply rotation (swap dimensions and rotate chair positions)
        rotation = getattr(table, 'rotation', 0) or 0
        if rotation in (90, 270):
            # Swap table dimensions and SVG bounds
            tw, th = th, tw
            svg_w = tw + PAD * 2
            svg_h = th + PAD * 2
            new_cx = svg_w / 2
            new_cy = svg_h / 2
            # Rotate each chair around the center
            cos_a = math.cos(math.radians(rotation))
            sin_a = math.sin(math.radians(rotation))
            for chair in chairs:
                dx = chair['x'] - cx
                dy = chair['y'] - cy
                chair['x'] = round(new_cx + dx * cos_a - dy * sin_a, 1)
                chair['y'] = round(new_cy + dx * sin_a + dy * cos_a, 1)
            cx, cy = new_cx, new_cy

        result[table.id] = {
            'tw': tw, 'th': th,
            'svg_w': svg_w, 'svg_h': svg_h,
            'cx': cx, 'cy': cy,
            'chairs': chairs,
            'rotation': rotation,
        }
    return result


@app.route('/wedding/<int:wedding_id>/seating-chart')
@login_required
def seating_chart(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    tables = reception.seating_tables if reception else []
    fixtures = reception.venue_fixtures if reception else []
    all_guests = wedding.guests
    all_attending = [g for g in all_guests if g.rsvp_status == 'accepted']
    # Unassigned includes all guests without a table (regardless of RSVP status)
    unassigned = [g for g in all_guests if not g.table_id and g.rsvp_status != 'declined']
    # Count guests awaiting RSVP who are assigned to tables
    pending_assigned = [g for g in all_guests if g.table_id and g.rsvp_status != 'accepted']
    preferences = SeatingPreference.query.filter_by(wedding_id=wedding_id).all()

    # Build stats
    total_capacity = sum(t.capacity for t in tables)
    total_attending = len(all_attending)
    total_assigned = len([g for g in all_guests if g.table_id])

    # Check for constraint violations (using dict lookup instead of nested loop)
    guest_table_map = {g.id: g.table_id for g in all_guests}
    violations = []
    for pref in preferences:
        guest_table = guest_table_map.get(pref.guest_id)
        other_table = guest_table_map.get(pref.other_guest_id)
        if guest_table and other_table:
            if pref.preference_type == 'together' and guest_table != other_table:
                violations.append(f'{pref.guest.name} and {pref.other_guest.name} should sit together but are at different tables')
            elif pref.preference_type == 'apart' and guest_table == other_table:
                violations.append(f'{pref.guest.name} and {pref.other_guest.name} should sit apart but are at the same table')

    # Flag guests assigned to tables who haven't accepted RSVP
    if pending_assigned:
        for g in pending_assigned:
            violations.append(f'{g.name} is assigned to a table but RSVP status is "{g.rsvp_status or "pending"}"')

    # Detect "lonely" guests — assigned to a table but share no household, social group, or side with tablemates
    lonely_guests = []
    for table in tables:
        assigned = table.assigned_guests
        if len(assigned) <= 1:
            continue
        for guest in assigned:
            guest_tags = set()
            if guest.household_group:
                guest_tags.add(('household', guest.household_group.strip().lower()))
            if guest.social_groups:
                for tag in guest.social_groups.split(','):
                    tag = tag.strip()
                    if tag:
                        guest_tags.add(('social', tag.lower()))
            if guest.side:
                guest_tags.add(('side', guest.side.strip().lower()))

            has_connection = False
            for other in assigned:
                if other.id == guest.id:
                    continue
                other_tags = set()
                if other.household_group:
                    other_tags.add(('household', other.household_group.strip().lower()))
                if other.social_groups:
                    for tag in other.social_groups.split(','):
                        tag = tag.strip()
                        if tag:
                            other_tags.add(('social', tag.lower()))
                if other.side:
                    other_tags.add(('side', other.side.strip().lower()))
                if guest_tags & other_tags:
                    has_connection = True
                    break

            if not has_connection and guest_tags:
                table_name = table.table_name or f'Table {table.table_number}'
                lonely_guests.append(f'{guest.name} at {table_name} — doesn\'t share a group, household, or side with any tablemate')

    stats = {
        'total_capacity': total_capacity,
        'total_attending': total_attending,
        'total_assigned': total_assigned,
        'total_unassigned': len(unassigned),
        'pending_rsvp_assigned': len(pending_assigned),
        'lonely_guest_count': len(lonely_guests),
        'capacity_surplus': total_capacity - total_attending,
    }

    table_floor_data = compute_table_floor_data(tables)

    # Compute fixture pixel data
    SCALE = 1.4
    fixture_floor_data = {}
    for f in fixtures:
        fw = round(f.width_inches * SCALE)
        fh = round(f.height_inches * SCALE)
        fixture_floor_data[f.id] = {'w': fw, 'h': fh}

    # Compute canvas size to fit all tables and fixtures with padding
    canvas_w = 900  # minimum width
    canvas_h = 600  # minimum height
    for table in tables:
        fd = table_floor_data[table.id]
        right = (table.x_position or 0) + fd['svg_w'] + 20
        bottom = (table.y_position or 0) + fd['svg_h'] + 40
        canvas_w = max(canvas_w, right)
        canvas_h = max(canvas_h, bottom)
    for f in fixtures:
        ffd = fixture_floor_data[f.id]
        right = (f.x_position or 0) + ffd['w'] + 20
        bottom = (f.y_position or 0) + ffd['h'] + 40
        canvas_w = max(canvas_w, right)
        canvas_h = max(canvas_h, bottom)

    # Detect tables that are too close together (overlapping clearance zones)
    min_clearance_px = (CHAIR_PUSHBACK_INCHES * 2 + 24) * SCALE  # bare minimum: chairs + 24" passage
    # ADA requires 36" clear aisle for wheelchair access
    ada_min_px = 36 * SCALE
    proximity_warnings = []
    accessibility_warnings = []

    # Collect all obstacle bounding boxes (tables + fixtures)
    obstacles = []
    for table in tables:
        fd = table_floor_data[table.id]
        ox = (table.x_position or 0) + (fd['svg_w'] - fd['tw']) / 2
        oy = (table.y_position or 0) + (fd['svg_h'] - fd['th']) / 2
        obstacles.append({
            'name': table.table_name or f'Table {table.table_number}',
            'x': ox, 'y': oy, 'w': fd['tw'], 'h': fd['th'],
            'is_table': True,
        })
    for f in fixtures:
        ffd = fixture_floor_data[f.id]
        obstacles.append({
            'name': f.label or VENUE_FIXTURE_TYPES.get(f.fixture_type, {}).get('label', f.fixture_type),
            'x': f.x_position or 0, 'y': f.y_position or 0,
            'w': ffd['w'], 'h': ffd['h'],
            'is_table': False,
        })

    for i, o1 in enumerate(obstacles):
        for o2 in obstacles[i+1:]:
            dx = abs((o1['x'] + o1['w']/2) - (o2['x'] + o2['w']/2))
            dy = abs((o1['y'] + o1['h']/2) - (o2['y'] + o2['h']/2))
            edge_dx = max(0, dx - o1['w']/2 - o2['w']/2)
            edge_dy = max(0, dy - o1['h']/2 - o2['h']/2)
            edge_dist = math.sqrt(edge_dx**2 + edge_dy**2)

            # Table-to-table needs chair clearance
            if o1['is_table'] and o2['is_table']:
                if edge_dist < min_clearance_px:
                    real_inches = round(edge_dist / SCALE)
                    proximity_warnings.append(
                        f'{o1["name"]} and {o2["name"]} are too close ({real_inches}" apart — need at least 84" for chairs + aisle)'
                    )

            # Any pair: check ADA wheelchair clearance (36")
            if edge_dist < ada_min_px:
                real_inches = round(edge_dist / SCALE)
                accessibility_warnings.append(
                    f'{o1["name"]} and {o2["name"]} have only {real_inches}" clearance — wheelchairs need at least 36"'
                )

    # Dietary balance warnings — flag tables where >60% of guests share a restriction
    dietary_warnings = []
    for table in tables:
        guests = table.assigned_guests
        if len(guests) < 3:
            continue
        restriction_counts = {}
        for g in guests:
            if g.dietary_restrictions:
                for r in g.dietary_restrictions.split(','):
                    r = r.strip().lower()
                    if r:
                        restriction_counts[r] = restriction_counts.get(r, 0) + 1
        for restriction, count in restriction_counts.items():
            if count >= len(guests) * 0.6 and count >= 3:
                tname = table.table_name or f'Table {table.table_number}'
                dietary_warnings.append(
                    f'{tname}: {count}/{len(guests)} guests have "{restriction}" — consider spreading dietary needs across tables'
                )

    return render_template('seating/chart.html', wedding=wedding, tables=tables,
                         fixtures=fixtures,
                         unassigned_guests=unassigned, preferences=preferences,
                         violations=violations, lonely_guests=lonely_guests, stats=stats,
                         proximity_warnings=proximity_warnings,
                         accessibility_warnings=accessibility_warnings,
                         dietary_warnings=dietary_warnings,
                         canvas_w=round(canvas_w), canvas_h=round(canvas_h),
                         table_size_ref=TABLE_SIZE_REFERENCE, table_roles=TABLE_ROLES,
                         table_floor_data=table_floor_data,
                         fixture_floor_data=fixture_floor_data,
                         fixture_types=VENUE_FIXTURE_TYPES)


@app.route('/wedding/<int:wedding_id>/seating-chart/table/add', methods=['POST'])
@login_required
def seating_table_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    if not reception:
        flash('Please set up reception details first.', 'warning')
        return redirect(url_for('seating_chart', wedding_id=wedding_id))

    preset = request.form.get('preset')
    if preset and preset in TABLE_SIZE_REFERENCE:
        ref = TABLE_SIZE_REFERENCE[preset]
        shape = ref['shape']
        capacity = ref['capacity']
        size = preset
        name_label = ref['label']
    else:
        shape = request.form.get('table_shape', 'round')
        capacity = request.form.get('capacity', 8, type=int)
        size = request.form.get('table_size', '')
        name_label = ''

    # Auto-number
    existing_count = len(reception.seating_tables)
    table_number = str(existing_count + 1)

    table = SeatingTable(
        reception_id=reception.id,
        table_number=table_number,
        table_name=request.form.get('table_name', '') or name_label,
        capacity=capacity,
        table_shape=shape,
        table_size=size,
        table_role=request.form.get('table_role', 'guest'),
        notes=request.form.get('notes', '')
    )
    # Compute proper grid position based on table dimensions
    pos_x, pos_y = compute_grid_position(existing_count, table)
    table.x_position = pos_x
    table.y_position = pos_y
    db.session.add(table)
    db.session.commit()
    log_activity(wedding_id, 'added', 'table', f'Table {table_number}')
    flash(f'Table {table_number} added!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/table/<int:table_id>/edit', methods=['POST'])
@login_required
def seating_table_edit(wedding_id, table_id):
    table = get_entity_or_404(SeatingTable, table_id, wedding_id)
    table.table_name = request.form.get('table_name', '')
    table.table_shape = request.form.get('table_shape', 'round')
    table.capacity = request.form.get('capacity', 8, type=int)
    table.table_size = request.form.get('table_size', '')
    table.table_role = request.form.get('table_role', 'guest')
    table.notes = request.form.get('notes', '')
    db.session.commit()
    flash(f'Table {table.table_number} updated!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/table/<int:table_id>/delete', methods=['POST'])
@login_required
def seating_table_delete(wedding_id, table_id):
    table = get_entity_or_404(SeatingTable, table_id, wedding_id)
    # Unassign guests from this table
    for g in table.assigned_guests:
        g.table_id = None
    db.session.delete(table)
    db.session.commit()
    flash('Table removed. Guests have been unassigned.', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/tables/bulk-add', methods=['POST'])
@login_required
def seating_tables_bulk_add(wedding_id):
    """Add multiple tables at once from a preset configuration."""
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    if not reception:
        flash('Please set up reception details first.', 'warning')
        return redirect(url_for('seating_chart', wedding_id=wedding_id))

    count = request.form.get('count', 1, type=int)
    preset = request.form.get('preset', 'round_60')
    include_head = request.form.get('include_head') == 'on'
    include_kids = request.form.get('include_kids') == 'on'

    existing = len(reception.seating_tables)
    ref = TABLE_SIZE_REFERENCE.get(preset, TABLE_SIZE_REFERENCE['round_60'])

    added = 0
    grid_index = 0  # tracks position in the guest table grid
    # Compute clearance for the selected table type
    clearance_px = (CHAIR_PUSHBACK_INCHES * 2 + AISLE_CLEARANCE_INCHES) * 1.4

    # Determine where guest tables start (below head table if present)
    guest_start_y = 50

    # Optionally add head table first
    if include_head:
        existing += 1
        head = SeatingTable(
            reception_id=reception.id,
            table_number=str(existing),
            table_name='Head Table',
            capacity=request.form.get('head_capacity', 8, type=int),
            table_shape='rectangular',
            table_size='head_16ft',
            table_role='head',
        )
        head_tw, head_th = compute_table_pixel_size(head)
        head.x_position = 50
        head.y_position = 30
        guest_start_y = 30 + head_th + clearance_px
        db.session.add(head)
        added += 1

    # Add guest tables in a grid layout with proper spacing
    # Build a temporary table object to compute its pixel size
    sample = SeatingTable(table_shape=ref['shape'], table_size=preset, capacity=ref['capacity'])
    sample_tw, sample_th = compute_table_pixel_size(sample)
    cell_w = sample_tw + clearance_px
    cell_h = sample_th + clearance_px

    for i in range(count):
        existing += 1
        col = i % 4
        row = i // 4
        table = SeatingTable(
            reception_id=reception.id,
            table_number=str(existing),
            table_name=f'{ref["label"]}',
            capacity=ref['capacity'],
            table_shape=ref['shape'],
            table_size=preset,
            table_role='guest',
            x_position=round(50 + col * cell_w),
            y_position=round(guest_start_y + row * cell_h),
        )
        db.session.add(table)
        added += 1
        grid_index = i

    # Optionally add kids table (placed after the last guest table)
    if include_kids:
        existing += 1
        kids = SeatingTable(
            reception_id=reception.id,
            table_number=str(existing),
            table_name='Kids Table',
            capacity=request.form.get('kids_capacity', 8, type=int),
            table_shape='round',
            table_size='round_60',
            table_role='kids',
        )
        next_i = grid_index + 1
        kids_col = next_i % 4
        kids_row = next_i // 4
        kids.x_position = round(50 + kids_col * cell_w)
        kids.y_position = round(guest_start_y + kids_row * cell_h)
        db.session.add(kids)
        added += 1

    db.session.commit()
    log_activity(wedding_id, 'added', 'tables', f'{added} tables')
    flash(f'{added} tables added!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/assign', methods=['POST'])
@login_required
def seating_assign(wedding_id):
    guest_id = request.form.get('guest_id', type=int)
    table_id = request.form.get('table_id', type=int)
    guest = get_entity_or_404(Guest, guest_id, wedding_id)
    guest.table_id = table_id if table_id else None
    db.session.commit()
    msg = f'{guest.name} assigned!'
    category = 'success'
    if table_id:
        warnings = []
        table = SeatingTable.query.get(table_id)
        if table and len(table.assigned_guests) > table.capacity:
            warnings.append(f'table is now over capacity ({len(table.assigned_guests)}/{table.capacity})')
        if guest.rsvp_status != 'accepted':
            warnings.append(f'RSVP status is "{guest.rsvp_status or "pending"}"')
        if warnings:
            msg += ' Note: ' + '; '.join(warnings) + '.'
            category = 'warning'
    flash(msg, category)
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/unassign/<int:guest_id>', methods=['POST'])
@login_required
def seating_unassign(wedding_id, guest_id):
    guest = get_entity_or_404(Guest, guest_id, wedding_id)
    guest.table_id = None
    db.session.commit()
    flash(f'{guest.name} unassigned.', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/bulk-assign', methods=['POST'])
@login_required
def seating_bulk_assign(wedding_id):
    table_id = request.form.get('table_id', type=int)
    guest_ids = request.form.getlist('guest_ids')
    assigned = 0
    pending_count = 0
    for gid in guest_ids:
        guest = Guest.query.get(int(gid))
        if guest:
            guest.table_id = table_id
            assigned += 1
            if guest.rsvp_status != 'accepted':
                pending_count += 1
    db.session.commit()
    msg = f'{assigned} guests assigned!'
    if pending_count:
        msg += f' ({pending_count} have not yet accepted their RSVP.)'
    flash(msg, 'success' if pending_count == 0 else 'warning')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/clear-all', methods=['POST'])
@login_required
def seating_clear_all(wedding_id):
    """Remove all guest-to-table assignments."""
    wedding = get_wedding_or_403(wedding_id)
    for g in wedding.guests:
        g.table_id = None
    db.session.commit()
    flash('All seating assignments cleared.', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/update-position', methods=['POST'])
@login_required
def seating_update_position(wedding_id):
    """AJAX endpoint for drag-and-drop table positioning."""
    table_id = request.json.get('table_id')
    x = request.json.get('x')
    y = request.json.get('y')
    table = get_entity_or_404(SeatingTable, table_id, wedding_id)
    table.x_position = x
    table.y_position = y
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/wedding/<int:wedding_id>/seating-chart/table/<int:table_id>/rotate', methods=['POST'])
@login_required
def seating_table_rotate(wedding_id, table_id):
    """AJAX endpoint to rotate a table by 90 degrees."""
    table = get_entity_or_404(SeatingTable, table_id, wedding_id)
    current = table.rotation or 0
    table.rotation = (current + 90) % 360
    db.session.commit()
    return jsonify({'status': 'ok', 'rotation': table.rotation})


# --- Venue Fixtures (dance floor, bar, stage, etc.) ---

@app.route('/wedding/<int:wedding_id>/seating-chart/fixture/add', methods=['POST'])
@login_required
def fixture_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    if not reception:
        flash('Please set up reception details first.', 'warning')
        return redirect(url_for('seating_chart', wedding_id=wedding_id))

    fixture_type = request.form.get('fixture_type', '')
    preset = VENUE_FIXTURE_TYPES.get(fixture_type)

    if preset:
        width = preset['width']
        height = preset['height']
        label = preset['label']
    else:
        width = request.form.get('width_inches', 72, type=int)
        height = request.form.get('height_inches', 36, type=int)
        label = request.form.get('label', 'Custom Fixture')

    # Place below existing tables/fixtures
    y_offset = 50
    for t in reception.seating_tables:
        y_offset = max(y_offset, (t.y_position or 0) + 150)
    for f in reception.venue_fixtures:
        y_offset = max(y_offset, (f.y_position or 0) + 100)

    fixture = VenueFixture(
        reception_id=reception.id,
        fixture_type=fixture_type or 'custom',
        label=request.form.get('label', '') or label,
        width_inches=width,
        height_inches=height,
        x_position=50,
        y_position=round(y_offset + 30),
        notes=request.form.get('notes', ''),
    )
    db.session.add(fixture)
    db.session.commit()
    flash(f'{fixture.label} added to floor plan!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/fixture/<int:fixture_id>/delete', methods=['POST'])
@login_required
def fixture_delete(wedding_id, fixture_id):
    get_wedding_or_403(wedding_id)
    fixture = get_entity_or_404(VenueFixture, fixture_id, wedding_id)
    db.session.delete(fixture)
    db.session.commit()
    flash('Fixture removed from floor plan.', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/fixture/update-position', methods=['POST'])
@login_required
def fixture_update_position(wedding_id):
    """AJAX endpoint for drag-and-drop fixture positioning."""
    fixture_id = request.json.get('fixture_id')
    x = request.json.get('x')
    y = request.json.get('y')
    fixture = get_entity_or_404(VenueFixture, fixture_id, wedding_id)
    fixture.x_position = x
    fixture.y_position = y
    db.session.commit()
    return jsonify({'status': 'ok'})


# --- Seating Preferences (together/apart) ---

@app.route('/wedding/<int:wedding_id>/seating-chart/preferences')
@login_required
def seating_preferences(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    preferences = SeatingPreference.query.filter_by(wedding_id=wedding_id).all()
    attending = [g for g in wedding.guests if g.rsvp_status == 'accepted']
    return render_template('seating/preferences.html', wedding=wedding,
                         preferences=preferences, guests=attending)


@app.route('/wedding/<int:wedding_id>/seating-chart/preferences/add', methods=['POST'])
@login_required
def seating_preference_add(wedding_id):
    guest_id = request.form.get('guest_id', type=int)
    other_guest_id = request.form.get('other_guest_id', type=int)
    pref_type = request.form.get('preference_type', 'together')
    priority = request.form.get('priority', 5, type=int)
    notes = request.form.get('notes', '')

    if guest_id == other_guest_id:
        flash('Cannot create a preference for the same guest.', 'warning')
        return redirect(url_for('seating_preferences', wedding_id=wedding_id))

    # Check for contradictory reverse preference (A→B "together" vs B→A "apart")
    reverse = SeatingPreference.query.filter_by(
        wedding_id=wedding_id, guest_id=other_guest_id, other_guest_id=guest_id
    ).first()
    if reverse and reverse.preference_type != pref_type:
        guest = Guest.query.get(guest_id)
        other = Guest.query.get(other_guest_id)
        flash(f'Conflict: {other.name} & {guest.name} already have a "{reverse.preference_type}" preference. '
              f'Remove it first before adding a "{pref_type}" preference.', 'warning')
        return redirect(url_for('seating_preferences', wedding_id=wedding_id))

    # Check for duplicate (same direction)
    existing = SeatingPreference.query.filter_by(
        wedding_id=wedding_id, guest_id=guest_id, other_guest_id=other_guest_id
    ).first()
    if existing:
        existing.preference_type = pref_type
        existing.priority = priority
        existing.notes = notes
    else:
        pref = SeatingPreference(
            wedding_id=wedding_id,
            guest_id=guest_id,
            other_guest_id=other_guest_id,
            preference_type=pref_type,
            priority=priority,
            notes=notes
        )
        db.session.add(pref)
    db.session.commit()
    guest = Guest.query.get(guest_id)
    other = Guest.query.get(other_guest_id)
    flash(f'Preference: {guest.name} & {other.name} → {pref_type}', 'success')
    return redirect(url_for('seating_preferences', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/preferences/<int:pref_id>/delete', methods=['POST'])
@login_required
def seating_preference_delete(wedding_id, pref_id):
    pref = get_entity_or_404(SeatingPreference, pref_id, wedding_id)
    db.session.delete(pref)
    db.session.commit()
    flash('Preference removed.', 'success')
    return redirect(url_for('seating_preferences', wedding_id=wedding_id))


# --- Auto-Assign Algorithm ---

@app.route('/wedding/<int:wedding_id>/seating-chart/auto-assign', methods=['POST'])
@login_required
def seating_auto_assign(wedding_id):
    """Auto-assign guests to tables using a constraint-based algorithm.

    Strategy:
    1. Group guests by household_group / side / guest_type
    2. Honor 'together' preferences by merging groups
    3. Honor 'apart' preferences by ensuring separation
    4. Assign kids to kids tables first
    5. Fill VIP/head tables first with family, then fill guest tables
    6. Try to keep groups together at the same table
    """
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    if not reception:
        flash('No reception set up.', 'warning')
        return redirect(url_for('seating_chart', wedding_id=wedding_id))

    tables = reception.seating_tables
    if not tables:
        flash('Add tables before auto-assigning.', 'warning')
        return redirect(url_for('seating_chart', wedding_id=wedding_id))

    strategy = request.form.get('strategy', 'balanced')
    only_unassigned = request.form.get('only_unassigned') == 'on'

    # Get attending guests
    if only_unassigned:
        guests_to_assign = [g for g in wedding.guests if g.rsvp_status == 'accepted' and not g.table_id]
    else:
        # Clear all assignments first
        for g in wedding.guests:
            if g.rsvp_status == 'accepted':
                g.table_id = None
        guests_to_assign = [g for g in wedding.guests if g.rsvp_status == 'accepted']

    if not guests_to_assign:
        flash('No guests to assign.', 'info')
        return redirect(url_for('seating_chart', wedding_id=wedding_id))

    # Load preferences (sorted by priority so higher-priority constraints are processed first)
    prefs = SeatingPreference.query.filter_by(wedding_id=wedding_id).all()
    together_pairs = sorted(
        [(p.guest_id, p.other_guest_id, p.priority) for p in prefs if p.preference_type == 'together'],
        key=lambda x: -x[2]  # highest priority first
    )
    apart_pairs = [(p.guest_id, p.other_guest_id, p.priority) for p in prefs if p.preference_type == 'apart']

    # Build guest groups using Union-Find for "together" constraints
    guest_ids = {g.id for g in guests_to_assign}
    parent = {gid: gid for gid in guest_ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Merge from "together" preferences (already sorted by priority, highest first)
    for a, b, priority in together_pairs:
        if a in guest_ids and b in guest_ids:
            union(a, b)

    # Also merge by household_group (case-insensitive, whitespace-normalized)
    household_map = {}
    for g in guests_to_assign:
        if g.household_group:
            key = g.household_group.strip().lower()
            if key in household_map:
                union(g.id, household_map[key])
            else:
                household_map[key] = g.id

    # Also group plus-ones with their hosts (case-insensitive, whitespace-normalized)
    name_to_id = {g.name.strip().lower(): g.id for g in guests_to_assign if g.name}
    for g in guests_to_assign:
        if g.is_plus_one and g.plus_one_of:
            host_key = g.plus_one_of.strip().lower()
            if host_key in name_to_id:
                union(g.id, name_to_id[host_key])

    # Build actual groups
    from collections import defaultdict
    groups = defaultdict(list)
    for g in guests_to_assign:
        groups[find(g.id)].append(g)

    # Build apart-set (which group roots must not share a table) with priority
    apart_roots = {}  # (root_a, root_b) -> priority
    for a, b, priority in apart_pairs:
        if a in guest_ids and b in guest_ids:
            key = (find(a), find(b))
            apart_roots[key] = max(apart_roots.get(key, 0), priority)

    # --- Social Group Affinity ---
    # Build a map: group_root -> set of social tags
    group_tags = {}
    for root, members in groups.items():
        tags = set()
        for g in members:
            if g.social_groups:
                for tag in g.social_groups.split(','):
                    tag = tag.strip()
                    if tag:
                        tags.add(tag)
        group_tags[root] = tags

    # Load group priorities from GuestGroup definitions
    defined_groups = GuestGroup.query.filter_by(wedding_id=wedding_id).all()
    group_priority = {dg.name: dg.priority for dg in defined_groups}
    group_seat_together = {dg.name: dg.seat_together for dg in defined_groups}

    def affinity_score(root_a, root_b):
        """Compute how much two groups want to be at the same table.
        Higher score = more affinity. Based on shared social tags."""
        tags_a = group_tags.get(root_a, set())
        tags_b = group_tags.get(root_b, set())
        shared = tags_a & tags_b
        score = 0
        for tag in shared:
            if group_seat_together.get(tag, True):  # default to True
                score += group_priority.get(tag, 5)
        # Also boost if same side
        sides_a = {g.side for g in groups[root_a] if g.side}
        sides_b = {g.side for g in groups[root_b] if g.side}
        if sides_a & sides_b:
            score += 2
        return score

    # Categorize tables by role
    role_tables = defaultdict(list)
    for t in tables:
        role = t.table_role or 'guest'
        role_tables[role].append(t)

    # Sort groups by traits for smart placement
    guest_lookup = {g.id: g for g in guests_to_assign}

    # Track which groups have accessibility needs
    groups_with_accessibility = set()
    for root, members in groups.items():
        if any(g.accessibility_needs for g in members):
            groups_with_accessibility.add(root)

    def group_sort_key(grp):
        """Priority: accessibility first, kids next, then family, then friends."""
        root = find(grp[0].id)
        has_accessibility = root in groups_with_accessibility
        types = [g.guest_type for g in grp]
        if has_accessibility:
            return (0, 0, -len(grp))
        if any(t == 'child' or t == 'kid' for t in types):
            return (0, 1, -len(grp))
        if any(t == 'family' for t in types):
            return (1, 0, -len(grp))
        if any(t == 'vip' for t in types):
            return (2, 0, -len(grp))
        return (3, 0, -len(grp))

    sorted_groups = sorted(groups.values(), key=group_sort_key)

    # Track assignments: table_id -> set of root group ids assigned
    table_assignments = defaultdict(set)  # table_id -> set of group roots
    table_counts = {}
    for t in tables:
        existing = len([g for g in t.assigned_guests if g.id not in guest_ids])
        table_counts[t.id] = existing

    def can_place(group_root, table, group_size):
        """Check if placing this group at this table violates constraints."""
        if table_counts.get(table.id, 0) + group_size > table.capacity:
            return False
        # Check apart constraints (respect priority — only block if priority >= 3)
        for assigned_root in table_assignments[table.id]:
            priority = apart_roots.get((group_root, assigned_root), 0) or apart_roots.get((assigned_root, group_root), 0)
            if priority >= 3:
                return False
        return True

    # Sort tables by table_number for accessibility preference (lower = closer to entrance)
    tables_by_number = sorted(tables, key=lambda t: t.table_number)

    def table_affinity(group_root, table):
        """Score how well this group fits at this table based on who's already there."""
        score = 0
        for existing_root in table_assignments[table.id]:
            score += affinity_score(group_root, existing_root)
        # Boost score for lower-numbered tables when group has accessibility needs
        if group_root in groups_with_accessibility:
            idx = tables_by_number.index(table) if table in tables_by_number else len(tables)
            score += max(0, len(tables) - idx)  # higher score for lower table numbers
        return score

    def place_group(grp, table):
        root = find(grp[0].id)
        for g in grp:
            g.table_id = table.id
        table_counts[table.id] = table_counts.get(table.id, 0) + len(grp)
        table_assignments[table.id].add(root)

    # Assignment pass
    unplaced = []
    for grp in sorted_groups:
        root = find(grp[0].id)
        placed = False

        # Determine preferred table type
        types = [g.guest_type for g in grp]
        is_kids = any(t in ('child', 'kid') for t in types)
        is_family = any(t == 'family' for t in types)

        # Try role-appropriate tables first
        preferred_roles = []
        if is_kids and role_tables.get('kids'):
            preferred_roles.append('kids')
        if is_family and role_tables.get('vip'):
            preferred_roles.append('vip')
        preferred_roles.append('guest')  # fallback

        # Find best table: prefer tables with highest affinity to this group
        best_table = None
        best_score = -1

        for role in preferred_roles:
            candidates = [t for t in role_tables.get(role, []) if can_place(root, t, len(grp))]
            for table in candidates:
                score = table_affinity(root, table)
                if score > best_score:
                    best_score = score
                    best_table = table

        if best_table:
            place_group(grp, best_table)
            placed = True

        if not placed:
            # Try any table with space, still preferring affinity
            candidates = [(table_affinity(root, t), t) for t in tables if can_place(root, t, len(grp))]
            candidates.sort(key=lambda x: -x[0])
            if candidates:
                place_group(grp, candidates[0][1])
                placed = True

        if not placed:
            unplaced.extend(grp)

    # Try to place remaining individually
    still_unplaced = 0
    for g in unplaced:
        placed = False
        for table in tables:
            if table_counts.get(table.id, 0) < table.capacity:
                g.table_id = table.id
                table_counts[table.id] = table_counts.get(table.id, 0) + 1
                placed = True
                break
        if not placed:
            still_unplaced += 1

    db.session.commit()
    assigned_count = len(guests_to_assign) - still_unplaced
    log_activity(wedding_id, 'auto-assigned', 'seating', f'{assigned_count} guests')

    msg = f'Auto-assigned {assigned_count} guests to tables!'
    if still_unplaced:
        msg += f' ({still_unplaced} could not be placed - not enough capacity.)'
    flash(msg, 'success' if still_unplaced == 0 else 'warning')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))

# ============================================
# POST-WEDDING TASKS GENERATION
# ============================================

@app.route('/wedding/<int:wedding_id>/tasks/generate-post-wedding', methods=['POST'])
@login_required
def generate_post_wedding_tasks(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    wedding_date = wedding.wedding_date
    count = 0
    for i, (title, category, priority) in enumerate(POST_WEDDING_TASKS):
        due = wedding_date + timedelta(days=7 + i * 3)  # stagger over weeks after wedding
        task = Task(
            wedding_id=wedding_id,
            title=title,
            due_date=due,
            priority=priority,
            category=category
        )
        db.session.add(task)
        count += 1
    db.session.commit()
    flash(f'{count} post-wedding tasks generated!', 'success')
    return redirect(url_for('tasks_view', wedding_id=wedding_id))

# ============================================
# EXPORT ROUTES (CSV, PRINTABLE)
# ============================================

@app.route('/wedding/<int:wedding_id>/export/guests')
@login_required
def export_guests_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Email', 'Phone', 'Address', 'RSVP Status', 'Meal Choice',
                     'Dietary Restrictions', 'Side', 'Guest Type', 'Table',
                     'Plus One', 'Gift Received', 'Thank You Sent'])
    for g in wedding.guests:
        table_name = ''
        if g.seating_table:
            table_name = g.seating_table.table_name or g.seating_table.table_number
        writer.writerow([
            g.name, g.email or '', g.phone or '', g.address or '',
            g.rsvp_status or 'pending', g.meal_choice or '', g.dietary_restrictions or '',
            g.side or '', g.guest_type or '', table_name,
            g.plus_one_of if g.is_plus_one else '', 'Yes' if g.gift_received else 'No',
            'Yes' if g.thank_you_sent else 'No'
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=guests_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/budget')
@login_required
def export_budget_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    budget = wedding.budget
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Item', 'Estimated Cost', 'Actual Cost', 'Paid Amount',
                     'Payment Status', 'Due Date', 'Covered By', 'Notes'])
    if budget:
        for e in budget.expenses:
            writer.writerow([
                e.category, e.item_name, e.estimated_cost or 0, e.actual_cost or 0,
                e.paid_amount or 0, e.payment_status or '', str(e.payment_due_date or ''),
                e.covered_by or '', e.notes or ''
            ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=budget_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/tasks')
@login_required
def export_tasks_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Description', 'Due Date', 'Priority', 'Category',
                     'Assigned To', 'Completed', 'Milestone'])
    for t in wedding.tasks:
        writer.writerow([
            t.title, t.description or '', str(t.due_date.date()) if t.due_date else '',
            t.priority, t.category or '', t.assigned_to or '',
            'Yes' if t.completed else 'No', 'Yes' if t.is_milestone else 'No'
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=tasks_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/vendors')
@login_required
def export_vendors_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Business Name', 'Contact', 'Email', 'Phone',
                     'Total Cost', 'Deposit', 'Balance Due', 'Service Date'])
    for v in wedding.vendors:
        writer.writerow([
            v.category, v.business_name, v.contact_name or '', v.email or '', v.phone or '',
            v.total_cost or 0, v.deposit_amount or 0, v.balance_due or 0,
            str(v.service_date or '')
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=vendors_{wedding_id}.csv'
    return response

def _render_or_pdf(template, filename, **context):
    """Render a template as HTML, or as a PDF download if ?format=pdf is in the query string."""
    html = render_template(template, **context)
    if request.args.get('format') == 'pdf':
        from weasyprint import HTML, CSS
        pdf = HTML(string=html).write_pdf(
            stylesheets=[CSS(string='@media print { .print-btn, .share-form-inline { display: none !important; } }')],
            presentational_hints=True
        )
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    return html

@app.route('/wedding/<int:wedding_id>/print/timeline')
@login_required
def print_timeline(wedding_id):
    """Printable day-of timeline."""
    wedding = get_wedding_or_403(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    return _render_or_pdf('print/timeline.html', f'timeline_{wedding_id}.pdf',
                          wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/print/vendor-contacts')
@login_required
def print_vendor_contacts(wedding_id):
    """Printable vendor contact sheet."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/vendor_contacts.html', f'vendor_contacts_{wedding_id}.pdf',
                          wedding=wedding, vendors=wedding.vendors)

@app.route('/wedding/<int:wedding_id>/print/shot-list')
@login_required
def print_shot_list(wedding_id):
    """Printable photography shot list."""
    wedding = get_wedding_or_403(wedding_id)
    shots = sorted(wedding.photo_shots, key=lambda x: (x.category or '', x.priority or ''))
    return _render_or_pdf('print/shot_list.html', f'shot_list_{wedding_id}.pdf',
                          wedding=wedding, shots=shots)

@app.route('/wedding/<int:wedding_id>/print/emergency-contacts')
@login_required
def print_emergency_contacts(wedding_id):
    """Printable emergency contact card."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/emergency_contacts.html', f'emergency_contacts_{wedding_id}.pdf',
                          wedding=wedding, vendors=wedding.vendors, participants=wedding.participants)

@app.route('/wedding/<int:wedding_id>/print/seating')
@login_required
def print_seating(wedding_id):
    """Printable seating chart with visual floor plan."""
    wedding = get_wedding_or_403(wedding_id)
    tables = wedding.reception.seating_tables if wedding.reception else []
    fixtures = wedding.reception.venue_fixtures if wedding.reception else []
    table_floor_data = compute_table_floor_data(tables, scale=1.0)
    fixture_floor_data = {}
    scale = 1.4
    for f in fixtures:
        fixture_floor_data[f.id] = {
            'w': int(f.width_inches * scale),
            'h': int(f.height_inches * scale),
        }
    return _render_or_pdf('print/seating.html', f'seating_{wedding_id}.pdf',
                          wedding=wedding, tables=tables,
                          table_floor_data=table_floor_data,
                          fixtures=fixtures,
                          fixture_floor_data=fixture_floor_data,
                          fixture_types=VENUE_FIXTURE_TYPES)

@app.route('/wedding/<int:wedding_id>/print')
@login_required
def print_center(wedding_id):
    """Print Center - all printable documents in one place."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('print/print_center.html', wedding=wedding)


def _generate_pdf_bytes(template_name, **context):
    """Render a template and return PDF bytes via WeasyPrint."""
    from weasyprint import HTML, CSS
    html = render_template(template_name, **context)
    return HTML(string=html).write_pdf(
        stylesheets=[CSS(string='@media print { .print-btn, .share-btn, .share-form-inline { display: none !important; } }')],
        presentational_hints=True
    )


# Mapping of document types to their template, filename pattern, and data-gathering logic.
PRINT_DOCUMENTS = {
    'timeline':            {'title': 'Day-Of Timeline',       'template': 'print/timeline.html',            'filename': 'timeline'},
    'vendor_contacts':     {'title': 'Vendor Contacts',       'template': 'print/vendor_contacts.html',     'filename': 'vendor_contacts'},
    'shot_list':           {'title': 'Photography Shot List', 'template': 'print/shot_list.html',           'filename': 'shot_list'},
    'emergency_contacts':  {'title': 'Emergency Contacts',    'template': 'print/emergency_contacts.html',  'filename': 'emergency_contacts'},
    'seating':             {'title': 'Seating Chart',         'template': 'print/seating.html',             'filename': 'seating'},
    'ceremony_program':    {'title': 'Ceremony Program',      'template': 'print/ceremony_program.html',    'filename': 'ceremony_program'},
    'music_cue_sheet':     {'title': 'Music Cue Sheet',       'template': 'print/music_cue_sheet.html',     'filename': 'music_cue_sheet'},
    'guest_list':          {'title': 'Guest List',            'template': 'print/guest_list.html',           'filename': 'guest_list'},
    'tips_tracker':        {'title': 'Tips & Payments',       'template': 'print/tips_tracker.html',         'filename': 'tips'},
    'hair_makeup':         {'title': 'Hair & Makeup Schedule','template': 'print/hair_makeup.html',          'filename': 'hair_makeup'},
    'bridal_party':        {'title': 'Wedding Party',         'template': 'print/bridal_party.html',         'filename': 'bridal_party'},
    'venue_info':          {'title': 'Venue Information',     'template': 'print/venue_info.html',           'filename': 'venue_info'},
    'decor_setup':         {'title': 'Decor & Setup Plan',    'template': 'print/decor_setup.html',          'filename': 'decor_setup'},
    'reception_script':    {'title': 'Reception Run Sheet',   'template': 'print/reception_script.html',     'filename': 'reception_script'},
    'emergency_kit':       {'title': 'Emergency Kit Checklist','template': 'print/emergency_kit.html',       'filename': 'emergency_kit'},
    'rehearsal':           {'title': 'Rehearsal Schedule',    'template': 'print/rehearsal.html',             'filename': 'rehearsal'},
    'transportation':      {'title': 'Transportation & Hotels','template': 'print/transportation.html',      'filename': 'transportation'},
    'contingency_plans':   {'title': 'Backup Plans',          'template': 'print/contingency_plans.html',    'filename': 'contingency_plans'},
    'budget_summary':      {'title': 'Budget Summary',        'template': 'print/budget_summary.html',       'filename': 'budget'},
    'etiquette_guide':     {'title': 'Wedding Etiquette Guide','template': 'print/etiquette_guide.html',     'filename': 'etiquette_guide'},
    'pacing_guide':        {'title': 'Pacing Your Wedding Day','template': 'print/pacing_guide.html',       'filename': 'pacing_guide'},
    'hosting_guide':       {'title': 'Hosting & Thank-You',    'template': 'print/hosting_guide.html',      'filename': 'hosting_guide'},
    'vendor_tipping_guide':{'title': 'Vendor Etiquette & Tipping','template': 'print/vendor_tipping_guide.html','filename': 'vendor_tipping_guide'},
    'speeches_guide':      {'title': 'Speech & Toast Guide',   'template': 'print/speeches_guide.html',     'filename': 'speeches_guide'},
    'wedding_party_guide': {'title': 'Wedding Party Guide',    'template': 'print/wedding_party_guide.html', 'filename': 'wedding_party_guide'},
}


def _get_print_context(document_type, wedding):
    """Build the template context dict for a given document type."""
    ctx = {'wedding': wedding}
    if document_type == 'timeline':
        ctx['items'] = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    elif document_type == 'vendor_contacts':
        ctx['vendors'] = wedding.vendors
    elif document_type == 'shot_list':
        ctx['shots'] = sorted(wedding.photo_shots, key=lambda x: (x.category or '', x.priority or ''))
    elif document_type == 'emergency_contacts':
        ctx['vendors'] = wedding.vendors
        ctx['participants'] = wedding.participants
    elif document_type == 'seating':
        tables = wedding.reception.seating_tables if wedding.reception else []
        fixtures = wedding.reception.venue_fixtures if wedding.reception else []
        ctx['tables'] = tables
        ctx['table_floor_data'] = compute_table_floor_data(tables, scale=1.0)
        ctx['fixtures'] = fixtures
        scale = 1.4
        ctx['fixture_floor_data'] = {f.id: {'w': int(f.width_inches * scale), 'h': int(f.height_inches * scale)} for f in fixtures}
        ctx['fixture_types'] = VENUE_FIXTURE_TYPES
    elif document_type == 'ceremony_program':
        ceremony = wedding.ceremony
        ctx['ceremony'] = ceremony
        ctx['readings'] = sorted(ceremony.readings, key=lambda x: (x.order or 0)) if ceremony and ceremony.readings else []
        ctx['timeline_items'] = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony and ceremony.timeline_items else []
        ctx['bridal_party'] = sorted(wedding.bridal_party, key=lambda x: (x.processional_order or 999))
    elif document_type == 'music_cue_sheet':
        ctx['ceremony'] = wedding.ceremony
        ctx['songs'] = sorted(wedding.songs, key=lambda x: (x.moment or '', x.order or 0))
    elif document_type == 'guest_list':
        ctx['guests'] = sorted(wedding.guests, key=lambda x: x.name)
    elif document_type == 'tips_tracker':
        ctx['tips'] = sorted(wedding.tips, key=lambda x: (x.service_category or '', x.recipient))
    elif document_type == 'hair_makeup':
        ctx['appointments'] = sorted(wedding.hair_makeup, key=lambda x: (x.appointment_time or datetime.min.time()))
    elif document_type == 'bridal_party':
        ctx['bridal_party'] = sorted(wedding.bridal_party, key=lambda x: (x.side or '', x.processional_order or 999))
    elif document_type == 'venue_info':
        ctx['ceremony'] = wedding.ceremony
        ctx['reception'] = wedding.reception
        ctx['vendors'] = wedding.vendors
        ctx['accommodations'] = wedding.accommodations if hasattr(wedding, 'accommodations') else []
    elif document_type == 'decor_setup':
        ctx['reception'] = wedding.reception
        ctx['floral_items'] = sorted(wedding.floral_items, key=lambda x: (x.item_type or ''))
        ctx['inventory_items'] = wedding.inventory_items
    elif document_type == 'reception_script':
        reception = wedding.reception
        ctx['reception'] = reception
        ctx['reception_items'] = sorted(reception.timeline_items, key=lambda x: (x.order or 0)) if reception and reception.timeline_items else []
        ctx['songs'] = sorted(wedding.songs, key=lambda x: (x.moment or '', x.order or 0))
        ctx['speeches'] = sorted(wedding.speeches, key=lambda x: (x.order or 0))
    elif document_type == 'emergency_kit':
        if not wedding.emergency_kit_items:
            seed_default_emergency_kit(wedding.id)
        ctx['kit_items'] = sorted(wedding.emergency_kit_items, key=lambda x: (x.category or '', x.item_name))
    elif document_type == 'rehearsal':
        ctx['rehearsal_dinner'] = wedding.rehearsal_dinner
        ceremony = wedding.ceremony
        ctx['ceremony_items'] = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony and ceremony.timeline_items else []
        ctx['bridal_party'] = sorted(wedding.bridal_party, key=lambda x: (x.processional_order or 999))
    elif document_type == 'transportation':
        ctx['accommodations'] = wedding.accommodations if hasattr(wedding, 'accommodations') else []
    elif document_type == 'contingency_plans':
        ctx['plans'] = sorted(wedding.contingency_plans, key=lambda x: (x.category or ''))
    elif document_type == 'budget_summary':
        budget = wedding.budget
        ctx['budget'] = budget
        ctx['expenses'] = sorted(budget.expenses, key=lambda x: (x.category or '', x.item_name)) if budget else []
    return ctx


@app.route('/wedding/<int:wedding_id>/print/share', methods=['POST'])
@login_required
def print_share(wedding_id):
    """Email a print document as a PDF attachment."""
    wedding = get_wedding_or_403(wedding_id)

    document_type = request.form.get('document_type', '').strip()
    recipient_email = request.form.get('recipient_email', '').strip()
    recipient_name = request.form.get('recipient_name', '').strip()
    message = request.form.get('message', '').strip()

    # Validate document type
    if document_type not in PRINT_DOCUMENTS:
        flash('Invalid document type.', 'error')
        return redirect(url_for('print_center', wedding_id=wedding_id))

    # Validate email
    if not recipient_email or not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', recipient_email):
        flash('Please enter a valid email address.', 'error')
        return redirect(url_for('print_center', wedding_id=wedding_id))

    doc_info = PRINT_DOCUMENTS[document_type]

    try:
        # Build context and generate PDF
        ctx = _get_print_context(document_type, wedding)
        pdf_bytes = _generate_pdf_bytes(doc_info['template'], **ctx)
        pdf_filename = f"{doc_info['filename']}_{wedding_id}.pdf"

        # Build email body
        greeting = f"Hi {recipient_name},\n\n" if recipient_name else "Hi,\n\n"
        custom_msg = f"{message}\n\n" if message else ""
        body_text = (
            f"{greeting}"
            f"{custom_msg}"
            f"{wedding.couple_names} shared a wedding document with you: "
            f"{doc_info['title']}.\n\n"
            f"The document is attached as a PDF.\n\n"
            f"Best regards,\nWedding Organizer"
        )

        subject = f"{doc_info['title']} - {wedding.couple_names}"

        success = send_pdf_email(
            to_email=recipient_email,
            subject=subject,
            body_text=body_text,
            pdf_bytes=pdf_bytes,
            pdf_filename=pdf_filename,
        )

        if success:
            flash(f'{doc_info["title"]} sent to {recipient_email}.', 'success')
        else:
            flash('Email could not be sent. Please check your SMTP configuration.', 'error')
    except Exception as e:
        print(f"Error sharing document: {e}")
        flash('An error occurred while generating or sending the document.', 'error')

    return redirect(url_for('print_center', wedding_id=wedding_id))

def _build_personal_timeline(wedding, participant):
    """Build personalized timeline data for a single participant."""
    from datetime import time as time_type
    # Get timeline items assigned to this participant
    assigned_items = sorted(
        participant.timeline_items,
        key=lambda x: (x.time or time_type.min, x.order)
    )
    # Also include items where their name appears in the 'who' field
    name_lower = participant.name.lower()
    for item in wedding.day_of_items:
        if item not in assigned_items and item.who and name_lower in item.who.lower():
            assigned_items.append(item)
    assigned_items = sorted(assigned_items, key=lambda x: (x.time or time_type.min, x.order))

    # Get hair & makeup appointments matching this person's name
    hair_makeup = [appt for appt in wedding.hair_makeup
                   if appt.person_name and appt.person_name.lower() == name_lower]
    hair_makeup = sorted(hair_makeup, key=lambda x: (x.appointment_time or time_type.min))

    # Get responsibilities from bridal party member if linked
    responsibilities = []
    if participant.bridal_party_member and participant.bridal_party_member.responsibilities:
        responsibilities = [r.strip() for r in participant.bridal_party_member.responsibilities.split('\n') if r.strip()]
    elif participant.notes:
        responsibilities = [r.strip() for r in participant.notes.split('\n') if r.strip()]

    # Key contacts: couple + coordinator/planner
    key_contacts = []
    for p in wedding.participants:
        if p.id != participant.id and p.role_category in ('couple', 'handler'):
            key_contacts.append(p)
    # Also add planner vendors
    for v in wedding.vendors:
        if v.category == 'planner' and v.contact_name:
            class _Contact:
                def __init__(self, name, role, phone, email):
                    self.name = name
                    self.role = role
                    self.phone = phone
                    self.email = email
            key_contacts.append(_Contact(v.contact_name, 'wedding_planner', v.phone, v.email))

    return {
        'participant': participant,
        'timeline_items': assigned_items,
        'hair_makeup': hair_makeup,
        'responsibilities': responsibilities,
        'key_contacts': key_contacts,
    }

@app.route('/wedding/<int:wedding_id>/print/personal-timelines')
@login_required
def print_personal_timelines(wedding_id):
    """Selection page: choose which participant's timeline to print."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('print/personal_timelines.html',
                           wedding=wedding, participants=wedding.participants)

@app.route('/wedding/<int:wedding_id>/print/personal-timeline/<int:participant_id>')
@login_required
def print_personal_timeline(wedding_id, participant_id):
    """Printable personal timeline for a specific participant."""
    wedding = get_wedding_or_403(wedding_id)
    participant = WeddingParticipant.query.get_or_404(participant_id)
    if participant.wedding_id != wedding.id:
        abort(404)
    data = _build_personal_timeline(wedding, participant)
    return _render_or_pdf('print/personal_timeline.html',
                          f'timeline_{participant.name.replace(" ", "_")}_{wedding_id}.pdf',
                          wedding=wedding, **data)

@app.route('/wedding/<int:wedding_id>/print/all-personal-timelines')
@login_required
def print_all_personal_timelines(wedding_id):
    """Printable combined personal timelines for all participants (one page per person)."""
    wedding = get_wedding_or_403(wedding_id)
    participant_data = []
    for p in sorted(wedding.participants, key=lambda x: (x.role_category or 'zzz', x.name)):
        data = _build_personal_timeline(wedding, p)
        participant_data.append(data)
    return _render_or_pdf('print/all_personal_timelines.html',
                          f'all_personal_timelines_{wedding_id}.pdf',
                          wedding=wedding, participant_data=participant_data)

@app.route('/wedding/<int:wedding_id>/print/ceremony-program')
@login_required
def print_ceremony_program(wedding_id):
    """Printable ceremony program with readings and script."""
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    readings = sorted(ceremony.readings, key=lambda x: (x.order or 0)) if ceremony and ceremony.readings else []
    timeline_items = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony and ceremony.timeline_items else []
    bridal_party = sorted(wedding.bridal_party, key=lambda x: (x.processional_order or 999))
    return _render_or_pdf('print/ceremony_program.html', f'ceremony_program_{wedding_id}.pdf',
                          wedding=wedding, ceremony=ceremony, readings=readings,
                          timeline_items=timeline_items, bridal_party=bridal_party)

@app.route('/wedding/<int:wedding_id>/print/music-cue-sheet')
@login_required
def print_music_cue_sheet(wedding_id):
    """Printable music cue sheet for DJ/band."""
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    songs = sorted(wedding.songs, key=lambda x: (x.moment or '', x.order or 0))
    return _render_or_pdf('print/music_cue_sheet.html', f'music_cue_sheet_{wedding_id}.pdf',
                          wedding=wedding, ceremony=ceremony, songs=songs)

@app.route('/wedding/<int:wedding_id>/print/guest-list')
@login_required
def print_guest_list(wedding_id):
    """Printable guest list with meal choices and dietary restrictions."""
    wedding = get_wedding_or_403(wedding_id)
    guests = sorted(wedding.guests, key=lambda x: x.name)
    return _render_or_pdf('print/guest_list.html', f'guest_list_{wedding_id}.pdf',
                          wedding=wedding, guests=guests)

@app.route('/wedding/<int:wedding_id>/print/tips')
@login_required
def print_tips_tracker(wedding_id):
    """Printable tips and payment tracker."""
    wedding = get_wedding_or_403(wedding_id)
    tips = sorted(wedding.tips, key=lambda x: (x.service_category or '', x.recipient))
    return _render_or_pdf('print/tips_tracker.html', f'tips_{wedding_id}.pdf',
                          wedding=wedding, tips=tips)

@app.route('/wedding/<int:wedding_id>/print/hair-makeup')
@login_required
def print_hair_makeup(wedding_id):
    """Printable hair and makeup schedule."""
    wedding = get_wedding_or_403(wedding_id)
    appointments = sorted(wedding.hair_makeup, key=lambda x: (x.appointment_time or datetime.min.time()))
    return _render_or_pdf('print/hair_makeup.html', f'hair_makeup_{wedding_id}.pdf',
                          wedding=wedding, appointments=appointments)

@app.route('/wedding/<int:wedding_id>/print/bridal-party')
@login_required
def print_bridal_party_info(wedding_id):
    """Printable wedding party info sheet."""
    wedding = get_wedding_or_403(wedding_id)
    bridal_party = sorted(wedding.bridal_party, key=lambda x: (x.side or '', x.processional_order or 999))
    return _render_or_pdf('print/bridal_party.html', f'bridal_party_{wedding_id}.pdf',
                          wedding=wedding, bridal_party=bridal_party)

@app.route('/wedding/<int:wedding_id>/print/venue-info')
@login_required
def print_venue_info(wedding_id):
    """Printable venue information sheet."""
    wedding = get_wedding_or_403(wedding_id)
    ceremony = wedding.ceremony
    reception = wedding.reception
    accommodations = wedding.accommodations if hasattr(wedding, 'accommodations') else []
    return _render_or_pdf('print/venue_info.html', f'venue_info_{wedding_id}.pdf',
                          wedding=wedding, ceremony=ceremony, reception=reception,
                          vendors=wedding.vendors, accommodations=accommodations)

@app.route('/wedding/<int:wedding_id>/print/decor-setup')
@login_required
def print_decor_setup(wedding_id):
    """Printable decor and setup plan."""
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    floral_items = sorted(wedding.floral_items, key=lambda x: (x.item_type or ''))
    inventory_items = wedding.inventory_items
    return _render_or_pdf('print/decor_setup.html', f'decor_setup_{wedding_id}.pdf',
                          wedding=wedding, reception=reception,
                          floral_items=floral_items, inventory_items=inventory_items)

@app.route('/wedding/<int:wedding_id>/print/reception-script')
@login_required
def print_reception_script(wedding_id):
    """Printable MC/DJ reception run sheet."""
    wedding = get_wedding_or_403(wedding_id)
    reception = wedding.reception
    reception_items = sorted(reception.timeline_items, key=lambda x: (x.order or 0)) if reception and reception.timeline_items else []
    songs = sorted(wedding.songs, key=lambda x: (x.moment or '', x.order or 0))
    speeches = sorted(wedding.speeches, key=lambda x: (x.order or 0))
    return _render_or_pdf('print/reception_script.html', f'reception_script_{wedding_id}.pdf',
                          wedding=wedding, reception=reception,
                          reception_items=reception_items, songs=songs, speeches=speeches)

@app.route('/wedding/<int:wedding_id>/print/emergency-kit')
@login_required
def print_emergency_kit(wedding_id):
    """Printable emergency kit supplies checklist."""
    wedding = get_wedding_or_403(wedding_id)
    # Auto-seed default items for weddings created before this feature
    if not wedding.emergency_kit_items:
        seed_default_emergency_kit(wedding.id)
    kit_items = sorted(wedding.emergency_kit_items, key=lambda x: (x.category or '', x.item_name))
    return _render_or_pdf('print/emergency_kit.html', f'emergency_kit_{wedding_id}.pdf',
                          wedding=wedding, kit_items=kit_items)

@app.route('/wedding/<int:wedding_id>/print/rehearsal')
@login_required
def print_rehearsal(wedding_id):
    """Printable rehearsal schedule."""
    wedding = get_wedding_or_403(wedding_id)
    rehearsal_dinner = wedding.rehearsal_dinner
    ceremony = wedding.ceremony
    ceremony_items = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony and ceremony.timeline_items else []
    bridal_party = sorted(wedding.bridal_party, key=lambda x: (x.processional_order or 999))
    return _render_or_pdf('print/rehearsal.html', f'rehearsal_{wedding_id}.pdf',
                          wedding=wedding, rehearsal_dinner=rehearsal_dinner,
                          ceremony_items=ceremony_items, bridal_party=bridal_party)

@app.route('/wedding/<int:wedding_id>/print/transportation')
@login_required
def print_transportation(wedding_id):
    """Printable transportation and accommodations sheet."""
    wedding = get_wedding_or_403(wedding_id)
    accommodations = wedding.accommodations if hasattr(wedding, 'accommodations') else []
    return _render_or_pdf('print/transportation.html', f'transportation_{wedding_id}.pdf',
                          wedding=wedding, accommodations=accommodations)

@app.route('/wedding/<int:wedding_id>/print/contingency-plans')
@login_required
def print_contingency_plans(wedding_id):
    """Printable backup and contingency plans."""
    wedding = get_wedding_or_403(wedding_id)
    plans = sorted(wedding.contingency_plans, key=lambda x: (x.category or ''))
    return _render_or_pdf('print/contingency_plans.html', f'contingency_plans_{wedding_id}.pdf',
                          wedding=wedding, plans=plans)

@app.route('/wedding/<int:wedding_id>/print/budget')
@login_required
def print_budget_summary(wedding_id):
    """Printable budget summary."""
    wedding = get_wedding_or_403(wedding_id)
    budget = wedding.budget
    expenses = sorted(budget.expenses, key=lambda x: (x.category or '', x.item_name)) if budget else []
    return _render_or_pdf('print/budget_summary.html', f'budget_{wedding_id}.pdf',
                          wedding=wedding, budget=budget, expenses=expenses)

@app.route('/wedding/<int:wedding_id>/export/mailing-labels')
@login_required
def export_mailing_labels(wedding_id):
    """Export guest addresses as CSV for mailing labels."""
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Address'])
    for g in wedding.guests:
        if g.address:
            writer.writerow([g.name, g.address])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=mailing_labels_{wedding_id}.csv'
    return response

# ============================================
# CSV EXPORTS - ADDITIONAL MODULES
# ============================================

@app.route('/wedding/<int:wedding_id>/export/bridal-party')
@login_required
def export_bridal_party_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Role', 'Side', 'Email', 'Phone', 'Processional Order',
                     'Responsibilities', 'Gift Idea', 'Gift Cost', 'Gift Purchased'])
    for m in wedding.bridal_party:
        writer.writerow([
            m.name, m.role or '', m.side or '', m.email or '', m.phone or '',
            m.processional_order or '', m.responsibilities or '', m.gift_idea or '',
            m.gift_cost or 0, 'Yes' if m.gift_purchased else 'No'
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=bridal_party_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/registry')
@login_required
def export_registry_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item Name', 'Store', 'URL', 'Price', 'Qty Requested', 'Qty Purchased', 'Purchased By'])
    for r in wedding.registry_items:
        writer.writerow([
            r.item_name, r.store or '', r.url or '', r.price or 0,
            r.quantity_requested or 1, r.quantity_purchased or 0, r.purchased_by or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=registry_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/music')
@login_required
def export_music_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Title', 'Artist', 'Moment', 'Duration (min)', 'Spotify URL', 'Notes'])
    for s in wedding.songs:
        writer.writerow([
            s.title, s.artist or '', s.moment or '', s.duration_minutes or '',
            s.spotify_url or '', s.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=music_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/photos')
@login_required
def export_photos_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Category', 'Description', 'People', 'Priority', 'Captured', 'Notes'])
    for s in wedding.photo_shots:
        writer.writerow([
            s.category or '', s.description, s.people or '', s.priority or '',
            'Yes' if s.captured else 'No', s.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=shot_list_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/attire')
@login_required
def export_attire_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Person Name', 'Person Type', 'Garment Type', 'Designer', 'Color',
                     'Size', 'Store', 'Price', 'Purchased', 'Accessories', 'Notes'])
    for a in wedding.attire:
        writer.writerow([
            a.person_name or '', a.person_type or '', a.garment_type or '',
            a.designer or '', a.color or '', a.size or '', a.store or '',
            a.price or 0, 'Yes' if a.purchased else 'No',
            a.accessories or '', a.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=attire_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/gifts')
@login_required
def export_gifts_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Event', 'From', 'Description', 'Estimated Value', 'Date Received',
                     'Thank You Sent', 'Notes'])
    for g in wedding.gifts:
        writer.writerow([
            g.event, g.from_name, g.description or '', g.estimated_value or 0,
            str(g.date_received or ''), 'Yes' if g.thank_you_sent else 'No',
            g.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=gifts_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/flowers')
@login_required
def export_flowers_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Item Type', 'Recipient', 'Flowers', 'Colors', 'Quantity', 'Cost', 'Notes'])
    for f in wedding.floral_items:
        writer.writerow([
            f.item_type, f.recipient or '', f.flowers or '', f.colors or '',
            f.quantity or 1, f.cost or 0, f.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=flowers_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/speeches')
@login_required
def export_speeches_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Speaker Name', 'Type', 'Order', 'Duration (min)', 'Reviewed', 'Notes'])
    for s in wedding.speeches:
        writer.writerow([
            s.speaker_name, s.speech_type or '', s.order or 0,
            s.duration_minutes or '', 'Yes' if s.reviewed else 'No', s.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=speeches_{wedding_id}.csv'
    return response

@app.route('/wedding/<int:wedding_id>/export/favors')
@login_required
def export_favors_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Description', 'Quantity', 'Cost Per Item', 'Total Cost',
                     'Assembled', 'Vendor', 'Notes'])
    for f in wedding.favors:
        writer.writerow([
            f.description, f.quantity or 0, f.cost_per_item or 0, f.total_cost or 0,
            'Yes' if f.assembled else 'No', f.vendor or '', f.notes or ''
        ])
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = f'attachment; filename=favors_{wedding_id}.csv'
    return response

# ============================================
# SAMPLE CSV TEMPLATE DOWNLOADS
# ============================================

@app.route('/templates/<template_name>.csv')
def download_sample_csv(template_name):
    """Download a sample CSV template for importing data."""
    allowed = {'guests', 'vendors', 'tasks', 'budget'}
    if template_name not in allowed:
        abort(404)
    return app.send_static_file(f'templates/{template_name}_template.csv')

# ============================================
# CSV IMPORTS
# ============================================

def _parse_csv_upload(request_obj):
    """Parse an uploaded CSV file and return rows as list of dicts. Returns (rows, error)."""
    if 'file' not in request_obj.files:
        return None, 'No file uploaded.'
    file = request_obj.files['file']
    if file.filename == '':
        return None, 'No file selected.'
    if not file.filename.lower().endswith('.csv'):
        return None, 'Please upload a CSV file.'
    try:
        content = file.read().decode('utf-8-sig')  # utf-8-sig handles BOM from Excel
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        if not rows:
            return None, 'CSV file is empty.'
        return rows, None
    except UnicodeDecodeError:
        return None, 'Could not read file. Please ensure it is a UTF-8 encoded CSV.'
    except csv.Error as e:
        return None, f'CSV parsing error: {str(e)}'

@app.route('/wedding/<int:wedding_id>/import/guests', methods=['POST'])
@login_required
def import_guests_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    rows, error = _parse_csv_upload(request)
    if error:
        flash(error, 'error')
        return redirect(url_for('guests_view', wedding_id=wedding_id))

    imported = 0
    skipped = 0
    for row in rows:
        name = row.get('Name', row.get('name', '')).strip()
        if not name:
            skipped += 1
            continue
        guest = Guest(
            wedding_id=wedding_id,
            name=sanitize_string(name),
            email=sanitize_string(row.get('Email', row.get('email', '')).strip()) or None,
            phone=sanitize_string(row.get('Phone', row.get('phone', '')).strip()) or None,
            address=sanitize_string(row.get('Address', row.get('address', '')).strip()) or None,
            rsvp_status=row.get('RSVP Status', row.get('rsvp_status', 'pending')).strip().lower() or 'pending',
            meal_choice=sanitize_string(row.get('Meal Choice', row.get('meal_choice', '')).strip()) or None,
            dietary_restrictions=sanitize_string(row.get('Dietary Restrictions', row.get('dietary_restrictions', '')).strip()) or None,
            side=sanitize_string(row.get('Side', row.get('side', '')).strip()) or None,
            guest_type=sanitize_string(row.get('Guest Type', row.get('guest_type', '')).strip()) or None,
            social_groups=sanitize_string(row.get('Social Groups', row.get('social_groups', '')).strip()) or None,
            household_group=sanitize_string(row.get('Household Group', row.get('household_group', '')).strip()) or None,
        )
        # Handle plus one
        plus_one = row.get('Plus One', row.get('plus_one_of', '')).strip()
        if plus_one:
            guest.is_plus_one = True
            guest.plus_one_of = sanitize_string(plus_one)
        db.session.add(guest)
        imported += 1

    db.session.commit()
    flash(f'Successfully imported {imported} guest(s). {skipped} row(s) skipped (no name).', 'success')
    return redirect(url_for('guests_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/import/vendors', methods=['POST'])
@login_required
def import_vendors_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    rows, error = _parse_csv_upload(request)
    if error:
        flash(error, 'error')
        return redirect(url_for('vendors_view', wedding_id=wedding_id))

    imported = 0
    skipped = 0
    for row in rows:
        business_name = row.get('Business Name', row.get('business_name', '')).strip()
        category = row.get('Category', row.get('category', '')).strip()
        if not business_name or not category:
            skipped += 1
            continue
        vendor = Vendor(
            wedding_id=wedding_id,
            category=sanitize_string(category),
            business_name=sanitize_string(business_name),
            contact_name=sanitize_string(row.get('Contact', row.get('contact_name', '')).strip()) or None,
            email=sanitize_string(row.get('Email', row.get('email', '')).strip()) or None,
            phone=sanitize_string(row.get('Phone', row.get('phone', '')).strip()) or None,
            website=sanitize_string(row.get('Website', row.get('website', '')).strip()) or None,
            notes=sanitize_string(row.get('Notes', row.get('notes', '')).strip()) or None,
        )
        # Parse numeric fields safely
        try:
            vendor.total_cost = float(row.get('Total Cost', row.get('total_cost', 0)) or 0)
        except (ValueError, TypeError):
            vendor.total_cost = 0
        try:
            vendor.deposit_amount = float(row.get('Deposit', row.get('deposit_amount', 0)) or 0)
        except (ValueError, TypeError):
            vendor.deposit_amount = 0
        db.session.add(vendor)
        imported += 1

    db.session.commit()
    flash(f'Successfully imported {imported} vendor(s). {skipped} row(s) skipped.', 'success')
    return redirect(url_for('vendors_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/import/tasks', methods=['POST'])
@login_required
def import_tasks_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    rows, error = _parse_csv_upload(request)
    if error:
        flash(error, 'error')
        return redirect(url_for('tasks_view', wedding_id=wedding_id))

    imported = 0
    skipped = 0
    for row in rows:
        title = row.get('Title', row.get('title', '')).strip()
        if not title:
            skipped += 1
            continue
        task = Task(
            wedding_id=wedding_id,
            title=sanitize_string(title),
            description=sanitize_string(row.get('Description', row.get('description', '')).strip()) or None,
            priority=row.get('Priority', row.get('priority', 'medium')).strip().lower() or 'medium',
            category=sanitize_string(row.get('Category', row.get('category', '')).strip()) or None,
            assigned_to=sanitize_string(row.get('Assigned To', row.get('assigned_to', '')).strip()) or None,
        )
        # Parse due date
        due_str = row.get('Due Date', row.get('due_date', '')).strip()
        if due_str:
            for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%d/%m/%Y'):
                try:
                    task.due_date = datetime.strptime(due_str, fmt)
                    break
                except ValueError:
                    continue
        if not task.due_date:
            task.due_date = wedding.wedding_date  # fallback to wedding date
        # Parse completed
        completed_str = row.get('Completed', row.get('completed', 'No')).strip().lower()
        task.completed = completed_str in ('yes', 'true', '1', 'x')
        db.session.add(task)
        imported += 1

    db.session.commit()
    flash(f'Successfully imported {imported} task(s). {skipped} row(s) skipped.', 'success')
    return redirect(url_for('tasks_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/import/budget', methods=['POST'])
@login_required
def import_budget_csv(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    rows, error = _parse_csv_upload(request)
    if error:
        flash(error, 'error')
        return redirect(url_for('budget_view', wedding_id=wedding_id))

    # Ensure budget exists
    if not wedding.budget:
        budget = Budget(wedding_id=wedding_id, total_budget=0)
        db.session.add(budget)
        db.session.flush()
    else:
        budget = wedding.budget

    imported = 0
    skipped = 0
    for row in rows:
        item_name = row.get('Item', row.get('item_name', row.get('Item Name', ''))).strip()
        category = row.get('Category', row.get('category', '')).strip()
        if not item_name or not category:
            skipped += 1
            continue
        expense = BudgetExpense(
            budget_id=budget.id,
            category=sanitize_string(category),
            item_name=sanitize_string(item_name),
            notes=sanitize_string(row.get('Notes', row.get('notes', '')).strip()) or None,
            covered_by=sanitize_string(row.get('Covered By', row.get('covered_by', '')).strip()) or None,
            payment_status=row.get('Payment Status', row.get('payment_status', '')).strip() or None,
        )
        for field, keys in [
            ('estimated_cost', ['Estimated Cost', 'estimated_cost']),
            ('actual_cost', ['Actual Cost', 'actual_cost']),
            ('paid_amount', ['Paid Amount', 'paid_amount']),
        ]:
            for key in keys:
                val = row.get(key, '').strip()
                if val:
                    try:
                        setattr(expense, field, float(val))
                    except (ValueError, TypeError):
                        pass
                    break
        db.session.add(expense)
        imported += 1

    db.session.commit()
    flash(f'Successfully imported {imported} expense(s). {skipped} row(s) skipped.', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

# ============================================
# FULL WEDDING JSON EXPORT / IMPORT
# ============================================

def _serialize_date(val):
    """Safely serialize date/datetime/time to string."""
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    # time objects
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    return str(val)

def _serialize_model(obj, exclude=None):
    """Serialize a SQLAlchemy model to a dict, excluding specified fields."""
    exclude = set(exclude or [])
    exclude.update({'id', '_sa_instance_state'})
    result = {}
    for col in obj.__table__.columns:
        if col.name in exclude:
            continue
        val = getattr(obj, col.name)
        result[col.name] = _serialize_date(val) if isinstance(val, (datetime, date)) or (hasattr(val, 'isoformat') and callable(val.isoformat)) else val
    return result

@app.route('/wedding/<int:wedding_id>/export/full')
@login_required
def export_wedding_json(wedding_id):
    """Export the entire wedding plan as a single JSON file."""
    wedding = get_wedding_or_403(wedding_id)
    exclude_fk = ['wedding_id']

    data = {
        'export_version': '1.0',
        'exported_at': datetime.utcnow().isoformat(),
        'wedding': _serialize_model(wedding, exclude=['id']),
        'people': [_serialize_model(p, exclude=exclude_fk) for p in wedding.people],
        'guests': [_serialize_model(g, exclude=exclude_fk + ['table_id', 'person_id']) for g in wedding.guests],
        'tasks': [_serialize_model(t, exclude=exclude_fk + ['depends_on_id']) for t in wedding.tasks],
        'vendors': [],
        'bridal_party': [_serialize_model(m, exclude=exclude_fk + ['person_id']) for m in wedding.bridal_party],
        'registry_items': [_serialize_model(r, exclude=exclude_fk) for r in wedding.registry_items],
        'attire': [_serialize_model(a, exclude=exclude_fk + ['person_id']) for a in wedding.attire],
        'songs': [_serialize_model(s, exclude=exclude_fk) for s in wedding.songs],
        'photo_shots': [_serialize_model(s, exclude=exclude_fk) for s in wedding.photo_shots],
        'floral_items': [_serialize_model(f, exclude=exclude_fk) for f in wedding.floral_items],
        'invitations': [_serialize_model(i, exclude=exclude_fk) for i in wedding.invitations],
        'speeches': [_serialize_model(s, exclude=exclude_fk) for s in wedding.speeches],
        'favors': [_serialize_model(f, exclude=exclude_fk) for f in wedding.favors],
        'gifts': [_serialize_model(g, exclude=exclude_fk) for g in wedding.gifts],
        'tips': [_serialize_model(t, exclude=exclude_fk) for t in wedding.tips],
        'contingency_plans': [_serialize_model(c, exclude=exclude_fk) for c in wedding.contingency_plans],
        'accommodations': [_serialize_model(a, exclude=exclude_fk) for a in wedding.accommodations],
        'day_of_items': [_serialize_model(i, exclude=exclude_fk) for i in wedding.day_of_items],
        'hair_makeup': [_serialize_model(h, exclude=exclude_fk) for h in wedding.hair_makeup],
        'guest_groups': [_serialize_model(g, exclude=exclude_fk) for g in wedding.guest_groups],
        'inventory_items': [_serialize_model(i, exclude=exclude_fk + ['bin_id']) for i in wedding.inventory_items],
        'inventory_bins': [_serialize_model(b, exclude=exclude_fk) for b in wedding.inventory_bins],
    }

    # Vendors with nested communication log and quotes
    for v in wedding.vendors:
        vendor_data = _serialize_model(v, exclude=exclude_fk)
        vendor_data['communication_log'] = [_serialize_model(n, exclude=['vendor_id']) for n in v.communication_log]
        data['vendors'].append(vendor_data)

    # Vendor quotes (wedding-level)
    data['vendor_quotes'] = [_serialize_model(q, exclude=exclude_fk) for q in wedding.vendor_quotes]

    # Ceremony with timeline and readings
    if wedding.ceremony:
        ceremony_data = _serialize_model(wedding.ceremony, exclude=exclude_fk)
        ceremony_data['timeline_items'] = [_serialize_model(i, exclude=['ceremony_id']) for i in wedding.ceremony.timeline_items]
        ceremony_data['readings'] = [_serialize_model(r, exclude=['ceremony_id']) for r in wedding.ceremony.readings]
        data['ceremony'] = ceremony_data
    else:
        data['ceremony'] = None

    # Reception with timeline, menu, tables
    if wedding.reception:
        reception_data = _serialize_model(wedding.reception, exclude=exclude_fk)
        reception_data['timeline_items'] = [_serialize_model(i, exclude=['reception_id']) for i in wedding.reception.timeline_items]
        reception_data['menu_items'] = [_serialize_model(m, exclude=['reception_id']) for m in wedding.reception.menu_items]
        reception_data['seating_tables'] = [_serialize_model(t, exclude=['reception_id']) for t in wedding.reception.seating_tables]
        data['reception'] = reception_data
    else:
        data['reception'] = None

    # Honeymoon with itinerary and packing
    if wedding.honeymoon:
        honeymoon_data = _serialize_model(wedding.honeymoon, exclude=exclude_fk)
        honeymoon_data['itinerary_items'] = [_serialize_model(i, exclude=['honeymoon_id']) for i in wedding.honeymoon.itinerary_items]
        honeymoon_data['packing_items'] = [_serialize_model(p, exclude=['honeymoon_id']) for p in wedding.honeymoon.packing_items]
        data['honeymoon'] = honeymoon_data
    else:
        data['honeymoon'] = None

    # Branding
    data['branding'] = _serialize_model(wedding.branding, exclude=exclude_fk) if wedding.branding else None

    # Budget with expenses and category limits
    if wedding.budget:
        budget_data = _serialize_model(wedding.budget, exclude=exclude_fk)
        budget_data['expenses'] = [_serialize_model(e, exclude=['budget_id']) for e in wedding.budget.expenses]
        budget_data['category_limits'] = [_serialize_model(l, exclude=['budget_id']) for l in wedding.budget.category_limits]
        data['budget'] = budget_data
    else:
        data['budget'] = None

    # Rehearsal dinner
    data['rehearsal_dinner'] = _serialize_model(wedding.rehearsal_dinner, exclude=exclude_fk) if wedding.rehearsal_dinner else None

    # Marriage license
    data['marriage_license'] = _serialize_model(wedding.marriage_license, exclude=exclude_fk) if wedding.marriage_license else None

    response = make_response(json.dumps(data, indent=2, default=str))
    response.headers['Content-Type'] = 'application/json'
    safe_name = wedding.couple_names.replace(' ', '_').replace('/', '_')[:50]
    response.headers['Content-Disposition'] = f'attachment; filename=wedding_{safe_name}_{wedding_id}.json'
    return response

@app.route('/wedding/<int:wedding_id>/import/full', methods=['POST'])
@login_required
def import_wedding_json(wedding_id):
    """Import a wedding plan from a JSON file, merging into the current wedding."""
    wedding = get_wedding_or_403(wedding_id)

    if 'file' not in request.files:
        flash('No file uploaded.', 'error')
        return redirect(url_for('wedding_dashboard', wedding_id=wedding_id))
    file = request.files['file']
    if file.filename == '' or not file.filename.lower().endswith('.json'):
        flash('Please upload a JSON file.', 'error')
        return redirect(url_for('wedding_dashboard', wedding_id=wedding_id))

    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        flash(f'Invalid JSON file: {str(e)}', 'error')
        return redirect(url_for('wedding_dashboard', wedding_id=wedding_id))

    if 'export_version' not in data:
        flash('This does not appear to be a valid Wedding Organizer export file.', 'error')
        return redirect(url_for('wedding_dashboard', wedding_id=wedding_id))

    def _parse_dt(val):
        if not val:
            return None
        for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d'):
            try:
                return datetime.strptime(val, fmt)
            except (ValueError, TypeError):
                continue
        return None

    def _parse_date(val):
        if not val:
            return None
        try:
            return datetime.strptime(val, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return None

    def _parse_time(val):
        if not val:
            return None
        for fmt in ('%H:%M:%S', '%H:%M'):
            try:
                return datetime.strptime(val, fmt).time()
            except (ValueError, TypeError):
                continue
        return None

    def _safe_float(val):
        try:
            return float(val) if val else None
        except (ValueError, TypeError):
            return None

    def _safe_int(val):
        try:
            return int(val) if val else None
        except (ValueError, TypeError):
            return None

    def _safe_bool(val):
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ('true', '1', 'yes')
        return bool(val) if val else False

    counts = {}

    # Import simple list models
    model_map = {
        'guests': (Guest, {'name': str, 'email': str, 'phone': str, 'address': str,
                          'rsvp_status': str, 'meal_choice': str, 'dietary_restrictions': str,
                          'side': str, 'guest_type': str, 'household_group': str, 'social_groups': str,
                          'is_plus_one': _safe_bool, 'plus_one_of': str,
                          'gift_received': _safe_bool, 'thank_you_sent': _safe_bool,
                          'rsvp_notes': str}),
        'tasks': (Task, {'title': str, 'description': str, 'priority': str, 'category': str,
                        'assigned_to': str, 'completed': _safe_bool, 'is_milestone': _safe_bool,
                        'due_date': _parse_dt}),
        'bridal_party': (BridalPartyMember, {'name': str, 'role': str, 'side': str, 'email': str,
                                             'phone': str, 'responsibilities': str,
                                             'gift_idea': str, 'gift_cost': _safe_float,
                                             'gift_purchased': _safe_bool, 'processional_order': _safe_int}),
        'registry_items': (RegistryItem, {'item_name': str, 'store': str, 'url': str,
                                         'price': _safe_float, 'quantity_requested': _safe_int,
                                         'quantity_purchased': _safe_int, 'purchased_by': str}),
        'attire': (Attire, {'person_name': str, 'person_type': str, 'garment_type': str,
                           'designer': str, 'color': str, 'size': str, 'store': str,
                           'price': _safe_float, 'purchased': _safe_bool, 'accessories': str, 'notes': str}),
        'songs': (Song, {'title': str, 'artist': str, 'moment': str, 'spotify_url': str,
                        'duration_minutes': _safe_float, 'notes': str, 'order': _safe_int}),
        'photo_shots': (PhotoShot, {'category': str, 'description': str, 'people': str,
                                    'priority': str, 'captured': _safe_bool, 'notes': str}),
        'floral_items': (FloralItem, {'item_type': str, 'recipient': str, 'flowers': str,
                                      'colors': str, 'quantity': _safe_int, 'cost': _safe_float, 'notes': str}),
        'invitations': (Invitation, {'item_type': str, 'designer': str, 'quantity': _safe_int,
                                     'cost': _safe_float, 'status': str, 'notes': str}),
        'speeches': (SpeechToast, {'speaker_name': str, 'speech_type': str, 'order': _safe_int,
                                   'duration_minutes': _safe_int, 'reviewed': _safe_bool, 'notes': str}),
        'favors': (WeddingFavor, {'description': str, 'quantity': _safe_int, 'cost_per_item': _safe_float,
                                  'total_cost': _safe_float, 'assembled': _safe_bool, 'vendor': str, 'notes': str}),
        'gifts': (Gift, {'event': str, 'from_name': str, 'description': str,
                         'estimated_value': _safe_float, 'thank_you_sent': _safe_bool, 'notes': str,
                         'date_received': _parse_date}),
        'tips': (TipItem, {'recipient': str, 'service_category': str, 'suggested_amount': _safe_float,
                           'actual_amount': _safe_float, 'payment_method': str,
                           'envelope_prepared': _safe_bool, 'given': _safe_bool, 'notes': str}),
        'contingency_plans': (ContingencyPlan, {'category': str, 'title': str, 'description': str,
                                                'contact_name': str, 'contact_phone': str, 'notes': str}),
        'accommodations': (Accommodation, {'accommodation_type': str, 'name': str, 'address': str,
                                           'phone': str, 'website': str, 'block_code': str, 'rate': str,
                                           'rooms_reserved': _safe_int, 'welcome_bag': _safe_bool, 'notes': str}),
        'day_of_items': (DayOfTimelineItem, {'title': str, 'description': str, 'location': str,
                                             'who': str, 'category': str, 'order': _safe_int,
                                             'time': _parse_time}),
        'hair_makeup': (HairMakeup, {'person_name': str, 'service_type': str, 'stylist_name': str,
                                     'style_notes': str, 'trial_completed': _safe_bool,
                                     'cost': _safe_float, 'notes': str, 'appointment_time': _parse_time}),
        'guest_groups': (GuestGroup, {'name': str, 'color': str, 'seat_together': _safe_bool,
                                      'priority': _safe_int, 'notes': str}),
    }

    for key, (model_cls, field_map) in model_map.items():
        items = data.get(key, [])
        if not items:
            continue
        count = 0
        for item_data in items:
            obj = model_cls(wedding_id=wedding_id)
            for field, converter in field_map.items():
                val = item_data.get(field)
                if val is not None and val != '':
                    try:
                        setattr(obj, field, converter(val) if converter != str else sanitize_string(str(val)))
                    except (ValueError, TypeError):
                        pass
            db.session.add(obj)
            count += 1
        counts[key] = count

    # Import vendors with nested communication log
    vendor_items = data.get('vendors', [])
    if vendor_items:
        v_count = 0
        for v_data in vendor_items:
            vendor = Vendor(wedding_id=wedding_id)
            for field in ['category', 'business_name', 'contact_name', 'email', 'phone',
                         'website', 'notes', 'setup_instructions', 'service_location']:
                val = v_data.get(field)
                if val:
                    setattr(vendor, field, sanitize_string(str(val)))
            for field in ['total_cost', 'deposit_amount', 'balance_due']:
                val = v_data.get(field)
                if val is not None:
                    try:
                        setattr(vendor, field, float(val))
                    except (ValueError, TypeError):
                        pass
            vendor.contract_signed = _safe_bool(v_data.get('contract_signed'))
            vendor.deposit_paid = _safe_bool(v_data.get('deposit_paid'))
            vendor.service_date = _parse_date(v_data.get('service_date'))
            db.session.add(vendor)
            db.session.flush()
            for note_data in v_data.get('communication_log', []):
                note = VendorNote(vendor_id=vendor.id)
                for f in ['note_type', 'subject', 'content']:
                    val = note_data.get(f)
                    if val:
                        setattr(note, f, sanitize_string(str(val)))
                note.date = _parse_dt(note_data.get('date')) or datetime.utcnow()
                db.session.add(note)
            v_count += 1
        counts['vendors'] = v_count

    db.session.commit()

    summary_parts = [f'{v} {k.replace("_", " ")}' for k, v in counts.items() if v > 0]
    if summary_parts:
        flash(f'Successfully imported: {", ".join(summary_parts)}.', 'success')
    else:
        flash('No data was imported from the file.', 'warning')

    return redirect(url_for('wedding_dashboard', wedding_id=wedding_id))

# ============================================
# GLOBAL SEARCH
# ============================================

@app.route('/wedding/<int:wedding_id>/search')
@login_required
def global_search(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    q = request.args.get('q', '').strip().lower()
    results = {'guests': [], 'vendors': [], 'tasks': [], 'expenses': []}
    if q:
        results['guests'] = [g for g in wedding.guests if q in g.name.lower() or
                            (g.email and q in g.email.lower())]
        results['vendors'] = [v for v in wedding.vendors if q in v.business_name.lower() or
                             (v.contact_name and q in v.contact_name.lower())]
        results['tasks'] = [t for t in wedding.tasks if q in t.title.lower() or
                           (t.description and q in t.description.lower())]
        if wedding.budget:
            results['expenses'] = [e for e in wedding.budget.expenses if
                                  q in e.item_name.lower() or q in e.category.lower()]
    total = sum(len(v) for v in results.values())
    return render_template('search/results.html', wedding=wedding, query=q,
                         results=results, total=total)

# ============================================
# ACTIVITY LOG / AUDIT TRAIL
# ============================================

@app.route('/wedding/<int:wedding_id>/activity')
@login_required
def activity_log_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    page = request.args.get('page', 1, type=int)
    per_page = 50
    logs = ActivityLog.query.filter_by(wedding_id=wedding_id)\
        .order_by(ActivityLog.timestamp.desc())\
        .limit(per_page).offset((page - 1) * per_page).all()
    total = ActivityLog.query.filter_by(wedding_id=wedding_id).count()
    return render_template('activity/log.html', wedding=wedding, logs=logs,
                         page=page, total=total, per_page=per_page)

# ============================================
# COMMENTS ON ITEMS
# ============================================

@app.route('/wedding/<int:wedding_id>/comment/add', methods=['POST'])
@login_required
def comment_add(wedding_id):
    comment = Comment(
        wedding_id=wedding_id,
        user_id=g.user.id if g.user else None,
        user_name=g.user.name if g.user else 'Unknown',
        entity_type=request.form.get('entity_type'),
        entity_id=request.form.get('entity_id', type=int),
        content=request.form.get('content')
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added!', 'success')
    return redirect(request.referrer or url_for('wedding_dashboard', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/comment/<int:comment_id>/delete', methods=['POST'])
@login_required
def comment_delete(wedding_id, comment_id):
    comment = get_entity_or_404(Comment, comment_id, wedding_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment removed.', 'success')
    return redirect(request.referrer or url_for('wedding_dashboard', wedding_id=wedding_id))

# ============================================
# COLLABORATION / PERMISSIONS UI
# ============================================

@app.route('/wedding/<int:wedding_id>/collaborators')
@login_required
def collaborators_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    access_list = WeddingAccess.query.filter_by(wedding_id=wedding_id).all()
    users = []
    for access in access_list:
        user = User.query.get(access.user_id)
        if user:
            users.append({'user': user, 'role': access.role, 'access_id': access.id})
    return render_template('collaboration/view.html', wedding=wedding, users=users)

@app.route('/wedding/<int:wedding_id>/collaborators/add', methods=['POST'])
@login_required
def collaborator_add(wedding_id):
    # Only owners can add collaborators
    wedding = get_wedding_or_403(wedding_id)
    if g.wedding_role != 'owner':
        abort(403, description='Only wedding owners can manage collaborators.')
    email = sanitize_string(request.form.get('email', '')).lower()
    role = request.form.get('role', 'viewer')
    if role not in ('viewer', 'planner'):
        role = 'viewer'  # Prevent self-escalation to owner
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('No user found with that email.', 'error')
        return redirect(url_for('collaborators_view', wedding_id=wedding_id))
    existing = WeddingAccess.query.filter_by(user_id=user.id, wedding_id=wedding_id).first()
    if existing:
        flash('User already has access.', 'error')
        return redirect(url_for('collaborators_view', wedding_id=wedding_id))
    access = WeddingAccess(user_id=user.id, wedding_id=wedding_id, role=role)
    db.session.add(access)
    log_activity(wedding_id, 'created', 'collaborator', user.name, f'Role: {role}')
    db.session.commit()
    flash(f'{user.name} added as {role}!', 'success')
    return redirect(url_for('collaborators_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/collaborators/<int:access_id>/update', methods=['POST'])
@login_required
def collaborator_update(wedding_id, access_id):
    # Only owners can update collaborator roles
    wedding = get_wedding_or_403(wedding_id)
    if g.wedding_role != 'owner':
        abort(403, description='Only wedding owners can manage collaborators.')
    access = WeddingAccess.query.get_or_404(access_id)
    if access.wedding_id != wedding_id:
        abort(404)
    new_role = request.form.get('role', 'viewer')
    if new_role not in ('viewer', 'planner'):
        new_role = 'viewer'
    access.role = new_role
    db.session.commit()
    flash('Role updated!', 'success')
    return redirect(url_for('collaborators_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/collaborators/<int:access_id>/remove', methods=['POST'])
@login_required
def collaborator_remove(wedding_id, access_id):
    # Only owners can remove collaborators
    wedding = get_wedding_or_403(wedding_id)
    if g.wedding_role != 'owner':
        abort(403, description='Only wedding owners can manage collaborators.')
    access = WeddingAccess.query.get_or_404(access_id)
    if access.wedding_id != wedding_id:
        abort(404)
    # Prevent removing the last owner
    if access.role == 'owner':
        owner_count = WeddingAccess.query.filter_by(wedding_id=wedding_id, role='owner').count()
        if owner_count <= 1:
            flash('Cannot remove the last owner.', 'error')
            return redirect(url_for('collaborators_view', wedding_id=wedding_id))
    db.session.delete(access)
    db.session.commit()
    flash('Access removed.', 'success')
    return redirect(url_for('collaborators_view', wedding_id=wedding_id))

# ============================================
# CALENDAR VIEW & ICAL EXPORT
# ============================================

@app.route('/wedding/<int:wedding_id>/calendar')
@login_required
def calendar_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    events = []
    # Tasks
    for t in wedding.tasks:
        events.append({
            'title': t.title,
            'date': t.due_date.strftime('%Y-%m-%d') if t.due_date else '',
            'type': 'task',
            'completed': t.completed,
            'category': t.category or 'general'
        })
    # Vendor payment dates
    for v in wedding.vendors:
        if v.final_payment_date:
            events.append({
                'title': f'Payment: {v.business_name}',
                'date': v.final_payment_date.strftime('%Y-%m-%d'),
                'type': 'payment',
                'completed': False,
                'category': 'vendors'
            })
    # Budget expense due dates
    if wedding.budget:
        for e in wedding.budget.expenses:
            if e.payment_due_date:
                events.append({
                    'title': f'Due: {e.item_name}',
                    'date': e.payment_due_date.strftime('%Y-%m-%d'),
                    'type': 'payment',
                    'completed': e.payment_status == 'paid',
                    'category': 'budget'
                })
    events.sort(key=lambda x: x['date'])
    return render_template('calendar/view.html', wedding=wedding, events=events)

@app.route('/wedding/<int:wedding_id>/calendar/export.ics')
@login_required
def calendar_export_ical(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Wedding Organizer//EN',
        f'X-WR-CALNAME:{wedding.couple_names} Wedding',
    ]
    # Wedding date
    wd = wedding.wedding_date
    lines.extend([
        'BEGIN:VEVENT',
        f'DTSTART:{wd.strftime("%Y%m%d")}',
        f'DTEND:{wd.strftime("%Y%m%d")}',
        f'SUMMARY:{wedding.couple_names} Wedding Day',
        'END:VEVENT',
    ])
    # Tasks
    for t in wedding.tasks:
        if t.due_date:
            lines.extend([
                'BEGIN:VEVENT',
                f'DTSTART:{t.due_date.strftime("%Y%m%d")}',
                f'SUMMARY:{t.title}',
                f'DESCRIPTION:{t.description or ""}',
                'END:VEVENT',
            ])
    lines.append('END:VCALENDAR')
    response = make_response('\r\n'.join(lines))
    response.headers['Content-Type'] = 'text/calendar'
    response.headers['Content-Disposition'] = f'attachment; filename=wedding_{wedding_id}.ics'
    return response

# ============================================
# BAR & DANCE FLOOR CALCULATORS
# ============================================

@app.route('/wedding/<int:wedding_id>/reception/calculators')
@login_required
def reception_calculators(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    guest_count = len([g for g in wedding.guests if g.rsvp_status == 'accepted'])
    if guest_count == 0:
        guest_count = (wedding.reception.expected_guest_count if wedding.reception and wedding.reception.expected_guest_count else None) or 100
    hours = 4  # default reception duration
    if wedding.reception and wedding.reception.start_time and wedding.reception.end_time:
        start = datetime.combine(date.today(), wedding.reception.start_time)
        end = datetime.combine(date.today(), wedding.reception.end_time)
        hours = max(1, (end - start).seconds / 3600)

    # Bar calculator (industry standard: 1 drink per person per hour for first hour, 0.5 after)
    drinks_per_person = 1 + 0.5 * (hours - 1)
    total_drinks = math.ceil(guest_count * drinks_per_person)
    beer_bottles = math.ceil(total_drinks * 0.3 / 5) * 6  # 30% beer, 6-packs
    wine_bottles = math.ceil(total_drinks * 0.4 / 5)  # 40% wine, 5 glasses per bottle
    liquor_bottles = math.ceil(total_drinks * 0.3 / 16)  # 30% spirits, 16 drinks per bottle

    # Dance floor calculator (4.5 sq ft per dancer, ~40% of guests dance at once)
    dancers = math.ceil(guest_count * 0.4)
    sq_feet = math.ceil(dancers * 4.5)
    side_length = math.ceil(math.sqrt(sq_feet))

    # Postage calculator (estimate)
    invitation_count = math.ceil(guest_count * 0.6)  # ~60% of guests per household invite

    bar_calc = {
        'total_drinks': total_drinks, 'beer_cases': beer_bottles // 6,
        'wine_bottles': wine_bottles, 'liquor_bottles': liquor_bottles,
        'hours': hours, 'guest_count': guest_count
    }
    dance_calc = {
        'dancers': dancers, 'sq_feet': sq_feet,
        'dimensions': f'{side_length}x{side_length}'
    }
    postage_calc = {
        'invitation_count': invitation_count,
        'stamps_invite': invitation_count,
        'stamps_rsvp': invitation_count,  # RSVP return postage
    }
    return render_template('reception/calculators.html', wedding=wedding,
                         bar_calc=bar_calc, dance_calc=dance_calc, postage_calc=postage_calc)

# ============================================
# INVITATION WORDING TEMPLATES
# ============================================

@app.route('/wedding/<int:wedding_id>/invitations/wording')
@login_required
def invitation_wording(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    return render_template('invitations/wording.html', wedding=wedding,
                         templates=INVITATION_WORDING_TEMPLATES)

# ============================================
# STATIONERY CHECKLIST
# ============================================

STATIONERY_CHECKLIST = [
    ('Save-the-Dates', 'First thing to send (6-8 months before)'),
    ('Wedding Invitations', 'Send 6-8 weeks before the wedding'),
    ('RSVP Cards', 'Include with invitations, pre-stamped return'),
    ('Reception Cards', 'If reception is at a different venue'),
    ('Ceremony Programs', 'Outline the ceremony order for guests'),
    ('Menu Cards', 'Table or place setting menus'),
    ('Place Cards / Escort Cards', 'Guide guests to their seats'),
    ('Table Numbers', 'Identify each table'),
    ('Thank-You Cards', 'Send within 3 months of wedding'),
    ('Wedding Signs', 'Welcome, seating chart, bar menu, etc.'),
    ('Favor Tags', 'Attached to wedding favors'),
    ('Rehearsal Dinner Invitations', 'For rehearsal dinner guests'),
]

@app.route('/wedding/<int:wedding_id>/invitations/checklist')
@login_required
def stationery_checklist(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    existing = {inv.item_type for inv in wedding.invitations}
    return render_template('invitations/checklist.html', wedding=wedding,
                         checklist=STATIONERY_CHECKLIST, existing=existing)

# ============================================
# PROCESSIONAL ORDER VISUALIZATION
# ============================================

@app.route('/wedding/<int:wedding_id>/bridal-party/processional')
@login_required
def processional_order(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    members = sorted(wedding.bridal_party, key=lambda x: x.processional_order or 999)
    people = Person.query.filter_by(wedding_id=wedding_id).order_by(Person.display_order).all()
    return render_template('bridal_party/processional.html', wedding=wedding,
                         members=members, people=people)

# ============================================
# MUSIC DURATION TRACKING
# ============================================

@app.route('/wedding/<int:wedding_id>/music/stats')
@login_required
def music_stats(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    songs = wedding.songs
    moments = {}
    for s in songs:
        m = s.moment or 'unassigned'
        if m not in moments:
            moments[m] = {'songs': [], 'total_duration': 0}
        moments[m]['songs'].append(s)
        moments[m]['total_duration'] += s.duration_minutes or 0
    total_duration = sum(s.duration_minutes or 0 for s in songs)
    do_not_play = [s for s in songs if s.moment == 'do_not_play']
    return render_template('music/stats.html', wedding=wedding, moments=moments,
                         total_duration=total_duration, do_not_play=do_not_play,
                         total_songs=len(songs))

# Background task for email reminders
def check_reminders():
    while True:
        try:
            with app.app_context():
                reminder_threshold = datetime.utcnow() + timedelta(days=3)
                tasks = Task.query.filter(
                    Task.completed == False,
                    Task.reminder_sent == False,
                    Task.due_date <= reminder_threshold
                ).all()
                
                for task in tasks:
                    wedding = Wedding.query.get(task.wedding_id)
                    if wedding:
                        send_reminder_email(
                            to_email=wedding.email,
                            couple_names=wedding.couple_names,
                            task_title=task.title,
                            task_description=task.description,
                            due_date=task.due_date
                        )
                        task.reminder_sent = True
                        db.session.commit()
                        logger.info("Reminder sent for task: %s", task.title)

        except Exception as e:
            logger.error("Error checking reminders: %s", e)
        
        time_module.sleep(3600)  # Check every hour

def start_reminder_thread():
    """Start the background reminder thread (once per process)."""
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

# ============================================
# INVENTORY & ITEM TRACKING
# ============================================

@app.route('/wedding/<int:wedding_id>/inventory')
@login_required
def inventory_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    items = InventoryItem.query.filter_by(wedding_id=wedding_id).all()
    bins = InventoryBin.query.filter_by(wedding_id=wedding_id).order_by(InventoryBin.label).all()

    # Stats
    total_items = len(items)
    total_quantity = sum(i.quantity or 1 for i in items)
    packed_count = sum(1 for i in items if i.status == 'packed')
    setup_count = sum(1 for i in items if i.status == 'setup')
    unassigned_count = sum(1 for i in items if not i.bin_id)
    rental_count = sum(1 for i in items if i.source == 'rented')
    total_cost = sum(i.cost or 0 for i in items)

    # Group by category
    by_category = {}
    for item in items:
        cat = item.category or 'other'
        by_category.setdefault(cat, []).append(item)

    # Group by area
    by_area = {}
    for item in items:
        area = item.area or 'other'
        by_area.setdefault(area, []).append(item)

    stats = dict(
        total_items=total_items,
        total_quantity=total_quantity,
        packed_count=packed_count,
        setup_count=setup_count,
        unassigned_count=unassigned_count,
        rental_count=rental_count,
        total_cost=total_cost
    )
    return render_template('inventory/view.html', wedding=wedding, items=items, bins=bins,
                         stats=stats, by_category=by_category, by_area=by_area,
                         categories=INVENTORY_CATEGORIES, areas=INVENTORY_AREAS)


@app.route('/wedding/<int:wedding_id>/inventory/add', methods=['GET', 'POST'])
@login_required
def inventory_item_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    bins = InventoryBin.query.filter_by(wedding_id=wedding_id).order_by(InventoryBin.label).all()
    if request.method == 'POST':
        item = InventoryItem(
            wedding_id=wedding_id,
            name=request.form.get('name'),
            category=request.form.get('category'),
            quantity=request.form.get('quantity', type=int) or 1,
            source=request.form.get('source'),
            source_detail=request.form.get('source_detail'),
            area=request.form.get('area'),
            table_number=request.form.get('table_number', type=int),
            status=request.form.get('status', 'needed'),
            condition=request.form.get('condition'),
            cost=request.form.get('cost', type=float),
            notes=request.form.get('notes'),
            setup_instructions=request.form.get('setup_instructions'),
            return_to=request.form.get('return_to')
        )
        bin_id = request.form.get('bin_id', type=int)
        if bin_id:
            item.bin_id = bin_id
        if request.form.get('return_by'):
            item.return_by = datetime.strptime(request.form.get('return_by'), '%Y-%m-%d').date()
        db.session.add(item)
        db.session.commit()
        flash('Item added to inventory!', 'success')
        return redirect(url_for('inventory_view', wedding_id=wedding_id))
    return render_template('inventory/add.html', wedding=wedding, bins=bins,
                         categories=INVENTORY_CATEGORIES, areas=INVENTORY_AREAS)


@app.route('/wedding/<int:wedding_id>/inventory/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def inventory_item_edit(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = get_entity_or_404(InventoryItem, item_id, wedding_id)
    bins = InventoryBin.query.filter_by(wedding_id=wedding_id).order_by(InventoryBin.label).all()
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.category = request.form.get('category')
        item.quantity = request.form.get('quantity', type=int) or 1
        item.source = request.form.get('source')
        item.source_detail = request.form.get('source_detail')
        item.area = request.form.get('area')
        item.table_number = request.form.get('table_number', type=int)
        item.status = request.form.get('status', 'needed')
        item.condition = request.form.get('condition')
        item.cost = request.form.get('cost', type=float)
        item.notes = request.form.get('notes')
        item.setup_instructions = request.form.get('setup_instructions')
        item.return_to = request.form.get('return_to')
        bin_id = request.form.get('bin_id', type=int)
        item.bin_id = bin_id if bin_id else None
        if request.form.get('return_by'):
            item.return_by = datetime.strptime(request.form.get('return_by'), '%Y-%m-%d').date()
        else:
            item.return_by = None
        db.session.commit()
        flash('Item updated!', 'success')
        return redirect(url_for('inventory_view', wedding_id=wedding_id))
    return render_template('inventory/edit.html', wedding=wedding, item=item, bins=bins,
                         categories=INVENTORY_CATEGORIES, areas=INVENTORY_AREAS)


@app.route('/wedding/<int:wedding_id>/inventory/<int:item_id>/delete', methods=['POST'])
@login_required
def inventory_item_delete(wedding_id, item_id):
    get_wedding_or_403(wedding_id)
    item = get_entity_or_404(InventoryItem, item_id, wedding_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from inventory.', 'success')
    return redirect(url_for('inventory_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/inventory/<int:item_id>/status', methods=['POST'])
@login_required
def inventory_item_status(wedding_id, item_id):
    get_wedding_or_403(wedding_id)
    item = get_entity_or_404(InventoryItem, item_id, wedding_id)
    new_status = request.form.get('status')
    if new_status in ('needed', 'acquired', 'packed', 'setup', 'returned', 'lost'):
        item.status = new_status
        db.session.commit()
    return redirect(request.referrer or url_for('inventory_view', wedding_id=wedding_id))


# --- Bins ---

@app.route('/wedding/<int:wedding_id>/inventory/bins/add', methods=['GET', 'POST'])
@login_required
def inventory_bin_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    if request.method == 'POST':
        bin = InventoryBin(
            wedding_id=wedding_id,
            label=request.form.get('label'),
            area=request.form.get('area'),
            table_number=request.form.get('table_number', type=int),
            color_code=request.form.get('color_code'),
            storage_location=request.form.get('storage_location'),
            assigned_to=request.form.get('assigned_to'),
            notes=request.form.get('notes')
        )
        db.session.add(bin)
        db.session.commit()
        flash('Bin created!', 'success')
        return redirect(url_for('inventory_view', wedding_id=wedding_id))
    return render_template('inventory/bin_add.html', wedding=wedding, areas=INVENTORY_AREAS)


@app.route('/wedding/<int:wedding_id>/inventory/bins/<int:bin_id>')
@login_required
def inventory_bin_view(wedding_id, bin_id):
    wedding = get_wedding_or_403(wedding_id)
    bin = get_entity_or_404(InventoryBin, bin_id, wedding_id)
    # Get unassigned items for quick-assign
    unassigned = InventoryItem.query.filter_by(wedding_id=wedding_id, bin_id=None).all()
    return render_template('inventory/bin_view.html', wedding=wedding, bin=bin,
                         unassigned=unassigned, categories=INVENTORY_CATEGORIES)


@app.route('/wedding/<int:wedding_id>/inventory/bins/<int:bin_id>/edit', methods=['GET', 'POST'])
@login_required
def inventory_bin_edit(wedding_id, bin_id):
    wedding = get_wedding_or_403(wedding_id)
    bin = get_entity_or_404(InventoryBin, bin_id, wedding_id)
    if request.method == 'POST':
        bin.label = request.form.get('label')
        bin.area = request.form.get('area')
        bin.table_number = request.form.get('table_number', type=int)
        bin.color_code = request.form.get('color_code')
        bin.storage_location = request.form.get('storage_location')
        bin.assigned_to = request.form.get('assigned_to')
        bin.notes = request.form.get('notes')
        db.session.commit()
        flash('Bin updated!', 'success')
        return redirect(url_for('inventory_bin_view', wedding_id=wedding_id, bin_id=bin_id))
    return render_template('inventory/bin_edit.html', wedding=wedding, bin=bin, areas=INVENTORY_AREAS)


@app.route('/wedding/<int:wedding_id>/inventory/bins/<int:bin_id>/delete', methods=['POST'])
@login_required
def inventory_bin_delete(wedding_id, bin_id):
    get_wedding_or_403(wedding_id)
    bin = get_entity_or_404(InventoryBin, bin_id, wedding_id)
    # Unassign items from this bin before deleting
    for item in bin.items:
        item.bin_id = None
    db.session.delete(bin)
    db.session.commit()
    flash('Bin deleted. Items have been unassigned.', 'success')
    return redirect(url_for('inventory_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/inventory/bins/<int:bin_id>/assign', methods=['POST'])
@login_required
def inventory_bin_assign(wedding_id, bin_id):
    """Quick-assign items to a bin."""
    item_ids = request.form.getlist('item_ids', type=int)
    for item_id in item_ids:
        item = InventoryItem.query.get(item_id)
        if item and item.wedding_id == wedding_id:
            item.bin_id = bin_id
    db.session.commit()
    flash(f'{len(item_ids)} item(s) assigned to bin.', 'success')
    return redirect(url_for('inventory_bin_view', wedding_id=wedding_id, bin_id=bin_id))


@app.route('/wedding/<int:wedding_id>/inventory/bins/<int:bin_id>/print')
@login_required
def inventory_bin_print(wedding_id, bin_id):
    wedding = get_wedding_or_403(wedding_id)
    bin = get_entity_or_404(InventoryBin, bin_id, wedding_id)
    return _render_or_pdf('inventory/bin_print.html', f'bin_{bin.label}_{wedding_id}.pdf',
                          wedding=wedding, bin=bin)


@app.route('/wedding/<int:wedding_id>/inventory/print')
@login_required
def inventory_print_all(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    bins = InventoryBin.query.filter_by(wedding_id=wedding_id).order_by(InventoryBin.label).all()
    unassigned = InventoryItem.query.filter_by(wedding_id=wedding_id, bin_id=None).all()
    return _render_or_pdf('inventory/print_all.html', f'inventory_{wedding_id}.pdf',
                          wedding=wedding, bins=bins, unassigned=unassigned)


@app.route('/wedding/<int:wedding_id>/inventory/labels')
@login_required
def inventory_labels_print(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    bins = InventoryBin.query.filter_by(wedding_id=wedding_id).order_by(InventoryBin.label).all()
    return _render_or_pdf('inventory/labels_print.html', f'labels_{wedding_id}.pdf',
                          wedding=wedding, bins=bins)


@app.route('/wedding/<int:wedding_id>/inventory/export')
@login_required
def inventory_export_csv(wedding_id):
    items = InventoryItem.query.filter_by(wedding_id=wedding_id).all()
    bins_map = {b.id: b.label for b in InventoryBin.query.filter_by(wedding_id=wedding_id).all()}
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Name', 'Category', 'Qty', 'Source', 'Source Detail', 'Area', 'Table #',
                     'Status', 'Condition', 'Cost', 'Bin', 'Return By', 'Return To', 'Notes'])
    for i in items:
        writer.writerow([i.name, i.category, i.quantity, i.source, i.source_detail,
                        i.area, i.table_number, i.status, i.condition, i.cost,
                        bins_map.get(i.bin_id, ''), i.return_by, i.return_to, i.notes])
    output.seek(0)
    return Response(output, mimetype='text/csv',
                   headers={'Content-Disposition': 'attachment;filename=inventory.csv'})


# ============================================
# EMERGENCY KIT MANAGEMENT ROUTES
# ============================================

EMERGENCY_KIT_CATEGORIES = ['fashion', 'health', 'beauty', 'tools', 'food', 'documents']

@app.route('/wedding/<int:wedding_id>/emergency-kit')
@login_required
def emergency_kit_view(wedding_id):
    """View and manage emergency kit items."""
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.emergency_kit_items:
        seed_default_emergency_kit(wedding.id)
    items_by_category = {}
    for cat in EMERGENCY_KIT_CATEGORIES:
        items_by_category[cat] = sorted(
            [i for i in wedding.emergency_kit_items if i.category == cat],
            key=lambda x: x.item_name
        )
    total = len(wedding.emergency_kit_items)
    packed = sum(1 for i in wedding.emergency_kit_items if i.packed)
    return render_template('emergency_kit_manage.html', wedding=wedding,
                           items_by_category=items_by_category,
                           categories=EMERGENCY_KIT_CATEGORIES,
                           total=total, packed=packed)

@app.route('/wedding/<int:wedding_id>/emergency-kit/add', methods=['POST'])
@login_required
def emergency_kit_add(wedding_id):
    """Add a new emergency kit item."""
    wedding = get_wedding_or_403(wedding_id)
    item_name = request.form.get('item_name', '').strip()
    category = request.form.get('category', 'tools')
    notes = request.form.get('notes', '').strip()
    if not item_name:
        flash('Item name is required.', 'error')
        return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))
    if category not in EMERGENCY_KIT_CATEGORIES:
        category = 'tools'
    item = EmergencyKitItem(
        wedding_id=wedding_id,
        item_name=item_name,
        category=category,
        packed=False,
        notes=notes or None
    )
    db.session.add(item)
    db.session.commit()
    flash('Item added to emergency kit!', 'success')
    return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/emergency-kit/<int:item_id>/edit', methods=['POST'])
@login_required
def emergency_kit_edit(wedding_id, item_id):
    """Edit an emergency kit item."""
    wedding = get_wedding_or_403(wedding_id)
    item = EmergencyKitItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    item_name = request.form.get('item_name', '').strip()
    if not item_name:
        flash('Item name is required.', 'error')
        return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))
    item.item_name = item_name
    category = request.form.get('category', item.category)
    if category in EMERGENCY_KIT_CATEGORIES:
        item.category = category
    item.notes = request.form.get('notes', '').strip() or None
    db.session.commit()
    flash('Item updated!', 'success')
    return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/emergency-kit/<int:item_id>/delete', methods=['POST'])
@login_required
def emergency_kit_delete(wedding_id, item_id):
    """Delete an emergency kit item."""
    wedding = get_wedding_or_403(wedding_id)
    item = EmergencyKitItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed from emergency kit.', 'success')
    return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/emergency-kit/<int:item_id>/toggle', methods=['POST'])
@login_required
def emergency_kit_toggle(wedding_id, item_id):
    """Toggle packed status of an emergency kit item."""
    wedding = get_wedding_or_403(wedding_id)
    item = EmergencyKitItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    item.packed = not item.packed
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'packed': item.packed, 'id': item.id})
    return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/emergency-kit/reset', methods=['POST'])
@login_required
def emergency_kit_reset(wedding_id):
    """Reset emergency kit to default items."""
    wedding = get_wedding_or_403(wedding_id)
    EmergencyKitItem.query.filter_by(wedding_id=wedding.id).delete()
    db.session.commit()
    seed_default_emergency_kit(wedding.id)
    flash('Emergency kit reset to defaults.', 'success')
    return redirect(url_for('emergency_kit_view', wedding_id=wedding_id))


# ============================================
# PRE-WEDDING EVENTS
# ============================================

@app.route('/wedding/<int:wedding_id>/pre-wedding-events')
@login_required
def pre_wedding_events_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    events = PreWeddingEvent.query.filter_by(wedding_id=wedding.id).order_by(PreWeddingEvent.date).all()
    return render_template('pre_wedding_events/view.html', wedding=wedding, events=events,
                         event_types=PRE_WEDDING_EVENT_TYPES)

@app.route('/wedding/<int:wedding_id>/pre-wedding-events/add', methods=['GET', 'POST'])
@login_required
def pre_wedding_events_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        event = PreWeddingEvent(
            wedding_id=wedding.id,
            event_type=request.form.get('event_type'),
            name=request.form.get('name'),
            time=request.form.get('time'),
            end_time=request.form.get('end_time'),
            venue_name=request.form.get('venue_name'),
            venue_address=request.form.get('venue_address'),
            host_name=request.form.get('host_name'),
            host_phone=request.form.get('host_phone'),
            host_email=request.form.get('host_email'),
            expected_guest_count=request.form.get('expected_guest_count', type=int),
            estimated_cost=request.form.get('estimated_cost', type=float),
            notes=request.form.get('notes'),
            status=request.form.get('status', 'planning')
        )
        if request.form.get('date'):
            event.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        db.session.add(event)
        db.session.commit()
        flash('Pre-wedding event added!', 'success')
        return redirect(url_for('pre_wedding_events_view', wedding_id=wedding_id))
    return render_template('pre_wedding_events/add.html', wedding=wedding,
                         event_types=PRE_WEDDING_EVENT_TYPES)

@app.route('/wedding/<int:wedding_id>/pre-wedding-events/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def pre_wedding_events_edit(wedding_id, event_id):
    wedding = get_wedding_or_403(wedding_id)
    event = PreWeddingEvent.query.get_or_404(event_id)
    if event.wedding_id != wedding.id:
        abort(403)
    if request.method == 'POST':
        event.event_type = request.form.get('event_type')
        event.name = request.form.get('name')
        event.time = request.form.get('time')
        event.end_time = request.form.get('end_time')
        event.venue_name = request.form.get('venue_name')
        event.venue_address = request.form.get('venue_address')
        event.host_name = request.form.get('host_name')
        event.host_phone = request.form.get('host_phone')
        event.host_email = request.form.get('host_email')
        event.expected_guest_count = request.form.get('expected_guest_count', type=int)
        event.estimated_cost = request.form.get('estimated_cost', type=float)
        event.actual_cost = request.form.get('actual_cost', type=float)
        event.notes = request.form.get('notes')
        event.status = request.form.get('status')
        if request.form.get('date'):
            event.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
        else:
            event.date = None
        db.session.commit()
        flash('Event updated!', 'success')
        return redirect(url_for('pre_wedding_events_view', wedding_id=wedding_id))
    return render_template('pre_wedding_events/edit.html', wedding=wedding, event=event,
                         event_types=PRE_WEDDING_EVENT_TYPES)

@app.route('/wedding/<int:wedding_id>/pre-wedding-events/<int:event_id>/delete', methods=['POST'])
@login_required
def pre_wedding_events_delete(wedding_id, event_id):
    wedding = get_wedding_or_403(wedding_id)
    event = PreWeddingEvent.query.get_or_404(event_id)
    if event.wedding_id != wedding.id:
        abort(403)
    db.session.delete(event)
    db.session.commit()
    flash('Event removed.', 'success')
    return redirect(url_for('pre_wedding_events_view', wedding_id=wedding_id))


# ============================================
# WEDDING SIGNAGE CHECKLIST
# ============================================

@app.route('/wedding/<int:wedding_id>/signage')
@login_required
def signage_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = SignageItem.query.filter_by(wedding_id=wedding.id).all()
    ceremony_items = [i for i in items if i.category == 'ceremony']
    reception_items = [i for i in items if i.category == 'reception']
    directional_items = [i for i in items if i.category == 'directional']
    other_items = [i for i in items if i.category not in ('ceremony', 'reception', 'directional')]
    stats = {
        'total': len(items),
        'completed': sum(1 for i in items if i.status == 'received' or i.status == 'placed'),
        'total_cost': sum(i.cost or 0 for i in items)
    }
    return render_template('signage/view.html', wedding=wedding, items=items,
                         ceremony_items=ceremony_items, reception_items=reception_items,
                         directional_items=directional_items, other_items=other_items, stats=stats)

@app.route('/wedding/<int:wedding_id>/signage/add', methods=['GET', 'POST'])
@login_required
def signage_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = SignageItem(
            wedding_id=wedding.id,
            name=request.form.get('name'),
            category=request.form.get('category'),
            description=request.form.get('description'),
            location=request.form.get('location'),
            size=request.form.get('size'),
            material=request.form.get('material'),
            vendor=request.form.get('vendor'),
            cost=request.form.get('cost', type=float),
            status=request.form.get('status', 'needed'),
            notes=request.form.get('notes')
        )
        db.session.add(item)
        db.session.commit()
        flash('Sign added!', 'success')
        return redirect(url_for('signage_view', wedding_id=wedding_id))
    return render_template('signage/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/signage/populate-defaults', methods=['POST'])
@login_required
def signage_populate_defaults(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    for name, category, description, location in DEFAULT_SIGNAGE_ITEMS:
        existing = SignageItem.query.filter_by(wedding_id=wedding.id, name=name).first()
        if not existing:
            item = SignageItem(wedding_id=wedding.id, name=name, category=category,
                             description=description, location=location, status='needed')
            db.session.add(item)
    db.session.commit()
    flash('Default signage checklist populated!', 'success')
    return redirect(url_for('signage_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/signage/<int:item_id>/toggle', methods=['POST'])
@login_required
def signage_toggle(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = SignageItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    # Cycle: needed -> ordered -> received -> placed -> needed
    status_cycle = ['needed', 'ordered', 'received', 'placed']
    try:
        idx = status_cycle.index(item.status)
        item.status = status_cycle[(idx + 1) % len(status_cycle)]
    except ValueError:
        item.status = 'needed'
    db.session.commit()
    return redirect(url_for('signage_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/signage/<int:item_id>/delete', methods=['POST'])
@login_required
def signage_delete(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = SignageItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Sign removed.', 'success')
    return redirect(url_for('signage_view', wedding_id=wedding_id))


# ============================================
# DAY-OF CONTACT SHEET & TASK DELEGATION
# ============================================

@app.route('/wedding/<int:wedding_id>/day-of-contacts')
@login_required
def day_of_contacts_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    contacts = DayOfContact.query.filter_by(wedding_id=wedding.id).all()
    tasks = DayOfTask.query.filter_by(wedding_id=wedding.id).all()
    vendor_contacts = [c for c in contacts if c.category == 'vendor']
    party_contacts = [c for c in contacts if c.category == 'wedding_party']
    family_contacts = [c for c in contacts if c.category == 'family']
    other_contacts = [c for c in contacts if c.category not in ('vendor', 'wedding_party', 'family')]
    setup_tasks = [t for t in tasks if t.category == 'setup']
    during_tasks = [t for t in tasks if t.category == 'during']
    breakdown_tasks = [t for t in tasks if t.category == 'breakdown']
    emergency_tasks = [t for t in tasks if t.category == 'emergency']
    return render_template('day_of_contacts/view.html', wedding=wedding,
                         contacts=contacts, tasks=tasks,
                         vendor_contacts=vendor_contacts, party_contacts=party_contacts,
                         family_contacts=family_contacts, other_contacts=other_contacts,
                         setup_tasks=setup_tasks, during_tasks=during_tasks,
                         breakdown_tasks=breakdown_tasks, emergency_tasks=emergency_tasks)

@app.route('/wedding/<int:wedding_id>/day-of-contacts/add', methods=['GET', 'POST'])
@login_required
def day_of_contacts_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        contact = DayOfContact(
            wedding_id=wedding.id,
            name=request.form.get('name'),
            role=request.form.get('role'),
            category=request.form.get('category'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            arrival_time=request.form.get('arrival_time'),
            departure_time=request.form.get('departure_time'),
            setup_location=request.form.get('setup_location'),
            notes=request.form.get('notes')
        )
        db.session.add(contact)
        db.session.commit()
        flash('Contact added!', 'success')
        return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))
    return render_template('day_of_contacts/add_contact.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/day-of-contacts/<int:contact_id>/delete', methods=['POST'])
@login_required
def day_of_contacts_delete(wedding_id, contact_id):
    wedding = get_wedding_or_403(wedding_id)
    contact = DayOfContact.query.get_or_404(contact_id)
    if contact.wedding_id != wedding.id:
        abort(403)
    db.session.delete(contact)
    db.session.commit()
    flash('Contact removed.', 'success')
    return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/day-of-tasks/add', methods=['GET', 'POST'])
@login_required
def day_of_tasks_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        task = DayOfTask(
            wedding_id=wedding.id,
            task=request.form.get('task'),
            assigned_to=request.form.get('assigned_to'),
            category=request.form.get('category'),
            timing=request.form.get('timing'),
            notes=request.form.get('notes')
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added!', 'success')
        return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))
    return render_template('day_of_contacts/add_task.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/day-of-tasks/<int:task_id>/toggle', methods=['POST'])
@login_required
def day_of_tasks_toggle(wedding_id, task_id):
    wedding = get_wedding_or_403(wedding_id)
    task = DayOfTask.query.get_or_404(task_id)
    if task.wedding_id != wedding.id:
        abort(403)
    task.completed = not task.completed
    db.session.commit()
    return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/day-of-tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def day_of_tasks_delete(wedding_id, task_id):
    wedding = get_wedding_or_403(wedding_id)
    task = DayOfTask.query.get_or_404(task_id)
    if task.wedding_id != wedding.id:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash('Task removed.', 'success')
    return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/day-of-tasks/populate-defaults', methods=['POST'])
@login_required
def day_of_tasks_populate_defaults(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    for task_name, category, timing in DEFAULT_DAY_OF_TASKS:
        existing = DayOfTask.query.filter_by(wedding_id=wedding.id, task=task_name).first()
        if not existing:
            task = DayOfTask(wedding_id=wedding.id, task=task_name, category=category, timing=timing)
            db.session.add(task)
    db.session.commit()
    flash('Default day-of tasks populated!', 'success')
    return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/day-of-contacts/import-vendors', methods=['POST'])
@login_required
def day_of_contacts_import_vendors(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    vendors = Vendor.query.filter_by(wedding_id=wedding.id).all()
    imported = 0
    for v in vendors:
        existing = DayOfContact.query.filter_by(wedding_id=wedding.id, name=v.contact_name or v.business_name).first()
        if not existing:
            contact = DayOfContact(
                wedding_id=wedding.id,
                name=v.contact_name or v.business_name,
                role=v.vendor_type or 'Vendor',
                category='vendor',
                phone=v.phone,
                email=v.email,
                notes=v.notes
            )
            db.session.add(contact)
            imported += 1
    db.session.commit()
    flash(f'{imported} vendor contacts imported!', 'success')
    return redirect(url_for('day_of_contacts_view', wedding_id=wedding_id))


# ============================================
# WEDDING DAY PACKING LIST
# ============================================

@app.route('/wedding/<int:wedding_id>/packing-list')
@login_required
def packing_list_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = PackingListItem.query.filter_by(wedding_id=wedding.id).all()
    categories = {}
    for item in items:
        cat = item.category or 'other'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    total = len(items)
    packed = sum(1 for i in items if i.packed)
    return render_template('packing_list/view.html', wedding=wedding, items=items,
                         categories=categories, total=total, packed=packed)

@app.route('/wedding/<int:wedding_id>/packing-list/add', methods=['GET', 'POST'])
@login_required
def packing_list_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = PackingListItem(
            wedding_id=wedding.id,
            item_name=request.form.get('item_name'),
            category=request.form.get('category'),
            assigned_to=request.form.get('assigned_to'),
            notes=request.form.get('notes')
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added!', 'success')
        return redirect(url_for('packing_list_view', wedding_id=wedding_id))
    return render_template('packing_list/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/packing-list/<int:item_id>/toggle', methods=['POST'])
@login_required
def packing_list_toggle(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = PackingListItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    item.packed = not item.packed
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'packed': item.packed, 'id': item.id})
    return redirect(url_for('packing_list_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/packing-list/<int:item_id>/delete', methods=['POST'])
@login_required
def packing_list_delete(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = PackingListItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed.', 'success')
    return redirect(url_for('packing_list_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/packing-list/populate-defaults', methods=['POST'])
@login_required
def packing_list_populate_defaults(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    for item_name, category in DEFAULT_PACKING_LIST:
        existing = PackingListItem.query.filter_by(wedding_id=wedding.id, item_name=item_name).first()
        if not existing:
            item = PackingListItem(wedding_id=wedding.id, item_name=item_name, category=category)
            db.session.add(item)
    db.session.commit()
    flash('Default packing list populated!', 'success')
    return redirect(url_for('packing_list_view', wedding_id=wedding_id))


# ============================================
# NAME CHANGE CHECKLIST
# ============================================

@app.route('/wedding/<int:wedding_id>/name-change')
@login_required
def name_change_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    tasks = NameChangeTask.query.filter_by(wedding_id=wedding.id).order_by(NameChangeTask.order).all()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    categories = {}
    for task in tasks:
        cat = task.category or 'other'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(task)
    return render_template('name_change/view.html', wedding=wedding, tasks=tasks,
                         categories=categories, total=total, completed=completed)

@app.route('/wedding/<int:wedding_id>/name-change/add', methods=['GET', 'POST'])
@login_required
def name_change_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        task = NameChangeTask(
            wedding_id=wedding.id,
            task_name=request.form.get('task_name'),
            category=request.form.get('category'),
            reference_number=request.form.get('reference_number'),
            notes=request.form.get('notes')
        )
        db.session.add(task)
        db.session.commit()
        flash('Task added!', 'success')
        return redirect(url_for('name_change_view', wedding_id=wedding_id))
    return render_template('name_change/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/name-change/<int:task_id>/toggle', methods=['POST'])
@login_required
def name_change_toggle(wedding_id, task_id):
    wedding = get_wedding_or_403(wedding_id)
    task = NameChangeTask.query.get_or_404(task_id)
    if task.wedding_id != wedding.id:
        abort(403)
    task.completed = not task.completed
    task.completed_date = date.today() if task.completed else None
    db.session.commit()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'completed': task.completed, 'id': task.id})
    return redirect(url_for('name_change_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/name-change/<int:task_id>/delete', methods=['POST'])
@login_required
def name_change_delete(wedding_id, task_id):
    wedding = get_wedding_or_403(wedding_id)
    task = NameChangeTask.query.get_or_404(task_id)
    if task.wedding_id != wedding.id:
        abort(403)
    db.session.delete(task)
    db.session.commit()
    flash('Task removed.', 'success')
    return redirect(url_for('name_change_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/name-change/populate-defaults', methods=['POST'])
@login_required
def name_change_populate_defaults(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    for task_name, category, order in DEFAULT_NAME_CHANGE_TASKS:
        existing = NameChangeTask.query.filter_by(wedding_id=wedding.id, task_name=task_name).first()
        if not existing:
            task = NameChangeTask(wedding_id=wedding.id, task_name=task_name, category=category, order=order)
            db.session.add(task)
    db.session.commit()
    flash('Default name change checklist populated!', 'success')
    return redirect(url_for('name_change_view', wedding_id=wedding_id))


# ============================================
# CUSTOM RSVP QUESTIONS
# ============================================

@app.route('/wedding/<int:wedding_id>/custom-rsvp-questions')
@login_required
def custom_rsvp_questions_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    questions = CustomRsvpQuestion.query.filter_by(wedding_id=wedding.id).order_by(CustomRsvpQuestion.order).all()
    return render_template('custom_rsvp/view.html', wedding=wedding, questions=questions)

@app.route('/wedding/<int:wedding_id>/custom-rsvp-questions/add', methods=['GET', 'POST'])
@login_required
def custom_rsvp_questions_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        import json
        options_text = request.form.get('options', '').strip()
        options_json = None
        if options_text:
            options_json = json.dumps([o.strip() for o in options_text.split('\n') if o.strip()])
        question = CustomRsvpQuestion(
            wedding_id=wedding.id,
            question_text=request.form.get('question_text'),
            question_type=request.form.get('question_type', 'text'),
            options=options_json,
            required=request.form.get('required') == 'on',
            active=True
        )
        # Set order to next available
        max_order = db.session.query(db.func.max(CustomRsvpQuestion.order)).filter_by(wedding_id=wedding.id).scalar() or 0
        question.order = max_order + 1
        db.session.add(question)
        db.session.commit()
        flash('Custom RSVP question added!', 'success')
        return redirect(url_for('custom_rsvp_questions_view', wedding_id=wedding_id))
    return render_template('custom_rsvp/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/custom-rsvp-questions/<int:question_id>/toggle', methods=['POST'])
@login_required
def custom_rsvp_questions_toggle(wedding_id, question_id):
    wedding = get_wedding_or_403(wedding_id)
    question = CustomRsvpQuestion.query.get_or_404(question_id)
    if question.wedding_id != wedding.id:
        abort(403)
    question.active = not question.active
    db.session.commit()
    return redirect(url_for('custom_rsvp_questions_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/custom-rsvp-questions/<int:question_id>/delete', methods=['POST'])
@login_required
def custom_rsvp_questions_delete(wedding_id, question_id):
    wedding = get_wedding_or_403(wedding_id)
    question = CustomRsvpQuestion.query.get_or_404(question_id)
    if question.wedding_id != wedding.id:
        abort(403)
    db.session.delete(question)
    db.session.commit()
    flash('Question removed.', 'success')
    return redirect(url_for('custom_rsvp_questions_view', wedding_id=wedding_id))


# ============================================
# HIDDEN COST QUICK-ADD TO BUDGET
# ============================================

@app.route('/wedding/<int:wedding_id>/budget/add-hidden-cost', methods=['POST'])
@login_required
def budget_add_hidden_cost(wedding_id):
    """Quick-add a hidden cost suggestion to the budget."""
    wedding = get_wedding_or_403(wedding_id)
    if not wedding.budget:
        budget = Budget(wedding_id=wedding_id, total_budget=0)
        db.session.add(budget)
        db.session.commit()
    expense = BudgetExpense(
        budget_id=wedding.budget.id,
        category=request.form.get('category'),
        item_name=request.form.get('item_name'),
        estimated_cost=request.form.get('estimated_cost', type=float),
        payment_status='unpaid',
        notes=request.form.get('description')
    )
    db.session.add(expense)
    db.session.commit()
    flash(f'Added "{expense.item_name}" to your budget!', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))


# ============================================
# GUEST ACCESSIBILITY PLANNER
# ============================================

@app.route('/wedding/<int:wedding_id>/accessibility')
@login_required
def accessibility_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    items = AccessibilityItem.query.filter_by(wedding_id=wedding.id).all()
    categories = {}
    for item in items:
        cat = item.category or 'other'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    total = len(items)
    arranged = sum(1 for i in items if i.status in ('arranged', 'confirmed'))
    return render_template('accessibility/view.html', wedding=wedding, items=items,
                         categories=categories, total=total, arranged=arranged)

@app.route('/wedding/<int:wedding_id>/accessibility/add', methods=['GET', 'POST'])
@login_required
def accessibility_add(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    if request.method == 'POST':
        item = AccessibilityItem(
            wedding_id=wedding.id,
            item_name=request.form.get('item_name'),
            category=request.form.get('category'),
            assigned_to=request.form.get('assigned_to'),
            cost=request.form.get('cost', type=float),
            vendor=request.form.get('vendor'),
            notes=request.form.get('notes')
        )
        db.session.add(item)
        db.session.commit()
        flash('Accessibility item added!', 'success')
        return redirect(url_for('accessibility_view', wedding_id=wedding_id))
    return render_template('accessibility/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/accessibility/<int:item_id>/toggle', methods=['POST'])
@login_required
def accessibility_toggle(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = AccessibilityItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    status_cycle = ['needed', 'arranged', 'confirmed']
    try:
        idx = status_cycle.index(item.status)
        item.status = status_cycle[(idx + 1) % len(status_cycle)]
    except ValueError:
        item.status = 'needed'
    db.session.commit()
    return redirect(url_for('accessibility_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/accessibility/<int:item_id>/delete', methods=['POST'])
@login_required
def accessibility_delete(wedding_id, item_id):
    wedding = get_wedding_or_403(wedding_id)
    item = AccessibilityItem.query.get_or_404(item_id)
    if item.wedding_id != wedding.id:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('Item removed.', 'success')
    return redirect(url_for('accessibility_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/accessibility/populate-defaults', methods=['POST'])
@login_required
def accessibility_populate_defaults(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    for item_name, category, notes in DEFAULT_ACCESSIBILITY_CHECKLIST:
        existing = AccessibilityItem.query.filter_by(wedding_id=wedding.id, item_name=item_name).first()
        if not existing:
            item = AccessibilityItem(wedding_id=wedding.id, item_name=item_name,
                                    category=category, notes=notes)
            db.session.add(item)
    db.session.commit()
    flash('Default accessibility checklist populated!', 'success')
    return redirect(url_for('accessibility_view', wedding_id=wedding_id))


# ============================================
# WEDDING HASHTAG & SOCIAL MEDIA
# ============================================

@app.route('/wedding/<int:wedding_id>/social-media', methods=['GET', 'POST'])
@login_required
def social_media_view(wedding_id):
    wedding = get_wedding_or_403(wedding_id)
    settings = wedding.social_media
    if request.method == 'POST':
        if not settings:
            settings = SocialMediaSettings(wedding_id=wedding.id)
            db.session.add(settings)
        settings.wedding_hashtag = request.form.get('wedding_hashtag', '').strip()
        settings.backup_hashtags = request.form.get('backup_hashtags', '').strip()
        settings.unplugged_ceremony = request.form.get('unplugged_ceremony') == 'on'
        settings.unplugged_message = request.form.get('unplugged_message', '').strip()
        settings.social_sharing_policy = request.form.get('social_sharing_policy', 'open')
        settings.sharing_policy_message = request.form.get('sharing_policy_message', '').strip()
        settings.photo_sharing_app = request.form.get('photo_sharing_app', '').strip()
        settings.photo_sharing_url = request.form.get('photo_sharing_url', '').strip()
        settings.photo_sharing_notes = request.form.get('photo_sharing_notes', '').strip()
        settings.notes = request.form.get('notes', '').strip()
        db.session.commit()
        flash('Social media settings saved!', 'success')
        return redirect(url_for('social_media_view', wedding_id=wedding_id))
    return render_template('social_media/view.html', wedding=wedding, settings=settings,
                         unplugged_templates=UNPLUGGED_CEREMONY_TEMPLATES,
                         sharing_policies=SOCIAL_SHARING_POLICIES)


# ============================================
# TIMELINE BUFFER WARNINGS
# ============================================

@app.route('/wedding/<int:wedding_id>/timeline-analysis')
@login_required
def timeline_analysis(wedding_id):
    """Analyze the day-of timeline for common issues: gaps, missing buffers, overtime risks."""
    wedding = get_wedding_or_403(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.time or datetime.min.time(), x.order))

    warnings = []
    tips = []

    # Only analyze if there are timed items
    timed_items = [i for i in items if i.time]

    if len(timed_items) < 2:
        tips.append({
            'type': 'info',
            'title': 'Add More Timeline Items',
            'message': 'Add at least a few timed items to your day-of timeline for analysis (e.g., getting ready, ceremony, photos, reception).'
        })
    else:
        # Check for gaps between consecutive items
        for i in range(len(timed_items) - 1):
            current = timed_items[i]
            next_item = timed_items[i + 1]
            current_minutes = current.time.hour * 60 + current.time.minute
            next_minutes = next_item.time.hour * 60 + next_item.time.minute
            gap = next_minutes - current_minutes

            if gap > 90:
                warnings.append({
                    'type': 'gap',
                    'title': f'Large gap: {gap} minutes',
                    'message': f'Between "{current.title}" ({current.time.strftime("%I:%M %p")}) and "{next_item.title}" ({next_item.time.strftime("%I:%M %p")}). Guests may lose momentum during long gaps. Consider adding cocktail hour entertainment or activities.',
                    'severity': 'warning'
                })
            elif gap < 10 and gap >= 0:
                warnings.append({
                    'type': 'buffer',
                    'title': f'No buffer: only {gap} minutes',
                    'message': f'Between "{current.title}" and "{next_item.title}". Add 15-30 minutes of buffer time. Hair/makeup runs long, guests arrive late, and photos take longer than expected.',
                    'severity': 'danger'
                })

        # Check total timeline length vs typical vendor contracts (8-10 hours)
        first_time = timed_items[0].time
        last_time = timed_items[-1].time
        total_minutes = (last_time.hour * 60 + last_time.minute) - (first_time.hour * 60 + first_time.minute)
        total_hours = total_minutes / 60

        if total_hours > 10:
            warnings.append({
                'type': 'overtime',
                'title': f'Timeline spans {total_hours:.1f} hours',
                'message': 'Most vendor contracts cover 8-10 hours. Overtime fees are typically $100-500/hour per vendor. Check your contracts and add overtime costs to your budget.',
                'severity': 'warning'
            })

        # Check for common missing elements
        categories = set(i.category for i in items if i.category)
        titles_lower = ' '.join(i.title.lower() for i in items)

        if 'prep' not in categories and 'getting ready' not in titles_lower and 'hair' not in titles_lower:
            tips.append({'type': 'missing', 'title': 'Getting Ready Time',
                        'message': 'No getting-ready block found. Hair and makeup typically takes 3-5 hours for the full party. The person getting married should finish first (not last) to allow 45-60 minutes before dressing.'})

        if 'photos' not in categories and 'portrait' not in titles_lower and 'photo' not in titles_lower:
            tips.append({'type': 'missing', 'title': 'Portrait Session',
                        'message': 'No photo session found. Plan 30-40 min for family formals, 20-30 min for bridal party, and 30-45 min for couple portraits. Reserve 15-20 min for golden hour/sunset shots.'})

        if 'first look' not in titles_lower:
            tips.append({'type': 'suggestion', 'title': 'Consider a First Look',
                        'message': 'A first look (45-60 min before ceremony) lets you do portraits before the ceremony, reducing the gap between ceremony and reception.'})

        if 'cocktail' not in titles_lower and 'reception' in categories:
            tips.append({'type': 'missing', 'title': 'Cocktail Hour',
                        'message': 'No cocktail hour found. This fills the gap while the couple does post-ceremony photos. Plan entertainment, appetizers, and drinks.'})

        if 'send' not in titles_lower and 'exit' not in titles_lower and 'departure' not in titles_lower:
            tips.append({'type': 'suggestion', 'title': 'Plan Your Exit',
                        'message': 'No send-off/exit planned. Sparklers, bubbles, or a grand exit make for great photos and a memorable ending.'})

    return render_template('day_of/analysis.html', wedding=wedding,
                         warnings=warnings, tips=tips, items=timed_items)


@app.route('/wedding/<int:wedding_id>/etiquette-guide')
@login_required
def etiquette_guide_view(wedding_id):
    """Wedding etiquette guide: being present, engaging with guests, and mindfulness tips."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('etiquette_guide/view.html', wedding=wedding)


@app.route('/wedding/<int:wedding_id>/print/etiquette-guide')
@login_required
def print_etiquette_guide(wedding_id):
    """Printable wedding etiquette guide."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/etiquette_guide.html', f'etiquette_guide_{wedding_id}.pdf',
                          wedding=wedding)


@app.route('/wedding/<int:wedding_id>/guides/pacing')
@login_required
def pacing_guide_view(wedding_id):
    """Pacing Your Wedding Day guide."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('guides/pacing.html', wedding=wedding)


@app.route('/wedding/<int:wedding_id>/print/pacing-guide')
@login_required
def print_pacing_guide(wedding_id):
    """Printable pacing guide."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/pacing_guide.html', f'pacing_guide_{wedding_id}.pdf',
                          wedding=wedding)


@app.route('/wedding/<int:wedding_id>/guides/hosting')
@login_required
def hosting_guide_view(wedding_id):
    """Hosting & Thank-You Etiquette guide."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('guides/hosting.html', wedding=wedding)


@app.route('/wedding/<int:wedding_id>/print/hosting-guide')
@login_required
def print_hosting_guide(wedding_id):
    """Printable hosting guide."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/hosting_guide.html', f'hosting_guide_{wedding_id}.pdf',
                          wedding=wedding)


@app.route('/wedding/<int:wedding_id>/guides/vendor-tipping')
@login_required
def vendor_tipping_guide_view(wedding_id):
    """Vendor Etiquette & Tipping guide."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('guides/vendor_tipping.html', wedding=wedding)


@app.route('/wedding/<int:wedding_id>/print/vendor-tipping-guide')
@login_required
def print_vendor_tipping_guide(wedding_id):
    """Printable vendor tipping guide."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/vendor_tipping_guide.html', f'vendor_tipping_guide_{wedding_id}.pdf',
                          wedding=wedding)


@app.route('/wedding/<int:wedding_id>/guides/speeches')
@login_required
def speeches_guide_view(wedding_id):
    """Speech & Toast guide."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('guides/speeches.html', wedding=wedding)


@app.route('/wedding/<int:wedding_id>/print/speeches-guide')
@login_required
def print_speeches_guide(wedding_id):
    """Printable speeches guide."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/speeches_guide.html', f'speeches_guide_{wedding_id}.pdf',
                          wedding=wedding)


@app.route('/wedding/<int:wedding_id>/guides/wedding-party')
@login_required
def wedding_party_guide_view(wedding_id):
    """Wedding Party Responsibilities guide."""
    wedding = get_wedding_or_403(wedding_id)
    return render_template('guides/wedding_party.html', wedding=wedding)


@app.route('/wedding/<int:wedding_id>/print/wedding-party-guide')
@login_required
def print_wedding_party_guide(wedding_id):
    """Printable wedding party guide."""
    wedding = get_wedding_or_403(wedding_id)
    return _render_or_pdf('print/wedding_party_guide.html', f'wedding_party_guide_{wedding_id}.pdf',
                          wedding=wedding)


# Start reminder thread:
# - Under gunicorn: __name__ != '__main__', start immediately
# - Under `python app.py` with debug/reloader: only in the reloader child process
if __name__ != '__main__':
    start_reminder_thread()

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_reminder_thread()
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=4345, debug=debug_mode)
