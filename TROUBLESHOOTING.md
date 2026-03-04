# Troubleshooting Guide

Common issues, edge cases, and their solutions.

---

## Database & Migration Issues

### New columns not appearing after code update

**Symptom:** `OperationalError: no such column` errors after updating to a new version.

**Cause:** SQLAlchemy's `db.create_all()` creates new tables but does **not** add columns to existing tables. If a model gains a new field (e.g., `social_groups` on Guest, `table_role` on SeatingTable), existing databases won't have the column.

**Fix:** Run the migration SQL manually or delete the database to recreate:

```sql
-- Option A: Add missing columns manually
ALTER TABLE guest ADD COLUMN social_groups TEXT;
ALTER TABLE guest ADD COLUMN household_group VARCHAR(100);
ALTER TABLE seating_table ADD COLUMN table_size VARCHAR(50);
ALTER TABLE seating_table ADD COLUMN table_role VARCHAR(20) DEFAULT 'guest';
ALTER TABLE seating_table ADD COLUMN x_position INTEGER DEFAULT 0;
ALTER TABLE seating_table ADD COLUMN y_position INTEGER DEFAULT 0;
```

```bash
# Option B: Delete and recreate (loses all data)
rm instance/wedding_organizer.db
docker-compose restart
```

### Database locked errors

**Symptom:** `OperationalError: database is locked`

**Cause:** SQLite allows only one writer at a time. Concurrent requests during heavy use can cause locking.

**Fix:** This is rare in single-user scenarios. If it persists, restart the container:
```bash
docker-compose restart
```

---

## Seating Chart Issues

### Auto-assign places no guests

**Symptom:** Running auto-assign completes but no guests are assigned.

**Possible causes:**
1. **No attending guests**: Only guests with `rsvp_status = 'accepted'` AND `attending_reception = True` are considered. Check guest RSVP statuses.
2. **"Only unassigned" checked**: If all attending guests are already assigned, nothing happens. Uncheck the option or clear assignments first.
3. **No tables exist**: Tables must be created before auto-assign can work.

### Auto-assign reports "could not be placed"

**Symptom:** Flash message says certain guests could not be placed.

**Cause:** Total table capacity is less than the number of attending guests, or "keep apart" constraints make placement impossible.

**Fix:** Add more tables or increase table capacities. Review "keep apart" preferences for conflicts.

### Floor plan positions not saving

**Symptom:** Dragging tables on the floor plan resets on page reload.

**Cause:** The drag-and-drop uses an AJAX POST to save positions. If the request fails silently (network issue, CSRF, etc.), positions won't persist.

**Fix:** Check browser console for errors. Ensure JavaScript is enabled. Try refreshing and dragging again.

### Constraint violations showing incorrectly

**Symptom:** "Seat Together" violations appear for guests who ARE at the same table.

**Cause:** The violation check compares `assigned_table_id` values. If guests were recently moved, the page may need a refresh.

**Fix:** Refresh the seating chart page.

---

## Reception Calculators

### Calculator shows wrong estimates or errors

**Symptom:** Bar calculator or other reception calculators show 0 or error.

**Cause:** The `expected_guest_count` field on the reception may be `None` (not set). The code defaults to 100 guests as a fallback, but if reception itself doesn't exist, calculators won't load.

**Fix:** Set the expected guest count on the Reception edit page. If the reception module hasn't been created, visit the Reception page first.

**Technical detail:** The fallback chain is:
```python
guest_count = (wedding.reception.expected_guest_count
               if wedding.reception and wedding.reception.expected_guest_count
               else None) or 100
```

---

## Guest Management

### Social group tags not matching group definitions

**Symptom:** The "Tags Without Group Definitions" section shows tags that look the same as defined groups.

**Cause:** Tag matching is exact and case-sensitive. "Church group" and "Church Group" are treated as different tags. Leading/trailing spaces in comma-separated lists also cause mismatches.

**Fix:** Edit the guest's social groups field to ensure exact spelling matches the group name. The system strips whitespace around commas, but the group name itself must match exactly.

### Bulk CSV import missing fields

**Symptom:** Imported guests are missing social_groups, household_group, or other newer fields.

**Cause:** The CSV import expects specific column headers. Newer fields may not be included in older CSV templates.

**Fix:** Ensure CSV headers include: `social_groups`, `household_group`, `meal_choice`, `dietary_restrictions`.

---

## RSVP Portal

### RSVP link not working

**Symptom:** Public RSVP link returns 404 or shows "RSVP Disabled."

**Cause:**
1. RSVP must be enabled on the wedding settings.
2. The token in the URL must match the wedding's `public_token`.

**Fix:** Check that the wedding has a valid `public_token` and that RSVP is enabled.

### Guest not found on RSVP portal

**Symptom:** Guest enters their name but the portal says "not found."

**Cause:** Name matching is case-insensitive but must be an exact match. Nicknames, middle names, or spelling variations won't match.

**Fix:** Advise guests to enter their name exactly as it appears on the invitation. The planner can also pre-populate email addresses for lookup.

---

## Email Reminders

### Reminders not sending

**Symptom:** Task reminders aren't being received.

**Cause:** Email SMTP settings may not be configured, or the background reminder thread failed to start.

**Fix:**
1. Verify SMTP settings in `docker-compose.yml` (see QUICKSTART.md)
2. Check container logs: `docker-compose logs -f`
3. Ensure tasks have due dates set (reminders fire 3 days before)

---

## Print / Export

### Print pages look wrong

**Symptom:** Print-ready pages (timeline, seating, contacts) have broken formatting when printed.

**Fix:** Use the browser's print function (Ctrl+P / Cmd+P). The CSS includes `@media print` styles. For best results:
- Use Chrome or Firefox
- Set margins to "Minimum" or "None"
- Enable "Background graphics" for colored elements

### CSV export has encoding issues

**Symptom:** Names with accents or special characters appear garbled in Excel.

**Fix:** The CSV is exported as UTF-8. When opening in Excel:
1. Use "Import from Text/CSV" (not double-click)
2. Select "UTF-8" encoding
3. Choose comma delimiter

---

## General Issues

### Date/time fields cause errors

**Symptom:** Submitting a form with date or time fields causes a 500 error.

**Cause:** Date fields expect `YYYY-MM-DD` format and time fields expect `HH:MM`. Non-standard formats or empty strings where dates are required will cause `strptime` parsing failures.

**Fix:** Use the browser's native date/time pickers. If entering manually, use the exact format: `2026-06-15` for dates, `14:30` for times.

### Numbers showing as None in templates

**Symptom:** Budget totals, counts, or calculations display "None" instead of 0.

**Cause:** Numeric database fields default to `NULL` when not set. Templates that display these directly without a fallback will show "None".

**Fix:** This has been addressed in most places with `or 0` fallbacks. If you encounter a new instance, the template fix is:
```jinja2
{{ value or 0 }}
```

### Application won't start in Docker

**Symptom:** Container exits immediately or shows import errors.

**Fix:**
```bash
# Rebuild the container
docker-compose up -d --build

# Check logs for specific error
docker-compose logs -f
```

---

## Performance Notes

- **SQLite limitations**: SQLite is single-writer. For weddings with 500+ guests, operations may feel slow during concurrent edits. This is expected for the target use case (1-2 concurrent planners).
- **Floor plan with many tables**: Dragging becomes less responsive with 30+ tables. The floor plan area has a fixed size; consider using the table detail cards for large events.
- **Auto-assign algorithm**: The Union-Find + affinity scoring algorithm runs in roughly O(n * t) time where n = number of guest groups and t = number of tables. For typical weddings (200 guests, 20 tables), this completes instantly.
