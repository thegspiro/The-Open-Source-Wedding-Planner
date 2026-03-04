from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g, Response, make_response
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
    BUDGET_TEMPLATES, POST_WEDDING_TASKS, INVITATION_WORDING_TEMPLATES,
    TABLE_SIZE_REFERENCE, TABLE_ROLES, SUGGESTED_GROUP_TYPES
)
import random
from datetime import datetime, timedelta, date
import os
import csv
import io
import secrets
from email_service import send_reminder_email
import threading
import time as time_module
import json
import math
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wedding_organizer.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize database and seed traditional elements
with app.app_context():
    db.create_all()
    
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


@app.context_processor
def inject_user():
    return dict(current_user=g.get('user'))


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
    """Get a wedding, checking that the current user has access."""
    wedding = Wedding.query.get_or_404(wedding_id)
    user = g.user
    if user:
        access = WeddingAccess.query.filter_by(user_id=user.id, wedding_id=wedding_id).first()
        if not access:
            flash('You do not have access to this wedding.', 'error')
            return None
    return wedding


# ============================================
# AUTH ROUTES
# ============================================

@app.route('/register', methods=['GET', 'POST'])
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
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters.')
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
# MAIN ROUTES
# ============================================

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
        couple_names = request.form['couple_names']
        wedding_date = datetime.strptime(request.form['wedding_date'], '%Y-%m-%d')
        email = request.form['email']

        wedding = Wedding(
            couple_names=couple_names,
            wedding_date=wedding_date,
            email=email,
            onboarding_completed=False
        )
        db.session.add(wedding)
        db.session.commit()

        # Give the current user owner access
        access = WeddingAccess(user_id=user.id, wedding_id=wedding.id, role='owner')
        db.session.add(access)
        db.session.commit()

        flash(f'Wedding created! Let\'s set up some details.', 'success')
        return redirect(url_for('onboarding_step1', wedding_id=wedding.id))

    return render_template('new_wedding.html')

# ============================================
# ONBOARDING FLOW
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/step1', methods=['GET', 'POST'])
@login_required
def onboarding_step1(wedding_id):
    """Step 1: How many people are getting married?"""
    wedding = Wedding.query.get_or_404(wedding_id)
    
    if request.method == 'POST':
        num_people = int(request.form.get('num_people', 2))
        # Store in session for next step
        
        session['onboarding_num_people'] = num_people
        return redirect(url_for('onboarding_step2', wedding_id=wedding_id))
    
    return render_template('onboarding/step1.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/step2', methods=['GET', 'POST'])
@login_required
def onboarding_step2(wedding_id):
    """Step 2: Collect information about each person"""
    wedding = Wedding.query.get_or_404(wedding_id)
    
    num_people = session.get('onboarding_num_people', 2)
    
    if request.method == 'POST':
        # Create Person records for each individual
        for i in range(num_people):
            name = request.form.get(f'person_{i}_name')
            title = request.form.get(f'person_{i}_title')
            pronouns = request.form.get(f'person_{i}_pronouns')
            side_label = request.form.get(f'person_{i}_side_label')
            
            if name:  # Only create if name provided
                person = Person(
                    wedding_id=wedding_id,
                    name=name,
                    title=title if title != 'other' else request.form.get(f'person_{i}_title_custom'),
                    preferred_pronouns=pronouns,
                    side_label=side_label,
                    display_order=i+1
                )
                db.session.add(person)
        
        db.session.commit()
        
        # Mark people module as complete
        modules = json.loads(wedding.modules_completed or '[]')
        if 'people' not in modules:
            modules.append('people')
            wedding.modules_completed = json.dumps(modules)
            db.session.commit()
        
        return redirect(url_for('onboarding_step3', wedding_id=wedding_id))
    
    return render_template('onboarding/step2.html', wedding=wedding, num_people=num_people)

@app.route('/wedding/<int:wedding_id>/onboarding/step3', methods=['GET', 'POST'])
@login_required
def onboarding_step3(wedding_id):
    """Step 3: Customize terminology and preferences"""
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    modules_completed = json.loads(wedding.modules_completed or '[]')
    return render_template('onboarding/hub.html', wedding=wedding, modules_completed=modules_completed)

# ============================================
# CEREMONY ONBOARDING
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/start', methods=['GET', 'POST'])
@login_required
def onboarding_ceremony_start(wedding_id):
    """Ceremony onboarding - choose ceremony type"""
    wedding = Wedding.query.get_or_404(wedding_id)
    return render_template('onboarding/modules/ceremony_start.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/templates', methods=['GET', 'POST'])
