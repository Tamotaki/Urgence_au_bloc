from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3, os

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
    cur.execute("""CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        salle TEXT NOT NULL,
        chirurgien TEXT NOT NULL,
        heure_debut TEXT NOT NULL,
        heure_fin TEXT NOT NULL,
        type_acte TEXT NOT NULL,
        statut TEXT DEFAULT 'confirmé'
    )""")
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'Lea2014', 'admin')")
        cur.execute("INSERT INTO users (username, password, role) VALUES ('dr.martin', 'Martin2023!', 'medecin')")
    cur.execute("SELECT COUNT(*) FROM reservations")
    if cur.fetchone()[0] == 0:
        reservations = [
            ("Bloc A", "Dr. Martin", "08:00", "10:30", "Appendicectomie"),
            ("Bloc A", "Dr. Rousseau", "11:00", "13:00", "Cholécystectomie"),
            ("Bloc B", "Dr. Chen", "08:30", "11:00", "Arthroplastie genou"),
            ("Bloc B", "Dr. Leblanc", "13:00", "15:30", "Herniorraphie"),
            ("Bloc C", "Dr. Martin", "14:00", "17:00", "Pontage coronarien"),
            ("Bloc D", "Dr. Faure", "09:00", "12:00", "Résection colique"),
        ]
        cur.executemany(
            "INSERT INTO reservations (salle, chirurgien, heure_debut, heure_fin, type_acte) VALUES (?,?,?,?,?)",
            reservations
        )
    con.commit()
    con.close()

# ─── ROUTES RANSOMWARE (page piratée) ────────────────────────────────────────
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
        # ⚠ VULNERABILITE INTENTIONNELLE : injection SQL
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        cur.execute(query)
        user = cur.fetchone()
        con.close()
        if user:
            session["user"] = user[1]
            session["role"] = user[3]
            session["mode"] = "hacked"
            return redirect(url_for("dashboard_hacked"))
        else:
            error = "Identifiants incorrects."
    except Exception as e:
        error = f"Erreur système : {e}"
    return render_template("index.html", error=error)

@app.route("/dashboard")
def dashboard_hacked():
    if "user" not in session:
        return redirect(url_for("index"))
    return render_template("dashboard.html", user=session.get("user"), role=session.get("role"))

# ─── ROUTES VERSION RESTAURÉE (page saine) ───────────────────────────────────
@app.route("/secure", methods=["GET"])
def index_clean():
    return render_template("index_clean.html")

@app.route("/secure/login", methods=["POST"])
def login_clean():
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    error = None
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # ✅ REQUETE PARAMETREE — protection contre SQLi
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    con.close()
    if user:
        session["user"] = user[1]
        session["role"] = user[3]
        session["mode"] = "clean"
        return redirect(url_for("dashboard_clean"))
    else:
        error = "Identifiants incorrects."
    return render_template("index_clean.html", error=error)

@app.route("/secure/dashboard")
def dashboard_clean():
    if "user" not in session or session.get("mode") != "clean":
        return redirect(url_for("index_clean"))
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT * FROM reservations ORDER BY salle, heure_debut")
    reservations = cur.fetchall()
    con.close()
    return render_template("dashboard_clean.html",
                           user=session.get("user"),
                           role=session.get("role"),
                           reservations=reservations)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
