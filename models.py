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
    phone = db.Column(db.String(50))  # Primary phone for the couple (emergency contacts)
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

    # Public Access / Reverse Proxy
    public_url = db.Column(db.String(500))  # e.g., https://wedding.mydomain.com
    embed_enabled = db.Column(db.Boolean, default=False)
    embed_token = db.Column(db.String(64), unique=True)  # token for embed/public page access

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
    inventory_items = db.relationship('InventoryItem', backref='wedding', lazy=True, cascade='all, delete-orphan')
    inventory_bins = db.relationship('InventoryBin', backref='wedding', lazy=True, cascade='all, delete-orphan')
    wedding_elements = db.relationship('WeddingElement', backref='wedding', lazy=True, cascade='all, delete-orphan')

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
    name_pronunciation = db.Column(db.String(200))  # phonetic guide for DJ/MC announcements

    # Side naming (for organizational purposes)
    side_label = db.Column(db.String(100))  # e.g., "Jamie's side", "Alex's family", etc.

    # Getting Ready
    getting_ready_location = db.Column(db.String(200))  # where this person is getting ready
    getting_ready_address = db.Column(db.Text)
    getting_ready_time = db.Column(db.Time)  # when they start getting ready

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
    venue_rules = db.Column(db.Text)  # noise curfews, candle restrictions, confetti policies, etc.
    venue_load_in_time = db.Column(db.Time)  # when vendors can start setting up

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
    music = db.Column(db.String(200))  # song for this moment (e.g., per-person processional music)

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
    venue_rules = db.Column(db.Text)  # noise curfews, candle restrictions, last call time, etc.
    venue_load_in_time = db.Column(db.Time)  # when vendors can start setting up

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

    # After-Party
    after_party_venue = db.Column(db.String(200))
    after_party_address = db.Column(db.Text)
    after_party_start_time = db.Column(db.Time)
    after_party_notes = db.Column(db.Text)

    # Relationships
    timeline_items = db.relationship('ReceptionTimelineItem', backref='reception', lazy=True, cascade='all, delete-orphan')
    menu_items = db.relationship('MenuItem', backref='reception', lazy=True, cascade='all, delete-orphan')
    seating_tables = db.relationship('SeatingTable', backref='reception', lazy=True, cascade='all, delete-orphan')
    venue_fixtures = db.relationship('VenueFixture', backref='reception', lazy=True, cascade='all, delete-orphan')

class ReceptionTimelineItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('reception.id'), nullable=False)
    order = db.Column(db.Integer, nullable=False)
    item_name = db.Column(db.String(200), nullable=False)
    scheduled_time = db.Column(db.Time)
    duration_seconds = db.Column(db.Integer)
    description = db.Column(db.Text)
    announcement_script = db.Column(db.Text)  # MC/DJ script text to read aloud for this moment

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
    rotation = db.Column(db.Integer, default=0)   # degrees (0, 90, 180, 270)
    notes = db.Column(db.Text)

    # Relationship
    assigned_guests = db.relationship('Guest', backref='seating_table', lazy=True)


class VenueFixture(db.Model):
    """Non-table elements on the floor plan: dance floor, stage, bar, catering, etc."""
    id = db.Column(db.Integer, primary_key=True)
    reception_id = db.Column(db.Integer, db.ForeignKey('reception.id'), nullable=False)
    fixture_type = db.Column(db.String(50), nullable=False)  # key into VENUE_FIXTURE_TYPES
    label = db.Column(db.String(200))  # custom label override
    width_inches = db.Column(db.Integer, nullable=False)   # real-world width
    height_inches = db.Column(db.Integer, nullable=False)  # real-world depth
    x_position = db.Column(db.Float, default=0)
    y_position = db.Column(db.Float, default=0)
    notes = db.Column(db.Text)


