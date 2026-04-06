# Changelog

All notable changes to the Wedding Organizer are documented in this file.

---

## [2.8.0] - 2026-04-06 — Beautiful Personalized Print Templates

### Changed
- **Redesigned all 5 print templates** (timeline, seating chart, emergency contacts, vendor contacts, shot list) with elegant wedding-appropriate styling
- **Wedding branding integration** - print templates now use the couple's custom colors (primary, secondary, accent), fonts, and monogram from Wedding Branding settings
- **Elegant typography** - switched from generic Georgia to Palatino/Optima font stack with proper letter-spacing and hierarchy
- **Decorative elements** - ornamental dividers, accent-colored borders, monogram display in headers
- **Contextual design** - seating chart styled as guest-facing display ("Please Find Your Seat"), shot list as a working photographer checklist, emergency contacts as a quick-reference card layout
- **Smart defaults** - templates look beautiful even without branding configured (warm gold/champagne palette)
- **Consistent footer** - simplified footers show couple names and date without "Printed from" branding

---

## [2.7.0] - 2026-04-06 — Server-Side PDF Generation

### Added
- **WeasyPrint PDF generation** for all 8 print-ready pages (timeline, vendor contacts, shot list, emergency contacts, seating chart, inventory bins, inventory all, inventory labels)
- **"Download PDF" button** on all print pages alongside existing "Print" button
- **`?format=pdf` query parameter** on all print routes - append to any print URL to get a PDF download
- WeasyPrint system dependencies in Dockerfile (libpango, libcairo, libharfbuzz, libgdk-pixbuf)

### Changed
- Updated `requirements.txt` with `weasyprint==62.3`
- Updated Dockerfile to install system libraries needed for PDF rendering
- All print routes now use `_render_or_pdf()` helper for consistent HTML/PDF output

---

## [2.6.0] - 2026-04-06 — Comprehensive Import/Export System

### Added

#### CSV Imports (4 modules)
- **Guest CSV import** with file upload - bulk add guests from spreadsheets
- **Vendor CSV import** - batch add vendors from CSV files
- **Task CSV import** - import task lists with flexible date parsing (YYYY-MM-DD, MM/DD/YYYY, etc.)
- **Budget CSV import** - import expenses with auto-creation of budget if needed
- **Sample CSV templates** - downloadable template files with example data for guests, vendors, tasks, and budget
- **"Download Template" buttons** on guests, vendors, tasks, and budget pages

#### CSV Exports (9 new modules)
- **Bridal party export** - name, role, side, contact, responsibilities, gift tracking
- **Registry export** - items, stores, prices, purchase status
- **Music/playlist export** - songs, artists, moments, Spotify URLs
- **Photography shot list export** - categories, descriptions, priority, capture status
- **Attire export** - garments, designers, sizes, fittings
- **Gift tracking export** - events, givers, values, thank-you status
- **Flowers/decor export** - arrangements, recipients, quantities, costs
- **Speeches/toasts export** - speakers, types, order, duration
- **Wedding favors export** - descriptions, quantities, costs, assembly status

#### Full Wedding JSON Export/Import
- **Export entire wedding** as a single JSON file from the dashboard - includes ALL modules (ceremony, reception, honeymoon, guests, vendors, budget, tasks, bridal party, registry, music, photos, flowers, attire, gifts, speeches, favors, tips, contingency plans, accommodations, timeline, hair/makeup, guest groups, inventory, seating tables, vendor communication logs, and more)
- **Import wedding from JSON** - restore or transfer a complete wedding plan between instances
- **Export/Import buttons** on the wedding dashboard

#### UI Updates
- Export CSV buttons added to 9 additional module pages (bridal party, registry, music, photos, attire, gifts, flowers, speeches, favors)
- Import CSV buttons with inline file upload on guests, vendors, tasks, and budget pages
- All import buttons use hidden file inputs for clean UX - click to browse, auto-submit on selection

---

## [2.5.0] - 2026-04-06 — Installation Docs, Deployment Guides & Infrastructure

