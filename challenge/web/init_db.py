"""Script d'initialisation standalone de la base de données."""
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(__file__), "blocmanager.db")

con = sqlite3.connect(DB_PATH)
cur = con.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    role TEXT DEFAULT 'user'
)""")
cur.execute("DELETE FROM users")
cur.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'Lea2014', 'admin')")
cur.execute("INSERT INTO users (username, password, role) VALUES ('dr.martin', 'Martin2023!', 'medecin')")
con.commit()
con.close()
print("[OK] Base de données initialisée.")
print("     - admin / Lea2014 (admin)")
print("     - dr.martin / Martin2023! (medecin)")
