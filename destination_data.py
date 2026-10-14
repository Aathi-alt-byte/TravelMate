ADDITIONS = [
    ("Kanyakumari","Tamil Nadu","photo-1501785888041-af3ef285b470","Where three seas meet beneath a wide southern sky.","Nature",3600),
    ("Mahabalipuram","Tamil Nadu","photo-1518005020951-eccb494ad742","Shoreline temples and stone-carved stories.","Heritage",3400),
    ("Rameswaram","Tamil Nadu","photo-1470770841072-f978cf4d019e","Pilgrimage heritage and long bridges over the sea.","Culture",3300),
    ("Valparai","Tamil Nadu","photo-1472396961693-142e6e269027","Quiet tea estates and forested mountain roads.","Nature",3100),
    ("Yercaud","Tamil Nadu","photo-1500534623283-312aade485b7","A gentle hill escape among coffee and orange groves.","Nature",2600),
    ("Madurai","Tamil Nadu","photo-1564507592333-c60657eea523","Temple towers, busy bazaars, and celebrated Tamil food.","Cities",3000),
    ("Thanjavur","Tamil Nadu","photo-1518005020951-eccb494ad742","Chola-era architecture and a deep classical arts tradition.","Heritage",2900),
    ("Chennai","Tamil Nadu","photo-1519608487953-e999c86e7455","A coastal city with heritage neighbourhoods and beaches.","Cities",3800),
    ("Alleppey","Kerala","photo-1500375592092-40eb2168fd21","Backwaters, canals, and slow days on the water.","Nature",3900),
    ("Wayanad","Kerala","photo-1472396961693-142e6e269027","Forest trails, waterfalls, and highland scenery.","Nature",3400),
    ("Kochi","Kerala","photo-1518005020951-eccb494ad742","A harbour city shaped by layered maritime histories.","Cities",4200),
    ("Thekkady","Kerala","photo-1500530855697-b586d89ba3ee","Spice gardens and forest experiences near Periyar.","Nature",3600),
    ("Varkala","Kerala","photo-1507525428034-b723cf961d3e","Clifftop walks and relaxed Arabian Sea beaches.","Beaches",3700),
    ("Coorg","Karnataka","photo-1593693397690-362cb9666fc2","Coffee country, wooded hills, and easy-going homestays.","Nature",3500),
    ("Hampi","Karnataka","photo-1464822759023-fed622ff2c3b","A remarkable landscape of Vijayanagara-era monuments.","Heritage",3200),
    ("Gokarna","Karnataka","photo-1519046904884-53103b34b206","Coastal trails connect beaches and a small temple town.","Beaches",3300),
    ("Chikmagalur","Karnataka","photo-1470770841072-f978cf4d019e","Coffee estates and cloud-brushed Western Ghats peaks.","Nature",3400),
    ("Shimla","Himachal Pradesh","photo-1501785888041-af3ef285b470","Colonial-era streets and mountain views in the former summer capital.","Mountains",4300),
    ("Jaipur","Rajasthan","photo-1564507592333-c60657eea523","Pink-hued streets, forts, and craft-filled markets.","Cities",4100),
    ("Agra","Uttar Pradesh","photo-1518005020951-eccb494ad742","Mughal monuments and gardens along the Yamuna.","Heritage",3900),
    ("Varanasi","Uttar Pradesh","photo-1519608487953-e999c86e7455","A living riverfront city with centuries of cultural traditions.","Culture",3500),
    ("Rishikesh","Uttarakhand","photo-1470770841072-f978cf4d019e","Riverfront ashrams, foothill trails, and outdoor activities.","Adventure",3600),
    ("Darjeeling","West Bengal","photo-1464822759023-fed622ff2c3b","Tea gardens and Himalayan views from a mountain town.","Mountains",3900),
    ("Srinagar","Jammu and Kashmir","photo-1501785888041-af3ef285b470","Lakefront gardens and mountain scenery in the Kashmir Valley.","Mountains",4800),
    ("Andaman Islands","Andaman and Nicobar Islands","photo-1507525428034-b723cf961d3e","Island beaches, marine life, and a slower coastal pace.","Beaches",6200),
]