# Venue fixture presets with typical real-world dimensions (inches)
VENUE_FIXTURE_TYPES = {
    'dance_floor_12': {
        'label': "12' Dance Floor",
        'category': 'entertainment',
        'width': 144, 'height': 144,
        'icon': 'dance',
    },
    'dance_floor_15': {
        'label': "15' Dance Floor",
        'category': 'entertainment',
        'width': 180, 'height': 180,
        'icon': 'dance',
    },
    'dance_floor_18': {
        'label': "18' Dance Floor",
        'category': 'entertainment',
        'width': 216, 'height': 216,
        'icon': 'dance',
    },
    'stage_8x4': {
        'label': "8'×4' Stage / Riser",
        'category': 'entertainment',
        'width': 96, 'height': 48,
        'icon': 'stage',
    },
    'stage_12x8': {
        'label': "12'×8' Stage",
        'category': 'entertainment',
        'width': 144, 'height': 96,
        'icon': 'stage',
    },
    'dj_booth': {
        'label': 'DJ Booth',
        'category': 'entertainment',
        'width': 72, 'height': 36,
        'icon': 'dj',
    },
    'band_area': {
        'label': 'Band / Live Music Area',
        'category': 'entertainment',
        'width': 144, 'height': 96,
        'icon': 'stage',
    },
    'bar_8ft': {
        'label': "8' Bar",
        'category': 'food_drink',
        'width': 96, 'height': 30,
        'icon': 'bar',
    },
    'bar_12ft': {
        'label': "12' Bar",
        'category': 'food_drink',
        'width': 144, 'height': 30,
        'icon': 'bar',
    },
    'buffet_8ft': {
        'label': "8' Buffet / Catering Table",
        'category': 'food_drink',
        'width': 96, 'height': 30,
        'icon': 'buffet',
    },
    'buffet_12ft': {
        'label': "12' Buffet / Catering Table",
        'category': 'food_drink',
        'width': 144, 'height': 30,
        'icon': 'buffet',
    },
    'dessert_table': {
        'label': 'Dessert / Cake Table',
        'category': 'food_drink',
        'width': 60, 'height': 30,
        'icon': 'cake',
    },
    'gift_table': {
        'label': 'Gift Table',
        'category': 'other',
        'width': 72, 'height': 30,
        'icon': 'gift',
    },
    'photo_booth': {
        'label': 'Photo Booth',
        'category': 'entertainment',
        'width': 96, 'height': 72,
        'icon': 'photo',
    },
    'guest_book_table': {
        'label': 'Guest Book / Sign-In Table',
        'category': 'other',
        'width': 48, 'height': 24,
        'icon': 'book',
    },
    'entrance': {
        'label': 'Entrance / Doorway',
        'category': 'access',
        'width': 72, 'height': 12,
        'icon': 'entrance',
    },
    'exit': {
        'label': 'Exit / Emergency Exit',
        'category': 'access',
        'width': 72, 'height': 12,
        'icon': 'exit',
    },
    'restrooms': {
        'label': 'Restrooms',
        'category': 'access',
        'width': 48, 'height': 48,
        'icon': 'restroom',
    },
    'wheelchair_ramp': {
        'label': 'Wheelchair Ramp / Accessible Entry',
        'category': 'access',
        'width': 60, 'height': 36,
        'icon': 'accessible',
    },
}


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
    # Round tables
    'round_48': {'shape': 'round', 'label': '48" Round', 'capacity': 6, 'diameter': 48},
    'round_60': {'shape': 'round', 'label': '60" Round (5ft)', 'capacity': 8, 'diameter': 60},
    'round_72': {'shape': 'round', 'label': '72" Round (6ft)', 'capacity': 10, 'diameter': 72},
    'round_84': {'shape': 'round', 'label': '84" Round (7ft)', 'capacity': 12, 'diameter': 84},
    # Standard banquet tables (30" wide, chairs on long sides)
    'banquet_4ft': {'shape': 'rectangular', 'label': '4ft Banquet', 'capacity': 4, 'length': 48, 'width': 30},
    'banquet_6ft': {'shape': 'rectangular', 'label': '6ft Banquet', 'capacity': 6, 'length': 72, 'width': 30},
    'banquet_8ft': {'shape': 'rectangular', 'label': '8ft Banquet', 'capacity': 8, 'length': 96, 'width': 30},
    # Long / farm / harvest tables
    'farm_10ft': {'shape': 'rectangular', 'label': '10ft Farm Table', 'capacity': 10, 'length': 120, 'width': 36},
    'farm_12ft': {'shape': 'rectangular', 'label': '12ft Farm Table', 'capacity': 12, 'length': 144, 'width': 36},
    'farm_16ft': {'shape': 'rectangular', 'label': '16ft Harvest Table', 'capacity': 16, 'length': 192, 'width': 36},
    # King's tables (wider, for bridal party)
    'kings_8ft': {'shape': 'rectangular', 'label': "8ft King's Table", 'capacity': 10, 'length': 96, 'width': 42},
    'kings_12ft': {'shape': 'rectangular', 'label': "12ft King's Table", 'capacity': 14, 'length': 144, 'width': 42},
    # Head table (one-sided seating, longer)
    'head_12ft': {'shape': 'rectangular', 'label': '12ft Head Table', 'capacity': 6, 'length': 144, 'width': 30, 'one_sided': True},
    'head_16ft': {'shape': 'rectangular', 'label': '16ft Head Table', 'capacity': 8, 'length': 192, 'width': 30, 'one_sided': True},
    'head_24ft': {'shape': 'rectangular', 'label': '24ft Head Table', 'capacity': 12, 'length': 288, 'width': 30, 'one_sided': True},
    # Other shapes
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
    name_pronunciation = db.Column(db.String(200))  # phonetic guide for DJ/MC announcements
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
    
    # Accessibility
    accessibility_needs = db.Column(db.Text)  # e.g., "wheelchair", "hearing", "mobility", "near exit"

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
    arrival_time = db.Column(db.Time)  # when vendor arrives (may differ from service_time)
    service_location = db.Column(db.String(200))
    setup_instructions = db.Column(db.Text)  # day-of setup requirements
    meals_needed = db.Column(db.Integer, default=0)  # vendor meals to provide
    overtime_rate = db.Column(db.String(100))  # hourly rate if event runs over contracted time
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
    name_pronunciation = db.Column(db.String(200))  # phonetic guide for DJ/MC announcements
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


