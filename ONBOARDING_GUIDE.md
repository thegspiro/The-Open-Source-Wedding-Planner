# Onboarding System - How to Test

## Overview

The new onboarding system provides a module-by-module setup experience with:
- **Template-based setup** - Choose from pre-built ceremony templates
- **Custom setup** - Answer questions to build your own
- **Skip-around navigation** - Jump to any module, skip what you don't need
- **Progress tracking** - See what's complete and what's left

## Testing the Ceremony Module

1. **Start the application:**
   ```bash
   docker-compose up -d
   ```

2. **Create a new wedding:**
   - Go to http://localhost:5000
   - Click "Add New Wedding"
   - Fill in basic details
   
3. **Complete initial onboarding (Steps 1-3):**
   - Step 1: Choose number of people getting married
   - Step 2: Enter details for each person
   - Step 3: Choose terminology preferences
   
4. **You'll be taken to the Onboarding Hub**
   - This shows all available modules
   - Each module shows completion status
   - Click any module to set it up

5. **Test the Ceremony Module:**
   
   **Option A: Template-based setup**
   - Click "Start Setup" on Ceremony module
   - Choose ceremony type (Religious, Secular, etc.)
   - Browse templates (Catholic, Jewish, Modern Secular, etc.)
   - Click a template to preview it
   - See the full timeline with durations
   - Click "Use This Template"
   - Customize venue, timing, and officiant details
   - Submit to complete

   **Option B: Custom setup**
   - Click "Start Setup" on Ceremony module
   - Choose ceremony type
   - Click "Build from Scratch"
   - You'll be guided through questions (currently simplified to go straight to customize)

6. **After Setup:**
   - Module shows as "Complete" in hub
   - Can click "Edit" to modify
   - Can skip to Dashboard to start planning
   - Timeline is saved and visible in Ceremony module

## What's Implemented

✅ **People Module** - Initial 3-step setup
✅ **Onboarding Hub** - Central navigation
✅ **Ceremony Module - Complete:**
   - Type selection (Religious, Secular, Spiritual, Civil)
   - Template filtering based on type
   - 8 pre-built ceremony templates:
     - Catholic Wedding
     - Jewish Wedding
     - Protestant Wedding
     - Modern Secular
     - Simple Secular
     - Courthouse/Civil
     - Hindu Wedding
   - Template preview with full timeline
   - Template application
   - Customization page for venue, timing, officiant
   - Timeline preserved from template

⏳ **Coming Soon:**
- Reception module templates
- Budget module templates
- Step-by-step custom question flows
- More ceremony templates

## Templates Included

### Ceremony Templates:
1. **Catholic** - 60 min, 17 steps, full mass
2. **Jewish** - 45 min, 11 steps, includes chuppah, breaking glass
3. **Protestant** - 30 min, 16 steps, with unity candle
4. **Modern Secular** - 25 min, 12 steps, personalized
5. **Simple Secular** - 15 min, 8 steps, brief and sweet
6. **Courthouse** - 10 min, 7 steps, legal ceremony
7. **Hindu** - 120 min, 10 steps, traditional elements

Each template includes:
- Full timeline with order and durations
- Music suggestions
- Unity ceremony recommendations
- Detailed descriptions

## Features to Test

1. **Template Filtering:**
   - Choose "Religious" → See Catholic, Jewish, Protestant, Hindu
   - Choose "Secular" → See Modern, Simple
   - Choose "Civil" → See Courthouse

2. **Template Preview:**
   - View full timeline before applying
   - See estimated duration
   - Read descriptions

3. **Customization:**
   - After applying template, add venue details
   - Set timing
   - Add officiant info
   - Timeline is preserved

4. **Progress Tracking:**
   - Hub shows completed modules
   - Can return to edit
   - Can skip to dashboard anytime

## Database Fields

The system uses:
- `wedding.onboarding_preferences` (JSON) - Stores ceremony type, etc.
- `wedding.modules_completed` (JSON array) - Tracks which modules are done
- `ceremony.timeline_items` - Stores timeline from templates
- `ceremony` fields - Venue, officiant, timing details

## Next Steps

To expand the system:
1. Add Reception templates (already prepared in templates_data.py)
2. Add Budget templates (already prepared in templates_data.py)
3. Build out custom question flows for each module
4. Add more ceremony templates
5. Add template editing before applying
6. Add timeline editing in customize page

Enjoy testing!
