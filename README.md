# Wedding Organizer - Complete Wedding Planning Platform

A comprehensive Docker-based wedding planning application built with Python Flask. Track every aspect of your wedding from ceremony details to guest management, with automated email reminders and a library of traditional wedding elements.

## 🎯 Core Features

### **20+ Complete Modules:**

1. **👥 People** - Manage information about individuals getting married
2. **📊 Dashboard** - Central hub with overview statistics
3. **💒 Ceremony** - Complete ceremony planning with timeline builder, vow writing, script builder
4. **🎉 Reception** - Reception venue, catering, music, timeline, and calculators
5. **👨‍👩‍👧‍👦 Guests** - Full guest list with RSVP tracking, social groups, meal summary
6. **🪑 Seating Chart** - Visual floor plan builder with drag-and-drop and auto-assign algorithm
7. **👥 Social Groups** - Tag guests by social circles for smarter seating
8. **🤝 Wedding Party** - Manage attendants and processional order
9. **💼 Vendors** - Track vendors, contracts, payments, communication log, quote comparison
10. **💰 Budget** - Budget tracking with templates, payment schedule, category limits
11. **✅ Tasks** - Task management with email reminders, priority, and categories
12. **✈️ Honeymoon** - Itinerary planning and packing lists
13. **🎨 Branding** - Wedding colors, fonts, and theme
14. **👔 Attire** - Track all wedding attire and fittings
15. **🎁 Registry** - Gift registry tracking
16. **🎤 Speeches** - Toast and speech management with order and duration
17. **🎁 Favors** - Wedding favor tracking with assembly status
18. **💌 Invitations** - Wording templates and stationery checklist
19. **📋 RSVP Portal** - Public guest-facing RSVP with token-based access
20. **🖨️ Print Pages** - Timeline, seating, vendor contacts, emergency contacts, shot list

---

## 🚀 Quick Start

### Prerequisites
- Docker
- Docker Compose

### Installation

```bash
cd wedding-organizer
docker-compose up -d
```

Access at: **http://localhost:5000**

### First Use
1. Click "Add New Wedding"
2. Enter wedding details and contact email
3. Complete the brief setup process
4. Start planning!

---

## 📋 Setup Process

When creating a wedding, you'll go through a quick 3-step setup:

1. **Number of people getting married** - Default is 2, but flexible
2. **Information about each person** - Names, optional titles, contact info
3. **Preferences** - Choose terminology that works for you

All information can be edited anytime from the People section.

---

## 🎨 Flexible Organization

- Organize wedding party and guests by custom labels
- All roles and titles are customizable
- Traditional elements can be adapted or removed
- Everything is editable throughout the planning process

---

## 📚 Traditional Elements Library

Browse 15+ traditional ceremony and reception elements:
- Unity ceremonies, cultural traditions, reception activities
- Detailed instructions and origins for each element
- Adaptable to any celebration style

---

## ⚙️ Configuration

### Email Setup (Optional)

Enable automated task reminders:

1. Edit `docker-compose.yml`
2. Uncomment email environment variables
3. Add your SMTP credentials
4. Restart container

See QUICKSTART.md for detailed email setup instructions.

---

## 🗄️ Database Structure

SQLite database with comprehensive models for all modules. Data persists in the `instance/` directory.

---

## 🔧 Docker Commands

```bash
# Start application
docker-compose up -d

# Stop application
docker-compose down

# View logs
docker-compose logs -f

# Rebuild
docker-compose up -d --build
```

---

### Seating Chart Builder
- **9 table presets** from 48" round to King's table
- **6 table roles**: head, sweetheart, King's, VIP, kids, guest
- **Drag-and-drop floor plan** with visual table shapes
- **Auto-assign algorithm** using Union-Find + affinity scoring
- **Seating preferences**: "seat together" and "keep apart" constraints
- **Social group clustering**: tag guests by real-world connections (church, work, college, etc.)

---

## 📖 Documentation

- **README.md** - This file
- **QUICKSTART.md** - Quick start guide
- **CHANGELOG.md** - Version history and release notes
- **TROUBLESHOOTING.md** - Common issues and edge case fixes
- **docs/WIKI.md** - Comprehensive feature documentation
- **docs/TRAINING.md** - Step-by-step user training guide
- **ONBOARDING_GUIDE.md** - Onboarding system documentation

---

## 💾 Data Persistence

Database stored in `instance/wedding_organizer.db` and mounted as Docker volume for persistence across restarts.

---

## 🎯 Use Cases

- Engaged couples planning their own wedding
- Professional wedding planners managing multiple weddings
- Event coordinators and venues
- Anyone organizing a wedding celebration

---

## 📄 License

Open source - free for personal and commercial use

---

**Start planning your perfect wedding today!** 💍