class WeddingElement(db.Model):
    """Tracks which traditional elements a wedding has included"""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    element_id = db.Column(db.Integer, db.ForeignKey('traditional_element.id'), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    element = db.relationship('TraditionalElement')

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
    # Immediate (within 1 week)
    ('File marriage certificate with county clerk', 'legal', 'high'),
    ('Preserve wedding dress/suit (clean within 2 weeks before stains set)', 'attire', 'high'),
    ('Back up all wedding photos and videos to cloud storage', 'photography', 'high'),
    ('Send final vendor payments if outstanding', 'budget', 'high'),
    ('Return rental items (suits, decor, equipment) before deadlines', 'vendors', 'high'),
    ('Collect guest photos from phones, texts, and social media', 'photography', 'high'),
    ('Donate or preserve wedding flowers', 'flowers', 'low'),
    ('Pack up leftover favors, decorations, and supplies', 'vendors', 'medium'),
    # Within 1 month
    ('Send thank-you notes for gifts (aim for within 3 months)', 'gifts', 'high'),
    ('Review and rate vendors online (Google, Yelp, The Knot)', 'vendors', 'medium'),
    ('Return or exchange duplicate/unwanted gifts', 'gifts', 'medium'),
    ('Submit name change paperwork if applicable (start with SSA)', 'legal', 'high'),
    ('Update driver\'s license and state ID', 'legal', 'medium'),
    ('Update passport (takes 6-8 weeks)', 'legal', 'medium'),
    ('Update bank accounts and credit cards', 'legal', 'medium'),
    ('Update insurance policies (health, auto, home)', 'legal', 'medium'),
    ('Update employer/HR records and payroll', 'legal', 'medium'),
    ('Update beneficiaries on all accounts', 'legal', 'medium'),
    ('Update emergency contacts everywhere', 'legal', 'low'),
    # Within 3 months
    ('Create a wedding photo album', 'photography', 'low'),
    ('Write reviews for all vendors', 'vendors', 'low'),
    ('Organize and store guest book, cards, and keepsakes', 'gifts', 'low'),
    ('Update voter registration', 'legal', 'low'),
    ('Update subscription services and memberships', 'legal', 'low'),
    ('Schedule bouquet/boutonniere preservation if desired', 'flowers', 'low'),
]

# ============================================
# INVENTORY & ITEM TRACKING
# ============================================

class InventoryBin(db.Model):
    """A bin/box used to organize and transport wedding items."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    label = db.Column(db.String(100), nullable=False)  # e.g., "Table 5 Box", "Ceremony Bin A"
    area = db.Column(db.String(50))  # ceremony, cocktail_hour, reception, other
    table_number = db.Column(db.Integer)  # optional: which table this bin is for
    color_code = db.Column(db.String(20))  # optional color label for physical bin
    storage_location = db.Column(db.String(200))  # where the bin is stored before the event
    assigned_to = db.Column(db.String(200))  # who is responsible for transporting this bin
    notes = db.Column(db.Text)
    setup_photo_url = db.Column(db.String(500))  # URL/path to a reference photo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('InventoryItem', backref='bin', lazy=True)

    @property
    def item_count(self):
        return len(self.items)

    @property
    def total_quantity(self):
        return sum(i.quantity or 1 for i in self.items)

    @property
    def packed_count(self):
        return sum(1 for i in self.items if i.status == 'packed')


class InventoryItem(db.Model):
    """An individual inventory item for the wedding."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)
    bin_id = db.Column(db.Integer, db.ForeignKey('inventory_bin.id'), nullable=True)  # optional bin assignment

    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))  # centerpiece, linen, flatware, candle, signage, favor, decor, tableware, other
    quantity = db.Column(db.Integer, default=1)
    source = db.Column(db.String(30))  # owned, rented, borrowed, purchased, diy
    source_detail = db.Column(db.String(200))  # vendor name, who it's borrowed from, etc.
    area = db.Column(db.String(50))  # ceremony, cocktail_hour, reception, other
    table_number = db.Column(db.Integer)  # which table (if applicable)
    status = db.Column(db.String(30), default='needed')  # needed, acquired, packed, setup, returned, lost
    condition = db.Column(db.String(30))  # new, good, fair, fragile
    cost = db.Column(db.Float)
    return_by = db.Column(db.Date)  # for rentals: return deadline
    return_to = db.Column(db.String(200))  # where to return after wedding
    notes = db.Column(db.Text)
    setup_instructions = db.Column(db.Text)  # how to set this item up
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


