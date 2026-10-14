import json
import os
import secrets
import sqlite3
import hmac
from datetime import date, timedelta

from flask import Flask, abort, g, jsonify, redirect, render_template, request, session, url_for
from settings import BASE_DIR, DATABASE_PATH

DESTINATIONS = [
    ("Ooty", "Tamil Nadu", "photo-1597074866923-dc0589150358", "Misty mornings above the Nilgiri hills.", "Mountains", 2800),
    ("Goa", "Goa", "photo-1519046904884-53103b34b206", "Slow days, salt air, and golden sunsets.", "Beaches", 3500),
    ("Munnar", "Kerala", "photo-1593693397690-362cb9666fc2", "A greener kind of getaway in the tea country.", "Nature", 3200),
    ("Kodaikanal", "Tamil Nadu", "photo-1500534623283-312aade485b7", "Pine-scented trails and quiet lake views.", "Nature", 2600),
    ("Manali", "Himachal Pradesh", "photo-1501785888041-af3ef285b470", "Mountain air, river walks, and open skies.", "Mountains", 4000),
    ("Mysuru", "Karnataka", "photo-1518005020951-eccb494ad742", "Palace-front streets, old-world markets, and local coffee.", "Cities", 2900),
]

DESTINATION_GUIDES = {
    "Ooty": {
        "best_time": "October to June",
        "season_note": "Clear, cool days are ideal for viewpoints and tea-estate walks; carry a light layer year-round.",
        "gallery": [
            ("photo-1464822759023-fed622ff2c3b", "The Nilgiri hills", "Highland views"),
            ("photo-1470770841072-f978cf4d019e", "A quiet lake in the hills", "Lake mornings"),
            ("photo-1511497584788-876760111969", "Green forest canopy", "Forest trails"),
        ],
        "attractions": [("Nilgiri Mountain Railway", "A heritage rail journey winding through tea country."), ("Doddabetta Peak", "A high viewpoint with wide Nilgiri panoramas."), ("Ooty Lake", "A relaxed lakeside stop close to town.")],
        "activities": ["Ride a section of the heritage toy train", "Walk a tea-estate trail", "Browse the Botanical Garden"],
        "expenses": [("Room share", 900), ("Meals", 700), ("Local transport", 500), ("Sightseeing and activities", 700)],
        "transport": "Ooty is reached by road from Coimbatore or by the Nilgiri Mountain Railway from Mettupalayam. Local taxis and town buses connect the main sights; agree taxi fares before setting off.",
        "stays": [("Tea-country homestay", "Simple room · breakfast often available", 1800), ("Town guesthouse", "Comfortable base near shops and eateries", 3200), ("Hill-view retreat", "Private stay with open valley views", 6800)],
    },
    "Goa": {
        "best_time": "November to February",
        "season_note": "The dry season brings sunny beach days and busy holiday periods. Monsoon months are lush, with some beach services reduced.",
        "gallery": [("photo-1507525428034-b723cf961d3e", "A wide tropical beach", "Along the coast"), ("photo-1519046904884-53103b34b206", "The shoreline at golden hour", "Sunset hour"), ("photo-1510414842594-a61c69b5ae57", "A calm palm-fringed beach", "Salt-air afternoons")],
        "attractions": [("Fontainhas, Panaji", "Colourful lanes and heritage houses in the Latin Quarter."), ("Old Goa churches", "Landmark basilicas and centuries-old architecture."), ("South Goa beaches", "Quieter stretches of sand for an unhurried day.")],
        "activities": ["Take a sunset walk on the beach", "Explore Panaji's old quarter on foot", "Try a local fish thali or Goan vegetarian meal"],
        "expenses": [("Room share", 1200), ("Meals", 900), ("Local transport", 700), ("Sightseeing and activities", 700)],
        "transport": "Dabolim and Manohar International airports serve Goa. Rental scooters are common for confident riders; taxis, app cabs, and local buses are alternatives. Distances between north and south Goa can be longer than they appear.",
        "stays": [("Beachside hostel", "Shared or compact private room", 1600), ("Village guesthouse", "Easy-going stay with local cafes nearby", 3500), ("Coastal boutique stay", "Pool or garden setting near the shore", 8200)],
    },
    "Munnar": {
        "best_time": "September to March",
        "season_note": "Post-monsoon brings fresh green hills and comfortable sightseeing weather; mornings can be cool at higher elevations.",
        "gallery": [("photo-1593693397690-362cb9666fc2", "Green plantation country", "Tea country"), ("photo-1472396961693-142e6e269027", "A hillside landscape", "Highland quiet"), ("photo-1500530855697-b586d89ba3ee", "A misty mountain valley", "Misty mornings")],
        "attractions": [("Tea Museum", "A look at the region's long tea-growing history."), ("Eravikulam National Park", "Mountain grasslands and the Nilgiri tahr habitat; check seasonal access."), ("Mattupetty Dam", "A reservoir framed by rolling highlands.")],
        "activities": ["Join a guided tea-estate walk", "Watch sunrise from a nearby viewpoint", "Sample cardamom, tea, and Kerala snacks"],
        "expenses": [("Room share", 1150), ("Meals", 800), ("Local transport", 650), ("Sightseeing and activities", 600)],
        "transport": "The nearest major rail and air connections are around Kochi. Munnar is reached by winding hill roads; taxis and local buses serve the town, while a hired car is useful for spread-out viewpoints.",
        "stays": [("Plantation homestay", "Family-run room among tea gardens", 1900), ("Munnar town hotel", "Practical base with dining nearby", 3800), ("Valley-view resort", "Quiet hillside stay with wide views", 9000)],
    },
    "Kodaikanal": {
        "best_time": "October to March",
        "season_note": "Cooler, clearer weather suits walks and lake visits. Summer is popular too, so book transport early during holiday weeks.",
        "gallery": [("photo-1470770841072-f978cf4d019e", "A lake among the hills", "Lakeside calm"), ("photo-1501785888041-af3ef285b470", "Mountain water and green slopes", "Hill-country views"), ("photo-1511497584788-876760111969", "A shaded woodland path", "Pine-country walks")],
        "attractions": [("Kodaikanal Lake", "A star-shaped lake surrounded by a walking path."), ("Coaker's Walk", "A paved ridge walk overlooking the valley."), ("Bryant Park", "A botanical garden close to the lake.")],
        "activities": ["Walk or cycle around the lake", "Catch the valley view from Coaker's Walk", "Pack a picnic for a pine-forest trail"],
        "expenses": [("Room share", 900), ("Meals", 650), ("Local transport", 500), ("Sightseeing and activities", 550)],
        "transport": "Most visitors arrive by road from Madurai or Dindigul. Local taxis and buses connect the town and viewpoints; check return transport before visiting outlying spots.",
        "stays": [("Pine-side homestay", "Compact room near walking trails", 1700), ("Lake-area hotel", "Convenient stay close to town", 3400), ("Valley-view cottage", "Independent stay with outdoor space", 7600)],
    },
    "Manali": {
        "best_time": "March to June; October to November",
        "season_note": "Spring and autumn are popular for mountain scenery and outdoor days. Winter brings snow but road and activity conditions can change quickly.",
        "gallery": [("photo-1501785888041-af3ef285b470", "A broad Himalayan valley", "Mountain air"), ("photo-1464822759023-fed622ff2c3b", "Snow-dusted mountain peaks", "High peaks"), ("photo-1470770841072-f978cf4d019e", "A mountain lake in soft light", "Quiet waters")],
        "attractions": [("Old Manali", "A village quarter known for cafes and riverside lanes."), ("Hadimba Devi Temple", "A cedar-forest temple with distinctive timber architecture."), ("Solang Valley", "An open valley for seasonal mountain activities.")],
        "activities": ["Take a guided riverside or forest walk", "Explore Old Manali at a gentle pace", "Check local conditions before booking snow or adventure activities"],
        "expenses": [("Room share", 1500), ("Meals", 900), ("Local transport", 800), ("Sightseeing and activities", 800)],
        "transport": "Manali is connected by road, with buses and taxis from Kullu and Chandigarh. Local cabs and buses reach nearby villages; mountain roads are weather-sensitive, so leave schedule flexibility.",
        "stays": [("Backpacker guesthouse", "Simple room near the old town", 2100), ("Riverside hotel", "Comfort stay with mountain views", 4600), ("Mountain lodge", "Larger rooms and a quieter setting", 10500)],
    },
    "Mysuru": {
        "best_time": "October to March",
        "season_note": "Pleasant days suit palace visits and neighbourhood walks. Dasara is a special time to visit, though accommodation can be busier and pricier.",
        "gallery": [("photo-1518005020951-eccb494ad742", "Historic city architecture", "Heritage streets"), ("photo-1564507592333-c60657eea523", "An ornate landmark building", "Palace details"), ("photo-1519608487953-e999c86e7455", "A city beneath an open sky", "Evening in town")],
        "attractions": [("Mysuru Palace", "An ornate royal residence and the city's best-known landmark."), ("Devaraja Market", "A lively market for flowers, spices, and local produce."), ("Chamundi Hill", "A hilltop temple and viewpoint above the city.")],
        "activities": ["Visit the palace early to avoid the busiest hours", "Browse Devaraja Market with a local guide", "Try Mysore masala dosa and local sweets"],
        "expenses": [("Room share", 950), ("Meals", 750), ("Local transport", 450), ("Sightseeing and activities", 750)],
        "transport": "Mysuru is connected by train and road from Bengaluru. City buses, auto-rickshaws, and app-based cabs cover local journeys; agree on fares or use the meter where available.",
        "stays": [("Market-area guesthouse", "Simple room within the central grid", 1500), ("Heritage-style hotel", "Comfortable base near the palace quarter", 3300), ("Garden hotel", "Quieter stay with extra amenities", 7200)],
    },
}

