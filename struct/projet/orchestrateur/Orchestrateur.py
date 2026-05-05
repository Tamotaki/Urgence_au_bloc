import uuid
import subprocess
import threading
import time
from flask import Flask, jsonify, request, redirect, abort

app = Flask(__name__)

sessions = {}          # { sid: { container_id, port, started_at } }
PORT_MIN  = 8100
PORT_MAX  = 8200
IMAGE     = "urgence-au-bloc-challenge"   # Nom de l'image de Gabriela
TTL       = 10800                          # 3h max par session


def next_port():
    used = {s["port"] for s in sessions.values()}
    for p in range(PORT_MIN, PORT_MAX + 1):
        if p not in used:
            return p
    return None


def kill(sid):
    s = sessions.pop(sid, None)
    if s:
        subprocess.run(["docker", "rm", "-f", s["container_id"]],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def cleanup():
    while True:
        time.sleep(60)
        now = time.time()
        for sid in [s for s, v in list(sessions.items()) if now - v["started_at"] > TTL]:
            kill(sid)


# Routes

@app.route("/")
def index():
    return redirect("/play")


@app.route("/play")
def play():
    port = next_port()
    if not port:
        abort(503, "Serveur plein, réessayez dans quelques minutes.")

    sid = str(uuid.uuid4())
    r = subprocess.run(
        ["docker", "run", "-d",
         "--name", f"challenge_{sid[:8]}",
         "-p", f"{port}:80",
         "--network", "none",
         IMAGE],
        capture_output=True, text=True
    )
    if r.returncode != 0:
        abort(500, f"Erreur Docker : {r.stderr.strip()}")

    sessions[sid] = {"container_id": r.stdout.strip(), "port": port, "started_at": time.time()}
    return redirect(f"/game/{sid}")


@app.route("/game/<sid>")
def game(sid):
    if sid not in sessions:
        abort(404, "Session introuvable ou expirée.")
    host = request.host.split(":")[0]
    return redirect(f"http://{host}:{sessions[sid]['port']}/")


@app.route("/api/status/<sid>")
def status(sid):
    if sid not in sessions:
        return jsonify({"error": "session introuvable"}), 404
    s = sessions[sid]
    elapsed = int(time.time() - s["started_at"])
    return jsonify({"session_id": sid, "port": s["port"],
                    "elapsed": elapsed, "remaining": max(0, TTL - elapsed)})


@app.route("/api/stop/<sid>", methods=["POST"])
def stop(sid):
    if sid not in sessions:
        return jsonify({"error": "session introuvable"}), 404
    kill(sid)
    return jsonify({"ok": True})


@app.route("/api/sessions")
def list_sessions():
    now = time.time()
    return jsonify([{"sid": sid, "port": s["port"],
                     "remaining": max(0, TTL - int(now - s["started_at"]))}
                    for sid, s in sessions.items()])


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "sessions": len(sessions)})


# Démarrage

if __name__ == "__main__":
    threading.Thread(target=cleanup, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)