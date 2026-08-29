# AGENTS.md — Repository Instructions for Coding Agents

This file defines repository-wide instructions for Codex and other coding agents working on Wedding Organizer.

Before making changes, read `README.md`, `CONTRIBUTING.md`, and the documentation relevant to the task. Important references include `INSTALL.md`, `QUICKSTART.md`, `TROUBLESHOOTING.md`, `ONBOARDING_GUIDE.md`, `docs/WIKI.md`, and the deployment/security documentation under `docs/`.

This repository currently has no separate `CLAUDE.md`; this file is therefore the primary persistent coding-agent instruction file. Project documentation remains authoritative for user-facing behavior, installation, deployment, and contribution workflows.

## Core Principle: Leave the Repository Better, Green, and Explainable

Do not silently ignore an error you encounter. Python errors, template errors, migration failures, broken routes, security regressions, test failures, container startup failures, health-check failures, and CI failures must be either fixed at their root cause or explicitly escalated when the repair genuinely exceeds the task's scope.

Never make a check pass by weakening the check. Do not remove validation, bypass CSRF or authorization, delete failing tests, suppress meaningful errors, or disable security controls merely to obtain a green result.

## Start of Every Task

Before editing code:

1. Read the repository documentation relevant to the task.
2. Inspect the current branch, `git status`, and recent history affecting the files you will modify.
3. Understand the existing implementation before replacing or refactoring it.
4. Inspect applicable migrations and tests before changing models or persistence behavior.
5. Inspect `.github/workflows/` when the task can affect CI.
6. Keep the change focused. Avoid unrelated refactors unless they are necessary to resolve an error actually encountered.

## Architecture Awareness

The application is a Flask wedding-planning platform with SQLAlchemy models, Jinja2 templates, SQLite persistence, Flask-Migrate/Alembic migrations, and Docker deployment.

Major areas include:

- `app.py` — Flask routes and application behavior
- `models.py` — SQLAlchemy ORM models
- `security.py` — CSRF, security headers, rate limiting, and related safeguards
- `email_service.py` — SMTP/email behavior
- `templates/` — Jinja2 UI templates
- `static/` — CSS and client-side assets
- `migrations/` — Flask-Migrate/Alembic migrations
- `scripts/` — operational utilities such as backups
- `instance/` — runtime SQLite data; do not treat runtime database files as source code

Large files are not permission to make broad rewrites. Make the smallest coherent change that preserves established behavior.

## Git and Branch Hygiene

Work on a dedicated branch unless the environment provides an existing task branch.

Before considering work complete:

- Fetch the latest `origin/main` when the environment permits.
- Determine whether the task branch has diverged from `origin/main`.
- Synchronize the branch when appropriate before final validation.
- Resolve ordinary text conflicts carefully, preserving the intent of both the current main branch and the proposed change.
- Never blindly choose "ours" or "theirs" for an entire conflicted file without understanding both sides.
- After resolving conflicts, rerun validation relevant to the affected code.
- Inspect `git status` and the complete final diff against `origin/main`.

Do not rewrite shared branch history unless explicitly required and safe. If a rebase requires a force push, use the safest available mechanism such as `--force-with-lease`.

## Existing Pull Requests — Including PRs You Did Not Create

A pull request does **not** need to have been created by Codex or by the current agent for you to diagnose or repair its code.

When asked to fix an existing PR:

1. Inspect the PR's base/head state, changed files, checks, and relevant discussion.
2. Treat the PR's HEAD as the code state to diagnose.
3. Reproduce failures locally when possible.
4. Fix the root cause and validate the repair.
5. If permissions allow, update the existing PR branch.
6. If the environment cannot modify the original branch, do not stop merely because another person or agent created the PR. Create a repair branch or commit from the PR state when permitted and clearly report how it should be applied.
7. If tooling or permissions genuinely prevent repair, report the exact limitation.

