# Wedding Organizer - Quick Start Guide

## Get Started in 3 Steps!

### Step 1: Start the Application
```bash
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

# Configure (recommended)
cp .env.example .env
# Edit .env and set a secure SECRET_KEY

docker-compose up -d
```

> **Tip:** Generate a secret key with: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### Step 2: Access the Application
Open: **http://localhost:4345**

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

Add SMTP settings to your `.env` file to enable automatic task reminders (sent 3 days before due dates) and guest emails.

### Gmail

1. Enable 2FA at https://myaccount.google.com/security
2. Create an app password at https://myaccount.google.com/apppasswords
3. Add to `.env`:
   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   FROM_EMAIL=your-email@gmail.com
   ```

### Outlook / Office 365

```
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
FROM_EMAIL=your-email@outlook.com
```

### SendGrid

```
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
FROM_EMAIL=your-verified-sender@example.com
```

### Amazon SES

```
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-ses-smtp-username
SMTP_PASSWORD=your-ses-smtp-password
FROM_EMAIL=your-verified-sender@example.com
```

> **Note:** Replace the region (`us-east-1`) with your SES region.

### After Configuring Email

```bash
docker-compose restart
```

Check the logs to verify: `docker-compose logs -f`

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
- Backup with `./scripts/backup.sh` (see [INSTALL.md](INSTALL.md#database-backups))

---

## 🆘 Need Help?

- **[INSTALL.md](INSTALL.md)** - Detailed installation and deployment guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and fixes
- **[docs/DEPLOYMENT-GUIDES.md](docs/DEPLOYMENT-GUIDES.md)** - Platform guides (Unraid, Proxmox, K8s, etc.)
- **[docs/REVERSE-PROXY.md](docs/REVERSE-PROXY.md)** - SSL/HTTPS setup
- **[docs/WIKI.md](docs/WIKI.md)** - Comprehensive feature documentation
- **[docs/TRAINING.md](docs/TRAINING.md)** - Step-by-step training guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and what's new

**Start planning your perfect wedding!** 💍
