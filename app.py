from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from models import *
from datetime import datetime, timedelta, time
import os
from email_service import send_reminder_email
import threading
import time as time_module
import json

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
# MAIN ROUTES
# ============================================

@app.route('/')
def index():
    weddings = Wedding.query.order_by(Wedding.wedding_date).all()
    return render_template('index.html', weddings=weddings)

@app.route('/wedding/new', methods=['GET', 'POST'])
def new_wedding():
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
        
        flash(f'Wedding created! Let\'s set up some details.', 'success')
        return redirect(url_for('onboarding_step1', wedding_id=wedding.id))
    
    return render_template('new_wedding.html')

# ============================================
# ONBOARDING FLOW
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/step1', methods=['GET', 'POST'])
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
def onboarding_hub(wedding_id):
    """Central hub for module-by-module onboarding"""
    wedding = Wedding.query.get_or_404(wedding_id)
    modules_completed = json.loads(wedding.modules_completed or '[]')
    return render_template('onboarding/hub.html', wedding=wedding, modules_completed=modules_completed)

# ============================================
# CEREMONY ONBOARDING
# ============================================

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/start', methods=['GET', 'POST'])
def onboarding_ceremony_start(wedding_id):
    """Ceremony onboarding - choose ceremony type"""
    wedding = Wedding.query.get_or_404(wedding_id)
    return render_template('onboarding/modules/ceremony_start.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/templates', methods=['GET', 'POST'])
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
def onboarding_ceremony_custom(wedding_id):
    """Start custom ceremony setup with questions"""
    wedding = Wedding.query.get_or_404(wedding_id)
    return render_template('onboarding/modules/ceremony_custom_start.html', wedding=wedding)

@app.route('/wedding/<int:wedding_id>/onboarding/ceremony/customize', methods=['GET', 'POST'])
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
def onboarding_reception_start(wedding_id):
    flash('Reception onboarding coming soon!', 'info')
    return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>/onboarding/budget/start')
def onboarding_budget_start(wedding_id):
    flash('Budget onboarding coming soon!', 'info')
    return redirect(url_for('onboarding_hub', wedding_id=wedding_id))

@app.route('/wedding/<int:wedding_id>')
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
    
    # Budget summary
    if wedding.budget:
        total_spent = sum([e.paid_amount or 0 for e in wedding.budget.expenses])
        stats['budget_total'] = wedding.budget.total_budget
        stats['budget_spent'] = total_spent
    else:
        stats['budget_total'] = 0
        stats['budget_spent'] = 0
    
    return render_template('wedding_dashboard.html', wedding=wedding, stats=stats)

@app.route('/wedding/<int:wedding_id>/delete', methods=['POST'])
def delete_wedding(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    db.session.delete(wedding)
    db.session.commit()
    flash('Wedding deleted successfully!', 'success')
    return redirect(url_for('index'))

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
# CEREMONY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/ceremony')
def ceremony_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    ceremony = wedding.ceremony
    timeline_items = sorted(ceremony.timeline_items, key=lambda x: x.order) if ceremony else []
    readings = sorted(ceremony.readings, key=lambda x: x.order or 999) if ceremony else []
    return render_template('ceremony/view.html', wedding=wedding, ceremony=ceremony,
                         timeline_items=timeline_items, readings=readings)

@app.route('/wedding/<int:wedding_id>/ceremony/edit', methods=['GET', 'POST'])
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
def reception_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    reception = wedding.reception
    timeline_items = sorted(reception.timeline_items, key=lambda x: x.order) if reception else []
    menu_items = reception.menu_items if reception else []
    tables = reception.seating_tables if reception else []
    return render_template('reception/view.html', wedding=wedding, reception=reception,
                         timeline_items=timeline_items, menu_items=menu_items, tables=tables)

@app.route('/wedding/<int:wedding_id>/reception/edit', methods=['GET', 'POST'])
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

# ============================================
# BRIDAL PARTY ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/bridal-party')
def bridal_party_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    bride_side = [m for m in wedding.bridal_party if m.side == 'bride']
    groom_side = [m for m in wedding.bridal_party if m.side == 'groom']
    return render_template('bridal_party/view.html', wedding=wedding, 
                         bride_side=bride_side, groom_side=groom_side)

@app.route('/wedding/<int:wedding_id>/bridal-party/add', methods=['GET', 'POST'])
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
        flash('Bridal party member added!', 'success')
        return redirect(url_for('bridal_party_view', wedding_id=wedding_id))
    return render_template('bridal_party/add.html', wedding=wedding)

# ============================================
# BUDGET ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/budget')
def budget_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    budget = wedding.budget
    expenses = budget.expenses if budget else []
    
    # Calculate totals
    total_estimated = sum([e.estimated_cost or 0 for e in expenses])
    total_actual = sum([e.actual_cost or 0 for e in expenses])
    total_paid = sum([e.paid_amount or 0 for e in expenses])
    
    stats = {
        'budget_total': budget.total_budget if budget else 0,
        'estimated': total_estimated,
        'actual': total_actual,
        'paid': total_paid,
        'remaining': (budget.total_budget if budget else 0) - total_paid
    }
    
    return render_template('budget/view.html', wedding=wedding, budget=budget, 
                         expenses=expenses, stats=stats)

@app.route('/wedding/<int:wedding_id>/budget/expense/add', methods=['POST'])
def budget_expense_add(wedding_id):
    budget = Wedding.query.get_or_404(wedding_id).budget
    expense = BudgetExpense(
        budget_id=budget.id,
        category=request.form.get('category'),
        item_name=request.form.get('item_name'),
        estimated_cost=request.form.get('estimated_cost', type=float),
        payment_status=request.form.get('payment_status', 'unpaid')
    )
    db.session.add(expense)
    db.session.commit()
    flash('Expense added!', 'success')
    return redirect(url_for('budget_view', wedding_id=wedding_id))

# ============================================
# VENDORS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/vendors')
def vendors_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    vendors = wedding.vendors
    return render_template('vendors/view.html', wedding=wedding, vendors=vendors)

@app.route('/wedding/<int:wedding_id>/vendors/add', methods=['GET', 'POST'])
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
            total_cost=request.form.get('total_cost', type=float)
        )
        db.session.add(vendor)
        db.session.commit()
        flash('Vendor added!', 'success')
        return redirect(url_for('vendors_view', wedding_id=wedding_id))
    return render_template('vendors/add.html', wedding=wedding)

# ============================================
# TASKS ROUTES
# ============================================

@app.route('/wedding/<int:wedding_id>/tasks')
def tasks_view(wedding_id):
    wedding = Wedding.query.get_or_404(wedding_id)
    pending = [t for t in wedding.tasks if not t.completed]
    completed = [t for t in wedding.tasks if t.completed]
    return render_template('tasks/view.html', wedding=wedding, 
                         pending_tasks=pending, completed_tasks=completed)

@app.route('/wedding/<int:wedding_id>/tasks/add', methods=['GET', 'POST'])
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

@app.route('/task/<int:task_id>/toggle')
def task_toggle(task_id):
    task = Task.query.get_or_404(task_id)
    task.completed = not task.completed
    db.session.commit()
    flash(f'Task {"completed" if task.completed else "reopened"}!', 'success')
    return redirect(url_for('tasks_view', wedding_id=task.wedding_id))

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

reminder_thread = threading.Thread(target=check_reminders, daemon=True)
reminder_thread.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
