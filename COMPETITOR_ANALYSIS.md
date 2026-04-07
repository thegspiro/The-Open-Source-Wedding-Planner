# Competitor Analysis & Feature Gap Report

**Date:** April 7, 2026
**Competitors Reviewed:** The Knot, Zola, WeddingWire, Joy (WithJoy), Appy Couple, WedSites

---

## Executive Summary

Our Open Source Wedding Planner is remarkably feature-rich with **75+ features across 20+ modules** and **274 API endpoints**. It already surpasses many competitors in areas like ceremony planning depth, seating chart sophistication, and day-of logistics. However, several key areas found across competitor platforms are **missing or underdeveloped** in our application.

---

## What We Already Do Well

These areas are at parity or exceed competitors:

| Category | Our Strength |
|---|---|
| Ceremony Planning | 10+ cultural ceremony templates, readings, traditional elements library -- unmatched |
| Seating Charts | Auto-assign algorithm, 9+ table presets, venue fixtures, drag-and-drop -- on par with paid Zola feature ($14.99) |
| Budget Management | 4 budget templates, category limits, payment schedules, vendor cost tracking |
| Guest Management | Household grouping, social circles, RSVP portal, QR check-in, meal tracking |
| Day-of Logistics | Emergency kit, contingency plans, tips/gratuities, inventory bins, personal timelines |
| Print Center | 20+ printable documents including MC scripts, mailing labels, ceremony programs |
| Data Portability | Full CSV import/export, JSON backup, iCal integration |
| Vendor Management | Quotes, communication logs, payment tracking, contact management |

---

## Feature Gaps Identified

### 1. Wedding Website Builder (HIGH PRIORITY)
**Found in:** The Knot, Zola, Joy, WeddingWire, Appy Couple, WedSites

Every major competitor offers a **guest-facing wedding website** with:
- Customizable templates (Joy offers 600+, Zola offers hundreds)
- Custom domains or subdomains (e.g., `jamie-and-alex.theknot.com`)
- Event details pages (ceremony, reception, rehearsal dinner, etc.)
- Travel & accommodations information for guests
- Photo galleries
- Wedding party bios
- FAQ section
- Password protection for privacy
- Mobile-responsive design

**Our gap:** We have a public RSVP portal and read-only shared link, but no full guest-facing wedding website that couples can customize and share. This is the #1 expected feature in the industry.

---

### 2. Digital Save the Dates & Invitations (HIGH PRIORITY)
**Found in:** Zola, Joy, Appy Couple, The Knot, WedSites

