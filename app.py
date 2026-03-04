from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from models import (
    db, Wedding, Person, Task, Ceremony, CeremonyTimelineItem, CeremonyReading,
    Reception, ReceptionTimelineItem, MenuItem, SeatingTable,
    Honeymoon, HoneymoonItinerary, PackingItem,
    WeddingBranding, BridalPartyMember, Guest,
    Budget, BudgetExpense, Vendor, RegistryItem, Attire, TraditionalElement,
    User, WeddingAccess,
    DayOfTimelineItem, PhotoShot, Song, FloralItem, Invitation,
    RehearsalDinner, Accommodation, MarriageLicense, HairMakeup,
    WeddingParticipant, timeline_assignments
)
from datetime import datetime, timedelta
import os
from email_service import send_reminder_email
import threading
import time as time_module
import json
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

# Placeholder routes for other modules (to be built out)
@app.route('/wedding/<int:wedding_id>/onboarding/reception/start')
@login_required
def onboarding_reception_start(wedding_id):
    flash('Reception onboarding coming soon!', 'info')
    return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/onboarding/budget/start')
@login_required
def onboarding_budget_start(wedding_id):
    flash('Budget onboarding coming soon!', 'info')
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
    
    return render_template('wedding_dashboard.html', wedding=wedding, stats=stats)

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
        reception.music_type = request.form.get('music_type')
        reception.first_dance_song = request.form.get('first_dance_song')
        reception.theme = request.form.get('theme')
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
            dietary_restrictions=request.form.get('dietary_restrictions')
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

    return render_template('budget/view.html', wedding=wedding, budget=budget,
                         expenses=expenses, stats=stats, module_costs=module_costs)

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
        if request.form.get('final_payment_date'):
            vendor.final_payment_date = datetime.strptime(request.form.get('final_payment_date'), '%Y-%m-%d').date()
        if request.form.get('service_date'):
            vendor.service_date = datetime.strptime(request.form.get('service_date'), '%Y-%m-%d').date()
        if request.form.get('service_time'):
            vendor.service_time = datetime.strptime(request.form.get('service_time'), '%H:%M').time()
        vendor.service_location = request.form.get('service_location')
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
            category=request.form.get('category')
        )
        db.session.add(task)
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
