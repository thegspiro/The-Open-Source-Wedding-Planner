from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ============================================
# USER & ACCESS MODELS
# ============================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'professional', 'friend', 'self'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    theme = db.Column(db.String(20), default='rose')  # rose, sage, ocean, lavender
    dark_mode = db.Column(db.Boolean, default=False)

    wedding_access = db.relationship('WeddingAccess', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class WeddingAccess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='owner')  # 'owner', 'planner', 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================
# MAIN WEDDING MODEL
# ============================================

class Wedding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    couple_names = db.Column(db.String(200), nullable=False)  # Display name for the wedding
    wedding_date = db.Column(db.DateTime, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Onboarding
    onboarding_completed = db.Column(db.Boolean, default=False)
    onboarding_step = db.Column(db.String(50))  # Current step in onboarding
    onboarding_preferences = db.Column(db.Text)  # JSON storing preferences like ceremony_style, etc.
    modules_completed = db.Column(db.Text)  # JSON array of completed module names

    # RSVP Portal
    rsvp_enabled = db.Column(db.Boolean, default=False)
    rsvp_token = db.Column(db.String(64), unique=True)  # public access token
    rsvp_deadline = db.Column(db.Date)
    rsvp_message = db.Column(db.Text)  # custom message on RSVP page

    # Shareable read-only link
    share_token = db.Column(db.String(64), unique=True)

    # Relationships
    people = db.relationship('Person', backref='wedding', lazy=True, cascade='all, delete-orphan')
    tasks = db.relationship('Task', backref='wedding', lazy=True, cascade='all, delete-orphan')
    ceremony = db.relationship('Ceremony', backref='wedding', uselist=False, cascade='all, delete-orphan')
    reception = db.relationship('Reception', backref='wedding', uselist=False, cascade='all, delete-orphan')
    honeymoon = db.relationship('Honeymoon', backref='wedding', uselist=False, cascade='all, delete-orphan')
    branding = db.relationship('WeddingBranding', backref='wedding', uselist=False, cascade='all, delete-orphan')
    budget = db.relationship('Budget', backref='wedding', uselist=False, cascade='all, delete-orphan')
    bridal_party = db.relationship('BridalPartyMember', backref='wedding', lazy=True, cascade='all, delete-orphan')
    guests = db.relationship('Guest', backref='wedding', lazy=True, cascade='all, delete-orphan')
    vendors = db.relationship('Vendor', backref='wedding', lazy=True, cascade='all, delete-orphan')
    registry_items = db.relationship('RegistryItem', backref='wedding', lazy=True, cascade='all, delete-orphan')
    attire = db.relationship('Attire', backref='wedding', lazy=True, cascade='all, delete-orphan')
    access_list = db.relationship('WeddingAccess', backref='wedding', lazy=True, cascade='all, delete-orphan')

# ============================================
# PERSON MODEL (People Getting Married)
# ============================================

class Person(db.Model):
    """Represents each person getting married - inclusive and flexible"""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    # Basic Information
    name = db.Column(db.String(200), nullable=False)
    title = db.Column(db.String(100))  # bride, groom, partner, spouse, or custom
    preferred_pronouns = db.Column(db.String(50))  # optional: they/them, she/her, he/him, etc.
    
    # Side naming (for organizational purposes)
    side_label = db.Column(db.String(100))  # e.g., "Jamie's side", "Alex's family", etc.
    
    # Contact
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    
    # Order (for display purposes)
    display_order = db.Column(db.Integer, default=1)

# ============================================
# TASK MODEL
# ============================================

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    reminder_sent = db.Column(db.Boolean, default=False)
    priority = db.Column(db.String(20), default='medium')
    category = db.Column(db.String(50))  # ceremony, reception, honeymoon, etc.
    assigned_to = db.Column(db.String(200))  # name of person assigned
    depends_on_id = db.Column(db.Integer, db.ForeignKey('task.id'))  # task dependency
    is_milestone = db.Column(db.Boolean, default=False)
    months_before = db.Column(db.Integer)  # auto-generated milestone: months before wedding
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    depends_on = db.relationship('Task', remote_side='Task.id', backref='dependent_tasks')

# ============================================
# CEREMONY MODULE
# ============================================

class Ceremony(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    # Venue Details
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)
    venue_contact = db.Column(db.String(120))
    venue_phone = db.Column(db.String(50))
    
    # Timing
    ceremony_date = db.Column(db.DateTime)
    start_time = db.Column(db.Time)
    duration_minutes = db.Column(db.Integer)
    
    # Officiant
    officiant_name = db.Column(db.String(200))
    officiant_contact = db.Column(db.String(120))
    officiant_phone = db.Column(db.String(50))
    officiant_type = db.Column(db.String(100))  # religious, civil, friend, etc.
    
    # Ceremony Style
    ceremony_style = db.Column(db.String(100))  # religious, secular, spiritual, cultural
    traditions = db.Column(db.Text)  # JSON or comma-separated list
    
    # Music
    processional_song = db.Column(db.String(200))
    recessional_song = db.Column(db.String(200))
    unity_ceremony_song = db.Column(db.String(200))
    
    # Special Elements
    has_unity_ceremony = db.Column(db.Boolean, default=False)
    unity_ceremony_type = db.Column(db.String(100))  # candle, sand, wine, etc.
    has_special_readings = db.Column(db.Boolean, default=False)
    vow_type = db.Column(db.String(50))  # traditional, custom, mixed

    # Vow Writing Workspace
    vow_draft_person1 = db.Column(db.Text)  # private vow draft
    vow_draft_person2 = db.Column(db.Text)  # private vow draft
    ceremony_script = db.Column(db.Text)  # full ceremony script
    
    # Relationships
    timeline_items = db.relationship('CeremonyTimelineItem', backref='ceremony', lazy=True, cascade='all, delete-orphan')
    readings = db.relationship('CeremonyReading', backref='ceremony', lazy=True, cascade='all, delete-orphan')

class CeremonyTimelineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ceremony_id = db.Column(db.Integer, db.ForeignKey('ceremony.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    duration_seconds = db.Column(db.Integer)  # precise to the second
    description = db.Column(db.Text)
    participants = db.Column(db.Text)  # JSON list of people involved

class CeremonyReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ceremony_id = db.Column(db.Integer, db.ForeignKey('ceremony.id'), nullable=False)
    title = db.Column(db.String(200))
    author = db.Column(db.String(200))
    reader_name = db.Column(db.String(200))
    text_content = db.Column(db.Text)
    order = db.Column(db.Integer)

# ============================================
# RECEPTION MODULE
# ============================================

class Reception(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    # Venue Details
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)
    venue_contact = db.Column(db.String(120))
    venue_phone = db.Column(db.String(50))
    venue_capacity = db.Column(db.Integer)
    
    # Timing
    reception_date = db.Column(db.DateTime)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    
    # Catering
    catering_style = db.Column(db.String(100))  # plated, buffet, family-style, stations
    bar_service = db.Column(db.String(100))  # open, cash, limited, none
    cake_flavor = db.Column(db.String(100))
    cake_design = db.Column(db.Text)
    
    # Entertainment
    music_type = db.Column(db.String(100))  # DJ, band, playlist
    first_dance_song = db.Column(db.String(200))
    parent_dance_songs = db.Column(db.Text)  # JSON
    
    # Decor
    theme = db.Column(db.String(200))
    centerpiece_description = db.Column(db.Text)
    lighting_notes = db.Column(db.Text)
    
    # Cocktail Hour
    cocktail_hour_notes = db.Column(db.Text)
    cocktail_menu = db.Column(db.Text)
    cocktail_entertainment = db.Column(db.Text)

    # Dance Floor & Layout
    dance_floor_size = db.Column(db.String(50))  # calculated or custom size

    # Kids Entertainment
    kids_activities = db.Column(db.Text)
    kids_sitter_name = db.Column(db.String(200))
    kids_sitter_phone = db.Column(db.String(50))

    # Guest Count
    expected_guest_count = db.Column(db.Integer)
    
    # Relationships
    timeline_items = db.relationship('ReceptionTimelineItem', backref='reception', lazy=True, cascade='all, delete-orphan')
    menu_items = db.relationship('MenuItem', backref='reception', lazy=True, cascade='all, delete-orphan')
    seating_tables = db.relationship('SeatingTable', backref='reception', lazy=True, cascade='all, delete-orphan')

class ReceptionTimelineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('reception.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    scheduled_time = db.Column(db.Time)
    duration_seconds = db.Column(db.Integer)
    description = db.Column(db.Text)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('reception.id'), nullable=False)
    course = db.Column(db.String(50))  # appetizer, salad, entree, dessert
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    dietary_tags = db.Column(db.String(200))  # vegetarian, vegan, gluten-free, etc.
    guest_count_selected = db.Column(db.Integer, default=0)

class SeatingTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('reception.id'), nullable=False)
    table_number = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(100))  # custom name (e.g., "Rose Table")
    capacity = db.Column(db.Integer, nullable=False)
    table_shape = db.Column(db.String(50))  # round, rectangular, square, oval, serpentine
    table_size = db.Column(db.String(50))  # e.g., "60in", "72in", "6ft", "8ft"
    table_role = db.Column(db.String(50))  # head, sweetheart, kings, guest, kids, vip
    x_position = db.Column(db.Float, default=0)  # for visual floor plan
    y_position = db.Column(db.Float, default=0)  # for visual floor plan
    notes = db.Column(db.Text)

    # Relationship
    assigned_guests = db.relationship('Guest', backref='seating_table', lazy=True)


class SeatingPreference(db.Model):
    """Tracks which guests should sit together or apart."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    other_guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    preference_type = db.Column(db.String(20), nullable=False)  # 'together' or 'apart'
    priority = db.Column(db.Integer, default=5)  # 1-10, higher = more important
    notes = db.Column(db.String(200))

    guest = db.relationship('Guest', foreign_keys=[guest_id], backref='seating_prefs_as_guest')
    other_guest = db.relationship('Guest', foreign_keys=[other_guest_id], backref='seating_prefs_as_other')


class GuestGroup(db.Model):
    """Named social groups for organizing guests (e.g., Church, Work, College)."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # "Church Group", "Work Friends", etc.
    color = db.Column(db.String(7))  # optional hex color for visual tagging
    seat_together = db.Column(db.Boolean, default=True)  # should algorithm try to seat together?
    priority = db.Column(db.Integer, default=5)  # 1-10 how important is grouping
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('guest_groups', lazy=True, cascade='all, delete-orphan'))