from destination_data import ADDITIONS, DESTINATION_PROFILES
DESTINATIONS.extend(ADDITIONS)

PREFERENCE_IDEAS = {
    "Nature": ["Take a slow walk through a nearby green space", "Pause at a scenic viewpoint", "Leave time for a quiet outdoor break"],
    "Adventure": ["Try a guided outdoor activity suited to local conditions", "Set out on a moderate trail with a local guide", "Keep an active morning and an easy afternoon"],
    "Relaxation": ["Keep the morning unhurried", "Leave a generous break between stops", "Enjoy a slow evening close to your stay"],
    "Culture": ["Explore a local landmark with time to look around", "Visit a museum, heritage site, or neighbourhood", "Look for a local craft or cultural experience"],
    "Food": ["Try a local breakfast favourite", "Plan lunch around a regional dish", "Visit a market or ask a local for a dinner pick"],
}

PREFERENCE_IDEAS.update({"Beaches": ["Take a beach walk", "Plan a relaxed coast day"], "History": ["Visit a heritage landmark", "Explore a local museum or historic quarter"]})
ACCOMMODATION_OPTIONS = ("Budget", "Standard", "Luxury")
TRANSPORT_OPTIONS = ("Bus", "Train", "Car", "Flight")
TRAVEL_PREFERENCES = ("Nature", "Adventure", "Relaxation", "Culture", "Food", "Beaches", "History")

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax",
                  SESSION_COOKIE_SECURE=os.environ.get("TRAVELMATE_HTTPS", "").lower() == "true")


def csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


@app.context_processor
def inject_csrf_token():
    return {"csrf_token": csrf_token}


@app.before_request
def protect_planner_posts():
    if request.method == "POST" and request.endpoint == "plan_trip":
        supplied = request.form.get("_csrf", "")
        if not hmac.compare_digest(str(session.get("_csrf", "")), str(supplied)):
            abort(400, description="This form expired. Refresh the page and try again.")


def get_connection():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS destinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                region TEXT NOT NULL,
                image_id TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'Nature',
                daily_cost INTEGER NOT NULL DEFAULT 0, best_time TEXT NOT NULL DEFAULT '', attractions_json TEXT NOT NULL DEFAULT '[]', activities_json TEXT NOT NULL DEFAULT '[]', gallery_json TEXT NOT NULL DEFAULT '[]', expenses_json TEXT NOT NULL DEFAULT '[]', stays_json TEXT NOT NULL DEFAULT '[]', food_json TEXT NOT NULL DEFAULT '[]', transport_note TEXT NOT NULL DEFAULT '', season_note TEXT NOT NULL DEFAULT '', duration_days INTEGER NOT NULL DEFAULT 3, travel_cost INTEGER NOT NULL DEFAULT 0
            )"""
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(destinations)")}
        if "category" not in columns:
            connection.execute("ALTER TABLE destinations ADD COLUMN category TEXT NOT NULL DEFAULT 'Nature'")
        if "daily_cost" not in columns:
            connection.execute("ALTER TABLE destinations ADD COLUMN daily_cost INTEGER NOT NULL DEFAULT 0")
        for column, declaration in {
            "best_time": "TEXT NOT NULL DEFAULT ''",
            "attractions_json": "TEXT NOT NULL DEFAULT '[]'",
            "activities_json": "TEXT NOT NULL DEFAULT '[]'",
            "gallery_json": "TEXT NOT NULL DEFAULT '[]'",
            "expenses_json": "TEXT NOT NULL DEFAULT '[]'",
            "stays_json": "TEXT NOT NULL DEFAULT '[]'",
            "food_json": "TEXT NOT NULL DEFAULT '[]'",
            "transport_note": "TEXT NOT NULL DEFAULT ''",
            "season_note": "TEXT NOT NULL DEFAULT ''",
            "duration_days": "INTEGER NOT NULL DEFAULT 3",
            "travel_cost": "INTEGER NOT NULL DEFAULT 0",
        }.items():
            if column not in columns:
                connection.execute(f"ALTER TABLE destinations ADD COLUMN {column} {declaration}")
        connection.executemany(
            """INSERT OR IGNORE INTO destinations
               (name, region, image_id, description, category, daily_cost) VALUES (?, ?, ?, ?, ?, ?)""",
            DESTINATIONS,
        )
        connection.executemany(
            "UPDATE destinations SET category = ?, daily_cost = ? WHERE name = ?",
            [(category, daily_cost, name) for name, _, _, _, category, daily_cost in DESTINATIONS],
        )


        local_food = {
            "Ooty": ["Ooty varkey", "Nilgiri tea", "South Indian meals"],
            "Goa": ["Goan fish curry", "Bebinca", "Prawn balchao"],
            "Munnar": ["Appam and stew", "Kerala sadya", "Cardamom tea"],
            "Kodaikanal": ["Homemade chocolates", "Puttu and kadala", "Hill-grown fruit"],
            "Manali": ["Siddu", "Trout preparations", "Himachali dham"],
            "Mysuru": ["Mysore masala dosa", "Mysore pak", "Ragi mudde"],
        }
        for name, region, image_id, description, category, daily_cost in DESTINATIONS:
            profile = DESTINATION_PROFILES.get(name)
            if profile is None:
                guide = DESTINATION_GUIDES[name]
                profile = {"best_time": guide["best_time"], "season_note": guide["season_note"],
                    "gallery": guide["gallery"], "attractions": guide["attractions"],
                    "activities": guide["activities"], "expenses": guide["expenses"], "stays": guide["stays"],
                    "transport": guide["transport"], "local_food": local_food[name],
                    "duration_days": 3, "travel_cost": 1500}
            values = (profile["best_time"], json.dumps(profile["attractions"]), json.dumps(profile["activities"]),
                json.dumps(profile["gallery"]), json.dumps(profile["expenses"]), json.dumps(profile["stays"]),
                json.dumps(profile.get("local_food", profile.get("food", []))), profile["transport"],
                profile["season_note"], profile.get("duration_days", 3), profile.get("travel_cost", 1500), name)
            connection.execute("""UPDATE destinations SET best_time=?,attractions_json=?,activities_json=?,
                gallery_json=?,expenses_json=?,stays_json=?,food_json=?,transport_note=?,season_note=?,
                duration_days=?,travel_cost=? WHERE name=?""", values)

@app.get("/")
def home():
    with get_connection() as connection:
        destinations = connection.execute(
            "SELECT * FROM destinations ORDER BY id"
        ).fetchall()
    return render_template("index.html", destinations=destinations)


@app.get("/destinations")
def destinations():
    with get_connection() as connection:
        destination_list = connection.execute(
            "SELECT * FROM destinations ORDER BY id"
        ).fetchall()
    destination_list = [dict(row) for row in destination_list]
    for destination in destination_list:
        destination["slug"] = destination["name"].lower().replace(" ", "-")
    return render_template("destinations.html", destinations=destination_list)


@app.get("/destinations/<destination_slug>")
def destination_detail(destination_slug):
    with get_connection() as connection:
        records = connection.execute("SELECT * FROM destinations").fetchall()
    destination = next((dict(record) for record in records
        if record["name"].lower().replace(" ", "-") == destination_slug), None)
    if destination is None:
        abort(404)
    guide = {
        "best_time": destination["best_time"], "season_note": destination["season_note"],
        "gallery": json.loads(destination["gallery_json"]),
        "attractions": json.loads(destination["attractions_json"]),
        "activities": json.loads(destination["activities_json"]),
        "expenses": json.loads(destination["expenses_json"]),
        "stays": json.loads(destination["stays_json"]),
        "transport": destination["transport_note"], "food": json.loads(destination["food_json"]),
        "duration_days": destination["duration_days"], "travel_cost": destination["travel_cost"],
    }
    destination["slug"] = destination_slug
    return render_template("destination_detail.html", destination=destination, guide=guide)


@app.route("/plan", methods=["GET", "POST"])
def plan_trip():
    with get_connection() as connection:
        destination_rows = connection.execute(
            "SELECT name, region, daily_cost, travel_cost FROM destinations ORDER BY name"
        ).fetchall()
    destination_options = [dict(row) for row in destination_rows]
    destination_names = {item["name"] for item in destination_options}
    form_data = {
        "destination": request.args.get("destination", "").strip(),
        "starting_location": request.args.get("starting_location", "").strip(),
        "start_date": request.args.get("start_date", "").strip(),
        "end_date": request.args.get("end_date", "").strip(),
        "travelers": request.args.get("travelers", "2").strip(),
        "preferences": request.args.getlist("preferences"),
        "accommodation": request.args.get("accommodation", "Standard").strip(),
        "transportation": request.args.get("transportation", "Train").strip(),
        "budget": request.args.get("budget", "").strip(),
    }
    errors = {}

    if request.method == "POST":
        form_data.update({
            "destination": request.form.get("destination", "").strip(),
            "starting_location": request.form.get("starting_location", "").strip(),
            "start_date": request.form.get("start_date", "").strip(),
            "end_date": request.form.get("end_date", "").strip(),
            "travelers": request.form.get("travelers", "").strip(),
            "preferences": request.form.getlist("preferences"),
            "accommodation": request.form.get("accommodation", "").strip(),
            "transportation": request.form.get("transportation", "").strip(),
            "budget": request.form.get("budget", "").strip(),
        })

        if form_data["destination"] not in destination_names:
            errors["destination"] = "Choose a destination from the list."
        if len(form_data["starting_location"]) < 2:
            errors["starting_location"] = "Enter a starting city or town."
        elif len(form_data["starting_location"]) > 80:
            errors["starting_location"] = "Starting location must be 80 characters or fewer."

        parsed_start = None
        parsed_end = None
        for field, label in (("start_date", "Start date"), ("end_date", "End date")):
            try:
                parsed_date = date.fromisoformat(form_data[field])
                if field == "start_date":
                    parsed_start = parsed_date
                else:
                    parsed_end = parsed_date
            except ValueError:
                errors[field] = f"Choose a valid {label.lower()} from the calendar."
        if parsed_start and parsed_start < date.today():
            errors["start_date"] = "Start date cannot be in the past."
        if parsed_start and parsed_end:
            if parsed_end < parsed_start:
                errors["end_date"] = "End date must be the same day or after your start date."
            elif (parsed_end - parsed_start).days >= 30:
                errors["end_date"] = "For this planner, choose a trip of 30 days or fewer."

        travelers = None
        try:
            travelers = int(form_data["travelers"])
            if not 1 <= travelers <= 20:
                raise ValueError
        except ValueError:
            errors["travelers"] = "Choose between 1 and 20 travelers."

        selected_preferences = form_data["preferences"]
        if not selected_preferences or any(item not in TRAVEL_PREFERENCES for item in selected_preferences):
            errors["preferences"] = "Choose at least one travel preference."
        if form_data["accommodation"] not in ACCOMMODATION_OPTIONS:
            errors["accommodation"] = "Choose Budget, Standard, or Luxury accommodation."
        if form_data["transportation"] not in TRANSPORT_OPTIONS:
            errors["transportation"] = "Choose Bus, Train, Car, or Flight."

        budget = None
        try:
            budget = int(form_data["budget"])
            if not 1 <= budget <= 50000000:
                raise ValueError
        except ValueError:
            errors["budget"] = "Enter a total budget between ₹1 and ₹5,00,00,000."

        if not errors:
            destination = next(item for item in destination_options if item["name"] == form_data["destination"])
            guide = DESTINATION_PROFILES.get(form_data["destination"]) or DESTINATION_GUIDES[form_data["destination"]]
            trip_days = (parsed_end - parsed_start).days + 1
            estimated_total = (destination["daily_cost"] * travelers * trip_days) + (destination["travel_cost"] * travelers)
            itinerary_days = []
            preference_cycle = [item for item in TRAVEL_PREFERENCES if item in selected_preferences]
            for day_index in range(trip_days):
                attraction = guide["attractions"][day_index % len(guide["attractions"])][0]
                local_activity = guide["activities"][day_index % len(guide["activities"])]
                preference = preference_cycle[day_index % len(preference_cycle)]
                preference_idea = PREFERENCE_IDEAS[preference][day_index % len(PREFERENCE_IDEAS[preference])]
                itinerary_days.append({
                    "number": day_index + 1,
                    "date": (parsed_start + timedelta(days=day_index)).strftime("%a, %d %b"),
                    "morning": attraction,
                    "afternoon": local_activity,
                    "evening": preference_idea,
                })
            owner_token = session.get("itinerary_owner_token")
            if not getattr(g, "user", None) and not owner_token:
                owner_token = secrets.token_urlsafe(32)
                session["itinerary_owner_token"] = owner_token
            public_id = secrets.token_urlsafe(12)
            try:
                with get_connection() as connection:
                    connection.execute(
                        """INSERT INTO planned_itineraries
                           (public_id, user_id, owner_token, destination_name, destination_region,
                            start_date, end_date, travelers, starting_location, preferences_json,
                            accommodation, transportation, budget, estimated_total, daily_cost,
                            travel_cost, itinerary_json)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (public_id, g.user["id"] if getattr(g, "user", None) else None,
                         owner_token if not getattr(g, "user", None) else None,
                         destination["name"], destination["region"], parsed_start.isoformat(),
                         parsed_end.isoformat(), travelers, form_data["starting_location"],
                         json.dumps(selected_preferences), form_data["accommodation"],
                         form_data["transportation"], budget, estimated_total,
                         destination["daily_cost"], destination["travel_cost"],
                         json.dumps(itinerary_days)),
                    )
            except sqlite3.Error:
                app.logger.exception("Generated itinerary could not be saved")
                errors["generation"] = "We couldn't save this itinerary just now. Please try again."
            else:
                return redirect(url_for("itinerary_result", public_id=public_id))

    return render_template(
        "plan_trip.html",
        destinations=destination_options,
        form_data=form_data,
        errors=errors,
        preferences=TRAVEL_PREFERENCES,
        accommodations=ACCOMMODATION_OPTIONS,
        transport_options=TRANSPORT_OPTIONS,
        today=date.today().isoformat(),
    )


