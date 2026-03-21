from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import os
import logging

from scraper import get_product_details
from db import add_price_entry, get_all_products

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


# ---------------------- Logging ----------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ---------------------- Flask Setup ----------------------
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

logger.info("[APP] Flask + CORS initialized")


# ====================== HTML ROUTES ======================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/signup")
def signup():
    return render_template("signup.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/my-products")
def my_products():
    return render_template("my-products.html")   # FIXED


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


# ====================== API: Track Product ======================

@app.route("/api/track", methods=["POST"])
def track_product():
    try:
        data = request.get_json()
        url = data.get("url")

        if not url:
            return jsonify({"error": "URL bhejo"}), 400

        # Scrape product
        details = get_product_details(url)

        if "error" in details:
            logger.warning(f"[SCRAPER] {url} → {details['error']}")
            return jsonify(details), 400

        # Save data in DB
        add_price_entry(url, details["name"], details["price"])
        logger.info(f"[DB] Saved {details['name']} @ ₹{details['price']}")

        return jsonify({
            "success": True,
            "name": details["name"],
            "current_price": details["price"],
            "message": "Tracking shuru ho gaya!"
        })

    except Exception as e:
        logger.error(f"[TRACK ERROR] {e}")
        return jsonify({"error": "Server crash"}), 500


# ====================== API: Get All Products ======================

@app.route("/api/my-products", methods=["GET"])
def my_products():
    try:
        products = get_all_products()
        out = []

        for p in products:
            if not p["price_history"]:
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
        logger.error(f"[MY PRODUCTS ERROR] {e}")
        return jsonify({"error": "Products load fail"}), 500


# ====================== Cron Job ======================

def update_all_prices():
    logger.info("[CRON] Auto price update started...")

    try:
        products = get_all_products()
        updated = 0
        failed = 0

        for p in products:
            url = p["url"]
            name = p["name"]

            logger.info(f"[CRON] Checking → {name}")
            details = get_product_details(url)

            if "error" not in details:
                add_price_entry(url, name, details["price"])
                updated += 1
            else:
                failed += 1
                logger.warning(f"[CRON] Fail → {name}: {details['error']}")

        logger.info(f"[CRON] FINISHED → Updated: {updated} | Failed: {failed}")

    except Exception as e:
        logger.error(f"[CRON ERROR] {e}")


# ====================== Scheduler Setup ======================

scheduler = BackgroundScheduler()
scheduler.add_job(
    update_all_prices,
    trigger=IntervalTrigger(minutes=60),
    id="price_update_task",
    replace_existing=True
)

scheduler.start()
logger.info("[CRON] Scheduler started (Every 60 mins)")


# ====================== Run App ======================

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    logger.info(f"[APP] Server running → http://localhost:{port}")

    try:
        app.run(debug=True, port=port, use_reloader=False)

    except (KeyboardInterrupt, SystemExit):
        logger.info("[APP] Shutting down...")
        scheduler.shutdown()
        logger.info("[APP] Closed safely")

    except Exception as e:
        logger.critical(f"[APP CRASH] {e}")
        scheduler.shutdown()