SUGGESTED_GROUP_TYPES = [
    'Church Group', 'Work Colleagues', 'College Friends', 'High School Friends',
    'Neighbors', 'Book Club', 'Sports Team', 'Gym Friends',
    'Parents of Kids\' Friends', 'Extended Family', 'Travel Friends',
    'Volunteering Group', 'Music/Band Friends', 'Online Friends',
]


# Table size reference data (inches)
TABLE_SIZE_REFERENCE = {
    'round_48': {'shape': 'round', 'label': '48" Round', 'capacity': 6, 'diameter': 48},
    'round_60': {'shape': 'round', 'label': '60" Round (5ft)', 'capacity': 8, 'diameter': 60},
    'round_72': {'shape': 'round', 'label': '72" Round (6ft)', 'capacity': 10, 'diameter': 72},
    'round_84': {'shape': 'round', 'label': '84" Round (7ft)', 'capacity': 12, 'diameter': 84},
    'banquet_6ft': {'shape': 'rectangular', 'label': '6ft Banquet', 'capacity': 6, 'length': 72, 'width': 30},
    'banquet_8ft': {'shape': 'rectangular', 'label': '8ft Banquet', 'capacity': 8, 'length': 96, 'width': 30},
    'kings_8ft': {'shape': 'rectangular', 'label': "8ft King's Table", 'capacity': 10, 'length': 96, 'width': 42},
    'square_48': {'shape': 'square', 'label': '48" Square', 'capacity': 4, 'side': 48},
    'sweetheart': {'shape': 'round', 'label': 'Sweetheart (couple)', 'capacity': 2, 'diameter': 36},
}