INVENTORY_CATEGORIES = [
    ('centerpiece', 'Centerpieces'),
    ('linen', 'Linens & Table Runners'),
    ('flatware', 'Flatware & Silverware'),
    ('tableware', 'Plates, Glasses & Tableware'),
    ('candle', 'Candles & Lighting'),
    ('signage', 'Signs & Table Numbers'),
    ('favor', 'Favors'),
    ('floral', 'Flowers & Greenery'),
    ('decor', 'Decorative Elements'),
    ('ceremony', 'Ceremony Items'),
    ('photo', 'Photo Props & Displays'),
    ('card_box', 'Card Box & Guest Book'),
    ('supplies', 'Supplies & Tools'),
    ('other', 'Other'),
]

INVENTORY_AREAS = [
    ('ceremony', 'Ceremony'),
    ('cocktail_hour', 'Cocktail Hour'),
    ('reception', 'Reception'),
    ('entrance', 'Entrance / Welcome'),
    ('photo_area', 'Photo Area'),
    ('other', 'Other'),
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

# ============================================
# EMERGENCY KIT CUSTOMIZATION
# ============================================

class EmergencyKitItem(db.Model):
    """Custom emergency kit item - users can add/remove supplies from the checklist."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))  # fashion, health, beauty, tools, food, documents
    packed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('emergency_kit_items', lazy=True, cascade='all, delete-orphan'))


# ============================================
# PRE-WEDDING EVENTS
# ============================================

class PreWeddingEvent(db.Model):
    """Track pre-wedding events: engagement party, bridal shower, bachelor/ette, welcome party, etc."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    event_type = db.Column(db.String(50), nullable=False)  # engagement_party, bridal_shower, bachelor, bachelorette, welcome_party, send_off_brunch, other
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date)
    time = db.Column(db.String(20))
    end_time = db.Column(db.String(20))
    venue_name = db.Column(db.String(200))
    venue_address = db.Column(db.Text)
    host_name = db.Column(db.String(200))
    host_phone = db.Column(db.String(50))
    host_email = db.Column(db.String(120))
    expected_guest_count = db.Column(db.Integer)
    estimated_cost = db.Column(db.Float)
    actual_cost = db.Column(db.Float)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='planning')  # planning, confirmed, completed, cancelled

    wedding = db.relationship('Wedding', backref=db.backref('pre_wedding_events', lazy=True, cascade='all, delete-orphan'))


PRE_WEDDING_EVENT_TYPES = [
    ('engagement_party', 'Engagement Party'),
    ('bridal_shower', 'Bridal Shower'),
    ('couples_shower', 'Couples Shower'),
    ('bachelor', 'Bachelor Party'),
    ('bachelorette', 'Bachelorette Party'),
    ('welcome_party', 'Welcome Party / Welcome Drinks'),
    ('rehearsal_dinner', 'Rehearsal Dinner'),
    ('send_off_brunch', 'Morning-After / Send-Off Brunch'),
    ('bridesmaids_luncheon', 'Bridesmaids Luncheon'),
    ('other', 'Other Event'),
]


# ============================================
# WEDDING SIGNAGE CHECKLIST
# ============================================

