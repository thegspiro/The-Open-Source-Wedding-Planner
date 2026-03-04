# Wedding Organizer Training Guide

Step-by-step instructions for using all features of the Wedding Organizer.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Your Guest List](#managing-your-guest-list)
3. [Setting Up Social Groups](#setting-up-social-groups)
4. [Building Your Seating Chart](#building-your-seating-chart)
5. [Using the Auto-Assign Algorithm](#using-the-auto-assign-algorithm)
6. [Seating Preferences (Together/Apart)](#seating-preferences-togetherpart)
7. [Managing Your Budget](#managing-your-budget)
8. [Vendor Management](#vendor-management)
9. [Task Management & Reminders](#task-management--reminders)
10. [RSVP Portal for Guests](#rsvp-portal-for-guests)
11. [Ceremony Planning](#ceremony-planning)
12. [Reception Planning](#reception-planning)
13. [Printing & Exporting](#printing--exporting)
14. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### Creating a Wedding
1. Open the application at `http://localhost:5000`
2. Click **"Add New Wedding"**
3. Enter couple names, wedding date, and contact email
4. Complete the 3-step setup:
   - Step 1: Number of people getting married
   - Step 2: Details for each person (name, title, side label)
   - Step 3: Terminology preferences
5. You'll arrive at your **Dashboard** — the central hub for all planning

### Navigating the Application
- **Dashboard**: Overview stats and quick links
- **Top navigation**: Direct links to major modules
- **More Modules**: Access all 20+ features from one page
- **Back buttons**: Every page has navigation back to its parent

---

## Managing Your Guest List

### Adding Guests
1. Go to **Guests** from the dashboard
2. Click **"Add Guest"**
3. Fill in:
   - **Name** (required)
   - **Email, Phone, Address** (optional)
   - **Guest Type**: family, friend, colleague, or other
   - **Side**: Which person's guest (e.g., "Bride's side", "Groom's side", "Both")
   - **Dietary Restrictions**: Any food allergies or preferences
   - **Household Group**: e.g., "Smith Family" — groups families together for seating
   - **Social Groups**: e.g., "Church Group, Work Colleagues" — comma-separated list
4. Click **"Add Guest"**

### Editing Guests
1. Click the **Edit** button next to any guest
2. Update any field
3. Additional fields available when editing:
   - **RSVP Status**: pending, accepted, declined
   - **Meal Choice**: specific meal selection
   - **Invitation Sent**: checkbox
   - **Attending Ceremony / Reception**: separate checkboxes
   - **Plus One**: mark as plus-one and link to host guest
   - **Gift Tracking**: received, description, thank-you sent
4. Click **"Save Changes"**

### Tracking RSVPs
- Set each guest's RSVP status to **accepted**, **declined**, or **pending**
- The dashboard shows RSVP summary counts
- Only **accepted** guests with **attending reception** checked are included in seating

---

## Setting Up Social Groups

Social groups help the seating algorithm seat guests who know each other together.

### Creating Groups
1. Go to **More Modules > Guest Groups** (or **Seating Chart > Social Groups**)
2. In the "Create Group" form:
   - **Group Name**: Type a name or select from suggestions (Church, Work, College, etc.)
   - **Priority** (1-10): How strongly to cluster this group (8-10 for close friends, 3-5 for loose associations)
   - **Color**: Visual identifier for the group
   - **Seat Together**: Check to have the algorithm try to seat members together. Uncheck for label-only groups.
   - **Notes**: Optional description
3. Click **"Create Group"**

### Tagging Guests
**Method 1 — From the Group page:**
1. Find the group card
2. Click **"Add guests to this group"** (expandable section)
3. Check the guests you want to add
4. Click **"Add Selected"**

**Method 2 — From the Guest edit page:**
1. Edit a guest
2. In the **Social Groups** field, type group names separated by commas
3. Example: `Church Group, Book Club, Neighbors`
4. Save changes

### Orphan Tags
If a guest has a tag that doesn't match any defined group, it appears under **"Tags Without Group Definitions"**. Click the **"+ Tag Name"** button to instantly create a group for it.

### Best Practices for Groups
- **Church/Religious**: Priority 7-8. These guests often don't know many others.
- **Work Colleagues**: Priority 5-6. Good for mixing departments.
- **College Friends**: Priority 8-9. Strong bonds make fun tables.
- **Extended Family**: Priority 6-7. Keep family branches together.
- **Neighbors**: Priority 3-4. Nice but not critical.

---

## Building Your Seating Chart

### Creating Tables

**Quick Add (Single Table):**
1. Go to **Seating Chart**
2. In the "Quick Add" panel:
   - Select a **Table Preset** (e.g., "60 inch Round, seats 8") or choose Custom
   - Optionally enter a **Custom Name** (e.g., "Rose Table", "Table 1")
   - Choose **Shape**: round, rectangular, square, oval, serpentine
   - Set **Capacity**: number of seats
   - Choose **Role**: guest, head table, sweetheart, King's, VIP, kids
3. Click **"Add Table"**

**Bulk Setup:**
1. In the "Bulk Setup" panel:
   - Set **Number of Guest Tables** (e.g., 10)
   - Choose **Table Type** preset
   - Optionally check **Include Head Table** and set its capacity
   - Optionally check **Include Kids Table** and set its capacity
2. Click **"Create Tables"**

### Arranging the Floor Plan
1. Tables appear as cards on the floor plan canvas
2. **Click and drag** any table to reposition it
3. Positions save automatically when you release the mouse
4. Table cards show:
   - Table number
   - Custom name (if set)
   - Occupancy count (e.g., "6/8")
   - Color coding by role

### Assigning Guests Manually

**Per-guest assignment:**
1. Scroll to the **"Unassigned Guests"** section
2. For each guest, select a table from the dropdown
3. Click **"Go"**

**Bulk assignment:**
1. In the **"Bulk Assign"** box above the unassigned list:
2. Check the guests you want to assign
3. Select a destination table
4. Click **"Assign Selected"**

**Unassigning a guest:**
1. In the **Table Details** section, find the guest
2. Click the **×** button next to their name

---

## Using the Auto-Assign Algorithm

### Running Auto-Assign
1. Ensure you have **tables created** and **guests with accepted RSVPs**
2. In the "Auto-Assign Guests" section:
   - Choose a **Strategy**:
     - **Balanced**: Fills tables evenly across all tables
     - **Grouped**: Tries to keep guests from the same side together
   - Check **"Only assign unassigned guests"** to preserve existing assignments
3. Click **"Auto-Assign"** and confirm

### What the Algorithm Does
1. Groups guests by **household** (families stay together)
2. Pairs **plus-ones** with their hosts
3. Merges groups from **"seat together" preferences**
4. Calculates **affinity scores** based on shared **social group tags**
5. Assigns groups to the table with the **highest affinity score**
6. Respects **"keep apart" constraints**
7. Routes **kids to kids tables** and **family to VIP tables** when available

### After Auto-Assign
- Review the results in the Table Details section
- Check for **constraint violations** (shown in red at the top)
- Manually adjust any placements that don't look right
- Use **"Clear All Assignments"** to start over if needed

---

## Seating Preferences (Together/Apart)

### Adding Preferences
1. Go to **Seating Chart > Preferences (Together/Apart)**
2. Fill in the form:
   - **Guest 1**: Select from dropdown
   - **Type**: "Seat Together" or "Keep Apart"
   - **Guest 2**: Select from dropdown
   - **Priority** (1-10): How important this constraint is
   - **Notes**: Reason (e.g., "married couple", "exes — awkward", "best friends")
3. Click **"Add Preference"**

### How Preferences Affect Seating
- **Seat Together**: The auto-assign algorithm merges these guests into a single group, guaranteeing they're at the same table
- **Keep Apart**: The algorithm will never place these guests at the same table. Violations are flagged on the seating chart.

### Tips
- Use priority 9-10 for absolute requirements (spouses, partners)
- Use priority 5-7 for strong preferences (close friends)
- Use priority 1-3 for nice-to-haves
- Check the constraint violations section after auto-assign to catch any issues

---

## Managing Your Budget

### Setting Up
1. Go to **Budget** from the dashboard
2. Set your **Total Budget** amount
3. Optionally apply a **Budget Template**:
   - Small Wedding ($10,000): Intimate 50-guest budget
   - Medium Wedding ($25,000): Standard 150-guest budget
   - Large Wedding ($50,000): Grand 250-guest budget

### Adding Expenses
1. Click **"Add Expense"**
2. Enter: category, description, estimated cost, actual cost, paid amount
3. Optionally set **"Covered By"** if someone else is paying (e.g., "Bride's parents")

### Category Limits
- Set per-category budget limits
- The budget page shows warnings when categories exceed their limits
- Visual bars show spending progress for each category

### Payment Schedule
- Track upcoming payments with due dates
- View overdue payments highlighted in red
- Mark payments as paid when completed

---

## Vendor Management

### Adding Vendors
1. Go to **Vendors** from the dashboard
2. Click **"Add Vendor"**
3. Enter: name, category, contact info, website, deposit, total cost

### Communication Log
1. Click on a vendor to view details
2. Go to **"Communication Log"**
3. Add entries with date, type (email/phone/meeting/other), and notes
4. Keep a complete history of all vendor interactions

### Quote Comparison
1. Go to **Vendors > Quote Comparison**
2. Add quotes from different vendors for the same service
3. Compare side-by-side: price, what's included, notes
4. Make informed decisions

---

## Task Management & Reminders

### Adding Tasks
1. Go to **Tasks** from the dashboard
2. Click **"Add Task"**
3. Enter: title, description, due date, priority (high/medium/low), category
4. Tasks appear in the task list sorted by due date

### Email Reminders
- Reminders are sent **3 days before** the due date
- Requires SMTP configuration (see QUICKSTART.md)
- Only tasks with due dates trigger reminders

### Filtering Tasks
- Filter by **Status**: pending, in progress, completed
- Filter by **Priority**: high, medium, low
- Filter by **Category**: venue, catering, decor, etc.

---

## RSVP Portal for Guests

### Setting Up
1. The wedding's `public_token` generates a shareable link
2. Share the link: `http://yoursite.com/rsvp/<token>`
3. Enable RSVP in wedding settings

### Guest Experience
1. Guest visits the RSVP link
2. Enters their name to find their invitation
3. Selects accept or decline
4. Provides meal choice and dietary restrictions
5. Sees confirmation

### Monitoring Responses
- RSVP statuses update on the guest list in real-time
- Dashboard shows running RSVP counts
- Filter guest list by RSVP status

---

## Ceremony Planning

### Using Templates
1. Go to **Ceremony** setup
2. Choose ceremony type: Religious, Secular, Spiritual, Civil
3. Browse templates:
   - Catholic (60 min), Jewish (45 min), Protestant (30 min), Hindu (120 min)
   - Modern Secular (25 min), Simple Secular (15 min), Courthouse (10 min)
4. Preview the full timeline before applying
5. Customize venue, timing, and officiant details

### Vow Writing
1. Go to **More Modules > Vow Writing**
2. Write and save drafts
3. Track versions over time

### Ceremony Script
1. Go to **More Modules > Ceremony Script**
2. Build the full script section by section
3. Useful for self-officiated ceremonies or to share with your officiant

---

## Reception Planning

### Calculators
Access from **More Modules > Reception Calculators**:
- **Bar Estimator**: Calculates drink quantities based on guest count and duration
- **Dance Floor Size**: Recommends floor dimensions based on guest count
- **Postage Calculator**: Estimates invitation mailing costs

### Music Management
- Add songs with title, artist, genre
- Track Spotify URLs for playlist building
- View duration stats and genre breakdown
- Mark songs as requested by specific guests

---

## Printing & Exporting

### Print Pages
Access from the seating chart or More Modules:
- **Print Timeline**: Full ceremony + reception schedule
- **Print Seating**: Table assignments for display boards
- **Print Vendor Contacts**: Quick-reference sheet for day-of
- **Print Emergency Contacts**: Critical numbers for coordinators
- **Print Shot List**: Photography must-have shots

**Tip:** Use Chrome or Firefox, set margins to "Minimum," and enable "Background graphics" for best results.

### CSV Export
Export from the respective module pages:
- **Guest list**: All fields including RSVP, dietary, groups
- **Expenses**: Categories, amounts, paid status
- **Vendors**: Contact info and contract details

### iCal Export
- Export tasks with due dates as `.ics` file
- Import into Google Calendar, Apple Calendar, or Outlook

---

## Tips & Best Practices

### Guest Management
- Enter **household groups** for families — the seating algorithm keeps them together automatically
- Add **social groups** early — it makes auto-assign much smarter
- Track dietary restrictions for **every guest** — your caterer will thank you
- Use the **meal summary** page when sending final counts to the caterer

### Seating Strategy
1. **Start with groups**: Define social groups and tag guests first
2. **Set preferences**: Add must-together (couples) and must-apart (exes) constraints
3. **Create tables**: Use bulk setup for speed, then customize
4. **Run auto-assign**: Let the algorithm do the heavy lifting
5. **Review and adjust**: Fine-tune manually after auto-assign
6. **Check violations**: Fix any flagged constraint violations

### Budget Management
- Use the **"Covered By"** field to track what others are paying for
- Set **category limits** early to avoid overspending
- Update **actual costs** as quotes come in (estimates are just starting points)
- Check the **payment schedule** weekly for upcoming due dates

### Vendor Management
- Log **every communication** — it's invaluable if disputes arise
- Use **quote comparison** before committing to any vendor
- Track **contract dates** and **signed status** so nothing falls through

### Timeline Tips
- Build your ceremony timeline **6+ months out** and refine as details solidify
- Allow **buffer time** between events (15-30 min between ceremony end and reception start)
- Share the printed timeline with your **wedding party, vendors, and coordinator**

### Day-Of Preparation
- Print the **seating chart** 2-3 days before (after final RSVP deadline)
- Print **vendor contacts** and **emergency contacts** for the coordinator
- Export the **timeline** and share with all vendors
- Have the **photography shot list** ready for your photographer
