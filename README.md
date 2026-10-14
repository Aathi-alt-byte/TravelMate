# TravelMate

A Flask and SQLite travel planner with destination guides, trip planning, estimated budgets, accounts, and Razorpay TEST-mode bookings. Trip and accommodation prices are planning estimates, not live quotes.

## Project structure

```text
TravelMate/
├── app.py                     # Main Flask app, destination pages and planner routes
├── booking.py                 # Accounts, bookings, SQLite schema, Razorpay orders and verification
├── destination_data.py        # Reusable destination guide data, separate from templates
├── requirements.txt
├── .env.example               # Placeholder values only; copy to .env
├── .gitignore
├── instance/
│   └── travelmate.sqlite3     # Created and migrated at app startup; keep local/private
├── static/
│   ├── css/style.css
│   └── js/
│       ├── app.js
│       ├── booking-form.js
│       ├── budget.js
│       ├── checkout.js
│       ├── destinations.js
│       ├── detail.js
│       └── planner.js
├── tests/
│   └── test_payments.py        # Isolated payment-flow tests with a fake gateway
└── templates/
    ├── base.html
    ├── index.html
    ├── destinations.html
    ├── destination_detail.html
    ├── plan_trip.html
    ├── budget.html
    ├── auth.html
    ├── booking_form.html
    ├── booking_detail.html
    ├── checkout.html
    ├── payment_result.html
    ├── itinerary.html
    ├── my_trips.html
    ├── about.html
    ├── contact.html
    ├── policy.html
    └── error.html
```

All pages extend `base.html`; page styles/scripts are in `static`. SQLite tables are initialized/migrated when the app starts. Booking amounts are stored as integer paise. User passwords are hashed. Razorpay card/UPI credentials are not stored.

## Windows setup (Command Prompt or VS Code terminal)

