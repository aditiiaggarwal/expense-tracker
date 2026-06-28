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
    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)