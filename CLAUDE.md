# CLAUDE.md — Project Context for Claude Code

This file provides Claude Code-specific orientation for Wedding Organizer.

**Read and follow `AGENTS.md` before beginning any task.** `AGENTS.md` is the authoritative repository-wide coding-agent workflow covering Git, pull requests, conflicts, CI, generated files, migration safety, security, validation, and the definition of done.

This file provides a compact project map and Claude-specific context. Do not duplicate or weaken requirements from `AGENTS.md` here.

## What This Is

Wedding Organizer is an open-source, Docker-deployable wedding planning application built with Python Flask, SQLAlchemy, Jinja2, SQLite, and Flask-Migrate/Alembic.

It supports multiple weddings and includes planning modules for people, ceremony, reception, guests/RSVPs, seating, wedding party, vendors, budget, tasks, honeymoon, branding, attire, registry, speeches, favors, invitations, public RSVP, and printable planning views.

The application handles sensitive personal information. Treat guest/contact information, RSVP responses, vendor/payment information, public RSVP tokens, email configuration, and wedding data as sensitive even when working in development.

## Read Before Editing

Use the repository documentation as project context rather than guessing behavior:

- `README.md` — product overview and features
- `CONTRIBUTING.md` — development workflow, migrations, testing, and PR expectations
- `INSTALL.md` — installation and deployment
- `QUICKSTART.md` — user setup and email configuration
- `ONBOARDING_GUIDE.md` — onboarding behavior
- `TROUBLESHOOTING.md` — known operational/schema issues
- `CHANGELOG.md` — shipped behavior/history
- `docs/WIKI.md` — broader feature documentation
- `docs/DEPLOYMENT-GUIDES.md` — platform deployment guidance
- `docs/REVERSE-PROXY.md` — proxy/HTTPS configuration

When code and documentation disagree, investigate which is stale. Do not silently choose whichever is convenient; update documentation in the same change when appropriate.

## Development Setup

Prerequisites:

- Python 3.10+
- Git
- Docker and Docker Compose for production-style validation

Typical local setup:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

The application is normally available at:

```text
http://localhost:4345
```

Docker validation:

```bash
docker-compose up -d --build
docker-compose logs
curl http://localhost:4345/health
```

Never put real secrets into `.env` examples or commits.

## Project Structure

```text
app.py              Flask routes and application behavior
models.py           SQLAlchemy ORM models
security.py         CSRF, security headers, rate limiting
email_service.py    SMTP/email sending
requirements.txt    Python dependencies
Dockerfile          Container definition
docker-compose.yml  Container orchestration
static/             CSS and client-side assets
templates/          Jinja2 templates
migrations/         Flask-Migrate/Alembic migrations
scripts/            Operational utilities such as backup/restore
docs/               Product/deployment documentation
instance/           Runtime SQLite database and instance data
```

`app.py` and `models.py` are large. Do not respond to their size by rewriting broad sections. Trace the relevant route/model/template relationships and make focused changes.

## Code Style

Follow the conventions documented in `CONTRIBUTING.md` and surrounding code:

- Python: PEP 8
- Templates: Jinja2 with consistent HTML indentation
- CSS: vanilla CSS
- JavaScript: vanilla JavaScript; do not introduce a framework casually

Prefer established helpers and patterns over creating parallel abstractions for one task.

## Database and Migrations

The application uses SQLite through SQLAlchemy and Flask-Migrate/Alembic.

For model changes:

```bash
flask db migrate -m "description"
flask db upgrade
```

Always review generated migration code before committing it.

A critical project characteristic is that the app may call `db.create_all()` for development convenience. This means a fresh database can appear healthy even when an existing installation cannot upgrade correctly. For schema work, reason about **both** paths:

1. a fresh database; and
2. an existing database applying migrations.

Do not delete `instance/wedding_organizer.db` to conceal a migration problem. Do not edit already-shipped migrations. Create a new migration.

Renames and semantic data transformations require particular care because Alembic autogeneration can represent them as destructive drop/add operations. Preserve user data explicitly.

## Runtime Database and Binary Artifacts

