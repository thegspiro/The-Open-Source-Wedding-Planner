"""
Wedding Templates - Pre-configured setups for common wedding types
"""

CEREMONY_TEMPLATES = {
    # Religious Templates
    'catholic': {
        'name': 'Catholic Wedding Ceremony',
        'category': 'religious',
        'tags': ['traditional', 'religious', 'formal'],
        'description': 'Traditional Catholic wedding mass with full ceremony elements',
        'typical_duration': 60,
        'timeline': [
            {'order': 1, 'name': 'Seating of Guests', 'duration': 300, 'description': 'Guests arrive and are seated'},
            {'order': 2, 'name': 'Seating of Mothers', 'duration': 120, 'description': 'Mothers are escorted to their seats'},
            {'order': 3, 'name': 'Processional', 'duration': 240, 'description': 'Wedding party and couple enter'},
            {'order': 4, 'name': 'Opening Prayer', 'duration': 180, 'description': 'Priest begins the ceremony'},
            {'order': 5, 'name': 'First Reading', 'duration': 120, 'description': 'Scripture reading'},
            {'order': 6, 'name': 'Responsorial Psalm', 'duration': 120, 'description': 'Sung response'},
            {'order': 7, 'name': 'Second Reading', 'duration': 120, 'description': 'Scripture reading'},
            {'order': 8, 'name': 'Gospel', 'duration': 180, 'description': 'Gospel reading by priest'},
            {'order': 9, 'name': 'Homily', 'duration': 600, 'description': 'Sermon by priest'},
            {'order': 10, 'name': 'Exchange of Vows', 'duration': 300, 'description': 'Couple exchanges vows'},
            {'order': 11, 'name': 'Blessing and Exchange of Rings', 'duration': 180, 'description': 'Ring ceremony'},
            {'order': 12, 'name': 'Prayers of the Faithful', 'duration': 240, 'description': 'Community prayers'},
            {'order': 13, 'name': 'Nuptial Blessing', 'duration': 180, 'description': 'Blessing over the couple'},
            {'order': 14, 'name': 'Sign of Peace', 'duration': 120, 'description': 'Exchange of peace'},
            {'order': 15, 'name': 'Pronouncement', 'duration': 60, 'description': 'Declared married'},
            {'order': 16, 'name': 'First Kiss', 'duration': 30, 'description': 'The kiss!'},
            {'order': 17, 'name': 'Recessional', 'duration': 180, 'description': 'Couple and party exit'},
        ],
        'music_suggestions': {
            'processional': 'Canon in D, Pachelbel',
            'recessional': 'Wedding March, Mendelssohn'
        }
    },
    
    'jewish': {
        'name': 'Jewish Wedding Ceremony',
        'category': 'religious',
        'tags': ['traditional', 'religious', 'cultural'],
        'description': 'Traditional Jewish wedding under the chuppah',
        'typical_duration': 45,
        'timeline': [
            {'order': 1, 'name': 'Guests Arrive', 'duration': 300, 'description': 'Guests gather'},
            {'order': 2, 'name': 'Bedeken (Veiling)', 'duration': 300, 'description': 'Groom veils bride'},
            {'order': 3, 'name': 'Processional', 'duration': 240, 'description': 'Procession to chuppah'},
            {'order': 4, 'name': 'Circling', 'duration': 180, 'description': 'Bride circles groom (traditionally 7 times)'},
            {'order': 5, 'name': 'Betrothal Blessings', 'duration': 240, 'description': 'First cup of wine, blessings'},
            {'order': 6, 'name': 'Ring Ceremony', 'duration': 180, 'description': 'Exchange of rings'},
            {'order': 7, 'name': 'Ketubah Reading', 'duration': 300, 'description': 'Marriage contract is read'},
            {'order': 8, 'name': 'Seven Blessings (Sheva Brachot)', 'duration': 420, 'description': 'Seven wedding blessings'},
            {'order': 9, 'name': 'Breaking the Glass', 'duration': 60, 'description': 'Groom breaks glass'},
            {'order': 10, 'name': 'Mazel Tov!', 'duration': 60, 'description': 'Celebration begins'},
            {'order': 11, 'name': 'Yichud', 'duration': 600, 'description': 'Couple spends time alone together'},
        ],
        'music_suggestions': {
            'processional': 'Erev Shel Shoshanim',
            'recessional': 'Hava Nagila'
        },
        'unity_ceremony': 'breaking_glass'
    },
    
    'protestant': {
        'name': 'Protestant Wedding Ceremony',
        'category': 'religious',
        'tags': ['traditional', 'religious'],
        'description': 'Traditional Protestant church wedding',
        'typical_duration': 30,
        'timeline': [
            {'order': 1, 'name': 'Seating of Guests', 'duration': 300, 'description': 'Guests arrive and are seated'},
            {'order': 2, 'name': 'Seating of Grandparents', 'duration': 120, 'description': 'Grandparents seated'},
            {'order': 3, 'name': 'Seating of Parents', 'duration': 120, 'description': 'Parents seated'},
            {'order': 4, 'name': 'Processional', 'duration': 240, 'description': 'Wedding party enters'},
            {'order': 5, 'name': 'Opening Words', 'duration': 120, 'description': 'Minister opens ceremony'},
            {'order': 6, 'name': 'Prayer', 'duration': 120, 'description': 'Opening prayer'},
            {'order': 7, 'name': 'Scripture Reading', 'duration': 180, 'description': 'Biblical passage'},
            {'order': 8, 'name': 'Message/Sermon', 'duration': 420, 'description': 'Brief message about marriage'},
            {'order': 9, 'name': 'Declaration of Intent', 'duration': 120, 'description': 'Do you take this person...'},
            {'order': 10, 'name': 'Exchange of Vows', 'duration': 240, 'description': 'Personal or traditional vows'},
            {'order': 11, 'name': 'Ring Exchange', 'duration': 180, 'description': 'Exchange of rings'},
            {'order': 12, 'name': 'Unity Candle', 'duration': 180, 'description': 'Lighting of unity candle'},
            {'order': 13, 'name': 'Pronouncement', 'duration': 60, 'description': 'Declared husband and wife'},
            {'order': 14, 'name': 'First Kiss', 'duration': 30, 'description': 'The kiss!'},
            {'order': 15, 'name': 'Presentation', 'duration': 60, 'description': 'Introduction as married couple'},
            {'order': 16, 'name': 'Recessional', 'duration': 180, 'description': 'Exit as married couple'},
        ],
        'music_suggestions': {
            'processional': 'Jesu, Joy of Man\'s Desiring',
            'recessional': 'Ode to Joy'
        },
        'unity_ceremony': 'unity_candle'
    },
    
    # Secular Templates
    'modern_secular': {
        'name': 'Modern Secular Ceremony',
        'category': 'secular',
        'tags': ['modern', 'nonreligious', 'personalized'],
        'description': 'Contemporary non-religious ceremony with personalized elements',
        'typical_duration': 25,
        'timeline': [
            {'order': 1, 'name': 'Guests Arrive', 'duration': 300, 'description': 'Guests mingle and find seats'},
            {'order': 2, 'name': 'Processional', 'duration': 180, 'description': 'Wedding party and couple enter'},
            {'order': 3, 'name': 'Welcome', 'duration': 120, 'description': 'Officiant welcomes everyone'},
            {'order': 4, 'name': 'Opening Words', 'duration': 180, 'description': 'About the couple and marriage'},
            {'order': 5, 'name': 'Reading or Poem', 'duration': 120, 'description': 'Meaningful reading by friend/family'},
            {'order': 6, 'name': 'Personal Vows', 'duration': 300, 'description': 'Couple exchanges personal vows'},
            {'order': 7, 'name': 'Ring Exchange', 'duration': 180, 'description': 'Exchange of rings with personal words'},
            {'order': 8, 'name': 'Unity Ceremony', 'duration': 180, 'description': 'Sand ceremony or other symbolic act'},
            {'order': 9, 'name': 'Pronouncement', 'duration': 60, 'description': 'Declared married!'},
            {'order': 10, 'name': 'Kiss', 'duration': 30, 'description': 'Sealed with a kiss'},
            {'order': 11, 'name': 'Celebration', 'duration': 60, 'description': 'Cheers and applause'},
            {'order': 12, 'name': 'Recessional', 'duration': 120, 'description': 'Exit together'},
        ],
        'music_suggestions': {
            'processional': 'Contemporary love song of choice',
            'recessional': 'Upbeat celebration song'
        },
        'unity_ceremony': 'sand_ceremony'
    },
    
    'simple_secular': {
        'name': 'Simple Secular Ceremony',
        'category': 'secular',
        'tags': ['simple', 'nonreligious', 'brief'],
        'description': 'Short, sweet, and meaningful non-religious ceremony',
        'typical_duration': 15,
        'timeline': [
            {'order': 1, 'name': 'Guests Gather', 'duration': 180, 'description': 'Informal gathering'},
            {'order': 2, 'name': 'Processional', 'duration': 120, 'description': 'Couple enters together or separately'},
            {'order': 3, 'name': 'Welcome', 'duration': 60, 'description': 'Brief welcome by officiant'},
            {'order': 4, 'name': 'Vows', 'duration': 180, 'description': 'Exchange of simple vows'},
            {'order': 5, 'name': 'Rings', 'duration': 120, 'description': 'Ring exchange'},
            {'order': 6, 'name': 'Pronouncement', 'duration': 30, 'description': 'You\'re married!'},
            {'order': 7, 'name': 'Kiss', 'duration': 20, 'description': 'The kiss'},
            {'order': 8, 'name': 'Celebration', 'duration': 60, 'description': 'Cheers!'},
        ],
        'music_suggestions': {
            'processional': 'Acoustic guitar or simple instrumental',
            'recessional': 'Favorite song'
        }
    },
    
    'courthouse': {
        'name': 'Courthouse/Civil Ceremony',
        'category': 'secular',
        'tags': ['simple', 'legal', 'brief', 'intimate'],
        'description': 'Quick legal ceremony at courthouse or with justice of the peace',
        'typical_duration': 10,
        'timeline': [
            {'order': 1, 'name': 'Gathering', 'duration': 120, 'description': 'Small group gathers (usually 2-10 people)'},
            {'order': 2, 'name': 'Legal Declaration', 'duration': 60, 'description': 'Officiant begins ceremony'},
            {'order': 3, 'name': 'Vows', 'duration': 120, 'description': 'Repeat after me...'},
            {'order': 4, 'name': 'Ring Exchange', 'duration': 60, 'description': 'Exchange rings (optional)'},
            {'order': 5, 'name': 'Pronouncement', 'duration': 30, 'description': 'Legally married'},
            {'order': 6, 'name': 'Kiss', 'duration': 15, 'description': 'Quick kiss'},
            {'order': 7, 'name': 'Paperwork', 'duration': 300, 'description': 'Sign marriage license'},
        ],
        'music_suggestions': None,
        'note': 'Even though this is simple, you can still have a reception celebration!'
    },
    
    # Cultural Templates
    'hindu': {
        'name': 'Hindu Wedding Ceremony',
        'category': 'religious',
        'tags': ['traditional', 'religious', 'cultural', 'indian'],
        'description': 'Traditional Hindu wedding with key ritual elements',
        'typical_duration': 120,
        'timeline': [
            {'order': 1, 'name': 'Baraat (Groom\'s Procession)', 'duration': 1800, 'description': 'Groom arrives with family and friends'},
            {'order': 2, 'name': 'Milni', 'duration': 600, 'description': 'Families meet and exchange gifts'},
            {'order': 3, 'name': 'Ganesh Puja', 'duration': 900, 'description': 'Prayers to Lord Ganesh'},
            {'order': 4, 'name': 'Kanya Aagaman', 'duration': 300, 'description': 'Bride\'s entrance'},
            {'order': 5, 'name': 'Jai Mala', 'duration': 600, 'description': 'Exchange of garlands'},
            {'order': 6, 'name': 'Kanyadaan', 'duration': 900, 'description': 'Giving away of the bride'},
            {'order': 7, 'name': 'Vivah Homa', 'duration': 1200, 'description': 'Sacred fire ceremony'},
            {'order': 8, 'name': 'Saptapadi (Seven Steps)', 'duration': 1200, 'description': 'Seven vows while circling fire'},
            {'order': 9, 'name': 'Sindoor and Mangalsutra', 'duration': 300, 'description': 'Symbols of marriage'},
            {'order': 10, 'name': 'Aashirvad', 'duration': 600, 'description': 'Blessings from elders'},
        ],
        'music_suggestions': {
            'processional': 'Traditional Indian wedding music',
            'recessional': 'Celebration music'
        }
    },
}

