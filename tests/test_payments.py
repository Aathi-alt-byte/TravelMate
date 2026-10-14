"""Payment-flow tests using a temporary SQLite database and a fake Razorpay client."""

import os
import sqlite3
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch


_test_directory = tempfile.TemporaryDirectory(prefix="travelmate-payment-tests-", ignore_cleanup_errors=True)
os.environ["TRAVELMATE_DATABASE"] = str(Path(_test_directory.name) / "payments.sqlite3")
os.environ["FLASK_SECRET_KEY"] = "unit-test-only-secret"

import booking
from app import app


class FakeRazorpayClient:
    def __init__(self):
        self.order_create_calls = []
        self.expected_order = None
        self.expected_amount = None
        self.payment_status = "captured"

        class Orders:
            def __init__(inner_self, outer):
                inner_self.outer = outer

            def create(inner_self, data):
                inner_self.outer.order_create_calls.append(data)
                # The payments table enforces globally unique gateway order IDs.
                # Keep generated IDs unique across separate test cases.
                inner_self.outer.expected_order = f"order_test_{id(inner_self.outer)}_{len(inner_self.outer.order_create_calls)}"
                inner_self.outer.expected_amount = data["amount"]
                return {"id": inner_self.outer.expected_order}

        class Utility:
            def verify_payment_signature(inner_self, details):
                if details["razorpay_signature"] != "valid-test-signature":
                    raise ValueError("invalid test signature")

        class Payments:
            def __init__(inner_self, outer):
                inner_self.outer = outer

            def fetch(inner_self, payment_id):
                return {
                    "id": payment_id,
                    "order_id": inner_self.outer.expected_order,
                    "amount": inner_self.outer.expected_amount,
                    "currency": "INR",
                    "status": inner_self.outer.payment_status,
                }

        self.order = Orders(self)
        self.utility = Utility()
        self.payment = Payments(self)


class PaymentFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config.update(TESTING=True, SECRET_KEY="unit-test-only-secret")
        booking.init_booking_db()

    def setUp(self):
        self.client = app.test_client()
        self.gateway = FakeRazorpayClient()
        self.gateway_patch = patch.object(booking, "razorpay_client", return_value=(self.gateway, "rzp_test_unit"))
        self.gateway_patch.start()

        connection = sqlite3.connect(os.environ["TRAVELMATE_DATABASE"])
        connection.execute(
            "INSERT INTO users(email,password_hash) VALUES (?,?)",
            (f"traveler-{id(self)}@example.test", "test-hash"),
        )
        self.user_id = connection.execute("SELECT last_insert_rowid()").fetchone()[0]
        start = date.today() + timedelta(days=20)
        self.start_date = start.isoformat()
        self.end_date = (start + timedelta(days=1)).isoformat()
        self.public_id = f"booking-{id(self)}"
        amount_paise = (2000 * 2 * 2 + 1500 * 2) * 100
        connection.execute(
            """INSERT INTO bookings(public_id,user_id,destination_name,destination_region,
               start_date,end_date,travelers,traveler_name,traveler_email,traveler_phone,
               amount_paise,daily_cost,travel_cost,trip_days)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (self.public_id, self.user_id, "Ooty", "Tamil Nadu", self.start_date, self.end_date,
             2, "Test Traveler", f"traveler-{id(self)}@example.test", "+911234567890",
             amount_paise, 2000, 1500, 2),
        )
        connection.commit()
        connection.close()
        with self.client.session_transaction() as session:
            session["user_id"] = self.user_id
            session["_csrf"] = "payment-test-csrf"

    def tearDown(self):
        self.gateway_patch.stop()

    def create_checkout(self):
        response = self.client.post(
            f"/booking/{self.public_id}/pay", data={"_csrf": "payment-test-csrf"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Secure checkout", response.data)
        return self.gateway.expected_order

    def verify(self, order_id, signature="valid-test-signature"):
        return self.client.post("/payment/verify", data={
            "_csrf": "payment-test-csrf",
            "razorpay_order_id": order_id,
            "razorpay_payment_id": f"pay_test_{self.public_id}",
            "razorpay_signature": signature,
        })

    def booking_state(self):
        connection = sqlite3.connect(os.environ["TRAVELMATE_DATABASE"])
        row = connection.execute(
            "SELECT payment_status,booking_status FROM bookings WHERE public_id=?", (self.public_id,)
        ).fetchone()
        connection.close()
        return row

    def test_captured_payment_confirms_and_duplicate_callback_is_idempotent(self):
        order_id = self.create_checkout()
        response = self.verify(order_id)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/payment/result/", response.headers["Location"])
        self.assertEqual(self.booking_state(), ("paid", "confirmed"))

        duplicate = self.verify(order_id)
        self.assertEqual(duplicate.status_code, 302)
        self.assertEqual(duplicate.headers["Location"], response.headers["Location"])
        self.assertEqual(self.booking_state(), ("paid", "confirmed"))

    def test_invalid_signature_keeps_booking_unpaid(self):
        order_id = self.create_checkout()
        response = self.verify(order_id, signature="invalid")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.booking_state(), ("verification_failed", "awaiting_payment"))

    def test_dismissed_checkout_has_no_confirmation(self):
        self.create_checkout()
        self.assertEqual(self.booking_state(), ("created", "awaiting_payment"))

    def test_repeated_pay_click_reuses_one_gateway_order(self):
        order_id = self.create_checkout()
        second = self.create_checkout()
        self.assertEqual(second, order_id)
        self.assertEqual(len(self.gateway.order_create_calls), 1)
        connection = sqlite3.connect(os.environ["TRAVELMATE_DATABASE"])
        count = connection.execute(
            "SELECT COUNT(*) FROM payments WHERE booking_id=(SELECT id FROM bookings WHERE public_id=?)",
            (self.public_id,),
        ).fetchone()[0]
        connection.close()
        self.assertEqual(count, 1)


if __name__ == "__main__":
    unittest.main()
