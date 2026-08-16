"""Add modules missing from the migration chain

Eleven tables and three columns existed in models.py but were created by no
migration. The app hid it: db.create_all() runs at import and creates missing
tables, so a fresh install worked. An existing install did not -- create_all
never alters a table that already exists, so upgrading left wedding.public_url,
embed_enabled and embed_token absent, and Wedding is selected on virtually every
page.

Revision ID: 9acbe1e907c8
Revises: a1c4e7b90f21
Create Date: 2026-08-16 17:44:57.697614

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9acbe1e907c8'
down_revision = 'a1c4e7b90f21'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('accessibility_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('item_name', sa.String(length=300), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('assigned_to', sa.String(length=200), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('vendor', sa.String(length=200), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('accessibility_item', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_accessibility_item_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('custom_rsvp_question',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('question_text', sa.String(length=500), nullable=False),
    sa.Column('question_type', sa.String(length=20), nullable=True),
    sa.Column('options', sa.Text(), nullable=True),
    sa.Column('required', sa.Boolean(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('custom_rsvp_question', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_custom_rsvp_question_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('day_of_contact',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('role', sa.String(length=100), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('phone', sa.String(length=50), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('arrival_time', sa.String(length=20), nullable=True),
    sa.Column('departure_time', sa.String(length=20), nullable=True),
    sa.Column('setup_location', sa.String(length=200), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('day_of_contact', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_day_of_contact_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('day_of_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('task', sa.String(length=300), nullable=False),
    sa.Column('assigned_to', sa.String(length=200), nullable=True),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('timing', sa.String(length=100), nullable=True),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('day_of_task', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_day_of_task_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('name_change_task',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('task_name', sa.String(length=300), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('completed', sa.Boolean(), nullable=True),
    sa.Column('completed_date', sa.Date(), nullable=True),
    sa.Column('reference_number', sa.String(length=100), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('order', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('name_change_task', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_name_change_task_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('packing_list_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('item_name', sa.String(length=200), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('packed', sa.Boolean(), nullable=True),
    sa.Column('assigned_to', sa.String(length=200), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('packing_list_item', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_packing_list_item_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('pre_wedding_event',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('event_type', sa.String(length=50), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('date', sa.Date(), nullable=True),
    sa.Column('time', sa.String(length=20), nullable=True),
    sa.Column('end_time', sa.String(length=20), nullable=True),
    sa.Column('venue_name', sa.String(length=200), nullable=True),
    sa.Column('venue_address', sa.Text(), nullable=True),
    sa.Column('host_name', sa.String(length=200), nullable=True),
    sa.Column('host_phone', sa.String(length=50), nullable=True),
    sa.Column('host_email', sa.String(length=120), nullable=True),
    sa.Column('expected_guest_count', sa.Integer(), nullable=True),
    sa.Column('estimated_cost', sa.Float(), nullable=True),
    sa.Column('actual_cost', sa.Float(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('pre_wedding_event', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_pre_wedding_event_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('signage_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=200), nullable=True),
    sa.Column('size', sa.String(length=50), nullable=True),
    sa.Column('material', sa.String(length=100), nullable=True),
    sa.Column('vendor', sa.String(length=200), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('signage_item', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_signage_item_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('social_media_settings',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('wedding_hashtag', sa.String(length=200), nullable=True),
    sa.Column('backup_hashtags', sa.Text(), nullable=True),
    sa.Column('unplugged_ceremony', sa.Boolean(), nullable=True),
    sa.Column('unplugged_message', sa.Text(), nullable=True),
    sa.Column('social_sharing_policy', sa.String(length=50), nullable=True),
    sa.Column('sharing_policy_message', sa.Text(), nullable=True),
    sa.Column('photo_sharing_app', sa.String(length=200), nullable=True),
    sa.Column('photo_sharing_url', sa.String(length=500), nullable=True),
    sa.Column('photo_sharing_notes', sa.Text(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('social_media_settings', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_social_media_settings_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('wedding_element',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('wedding_id', sa.Integer(), nullable=False),
    sa.Column('element_id', sa.Integer(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['element_id'], ['traditional_element.id'], ),
    sa.ForeignKeyConstraint(['wedding_id'], ['wedding.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('wedding_element', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_wedding_element_element_id'), ['element_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_wedding_element_wedding_id'), ['wedding_id'], unique=False)

    op.create_table('custom_rsvp_answer',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('question_id', sa.Integer(), nullable=False),
    sa.Column('guest_id', sa.Integer(), nullable=False),
    sa.Column('answer_text', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['guest_id'], ['guest.id'], ),
    sa.ForeignKeyConstraint(['question_id'], ['custom_rsvp_question.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('custom_rsvp_answer', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_custom_rsvp_answer_guest_id'), ['guest_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_custom_rsvp_answer_question_id'), ['question_id'], unique=False)

    with op.batch_alter_table('wedding', schema=None) as batch_op:
        batch_op.add_column(sa.Column('public_url', sa.String(length=500), nullable=True))
        batch_op.add_column(sa.Column('embed_enabled', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('embed_token', sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint('uq_wedding_embed_token', ['embed_token'])



def downgrade():
    with op.batch_alter_table('wedding', schema=None) as batch_op:
        batch_op.drop_constraint('uq_wedding_embed_token', type_='unique')
        batch_op.drop_column('embed_token')
        batch_op.drop_column('embed_enabled')
        batch_op.drop_column('public_url')

    with op.batch_alter_table('custom_rsvp_answer', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_custom_rsvp_answer_question_id'))
        batch_op.drop_index(batch_op.f('ix_custom_rsvp_answer_guest_id'))

    op.drop_table('custom_rsvp_answer')
    with op.batch_alter_table('wedding_element', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_wedding_element_wedding_id'))
        batch_op.drop_index(batch_op.f('ix_wedding_element_element_id'))

    op.drop_table('wedding_element')
    with op.batch_alter_table('social_media_settings', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_social_media_settings_wedding_id'))

    op.drop_table('social_media_settings')
    with op.batch_alter_table('signage_item', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_signage_item_wedding_id'))

    op.drop_table('signage_item')
    with op.batch_alter_table('pre_wedding_event', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_pre_wedding_event_wedding_id'))

    op.drop_table('pre_wedding_event')
    with op.batch_alter_table('packing_list_item', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_packing_list_item_wedding_id'))

    op.drop_table('packing_list_item')
    with op.batch_alter_table('name_change_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_name_change_task_wedding_id'))

    op.drop_table('name_change_task')
    with op.batch_alter_table('day_of_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_day_of_task_wedding_id'))

    op.drop_table('day_of_task')
    with op.batch_alter_table('day_of_contact', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_day_of_contact_wedding_id'))

    op.drop_table('day_of_contact')
    with op.batch_alter_table('custom_rsvp_question', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_custom_rsvp_question_wedding_id'))

    op.drop_table('custom_rsvp_question')
    with op.batch_alter_table('accessibility_item', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_accessibility_item_wedding_id'))

    op.drop_table('accessibility_item')