Never claim that a PR is mergeable, green, or ready to merge unless that state has actually been verified.

## Merge Conflicts

For text conflicts:

- read the surrounding code and both conflicting versions;
- determine the behavioral intent of each side;
- produce a coherent combined result rather than mechanically selecting one side;
- check models, templates, routes, migrations, and documentation for related changes; and
- rerun targeted validation immediately after resolution.

Migration conflicts deserve special care. Do not combine Alembic revisions by casually editing revision identifiers or deleting migrations. Understand the migration graph and preserve already-shipped history.

## Binary, Runtime, and Generated Files

The application's SQLite database is runtime data, not a normal source artifact.

Before every commit and before reporting completion, inspect `git status` and the full diff for unintended files.

Do not commit unintended:

- `instance/*.db` or other SQLite database files
- database journals/WAL files
- backups containing user/wedding data
- logs
- caches or `__pycache__`
- coverage output
- compiled/build output
- temporary files
- test artifacts
- screenshots created only for debugging
- archives
- editor/OS metadata
- `.env` files, credentials, SMTP passwords, secret keys, tokens, or other secrets

If running the application, tests, migrations, or Docker creates files in the working tree:

1. determine why they were created;
2. remove unintended artifacts from the proposed change;
3. update `.gitignore` when appropriate; and
4. adjust the workflow when necessary so routine validation does not dirty the repository.

Do not attempt to synthesize or manually merge an opaque binary conflict. Determine which version is authoritative, regenerate from source when possible, or escalate it for review.

## Database and Migration Safety

The application uses SQLAlchemy with Flask-Migrate/Alembic. `db.create_all()` may make a fresh development database appear to work even when the migration path for an existing installation is broken. Therefore, **fresh-database success is not sufficient validation for schema changes.**

When changing `models.py`:

1. generate a new migration with the repository's documented Flask-Migrate workflow;
2. review the generated migration file manually;
3. include the migration in the same PR;
4. test a fresh database when practical;
5. test upgrading an existing database when practical;
6. preserve existing user data during renames, type changes, and relationship changes; and
7. never modify or squash a migration that has already been merged/shipped — create a new migration instead.

Alembic autogeneration understands schema differences, not business intent. A generated migration that drops and recreates a column may destroy information. Hand-edit the new migration when necessary to preserve data.

Do not delete or replace `instance/wedding_organizer.db` as a shortcut for making a schema problem disappear. Existing installations matter.

## Security and Public Surfaces

Wedding Organizer contains personal guest information, contact information, RSVP data, vendor/payment information, and public token-based RSVP functionality. Treat these as sensitive application data.

When modifying routes or forms:

- preserve CSRF protection for state-changing actions;
- validate and normalize untrusted input server-side;
- preserve authentication/authorization boundaries;
- do not expose internal IDs, secrets, or sensitive records unnecessarily;
- treat public RSVP tokens as credentials and avoid leaking them through logs or unrelated pages;
- preserve rate-limiting/security-header behavior unless intentionally changing it with justification;
- never commit real wedding, guest, email, payment, SMTP, or production database data as fixtures.

When working on email features, do not send real messages during automated tests. Use test doubles or safe local/test configuration.

## Testing and Validation

Follow `CONTRIBUTING.md` and the repository's current CI configuration rather than assuming a test command exists.

For changes that can affect runtime behavior, perform the applicable validation available in the repository. At minimum, verify that Python imports/starts cleanly and that the affected behavior works.

For production/container-impacting changes, use the documented Docker validation when practical:

```bash
docker-compose down
docker-compose up -d --build
docker-compose logs
curl http://localhost:4345/health
```

Do not leave a development or validation container running unnecessarily after the task when the environment expects cleanup.

When applicable, test:

- creating a new wedding;
- behavior with existing persisted data;
- the affected module(s);
- public RSVP behavior for RSVP-related changes;
- email behavior using safe test configuration;
- mobile/responsive layout for UI changes;
- fresh and upgraded database paths for schema changes; and
- container startup/health for deployment changes.

