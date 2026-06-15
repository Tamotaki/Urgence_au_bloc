#!/usr/bin/env python3
"""
Generateur de challenge CTF - Hopital Saint-Louis
Scenario : ransomware + recon logs + SQLi + XOR
"""
import os
import random
import datetime
import hashlib

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR  = "/var/log/apache2"
TMP_DIR  = "/tmp"
WWW_DIR  = "/var/www/html"

XOR_KEY  = "S3cr3tK3y!"
FLAG     = "CTF{recon_sqli_xordecrypt}"

# Seed pour reproductibilite
random.seed(42)

# Pools de donnees pour generer du bruit realiste
LEGIT_IPS = [
    "10.42.0.15",   # poste infirmier 1
    "10.42.0.18",   # poste infirmier 2
    "10.42.0.22",   # poste admin
    "10.42.1.4",    # medecin wifi
    "10.42.1.7",    # medecin wifi
    "10.42.2.10",   # bloc operatoire
    "10.42.2.11",   # bloc operatoire
    "192.168.50.3", # imprimante
    "192.168.50.5", # NAS backup
    "127.0.0.1",    # monitoring local
]

NOISE_IPS = [
    "45.155.205.233",
    "194.165.16.77",
    "92.255.85.135",
    "162.142.125.219",
    "167.94.138.45",
    "198.235.24.12",
    "66.249.66.1",
    "157.55.39.42",
]

# Tor exit node connu
ATTACKER_IP = "185.220.101.47"

LEGIT_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "curl/8.4.0",
    "Wget/1.21.4",
]

BOT_UAS = [
    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)",
    "Mozilla/5.0 (compatible; CensysInspect/1.1; +https://about.censys.io/)",
    "Mozilla/5.0 (compatible; Nimbostratus-Bot/v1.3.2)",
    "python-requests/2.31.0",
    "Go-http-client/1.1",
]

LEGIT_PATHS = [
    ("/",                         200, 1842),
    ("/login",                    200, 1024),
    ("/static/css/main.css",      200, 4521),
    ("/static/js/app.js",         200, 12480),
    ("/static/img/logo.png",      200, 8932),
    ("/static/img/favicon.ico",   200, 318),
    ("/api/health",               200, 47),
    ("/api/status",               200, 128),
    ("/dashboard",                200, 5421),
    ("/dashboard/patients",       200, 8234),
    ("/dashboard/plannings",      200, 6789),
    ("/api/bloc/list",            200, 2145),
    ("/api/notifications",        200, 512),
    ("/static/css/bootstrap.css", 200, 152480),
    ("/favicon.ico",              200, 318),
]

SCAN_PATHS = [
    ("/.env",             404, 196),
    ("/.git/config",      404, 196),
    ("/.git/HEAD",        404, 196),
    ("/wp-admin",         404, 196),
    ("/wp-login.php",     404, 196),
    ("/phpmyadmin/",      404, 196),
    ("/admin",            404, 196),
    ("/.aws/credentials", 404, 196),
    ("/config.php",       404, 196),
    ("/backup.zip",       404, 196),
    ("/.DS_Store",        404, 196),
    ("/robots.txt",       200, 64),
    ("/sitemap.xml",      404, 196),
    ("/server-status",    403, 218),
    ("/api/v1/users",     404, 196),
    ("/actuator/health",  404, 196),
    ("/swagger.json",     404, 196),
]


# Genere une ligne de log au format Apache combined
def make_log_line(t, ip, method, path, status, size, ua, referer="-"):
    ts = t.strftime("%d/%b/%Y:%H:%M:%S +0000")
    return f'{ip} - - [{ts}] "{method} {path} HTTP/1.1" {status} {size} "{referer}" "{ua}"'


# Genere du trafic de fond credible
def generate_noise_events(start_time, count=3):
    events = []
    t = start_time
    for _ in range(count):
        ip = random.choice(LEGIT_IPS)
        path, status, size = random.choice(LEGIT_PATHS)
        ua = random.choice(LEGIT_UAS)
        method = "GET" if random.random() < 0.85 else "POST"
        events.append((t, ip, method, path, status, size, ua, "-"))
        t += datetime.timedelta(seconds=random.randint(15, 45))
    return events


