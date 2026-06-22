import os
import stripe
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder=".")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/charge", methods=["POST"])
def charge():
    data = request.get_json()

    token    = data.get("token")
    amount   = data.get("amount")    # in cents, e.g. 25000 = $250.00
    currency = data.get("currency", "usd")
    invoice  = data.get("invoice", "")
    email    = data.get("email", "")

    if not token or not amount:
        return jsonify({"success": False, "error": "Missing token or amount."}), 400

    try:
        charge = stripe.Charge.create(
            amount=amount,
            currency=currency,
            source=token,
            description=f"Invoice {invoice}",
            receipt_email=email,
            metadata={"invoice": invoice},
        )

        return jsonify({
            "success":  True,
            "chargeId": charge.id,
            "status":   charge.status,
        })

    except stripe.error.CardError as e:
        # Card was declined
        return jsonify({"success": False, "error": e.user_message}), 402

    except stripe.error.InvalidRequestError as e:
        return jsonify({"success": False, "error": "Invalid payment request."}), 400

    except stripe.error.AuthenticationError:
        return jsonify({"success": False, "error": "Payment configuration error."}), 500

    except stripe.error.StripeError as e:
        return jsonify({"success": False, "error": "Payment failed. Please try again."}), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
