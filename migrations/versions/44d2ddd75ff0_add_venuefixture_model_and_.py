"""Add VenueFixture model and accessibility_needs to Guest

Revision ID: 44d2ddd75ff0
Revises: 3f42632fa23f
Create Date: 2026-04-06 20:57:34.284292

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '44d2ddd75ff0'
down_revision = '3f42632fa23f'
branch_labels = None
depends_on = None


def upgrade():
    # db.create_all() may have already created these; use IF NOT EXISTS where possible
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if 'venue_fixture' not in existing_tables:
        op.create_table('venue_fixture',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('reception_id', sa.Integer(), nullable=False),
            sa.Column('fixture_type', sa.String(length=50), nullable=False),
            sa.Column('label', sa.String(length=200), nullable=True),
            sa.Column('width_inches', sa.Integer(), nullable=False),
            sa.Column('height_inches', sa.Integer(), nullable=False),
            sa.Column('x_position', sa.Float(), nullable=True),
            sa.Column('y_position', sa.Float(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['reception_id'], ['reception.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    guest_cols = [c['name'] for c in inspector.get_columns('guest')]
    if 'accessibility_needs' not in guest_cols:
        with op.batch_alter_table('guest', schema=None) as batch_op:
            batch_op.add_column(sa.Column('accessibility_needs', sa.Text(), nullable=True))

    table_cols = [c['name'] for c in inspector.get_columns('seating_table')]
    if 'rotation' not in table_cols:
        with op.batch_alter_table('seating_table', schema=None) as batch_op:
            batch_op.add_column(sa.Column('rotation', sa.Integer(), nullable=True))


def downgrade():
    with op.batch_alter_table('seating_table', schema=None) as batch_op:
        batch_op.drop_column('rotation')

    with op.batch_alter_table('guest', schema=None) as batch_op:
        batch_op.drop_column('accessibility_needs')

    op.drop_table('venue_fixture')