class SignageItem(db.Model):
    """Track all signs and printed materials needed for the wedding."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))  # ceremony, reception, directional, informational, other
    description = db.Column(db.Text)
    location = db.Column(db.String(200))  # where the sign will be placed
    size = db.Column(db.String(50))  # e.g., "24x36", "8.5x11"
    material = db.Column(db.String(100))  # e.g., "acrylic", "chalkboard", "printed", "wood"
    vendor = db.Column(db.String(200))  # who is making it
    cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='needed')  # needed, ordered, received, placed
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('signage_items', lazy=True, cascade='all, delete-orphan'))


DEFAULT_SIGNAGE_ITEMS = [
    ('Welcome Sign', 'ceremony', 'Welcomes guests and confirms they are at the right wedding', 'Venue entrance'),
    ('Ceremony Program', 'ceremony', 'Order of ceremony events, wedding party names', 'Ceremony seating'),
    ('Unplugged Ceremony Sign', 'ceremony', 'Asks guests to put away phones during ceremony', 'Ceremony entrance'),
    ('Reserved Seating Signs', 'ceremony', 'Mark reserved rows for family', 'Front rows'),
    ('In Loving Memory Sign', 'ceremony', 'Honor deceased loved ones', 'Memorial table'),
    ('Seating Chart / Escort Display', 'reception', 'Shows guests their table assignments', 'Reception entrance'),
    ('Table Numbers', 'reception', 'Identify each table', 'Each table'),
    ('Place Cards', 'reception', 'Individual seat assignments at tables', 'Each place setting'),
    ('Bar Menu Sign', 'reception', 'Lists drink options and signature cocktails', 'Bar area'),
    ('Buffet / Food Station Labels', 'reception', 'Label each dish with name and allergen info', 'Food stations'),
    ('Dessert Table Sign', 'reception', 'Label desserts and cake flavor', 'Dessert table'),
    ('Guest Book Sign', 'reception', 'Encourages guests to sign the guest book', 'Guest book table'),
    ('Cards & Gifts Sign', 'reception', 'Directs guests where to leave cards and gifts', 'Gift table'),
    ('Photo Booth Sign', 'reception', 'Instructions for photo booth and props', 'Photo booth area'),
    ('Hashtag Sign', 'reception', 'Displays wedding hashtag for social media', 'Reception area'),
    ('Restroom Directional Signs', 'directional', 'Points guests toward restrooms', 'Hallways'),
    ('Parking Signs', 'directional', 'Directs guests to parking areas', 'Venue exterior'),
    ('Cocktail Hour Sign', 'reception', 'Directs guests to cocktail hour location', 'After ceremony'),
    ('Dance Floor Rules Sign', 'reception', 'Fun sign for the dance floor area', 'Dance floor'),
    ('Sparkler / Send-Off Sign', 'reception', 'Instructions for sparkler send-off', 'Exit area'),
    ('Thank You Sign', 'reception', 'Thanks guests as they leave', 'Exit'),
]


# ============================================
# DAY-OF CONTACT SHEET & TASK DELEGATION
# ============================================

class DayOfContact(db.Model):
    """Master contact sheet for the wedding day - vendors, VIPs, and key people."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(100), nullable=False)  # e.g., "Photographer", "DJ", "Day-of Coordinator", "MOH", "Best Man"
    category = db.Column(db.String(50))  # vendor, wedding_party, family, coordinator, other
    phone = db.Column(db.String(50))
    email = db.Column(db.String(120))
    arrival_time = db.Column(db.String(20))
    departure_time = db.Column(db.String(20))
    setup_location = db.Column(db.String(200))
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('day_of_contacts', lazy=True, cascade='all, delete-orphan'))


class DayOfTask(db.Model):
    """Task delegation for wedding day - who handles what."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    task = db.Column(db.String(300), nullable=False)
    assigned_to = db.Column(db.String(200))
    category = db.Column(db.String(50))  # setup, during, breakdown, emergency
    timing = db.Column(db.String(100))  # e.g., "Before ceremony", "End of night", "During reception"
    completed = db.Column(db.Boolean, default=False)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('day_of_tasks', lazy=True, cascade='all, delete-orphan'))


DEFAULT_DAY_OF_TASKS = [
    ('Transport marriage license and pen to ceremony venue', 'setup', 'Before ceremony'),
    ('Bring rings to ceremony', 'setup', 'Before ceremony'),
    ('Set up card box and gift table', 'setup', 'Before reception'),
    ('Set up guest book and pens', 'setup', 'Before reception'),
    ('Set up place cards / escort cards', 'setup', 'Before reception'),
    ('Coordinate vendor arrivals and setup', 'setup', 'Before ceremony'),
    ('Distribute wedding party bouquets and boutonnieres', 'setup', 'Before ceremony'),
    ('Ensure tip envelopes are prepared and distributed', 'during', 'During reception'),
    ('Gather family members for group photos', 'during', 'After ceremony'),
    ('Bustle the dress before reception', 'during', 'Between ceremony and reception'),
    ('Collect gifts and cards at end of night', 'breakdown', 'End of night'),
    ('Transport gifts and cards to safe location', 'breakdown', 'End of night'),
    ('Collect guest book and any keepsakes', 'breakdown', 'End of night'),
    ('Return any rented items or decorations', 'breakdown', 'End of night'),
    ('Settle final vendor payments', 'breakdown', 'End of night'),
    ('Ensure couple has overnight bag and essentials', 'breakdown', 'End of night'),
    ('Confirm ride/transportation for couple', 'breakdown', 'End of night'),
    ('Pack up leftover cake', 'breakdown', 'End of night'),
    ('Handle emergency situations as point person', 'emergency', 'All day'),
    ('Be point of contact for vendor questions', 'emergency', 'All day'),
]


# ============================================
# WEDDING DAY PACKING LIST
# ============================================

class PackingListItem(db.Model):
    """Wedding day packing list - everything to bring on the big day."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    item_name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50))  # documents, attire, accessories, ceremony, reception, personal, gifts, other
    packed = db.Column(db.Boolean, default=False)
    assigned_to = db.Column(db.String(200))  # who is responsible for bringing it
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('packing_list_items', lazy=True, cascade='all, delete-orphan'))