If the repository gains automated tests or CI checks, those checks become part of the definition of done. Do not rely indefinitely on manual testing when an existing automated test covers the behavior.

## CI Failure Handling

When CI fails:

1. inspect the failing job and find the first meaningful error;
2. reproduce the same command/environment locally when possible;
3. determine whether the failure is deterministic, flaky, environmental, or caused by the proposed change;
4. fix deterministic/root-cause failures;
5. rerun affected validation after the fix; and
6. rerun a job without a code change only when there is evidence the failure is transient or environmental.

Do not repeatedly rerun deterministic failures hoping for a green attempt.

## Flask/Jinja Changes

When changing templates or routes:

- keep Jinja2 structure and indentation consistent with surrounding templates;
- preserve form field names expected by route handlers;
- preserve CSRF fields/tokens where required;
- verify redirects and flash/error messages on both success and failure paths;
- avoid duplicating business logic in templates when it belongs in Python;
- test empty, missing, and malformed input states rather than only the happy path; and
- check responsive/mobile behavior for visible UI changes.

## Backup and Restore Safety

Backup and restore code is data-loss-sensitive.

When modifying `scripts/backup.sh` or related behavior:

- never overwrite the only copy of a database without a verified backup;
- validate source and destination paths;
- fail loudly on incomplete operations;
- avoid printing secrets or sensitive data to logs; and
- test using disposable sample data, never a real user's wedding database.

## Documentation

Update user and operator documentation when behavior, setup, configuration, deployment, migrations, or troubleshooting changes.

Relevant documentation may include:

- `README.md`
- `INSTALL.md`
- `QUICKSTART.md`
- `ONBOARDING_GUIDE.md`
- `TROUBLESHOOTING.md`
- `CHANGELOG.md`
- `docs/WIKI.md`
- deployment and reverse-proxy guides under `docs/`

Do not document functionality as working unless it is implemented and verified.

## Scope and Hard Stops

Fix errors you encounter when the repair is reasonably related to the code or validation being touched. If resolving a discovered problem would require a large unrelated redesign, destructive migration, security-policy decision, or substantial expansion of scope:

- stop before making speculative broad changes;
- report the problem completely;
- explain why it exceeds the current task; and
- identify the safest next action.

Do not silently continue past a known correctness, data-loss, security, migration, or CI problem.

## Pre-Commit Review

Before committing, verify:

- [ ] The requested behavior is implemented.
- [ ] Relevant documentation and existing implementation were reviewed first.
- [ ] Security/CSRF/auth boundaries remain correct.
- [ ] No real wedding/guest/user data or secrets were added.
- [ ] Model changes include a reviewed migration when required.
- [ ] Existing-data upgrade behavior was considered for persistence changes.
- [ ] Relevant automated/manual validation was run.
- [ ] Docker/container health was checked for applicable deployment/runtime changes.
- [ ] Mobile/responsive behavior was checked for applicable UI changes.
- [ ] `git status` contains no runtime database, backup, log, cache, or other unintended artifact.
- [ ] The final diff contains no unrelated changes, debug code, credentials, or accidental generated files.
- [ ] Documentation and changelog updates were made when required.

## Definition of Done

Do not report a task as complete until:

- the requested behavior is implemented;
- applicable validation has passed;
- schema/data-migration implications have been reviewed where applicable;
- security and sensitive-data implications have been reviewed where applicable;
- the final diff has been reviewed;
- no unintended binary/runtime/generated artifacts are included;
- the branch's relationship to current `main` has been considered;
- known limitations or checks that could not be performed are explicitly reported; and
- no known failure is being hidden behind a suppression, bypass, skipped validation, or unsupported claim.

A concise completion report should state what changed, what validation actually ran, its result, and any remaining limitation.