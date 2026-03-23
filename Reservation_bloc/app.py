from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3, os, hashlib

app = Flask(__name__)
app.secret_key = "ransom_secret_key_2024"
DB_PATH = os.path.join(os.path.dirname(__file__), "blocmanager.db")

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    )""")
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Mot de passe faible intentionnel (Lea2014 en clair)
        cur.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'Lea2014', 'admin')")
        cur.execute("INSERT INTO users (username, password, role) VALUES ('dr.martin', 'Martin2023!', 'medecin')")
    con.commit()
    con.close()

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    error = None
    try:
        con = sqlite3.connect(DB_PATH)
        cur = con.cursor()
        # VULNERABILITE INTENTIONNELLE : injection SQL
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cur.execute(query)
        user = cur.fetchone()
        con.close()
        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            return redirect(url_for("dashboard"))
        else:
            error = "Identifiants incorrects."
    except Exception as e:
        error = f"Erreur système : {e}"
    return render_template("index.html", error=error)

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user=session.get("user"), role=session.get("role"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=80, debug=False)
