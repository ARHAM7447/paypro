import sqlite3
from datetime import datetime

DB_NAME = "database.sqlite"


# ----------------- Initialize Database -----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            name TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            price REAL,
            time TEXT,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ----------------- Add / Update Product Price -----------------
def add_price_entry(url, name, price):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM products WHERE url = ?", (url,))
    result = cursor.fetchone()

    if result:
        product_id = result[0]
    else:
        cursor.execute("INSERT INTO products (url, name) VALUES (?, ?)", (url, name))
        product_id = cursor.lastrowid

    cursor.execute(
        "INSERT INTO price_history (product_id, price, time) VALUES (?, ?, ?)",
        (product_id, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()


# ----------------- Get All Products + Price History -----------------
def get_all_products():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, url, name FROM products")
    products = cursor.fetchall()

    result = []

    for product_id, url, name in products:
        cursor.execute("""
            SELECT price, time FROM price_history
            WHERE product_id = ?
            ORDER BY id ASC
        """, (product_id,))
        history = cursor.fetchall()

        price_history = [
            {"price": price, "time": time}
            for price, time in history
        ]

        result.append({
            "url": url,
            "name": name,
            "price_history": price_history
        })

    conn.close()
    return result