# Reconstitue le scenario d'attaque dans l'ordre chronologique
def generate_attack_events(start_time):
    SQLMAP_UA = "sqlmap/1.7.11#stable (https://sqlmap.org)"
    BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"

    attack = [
        # Phase 1 : reconnaissance
        (0,    "GET",  "/login",            200, 1024,  BROWSER_UA, "-"),
        # Phase 2 : tentative SQLi
        (10,   "POST", "/login",            500, 480,   SQLMAP_UA, "-"),
        (12,   "POST", "/login",            302, 0,     SQLMAP_UA, "-"),
        # Phase 3 : dashboard & upload note
        (15,   "GET",  "/dashboard",        200, 5421,  BROWSER_UA, "-"),
        (20,   "POST", "/api/upload",       200, 84,    BROWSER_UA, "-"),
        (25,   "GET",  "/uploads/note.txt", 200, 312,   BROWSER_UA, "-"),
        # Phase 4 : exfiltration backup
        (30,   "GET",  "/tmp/backup.xor",   200, 512,   BROWSER_UA, "-"),
        # Phase 5 : fuite de clé (User-Agent custom)
        (35,   "GET",  "/",                 200, 1842,  f"XOR_KEY={XOR_KEY}", "-"),
    ]

    events = []
    for offset, method, path, status, size, ua, referer in attack:
        t = start_time + datetime.timedelta(seconds=offset)
        events.append((t, ATTACKER_IP, method, path, status, size, ua, referer))
    return events


# Genere le access.log final
def generate_apache_logs():
    os.makedirs(LOG_DIR, exist_ok=True)
    base_time = datetime.datetime(2024, 11, 18, 3, 20, 0)

    # Bruit avant l'attaque
    noise_before = generate_noise_events(base_time, count=5)

    # L'attaque commence a 03:38
    attack_start = datetime.datetime(2024, 11, 18, 3, 38, 0)
    attack = generate_attack_events(attack_start)

    # Bruit apres l'attaque
    noise_after = generate_noise_events(
        attack_start + datetime.timedelta(seconds=40),
        count=5,
    )

    all_events = noise_before + attack + noise_after
    all_events.sort(key=lambda e: e[0])

    lines = [make_log_line(*e) for e in all_events]

    with open(os.path.join(LOG_DIR, "access.log"), "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"[+] access.log : {len(lines)} lignes generees")


# error.log avec indices supplementaires
def generate_error_log():
    error_lines = [
        "[Mon Nov 18 03:40:46.123456 2024] [php:notice] [pid 1247] [client 185.220.101.47:54321] PHP Notice: Undefined index: username in /var/www/html/login.php on line 23",
        "[Mon Nov 18 03:40:47.234567 2024] [php:warn] [pid 1247] [client 185.220.101.47:54322] PHP Warning: mysqli_query(): You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near '\\' OR 1=1-- ' at line 1 in /var/www/html/login.php on line 31",
        "[Mon Nov 18 03:40:48.345678 2024] [php:warn] [pid 1247] [client 185.220.101.47:54323] PHP Warning: mysqli_fetch_assoc() expects parameter 1 to be mysqli_result, bool given in /var/www/html/login.php on line 35",
        "[Mon Nov 18 03:40:51.456789 2024] [php:warn] [pid 1247] [client 185.220.101.47:54324] PHP Warning: mysqli_query(): You have an error in your SQL syntax; check the manual that corresponds to your MariaDB server version for the right syntax to use near 'AND SLEEP(5)-- ' at line 1 in /var/www/html/login.php on line 31",
        "[Mon Nov 18 03:42:08.567890 2024] [php:notice] [pid 1248] [client 185.220.101.47:54401] PHP Notice: Login successful for user 'admin' (auth bypass detected? check WAF) in /var/www/html/login.php on line 42",
        "[Mon Nov 18 03:46:32.678901 2024] [php:warn] [pid 1251] [client 185.220.101.47:54502] PHP Warning: move_uploaded_file(): Unable to move '/tmp/phpA8x2K9' to '/var/www/html/uploads/note.txt' in /var/www/html/api/upload.php on line 18",
        "[Mon Nov 18 03:47:55.789012 2024] [authz_core:error] [pid 1252] [client 185.220.101.47:54603] AH01630: client denied by server configuration: /var/www/html/dashboard/admin",
    ]
    with open(os.path.join(LOG_DIR, "error.log"), "w") as f:
        f.write("\n".join(error_lines) + "\n")
    print(f"[+] error.log : {len(error_lines)} lignes generees")


# Note laissee par l'attaquant
def generate_attacker_note():
    os.makedirs(os.path.join(WWW_DIR, "uploads"), exist_ok=True)
    note = """>>> RANSOM_NOTE.txt <<<

Vos fichiers ont ete chiffres.
Toutes vos sauvegardes ont ete deplacees dans /tmp/backup.xor

Pour recuperer vos donnees :
  1. Identifier la cle de dechiffrement (XOR symetrique simple)
  2. Utiliser l'outil fourni : /tmp/ransomware_fake.py
  3. Payer 0.5 BTC a : bc1q[redacted]

Vous avez 72h. Au-dela, la cle sera detruite.

PS : Bonne chance pour la trouver, elle est sous votre nez.
PS2: pensez a verifier vos logs avant de redemarrer.

- S0lar1s Group
"""
    with open(os.path.join(WWW_DIR, "uploads", "note.txt"), "w") as f:
        f.write(note)
    print(f"[+] note.txt depose dans {WWW_DIR}/uploads/")


# Chiffrement XOR
def xor_encrypt(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])