Competitors offer:
- Digital save-the-date cards with matching designs
- Digital wedding invitations (email and/or text delivery)
- Coordinated stationery suite (save the date, invitation, RSVP, thank you)
- Template galleries with customizable designs
- Send tracking (delivered, opened, RSVP'd)
- Print-at-home or professional printing integration

**Our gap:** We have invitation wording templates and a stationery checklist, but no ability to design, preview, or send digital invitations/save-the-dates directly to guests.

---

### 3. Vendor Directory & Marketplace (MEDIUM PRIORITY)
**Found in:** The Knot (166,000+ vendors), WeddingWire (250,000+), Zola, Joy

Competitors offer:
- Searchable vendor directory by location & category
- Vendor reviews and ratings from real couples
- Photo portfolios per vendor
- Direct messaging to vendors through the platform
- Pricing transparency and availability checking
- 360-degree virtual venue tours (WeddingWire)
- AI-powered vendor matching based on style (The Knot)

**Our gap:** We track vendors the couple has already chosen, but don't help them discover or compare new vendors. As an open-source self-hosted app, a full marketplace may be out of scope, but a **curated vendor directory with community reviews** or integration with external vendor APIs could be valuable.

---

### 4. Guest Communication & Messaging Hub (MEDIUM PRIORITY)
**Found in:** Joy, Zola, The Knot, Appy Couple

Competitors offer:
- In-app guest messaging and announcements
- Broadcast updates to all guests or filtered groups
- Email templates that match the wedding website design
- SMS/text message notifications to guests
- Push notifications via mobile app
- Guest-facing mobile app experience
- Premium guest texting (Zola offers at $79.99)

**Our gap:** We have basic email capability (send to individual guests, day-of batch emails), but lack a structured **guest communication hub** with templates, scheduled messages, group targeting, and multi-channel delivery (email + SMS).

---

### 5. Photo Sharing & Gallery (MEDIUM PRIORITY)
**Found in:** Joy (unlimited free storage), The Knot, Appy Couple, WedSites

Competitors offer:
- Shared photo album where guests upload photos
- Curated photo galleries on the wedding website
- Engagement photo galleries
- Real-time photo sharing during the event
- Photo moderation by the couple
- Download options for guests
- Integration with professional photographer delivery

**Our gap:** We have a photography shot list feature, but no **photo sharing or gallery** functionality where guests can view or contribute photos.

---

### 6. AI-Powered Planning Assistance (LOW-MEDIUM PRIORITY)
**Found in:** The Knot (AI vendor matching, ChatGPT integration), Joy (AI thank-you writer)

Competitors offer:
- AI-powered vendor recommendations based on style/budget
- AI-generated content (thank-you notes, vow drafts, speeches)
- Smart checklist prioritization
- Visual style matching (upload inspiration photos, get vendor matches)
- ChatGPT integration for conversational planning help

**Our gap:** No AI-powered features currently. Potential opportunities:
- AI-assisted vow writing
- AI speech/toast drafting
- Smart budget allocation recommendations
- Automated timeline optimization

---

### 7. Registry Store & Cash Funds (LOW-MEDIUM PRIORITY)
**Found in:** Zola (integrated store), The Knot (registry store), Joy, Amazon Wedding Registry

Competitors offer:
- Integrated gift purchasing (buy directly on the platform)
- Universal registry (add items from any store)
- Cash fund / honeymoon fund with zero or low fees
- Group gifting for expensive items
- Gift tracking with automatic thank-you reminders
- Registry calculator (suggested # of gifts by price point based on guest count)

**Our gap:** We have a basic registry list (item, store, link, purchased status), but no **integrated purchasing, cash fund management, or gift card support**. Adding a universal registry link aggregator and cash fund tracking would be valuable without needing to become an e-commerce platform.

---

### 8. Travel & Accommodations Coordination (LOW PRIORITY)
**Found in:** Joy, Zola, The Knot

Competitors offer:
- Hotel room block management with booking links
- Map integration showing venue, hotels, and airports
- Ride-sharing integrations (Uber/Lyft links)
- Travel recommendations and local attractions
- Guest-facing travel info page

**Our gap:** We have accommodation tracking (hotel blocks, rates, booking codes), but lack **map integration, ride-sharing links, and a guest-facing travel information page**. This ties into the wedding website gap.

---

### 9. Mobile App Experience (LOW PRIORITY)
**Found in:** The Knot, Zola, Joy, WeddingWire

Competitors offer:
- Native iOS and Android apps
- Push notifications for task reminders
- On-the-go vendor messaging
- Wedding countdown widget
- Quick-access guest check-in
- Offline access to key information

**Our gap:** We are a web application only. A **Progressive Web App (PWA)** approach could provide app-like features (offline access, push notifications, home screen install) without the overhead of native app development.

---

### 10. Social Features & Inspiration (LOW PRIORITY)
**Found in:** The Knot, Zola, WeddingWire, Pinterest integration

Competitors offer:
- Style quizzes to determine wedding aesthetic
- Inspiration galleries and mood boards
- Real wedding galleries for ideas
- Pinterest board integration
- Social media sharing of wedding details
- Community forums and advice columns

**Our gap:** We have no inspiration/discovery features. Our app is execution-focused (plan and manage), not discovery-focused (explore and get inspired). This is acceptable for an open-source tool but worth noting.

---

## Commonly Overlooked Wedding Planning Items

*Compiled from listicles, blogs, personal posts, Reddit threads, and wedding professional advice about things that slip through the cracks when planning a wedding.*

### A. Pre-Wedding Event Management
**Status: Partially covered (rehearsal dinner only)**

Our app tracks the rehearsal dinner but doesn't help manage the full suite of pre-wedding events:
- **Engagement party** planning (venue, guest list, host coordination)
- **Bridal shower / couples shower** (separate guest list, gifts, host)
- **Bachelor/bachelorette party** planning (travel, activities, budget, invitations)
- **Welcome party / welcome drinks** the night before (for destination weddings)
- **Morning-after brunch / send-off brunch** for out-of-town guests
- **Per-event RSVPs** (different guest lists per event -- not all guests attend all events)

### B. Wedding Signage & Stationery Checklist
**Status: Not covered**

Couples consistently forget to plan, order, or create signage:
- Welcome sign (confirms guests are at the right wedding)
- Ceremony program sign or printed programs
- Unplugged ceremony sign (phones away policy)
- Seating chart display / escort card table
- Escort cards vs. place cards (table assignment vs. seat assignment)
- Table numbers
- Bar menu sign
- Buffet/food station labels (with allergen info)
- Dessert table sign
- Guest book sign ("Please sign our guest book")
- Cards & gifts sign/table
- Photo booth instructions sign
- Hashtag sign (social media hashtag for the wedding)
- Memorial / "In Loving Memory" sign for deceased loved ones
- Parking and directions signs
- Restroom directional signs
- Sparkler/send-off instructions sign
- Thank you sign at exit

### C. Day-of Contact Sheet & Task Delegation
**Status: Partially covered (vendor contacts exist, but no delegation system)**

Frequently cited as the #1 thing that falls through the cracks:
- **Master contact sheet** with every vendor name, phone, arrival time, setup location -- printed copies for planner, MOH, and best man
- **Task delegation list** -- who handles what (gift transport, card box, guest book, cake knife, decorations setup/teardown, final vendor payments, emergency contact person)
- **Point person assignment** -- designate a trusted friend/coordinator as the go-to for vendor questions, guest issues, and timeline management so the couple doesn't have to
- **End-of-night responsibilities** -- who collects gifts/cards, who handles decoration breakdown, who settles final payments, who transports personal items, who returns rentals

### D. Guest Comfort & Accessibility
**Status: Partially covered (wheelchair ramp fixture, kids activities)**

Commonly overlooked details for guest experience:
- **Accessibility audit** -- wheelchair access, ramps, accessible restrooms, hearing loops, sign language interpreters, large-print materials
- **Sensory-friendly quiet room** for neurodivergent guests, overwhelmed children, or nursing mothers
- **Elderly guest accommodations** -- seating near exits, hearing assistance, transportation
- **Bathroom amenity baskets** -- mints, hairspray, deodorant, stain remover, band-aids, feminine products, sewing kit
- **Coat check** planning (winter weddings)
- **Guest entertainment during gaps** -- activities during cocktail hour, photo sessions, or ceremony-to-reception transitions
- **Late-night snacks** -- food service after dancing (sliders, pizza, fries, s'mores)
- **Coffee/tea service** timing for late receptions
- **Blankets or heaters** for outdoor evening events
- **Fans or cooling stations** for outdoor summer events
- **Bug spray / sunscreen station** for outdoor weddings
- **Shuttle service / parking coordination** for venues with limited parking
- **Designated driver / ride-share info** for guests who drink

### E. Timeline Buffer & Logistics Gaps
**Status: Partially covered (timeline exists, but no buffer/gap warnings)**

The most frequently cited mistake in wedding planning:
- **Buffer time warnings** -- the app should flag timelines without adequate buffers (recommend 30-45 min padding)
- **Getting-ready timeline** -- hair/makeup scheduling (bride should finish first, not last; allow 45-60 min before dressing)
- **Ceremony-to-reception gap management** -- warn if gap exceeds 1 hour; suggest cocktail hour entertainment
- **Photo session realistic timing** -- family formals (30-40 min), bridal party (20-30 min), couple portraits (30-45 min), golden hour (15-20 min)
- **Vendor arrival/setup windows** -- track when each vendor arrives, how long they need for setup
- **Vendor departure/overtime tracking** -- warn when timeline may trigger overtime fees ($100-500/hr per vendor)
- **Breakdown/cleanup timeline** -- who does what after the reception ends

### F. Hidden Costs & Budget Items Couples Forget
**Status: Partially covered (budget exists, but lacks these common categories)**

Budget line items that repeatedly blindside couples:
- **Venue fees beyond rental** -- service charges (15-25%), corkage fees, cake cutting fees, valet, A/V equipment, overtime charges, cleaning fees, garbage removal
- **Vendor meals** -- photographers, videographers, DJ, band, planner all need meals ($30-90 each)
- **Vendor overtime** -- per-hour charges when events run long
- **Vendor tips** (we have this!) but many apps don't remind couples early enough
- **Wedding insurance** -- liability and cancellation coverage ($150-500)
- **Permits** -- outdoor venues, parks, historical sites ($50-250+)
- **Marriage license fees** (we track this!)
- **Postage** -- for save-the-dates, invitations, RSVP cards, thank-you notes
- **Dress/suit alterations** -- often $200-800 on top of purchase price
- **Dress preservation/cleaning** -- post-wedding ($150-500)
- **Beauty prep** -- hair trials, makeup trials, manicures, spray tans, teeth whitening, facials
- **Welcome bags** for hotel guests
- **Wedding party gifts** -- bridesmaids, groomsmen, parents, flower girl, ring bearer
- **Day-of emergency fund** -- cash for tips, unexpected costs (recommend 5% buffer)
- **Pre-wedding event costs** -- engagement party, shower, bachelor/ette
- **Post-wedding costs** -- thank-you cards, photo album, name change fees
- **Rental extras** -- extra tables beyond dinner (guest book, gifts, place cards, cocktail hour)
- **Non-preferred vendor surcharge** -- venues that charge 15-25% for outside vendors

### G. Wedding Day Essentials Packing List
**Status: Partially covered (emergency kit exists, but missing these commonly forgotten items)**

Items couples forget to bring or arrange on the wedding day:
- **Marriage license + pen** for signing
- **Rings** (surprisingly forgotten more than you'd think)
- **Printed vows** (backup copy)
- **Spare invitation suite** for detail photography
- **Outfit hangers** (personalized or nice ones for photos)
- **Shoes + heel stoppers** for outdoor photos on grass
- **Change of shoes** (comfortable reception shoes)
- **Undergarments** (specific to dress style)
- **Garter** (if doing garter toss)
- **Cake topper**
- **Cake knife and server**
- **Card box**
- **Guest book + pens**
- **Flower girl petals**
- **Ring bearer pillow**
- **Unity ceremony supplies** (candle, sand, wine, etc.)
- **Wedding party/parent cards and gifts**
- **Phone chargers / portable batteries**
- **Snacks and water** for getting-ready time
- **Breakfast/lunch for wedding party** during prep
- **Steamer** for dress/suit touch-ups
- **Bouquet charm** or memorial photo
- **Gift table supplies** (tablecloth, sign)
- **Sparklers / send-off supplies**
- **Cash for last-minute needs**

### H. Photography & Videography Planning Gaps
**Status: Partially covered (shot list exists, but missing these elements)**

Details photographers and videographers say couples overlook:
- **First look logistics** -- private location, timing (45-60 min total)
- **Golden hour / sunset portrait scheduling** -- coordinate with actual sunset time
- **Second shooter coordination** -- who covers what angles
- **Detail shots checklist** -- rings, shoes, invitation suite, bouquet, perfume, jewelry, venue details, table settings
- **Photo wrangler** -- assign someone from each family side to gather people for group shots
- **Videographer audio** -- ceremony microphone setup for clear vow recording (lavalier mics, windscreens for outdoor)
- **Unplugged ceremony policy** -- guests' phones/iPads blocking professional photos
- **Photo booth planning** -- props, signage, guest book integration
- **Professional photo/video delivery timeline** -- set expectations (6-12 weeks typical)
- **Drone photography** -- permits and venue restrictions
- **Dress bustling practice** -- someone must learn how before the reception photos/dancing

### I. Music & Sound System Details
**Status: Partially covered (playlist exists, but missing technical logistics)**

Audio/music details that slip through the cracks:
- **Do-not-play list** (we have the moment "do not play" but could be more prominent)
- **Song requests from guests** -- collect via RSVP (Zola does this)
- **Sound system for outdoor ceremony** -- separate from reception; needs its own PA
- **Microphone plan** -- officiant mic, couple's lavalier, reading podium mic, toast mic
- **Windscreens** for outdoor microphones
- **Battery checks** for wireless mics
- **Music downloaded offline** -- never rely on WiFi/streaming
- **Phone on airplane mode** during playlist playback (prevent calls interrupting)
- **Music stand / podium** for readers who need hands free
- **Toast order** -- written down and shared with DJ/MC and all speakers
- **Reception music transitions** -- dinner music vs. dancing music vs. last dance

### J. Social Media & Guest Communication Policies
**Status: Not covered**

Increasingly important modern wedding details:
- **Wedding hashtag** -- generator and display on signage
- **Unplugged ceremony policy** -- communicate on website, signage, and via officiant announcement
- **Social media sharing guidelines** -- what's OK to post and when (don't spoil dress reveal)
- **Photo/video sharing policy** -- can guests share before couple posts officially?
- **Digital guestbook** -- alternative to physical guest book
- **Guest-contributed playlist** -- collaborative Spotify playlist

### K. Legal & Administrative Details
**Status: Partially covered (marriage license tracked)**

Legal items that cause last-minute panic:
- **Marriage license timing** -- waiting periods (1-6 days by state), expiration dates (30 days to 1 year)
- **Witness requirements** -- number of witnesses needed varies by jurisdiction
- **Officiant credentials** -- verify legal authority to perform ceremony in your jurisdiction
- **Name change checklist** -- Social Security, driver's license, passport, bank accounts, credit cards, insurance, voter registration, employer, medical records (post-wedding)
- **Legal document updates** -- beneficiaries, wills, power of attorney, insurance policies
- **Certified marriage certificate copies** -- ordering additional copies for legal purposes

### L. Post-Wedding Tasks
**Status: Partially covered (thank-you tracking, some tasks auto-generated)**

Things that need attention after the celebration:
- **Thank-you card timeline** -- aim for within 3 months; track who sent what gift
- **Photo organization** -- collect guest photos, organize professional photos, back up to cloud
- **Wedding dress/suit preservation** -- clean within 2 weeks before stains set
- **Rental returns** -- track deadlines and responsible parties
- **Vendor reviews** -- leave reviews for vendors (we track vendor ratings but don't prompt for public reviews)
- **Final vendor payments** -- settle outstanding balances
- **Gift inventory and organization** -- track, exchange duplicates, store
- **Name change process** (see Legal section above)
- **Address update announcements** -- new address if moved
- **Keepsake organization** -- guest book, card box contents, programs, photos, bouquet preservation

### M. Couple Self-Care & Relationship
**Status: Not covered**

Consistently cited in personal blogs and Reddit as the most undervalued aspect:
- **Wedding-free days** -- schedule 1-2 days/week with no wedding talk
- **Stress management reminders** -- meditation, exercise, date nights
- **Boundary-setting guidance** -- managing family opinions and drama
- **Couple check-ins** -- regular relationship conversations beyond logistics
- **Pre-marital counseling** -- many officiants require it; track sessions
- **Day-of self-care** -- eat breakfast, stay hydrated, take moments alone together
- **Post-wedding blues awareness** -- the emotional letdown after months of planning

### N. Weather & Environmental Contingencies
**Status: Partially covered (contingency plans module exists)**

Specific weather scenarios couples fail to plan for:
- **Rain plan** -- tent rental, indoor backup space, umbrella supply
- **Extreme heat plan** -- fans, shade structures, water stations, early timeline
- **Cold weather plan** -- heaters, blankets, warm drink stations, coat check
- **Wind plan** -- secure decorations, hair considerations, candle alternatives
- **Sunset/lighting transitions** -- outdoor to indoor, string lights, lanterns for after dark

---

## Priority Recommendations

### Tier 1 - High Impact, Fills Major Gaps
1. **Wedding Website Builder** - The single most expected feature across all competitors. A template-based, guest-facing website with event details, RSVP, travel info, and photo gallery would dramatically increase our value proposition.
2. **Digital Invitations & Save the Dates** - Closely tied to the wedding website; let couples design and send digital stationery to their guest list.
3. **Wedding Signage & Stationery Checklist** (Section B) - A simple checklist module that prompts couples to plan all the signs and printed materials they'll need. Low effort, high value.

### Tier 2 - Medium Impact, Enhances Existing Strengths
4. **Guest Communication Hub** - Upgrade from basic email to a structured messaging system with templates, scheduling, group targeting, and delivery tracking.
5. **Photo Sharing Gallery** - Allow guests to upload and view photos, building on our existing photography module.
6. **Enhanced Registry** - Add universal registry link aggregation and cash fund/honeymoon fund tracking.
7. **Timeline Buffer Warnings** (Section E) - Smart timeline validation that flags unrealistic schedules, missing buffers, and potential overtime charges.
8. **Day-of Contact Sheet & Task Delegation** (Section C) - Printable master contact sheet + task assignment for end-of-night responsibilities.
9. **Hidden Cost Reminders** (Section F) - Auto-suggest commonly forgotten budget line items (vendor meals, overtime, insurance, permits, postage, alterations).

### Tier 3 - Medium Impact, New Modules
10. **Pre-Wedding Event Manager** (Section A) - Track engagement party, bridal shower, bachelor/ette party with separate guest lists and RSVPs per event.
11. **Guest Comfort & Accessibility Planner** (Section D) - Accessibility audit checklist, bathroom amenity planning, shuttle coordination, late-night snack planning.
12. **Name Change & Post-Wedding Checklist** (Sections K, L) - Step-by-step name change guide + post-wedding task tracker (dress preservation, vendor reviews, photo organization).
13. **Wedding Day Packing List** (Section G) - Enhanced packing checklist beyond the emergency kit (rings, license, cake topper, card box, etc.).

### Tier 4 - Nice to Have, Differentiators
14. **PWA Support** - Progressive Web App capabilities for mobile-like experience.
15. **AI Writing Assistant** - Help with vows, speeches, thank-you notes, and planning suggestions.
16. **Map Integration** - Interactive maps showing venue locations, hotels, and transportation options.
17. **Vendor Discovery** - Community-contributed vendor directory or external API integration.
18. **Social Media & Hashtag Tools** (Section J) - Wedding hashtag generator, unplugged ceremony policy templates, digital guestbook.
19. **Couple Self-Care Reminders** (Section M) - Wellness check-ins, wedding-free day scheduling, boundary-setting tips.
20. **Style Quiz / Inspiration** - Help couples discover their wedding style and theme.
21. **Song Request via RSVP** (Section I) - Let guests suggest songs when they RSVP.
22. **Custom RSVP Questions** - Allow arbitrary questions beyond meal choice and dietary restrictions.

---

## Sources

### Competitor Platform Research
- [The Knot Wedding Planning App](https://www.theknot.com/wedding-planning-app)
- [The Knot AI-Powered Planning Experience](https://www.theknotww.com/press-releases/the-knot-launches-new-ai-powered-planning-experience/)
- [The Knot ChatGPT Integration](https://www.businesswire.com/news/home/20260202639400/en/The-Knot-Worldwide-Launches-The-Wedding-Industrys-First-App-Within-ChatGPT)
- [Zola Wedding Planning Tools](https://www.zola.com/wedding-planning)
- [Zola Wedding Checklist](https://www.zola.com/wedding-planning/checklist)
- [Zola Best Wedding Planning Apps](https://www.zola.com/expert-advice/best-wedding-planning-apps)
- [Joy Wedding Website & Planning](https://withjoy.com/)
- [Joy Named Best Wedding Website 2025](https://www.businesswire.com/news/home/20250716401625/en/Joy-Named-Best-Wedding-Website-Experience-of-2025-by-BRIDES)
- [WeddingWire Vendor Manager](https://www.weddingwire.com/wedding-planning/vendor-manager.html)
- [WeddingWire Wedding Vendors](https://www.weddingwire.com/wedding-vendors)
- [Top Wedding Planning Apps 2026](https://presidentialctr.com/best-wedding-planning-apps/)
- [Best Free Wedding Planning Apps 2026](https://venuepreview.com/blog/best-free-wedding-planning-apps-2026/)
- [Appy Couple Features](https://www.appycouple.com/features/)
- [WedSites Features](https://wedsites.com/)

### Overlooked Details & Common Mistakes
- [Top 25 Common Things Brides Forget -- 48 Fields](https://www.48fields.com/checklist-top-25-common-things-brides-forget-for-wedding/)
- [Most Forgotten Things on Wedding Day -- Legend & Lace Studios](https://legendandlacestudios.com/most-forgotten-things-on-wedding-day-the-ultimate-checklist/wedding-planning-tips/)
- [30 Items You're Forgetting While Wedding Planning -- Three16 Photography](https://three16photography.com/wedding-planning-tips-30-things-youre-forgetting-about-while-wedding-planning/)
- [Commonly Forgotten Items -- Burgh Brides](https://burghbrides.com/blog/commonly-forgotten-items-wedding-day/)
- [25 Small Wedding Details -- Zola](https://www.zola.com/expert-advice/small-wedding-details)
- [16 Wedding Details Couples Forget -- WeddingWire](https://www.weddingwire.com/wedding-ideas/16-wedding-details-every-couple-forgets-but-shouldn-t)
- [23 Things You May Forget -- Here Comes the Guide](https://www.herecomestheguide.com/wedding-ideas/things-you-forget-wedding-planning)
- [150 Things People Don't Think Of -- BuzzFeed](https://www.buzzfeed.com/jennifer_mcphee/150-things-most-people-dont-think-of-when-plannin-b6ut58hl75)
- [19 Common Things Brides Forget -- Wezoree](https://wezoree.com/inspiration/top-common-things-brides-forget-for-their-wedding/)
- [Top 10 Things Brides Forget -- Heritage at Milford](https://theheritageatmilfordfamilyfarm.com/wedding-planning-tips/top-10-things-every-bride-forgets-but-really-shouldnt-insider-wedding-wisdom-from-a-venue-owner-whos-seen-300-i-dos)

### Wedding Regrets & Lessons Learned
- [20 Biggest Wedding Regrets -- Zoe Larkin Photography](https://zoelarkin.com/wedding-regrets/)
- [23 Things Couples Regret Not Doing -- Critsey Rowe](https://www.critseyrowe.com/20-things-couples-regret-not-doing-at-their-wedding/)
- [Wedding Regrets -- The Knot Insiders](https://www.theknot.com/content/wedding-regrets)
- [Reddit Wedding Planning Tips -- The Knot](https://www.theknot.com/content/reddit-wedding-planning)

### Hidden Costs
- [21 Hidden Wedding Costs -- Here Comes the Guide](https://www.herecomestheguide.com/wedding-ideas/hidden-wedding-costs)
- [24 Hidden Wedding Costs -- The Knot](https://www.theknot.com/content/hidden-wedding-costs)
- [35 Hidden Wedding Costs -- Wedding Shoppe](https://www.weddingshoppeinc.com/blogs/weddings/35-hidden-wedding-costs)
- [30 Unexpected Costs -- Bridal Guide](https://www.bridalguide.com/planning/wedding-budget/unexpected-wedding-costs)

### Accessibility & Guest Comfort
- [Accessible Wedding Planning -- Lakeshore in Love](https://lakeshoreinlove.com/how-to-make-your-wedding-accessible-for-guests-with-disabilities/)
- [Disability-Friendly Wedding -- The Knot](https://www.theknot.com/content/accessible-wedding)
- [Dos & Don'ts of Disability Wedding Planning -- Hi Holden](https://hiholden.com/blogs/all/the-dos-don-ts-of-disability-wedding-planning)

### Post-Wedding Tasks
- [8 Things Couples Forget After Wedding -- Bespoke Bride](https://www.bespoke-bride.com/2026/03/03/after-the-wedding-in-2026-8-things-couples-forget-to-do-and-how-to-make-them-easy/)
- [Post-Wedding To-Do List -- Wedivite](https://blog.wedivite.com/after-the-wedding/)
- [15 Post-Wedding Must-Do Tasks -- Trusted Wedding Gown Preservation](https://www.trustedweddinggownpreservation.com/blogs/news/your-post-wedding-checklist-15-must-do-tasks-you-shouldn-t-miss)

### Timeline & Logistics
- [12 Wedding Timeline Mistakes -- Woman Getting Married](https://www.womangettingmarried.com/wedding-timeline-mistakes-that-will-ruin-your-photos-and-how-to-avoid-them/)
- [Complete Wedding Signage Checklist -- iCustomLabel](https://icustomlabel.com/blogs/wedding-decor-and-gifts/complete-wedding-signage-checklist)
- [Wedding Decor Checklist -- Esselle Weddings](https://www.esselleweddings.com/esselle-blog/2025/5/20/dont-forget-these-a-wedding-decor-checklist-for-things-that-couples-can-often-forget-to-consider)
- [Most Commonly Forgotten Details -- The Springs](https://springsvenue.com/the-most-commonly-forgotten-wedding-planning-details/)
- [10 Details Couples Forget -- Commonwealth Commerce](https://commonwealthcommerce.com/details-couples-often-forget-when-planning-a-wedding-10-gentle-reminders/)