`instance/wedding_organizer.db` is runtime user data. It is not a source file to regenerate, replace, or commit as part of an ordinary code fix.

If local development or tests create database files, journals, backups, logs, caches, screenshots, or other artifacts, follow `AGENTS.md`: keep them out of the proposed diff unless the repository intentionally tracks that exact artifact.

If a Git conflict involves the SQLite database or another opaque binary, do not attempt to merge binary contents. Determine which artifact should exist, regenerate from source when appropriate, or escalate.

## Security Invariants

Treat changes to `security.py`, authentication/session behavior, public RSVP, forms, email, and data export as security-sensitive.

Preserve:

- CSRF protection on state-changing requests;
- server-side validation of untrusted input;
- authentication and authorization boundaries;
- rate limiting where established;
- security headers where established; and
- confidentiality of RSVP tokens, secret keys, SMTP credentials, and personal data.

Do not log secrets or full sensitive records as a debugging shortcut.

Public RSVP token links are effectively bearer credentials. Avoid exposing tokens outside the specific flow that needs them.

## Email

Email is optional and configured through environment variables. Never hard-code credentials.

Do not allow automated tests or agent validation to send real messages. Use safe test configuration, mocks, or a local sink when email behavior must be exercised.

When changing reminder/email behavior, test failure paths as well as successful sends. An SMTP failure should not corrupt task, RSVP, or wedding state.

## Templates and Forms

When modifying Jinja templates:

- preserve field names expected by Flask handlers;
- preserve CSRF integration;
- verify empty and validation-error states;
- avoid placing business logic in templates when it belongs in Python;
- preserve accessibility semantics where practical;
- check responsive/mobile behavior; and
- verify public-facing pages do not expose data from another wedding.

For route changes, trace the corresponding template(s), model operations, redirects, and flash/error handling rather than editing the route in isolation.

## RSVP Portal

The RSVP portal is public and token-based, so changes require extra scrutiny.

Verify that:

- a token grants access only to the intended RSVP context;
- malformed/expired/unknown tokens fail safely;
- public responses cannot be used to enumerate unrelated guests or weddings;
- state-changing submissions remain CSRF/validation-safe according to the application's intended public-flow design; and
- error messages do not leak sensitive internal details.

## Backup and Restore

The repository includes backup tooling under `scripts/`. Backup/restore changes can destroy user data if implemented incorrectly.

Use disposable sample databases for testing. Validate paths and failure behavior. Never overwrite or delete the only copy of a database merely to test restore logic.

## Testing Expectations

Follow `CONTRIBUTING.md` and current CI rather than inventing commands that the repository does not provide.

For Docker/runtime changes, the documented production-style check is:

```bash
docker-compose down
docker-compose up -d --build
docker-compose logs
curl http://localhost:4345/health
```

When applicable, verify:

- a new wedding can be created;
- affected modules work with an existing database;
- RSVP flows work with safe test data;
- mobile/responsive layout remains usable;
- migrations work on fresh and existing databases; and
- the container reaches a healthy state.

As automated test coverage grows, prefer regression tests over relying only on manual verification.

## Git, PRs, CI, and Conflicts

Do not maintain a separate Claude-specific policy here. Follow `AGENTS.md`.

In particular:

- you may diagnose and repair PRs created by other people or agents;
- work from the PR's code state rather than refusing because of PR ownership;
- resolve text conflicts by understanding both sides;
- do not manually merge opaque binary files;
- inspect the full diff and `git status` before completion;
- diagnose deterministic CI failures instead of repeatedly rerunning them; and
- report exact permission/tooling limitations when the original PR branch cannot be updated.

## Documentation

Documentation is part of the application. Update the appropriate user/operator documentation whenever behavior, setup, migrations, configuration, email, deployment, backup/restore, or troubleshooting changes.

Do not claim an unverified feature works merely because a model, setting, route stub, or dependency exists.

## Completion

Before saying a task is complete, apply the `AGENTS.md` definition of done. At minimum, state:

- what changed;
- what validation actually ran;
- whether schema/data/security implications were checked; and
- anything that could not be validated.

Do not say "all tests pass" or "ready to merge" unless you have actually established that result.