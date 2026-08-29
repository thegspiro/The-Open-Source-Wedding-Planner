# Application Modification Checklist

This file is the authoritative checklist for anyone modifying the application. Complete every applicable item and document anything that is not applicable or cannot be completed.

## 1. Application overview

- [ ] Treat this repository as a Python 3.10+ Flask wedding-planning application.
- [ ] Use `app.py` as the primary application and routes module, `models.py` as the SQLAlchemy model layer, `security.py` as the CSRF, security, and rate-limiting module, and `email_service.py` as the SMTP integration.
- [ ] Account for Jinja templates in `templates/`, static assets in `static/`, migrations in `migrations/versions/`, tests in `tests/`, and SQLite data in `instance/`.
- [ ] Remember that the application normally listens on port `4345`.

## 2. Non-assumption policy

> **Never assume behavior, requirements, schemas, dependencies, command success, or test coverage.**

- [ ] Before changing behavior, inspect the relevant implementation, callers, models, templates, migrations, tests, configuration, and documentation.
- [ ] Verify command output and exit status; never infer success merely because no error was visibly printed.
- [ ] When repository evidence is insufficient, explicitly document every unavoidable assumption and confirm it with a maintainer before relying on it.
- [ ] Never invent APIs, model fields, environment variables, or migration history.

## 3. Error-handling policy

- [ ] Investigate and fix every error encountered while performing a change, including pre-existing errors exposed by validation.
- [ ] Never silently ignore, suppress, or work around a failure merely because it predates the current change.
- [ ] If an error genuinely cannot be fixed in the same change, document the exact command, exact output, impact, root-cause evidence, and an actionable follow-up tracking reference.
- [ ] After fixing an error's cause, rerun the failed check and record the result.
- [ ] Address concrete failures discovered during the work without introducing unrelated speculative refactors.

## 4. Required workflow for every change

- [ ] Read `Agent.md`, `README.md`, `CONTRIBUTING.md`, and all documentation relevant to the affected feature.
- [ ] Run `git status` before starting and preserve unrelated user changes.
- [ ] Trace affected behavior end-to-end across routes, models, templates, JavaScript/CSS, security controls, exports/imports, and tests, as applicable.
- [ ] Make the smallest complete change that fixes the underlying cause rather than masking symptoms.
- [ ] Add or update regression tests for bug fixes and behavior tests for new functionality.
- [ ] Update user-facing and contributor documentation whenever behavior, configuration, setup, troubleshooting, or operational procedures change.
- [ ] Review the final diff for accidental edits, secrets, debug output, placeholders, stale comments, and missing migration or documentation files.
- [ ] Commit only after applicable validation passes, with a clear commit message explaining the completed change.

## 5. Validation checklist

- [ ] Run `ruff check .` for static correctness checks.
- [ ] During development, run focused tests for each affected module, such as `pytest tests/test_affected_feature.py`, then run the complete `pytest` suite before completion.
- [ ] Run `python -m compileall app.py models.py security.py email_service.py` as a syntax check that does not depend on importing the modules.
- [ ] For deployment-affecting changes, perform a clean Docker rebuild, review container logs, and run `curl http://localhost:4345/health`.
- [ ] Report every command exactly and mark it **passed**, **failed**, or **not run**, including a reason for every command not run.
- [ ] Report a command as passing only after inspecting both its output and exit status.

## 6. Database and migration rules

- [ ] Whenever `models.py` changes the persisted schema, create a new Flask-Migrate/Alembic migration with `flask db migrate -m "description"`.
- [ ] Manually review every generated migration and apply it with `flask db upgrade`.
- [ ] Never rewrite or squash migrations already merged into shared history.
- [ ] Test schema changes against both a fresh database and an existing upgraded database.
- [ ] Run `scripts/check_migration_drift.py` using its documented invocation.
- [ ] Preserve user data and explicitly consider backup and restore procedures for destructive or data-transforming migrations.

## 7. Security and data-safety checks

- [ ] Verify authorization for wedding-scoped resources, CSRF protection for writes, input validation, safe public RSVP/share-token behavior, secure session handling, and rate limiting where applicable.
- [ ] Never commit `.env`, secrets, SMTP credentials, databases, backups, or personal wedding or guest information.
- [ ] Treat imports, exports, email, printing, public routes, and file operations as security-sensitive.
- [ ] Consult `SECURITY.md` for vulnerability handling.

## 8. Documentation requirements

- [ ] Document what changed, why it changed, affected files or components, migration implications, configuration changes, compatibility concerns, and validation results.
- [ ] Keep `README.md`, `INSTALL.md`, `QUICKSTART.md`, `CONTRIBUTING.md`, `TROUBLESHOOTING.md`, `.env.example`, and relevant pages in `docs/` synchronized with actual behavior.
- [ ] Add a `CHANGELOG.md` entry when the project's existing convention calls for one.
- [ ] Do not make undocumented behavior changes or publish misleading claims that have not been verified.

## 9. Manual regression areas

When relevant, verify all of the following:

- [ ] Creating and accessing weddings.
- [ ] Authenticated authorization boundaries.
- [ ] Public RSVP and share links.
- [ ] CRUD write paths.
- [ ] Seating auto-assignment.
- [ ] Emergency-kit behavior.
- [ ] Exports and imports.
- [ ] Printable views.
- [ ] Email reminders.
- [ ] Responsive layouts.
- [ ] Accessibility and keyboard behavior.
- [ ] Both empty/new installations and representative existing data.

## 10. Completion definition

Work is complete only when:

- [ ] The requested behavior is fully implemented.
- [ ] Every encountered error is resolved or transparently documented with actionable follow-up.
- [ ] All applicable automated and manual checks pass.
- [ ] Required migrations are included and verified.
- [ ] Documentation is current.
- [ ] The final diff contains no unrelated changes.

> **“Pre-existing” is not an acceptable reason to conceal or disregard a reproducible failure.**