DEFAULT_PACKING_LIST = [
    ('Marriage license', 'documents'),
    ('Pen for signing license', 'documents'),
    ('Printed vows (backup copy)', 'documents'),
    ('Vendor contact sheet (printed)', 'documents'),
    ('Day-of timeline (printed copies)', 'documents'),
    ('Insurance documents', 'documents'),
    ('ID / drivers license', 'documents'),
    ('Wedding rings', 'ceremony'),
    ('Unity ceremony supplies (candle/sand/wine)', 'ceremony'),
    ('Ring bearer pillow', 'ceremony'),
    ('Flower girl petals / basket', 'ceremony'),
    ('Guest book and pens', 'ceremony'),
    ('Card box', 'ceremony'),
    ('Cake topper', 'reception'),
    ('Cake knife and server', 'reception'),
    ('Toasting flutes', 'reception'),
    ('Table numbers', 'reception'),
    ('Place cards / escort cards', 'reception'),
    ('Favors', 'reception'),
    ('Sparklers / send-off supplies', 'reception'),
    ('Gift table supplies (tablecloth, sign)', 'reception'),
    ('Welcome sign', 'reception'),
    ('Dress / suit on hanger', 'attire'),
    ('Shoes (ceremony)', 'attire'),
    ('Comfortable shoes (reception)', 'attire'),
    ('Heel stoppers for grass', 'attire'),
    ('Veil / headpiece', 'attire'),
    ('Jewelry', 'accessories'),
    ('Garter', 'accessories'),
    ('Cufflinks / tie', 'accessories'),
    ('Bouquet charm / memorial photo', 'accessories'),
    ('Undergarments (specific to dress)', 'attire'),
    ('Steamer / wrinkle spray', 'personal'),
    ('Phone charger / portable battery', 'personal'),
    ('Snacks and water for getting ready', 'personal'),
    ('Cash for emergencies and tips', 'personal'),
    ('Overnight bag for wedding night', 'personal'),
    ('Tip envelopes (labeled)', 'gifts'),
    ('Wedding party gifts', 'gifts'),
    ('Parent gifts / cards', 'gifts'),
    ('Spare invitation suite for photos', 'personal'),
    ('Perfume / cologne', 'personal'),
    ('Deodorant', 'personal'),
    ('Breath mints', 'personal'),
]


# ============================================
# NAME CHANGE CHECKLIST
# ============================================

class NameChangeTask(db.Model):
    """Post-wedding name change checklist tracker."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    task_name = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(50))  # government, financial, insurance, employment, medical, personal, other
    completed = db.Column(db.Boolean, default=False)
    completed_date = db.Column(db.Date)
    reference_number = db.Column(db.String(100))  # confirmation or reference number
    notes = db.Column(db.Text)
    order = db.Column(db.Integer, default=0)

    wedding = db.relationship('Wedding', backref=db.backref('name_change_tasks', lazy=True, cascade='all, delete-orphan'))


DEFAULT_NAME_CHANGE_TASKS = [
    ('Get certified copies of marriage certificate', 'government', 1),
    ('Update Social Security card (SSA office or online)', 'government', 2),
    ('Update drivers license / state ID', 'government', 3),
    ('Update passport', 'government', 4),
    ('Update voter registration', 'government', 5),
    ('Update bank accounts (checking, savings)', 'financial', 6),
    ('Update credit cards', 'financial', 7),
    ('Update investment / retirement accounts', 'financial', 8),
    ('Update loan documents (mortgage, auto, student)', 'financial', 9),
    ('Update health insurance', 'insurance', 10),
    ('Update auto insurance', 'insurance', 11),
    ('Update life insurance', 'insurance', 12),
    ('Update homeowners / renters insurance', 'insurance', 13),
    ('Update employer / HR records', 'employment', 14),
    ('Update payroll and direct deposit', 'employment', 15),
    ('Update professional licenses or certifications', 'employment', 16),
    ('Update doctor / dentist / medical records', 'medical', 17),
    ('Update pharmacy records', 'medical', 18),
    ('Update email signature', 'personal', 19),
    ('Update social media profiles', 'personal', 20),
    ('Update subscriptions and memberships', 'personal', 21),
    ('Update utility accounts', 'personal', 22),
    ('Update will / estate documents', 'personal', 23),
    ('Update power of attorney', 'personal', 24),
    ('Update beneficiaries on all accounts', 'personal', 25),
    ('Order new checks and address labels', 'personal', 26),
    ('Update airline frequent flyer accounts', 'personal', 27),
]


# ============================================
# CUSTOM RSVP QUESTIONS
# ============================================

class CustomRsvpQuestion(db.Model):
    """Custom questions to add to the RSVP form beyond meal choice and dietary restrictions."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    question_text = db.Column(db.String(500), nullable=False)
    question_type = db.Column(db.String(20), default='text')  # text, select, checkbox
    options = db.Column(db.Text)  # JSON array of options for select/checkbox types
    required = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, default=0)
    active = db.Column(db.Boolean, default=True)

    wedding = db.relationship('Wedding', backref=db.backref('custom_rsvp_questions', lazy=True, cascade='all, delete-orphan'))


