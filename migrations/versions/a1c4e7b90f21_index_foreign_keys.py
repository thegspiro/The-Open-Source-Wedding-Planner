"""Index every foreign key column

Nearly every query in the app filters on a foreign key - overwhelmingly
wedding_id - and none of those columns carried an index, so each one scanned
the whole table. Invisible with a single wedding; compounding for a
professional planner account holding many.

Indexes are created only where missing. Installs that were bootstrapped by
db.create_all() after the models changed will already have them, and
re-creating an existing index is an error on both SQLite and PostgreSQL.

Revision ID: a1c4e7b90f21
Revises: 44d2ddd75ff0
"""
from alembic import op
import sqlalchemy as sa


revision = 'a1c4e7b90f21'
down_revision = '44d2ddd75ff0'
branch_labels = None
depends_on = None


# (table, column) pairs, derived from the models' foreign keys.
FK_COLUMNS = [
    ('accessibility_item', 'wedding_id'),
    ('accommodation', 'wedding_id'),
    ('activity_log', 'wedding_id'),
    ('activity_log', 'user_id'),
    ('budget', 'wedding_id'),
    ('ceremony', 'wedding_id'),
    ('comment', 'wedding_id'),
    ('comment', 'user_id'),
    ('contingency_plan', 'wedding_id'),
    ('custom_rsvp_question', 'wedding_id'),
    ('day_of_contact', 'wedding_id'),
    ('day_of_task', 'wedding_id'),
    ('day_of_timeline_item', 'wedding_id'),
    ('emergency_kit_item', 'wedding_id'),
    ('floral_item', 'wedding_id'),
    ('gift', 'wedding_id'),
    ('guest_group', 'wedding_id'),
    ('hair_makeup', 'wedding_id'),
    ('honeymoon', 'wedding_id'),
    ('inventory_bin', 'wedding_id'),
    ('invitation', 'wedding_id'),
    ('marriage_license', 'wedding_id'),
    ('name_change_task', 'wedding_id'),
    ('packing_list_item', 'wedding_id'),
    ('person', 'wedding_id'),
    ('photo_shot', 'wedding_id'),
    ('pre_wedding_event', 'wedding_id'),
    ('reception', 'wedding_id'),
    ('registry_item', 'wedding_id'),
    ('rehearsal_dinner', 'wedding_id'),
    ('signage_item', 'wedding_id'),
    ('social_media_settings', 'wedding_id'),
    ('song', 'wedding_id'),
    ('speech_toast', 'wedding_id'),
    ('task', 'wedding_id'),
    ('task', 'depends_on_id'),
    ('tip_item', 'wedding_id'),
    ('vendor', 'wedding_id'),
    ('vendor_quote', 'wedding_id'),
    ('wedding_access', 'user_id'),
    ('wedding_access', 'wedding_id'),
    ('wedding_branding', 'wedding_id'),
    ('wedding_element', 'wedding_id'),
    ('wedding_element', 'element_id'),
    ('wedding_favor', 'wedding_id'),
    ('attire', 'wedding_id'),
    ('attire', 'person_id'),
    ('bridal_party_member', 'wedding_id'),
    ('bridal_party_member', 'person_id'),
    ('budget_category_limit', 'budget_id'),
    ('budget_expense', 'budget_id'),
    ('ceremony_reading', 'ceremony_id'),
    ('ceremony_timeline_item', 'ceremony_id'),
    ('honeymoon_itinerary', 'honeymoon_id'),
    ('inventory_item', 'wedding_id'),
    ('inventory_item', 'bin_id'),
    ('menu_item', 'reception_id'),
    ('packing_item', 'honeymoon_id'),
    ('reception_timeline_item', 'reception_id'),
    ('seating_table', 'reception_id'),
    ('vendor_note', 'vendor_id'),
    ('venue_fixture', 'reception_id'),
    ('guest', 'wedding_id'),
    ('guest', 'table_id'),
    ('guest', 'person_id'),
    ('wedding_participant', 'wedding_id'),
    ('wedding_participant', 'person_id'),
    ('wedding_participant', 'bridal_party_id'),
    ('custom_rsvp_answer', 'question_id'),
    ('custom_rsvp_answer', 'guest_id'),
    ('seating_preference', 'wedding_id'),
    ('seating_preference', 'guest_id'),
    ('seating_preference', 'other_guest_id'),
]


def _existing(inspector, table):
    if table not in inspector.get_table_names():
        return None
    return {ix['name'] for ix in inspector.get_indexes(table)}


def upgrade():
    inspector = sa.inspect(op.get_bind())
    for table, column in FK_COLUMNS:
        present = _existing(inspector, table)
        if present is None:
            continue
        name = f'ix_{table}_{column}'
        if name not in present:
            op.create_index(name, table, [column], unique=False)


def downgrade():
    inspector = sa.inspect(op.get_bind())
    for table, column in FK_COLUMNS:
        present = _existing(inspector, table)
        if present is None:
            continue
        name = f'ix_{table}_{column}'
        if name in present:
            op.drop_index(name, table_name=table)
