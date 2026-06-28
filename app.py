from flask import Flask, render_template, request, redirect, url_for, session
from flask_bcrypt import Bcrypt
from database import get_db_connection
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
bcrypt = Bcrypt(app)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        shop_name = request.form["shop_name"]
        owner_name = request.form["owner_name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (shop_name, owner_name, email, password) VALUES (%s, %s, %s, %s)",
                (shop_name, owner_name, email, hashed_password)
            )
            conn.commit()
            return redirect(url_for("login"))
        except Exception as e:
            conn.rollback()
            return render_template("register.html", error="Email already exists!")
        finally:
            cursor.close()
            conn.close()

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.check_password_hash(user[4], password):
            session["user_id"] = user[0]
            session["shop_name"] = user[1]
            session["owner_name"] = user[2]
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid email or password!")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stock WHERE user_id = %s", (session["user_id"],))
    total_stock = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM stock WHERE user_id = %s AND quantity <= low_stock_alert", (session["user_id"],))
    low_stock_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bills WHERE user_id = %s", (session["user_id"],))
    total_bills = cursor.fetchone()[0]
    cursor.execute("SELECT * FROM stock WHERE user_id = %s ORDER BY created_at DESC LIMIT 5", (session["user_id"],))
    recent_stock = cursor.fetchall()
    cursor.execute("SELECT * FROM stock WHERE user_id = %s AND quantity <= low_stock_alert", (session["user_id"],))
    low_stock = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("dashboard.html",
        total_stock=total_stock,
        low_stock_count=low_stock_count,
        total_bills=total_bills,
        recent_stock=recent_stock,
        low_stock=low_stock
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/stock")
def stock():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM stock WHERE user_id = %s ORDER BY item_name", (session["user_id"],))
    stock_items = cursor.fetchall()
    cursor.execute("SELECT * FROM stock WHERE user_id = %s AND quantity <= low_stock_alert", (session["user_id"],))
    low_stock = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("stock.html", stock=stock_items, low_stock=low_stock)

@app.route("/stock/add", methods=["POST"])
def add_stock():
    if "user_id" not in session:
        return redirect(url_for("login"))
    item_name = request.form["item_name"]
    quantity = int(request.form["quantity"])
    unit = request.form["unit"]
    low_stock_alert = int(request.form["low_stock_alert"] or 5)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO stock (user_id, item_name, quantity, unit, low_stock_alert) VALUES (%s, %s, %s, %s, %s)",
        (session["user_id"], item_name, quantity, unit, low_stock_alert)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("stock"))

@app.route("/stock/delete/<int:item_id>")
def delete_stock(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM stock WHERE id = %s AND user_id = %s", (item_id, session["user_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("stock"))

@app.route("/bills")
def bills():
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills WHERE user_id = %s ORDER BY created_at DESC", (session["user_id"],))
    bills = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("bills.html", bills=bills)

@app.route("/bills/add", methods=["POST"])
def add_bill():
    if "user_id" not in session:
        return redirect(url_for("login"))
    
    customer_name = request.form["customer_name"]
    total_amount = float(request.form["total_amount"])
    status = request.form["status"]
    
    item_names = request.form.getlist("item_name[]")
    item_qtys = request.form.getlist("item_qty[]")
    item_prices = request.form.getlist("item_price[]")
    
    items_text = ", ".join([
        f"{item_names[i]} x{item_qtys[i]} @ ₹{item_prices[i]}"
        for i in range(len(item_names))
    ])
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO bills (user_id, customer_name, total_amount, status, items) VALUES (%s, %s, %s, %s, %s)",
        (session["user_id"], customer_name, total_amount, status, items_text)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("bills"))
@app.route("/bills/delete/<int:bill_id>")
def delete_bill(bill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM bills WHERE id = %s AND user_id = %s", (bill_id, session["user_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("bills"))

@app.route("/bills/print/<int:bill_id>")
def print_bill(bill_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills WHERE id = %s AND user_id = %s", (bill_id, session["user_id"]))
    bill = cursor.fetchone()
    cursor.execute("SELECT shop_name, owner_name FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("print_bill.html", bill=bill, user=user)

if __name__ == "__main__":
    app.run(debug=True)