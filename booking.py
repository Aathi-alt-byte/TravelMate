import hmac
import os
import re
import secrets
import sqlite3
from datetime import date, datetime
from email.utils import parseaddr
from urllib.parse import urljoin, urlparse

from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from settings import DATABASE_PATH

booking_bp = Blueprint("travel", __name__)
CANCELLATION_DAYS = 7


def db():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_booking_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT NOT NULL UNIQUE COLLATE NOCASE,
          password_hash TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS trips (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL REFERENCES users(id),
          destination_name TEXT NOT NULL,
          start_date TEXT NOT NULL,
          end_date TEXT NOT NULL,
          travelers INTEGER NOT NULL CHECK(travelers BETWEEN 1 AND 20),
          estimated_amount_paise INTEGER NOT NULL,
          status TEXT NOT NULL DEFAULT 'planned',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS bookings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          public_id TEXT NOT NULL UNIQUE,
          trip_id INTEGER REFERENCES trips(id),
          user_id INTEGER NOT NULL REFERENCES users(id),
          destination_name TEXT NOT NULL,
          destination_region TEXT NOT NULL,
          start_date TEXT NOT NULL,
          end_date TEXT NOT NULL,
          travelers INTEGER NOT NULL CHECK(travelers BETWEEN 1 AND 20),
          traveler_name TEXT NOT NULL,
          traveler_email TEXT NOT NULL,
          traveler_phone TEXT NOT NULL,
          amount_paise INTEGER NOT NULL CHECK(amount_paise > 0),
          daily_cost INTEGER NOT NULL DEFAULT 0,
          travel_cost INTEGER NOT NULL DEFAULT 0,
          trip_days INTEGER NOT NULL DEFAULT 1,
          payment_status TEXT NOT NULL DEFAULT 'created',
          booking_status TEXT NOT NULL DEFAULT 'awaiting_payment',
          cancellation_status TEXT NOT NULL DEFAULT 'not_requested',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS payments (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          booking_id INTEGER NOT NULL REFERENCES bookings(id),
          gateway TEXT NOT NULL DEFAULT 'razorpay',
          order_id TEXT NOT NULL UNIQUE,
          payment_id TEXT UNIQUE,
          signature_verified INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'created',
          amount_paise INTEGER NOT NULL,
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS contact_enquiries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          name TEXT NOT NULL,
          email TEXT NOT NULL,
          subject TEXT NOT NULL,
          message TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'new',
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS planned_itineraries (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          public_id TEXT NOT NULL UNIQUE,
          user_id INTEGER REFERENCES users(id),
          owner_token TEXT,
          destination_name TEXT NOT NULL,
          destination_region TEXT NOT NULL,
          start_date TEXT NOT NULL,
          end_date TEXT NOT NULL,
          travelers INTEGER NOT NULL CHECK(travelers BETWEEN 1 AND 20),
          starting_location TEXT NOT NULL,
          preferences_json TEXT NOT NULL,
          accommodation TEXT NOT NULL,
          transportation TEXT NOT NULL,
          budget INTEGER NOT NULL CHECK(budget > 0),
          estimated_total INTEGER NOT NULL,
          daily_cost INTEGER NOT NULL,
          travel_cost INTEGER NOT NULL,
          itinerary_json TEXT NOT NULL,
          saved INTEGER NOT NULL DEFAULT 0 CHECK(saved IN (0, 1)),
          created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
          CHECK(user_id IS NOT NULL OR owner_token IS NOT NULL)
        );
        """)
        booking_columns = {row["name"] for row in conn.execute("PRAGMA table_info(bookings)")}
        for column, declaration in {
            "trip_id": "INTEGER REFERENCES trips(id)",
            "daily_cost": "INTEGER NOT NULL DEFAULT 0",
            "travel_cost": "INTEGER NOT NULL DEFAULT 0",
            "trip_days": "INTEGER NOT NULL DEFAULT 1",
        }.items():
            if column not in booking_columns:
                conn.execute(f"ALTER TABLE bookings ADD COLUMN {column} {declaration}")
        conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments(booking_id);
        CREATE INDEX IF NOT EXISTS idx_itineraries_owner ON planned_itineraries(user_id, saved, created_at DESC);
        """)


def csrf_token():
    token = session.get("_csrf")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf"] = token
    return token


def claim_session_itineraries(user_id):
    owner_token = session.get("itinerary_owner_token")
    if owner_token:
        with db() as conn:
            conn.execute(
                """UPDATE planned_itineraries SET user_id=?, owner_token=NULL
                   WHERE user_id IS NULL AND owner_token=?""",
                (user_id, owner_token),
            )
        session.pop("itinerary_owner_token", None)


@booking_bp.before_app_request
def protect_booking_posts():
    if request.method != "POST" or request.blueprint != "travel":
        return
    supplied = request.form.get("_csrf") or request.headers.get("X-CSRF-Token", "")
    if not hmac.compare_digest(str(session.get("_csrf", "")), str(supplied)):
        abort(400, description="This form expired. Refresh the page and try again.")


@booking_bp.before_app_request
def load_user():
    user_id = session.get("user_id")
    g.user = None
    if user_id:
        with db() as conn:
            g.user = conn.execute("SELECT id, email FROM users WHERE id=?", (user_id,)).fetchone()
        if g.user is None:
            session.pop("user_id", None)


@booking_bp.app_context_processor
def inject_travel_globals():
    return {"csrf_token": csrf_token, "current_user": getattr(g, "user", None),
            "payment_mode": "TEST"}


def safe_next_url(target):
    if not target:
        return None
    parsed = urlparse(urljoin(request.host_url, target))
    return target if parsed.scheme in {"http", "https"} and parsed.netloc == request.host else None


def require_user():
    if not getattr(g, "user", None):
        next_path = request.full_path if request.query_string else request.path
        return redirect(url_for("travel.login", next=next_path))
    return None


def razorpay_client():
    key_id = os.environ.get("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", "").strip()
    if not key_id or not key_secret or "replace" in key_id.lower() or not key_id.startswith("rzp_test_"):
        return None, None
    try:
        import razorpay
    except ImportError:
        return None, None
    return razorpay.Client(auth=(key_id, key_secret)), key_id


def valid_email(value):
    value = value.strip()
    parsed = parseaddr(value)[1]
    return len(value) <= 254 and parsed == value and re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) is not None