RECEPTION_TEMPLATES = {
    'formal_dinner': {
        'name': 'Formal Sit-Down Dinner',
        'tags': ['formal', 'traditional', 'elegant'],
        'description': 'Classic formal reception with plated dinner service',
        'typical_duration': 300,  # 5 hours
        'catering_style': 'plated',
        'bar_service': 'open',
        'timeline': [
            {'order': 1, 'name': 'Cocktail Hour', 'duration': 3600, 'description': 'Guests mingle, appetizers served'},
            {'order': 2, 'name': 'Grand Entrance', 'duration': 300, 'description': 'Wedding party and couple introduced'},
            {'order': 3, 'name': 'First Dance', 'duration': 240, 'description': 'Couple\'s first dance as married'},
            {'order': 4, 'name': 'Welcome Toast', 'duration': 300, 'description': 'Welcome and thank you from couple'},
            {'order': 5, 'name': 'Dinner Service', 'duration': 3600, 'description': 'Multi-course plated dinner'},
            {'order': 6, 'name': 'Toasts', 'duration': 900, 'description': 'Speeches from honor attendants'},
            {'order': 7, 'name': 'Parent Dances', 'duration': 480, 'description': 'Special dances with parents'},
            {'order': 8, 'name': 'Cake Cutting', 'duration': 300, 'description': 'Cutting and serving of cake'},
            {'order': 9, 'name': 'Open Dancing', 'duration': 5400, 'description': 'Dance floor opens to all guests'},
            {'order': 10, 'name': 'Bouquet & Garter Toss', 'duration': 600, 'description': 'Traditional tosses (optional)'},
            {'order': 11, 'name': 'Last Dance', 'duration': 240, 'description': 'Final song'},
            {'order': 12, 'name': 'Grand Exit', 'duration': 300, 'description': 'Sparkler send-off or grand exit'},
        ]
    },
    
    'cocktail_party': {
        'name': 'Cocktail Party Reception',
        'tags': ['modern', 'casual', 'mingling'],
        'description': 'Sophisticated cocktail-style reception with heavy appetizers',
        'typical_duration': 240,  # 4 hours
        'catering_style': 'stations',
        'bar_service': 'open',
        'timeline': [
            {'order': 1, 'name': 'Doors Open', 'duration': 1800, 'description': 'Guests arrive and begin mingling'},
            {'order': 2, 'name': 'Couple Entrance', 'duration': 180, 'description': 'Couple makes entrance'},
            {'order': 3, 'name': 'Welcome & Toast', 'duration': 300, 'description': 'Brief welcome'},
            {'order': 4, 'name': 'First Dance', 'duration': 240, 'description': 'Couple\'s dance'},
            {'order': 5, 'name': 'Open Mingling', 'duration': 7200, 'description': 'Guests mingle, food stations available'},
            {'order': 6, 'name': 'Cake Cutting', 'duration': 300, 'description': 'Cake moment'},
            {'order': 7, 'name': 'Dancing', 'duration': 3600, 'description': 'Dance floor open'},
            {'order': 8, 'name': 'Farewell', 'duration': 180, 'description': 'Couple exits'},
        ]
    },
    
    'backyard_bbq': {
        'name': 'Backyard BBQ Reception',
        'tags': ['casual', 'outdoor', 'relaxed'],
        'description': 'Laid-back outdoor celebration with BBQ-style food',
        'typical_duration': 240,
        'catering_style': 'buffet',
        'bar_service': 'limited',
        'timeline': [
            {'order': 1, 'name': 'Guests Arrive', 'duration': 1800, 'description': 'Casual arrival, lawn games available'},
            {'order': 2, 'name': 'Couple Arrival', 'duration': 120, 'description': 'Newlyweds join the party'},
            {'order': 3, 'name': 'Welcome', 'duration': 180, 'description': 'Casual welcome and thank you'},
            {'order': 4, 'name': 'Buffet Opens', 'duration': 3600, 'description': 'BBQ buffet service'},
            {'order': 5, 'name': 'Toasts', 'duration': 600, 'description': 'Informal toasts'},
            {'order': 6, 'name': 'Cake & Dessert', 'duration': 1200, 'description': 'Cake cutting and dessert'},
            {'order': 7, 'name': 'Music & Mingling', 'duration': 5400, 'description': 'Music, dancing, yard games'},
            {'order': 8, 'name': 'Goodbye', 'duration': 300, 'description': 'Casual farewell'},
        ]
    },
    
    'brunch_reception': {
        'name': 'Morning/Brunch Reception',
        'tags': ['daytime', 'brunch', 'casual'],
        'description': 'Daytime celebration with brunch-style food',
        'typical_duration': 180,  # 3 hours
        'catering_style': 'buffet',
        'bar_service': 'limited',  # mimosas, bellinis
        'timeline': [
            {'order': 1, 'name': 'Arrival', 'duration': 1200, 'description': 'Guests arrive, coffee and pastries'},
            {'order': 2, 'name': 'Couple Entrance', 'duration': 180, 'description': 'Newlyweds arrive'},
            {'order': 3, 'name': 'Welcome Toast', 'duration': 240, 'description': 'Morning toast with mimosas'},
            {'order': 4, 'name': 'Brunch Service', 'duration': 3600, 'description': 'Brunch buffet'},
            {'order': 5, 'name': 'Toasts', 'duration': 600, 'description': 'Speeches'},
            {'order': 6, 'name': 'Cake Cutting', 'duration': 300, 'description': 'Cake served with coffee'},
            {'order': 7, 'name': 'Mingling', 'duration': 2400, 'description': 'Relaxed socializing'},
            {'order': 8, 'name': 'Farewell', 'duration': 300, 'description': 'Send-off'},
        ]
    },
    
    'destination_beach': {
        'name': 'Beach/Destination Reception',
        'tags': ['beach', 'destination', 'outdoor', 'casual'],
        'description': 'Relaxed beach or destination celebration',
        'typical_duration': 240,
        'catering_style': 'buffet',
        'bar_service': 'open',
        'timeline': [
            {'order': 1, 'name': 'Beach Gathering', 'duration': 1800, 'description': 'Guests gather on beach'},
            {'order': 2, 'name': 'Couple Arrival', 'duration': 180, 'description': 'Couple joins celebration'},
            {'order': 3, 'name': 'Beach Toast', 'duration': 300, 'description': 'Toast at sunset'},
            {'order': 4, 'name': 'Dinner Service', 'duration': 3600, 'description': 'Seafood buffet or local cuisine'},
            {'order': 5, 'name': 'Beach Bonfire', 'duration': 5400, 'description': 'Bonfire, music, s\'mores'},
            {'order': 6, 'name': 'Dancing', 'duration': 3600, 'description': 'Dancing under the stars'},
        ]
    },
    
    'no_reception': {
        'name': 'Ceremony Only (No Reception)',
        'tags': ['simple', 'ceremony-only'],
        'description': 'Just the ceremony, no formal reception',
        'typical_duration': 0,
        'note': 'Some couples choose to celebrate privately or have a casual gathering later!'
    }
}