@app.get("/itinerary/<public_id>")
def itinerary_result(public_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM planned_itineraries WHERE public_id = ?", (public_id,)
        ).fetchone()
    if row is None:
        abort(404)
    user = getattr(g, "user", None)
    if row["user_id"] is not None:
        if not user or row["user_id"] != user["id"]:
            abort(404)
    elif not secrets.compare_digest(row["owner_token"] or "", session.get("itinerary_owner_token", "")):
        abort(404)

    itinerary = dict(row)
    itinerary["preferences"] = json.loads(itinerary.pop("preferences_json"))
    itinerary["days"] = json.loads(itinerary.pop("itinerary_json"))
    start_date = date.fromisoformat(row["start_date"])
    end_date = date.fromisoformat(row["end_date"])
    itinerary["trip_days"] = (end_date - start_date).days + 1
    itinerary["start_date_display"] = start_date.strftime("%d %b %Y")
    itinerary["end_date_display"] = end_date.strftime("%d %b %Y")
    itinerary["within_budget"] = row["budget"] >= row["estimated_total"]
    return render_template("itinerary.html", itinerary=itinerary)


@app.get("/budget")
def budget_calculator():
    with get_connection() as connection:
        destinations = [dict(row) for row in connection.execute(
            "SELECT name, region, daily_cost, travel_cost FROM destinations ORDER BY name"
        ).fetchall()]

    selected_destination = request.args.get("destination", "").strip()
    destination = next((item for item in destinations if item["name"] == selected_destination), None)

    def query_integer(name, default, minimum, maximum):
        try:
            value = int(request.args.get(name, default))
        except (TypeError, ValueError):
            return default
        return value if minimum <= value <= maximum else default

    daily_cost = destination["daily_cost"] if destination else 0
    transportation = daily_cost * 8 // 100
    accommodation = daily_cost * 40 // 100
    food = daily_cost * 25 // 100
    activities = daily_cost * 14 // 100
    local_transportation = daily_cost * 10 // 100
    other = daily_cost - transportation - accommodation - food - activities - local_transportation
    budget = query_integer("budget", 0, 0, 50000000)
    calculator_data = {
        "transportation": query_integer("transportation_cost", transportation, 0, 5000000),
        "local_transportation": query_integer("local_transportation_cost", local_transportation, 0, 5000000),
        "accommodation": query_integer("accommodation_cost", accommodation, 0, 5000000),
        "food": query_integer("food_cost", food, 0, 5000000),
        "activities": query_integer("activities_cost", activities, 0, 5000000),
        "other": query_integer("other_cost", other, 0, 5000000),
        "travelers": query_integer("travelers", 2, 1, 20),
        "days": query_integer("days", 3, 1, 365),
        "budget": budget or "",
    }
    return render_template(
        "budget.html",
        destinations=destinations,
        selected_destination=selected_destination if destination else "",
        calculator_data=calculator_data,
        has_destination_estimate=destination is not None,
    )


@app.get("/api/destinations")
def search_destinations():
    query = request.args.get("q", "").strip()
    with get_connection() as connection:
        if query:
            matches = connection.execute(
                     """SELECT name, region, description, category, daily_cost FROM destinations
                   WHERE name LIKE ? OR region LIKE ? ORDER BY name LIMIT 8""",
                (f"%{query}%", f"%{query}%"),
            ).fetchall()
        else:
            matches = connection.execute(
                "SELECT name, region, description, category, daily_cost FROM destinations ORDER BY name LIMIT 8"
            ).fetchall()
    return jsonify([dict(destination) for destination in matches])


from booking import booking_bp, init_booking_db
app.register_blueprint(booking_bp)

initialize_database()
init_booking_db()

@app.errorhandler(404)
def not_found(error):
    return render_template("error.html", code=404, message="The page you requested was not found."), 404

@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Please check the request and try again.")), 400

@app.errorhandler(500)
def server_error(error):
    app.logger.exception("Unhandled request error")
    return render_template("error.html", code=500, message="Something went wrong. Please try again or contact support."), 500

if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "") == "1")