@booking_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("travel.my_trips"))
    error = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not valid_email(email):
            error = "Enter a valid email address."
        elif len(password) < 10 or len(password) > 128:
            error = "Use a password between 10 and 128 characters."
        else:
            try:
                with db() as conn:
                    conn.execute("INSERT INTO users(email,password_hash) VALUES (?,?)",
                                 (email, generate_password_hash(password)))
                with db() as conn:
                    user_id = conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()["id"]
                owner_token = session.get("itinerary_owner_token")
                session.clear()
                if owner_token:
                    session["itinerary_owner_token"] = owner_token
                session["user_id"] = user_id
                claim_session_itineraries(user_id)
                flash("Your account is ready.")
                return redirect(url_for("travel.my_trips"))
            except sqlite3.IntegrityError:
                error = "An account with that email already exists."
    return render_template("auth.html", mode="register", error=error)


@booking_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("travel.my_trips"))
    error = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with db() as conn:
            user = conn.execute("SELECT id,password_hash FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            owner_token = session.get("itinerary_owner_token")
            session.clear()
            if owner_token:
                session["itinerary_owner_token"] = owner_token
            session["user_id"] = user["id"]
            claim_session_itineraries(user["id"])
            return redirect(safe_next_url(request.args.get("next")) or url_for("travel.my_trips"))
        error = "Email or password was not recognized."
    return render_template("auth.html", mode="login", error=error)


@booking_bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@booking_bp.route("/book/<destination_slug>", methods=["GET", "POST"])
def book_trip(destination_slug):
    auth = require_user()
    if auth:
        return auth
    name = destination_slug.replace("-", " ").title()
    with db() as conn:
        destination = conn.execute("SELECT name,region,daily_cost,travel_cost FROM destinations WHERE lower(replace(name,' ','-'))=?",
                                   (destination_slug.lower(),)).fetchone()
    if not destination:
        abort(404)
    error = ""
    form = {"name": "", "email": g.user["email"], "phone": "", "start_date": request.args.get("start_date", ""), "end_date": request.args.get("end_date", ""), "travelers": request.args.get("travelers", "2")}
    if request.method == "POST":
        form.update({key: request.form.get(key, "").strip() for key in form})
        try:
            start = date.fromisoformat(form["start_date"])
            end = date.fromisoformat(form["end_date"])
            travelers = int(form["travelers"])
            if len(form["name"]) < 2 or len(form["name"]) > 100 or request.form.get("terms_accepted") != "on":
                raise ValueError
            if not valid_email(form["email"]) or not re.fullmatch(r"[+()\d\s-]{8,20}", form["phone"]):
                raise ValueError
            if start < date.today() or end < start or (end-start).days > 29 or not 1 <= travelers <= 20:
                raise ValueError
        except (ValueError, TypeError):
            error = "Check traveller details, contact information, dates, and traveller count."
        if not error:
            days = (end-start).days + 1
            amount_paise = (int(destination["daily_cost"]) * travelers * days + int(destination["travel_cost"]) * travelers) * 100
            # Reuse an existing unpaid booking for the same user and itinerary.
            with db() as conn:
                existing = conn.execute("""SELECT public_id FROM bookings WHERE user_id=? AND destination_name=?
                    AND start_date=? AND end_date=? AND travelers=? AND booking_status='awaiting_payment'""",
                    (g.user["id"], destination["name"], start.isoformat(), end.isoformat(), travelers)).fetchone()
                if existing:
                    return redirect(url_for("travel.booking_detail", public_id=existing["public_id"]))
                public_id = secrets.token_urlsafe(9)
                trip_cursor = conn.execute("""INSERT INTO trips(user_id,destination_name,start_date,end_date,
                    travelers,estimated_amount_paise) VALUES (?,?,?,?,?,?)""",
                    (g.user["id"],destination["name"],start.isoformat(),end.isoformat(),travelers,amount_paise))
                trip_id = trip_cursor.lastrowid
                conn.execute("""INSERT INTO bookings(public_id,trip_id,user_id,destination_name,destination_region,start_date,end_date,
                    travelers,traveler_name,traveler_email,traveler_phone,amount_paise,daily_cost,travel_cost,trip_days)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (public_id,trip_id,g.user["id"],destination["name"],destination["region"],start.isoformat(),end.isoformat(),
                     travelers,form["name"],form["email"],form["phone"],amount_paise,
                     int(destination["daily_cost"]),int(destination["travel_cost"]),days))
            return redirect(url_for("travel.booking_detail", public_id=public_id))
    return render_template("booking_form.html", destination=destination, form=form, error=error,
                           today=date.today().isoformat())


@booking_bp.get("/booking/<public_id>")
def booking_detail(public_id):
    auth = require_user()
    if auth:
        return auth
    with db() as conn:
        booking = conn.execute("""SELECT * FROM bookings WHERE public_id=? AND user_id=?""",
                               (public_id,g.user["id"])).fetchone()
        if not booking:
            abort(404)
        payment = conn.execute("SELECT * FROM payments WHERE booking_id=? ORDER BY id DESC LIMIT 1",
                               (booking["id"],)).fetchone()
    return render_template("booking_detail.html", booking=booking, payment=payment,
                           razorpay_key=os.environ.get("RAZORPAY_KEY_ID", ""),
                           cancellation_days=CANCELLATION_DAYS,
                           cancellation_eligible=(booking["payment_status"] == "paid"
                               and booking["cancellation_status"] == "not_requested"
                               and (date.fromisoformat(booking["start_date"]) - date.today()).days >= CANCELLATION_DAYS))


@booking_bp.post("/booking/<public_id>/pay")
def create_payment_order(public_id):
    auth = require_user()
    if auth:
        return auth
    client, key_id = razorpay_client()
    if not client:
        flash("Razorpay test mode is not configured. Add test keys and install the Razorpay SDK.")
        return redirect(url_for("travel.booking_detail", public_id=public_id))
    with db() as conn:
        # Serialize order creation so a repeated click reuses the active order.
        conn.execute("BEGIN IMMEDIATE")
        booking = conn.execute("SELECT * FROM bookings WHERE public_id=? AND user_id=?",
                               (public_id,g.user["id"])).fetchone()
        if not booking:
            abort(404)
        if booking["booking_status"] != "awaiting_payment":
            flash("This booking is no longer awaiting payment.")
            return redirect(url_for("travel.booking_detail", public_id=public_id))
        payment = conn.execute("SELECT * FROM payments WHERE booking_id=? ORDER BY id DESC LIMIT 1",
                               (booking["id"],)).fetchone()
        if payment and payment["status"] in {"created", "verification_pending", "not_captured"}:
            order_id = payment["order_id"]
        else:
            try:
                order = client.order.create(data={"amount": booking["amount_paise"], "currency": "INR",
                                                  "receipt": booking["public_id"],
                                                  "notes": {"booking_id": booking["public_id"]}})
                order_id = order["id"]
            except Exception:
                current_app.logger.exception("Razorpay order creation failed")
                flash("Payment setup failed. Your booking remains unpaid; please try again.")
                return redirect(url_for("travel.booking_detail", public_id=public_id))
            conn.execute("""INSERT INTO payments(booking_id,order_id,amount_paise,status)
                            VALUES (?,?,?,'created')""", (booking["id"],order_id,booking["amount_paise"]))
    return render_template("checkout.html", booking=booking, order_id=order_id, razorpay_key=key_id,
                           csrf=csrf_token(), daily_total=booking["daily_cost"] * booking["trip_days"] * booking["travelers"],
                           travel_total=booking["travel_cost"] * booking["travelers"])


@booking_bp.post("/payment/verify")
def verify_payment():
    auth = require_user()
    if auth:
        return auth
    order_id = request.form.get("razorpay_order_id", "")
    payment_id = request.form.get("razorpay_payment_id", "")
    signature = request.form.get("razorpay_signature", "")
    client, _ = razorpay_client()
    if not client or not order_id or not payment_id or not signature:
        flash("Payment details were incomplete. The booking is still unpaid.")
        return redirect(url_for("travel.my_trips"))
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("""SELECT b.*,p.id AS payment_row,p.order_id AS expected_order,
            p.amount_paise AS expected_amount,p.payment_id AS existing_payment_id,
            p.signature_verified AS signature_verified,p.status AS payment_record_status
            FROM bookings b JOIN payments p ON p.booking_id=b.id WHERE p.order_id=? AND b.user_id=?""",
            (order_id,g.user["id"])).fetchone()
        if not row:
            abort(404)
        if row["payment_status"] == "paid" and row["payment_record_status"] == "captured":
            if row["existing_payment_id"] == payment_id and row["signature_verified"]:
                return redirect(url_for("travel.payment_result", public_id=row["public_id"]))
            flash("This booking already has a verified payment. No second payment was applied.")
            return redirect(url_for("travel.booking_detail", public_id=row["public_id"]))
        if row["booking_status"] != "awaiting_payment":
            flash("This booking is no longer awaiting payment.")
            return redirect(url_for("travel.booking_detail", public_id=row["public_id"]))
        payment_used = conn.execute(
            "SELECT id FROM payments WHERE payment_id=? AND id<>?", (payment_id, row["payment_row"])
        ).fetchone()
        if payment_used:
            abort(400, description="This payment reference has already been used.")
        try:
            client.utility.verify_payment_signature({"razorpay_order_id": order_id,
                "razorpay_payment_id": payment_id,"razorpay_signature": signature})
        except Exception:
            current_app.logger.exception("Razorpay signature verification failed")
            conn.execute("UPDATE payments SET status='verification_failed',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (row["payment_row"],))
            conn.execute("UPDATE bookings SET payment_status='verification_failed' WHERE id=? AND payment_status!='paid'",
                         (row["id"],))
            flash("The gateway signature could not be verified. The booking remains unpaid.")
            return redirect(url_for("travel.booking_detail", public_id=row["public_id"]))
        conn.execute("""UPDATE payments SET payment_id=?,signature_verified=1,status='verification_pending',
                     updated_at=CURRENT_TIMESTAMP WHERE id=?""", (payment_id,row["payment_row"]))
        conn.execute("UPDATE bookings SET payment_status='verification_pending' WHERE id=?",
                     (row["id"],))
        try:
            gateway_payment = client.payment.fetch(payment_id)
            verified = (gateway_payment.get("order_id") == row["expected_order"]
                        and int(gateway_payment.get("amount", -1)) == row["expected_amount"]
                        and gateway_payment.get("currency") == "INR")
            captured = verified and gateway_payment.get("status") == "captured"
        except Exception:
            current_app.logger.exception("Razorpay payment status fetch failed")
            flash("Payment signature is valid, but gateway status is temporarily unavailable. The booking remains unconfirmed.")
            return redirect(url_for("travel.booking_detail", public_id=row["public_id"]))
        if not captured:
            conn.execute("UPDATE payments SET status='not_captured',updated_at=CURRENT_TIMESTAMP WHERE id=?",
                         (row["payment_row"],))
            conn.execute("UPDATE bookings SET payment_status='not_captured' WHERE id=?",
                         (row["id"],))
            flash("The gateway has not reported a captured payment. The booking is not confirmed.")
            return redirect(url_for("travel.booking_detail", public_id=row["public_id"]))
        conn.execute("""UPDATE payments SET payment_id=?,signature_verified=1,status='captured',
                     updated_at=CURRENT_TIMESTAMP WHERE id=?""", (payment_id,row["payment_row"]))
        conn.execute("""UPDATE bookings SET payment_status='paid',booking_status='confirmed'
                     WHERE id=?""", (row["id"],))
        if row["trip_id"]:
            conn.execute("UPDATE trips SET status='confirmed' WHERE id=? AND user_id=?", (row["trip_id"],g.user["id"]))
    return redirect(url_for("travel.payment_result", public_id=row["public_id"]))


@booking_bp.get("/payment/result/<public_id>")
def payment_result(public_id):
    auth = require_user()
    if auth:
        return auth
    with db() as conn:
        booking = conn.execute("SELECT * FROM bookings WHERE public_id=? AND user_id=?",
                               (public_id,g.user["id"])).fetchone()
        payment = conn.execute("SELECT * FROM payments WHERE booking_id=? ORDER BY id DESC LIMIT 1",
                               (booking["id"],)).fetchone() if booking else None
    if not booking:
        abort(404)
    return render_template("payment_result.html", booking=booking, payment=payment)


@booking_bp.get("/my-trips")
def my_trips():
    auth = require_user()
    if auth:
        return auth
    with db() as conn:
        bookings = conn.execute("""SELECT * FROM bookings WHERE user_id=? ORDER BY created_at DESC""",
                                (g.user["id"],)).fetchall()
        itineraries = conn.execute(
            """SELECT * FROM planned_itineraries WHERE user_id=? AND saved=1
               ORDER BY created_at DESC""", (g.user["id"],)
        ).fetchall()
    return render_template("my_trips.html", bookings=bookings, itineraries=itineraries,
                           cancellation_days=CANCELLATION_DAYS)


@booking_bp.post("/itinerary/<public_id>/save")
def save_itinerary(public_id):
    auth = require_user()
    if auth:
        return auth
    with db() as conn:
        itinerary = conn.execute(
            "SELECT id, user_id, owner_token FROM planned_itineraries WHERE public_id=?",
            (public_id,),
        ).fetchone()
        if not itinerary or (itinerary["user_id"] not in (None, g.user["id"])):
            abort(404)
        if itinerary["user_id"] is None:
            owner_token = session.get("itinerary_owner_token", "")
            if not owner_token or not secrets.compare_digest(itinerary["owner_token"] or "", owner_token):
                abort(404)
        conn.execute(
            "UPDATE planned_itineraries SET user_id=?, owner_token=NULL, saved=1 WHERE id=?",
            (g.user["id"], itinerary["id"]),
        )
    flash("Your itinerary is saved in My Trips.")
    return redirect(url_for("itinerary_result", public_id=public_id))


@booking_bp.post("/my-trips/<public_id>/cancel")
def cancel_booking(public_id):
    auth = require_user()
    if auth:
        return auth
    with db() as conn:
        booking = conn.execute("SELECT * FROM bookings WHERE public_id=? AND user_id=?",
                               (public_id,g.user["id"])).fetchone()
        if not booking:
            abort(404)
        if booking["payment_status"] == "paid":
            days_before_trip = (date.fromisoformat(booking["start_date"]) - date.today()).days
            if booking["cancellation_status"] != "not_requested":
                flash("A cancellation request is already recorded. No refund has been issued.")
            elif days_before_trip < CANCELLATION_DAYS:
                flash(f"Cancellation requests must be submitted at least {CANCELLATION_DAYS} days before travel.")
            else:
                conn.execute("UPDATE bookings SET cancellation_status='requested' WHERE id=?",
                             (booking["id"],))
                flash("Cancellation request submitted for support review. No refund has been issued or marked complete.")
        elif booking["booking_status"] == "awaiting_payment":
            conn.execute("""UPDATE bookings SET booking_status='cancelled',
                cancellation_status='cancelled_unpaid' WHERE id=?""", (booking["id"],))
            if booking["trip_id"]:
                conn.execute("UPDATE trips SET status='cancelled' WHERE id=? AND user_id=?",
                             (booking["trip_id"],g.user["id"]))
            flash("Unpaid booking cancelled. No payment or refund was made.")
        else:
            flash("This booking is not eligible for cancellation.")
    return redirect(url_for("travel.my_trips"))


@booking_bp.route("/about", methods=["GET"])
def about():
    return render_template("about.html")


@booking_bp.route("/contact", methods=["GET", "POST"])
def contact():
    error = ""
    sent = False
    form = {"name": "", "email": "", "subject": "", "message": ""}
    if request.method == "POST":
        form.update({k: request.form.get(k,"").strip() for k in form})
        if (len(form["name"]) < 2 or len(form["name"]) > 100 or not valid_email(form["email"])
            or not 3 <= len(form["subject"]) <= 120 or not 10 <= len(form["message"]) <= 4000):
            error = "Check each field. Include a valid email and a message of at least 10 characters."
        else:
            with db() as conn:
                conn.execute("""INSERT INTO contact_enquiries(name,email,subject,message) VALUES (?,?,?,?)""",
                             (form["name"],form["email"],form["subject"],form["message"]))
            sent = True
            form = {"name": "", "email": "", "subject": "", "message": ""}
    return render_template("contact.html", form=form, error=error, sent=sent)


@booking_bp.get("/privacy")
def privacy():
    return render_template("policy.html", kind="privacy")


@booking_bp.get("/terms")
def terms():
    return render_template("policy.html", kind="terms")
