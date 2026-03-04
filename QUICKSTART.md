# Wedding Organizer - Quick Start Guide

## Get Started in 3 Steps!

### Step 1: Start the Application
```bash
cd wedding-organizer
docker-compose up -d
```

### Step 2: Access the Application
Open: **http://localhost:5000**

### Step 3: Create Your Wedding
1. Click "Add New Wedding"
2. Enter couple names, wedding date, and email
3. Start organizing!

---

## 🎯 What You Can Do

### **20+ Comprehensive Modules:**

1. **Dashboard** - Overview of all wedding details
2. **Ceremony** - Venue, officiant, music, timeline, vow writing, script builder
3. **Reception** - Venue, catering, seating chart, timeline, calculators
4. **Guests** - Full guest list with RSVP, social groups, meal summary
5. **Seating Chart** - Visual floor plan with drag-and-drop and auto-assign
6. **Social Groups** - Tag guests by social circles for smarter seating
7. **Bridal Party** - Manage attendants, processional order, gift tracking
8. **Vendors** - Track vendors, contracts, communication log, quote comparison
9. **Budget** - Budget tracking with templates, payment schedule, category limits
10. **Tasks** - Task management with email reminders, priority, categories
11. **Honeymoon** - Itinerary and packing lists
12. **Branding** - Wedding colors and style
13. **Attire** - Track all wedding outfits
14. **Registry** - Gift registry management
15. **Speeches** - Toast management with speaker order
16. **Favors** - Wedding favor tracking with assembly status
17. **Invitations** - Wording templates and stationery checklist
18. **RSVP Portal** - Public guest-facing RSVP page
19. **Print Pages** - Timeline, seating, contacts, shot list
20. **Calendar** - All dates and deadlines in one view

### **Additional Features**
- Online RSVP portal with shareable link
- CSV export for guests, expenses, and vendors
- iCal export for tasks and deadlines
- Activity logging across all modules
- Global search across all data
- Traditional elements library (15+ ceremonies and customs)

---

## 📧 Enable Email Reminders (Optional - 5 minutes)

### Gmail Setup:

1. **Get App Password:**
   - https://myaccount.google.com/apppasswords
   - Enable 2FA if needed
   - Create app password
   - Copy 16-character code

2. **Configure:**
   Edit `docker-compose.yml` and uncomment:
   ```yaml
   - SMTP_HOST=smtp.gmail.com
   - SMTP_PORT=587
   - SMTP_USER=your-email@gmail.com
   - SMTP_PASSWORD=your-16-char-app-password
   - FROM_EMAIL=your-email@gmail.com
   ```

3. **Restart:**
   ```bash
   docker-compose restart
   ```

Automatic reminders sent 3 days before task due dates!

---

## 🎨 Key Features

✅ **Unlimited weddings** - Manage multiple weddings
✅ **Smart seating chart** - Auto-assign with social group clustering
✅ **Drag-and-drop floor plan** - Visual table arrangement
✅ **Online RSVP portal** - Shareable link for guest responses
✅ **Complete guest management** - RSVP, meals, dietary, social groups
✅ **Vendor tracking** - Contracts, payments, communication log, quotes
✅ **Budget control** - Templates, category limits, payment schedule
✅ **Email reminders** - Never miss a deadline
✅ **Print-ready pages** - Timeline, seating, contacts, shot list
✅ **CSV/iCal export** - Guest lists, expenses, vendor info, tasks
✅ **Traditional elements** - Library of wedding traditions
✅ **Responsive design** - Works on all devices

---

## 📋 Common Commands

```bash
# Stop application
docker-compose down

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Rebuild
docker-compose up -d --build
```

---

## 💡 Quick Tips

- **Ceremony Timeline:** Add items in order - guests seating, processional, readings, vows, unity ceremony, pronouncement, recessional
- **Reception Timeline:** Grand entrance, first dance, toasts, dinner, cake cutting, special dances
- **Guest RSVP:** Mark guests as accepted/declined to track attendance
- **Budget:** Add expenses by category to track spending
- **Vendors:** Link vendors to specific categories for easy reference

---

## 🗄️ Data Storage

- Database: `instance/wedding_organizer.db`
- Persists across container restarts
- Backup by copying the database file

---

## 🆘 Need Help?

- **README.md** - Feature overview
- **CHANGELOG.md** - Version history and what's new
- **TROUBLESHOOTING.md** - Common issues and fixes
- **docs/WIKI.md** - Comprehensive feature documentation
- **docs/TRAINING.md** - Step-by-step training guide
- **ONBOARDING_GUIDE.md** - Setup wizard documentation

**Start planning your perfect wedding!** 💍