BUDGET_TEMPLATES = {
    'budget_5k': {
        'name': 'Micro Wedding ($5,000)',
        'total': 5000,
        'guest_count': '20-30',
        'description': 'Intimate celebration with closest family and friends',
        'expenses': [
            {'category': 'Venue', 'percentage': 15, 'amount': 750},
            {'category': 'Catering', 'percentage': 30, 'amount': 1500},
            {'category': 'Photography', 'percentage': 20, 'amount': 1000},
            {'category': 'Attire', 'percentage': 10, 'amount': 500},
            {'category': 'Flowers & Decor', 'percentage': 10, 'amount': 500},
            {'category': 'Music/DJ', 'percentage': 5, 'amount': 250},
            {'category': 'Invitations & Stationery', 'percentage': 3, 'amount': 150},
            {'category': 'Miscellaneous', 'percentage': 7, 'amount': 350},
        ]
    },
    
    'budget_15k': {
        'name': 'Small Wedding ($15,000)',
        'total': 15000,
        'guest_count': '50-75',
        'description': 'Thoughtful celebration for close circle',
        'expenses': [
            {'category': 'Venue', 'percentage': 15, 'amount': 2250},
            {'category': 'Catering', 'percentage': 35, 'amount': 5250},
            {'category': 'Photography/Videography', 'percentage': 12, 'amount': 1800},
            {'category': 'Flowers & Decor', 'percentage': 10, 'amount': 1500},
            {'category': 'Music/DJ', 'percentage': 8, 'amount': 1200},
            {'category': 'Attire', 'percentage': 8, 'amount': 1200},
            {'category': 'Invitations & Stationery', 'percentage': 3, 'amount': 450},
            {'category': 'Cake', 'percentage': 2, 'amount': 300},
            {'category': 'Transportation', 'percentage': 2, 'amount': 300},
            {'category': 'Miscellaneous', 'percentage': 5, 'amount': 750},
        ]
    },
    
    'budget_30k': {
        'name': 'Medium Wedding ($30,000)',
        'total': 30000,
        'guest_count': '100-125',
        'description': 'Full celebration with all traditional elements',
        'expenses': [
            {'category': 'Venue', 'percentage': 15, 'amount': 4500},
            {'category': 'Catering', 'percentage': 30, 'amount': 9000},
            {'category': 'Photography/Videography', 'percentage': 12, 'amount': 3600},
            {'category': 'Flowers & Decor', 'percentage': 10, 'amount': 3000},
            {'category': 'Music/DJ or Band', 'percentage': 8, 'amount': 2400},
            {'category': 'Attire', 'percentage': 7, 'amount': 2100},
            {'category': 'Invitations & Stationery', 'percentage': 3, 'amount': 900},
            {'category': 'Cake', 'percentage': 2, 'amount': 600},
            {'category': 'Transportation', 'percentage': 2, 'amount': 600},
            {'category': 'Hair & Makeup', 'percentage': 2, 'amount': 600},
            {'category': 'Favors & Gifts', 'percentage': 2, 'amount': 600},
            {'category': 'Miscellaneous', 'percentage': 7, 'amount': 2100},
        ]
    },
    
    'budget_50k_plus': {
        'name': 'Large Wedding ($50,000+)',
        'total': 50000,
        'guest_count': '150+',
        'description': 'Grand celebration with premium vendors',
        'expenses': [
            {'category': 'Venue', 'percentage': 12, 'amount': 6000},
            {'category': 'Catering', 'percentage': 30, 'amount': 15000},
            {'category': 'Photography/Videography', 'percentage': 12, 'amount': 6000},
            {'category': 'Flowers & Decor', 'percentage': 10, 'amount': 5000},
            {'category': 'Music/Band', 'percentage': 10, 'amount': 5000},
            {'category': 'Attire', 'percentage': 6, 'amount': 3000},
            {'category': 'Invitations & Stationery', 'percentage': 3, 'amount': 1500},
            {'category': 'Cake', 'percentage': 2, 'amount': 1000},
            {'category': 'Transportation & Valet', 'percentage': 3, 'amount': 1500},
            {'category': 'Hair & Makeup', 'percentage': 2, 'amount': 1000},
            {'category': 'Wedding Planner', 'percentage': 5, 'amount': 2500},
            {'category': 'Favors & Gifts', 'percentage': 2, 'amount': 1000},
            {'category': 'Miscellaneous', 'percentage': 3, 'amount': 1500},
        ]
    }
}
