# Wedding Organizer Wiki

Comprehensive documentation for all features and modules.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Core Modules](#core-modules)
3. [Seating Chart Builder](#seating-chart-builder)
4. [Social Groups & Guest Clustering](#social-groups--guest-clustering)
5. [Auto-Assign Algorithm](#auto-assign-algorithm)
6. [RSVP Portal](#rsvp-portal)
7. [Budget System](#budget-system)
8. [Print & Export](#print--export)
9. [Activity Logging](#activity-logging)
10. [Data Model Reference](#data-model-reference)

---

## Architecture Overview

### Technology Stack
- **Backend**: Python 3 / Flask
- **Database**: SQLite via SQLAlchemy ORM
- **Frontend**: Jinja2 templates, vanilla CSS, vanilla JavaScript
- **Deployment**: Docker / Docker Compose
- **Email**: SMTP (optional, for task reminders)

### Project Structure
```
wedding-organizer/
├── app.py                  # All Flask routes (~4000+ lines)
├── models.py               # SQLAlchemy models and reference data
├── templates/              # Jinja2 HTML templates
│   ├── base.html           # Base layout with nav
│   ├── wedding_dashboard.html
│   ├── ceremony/           # Ceremony module templates
│   ├── reception/          # Reception module templates
│   ├── guests/             # Guest management templates
│   ├── seating/            # Seating chart templates
│   ├── budget/             # Budget module templates
│   ├── vendors/            # Vendor management templates
│   ├── tasks/              # Task management templates
│   ├── print/              # Print-ready templates
│   └── ...                 # Additional module templates
├── static/css/style.css    # All styles
├── instance/               # SQLite database (auto-created)
├── docker-compose.yml
├── Dockerfile
└── docs/                   # Documentation
```

### Key Design Decisions
- **Single-file routes**: All routes live in `app.py` for simplicity. Each route is a standalone function.
- **No JavaScript frameworks**: Vanilla JS only, for drag-and-drop and AJAX. No build step required.
- **SQLite**: Zero-configuration database. Suitable for 1-2 concurrent planners per wedding.
- **No authentication on wedding data**: Each wedding is accessed by its numeric ID. The RSVP portal uses token-based public access.

---

## Core Modules

### 1. People
Manage individuals getting married. Supports 2+ people. Each person has:
- Name, title, contact info
- Side label (used for guest association)
- Display order (affects processional, forms)

### 2. Dashboard
Central hub showing:
- Wedding date and countdown
- Guest count summary (invited, accepted, declined, pending)
- Budget summary (total, spent, remaining)
- Upcoming tasks
- Quick links to all modules

### 3. Ceremony
- Venue details, officiant info
- Timeline builder with second-level precision
- Ceremony templates (Catholic, Jewish, Protestant, Hindu, secular, civil)
- Vow writing workspace
- Ceremony script builder
- Processional order visualization

### 4. Reception
- Venue, catering, music, timeline
- Expected guest count
- Floor plan and layout options
- Calculators: bar estimator, dance floor size, postage cost
- Seating chart (see dedicated section below)

### 5. Guests
- Full guest list with RSVP tracking
- Fields: name, email, phone, address, guest type, side, dietary restrictions, meal choice
- Household grouping (e.g., "Smith Family")
- Social group tags (e.g., "Church Group, Work Colleagues")
- Plus-one tracking (is_plus_one, plus_one_of)
- Gift tracking (received, description, thank-you sent)
- Invitation sent tracking
- Attending ceremony / attending reception flags
- Online RSVP portal
- Meal summary report for caterers
- CSV export

### 6. Wedding Party
- Manage attendants with roles and titles
- Processional order visualization
- Gift cost tracking per party member

### 7. Vendors
- Vendor profiles: name, category, contact info, website
- Contract tracking: date, signed status, deposit, total cost
- Communication log: date, type (email/phone/meeting), notes
- Quote comparison: add multiple quotes per vendor category
- Vendor notes page
- CSV export

### 8. Budget
- Total budget setting
- Expenses by category with estimated/actual/paid amounts
- "Covered by" field for items paid by others
- Cross-module aggregation: vendor deposits, attire costs, party gifts
- Category budget limits with over-budget warnings
- Budget templates (small $10k, medium $25k, large $50k)
- Payment schedule with due dates and overdue tracking
- CSV export

### 9. Tasks
- Task management with title, description, due date
- Priority levels: high, medium, low
- Categories: venue, catering, decor, attire, music, photo, flowers, transport, legal, other
- Status: pending, in_progress, completed
- Email reminders (3 days before due date)
- Filter by status, priority, category
- iCal export

### 10. Honeymoon
- Destination and date planning
- Itinerary with activities, times, locations
- Packing list with checked-off items

### 11. Branding
- Wedding colors (primary, secondary, accent)
- Font choices
- Theme/style description
- Mood board notes

### 12. Attire
- Track all wedding outfits
- Fields: person, description, store, price, fitting dates
- Status tracking (ordered, altered, ready)

### 13. Registry
- Gift registry management
- Store links and item tracking
- Status: available, purchased, received

### 14. Additional Features
- **Speeches & Toasts**: speaker, type, duration, order, status
- **Wedding Favors**: item, quantity, cost, assembly status
- **Invitation Wording**: templates and stationery checklist
- **Calendar View**: all dates aggregated
- **Activity Log**: change tracking across modules
- **Global Search**: search guests, vendors, tasks, expenses
- **Hotel Welcome Bags**: for out-of-town guests

---

## Seating Chart Builder

### Overview
The seating chart builder is accessed from **Reception > Seating Chart** or the More Modules page. It provides:

1. **Table Management** — Create tables individually or in bulk
2. **Floor Plan** — Visual drag-and-drop table layout
3. **Guest Assignment** — Manual or automatic guest-to-table assignment
4. **Preferences** — "Seat together" and "keep apart" constraints
5. **Social Groups** — Tag-based clustering (see next section)

### Table Presets

| Preset | Shape | Capacity | Real-World Size |
|--------|-------|----------|----------------|
| 48" Round | Round | 6 | Small cocktail table |
| 60" Round | Round | 8 | Standard banquet round |
| 72" Round | Round | 10 | Large banquet round |
| 84" Round | Round | 12 | Extra-large round |
| 6ft Banquet | Rectangular | 6 | Standard folding table |
| 8ft Banquet | Rectangular | 8 | Long banquet table |
| King's Table | Rectangular | 20 | One long table for all |
| Sweetheart | Round | 2 | Couple-only table |
| Custom | Any | Any | User-defined |

### Table Roles

| Role | Purpose | Auto-Assign Behavior |
|------|---------|---------------------|
| Guest | Standard guest table | Default assignment target |
| Head Table | Wedding party | Prioritized for wedding party |
| Sweetheart | Couple only | Skipped by auto-assign |
| King's | Long communal table | Treated as large guest table |
| VIP / Family | Close family | Family-type guests prioritized |
| Kids | Children's table | Child guests prioritized |

### Table Shapes
Tables can be: **round**, **rectangular**, **square**, **oval**, or **serpentine**. The shape affects the visual icon on the floor plan but not the seating logic.

### Floor Plan
- Tables appear as draggable cards on a fixed-size canvas
- Drag to reposition; positions save automatically via AJAX
- Cards show table number, name, and occupancy (e.g., "6/8")
- Over-capacity tables are highlighted in red

### Manual Assignment
- **Per-guest dropdown**: Each unassigned guest has a table dropdown in the unassigned list
- **Bulk assign**: Select multiple guests via checkboxes, choose a table, assign all at once
- **Unassign**: Click the × button on any guest in a table's detail card

---

## Social Groups & Guest Clustering

### Concept
Social groups represent real-world connections between guests: church friends, work colleagues, college roommates, sports teams, etc. Tagging guests with groups helps the auto-assign algorithm seat people who know each other together.

### How It Works
1. **Tag guests** with comma-separated groups on their profile (e.g., "Church Group, Book Club")
2. **Define groups** on the Guest Groups page with:
   - **Name** (must exactly match the tag text)
   - **Color** (visual indicator on group cards)
   - **Priority** (1-10, higher = stronger clustering preference)
   - **Seat together** flag (on/off — some groups are just labels)
   - **Notes** (e.g., "All from St. Mary's parish")
3. **Auto-assign** uses these tags to calculate affinity scores between guest clusters

### Group Management Page
Located at `/wedding/<id>/guests/groups`:
- **Create groups** with suggested names from a dropdown (14 preset suggestions)
- **View members** of each group
- **Bulk-add guests** to a group via checkbox selection
- **Remove individuals** from a group
- **Orphan tag detection**: if a guest has a tag that doesn't match any defined group, it appears in a "Tags Without Group Definitions" section with one-click group creation

### Suggested Group Types
Church/Religious, Work Colleagues, College Friends, High School Friends, Neighbors, Sports Team, Book Club, Gym/Fitness, Volunteer Group, Parent Friends, Hobby Group, Travel Friends, Online Community, Extended Family Branch

---

## Auto-Assign Algorithm

### Overview
The auto-assign algorithm (`/wedding/<id>/seating/auto-assign`) assigns attending guests to tables using a constraint-satisfaction approach.

### Algorithm Steps

#### Step 1: Identify Attending Guests
Only guests with `rsvp_status = 'accepted'` AND `attending_reception = True` are considered. Optionally, only unassigned guests are included.

#### Step 2: Build Guest Groups (Union-Find)
A Union-Find (disjoint sets) data structure merges guests into groups:
1. **Household groups**: Guests sharing the same `household_group` value are merged
2. **Plus-ones**: A guest and their plus-one are merged into one group
3. **"Together" preferences**: Any "seat together" constraint merges the two guests' groups

#### Step 3: Collect Social Tags per Group
For each merged group, collect all social group tags from member guests. These tags drive affinity scoring.

#### Step 4: Sort Groups by Size
Larger groups are placed first (they have fewer valid table options).

#### Step 5: Place Groups on Tables
For each group, the algorithm:
1. Filters tables with enough remaining capacity
2. Excludes tables where an "apart" constraint would be violated
3. Applies role matching (kids → kids table, family → VIP table)
4. **Scores each candidate table** by affinity:
   - For each group already at the table, count shared social tags
   - Weight by group priority (higher priority = more score)
   - Add same-side bonus (+2) if groups share a wedding side
5. Picks the table with the highest affinity score
6. If no table fits, the group is reported as "could not be placed"

#### Step 6: Strategy Modifiers
- **Balanced**: Fill tables evenly (default)
- **Grouped**: Prefer tables that already have guests from the same wedding side

### Complexity
- Time: O(G × T) where G = number of guest groups, T = number of tables
- For 200 guests and 20 tables: effectively instant

---

## RSVP Portal

### Setup
Each wedding can generate a `public_token` that creates a shareable RSVP link:
```
http://yoursite.com/rsvp/<token>
```

### Guest Experience
1. Guest visits the link
2. Enters their name to find their invitation
3. Selects RSVP status (accept/decline)
4. Optionally provides meal choice and dietary restrictions
5. Sees a confirmation page

### Planner Controls
- Enable/disable RSVP portal
- View RSVP responses on the guest list
- Guest statuses update in real-time

---

## Budget System

### Cross-Module Aggregation
The budget page aggregates costs from multiple sources:
- **Direct expenses**: Items added to the budget module
- **Vendor deposits**: Deposit amounts from vendor contracts
- **Attire costs**: Prices from the attire module
- **Wedding party gifts**: Gift costs from party member profiles

### "Covered By" Field
Expenses can be marked as covered by someone other than the couple (e.g., "Bride's parents", "Groom's family"). These still appear in the total budget but can be filtered to see the couple's actual out-of-pocket cost.

### Category Budget Limits
Set per-category limits (e.g., "Catering: $5,000"). The budget page shows warnings when a category exceeds its limit.

### Payment Schedule
Track upcoming payments with:
- Vendor name
- Amount due
- Due date
- Paid status
- Overdue highlighting for past-due items

---

## Print & Export

### Print-Ready Pages
All accessible from the seating chart or dashboard:
- **Timeline**: Ceremony + reception timeline for day-of coordination
- **Seating Chart**: Table assignments for display
- **Vendor Contacts**: Quick-reference contact sheet
- **Emergency Contacts**: Day-of emergency numbers
- **Photography Shot List**: Required photos checklist

### CSV Export
Available for:
- **Guests**: All guest fields including RSVP, dietary, groups
- **Expenses**: All budget items with categories and amounts
- **Vendors**: Contact info, contract details, amounts

### iCal Export
Export tasks with due dates as `.ics` file for calendar import.

---

## Activity Logging

All significant actions are logged with:
- Timestamp
- Action description
- Module affected

View the activity log at `/wedding/<id>/activity`.

---

## Data Model Reference

### Core Models
| Model | Key Fields | Description |
|-------|-----------|-------------|
| Wedding | couple_names, date, email, public_token | Top-level wedding entity |
| WeddingPerson | name, title, side_label, display_order | Person getting married |
| Ceremony | venue, officiant, start_time | Ceremony details |
| Reception | venue, expected_guest_count, start_time | Reception details |

### Guest Models
| Model | Key Fields | Description |
|-------|-----------|-------------|
| Guest | name, email, rsvp_status, side, guest_type, social_groups, household_group, meal_choice, dietary_restrictions, attending_reception | Individual guest |
| GuestGroup | name, color, priority, seat_together, notes | Named social group definition |

### Seating Models
| Model | Key Fields | Description |
|-------|-----------|-------------|
| SeatingTable | table_number, table_name, capacity, table_shape, table_role, table_size, x_position, y_position | Physical table |
| SeatingPreference | guest_id, other_guest_id, preference_type, priority, notes | Together/apart constraint |

### Financial Models
| Model | Key Fields | Description |
|-------|-----------|-------------|
| Expense | category, description, estimated_cost, actual_cost, paid_amount, covered_by | Budget line item |
| Vendor | name, category, contact_name, email, phone, deposit_amount, total_cost | Service provider |

### Planning Models
| Model | Key Fields | Description |
|-------|-----------|-------------|
| Task | title, due_date, priority, category, status | To-do item |
| TimelineItem | title, start_time, duration_minutes, order | Ceremony/reception schedule item |
| Speech | speaker_name, type, duration_minutes, order | Toast/speech entry |
| Favor | item_name, quantity, cost_per_item, assembly_complete | Wedding favor |

### Reference Data (in models.py)
- `TABLE_SIZE_REFERENCE`: 9 table presets with shape, capacity, dimensions
- `TABLE_ROLES`: 6 table role definitions
- `SUGGESTED_GROUP_TYPES`: 14 social group suggestions
- `CEREMONY_TEMPLATES`: 7 ceremony templates with full timelines
