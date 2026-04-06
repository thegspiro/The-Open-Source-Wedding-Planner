# Contributing to Wedding Organizer

Thank you for your interest in contributing! This guide will help you get set up for development.

## Getting Started

### Prerequisites

- Python 3.10 or later
- Git
- Docker and Docker Compose (for testing production builds)

### Local Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment config
cp .env.example .env
# Edit .env and set SECRET_KEY to any value for development

# Run the application
python app.py
```

Access at: **http://localhost:5000**

### Running with Docker

```bash
docker-compose up -d --build
```

## Project Structure

```
wedding-organizer/
├── app.py              # All Flask routes (~5,100 lines)
├── models.py           # SQLAlchemy ORM models (~1,200 lines)
├── security.py         # CSRF, security headers, rate limiting
├── email_service.py    # SMTP email sending
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container definition
├── docker-compose.yml  # Container orchestration
├── static/css/         # Stylesheets
├── templates/          # Jinja2 templates (100+ files)
│   ├── base.html       # Base layout and navigation
│   └── .../            # Module-specific templates
├── migrations/         # Flask-Migrate (Alembic) migration files
├── scripts/            # Utility scripts (backup, etc.)
├── docs/               # Documentation
└── instance/           # SQLite database (auto-created)
```

## Making Changes

### Code Style

- **Python:** Follow PEP 8 conventions
- **Templates:** Use Jinja2 with consistent indentation (2 spaces for HTML)
- **CSS:** Vanilla CSS, no preprocessors
- **JavaScript:** Vanilla JS, no frameworks

### Database Changes

The application uses SQLite via SQLAlchemy with **Flask-Migrate** (Alembic) for schema migrations. If you add or modify columns in models:

1. Add the column to the model in `models.py`
2. Generate a migration:
   ```bash
   flask db migrate -m "Add column_name to table_name"
   ```
3. Review the generated migration file in `migrations/versions/` to ensure it is correct
4. Apply the migration:
   ```bash
   flask db upgrade
   ```
5. Include the generated migration file in your PR
6. Test with both a fresh database and an existing one

> **Note:** The app still calls `db.create_all()` on startup for dev convenience (so fresh databases work without running migrations), but existing databases should be upgraded with `flask db upgrade`. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#new-columns-not-appearing-after-code-update) if you encounter schema issues.

### Migrations Workflow

The project uses [Flask-Migrate](https://flask-migrate.readthedocs.io/) (an Alembic wrapper) to manage database schema changes. Migration files live in `migrations/versions/`.

| Command | Purpose |
|---------|---------|
| `flask db migrate -m "description"` | Auto-generate a migration from model changes |
| `flask db upgrade` | Apply all pending migrations to the database |
| `flask db downgrade` | Revert the most recent migration |
| `flask db current` | Show the current migration revision |
| `flask db history` | List all migration revisions |

**Tips:**
- Always review the auto-generated migration before committing -- Alembic does not detect every change (e.g., renaming columns requires manual edits to the migration).
- Each PR that changes `models.py` should include the corresponding migration file.
- Do not modify or squash existing migration files that have already been merged -- create new migrations instead.

### Testing Changes

```bash
# Test with Docker (clean build)
docker-compose down
docker-compose up -d --build
docker-compose logs -f

# Verify health check
curl http://localhost:5000/health
```

Test the following when applicable:
- Create a new wedding and verify all modules
- Test with existing data (don't delete `instance/wedding_organizer.db`)
- Test the RSVP portal with a public token
- Check mobile/responsive layout in browser dev tools

## Submitting a Pull Request

1. **Fork** the repository
2. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes** and commit with clear messages
4. **Push** your branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request** against `main`

### PR Guidelines

- Keep PRs focused - one feature or fix per PR
- Include a clear description of what changed and why
- If adding database columns, include the generated Flask-Migrate migration file
- Test on both fresh and existing databases
- Update documentation if relevant (README, QUICKSTART, TROUBLESHOOTING)

## Areas Where Help is Needed

- **Database migrations** - Improving and extending Flask-Migrate usage
- **Platform templates** - Unraid Community App template, Helm chart
- **Testing** - Adding unit and integration tests
- **Accessibility** - Improving ARIA labels and keyboard navigation
- **Localization** - i18n support for multiple languages
- **Documentation** - Improving guides, adding screenshots

## Questions?

Open an issue on the repository for questions, bug reports, or feature requests.