TABLE_ROLES = {
    'guest': 'Guest Table',
    'head': 'Head Table (traditional)',
    'sweetheart': 'Sweetheart Table (couple only)',
    'kings': "King's Table (couple + party + SOs)",
    'vip': 'VIP / Family Table',
    'kids': 'Kids Table',
}

# ============================================
# HONEYMOON MODULE
# ============================================

class Honeymoon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    destination = db.Column(db.String(200))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    budget = db.Column(db.Float)
    
    # Travel
    flight_confirmation = db.Column(db.String(200))
    airline = db.Column(db.String(100))
    
    # Relationships
    itinerary_items = db.relationship('HoneymoonItinerary', backref='honeymoon', lazy=True, cascade='all, delete-orphan')
    packing_items = db.relationship('PackingItem', backref='honeymoon', lazy=True, cascade='all, delete-orphan')

class HoneymoonItinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    honeymoon_id = db.Column(db.Integer, db.ForeignKey('honeymoon.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date)
    location = db.Column(db.String(200))
    accommodation_name = db.Column(db.String(200))
    accommodation_confirmation = db.Column(db.String(200))
    activities = db.Column(db.Text)
    notes = db.Column(db.Text)

class PackingItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    honeymoon_id = db.Column(db.Integer, db.ForeignKey('honeymoon.id'), nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100))  # clothing, toiletries, documents, etc.
    packed = db.Column(db.Boolean, default=False)

# ============================================
# WEDDING BRANDING MODULE
# ============================================

class WeddingBranding(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    # Colors (hex codes)
    primary_color = db.Column(db.String(7))  # #RRGGBB
    secondary_color = db.Column(db.String(7))
    accent_color = db.Column(db.String(7))
    additional_colors = db.Column(db.Text)  # JSON array
    
    # Typography
    primary_font = db.Column(db.String(100))
    secondary_font = db.Column(db.String(100))
    
    # Logo/Monogram
    logo_url = db.Column(db.String(500))
    monogram_text = db.Column(db.String(50))
    
    # Style
    overall_style = db.Column(db.String(100))  # modern, rustic, classic, bohemian, etc.
    mood = db.Column(db.Text)

# ============================================
# BRIDAL PARTY MODULE
# ============================================

class BridalPartyMember(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))  # Optional: which person's side
    
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100))  # Custom role: maid of honor, best man, attendant, etc.
    side = db.Column(db.String(100))  # Flexible: can be person name, "both", "shared", etc.
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    
    # Attire Measurements
    dress_size = db.Column(db.String(20))
    suit_size = db.Column(db.String(20))
    shoe_size = db.Column(db.String(20))
    height = db.Column(db.String(20))
    
    # Gift Tracking
    gift_idea = db.Column(db.Text)
    gift_cost = db.Column(db.Float)
    gift_purchased = db.Column(db.Boolean, default=False)
    gift_given = db.Column(db.Boolean, default=False)
    
    # Plus One
    has_plus_one = db.Column(db.Boolean, default=False)
    plus_one_name = db.Column(db.String(200))
    
    # Tasks/Responsibilities
    responsibilities = db.Column(db.Text)
    
    # Processional Order
    processional_order = db.Column(db.Integer)
    
    # Relationship
    person = db.relationship('Person', backref='party_members', foreign_keys=[person_id])