# (best season, suggested days, approximate ground travel from nearest major gateway,
#  attractions, regional foods). Cost figures are planning estimates in INR.
HINTS = {
"Kanyakumari":("October to March",2,1800,"Vivekananda Rock Memorial|Thiruvalluvar Statue|Sunset Point","Kanyakumari fish curry|Appam with stew|Banana chips"),
"Mahabalipuram":("November to February",2,1200,"Shore Temple|Pancha Rathas|Arjuna's Penance","South Indian seafood|Filter coffee|Sundal"),
"Rameswaram":("October to April",2,1600,"Ramanathaswamy Temple|Pamban Bridge|Dhanushkodi","Prawn curry|Meen kuzhambu|South Indian thali"),
"Valparai":("September to March",3,2200,"Aliyar Dam|Nallamudi Viewpoint|Sholayar Dam","Kongunadu meals|Tea|Local banana fritters"),
"Yercaud":("October to June",2,900,"Yercaud Lake|Lady's Seat|Pagoda Point","Pepper chicken|Coffee|Hill-grown fruit"),
"Madurai":("October to March",2,700,"Meenakshi Amman Temple|Thirumalai Nayakkar Palace|Gandhi Memorial Museum","Jigarthanda|Kari dosa|Paruthi paal"),
"Thanjavur":("November to February",2,900,"Brihadisvara Temple|Thanjavur Palace|Saraswathi Mahal Library","Thavala vadai|Thanjavur meals|Filter coffee"),
"Chennai":("November to February",3,500,"Marina Beach|Kapaleeshwarar Temple|Government Museum","Idli and sambar|Filter coffee|Chennai biryani"),
"Alleppey":("October to March",2,2200,"Alappuzha Beach|Backwater canals|Pathiramanal Island","Karimeen pollichathu|Appam and stew|Toddy-shop meals"),
"Wayanad":("October to May",3,1800,"Edakkal Caves|Soochipara Falls|Pookode Lake","Malabar biryani|Puttu and kadala|Wayanad coffee"),
"Kochi":("October to March",3,600,"Fort Kochi|Mattancherry Palace|Chinese fishing nets","Appam and stew|Kerala fish curry|Pazham pori"),
"Thekkady":("October to March",2,1700,"Periyar Tiger Reserve|Kumily spice market|Mangala Devi viewpoint","Kerala sadya|Spiced tea|Appam and stew"),
"Varkala":("October to March",2,1500,"Varkala Cliff|Papanasam Beach|Janardanaswamy Temple","Kerala fish curry|Appam|Banana fritters"),
"Coorg":("October to March",3,2000,"Abbey Falls|Raja's Seat|Madikeri Fort","Pandi curry|Kadambuttu|Coorg coffee"),
"Hampi":("October to February",3,1900,"Virupaksha Temple|Vittala Temple|Hampi Bazaar","Jolada rotti|North Karnataka meals|Benne dosa"),
"Gokarna":("October to March",2,1600,"Mahabaleshwar Temple|Kudle Beach|Om Beach","Konkani fish curry|Neer dosa|Coconut sweets"),
"Chikmagalur":("September to March",3,1700,"Mullayanagiri|Baba Budangiri|Hebbe Falls","Akki rotti|Malanadu chicken|Coffee"),
"Shimla":("March to June; October to November",3,1800,"The Ridge|Jakhoo Temple|Kalka-Shimla Railway","Madra|Siddu|Chha gosht"),
"Jaipur":("October to March",3,900,"Amber Fort|Hawa Mahal|City Palace","Dal baati churma|Pyaaz kachori|Ghewar"),
"Agra":("October to March",2,1000,"Taj Mahal|Agra Fort|Fatehpur Sikri","Petha|Bedai and jalebi|Mughlai cuisine"),
"Varanasi":("October to March",3,700,"Kashi Vishwanath Temple|Dashashwamedh Ghat|Sarnath","Kachori sabzi|Tamatar chaat|Banarasi lassi"),
"Rishikesh":("September to November; February to May",3,1000,"Triveni Ghat|Ram Jhula|Neer Garh Waterfall","Aloo puri|Garhwali thali|Local sweets"),
"Darjeeling":("March to May; October to November",3,1800,"Darjeeling Himalayan Railway|Tiger Hill|Batasia Loop","Momos|Thukpa|Darjeeling tea"),
"Srinagar":("April to October",3,2200,"Dal Lake|Mughal Gardens|Shankaracharya Temple","Kashmiri wazwan|Kahwa|Dum aloo"),
"Andaman Islands":("November to April",5,6500,"Cellular Jail|Radhanagar Beach|Mahatma Gandhi Marine National Park","Seafood curry|Coconut dishes|Andaman fish fry"),
}

def build_profiles():
    profiles = {}
    for row in ADDITIONS:
        name, region, image_id, description, category, daily_cost = row
        best_time, days, travel_cost, attractions, foods = HINTS[name]
        names = attractions.split("|")
        gallery = [(image_id, name + " landscape", "Explore " + name)]
        gallery += [
            ("photo-1470770841072-f978cf4d019e", "Landscape near " + name, "Local scenery"),
            ("photo-1500534623283-312aade485b7", "Outdoor views near " + name, "A change of pace"),
        ]
        profiles[name] = {
            "best_time": best_time,
            "duration_days": days,
            "travel_cost": travel_cost,
            "attractions": [(n, "A popular place to visit in " + name + "; check local access and hours before you go.") for n in names],
            "activities": ["Explore " + names[0], "Take time for a local food stop", "Enjoy a relaxed walk around " + name],
            "local_food": foods.split("|"),
            "gallery": gallery,
            "stays": [("Guesthouse", "Simple stay; verify facilities and availability.", int(daily_cost*.55)),
                      ("Comfort hotel", "Mid-range stay type; rates vary by date.", int(daily_cost*1.15)),
                      ("Premium stay", "Higher-comfort stay type; rates vary by date.", int(daily_cost*2.3))],
            "expenses": [("Accommodation", int(daily_cost*.4)), ("Meals", int(daily_cost*.25)),
                         ("Local transport", int(daily_cost*.15)), ("Activities", daily_cost-int(daily_cost*.8))],
            "transport": "Compare current rail, road, and air connections to the nearest regional gateway. Local access, schedules, and fares vary; confirm them for your dates.",
            "season_note": "Seasonal conditions vary. Check current weather, local advisories, and opening schedules before travel.",
        }
    return profiles

DESTINATION_PROFILES = build_profiles()
