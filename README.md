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
git clone https://github.com/thegspiro/the-open-source-wedding-planner.git
cd the-open-source-wedding-planner

# Configure environment
cp .env.example .env
# Edit .env and set a secure SECRET_KEY

docker-compose up -d
```

Access at: **http://localhost:4345**

> For detailed installation options (local development, VPS, reverse proxy, etc.), see **[INSTALL.md](INSTALL.md)**.

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

Enable automated task reminders and guest emails by adding SMTP settings to your `.env` file:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
```

Then restart: `docker-compose restart`

Supports Gmail, Outlook, SendGrid, Amazon SES, and any SMTP provider. See [QUICKSTART.md](QUICKSTART.md#-enable-email-reminders-optional---5-minutes) for detailed setup instructions per provider.

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

### Setup & Deployment
- **[INSTALL.md](INSTALL.md)** - Complete installation guide (Docker, local dev, production)
- **[docs/DEPLOYMENT-GUIDES.md](docs/DEPLOYMENT-GUIDES.md)** - Platform-specific guides (Unraid, Proxmox, Kubernetes, Synology, Raspberry Pi, VPS)
- **[docs/REVERSE-PROXY.md](docs/REVERSE-PROXY.md)** - SSL/HTTPS setup (Nginx, Traefik, Caddy, Cloudflare)
- **[.env.example](.env.example)** - Environment configuration reference

### Contributing
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development setup, code style, and PR guidelines

### Usage & Reference
- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide
- **[ONBOARDING_GUIDE.md](ONBOARDING_GUIDE.md)** - Onboarding system documentation
- **[docs/WIKI.md](docs/WIKI.md)** - Comprehensive feature documentation
- **[docs/TRAINING.md](docs/TRAINING.md)** - Step-by-step user training guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and edge case fixes
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

---

## 💾 Data Persistence & Backups

Database stored in `instance/wedding_organizer.db` and mounted as Docker volume for persistence across restarts.

A backup script is included:
```bash
chmod +x scripts/backup.sh
./scripts/backup.sh              # Create a backup
./scripts/backup.sh --restore latest  # Restore latest backup
```

See [INSTALL.md](INSTALL.md#database-backups) for automated backup setup.

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