### Added
- **`.env.example`** - Environment configuration reference with all supported variables and examples for Gmail, Outlook, SendGrid, and Amazon SES
- **`INSTALL.md`** - Comprehensive installation guide covering Docker, local development, production deployment, database backups, and updating
- **`docs/DEPLOYMENT-GUIDES.md`** - Platform-specific deployment guides for Unraid (3 methods), Proxmox (LXC, VM, bare metal), Synology NAS, Kubernetes (full manifests), Raspberry Pi, VPS (DigitalOcean/Linode/Hetzner), TrueNAS Scale, and Docker Swarm
- **`docs/REVERSE-PROXY.md`** - Ready-to-use reverse proxy configurations for Nginx + Let's Encrypt, Traefik (automatic SSL), Caddy (simplest SSL), and Cloudflare Tunnel
- **`scripts/backup.sh`** - Automated database backup and restore script with rotation (keeps last 30 backups), cron-ready
- **`CONTRIBUTING.md`** - Developer guide with local setup, project structure, code style, database migration guidance, and PR process
- **`/health` endpoint** - Returns application and database health status (200 healthy / 503 unhealthy) for monitoring and container orchestration
- **`HEALTHCHECK` in Dockerfile** - Container health monitoring that polls `/health` every 30 seconds
- **Multi-architecture Docker build instructions** - Documentation for building images for amd64, arm64, and armv7 using Docker Buildx
- **Startup SECRET_KEY warning** - Application logs a warning with fix instructions when running with a default insecure secret key

### Changed
- **`docker-compose.yml`** - Added optional `.env` file support (`required: false` for backwards compatibility), SECRET_KEY now reads from environment with fallback
- **`app.py`** - Activated `python-dotenv` (`load_dotenv()`) so `.env` files work for both Docker and local development
- **`README.md`** - Updated Quick Start with git clone and `.env` setup, reorganized documentation section with links to all new guides, added backup instructions
- **`QUICKSTART.md`** - Updated email section to use `.env` instead of editing `docker-compose.yml`, added setup instructions for Outlook, SendGrid, and Amazon SES, updated help links
- **`TROUBLESHOOTING.md`** - Added sections for health check usage, SECRET_KEY warning resolution, and backup/restore documentation
- **`docs/WIKI.md`** - Updated project structure to include new files and directories
- **`.gitignore`** - Added `backups/` directory

---

## [2.4.0] - 2026-03-04 — Social Group Tagging for Smarter Seating

### Added
- **Social Groups field** on guest profiles (comma-separated tags like "Church Group, Work Colleagues")
- **GuestGroup model** with name, color, seat_together flag, and priority (1-10)
- **Group management page** (`/wedding/<id>/guests/groups`): create, delete, bulk-assign guests
- **14 suggested group types**: Church, Work, College, Neighbors, Sports Team, Book Club, etc.
- **Orphan tag detection**: tags on guests without a corresponding group definition show quick-create buttons
- **Remove individual guests** from a group via the group card UI
- **Affinity scoring** in auto-assign algorithm: clusters guests sharing social tags at the same table
- **Group priority levels** (1-10) control clustering strength
- **Same-side bonus**: guests from the same wedding side get a slight affinity boost during table assignment
- Social group tags displayed on seating chart table detail cards and unassigned guest list

### Changed
- Auto-assign algorithm now selects tables by highest affinity score rather than first-fit
- Guest add and edit forms include social groups input
- More Modules page includes Guest Groups link

---

## [2.3.0] - 2026-03-04 — Comprehensive Seating Chart Builder

### Added
- **Table management**: add/edit/delete individual tables or bulk-create up to 50 at once
- **9 table presets**: 48"/60"/72"/84" round, 6ft/8ft banquet, King's table, sweetheart table, custom
- **6 table roles**: head table, sweetheart, King's, VIP/family, kids, general guest
- **Visual floor plan** with drag-and-drop table positioning (positions saved via AJAX)
- **Table shape visualization**: round, rectangular, square, oval, serpentine
- **Color-coded table roles** on floor plan and detail cards
- **Seating preferences system**: define "seat together" or "keep apart" constraints between any two guests
- Priority levels (1-10) and notes field for each preference
- **Constraint violation detection** displayed on seating chart page
- **Auto-assign algorithm** using Union-Find (disjoint sets):
  - Groups guests by household
  - Automatically groups plus-ones with their hosts
  - Merges groups from "together" preferences
  - Honors "apart" constraints by preventing co-assignment
  - Assigns kids to kids tables, family to VIP tables
  - Two strategies: "Balanced" (fill evenly) and "Grouped" (keep sides together)
  - Reports unplaceable guests when capacity is insufficient
