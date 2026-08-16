#!/usr/bin/env python3
"""Fail if the migration chain no longer builds the schema models.py declares.

Why this exists: db.create_all() runs at import, so a fresh install gets its
schema from the models regardless of what the migrations say. That makes drift
invisible in development and in tests -- everything works -- right up until an
existing installation upgrades. create_all() creates missing tables but never
alters a table that already exists, so a column added to an existing model
reaches nobody, and the app dies with "no such column" on a database that was
working five minutes earlier.

When this fails, the fix is to generate the missing migration, not to edit this
script:

    rm -f /tmp/drift.db
    SKIP_DB_CREATE_ALL=1 DATABASE_URL=sqlite:////tmp/drift.db flask db upgrade
    SKIP_DB_CREATE_ALL=1 DATABASE_URL=sqlite:////tmp/drift.db flask db migrate -m "..."

Then read what Alembic generated before committing it.
"""

import os
import sys
import tempfile

# Run from anywhere: this script lives in scripts/, the app at the repo root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Must be set before app is imported: create_all() runs at import time and would
# otherwise build the schema from the models, which is the thing under test.
os.environ["SKIP_DB_CREATE_ALL"] = "1"
os.environ.setdefault("SECRET_KEY", "migration-drift-check")

_db_path = os.path.join(tempfile.mkdtemp(prefix="drift-"), "chain.db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"

from alembic.autogenerate import compare_metadata  # noqa: E402
from alembic.migration import MigrationContext  # noqa: E402
from flask_migrate import upgrade  # noqa: E402

from app import app  # noqa: E402
from models import db  # noqa: E402


# Alembic reports these as differences even on a clean chain: SQLite renders
# server defaults and some type widths differently than the model declares.
# Ignoring the noise keeps the check honest about what it can actually prove.
IGNORED_DIFF_KINDS = {
    "modify_default",
    "modify_nullable",
    "modify_type",
}


def describe(diff):
    """Turn one Alembic diff tuple into a line a human can act on."""
    kind = diff[0]
    if kind in ("add_table", "remove_table"):
        return f"{kind}: {diff[1].name}"
    if kind in ("add_column", "remove_column"):
        return f"{kind}: {diff[2]}.{diff[3].name}"
    if kind in ("add_index", "remove_index", "add_constraint", "remove_constraint"):
        obj = diff[1]
        table = getattr(obj, "table", None)
        name = getattr(obj, "name", obj)
        return f"{kind}: {getattr(table, 'name', '?')}.{name}"
    return f"{kind}: {diff[1:]}"


def main():
    with app.app_context():
        upgrade()

        connection = db.engine.connect()
        context = MigrationContext.configure(connection)
        diffs = compare_metadata(context, db.metadata)
        connection.close()

    actionable = [d for d in diffs
                  if (d[0] if isinstance(d[0], str) else d[0][0]) not in IGNORED_DIFF_KINDS]

    if not actionable:
        tables = len(db.metadata.tables)
        print(f"OK: the migration chain reproduces all {tables} tables in models.py")
        return 0

    print("Migration drift detected.\n")
    print("models.py declares schema that no migration creates. A fresh install")
    print("hides this because create_all() runs at import; an existing install")
    print("upgrading does not, and will fail with a missing table or column.\n")
    for diff in actionable:
        # A diff may be a single tuple or a list of them (grouped column changes).
        for item in (diff if isinstance(diff, list) else [diff]):
            print(f"  {describe(item)}")
    print("\nGenerate the missing migration -- see the header of this script.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