class CustomRsvpAnswer(db.Model):
    """Guest answers to custom RSVP questions."""
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('custom_rsvp_question.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)

    answer_text = db.Column(db.Text)

    question = db.relationship('CustomRsvpQuestion', backref=db.backref('answers', lazy=True, cascade='all, delete-orphan'))
    guest = db.relationship('Guest', backref=db.backref('custom_rsvp_answers', lazy=True, cascade='all, delete-orphan'))


# ============================================
# HIDDEN COST REMINDERS
# ============================================

HIDDEN_COST_REMINDERS = [
    ('Vendor Meals', 'Catering', 'Photographers, videographers, DJ, band, planner all need meals. Budget $30-90 per vendor.', 150),
    ('Vendor Overtime', 'Vendors', 'Overtime fees of $100-500/hr per vendor if your event runs long. Add buffer.', 300),
    ('Service Charges / Gratuity', 'Venue', 'Many venues add 15-25% service charge on top of quoted prices.', 500),
    ('Corkage Fee', 'Venue', 'Fee charged by venue if you bring your own alcohol. Typically $15-35 per bottle.', 200),
    ('Cake Cutting Fee', 'Venue', 'Some venues charge $1-3 per slice to cut and plate your cake.', 150),
    ('Wedding Insurance', 'Insurance', 'Liability and cancellation coverage. Typically $150-500.', 300),
    ('Event Permits', 'Venue', 'Required for outdoor venues, parks, historical sites. $50-250+.', 100),
    ('Postage', 'Stationery', 'Save-the-dates, invitations, RSVP cards, thank-you notes. Budget per stamp.', 150),
    ('Dress/Suit Alterations', 'Attire', 'Alterations often cost $200-800 on top of purchase price.', 400),
    ('Dress Preservation & Cleaning', 'Attire', 'Post-wedding professional cleaning and preservation. $150-500.', 250),
    ('Beauty Prep (Trials)', 'Beauty', 'Hair trial, makeup trial, manicure, spray tan, teeth whitening, facials.', 300),
    ('Welcome Bags', 'Hospitality', 'Gift bags for hotel guests with snacks, water, local info. $5-15 per bag.', 200),
    ('Wedding Party Gifts', 'Gifts', 'Bridesmaids, groomsmen, parents, flower girl, ring bearer gifts.', 500),
    ('Parent Gifts', 'Gifts', 'Thank-you gifts for parents of the couple.', 200),
    ('Day-of Emergency Fund', 'Emergency', 'Cash for tips, unexpected costs. Recommend 5% of total budget.', 500),
    ('Valet / Parking', 'Transportation', 'Valet service or parking attendant fees if venue has limited parking.', 300),
    ('Guest Shuttles', 'Transportation', 'Shuttle service between hotel and venue. $500-2000.', 800),
    ('Non-Preferred Vendor Fee', 'Venue', 'Some venues charge 15-25% surcharge for vendors not on their preferred list.', 400),
    ('Garbage Removal / Cleanup', 'Venue', 'Post-event cleaning and garbage removal. $150-500.', 250),
    ('Extra Tables Rental', 'Rentals', 'Gift table, guest book table, place cards, cocktail hour tables.', 150),
    ('Dance Floor Rental', 'Rentals', 'Portable dance floor if venue does not have one. $200-800.', 400),
    ('Late-Night Snacks', 'Catering', 'Pizza, sliders, fries, or snacks for late-night dancing guests.', 300),
    ('Rehearsal Dinner', 'Events', 'Often forgotten in main wedding budget. Can be $1000-5000+.', 2000),
    ('Thank-You Cards', 'Stationery', 'Cards and postage for post-wedding thank-you notes.', 100),
    ('Marriage License Fee', 'Legal', 'Application fee varies by county. $20-100.', 50),
    ('Certified Copies', 'Legal', 'Additional certified copies of marriage certificate. $10-25 each.', 30),
]


# ============================================
# GUEST ACCESSIBILITY PLANNER
# ============================================

class AccessibilityItem(db.Model):
    """Track accessibility needs and accommodations for guests."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    item_name = db.Column(db.String(300), nullable=False)
    category = db.Column(db.String(50))  # mobility, hearing, vision, sensory, dietary, seating, other
    status = db.Column(db.String(20), default='needed')  # needed, arranged, confirmed
    assigned_to = db.Column(db.String(200))  # who is responsible
    cost = db.Column(db.Float)
    vendor = db.Column(db.String(200))  # vendor or provider
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('accessibility_items', lazy=True, cascade='all, delete-orphan'))


DEFAULT_ACCESSIBILITY_CHECKLIST = [
    ('Wheelchair accessible entrance and pathways', 'mobility', 'Check that all ceremony and reception areas are wheelchair accessible'),
    ('Accessible restrooms available', 'mobility', 'Verify ADA-compliant restrooms are available at the venue'),
    ('Reserved parking near entrance for disabled guests', 'mobility', 'Designate accessible parking spots close to the venue entrance'),
    ('Ramps available where there are steps', 'mobility', 'Ensure portable ramps are available if venue has stairs'),
    ('Seating near exits for mobility-impaired guests', 'seating', 'Reserve end-of-row or near-exit seats for guests with mobility needs'),
    ('Microphone for ceremony (hearing-impaired guests)', 'hearing', 'Ensure sound system amplifies vows and readings clearly'),
    ('Sign language interpreter (if needed)', 'hearing', 'Book interpreter through Registry of Interpreters for the Deaf'),
    ('Large-print programs and signage (16pt+ Sans Serif)', 'vision', 'Use Arial, Verdana, or Tahoma at 16pt minimum for readability'),
    ('Well-lit pathways and signage', 'vision', 'Ensure all walkways and signs are adequately illuminated'),
    ('Quiet/sensory-friendly break room', 'sensory', 'Designate a quiet space away from music for overwhelmed or neurodivergent guests'),
    ('Allergen labels on all food stations', 'dietary', 'Label every dish with common allergens (nuts, dairy, gluten, shellfish)'),
    ('Accommodation disclosure on RSVP', 'other', 'Add a field on RSVP for guests to share accessibility needs'),
    ('Chairs available during cocktail hour', 'seating', 'Provide ample seating during standing portions of the event'),
    ('Service animal accommodations', 'other', 'Ensure venue allows service animals and has a relief area'),
    ('Low centerpieces at accessible tables', 'seating', 'Avoid tall arrangements that block sightlines for seated wheelchair users'),
]


# ============================================
# WEDDING HASHTAG & SOCIAL MEDIA
# ============================================

class SocialMediaSettings(db.Model):
    """Wedding social media preferences and hashtag."""
    id = db.Column(db.Integer, primary_key=True)
    wedding_id = db.Column(db.Integer, db.ForeignKey('wedding.id'), nullable=False)

    wedding_hashtag = db.Column(db.String(200))
    backup_hashtags = db.Column(db.Text)  # JSON array of alternatives
    unplugged_ceremony = db.Column(db.Boolean, default=False)
    unplugged_message = db.Column(db.Text)  # Custom wording for unplugged ceremony sign/announcement
    social_sharing_policy = db.Column(db.String(50), default='open')  # open, wait_for_couple, no_posting
    sharing_policy_message = db.Column(db.Text)  # Custom message about when/what guests can share
    photo_sharing_app = db.Column(db.String(200))  # e.g., "Wedding Share", "The Guest", etc.
    photo_sharing_url = db.Column(db.String(500))  # URL or QR code link
    photo_sharing_notes = db.Column(db.Text)
    notes = db.Column(db.Text)

    wedding = db.relationship('Wedding', backref=db.backref('social_media', uselist=False, cascade='all, delete-orphan'))


UNPLUGGED_CEREMONY_TEMPLATES = [
    ('polite', 'Welcome! We invite you to be fully present during our ceremony. Please silence your phones and put away cameras. Our professional photographer will capture every moment for us to share with you later.'),
    ('friendly', 'We are so happy you are here! We kindly ask that you turn off your phones and cameras during the ceremony so everyone can be fully present. We promise to share photos!'),
    ('direct', 'This is an unplugged ceremony. Please turn off all phones, cameras, and recording devices. We want to see your faces, not your screens! Photos will be shared after the wedding.'),
    ('humorous', 'Unless you are our photographer, please put your phone away! We hired a professional for a reason. Plus, no one looks good lit by a phone screen. Enjoy the moment!'),
    ('short', 'Unplugged ceremony. Phones off, love on.'),
]

SOCIAL_SHARING_POLICIES = [
    ('open', 'Share freely! Post photos and videos anytime.'),
    ('wait_for_couple', 'Please wait to post until the couple shares first (usually 24-48 hours after the wedding).'),
    ('no_posting', 'We kindly request no social media posts from our wedding. We want to keep it private.'),
    ('hashtag_only', 'Feel free to post using our wedding hashtag so we can find your photos!'),
]