- **Bulk assign** with guest selection checkboxes and table dropdown
- **Per-guest assignment dropdown** in unassigned guest list
- **Clear all assignments** button with confirmation
- **Unassign individual guests** from table detail cards
- **Stats dashboard**: tables, total seats, attending, assigned, unassigned, spare seats
- **Print seating chart** view for day-of reference
- **SeatingPreference model** (guest_id, other_guest_id, preference_type, priority, notes)
- **TABLE_SIZE_REFERENCE** and **TABLE_ROLES** reference data

### Changed
- SeatingTable model now includes `table_size` and `table_role` fields
- Seating chart template completely rewritten from scratch

---

## [2.2.0] - 2026-03-04 — 100 Wedding Planner Improvements

### Added — New Modules & Features
- **Online RSVP Portal** with public token-based access (no login required for guests)
- **Shareable read-only wedding dashboard** via unique token link
- **Vendor communication log** with date, type, and notes tracking
- **Vendor quote comparison** page for comparing quotes side-by-side
- **Speeches & toasts management** with speaker, type, duration, and order
- **Wedding favors tracking** with per-item cost, quantity, assembly status
- **Vow writing workspace** with drafts and version tracking
- **Ceremony script builder** for officiants/self-written ceremonies
- **Budget templates** (small $10k / medium $25k / large $50k wedding presets)
- **Payment schedule** with due dates, amounts, and overdue tracking
- **Processional order visualization** for ceremony lineup
- **Reception calculators**: bar estimator, dance floor size, postage cost
- **Invitation wording templates** with traditional and modern options
- **Stationery checklist** for invitation suite tracking
- **Guest meal summary** report for caterers
- **Music playlist stats**: total duration, genre breakdown, Spotify URL support
- **Calendar view** aggregating all wedding dates and deadlines
- **Activity log** tracking all changes across modules
- **Global search** across guests, vendors, tasks, expenses
- **CSV export** for guests, expenses, and vendors
- **iCal export** for tasks and deadlines
- **Print-ready pages**: timeline, vendor contacts, emergency contacts, photography shot list
- **Hotel welcome bags** tracking for out-of-town guests
- **Emergency contacts** page for day-of coordination

### Added — Template & UI Enhancements
- Enhanced task form with priority levels and category selection
- Task filtering by status, priority, and category
- Vendor notes page for per-vendor documentation
- Budget view shows category breakdowns with visual bars
- Guest list shows dietary restrictions and meal choices inline
- Music list includes genre, artist, and request source fields
- Reception edit form includes floor plan and layout options

### Changed
- All templates updated for consistent navigation and styling
- Dashboard shows richer statistics across all modules
- More Modules page reorganized with all new module links
- Base template includes activity logging hooks

---

## [2.1.0] - 2026-03-03 — Planning Milestones & Financial Tracking

### Added
- Planning milestones with target dates and completion tracking
- Contingency plans for weather, vendor no-shows, and emergencies
- Tipping tracker with suggested amounts and actual tips paid
- Gift tracking with thank-you note status
- Vendor contract detail fields (contract date, signed status, terms)
- Category budget limits with over-budget warnings
- Hotel welcome bags module for guest hospitality

---

## [2.0.0] - 2026-03-03 — Covered-By Field & Budget Aggregation

### Added
- "Covered by" field on expenses for tracking items paid by parents, sponsors, etc.
- Cross-module cost aggregation: vendor deposits, attire costs, and gifts roll into budget totals

### Fixed
- Budget tracking now correctly sums costs across all modules, not just direct expenses

---

## [1.9.0] - 2026-03-03 — Individual Timelines

### Added
- Per-participant timeline/itinerary views showing each person's schedule for the day
- Automatic timeline generation based on ceremony and reception events

---

## [1.8.0] - 2026-03-02 — Comprehensive Module CRUD

### Added
- Complete CRUD operations for all 13 modules
- Ceremony timeline builder with second-level precision
- Reception timeline with music and activity scheduling

---

## [1.7.0] - 2026-03-02 — User Accounts & Roles

### Added
- User account system with three role types: professional planner, friend helper, self-planner
- Role-based access and UI customization
- Production-ready Docker configuration with built-in SQLite

### Fixed
- Missing routes and dead code cleanup
- Security issues in form handling

---

## [1.0.0] - Initial Release

### Added
- 13 core wedding planning modules
- Traditional elements library (15+ ceremonies and customs)
- Email reminder system for task deadlines
- Docker-based deployment
- Multi-wedding support