Open a terminal in the project folder, the one containing `app.py`.

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
copy .env.example .env
```

In PowerShell, use `Copy-Item .env.example .env` instead of `copy`. In VS Code, choose the interpreter at `.venv\Scripts\python.exe` if it does not select the environment automatically.

Open `.env` in an editor and set a long random `FLASK_SECRET_KEY`. Keep this file private and do not commit it. The supplied Razorpay values are placeholders, not usable credentials. Set them only from your Razorpay Dashboard in **Test Mode**:

```dotenv
FLASK_SECRET_KEY=your_private_random_secret
RAZORPAY_KEY_ID=rzp_test_your_test_key_id
RAZORPAY_KEY_SECRET=your_test_key_secret
TRAVELMATE_HTTPS=false
FLASK_DEBUG=0
```

Use a key ID beginning `rzp_test_`. This application rejects live-mode key IDs; it is a test integration and must not be represented as accepting real payments. Do not put secrets in Python, HTML, JavaScript, screenshots, or source control. `.gitignore` excludes `.env`, virtual environments, and local SQLite files.

## Start the website

With the virtual environment active and `.env` configured:

```bat
python app.py
```

Open <http://127.0.0.1:5000>. Stop the server with `Ctrl+C`. Debug mode is off unless explicitly enabled for local development with `FLASK_DEBUG=1`. For HTTPS deployments set `TRAVELMATE_HTTPS=true` so session cookies use the Secure flag.

## Database setup

No separate database server or manual schema command is needed. On first start, TravelMate creates `instance/travelmate.sqlite3`, adds destination records, and creates or migrates the account, trip, booking, payment, and contact enquiry tables. Later starts preserve existing data and apply the small additive booking-column migrations. Do not delete the SQLite file to “reinitialize” a database containing bookings or accounts. Keep backups private because the database includes traveller contact details and payment identifiers.

## Razorpay TEST-mode payment procedure

1. Create or sign in to a Razorpay account and use the Dashboard’s **Test Mode**. Generate Test API Keys from the Dashboard’s API Keys settings. Razorpay’s current Dashboard labels can change; consult its [official Python integration guide](https://razorpay.com/docs/server-integration/python/test-app/) for the latest key and test credential steps.
2. Put the Test Key ID and Test Key Secret in local `.env`, then restart Flask. Never share or commit the secret. The key ID displayed to Checkout is public; the key secret stays on the Flask server.
3. In the site, register a test account, sign in, open a destination, click **Book This Trip**, and submit traveller details, dates, traveller count, and terms acceptance. Check the displayed total; it is an estimate and the server recalculates it.
4. Open the new booking and click **Pay Now**. Checkout uses a server-created order whose amount comes from the saved booking, not browser input.
5. In Razorpay’s mock checkout, choose an enabled test payment method and use the test details listed in Razorpay’s official docs for that method. The mock bank page may offer success/failure simulation. Test UPI identifiers and available methods depend on the current Razorpay account/product configuration; follow its current test credential list rather than using real payment details. The official docs describe test transactions as simulated and state that no real money is deducted.
6. After Checkout returns, the browser posts the order ID, payment ID, and signature. Flask verifies the signature using the official Python SDK and fetches payment status from Razorpay. Only a matching order, exact amount, INR currency, and `captured` gateway status marks the booking paid. A Checkout success callback by itself is not confirmation.
7. For a successful case, verify the confirmation page and **My Trips** status. Also verify the payment under the Test Mode Dashboard’s Transactions/Payments section. Depending on capture settings, a payment may be `authorized` rather than `captured`; this application intentionally does not confirm an uncaptured payment.
8. Repeat with a simulated failure and with Checkout dismissed. Both must leave the booking unpaid. Confirm the booking remains visible as awaiting payment or unpaid, and that payment verification errors never display a paid confirmation.

Razorpay Test Mode is not live payments. Do not switch this project to live keys as-is: the code explicitly requires Test keys and a real launch needs a separate production readiness review.

### Run payment tests

From the project folder in the VS Code terminal:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

These tests use a temporary SQLite database and a fake Razorpay client. They cover captured-payment confirmation, invalid signatures, checkout dismissal, repeated Pay Now clicks, and duplicate verification callbacks. They do not contact Razorpay or change the local booking database. Razorpay Checkout displays only payment methods enabled for the merchant account; TravelMate does not collect card numbers, CVVs, UPI PINs, or banking passwords.

The app records eligible cancellation requests for support review. It does not initiate or mark refunds as complete; an authorized support workflow must process any refund through Razorpay and confirm its status.

## Manual verification checklist

- [ ] Destination search from the home page returns matching destinations and the explore link opens the correct detail page.
- [ ] Explore page search, state/type/budget/duration filters, sorting, clear filters, and load more behave as expected.
- [ ] A signed-out visitor is sent to sign in before accessing personal trips or creating a booking.
- [ ] Booking rejects invalid email/phone, past or reversed dates, too many travellers, and missing terms acceptance.
- [ ] Booking estimate updates when dates or traveller count change; changing browser values cannot change the server-calculated amount.
- [ ] A valid booking receives a unique booking ID and appears only under its owning account in **My Trips**.
- [ ] Razorpay Checkout opens in Test Mode; test success, test failure, and dismissal produce accurate outcomes.
- [ ] A paid state appears only after server signature validation and gateway confirmation as captured; verify Dashboard status.
- [ ] Unpaid booking cancellation updates the booking; paid booking cancellation does not imply a refund.
- [ ] Forms with missing/invalid CSRF tokens are rejected; sign out and account ownership checks work.
- [ ] Test at desktop, tablet, and mobile widths. Check navigation menu, destination cards, planner, budget controls, and checkout button using mouse and keyboard.
- [ ] Try the website without Razorpay test keys: the booking is not falsely marked paid and the user sees a useful message.

## Security and operational notes

Flask uses HTTP-only, SameSite=Lax session cookies; HTTPS deployments should set the secure cookie option. The configured secret should be a high-entropy value. State-changing forms include CSRF tokens. Booking queries are scoped to the authenticated account. Payment amounts and status are verified server-side. The database never stores card numbers, CVV, UPI PINs, or gateway credentials. User contact details and payment references are still sensitive and should be protected with restricted file access and secure backups.

The support email and phone on the site are placeholders. Destination image URLs load from Unsplash and require an internet connection. Destination costs and seasonal information are illustrative and can vary.

## Optional future improvements

- Email booking confirmations and password reset with a configured mail provider.
- Razorpay webhooks with signature validation and idempotent event processing for delayed payment updates.
- Admin tools for destination content, enquiries, and cancellation/refund operations.
- Production security review, rate limiting, stronger CSP, HTTPS deployment, monitoring, and managed database backups.
- Real inventory/availability and supplier quotes instead of sample estimates.
- Destination image licensing/local asset pipeline, accessibility audit, and automated browser coverage.
