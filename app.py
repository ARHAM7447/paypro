from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

from scraper import get_product_details
from db import add_price_entry, get_all_products

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

# ====================== CONFIG ======================
load_dotenv()

app = Flask(__name__,
            template_folder="templates",
            static_folder="static")

CORS(app, resources={r"/api/*": {"origins": "*"}})

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

logger.info("🚀 PriceTrack Flask app initialized")

# ====================== HTML ROUTES ======================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        print("Email:", email)
        print("Password:", password)

        return "Login working ✅"

    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        # 🔍 Basic validation
        if password != confirm_password:
            return "❌ Passwords do not match"

        # 👉 Abhi ke liye print (later DB me save karenge)
        print("Name:", name)
        print("Email:", email)
        print("Password:", password)

        # ✅ Success response (temporary)
        return "Signup successful ✅"

    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# Yeh wala sabse important — HTML mein jo use kiya hai uske hisaab se
@app.route("/my-products")
def my_products():           # ← Simple aur common naam, ab conflict nahi
    return render_template("my-products.html")

@app.route("/wishlist")
def wishlist():
    return render_template("wishlist.html")

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/alerts")
def alerts():
    return render_template("alerts.html")

@app.route("/discover")
def discover():
    return render_template("discover.html")

@app.route("/how-it-works")
def how_it_works():
    return render_template("how-it-works.html")

@app.route("/features")
def features():
    return render_template("features.html")


# ====================== API ROUTES ======================
@app.route("/api/track", methods=["POST"])
def track_product():
    try:
        data = request.get_json(silent=True)
        if not data or not data.get("url"):
            return jsonify({"error": "URL bhejo"}), 400

        url = data["url"].strip()
        details = get_product_details(url)

        if "error" in details:
            logger.warning(f"Scraper failed: {details['error']}")
            return jsonify(details), 400

        add_price_entry(url, details["name"], details["price"])
        logger.info(f"✅ Tracked {details['name']} @ ₹{details['price']}")

        return jsonify({
            "success": True,
            "name": details["name"],
            "current_price": details["price"],
            "message": "Tracking shuru ho gaya! ✅"
        })

    except Exception as e:
        logger.error(f"Track error: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/api/my-products", methods=["GET"])
def get_my_products():
    try:
        products = get_all_products()
        out = []
        for p in products:
            if not p.get("price_history"):
                continue
            last = p["price_history"][-1]
            out.append({
                "url": p["url"],
                "name": p["name"],
                "current_price": last["price"],
                "last_updated": last["time"]
            })
        return jsonify(out)
    except Exception as e:
        logger.error(f"My products error: {e}")
        return jsonify({"error": "Failed to load products"}), 500


# ====================== CRON JOB ======================
def update_all_prices():
    logger.info("🔄 Cron started...")
    try:
        products = get_all_products()
        updated = failed = 0
        for p in products:
            details = get_product_details(p["url"])
            if "error" not in details:
                add_price_entry(p["url"], p["name"], details["price"])
                updated += 1
            else:
                failed += 1
        logger.info(f"✅ Cron done → Updated: {updated} | Failed: {failed}")
    except Exception as e:
        logger.error(f"Cron failed: {e}")

# ====================== SCHEDULER + SERVER ======================
scheduler = BackgroundScheduler()
scheduler.add_job(update_all_prices, IntervalTrigger(minutes=60), id='price_update', replace_existing=True)
scheduler.start()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info(f"🌐 Server running → http://localhost:{port}")

    try:
        app.run(debug=True, port=port, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("👋 Shutdown safe")
    except Exception as e:
        logger.critical(f"💥 Crash: {e}")
        scheduler.shutdown()