@login_required
def onboarding_ceremony_templates(wedding_id):
    """Show ceremony templates based on type selected"""
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    return render_template('onboarding/modules/ceremony_custom_start.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/customize', methods=['GET', 'POST'])
@login_required
def onboarding_ceremony_customize(wedding_id):
    """Customize ceremony details after template or custom setup"""
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)

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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    wedding.modules_completed = json.dumps([])
    db.session.commit()
    flash('Onboarding progress has been reset. You can set up modules again.', 'info')
    return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>')
@login_required
def wedding_dashboard(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    
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
    wedding = Wedding.query.get_or_404(wedding_id)
    db.session.delete(wedding)
    db.session.commit()
    flash('Wedding deleted successfully!', 'success')
    return redirect(url_for('index'))

# More Modules Page
@app.route('/wedding/<int:wedding_id>/more')
@login_required
def more_modules(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    
    return render_template('traditional_elements.html', grouped_elements=grouped)

# ============================================
# PEOPLE ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/people')
@login_required
def people_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    people = Person.query.filter_by(wedding_id=wedding_id).order_by(Person.display_order).all()
    return render_template('people/view.html', wedding=wedding, people=people)

@app.route('/wedding/<int:wedding_id>/people/<int:person_id>/edit', methods=['GET', 'POST'])
@login_required
def person_edit(wedding_id, person_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    person = Person.query.get_or_404(person_id)

    if request.method == 'POST':
        person.name = request.form.get('name')
        person.title = request.form.get('title')
        person.preferred_pronouns = request.form.get('preferred_pronouns')
        person.side_label = request.form.get('side_label')
        person.email = request.form.get('email')
        person.phone = request.form.get('phone')
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
    wedding = Wedding.query.get_or_404(wedding_id)
    ceremony = wedding.ceremony
    timeline_items = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony else []
    readings = sorted(ceremony.readings, key=lambda x: x.order or 999) if ceremony else []
    return render_template('ceremony/view.html', wedding=wedding, ceremony=ceremony,
                         timeline_items=timeline_items, readings=readings)

@app.route('/wedding/<int:wedding_id>/ceremony/edit', methods=['GET', 'POST'])
@login_required
def ceremony_edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
        db.session.commit()
        flash('Ceremony details updated!', 'success')
        return redirect(url_for('ceremony_view', wedding_id=wedding_id))
    return render_template('ceremony/edit.html', wedding=wedding, ceremony=ceremony)

@app.route('/wedding/<int:wedding_id>/ceremony/timeline/add', methods=['POST'])
@login_required
def ceremony_timeline_add(wedding_id):
    ceremony = Wedding.query.get_or_404(wedding_id).ceremony
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

# ============================================
# RECEPTION ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/reception')
@login_required
def reception_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    reception = wedding.reception
    timeline_items = sorted(reception.timeline_items, key=lambda x: x.order) if reception else []
    menu_items = reception.menu_items if reception else []
    tables = reception.seating_tables if reception else []
    return render_template('reception/view.html', wedding=wedding, reception=reception,
                         timeline_items=timeline_items, menu_items=menu_items, tables=tables)

@app.route('/wedding/<int:wedding_id>/reception/edit', methods=['GET', 'POST'])
@login_required
def reception_edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    if request.method == 'POST':
        guest = Guest(
            wedding_id=wedding_id,
            name=request.form.get('name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            address=request.form.get('address'),
            guest_type=request.form.get('guest_type'),
            side=request.form.get('side'),
            dietary_restrictions=request.form.get('dietary_restrictions'),
            household_group=request.form.get('household_group'),
            social_groups=request.form.get('social_groups')
        )
        db.session.add(guest)
        db.session.commit()
        flash('Guest added!', 'success')
        return redirect(url_for('guests_view', wedding_id=wedding_id))
    return render_template('guests/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/guests/<int:guest_id>/edit', methods=['GET', 'POST'])
@login_required
def guest_edit(wedding_id, guest_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    guest = Guest.query.get_or_404(guest_id)
    if request.method == 'POST':
        guest.name = request.form.get('name')
        guest.email = request.form.get('email')
        guest.phone = request.form.get('phone')
        guest.address = request.form.get('address')
        guest.guest_type = request.form.get('guest_type')
        guest.side = request.form.get('side')
        guest.dietary_restrictions = request.form.get('dietary_restrictions')
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
        db.session.commit()
        flash('Guest updated!', 'success')
        return redirect(url_for('guests_view', wedding_id=wedding_id))
    return render_template('guests/edit.html', wedding=wedding, guest=guest)

@app.route('/wedding/<int:wedding_id>/guests/<int:guest_id>/delete', methods=['POST'])
@login_required
def guest_delete(wedding_id, guest_id):
    guest = Guest.query.get_or_404(guest_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    members = wedding.bridal_party
    return render_template('bridal_party/view.html', wedding=wedding, members=members)

@app.route('/wedding/<int:wedding_id>/bridal-party/add', methods=['GET', 'POST'])
@login_required
def bridal_party_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    if request.method == 'POST':
        member = BridalPartyMember(
            wedding_id=wedding_id,
            name=request.form.get('name'),
            role=request.form.get('role'),
            side=request.form.get('side'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            processional_order=request.form.get('processional_order', type=int)
        )
        db.session.add(member)
        db.session.commit()
        flash('Wedding party member added!', 'success')
        return redirect(url_for('bridal_party_view', wedding_id=wedding_id))
    return render_template('bridal_party/add.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/bridal-party/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
def bridal_party_edit(wedding_id, member_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    member = BridalPartyMember.query.get_or_404(member_id)
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
        db.session.commit()
        flash('Wedding party member updated!', 'success')
        return redirect(url_for('bridal_party_view', wedding_id=wedding_id))
    return render_template('bridal_party/edit.html', wedding=wedding, member=member)

@app.route('/wedding/<int:wedding_id>/bridal-party/<int:member_id>/delete', methods=['POST'])
@login_required
def bridal_party_delete(wedding_id, member_id):
    member = BridalPartyMember.query.get_or_404(member_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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

    return render_template('budget/view.html', wedding=wedding, budget=budget,
                         expenses=expenses, stats=stats, module_costs=module_costs,
                         category_limits=category_limits, category_spending=category_spending,
                         limit_warnings=limit_warnings)

@app.route('/wedding/<int:wedding_id>/budget/update', methods=['POST'])
@login_required
def budget_update(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    expense = BudgetExpense.query.get_or_404(expense_id)
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
    expense = BudgetExpense.query.get_or_404(expense_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    vendors = wedding.vendors
    return render_template('vendors/view.html', wedding=wedding, vendors=vendors)

@app.route('/wedding/<int:wedding_id>/vendors/add', methods=['GET', 'POST'])
@login_required
def vendor_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    vendor = Vendor.query.get_or_404(vendor_id)
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
        vendor.backup_phone = request.form.get('backup_phone')
        if request.form.get('final_payment_date'):
            vendor.final_payment_date = datetime.strptime(request.form.get('final_payment_date'), '%Y-%m-%d').date()
        if request.form.get('service_date'):
            vendor.service_date = datetime.strptime(request.form.get('service_date'), '%Y-%m-%d').date()
        if request.form.get('service_time'):
            vendor.service_time = datetime.strptime(request.form.get('service_time'), '%H:%M').time()
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
    vendor = Vendor.query.get_or_404(vendor_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    pending = [t for t in wedding.tasks if not t.completed]
    completed = [t for t in wedding.tasks if t.completed]
    return render_template('tasks/view.html', wedding=wedding,
                         pending_tasks=pending, completed_tasks=completed)

@app.route('/wedding/<int:wedding_id>/tasks/add', methods=['GET', 'POST'])
@login_required
def task_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    if request.method == 'POST':
        task = Task(
            wedding_id=wedding_id,
            title=request.form.get('title'),
            description=request.form.get('description'),
            due_date=datetime.strptime(request.form.get('due_date'), '%Y-%m-%d'),
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
    wedding = Wedding.query.get_or_404(wedding_id)
    task = Task.query.get_or_404(task_id)
    if request.method == 'POST':
        task.title = request.form.get('title')
        task.description = request.form.get('description')
        task.due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d')
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
    task = Task.query.get_or_404(task_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    items = wedding.registry_items
    return render_template('registry/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/registry/add', methods=['GET', 'POST'])
@login_required
def registry_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    item = RegistryItem.query.get_or_404(item_id)
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
    item = RegistryItem.query.get_or_404(item_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    items = wedding.attire
    return render_template('attire/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/attire/add', methods=['GET', 'POST'])
@login_required
def attire_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    item = Attire.query.get_or_404(item_id)
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
    item = Attire.query.get_or_404(item_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    honeymoon = wedding.honeymoon
    itinerary = sorted(honeymoon.itinerary_items, key=lambda x: x.day_number) if honeymoon else []
    packing = honeymoon.packing_items if honeymoon else []
    return render_template('honeymoon/view.html', wedding=wedding, honeymoon=honeymoon,
                         itinerary=itinerary, packing=packing)

@app.route('/wedding/<int:wedding_id>/honeymoon/edit', methods=['GET', 'POST'])
@login_required
def honeymoon_edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    honeymoon = Wedding.query.get_or_404(wedding_id).honeymoon
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
    wedding = Wedding.query.get_or_404(wedding_id)
    branding = wedding.branding
    return render_template('branding/view.html', wedding=wedding, branding=branding)

@app.route('/wedding/<int:wedding_id>/branding/edit', methods=['GET', 'POST'])
@login_required
def branding_edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    reception = Wedding.query.get_or_404(wedding_id).reception
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
    reception = Wedding.query.get_or_404(wedding_id).reception
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
    reception = Wedding.query.get_or_404(wedding_id).reception
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
    table = SeatingTable.query.get_or_404(table_id)
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
    ceremony = Wedding.query.get_or_404(wedding_id).ceremony
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
    person = Person.query.get_or_404(person_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    participants = wedding.participants
    return render_template('day_of/view.html', wedding=wedding, items=items, participants=participants)

@app.route('/wedding/<int:wedding_id>/day-of/add', methods=['GET', 'POST'])
@login_required
def day_of_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    item = DayOfTimelineItem.query.get_or_404(item_id)
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
    item = DayOfTimelineItem.query.get_or_404(item_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    if request.method == 'POST':
        participant = WeddingParticipant(
            wedding_id=wedding_id,
            name=request.form.get('name'),
            role=request.form.get('role'),
            role_category=request.form.get('role_category'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            notes=request.form.get('notes')
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
    wedding = Wedding.query.get_or_404(wedding_id)
    participant = WeddingParticipant.query.get_or_404(participant_id)
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
        db.session.commit()
        flash('Participant updated!', 'success')
        return redirect(url_for('itinerary_participants', wedding_id=wedding_id))
    return render_template('itinerary/edit_participant.html', wedding=wedding,
                           participant=participant, people=wedding.people,
                           bridal_party=wedding.bridal_party)

@app.route('/wedding/<int:wedding_id>/itinerary/participant/<int:participant_id>/delete', methods=['POST'])
@login_required
def itinerary_delete_participant(wedding_id, participant_id):
    participant = WeddingParticipant.query.get_or_404(participant_id)
    db.session.delete(participant)
    db.session.commit()
    flash('Participant removed.', 'success')
    return redirect(url_for('itinerary_participants', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/itinerary/participant/<int:participant_id>')
@login_required
def itinerary_individual(wedding_id, participant_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    participant = WeddingParticipant.query.get_or_404(participant_id)
    # Get this person's timeline items, sorted by time
    items = sorted(participant.timeline_items,
                   key=lambda x: (x.order, x.time or datetime.min.time()))
    return render_template('itinerary/individual.html', wedding=wedding,
                           participant=participant, items=items)

@app.route('/wedding/<int:wedding_id>/itinerary/handler-view')
@login_required
def itinerary_handler_view(wedding_id):
    """Handler view showing all participants and where they should be at each time."""
    wedding = Wedding.query.get_or_404(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    participants = wedding.participants
    return render_template('itinerary/handler_view.html', wedding=wedding,
                           items=items, participants=participants)

@app.route('/wedding/<int:wedding_id>/itinerary/import-people', methods=['POST'])
@login_required
def itinerary_import_people(wedding_id):
    """Quickly import people and bridal party members as participants."""
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    shots = wedding.photo_shots
    return render_template('photos/view.html', wedding=wedding, shots=shots)

@app.route('/wedding/<int:wedding_id>/photos/add', methods=['GET', 'POST'])
@login_required
def photos_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    shot = PhotoShot.query.get_or_404(shot_id)
    db.session.delete(shot)
    db.session.commit()
    flash('Shot removed.', 'success')
    return redirect(url_for('photos_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/photos/<int:shot_id>/toggle', methods=['POST'])
@login_required
def photos_toggle(wedding_id, shot_id):
    shot = PhotoShot.query.get_or_404(shot_id)
    shot.captured = not shot.captured
    db.session.commit()
    return redirect(url_for('photos_view', wedding_id=wedding_id))

# ============================================
# MUSIC & PLAYLIST ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/music')
@login_required
def music_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    songs = wedding.songs
    return render_template('music/view.html', wedding=wedding, songs=songs)

@app.route('/wedding/<int:wedding_id>/music/add', methods=['GET', 'POST'])
@login_required
def music_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    song = Song.query.get_or_404(song_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    items = wedding.floral_items
    return render_template('flowers/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/flowers/add', methods=['GET', 'POST'])
@login_required
def flowers_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    item = FloralItem.query.get_or_404(item_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    items = wedding.invitations
    return render_template('invitations/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/invitations/add', methods=['GET', 'POST'])
@login_required
def invitations_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    item = Invitation.query.get_or_404(item_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    rehearsal = wedding.rehearsal_dinner
    return render_template('rehearsal/view.html', wedding=wedding, rehearsal=rehearsal)

@app.route('/wedding/<int:wedding_id>/rehearsal/edit', methods=['GET', 'POST'])
@login_required
def rehearsal_edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    items = wedding.accommodations
    return render_template('accommodations/view.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/accommodations/add', methods=['GET', 'POST'])
@login_required
def accommodations_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    item = Accommodation.query.get_or_404(item_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    license_info = wedding.marriage_license
    return render_template('license/view.html', wedding=wedding, license_info=license_info)

@app.route('/wedding/<int:wedding_id>/license/edit', methods=['GET', 'POST'])
@login_required
def license_edit(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    appointments = wedding.hair_makeup
    return render_template('hair_makeup/view.html', wedding=wedding, appointments=appointments)

@app.route('/wedding/<int:wedding_id>/hair-makeup/add', methods=['GET', 'POST'])
@login_required
def hair_makeup_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    appt = HairMakeup.query.get_or_404(appt_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    plans = wedding.contingency_plans
    return render_template('contingency/view.html', wedding=wedding, plans=plans)

@app.route('/wedding/<int:wedding_id>/contingency/add', methods=['GET', 'POST'])
@login_required
def contingency_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    plan = ContingencyPlan.query.get_or_404(plan_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    limit = BudgetCategoryLimit.query.get_or_404(limit_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    tip = TipItem.query.get_or_404(tip_id)
    tip.envelope_prepared = not tip.envelope_prepared
    db.session.commit()
    return redirect(url_for('tips_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/tips/<int:tip_id>/toggle-given', methods=['POST'])
@login_required
def tips_toggle_given(wedding_id, tip_id):
    tip = TipItem.query.get_or_404(tip_id)
    tip.given = not tip.given
    db.session.commit()
    return redirect(url_for('tips_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/tips/<int:tip_id>/delete', methods=['POST'])
@login_required
def tips_delete(wedding_id, tip_id):
    tip = TipItem.query.get_or_404(tip_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    gift = Gift.query.get_or_404(gift_id)
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
    gift = Gift.query.get_or_404(gift_id)
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
    return render_template('rsvp/portal.html', wedding=wedding, guests=guests,
                         menu_items=menu_items, token=token)

@app.route('/rsvp/<token>/submit', methods=['POST'])
def rsvp_submit(token):
    """Process RSVP submission from public portal."""
    wedding = Wedding.query.filter_by(rsvp_token=token).first_or_404()
    guest_name = request.form.get('guest_name', '').strip()
    rsvp_status = request.form.get('rsvp_status')
    meal_choice = request.form.get('meal_choice')
    dietary = request.form.get('dietary_restrictions', '').strip()
    rsvp_notes = request.form.get('rsvp_notes', '').strip()
    plus_one_name = request.form.get('plus_one_name', '').strip()

    guest = Guest.query.filter_by(wedding_id=wedding.id, name=guest_name).first()
    if not guest:
        # Allow new guests to RSVP (they type their name)
        guest = Guest(wedding_id=wedding.id, name=guest_name)
        db.session.add(guest)

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
                       plus_one_of=guest_name, rsvp_status='accepted')
            db.session.add(po)

    db.session.commit()
    return render_template('rsvp/thank_you.html', wedding=wedding, guest=guest, token=token)

@app.route('/wedding/<int:wedding_id>/rsvp/enable', methods=['POST'])
@login_required
def rsvp_enable(wedding_id):
    """Enable/disable RSVP portal and generate token."""
    wedding = Wedding.query.get_or_404(wedding_id)
    wedding.rsvp_enabled = not wedding.rsvp_enabled
    if wedding.rsvp_enabled and not wedding.rsvp_token:
        wedding.rsvp_token = generate_token()
    if request.form.get('rsvp_deadline'):
        wedding.rsvp_deadline = datetime.strptime(request.form.get('rsvp_deadline'), '%Y-%m-%d').date()
    if request.form.get('rsvp_message'):
        wedding.rsvp_message = request.form.get('rsvp_message')
    db.session.commit()
    status = 'enabled' if wedding.rsvp_enabled else 'disabled'
    flash(f'RSVP portal {status}!', 'success')
    return redirect(url_for('guests_view', wedding_id=wedding_id))

# ============================================
# GUEST MEAL COUNT SUMMARY
# ============================================

@app.route('/wedding/<int:wedding_id>/guests/meal-summary')
@login_required
def guest_meal_summary(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    vendor = Vendor.query.get_or_404(vendor_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    quotes = VendorQuote.query.filter_by(wedding_id=wedding_id).order_by(VendorQuote.category).all()
    # Group by category
    grouped = {}
    for q in quotes:
        grouped.setdefault(q.category, []).append(q)
    return render_template('vendors/quotes.html', wedding=wedding, grouped_quotes=grouped)

@app.route('/wedding/<int:wedding_id>/vendor-quotes/add', methods=['GET', 'POST'])
@login_required
def vendor_quote_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    speeches = SpeechToast.query.filter_by(wedding_id=wedding_id).order_by(SpeechToast.order).all()
    return render_template('speeches/view.html', wedding=wedding, speeches=speeches)

@app.route('/wedding/<int:wedding_id>/speeches/add', methods=['GET', 'POST'])
@login_required
def speeches_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    speech = SpeechToast.query.get_or_404(speech_id)
    speech.reviewed = not speech.reviewed
    db.session.commit()
    return redirect(url_for('speeches_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/speeches/<int:speech_id>/delete', methods=['POST'])
@login_required
def speeches_delete(wedding_id, speech_id):
    speech = SpeechToast.query.get_or_404(speech_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    favors = WeddingFavor.query.filter_by(wedding_id=wedding_id).all()
    total_cost = sum(f.total_cost or 0 for f in favors)
    assembled_count = sum(1 for f in favors if f.assembled)
    return render_template('favors/view.html', wedding=wedding, favors=favors,
                         total_cost=total_cost, assembled_count=assembled_count)

@app.route('/wedding/<int:wedding_id>/favors/add', methods=['GET', 'POST'])
@login_required
def favors_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    favor = WeddingFavor.query.get_or_404(favor_id)
    favor.assembled = not favor.assembled
    db.session.commit()
    return redirect(url_for('favors_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/favors/<int:favor_id>/delete', methods=['POST'])
@login_required
def favors_delete(wedding_id, favor_id):
    favor = WeddingFavor.query.get_or_404(favor_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    group = GuestGroup.query.get_or_404(group_id)
    name = group.name
    db.session.delete(group)
    db.session.commit()
    flash(f'Group "{name}" deleted.', 'success')
    return redirect(url_for('guest_groups_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/guest-groups/<int:group_id>/assign', methods=['POST'])
@login_required
def guest_group_bulk_assign(wedding_id, group_id):
    """Add a social group tag to multiple guests at once."""
    group = GuestGroup.query.get_or_404(group_id)
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
    group = GuestGroup.query.get_or_404(group_id)
    guest = Guest.query.get_or_404(guest_id)
    if guest.social_groups:
        tags = [t.strip() for t in guest.social_groups.split(',') if t.strip()]
        tags = [t for t in tags if t != group.name]
        guest.social_groups = ', '.join(tags) if tags else None
        db.session.commit()
    flash(f'{guest.name} removed from "{group.name}".', 'success')
    return redirect(url_for('guest_groups_view', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart')
@login_required
def seating_chart(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    reception = wedding.reception
    tables = reception.seating_tables if reception else []
    all_attending = [g for g in wedding.guests if g.rsvp_status == 'accepted']
    unassigned = [g for g in all_attending if not g.table_id]
    preferences = SeatingPreference.query.filter_by(wedding_id=wedding_id).all()

    # Build stats
    total_capacity = sum(t.capacity for t in tables)
    total_attending = len(all_attending)
    total_assigned = total_attending - len(unassigned)

    # Check for constraint violations
    violations = []
    for pref in preferences:
        guest_table = None
        other_table = None
        for g in all_attending:
            if g.id == pref.guest_id:
                guest_table = g.table_id
            if g.id == pref.other_guest_id:
                other_table = g.table_id
        if guest_table and other_table:
            if pref.preference_type == 'together' and guest_table != other_table:
                violations.append(f'{pref.guest.name} and {pref.other_guest.name} should sit together but are at different tables')
            elif pref.preference_type == 'apart' and guest_table == other_table:
                violations.append(f'{pref.guest.name} and {pref.other_guest.name} should sit apart but are at the same table')

    stats = {
        'total_capacity': total_capacity,
        'total_attending': total_attending,
        'total_assigned': total_assigned,
        'total_unassigned': len(unassigned),
        'capacity_surplus': total_capacity - total_attending,
    }

    return render_template('seating/chart.html', wedding=wedding, tables=tables,
                         unassigned_guests=unassigned, preferences=preferences,
                         violations=violations, stats=stats,
                         table_size_ref=TABLE_SIZE_REFERENCE, table_roles=TABLE_ROLES)


@app.route('/wedding/<int:wedding_id>/seating-chart/table/add', methods=['POST'])
@login_required
def seating_table_add(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
        x_position=50 + (existing_count % 4) * 220,
        y_position=50 + (existing_count // 4) * 200,
        notes=request.form.get('notes', '')
    )
    db.session.add(table)
    db.session.commit()
    log_activity(wedding_id, 'added', 'table', f'Table {table_number}')
    flash(f'Table {table_number} added!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/table/<int:table_id>/edit', methods=['POST'])
@login_required
def seating_table_edit(wedding_id, table_id):
    table = SeatingTable.query.get_or_404(table_id)
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
    table = SeatingTable.query.get_or_404(table_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    # Optionally add head table first
    if include_head:
        existing += 1
        head = SeatingTable(
            reception_id=reception.id,
            table_number=str(existing),
            table_name='Head Table',
            capacity=request.form.get('head_capacity', 8, type=int),
            table_shape='rectangular',
            table_size='banquet_8ft',
            table_role='head',
            x_position=350,
            y_position=30,
        )
        db.session.add(head)
        added += 1

    # Add guest tables in a grid layout
    for i in range(count):
        existing += 1
        table = SeatingTable(
            reception_id=reception.id,
            table_number=str(existing),
            table_name=f'{ref["label"]}',
            capacity=ref['capacity'],
            table_shape=ref['shape'],
            table_size=preset,
            table_role='guest',
            x_position=50 + (i % 4) * 220,
            y_position=180 + (i // 4) * 200,
        )
        db.session.add(table)
        added += 1

    # Optionally add kids table
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
            x_position=50 + (count % 4) * 220,
            y_position=180 + (count // 4) * 200,
        )
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
    guest = Guest.query.get_or_404(guest_id)
    guest.table_id = table_id if table_id else None
    db.session.commit()
    flash(f'{guest.name} assigned!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/unassign/<int:guest_id>', methods=['POST'])
@login_required
def seating_unassign(wedding_id, guest_id):
    guest = Guest.query.get_or_404(guest_id)
    guest.table_id = None
    db.session.commit()
    flash(f'{guest.name} unassigned.', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/bulk-assign', methods=['POST'])
@login_required
def seating_bulk_assign(wedding_id):
    table_id = request.form.get('table_id', type=int)
    guest_ids = request.form.getlist('guest_ids')
    for gid in guest_ids:
        guest = Guest.query.get(int(gid))
        if guest:
            guest.table_id = table_id
    db.session.commit()
    flash(f'{len(guest_ids)} guests assigned!', 'success')
    return redirect(url_for('seating_chart', wedding_id=wedding_id))


@app.route('/wedding/<int:wedding_id>/seating-chart/clear-all', methods=['POST'])
@login_required
def seating_clear_all(wedding_id):
    """Remove all guest-to-table assignments."""
    wedding = Wedding.query.get_or_404(wedding_id)
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
    table = SeatingTable.query.get_or_404(table_id)
    table.x_position = x
    table.y_position = y
    db.session.commit()
    return jsonify({'status': 'ok'})


# --- Seating Preferences (together/apart) ---

@app.route('/wedding/<int:wedding_id>/seating-chart/preferences')
@login_required
def seating_preferences(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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

    # Check for duplicate
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
    pref = SeatingPreference.query.get_or_404(pref_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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

    # Load preferences
    prefs = SeatingPreference.query.filter_by(wedding_id=wedding_id).all()
    together_pairs = [(p.guest_id, p.other_guest_id) for p in prefs if p.preference_type == 'together']
    apart_pairs = [(p.guest_id, p.other_guest_id) for p in prefs if p.preference_type == 'apart']

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

    # Merge from "together" preferences
    for a, b in together_pairs:
        if a in guest_ids and b in guest_ids:
            union(a, b)

    # Also merge by household_group
    household_map = {}
    for g in guests_to_assign:
        if g.household_group:
            if g.household_group in household_map:
                union(g.id, household_map[g.household_group])
            else:
                household_map[g.household_group] = g.id

    # Also group plus-ones with their hosts
    name_to_id = {g.name: g.id for g in guests_to_assign}
    for g in guests_to_assign:
        if g.is_plus_one and g.plus_one_of and g.plus_one_of in name_to_id:
            union(g.id, name_to_id[g.plus_one_of])

    # Build actual groups
    from collections import defaultdict
    groups = defaultdict(list)
    for g in guests_to_assign:
        groups[find(g.id)].append(g)

    # Build apart-set (which group roots must not share a table)
    apart_roots = set()
    for a, b in apart_pairs:
        if a in guest_ids and b in guest_ids:
            apart_roots.add((find(a), find(b)))

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

    def group_sort_key(grp):
        """Priority: kids first (for kids table), then family, then friends."""
        types = [g.guest_type for g in grp]
        if any(t == 'child' or t == 'kid' for t in types):
            return (0, -len(grp))
        if any(t == 'family' for t in types):
            return (1, -len(grp))
        if any(t == 'vip' for t in types):
            return (2, -len(grp))
        return (3, -len(grp))

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
        # Check apart constraints
        for assigned_root in table_assignments[table.id]:
            if (group_root, assigned_root) in apart_roots or (assigned_root, group_root) in apart_roots:
                return False
        return True

    def table_affinity(group_root, table):
        """Score how well this group fits at this table based on who's already there."""
        score = 0
        for existing_root in table_assignments[table.id]:
            score += affinity_score(group_root, existing_root)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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

@app.route('/wedding/<int:wedding_id>/print/timeline')
@login_required
def print_timeline(wedding_id):
    """Printable day-of timeline."""
    wedding = Wedding.query.get_or_404(wedding_id)
    items = sorted(wedding.day_of_items, key=lambda x: (x.order, x.time or datetime.min.time()))
    return render_template('print/timeline.html', wedding=wedding, items=items)

@app.route('/wedding/<int:wedding_id>/print/vendor-contacts')
@login_required
def print_vendor_contacts(wedding_id):
    """Printable vendor contact sheet."""
    wedding = Wedding.query.get_or_404(wedding_id)
    return render_template('print/vendor_contacts.html', wedding=wedding, vendors=wedding.vendors)

@app.route('/wedding/<int:wedding_id>/print/shot-list')
@login_required
def print_shot_list(wedding_id):
    """Printable photography shot list."""
    wedding = Wedding.query.get_or_404(wedding_id)
    shots = sorted(wedding.photo_shots, key=lambda x: (x.category or '', x.priority or ''))
    return render_template('print/shot_list.html', wedding=wedding, shots=shots)

@app.route('/wedding/<int:wedding_id>/print/emergency-contacts')
@login_required
def print_emergency_contacts(wedding_id):
    """Printable emergency contact card."""
    wedding = Wedding.query.get_or_404(wedding_id)
    return render_template('print/emergency_contacts.html', wedding=wedding,
                         vendors=wedding.vendors, participants=wedding.participants)

@app.route('/wedding/<int:wedding_id>/print/seating')
@login_required
def print_seating(wedding_id):
    """Printable seating chart."""
    wedding = Wedding.query.get_or_404(wedding_id)
    tables = wedding.reception.seating_tables if wedding.reception else []
    return render_template('print/seating.html', wedding=wedding, tables=tables)

@app.route('/wedding/<int:wedding_id>/export/mailing-labels')
@login_required
def export_mailing_labels(wedding_id):
    """Export guest addresses as CSV for mailing labels."""
    wedding = Wedding.query.get_or_404(wedding_id)
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
# GLOBAL SEARCH
# ============================================

@app.route('/wedding/<int:wedding_id>/search')
@login_required
def global_search(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    comment = Comment.query.get_or_404(comment_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    email = request.form.get('email', '').strip().lower()
    role = request.form.get('role', 'viewer')
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
    access = WeddingAccess.query.get_or_404(access_id)
    access.role = request.form.get('role', 'viewer')
    db.session.commit()
    flash('Role updated!', 'success')
    return redirect(url_for('collaborators_view', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/collaborators/<int:access_id>/remove', methods=['POST'])
@login_required
def collaborator_remove(wedding_id, access_id):
    access = WeddingAccess.query.get_or_404(access_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
    existing = {inv.item_type for inv in wedding.invitations}
    return render_template('invitations/checklist.html', wedding=wedding,
                         checklist=STATIONERY_CHECKLIST, existing=existing)

# ============================================
# PROCESSIONAL ORDER VISUALIZATION
# ============================================

@app.route('/wedding/<int:wedding_id>/bridal-party/processional')
@login_required
def processional_order(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
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
    wedding = Wedding.query.get_or_404(wedding_id)
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
                        print(f"Reminder sent for task: {task.title}")
        
        except Exception as e:
            print(f"Error checking reminders: {e}")
        
        time_module.sleep(3600)  # Check every hour

def start_reminder_thread():
    """Start the background reminder thread (once per process)."""
    reminder_thread = threading.Thread(target=check_reminders, daemon=True)
    reminder_thread.start()

# Start reminder thread:
# - Under gunicorn: __name__ != '__main__', start immediately
# - Under `python app.py` with debug/reloader: only in the reloader child process
if __name__ != '__main__':
    start_reminder_thread()

if __name__ == '__main__':
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_reminder_thread()
    app.run(host='0.0.0.0', port=5000, debug=True)
