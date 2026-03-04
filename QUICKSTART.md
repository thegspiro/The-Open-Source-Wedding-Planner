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

### **12 Comprehensive Modules:**

1. **Dashboard** - Overview of all wedding details
2. **Ceremony** - Venue, officiant, music, timeline (precise to the second!)
3. **Reception** - Venue, catering, seating chart, timeline
4. **Guests** - Full guest list with RSVP tracking
5. **Bridal Party** - Manage bridesmaids, groomsmen, processional order
6. **Vendors** - Track all vendors and contracts
7. **Budget** - Complete budget tracking
8. **Tasks** - Task management with email reminders
9. **Honeymoon** - Itinerary and packing lists
10. **Branding** - Wedding colors and style
11. **Attire** - Track all wedding outfits
12. **Registry** - Gift registry management

### **Traditional Elements Library**
- Browse 15+ traditional wedding elements
- Unity ceremonies, cultural traditions, reception activities
- Detailed instructions for each

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
✅ **Timeline builder** - Precise to-the-second scheduling
✅ **Complete guest management** - RSVP, meals, seating
✅ **Vendor tracking** - Contracts, payments, schedules
✅ **Budget control** - Real-time expense tracking
✅ **Email reminders** - Never miss a deadline
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

Check the full README.md for:
- Detailed module documentation
- All traditional elements
- Database structure
- Advanced configuration

**Start planning your perfect wedding!** 💍