# ============================================
# GUEST MANAGEMENT MODULE
# ============================================

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    table_id = db.Column(db.Integer, db.ForeignKey('seating_table.id'))
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))  # Optional: associated person
    
    # Basic Info
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    address = db.Column(db.Text)
    
    # RSVP
    invitation_sent = db.Column(db.Boolean, default=False)
    invitation_sent_date = db.Column(db.Date)
    rsvp_status = db.Column(db.String(20))  # pending, accepted, declined
    rsvp_date = db.Column(db.Date)
    attending_ceremony = db.Column(db.Boolean, default=True)
    attending_reception = db.Column(db.Boolean, default=True)
    
    # Meal Selection
    meal_choice = db.Column(db.String(200))
    dietary_restrictions = db.Column(db.Text)
    
    # Guest Category
    guest_type = db.Column(db.String(50))  # family, friend, colleague, etc.
    side = db.Column(db.String(100))  # Flexible: person name, "both", "shared", etc.
    household_group = db.Column(db.String(200))  # group name for household tracking
    social_groups = db.Column(db.Text)  # comma-separated group tags: "Church Group, Book Club, Work"
    rsvp_token = db.Column(db.String(64), unique=True)  # individual RSVP link token
    rsvp_notes = db.Column(db.Text)  # guest notes from RSVP form
    guest_token = db.Column(db.String(64), unique=True)  # token for cookie-based guest identification
    
    # Plus One
    is_plus_one = db.Column(db.Boolean, default=False)
    plus_one_of = db.Column(db.String(200))
    
    # Gift Registry
    gift_received = db.Column(db.Boolean, default=False)
    gift_description = db.Column(db.Text)
    thank_you_sent = db.Column(db.Boolean, default=False)
    thank_you_sent_date = db.Column(db.Date)
    
    # Relationship
    person = db.relationship('Person', backref='guests', foreign_keys=[person_id])

# ============================================
# BUDGET MODULE
# ============================================

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    total_budget = db.Column(db.Float, nullable=False)
    
    # Relationships
    expenses = db.relationship('BudgetExpense', backref='budget', lazy=True, cascade='all, delete-orphan')

class BudgetExpense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    
    category = db.Column(db.String(100), nullable=False)  # venue, catering, photography, etc.
    item_name = db.Column(db.String(200), nullable=False)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    paid_amount = db.Column(db.Float, default=0)
    payment_due_date = db.Column(db.Date)
    payment_status = db.Column(db.String(50))  # unpaid, deposit, partial, paid
    covered_by = db.Column(db.String(200))  # name of person purchasing on couple's behalf
    refund_amount = db.Column(db.Float, default=0)
    refund_notes = db.Column(db.String(500))
    notes = db.Column(db.Text)

# ============================================
# VENDOR MODULE
# ============================================