# Genere le fichier chiffre
def generate_xor_file():
    os.makedirs(TMP_DIR, exist_ok=True)
    plaintext = f"""
SAUVEGARDE SYSTEME - CENTRE HOSPITALIER SAINT-LOUIS
Service Informatique - DSI

Date export   : 18/11/2024 03:47:12 UTC
Serveur       : saint-louis-srv01.intra.hsl
Operateur     : backup-svc (cron auto)
Volume        : 1.2 GB (compresse)
Checksum      : sha256:8f2c4e9a...

PLANNINGS BLOC OPERATOIRE (semaine 47)

  Bloc A - Cardiologie
    Lundi    08:00  Dr. Martin     / Inf. Dupont
    Mardi    07:30  Dr. Rousseau   / Inf. Bernard
    Mercredi 09:00  Dr. Martin     / Inf. Dupont
    Jeudi    08:00  Dr. Rousseau   / Inf. Petit
    Vendredi 07:00  Dr. Martin     / Inf. Bernard

  Bloc B - Orthopedie
    Lundi    08:30  Dr. Chen       / Inf. Moreau
    Mardi    08:00  Dr. Leblanc    / Inf. Garcia
    Mercredi 07:30  Dr. Chen       / Inf. Moreau
    Jeudi    09:00  Dr. Leblanc    / Inf. Garcia
    Vendredi 08:00  Dr. Chen       / Inf. Moreau

  Bloc C - Neurochirurgie
    Lundi    06:00  Dr. Martin     / Inf. Lambert
    Mercredi 06:00  Dr. Martin     / Inf. Lambert
    Vendredi 06:00  Dr. Martin     / Inf. Lambert

  Bloc D - Urgences
    24/7 garde tournante - Dr. Faure (referent)

DONNEES PATIENTS (extrait, anonymise)

  Patient #04821 - Suivi post-op cardiaque (J+3)
  Patient #04822 - Preparation arthroscopie genou
  Patient #04823 - Surveillance neurologique
  Patient #04824 - Sortie prevue 19/11
  Patient #04825 - Bilan pre-operatoire (RDV bloc C)

ACCES SYSTEME (a conserver en lieu sur)

  Compte admin DSI    : root / [voir coffre-fort physique]
  Compte backup-svc   : backup-svc / [rotation mensuelle]
  Compte monitoring   : prom-ro / [LDAP]
  VPN site distant    : hsl-vpn / [token YubiKey]

CLE DE RESTAURATION SYSTEME

  /!\\ NE PAS DIFFUSER - USAGE INTERNE DSI UNIQUEMENT /!\\

  {FLAG}

  Cette cle permet de restaurer l'integralite de l'arborescence
  /var/data/hsl/ en cas de defaillance majeure.

PROCEDURE DE RESTAURATION

  1. Monter le volume de sauvegarde sur /mnt/restore
  2. Executer : hsl-restore --key=<CLE> --target=/var/data/hsl
  3. Verifier l'integrite : hsl-verify --full
  4. Redemarrer les services : systemctl restart hsl-*

FIN DU FICHIER
""".encode()

    encrypted = xor_encrypt(plaintext, XOR_KEY)
    with open(os.path.join(TMP_DIR, "backup.xor"), "wb") as f:
        f.write(encrypted)
    print(f"[+] backup.xor : {len(encrypted)} octets chiffres")


# Indices caches dissemines
def generate_hidden_clues():
    clues = {
        os.path.join(TMP_DIR, ".hidden_clue"):
            "Indice 1/3 - Les attaquants laissent toujours des traces.\n"
            "Cherche dans /var/log/apache2/ - le diable est dans les User-Agents.\n",
        os.path.join(TMP_DIR, ".readme_dsi"):
            "Note DSI - 18/11/2024\n\n"
            "Le backup nocturne a ete deplace dans /tmp suite a l'incident.\n"
            "Format : XOR symetrique (script de dechiffrement dans /tmp/).\n"
            "La cle n'est PAS dans ce fichier. Demander a l'equipe SOC.\n",
        "/var/log/apache2/.fail2ban_skipped":
            "WARN: fail2ban desactive temporairement pour debug - 17/11/2024 22:14\n"
            "TODO: reactiver apres maintenance (ticket #4421)\n",
    }
    for path, content in clues.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        print(f"[+] indice : {path}")


if __name__ == "__main__":
    print("[*] Generation du challenge HOPITAL SAINT-LOUIS...")
    generate_apache_logs()
    generate_error_log()
    generate_attacker_note()
    generate_xor_file()
    generate_hidden_clues()
    print("[+] Challenge pret - bonne chance aux joueurs")