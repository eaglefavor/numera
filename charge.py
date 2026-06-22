import os
import json
import stripe
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
        except (ValueError, json.JSONDecodeError):
            self._respond(400, {"success": False, "error": "Invalid request body."})
            return

        token    = body.get("token")
        amount   = body.get("amount")
        currency = body.get("currency", "usd")
        invoice  = body.get("invoice", "")
        email    = body.get("email", "")

        if not token or not amount:
            self._respond(400, {"success": False, "error": "Missing token or amount."})
            return

        try:
            charge = stripe.Charge.create(
                amount=amount,
                currency=currency,
                source=token,
                description=f"Invoice {invoice}",
                receipt_email=email,
                metadata={"invoice": invoice},
            )
            self._respond(200, {
                "success":  True,
                "chargeId": charge.id,
                "status":   charge.status,
            })

        except stripe.error.CardError as e:
            self._respond(402, {"success": False, "error": e.user_message})

        except stripe.error.InvalidRequestError:
            self._respond(400, {"success": False, "error": "Invalid payment request."})

        except stripe.error.AuthenticationError:
            self._respond(500, {"success": False, "error": "Payment configuration error."})

        except stripe.error.StripeError:
            self._respond(500, {"success": False, "error": "Payment failed. Please try again."})

    def _respond(self, status, data):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