class Vendor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    category = db.Column(db.String(100), nullable=False)  # photographer, caterer, florist, etc.
    business_name = db.Column(db.String(200), nullable=False)
    contact_name = db.Column(db.String(200))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(50))
    website = db.Column(db.String(500))
    
    # Contract
    contract_signed = db.Column(db.Boolean, default=False)
    contract_date = db.Column(db.Date)
    cancellation_policy = db.Column(db.Text)
    contract_notes = db.Column(db.Text)

    # Backup
    backup_contact = db.Column(db.String(200))
    backup_phone = db.Column(db.String(50))

    # Financial
    total_cost = db.Column(db.Float)
    deposit_amount = db.Column(db.Float)
    deposit_paid = db.Column(db.Boolean, default=False)
    balance_due = db.Column(db.Float)
    final_payment_date = db.Column(db.Date)
    
    # Service Details
    service_date = db.Column(db.Date)
    service_time = db.Column(db.Time)
    service_location = db.Column(db.String(200))
    setup_instructions = db.Column(db.Text)  # day-of setup requirements
    meals_needed = db.Column(db.Integer, default=0)  # vendor meals to provide
    rating = db.Column(db.Integer)  # 1-5 star rating
    review_notes = db.Column(db.Text)  # post-wedding review
    notes = db.Column(db.Text)

# ============================================
# REGISTRY MODULE
# ============================================

class RegistryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    
    item_name = db.Column(db.String(200), nullable=False)
    store = db.Column(db.String(200))
    url = db.Column(db.String(500))
    price = db.Column(db.Float)
    quantity_requested = db.Column(db.Integer, default=1)
    quantity_purchased = db.Column(db.Integer, default=0)
    purchased_by = db.Column(db.String(200))

# ============================================
# ATTIRE MODULE
# ============================================

class Attire(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))  # Optional: if for someone getting married
    
    person_type = db.Column(db.String(100))  # Flexible: "person getting married", "wedding party", custom
    person_name = db.Column(db.String(200))
    
    # Garment Details
    garment_type = db.Column(db.String(100))  # dress, suit, tuxedo, outfit, etc.
    designer = db.Column(db.String(200))
    style_number = db.Column(db.String(100))
    color = db.Column(db.String(100))
    size = db.Column(db.String(50))
    
    # Shopping
    store = db.Column(db.String(200))
    price = db.Column(db.Float)
    purchased = db.Column(db.Boolean, default=False)
    purchase_date = db.Column(db.Date)
    
    # Fittings
    first_fitting_date = db.Column(db.Date)
    final_fitting_date = db.Column(db.Date)
    pickup_date = db.Column(db.Date)
    
    # Accessories
    accessories = db.Column(db.Text)  # shoes, jewelry, veil, etc.
    notes = db.Column(db.Text)
    
    # Relationship
    person = db.relationship('Person', backref='attire_items', foreign_keys=[person_id])

# ============================================
# DAY-OF TIMELINE MODULE
# ============================================

class DayOfTimelineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    time = db.Column(db.Time)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200))
    who = db.Column(db.String(500))  # who is involved
    category = db.Column(db.String(50))  # prep, ceremony, photos, reception, other
    order = db.Column(db.Integer, default=0)

    wedding = db.relationship('Wedding', backref=db.backref('day_of_items', lazy=True, cascade='all, delete-orphan'))

# ============================================
# PHOTOGRAPHY MODULE
# ============================================

class PhotoShot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    category = db.Column(db.String(50))  # getting_ready, ceremony, portraits, reception, detail
    description = db.Column(db.String(500), nullable=False)
    people = db.Column(db.String(500))  # who should be in the shot
    priority = db.Column(db.String(20), default='nice_to_have')  # must_have, nice_to_have
    captured = db.Column(db.Boolean, default=False)
    timeline_slot = db.Column(db.String(100))  # linked day-of timeline slot
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('photo_shots', lazy=True, cascade='all, delete-orphan'))

# ============================================
# MUSIC & PLAYLIST MODULE
# ============================================

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200))
    moment = db.Column(db.String(100))  # processional, first_dance, dinner, dancing, do_not_play, etc.
    spotify_url = db.Column(db.String(500))
    duration_minutes = db.Column(db.Float)  # song length
    notes = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

    wedding = db.relationship('Wedding', backref=db.backref('songs', lazy=True, cascade='all, delete-orphan'))

# ============================================
# FLOWERS & DECOR MODULE
# ============================================

class FloralItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    item_type = db.Column(db.String(100), nullable=False)  # bouquet, boutonniere, centerpiece, arch, corsage, etc.
    recipient = db.Column(db.String(200))  # who it's for
    flowers = db.Column(db.Text)  # flower types
    colors = db.Column(db.String(200))
    quantity = db.Column(db.Integer, default=1)
    cost = db.Column(db.Float)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('floral_items', lazy=True, cascade='all, delete-orphan'))

# ============================================
# INVITATIONS & STATIONERY MODULE
# ============================================

class Invitation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    item_type = db.Column(db.String(100), nullable=False)  # save_the_date, invitation, rsvp_card, program, menu_card, thank_you, place_card
    designer = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    cost = db.Column(db.Float)
    order_date = db.Column(db.Date)
    arrival_date = db.Column(db.Date)
    send_by_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='not_started')  # not_started, designing, ordered, received, sent
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('invitations', lazy=True, cascade='all, delete-orphan'))

# ============================================
# REHEARSAL DINNER MODULE
# ============================================

class RehearsalDinner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    date = db.Column(db.Date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)
    venue_contact = db.Column(db.String(120))
    venue_phone = db.Column(db.String(50))
    expected_guest_count = db.Column(db.Integer)
    menu_notes = db.Column(db.Text)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('rehearsal_dinner', uselist=False, cascade='all, delete-orphan'))

# ============================================
# GUEST ACCOMMODATIONS MODULE
# ============================================

class Accommodation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    accommodation_type = db.Column(db.String(50), nullable=False)  # hotel_block, recommended, transportation, parking
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text)
    phone = db.Column(db.String(50))
    website = db.Column(db.String(500))
    block_code = db.Column(db.String(100))  # for hotel blocks
    rate = db.Column(db.String(100))  # nightly rate or shuttle cost
    deadline = db.Column(db.Date)  # booking deadline
    rooms_reserved = db.Column(db.Integer)

    # Welcome/Gift Bags
    welcome_bag = db.Column(db.Boolean, default=False)
    welcome_bag_items = db.Column(db.Text)  # description of bag contents
    welcome_bags_delivered = db.Column(db.Boolean, default=False)

    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('accommodations', lazy=True, cascade='all, delete-orphan'))

# ============================================
# MARRIAGE LICENSE MODULE
# ============================================

class MarriageLicense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    county = db.Column(db.String(200))
    state = db.Column(db.String(100))
    application_date = db.Column(db.Date)
    pickup_date = db.Column(db.Date)
    expiration_date = db.Column(db.Date)
    filing_deadline = db.Column(db.Date)
    filed = db.Column(db.Boolean, default=False)
    filed_date = db.Column(db.Date)
    documents_needed = db.Column(db.Text)  # JSON list
    cost = db.Column(db.Float)
    waiting_period_days = db.Column(db.Integer)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('marriage_license', uselist=False, cascade='all, delete-orphan'))

# ============================================
# HAIR & MAKEUP MODULE
# ============================================

class HairMakeup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    person_name = db.Column(db.String(200), nullable=False)
    service_type = db.Column(db.String(50))  # hair, makeup, both
    appointment_time = db.Column(db.Time)
    stylist_name = db.Column(db.String(200))
    style_notes = db.Column(db.Text)
    trial_date = db.Column(db.Date)
    trial_completed = db.Column(db.Boolean, default=False)
    cost = db.Column(db.Float)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('hair_makeup', lazy=True, cascade='all, delete-orphan'))

# ============================================
# WEDDING PARTICIPANT & ITINERARY MODULE
# ============================================

class WeddingParticipant(db.Model):
    """Any individual with a role on the wedding day - couples, family, party, vendors, handlers."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100))  # bride, groom, mother_of_bride, best_man, photographer, coordinator, etc.
    role_category = db.Column(db.String(50))  # couple, family, wedding_party, vendor, handler
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    notes = db.Column(db.Text)

    # Optional links to existing records
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'))
    bridal_party_id = db.Column(db.Integer, db.ForeignKey('bridal_party_member.id'))

    person = db.relationship('Person', backref='participant_records', foreign_keys=[person_id])
    bridal_party_member = db.relationship('BridalPartyMember', backref='participant_records', foreign_keys=[bridal_party_id])

    wedding = db.relationship('Wedding', backref=db.backref('participants', lazy=True, cascade='all, delete-orphan'))


# Association table for many-to-many between timeline items and participants
timeline_assignments = db.Table('timeline_assignments',
    db.Column('timeline_item_id', db.Integer, db.ForeignKey('day_of_timeline_item.id'), primary_key=True),
    db.Column('participant_id', db.Integer, db.ForeignKey('wedding_participant.id'), primary_key=True)
)

# Add relationship to DayOfTimelineItem
DayOfTimelineItem.assigned_participants = db.relationship(
    'WeddingParticipant',
    secondary=timeline_assignments,
    backref=db.backref('timeline_items', lazy=True),
    lazy=True
)


# ============================================
# TRADITIONAL ELEMENTS LIBRARY
# ============================================

class TraditionalElement(db.Model):
    """Library of traditional wedding elements that couples can browse"""
    id = db.Column(db.Integer, primary_key=True)

    category = db.Column(db.String(100), nullable=False)  # ceremony, reception, cultural, religious
    subcategory = db.Column(db.String(100))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    origin = db.Column(db.String(200))  # cultural/religious origin
    typical_timing = db.Column(db.String(200))  # when in ceremony/reception
    what_you_need = db.Column(db.Text)  # items/people needed
    how_to_do_it = db.Column(db.Text)  # instructions

# ============================================
# CONTINGENCY PLAN MODULE
# ============================================

class ContingencyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    category = db.Column(db.String(100), nullable=False)  # weather, vendor_backup, venue_backup, emergency, transportation, power_outage, other
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    contact_name = db.Column(db.String(200))
    contact_phone = db.Column(db.String(50))
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('contingency_plans', lazy=True, cascade='all, delete-orphan'))

# ============================================
# BUDGET CATEGORY LIMIT MODULE
# ============================================

class BudgetCategoryLimit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)

    category = db.Column(db.String(100), nullable=False)
    limit_amount = db.Column(db.Float, nullable=False)

    budget = db.relationship('Budget', backref=db.backref('category_limits', lazy=True, cascade='all, delete-orphan'))

# ============================================
# TIPPING TRACKER MODULE
# ============================================

class TipItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    recipient = db.Column(db.String(200), nullable=False)  # e.g., "Lead Photographer", "DJ", "Catering Staff"
    service_category = db.Column(db.String(100))  # photography, catering, music, beauty, transportation, venue, planner, officiant, other
    suggested_amount = db.Column(db.Float)
    actual_amount = db.Column(db.Float)
    payment_method = db.Column(db.String(50))  # cash, check, venmo, other
    envelope_prepared = db.Column(db.Boolean, default=False)
    given = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('tips', lazy=True, cascade='all, delete-orphan'))

# ============================================
# GIFT TRACKING MODULE
# ============================================

class Gift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    event = db.Column(db.String(50), nullable=False)  # shower, wedding, engagement, other
    from_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    estimated_value = db.Column(db.Float)
    date_received = db.Column(db.Date)
    thank_you_sent = db.Column(db.Boolean, default=False)
    thank_you_sent_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('gifts', lazy=True, cascade='all, delete-orphan'))

# ============================================
# VENDOR COMMUNICATION LOG
# ============================================

class VendorNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendor.id'), nullable=False)
    note_type = db.Column(db.String(50))  # email, call, meeting, other
    subject = db.Column(db.String(200))
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    vendor = db.relationship('Vendor', backref=db.backref('communication_log', lazy=True, cascade='all, delete-orphan'))

# ============================================
# VENDOR QUOTE COMPARISON
# ============================================

class VendorQuote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)  # photographer, caterer, etc.
    vendor_name = db.Column(db.String(200), nullable=False)
    contact_info = db.Column(db.String(200))
    quote_amount = db.Column(db.Float)
    package_details = db.Column(db.Text)
    pros = db.Column(db.Text)
    cons = db.Column(db.Text)
    is_selected = db.Column(db.Boolean, default=False)
    date_received = db.Column(db.Date)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('vendor_quotes', lazy=True, cascade='all, delete-orphan'))

# ============================================
# SPEECHES & TOASTS TRACKER
# ============================================

class SpeechToast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    speaker_name = db.Column(db.String(200), nullable=False)
    speech_type = db.Column(db.String(50))  # toast, speech, blessing, roast
    order = db.Column(db.Integer, default=0)
    duration_minutes = db.Column(db.Integer)
    reviewed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('speeches', lazy=True, cascade='all, delete-orphan'))

# ============================================
# WEDDING FAVORS
# ============================================

class WeddingFavor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Integer)
    cost_per_item = db.Column(db.Float)
    total_cost = db.Column(db.Float)
    assembled = db.Column(db.Boolean, default=False)
    assembly_notes = db.Column(db.Text)
    vendor = db.Column(db.String(200))
    order_date = db.Column(db.Date)
    arrival_date = db.Column(db.Date)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('favors', lazy=True, cascade='all, delete-orphan'))

# ============================================
# ACTIVITY LOG (AUDIT TRAIL)
# ============================================

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name = db.Column(db.String(200))
    action = db.Column(db.String(50), nullable=False)  # created, updated, deleted
    entity_type = db.Column(db.String(100))  # guest, vendor, task, expense, etc.
    entity_name = db.Column(db.String(200))
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    wedding = db.relationship('Wedding', backref=db.backref('activity_log', lazy=True, cascade='all, delete-orphan'))

# ============================================
# COMMENTS ON ITEMS
# ============================================

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user_name = db.Column(db.String(200))
    entity_type = db.Column(db.String(100), nullable=False)  # vendor, task, expense, etc.
    entity_id = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    wedding = db.relationship('Wedding', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan'))

# ============================================
# BUDGET TEMPLATES
# ============================================

BUDGET_TEMPLATES = {
    'small': {
        'name': 'Small Wedding (under 50 guests)',
        'total': 15000,
        'categories': {
            'Venue': 3000, 'Catering': 3000, 'Photography': 2000,
            'Attire': 1500, 'Flowers': 800, 'Music/DJ': 800,
            'Invitations': 300, 'Officiant': 300, 'Hair & Makeup': 500,
            'Decorations': 500, 'Transportation': 300, 'Favors': 200,
            'Cake': 300, 'Rings': 1000, 'Miscellaneous': 500
        }
    },
    'medium': {
        'name': 'Medium Wedding (50-150 guests)',
        'total': 30000,
        'categories': {
            'Venue': 6000, 'Catering': 7000, 'Photography': 3500,
            'Videography': 2000, 'Attire': 2500, 'Flowers': 2000,
            'Music/DJ': 1500, 'Invitations': 600, 'Officiant': 500,
            'Hair & Makeup': 800, 'Decorations': 1000, 'Transportation': 600,
            'Favors': 400, 'Cake': 500, 'Rings': 1500, 'Miscellaneous': 600
        }
    },
    'large': {
        'name': 'Large Wedding (150+ guests)',
        'total': 50000,
        'categories': {
            'Venue': 10000, 'Catering': 12000, 'Photography': 5000,
            'Videography': 3000, 'Attire': 4000, 'Flowers': 3500,
            'Music/Band': 3000, 'Invitations': 1000, 'Officiant': 700,
            'Hair & Makeup': 1200, 'Decorations': 2000, 'Transportation': 1000,
            'Favors': 700, 'Cake': 800, 'Rings': 2000, 'Miscellaneous': 1100
        }
    }
}

# ============================================
# POST-WEDDING TASK TEMPLATES
# ============================================

POST_WEDDING_TASKS = [
    ('Send thank-you notes for gifts', 'gifts', 'high'),
    ('Preserve wedding dress/attire', 'attire', 'medium'),
    ('Back up all wedding photos and videos', 'photography', 'high'),
    ('Return rental items (suits, decor, etc.)', 'vendors', 'high'),
    ('Review and rate vendors', 'vendors', 'medium'),
    ('Submit name change paperwork (if applicable)', 'legal', 'high'),
    ('Update driver\'s license and Social Security card', 'legal', 'medium'),
    ('Update bank accounts and insurance', 'legal', 'medium'),
    ('File marriage certificate', 'legal', 'high'),
    ('Update emergency contacts', 'legal', 'low'),
    ('Write reviews for vendors online', 'vendors', 'low'),
    ('Create a wedding photo album', 'photography', 'low'),
    ('Return or exchange duplicate gifts', 'gifts', 'low'),
    ('Send final vendor payments if outstanding', 'budget', 'high'),
    ('Donate or preserve wedding flowers', 'flowers', 'low'),
]

# ============================================
# INVITATION WORDING TEMPLATES
# ============================================

INVITATION_WORDING_TEMPLATES = {
    'formal': {
        'name': 'Traditional Formal',
        'text': 'Mr. and Mrs. [Parent Names]\nrequest the honour of your presence\nat the marriage of their daughter\n[Bride Name]\nto\n[Groom Name]\non [Date]\nat [Time]\n[Venue Name]\n[Address]'
    },
    'semiformal': {
        'name': 'Semi-Formal',
        'text': 'Together with their families\n[Name] and [Name]\ninvite you to celebrate their marriage\non [Date]\nat [Time]\n[Venue Name]\n[Address]\nDinner and dancing to follow'
    },
    'casual': {
        'name': 'Casual & Fun',
        'text': '[Name] and [Name]\nare tying the knot!\nJoin us for the celebration\n[Date] at [Time]\n[Venue Name]\n[Address]\nFood, drinks, and dancing!'
    },
    'couple_hosted': {
        'name': 'Couple-Hosted',
        'text': '[Name] and [Name]\njoyfully invite you\nto share in the celebration of their marriage\n[Date]\nat [Time]\n[Venue Name]\n[Address]\nReception to follow'
    }
}
