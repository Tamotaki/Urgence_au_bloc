import uuid
import os
import threading
import time
import docker
import requests as req
from flask import Flask, jsonify, request, redirect, abort, render_template, Response, stream_with_context

app = Flask(__name__)

sessions = {}
PORT_MIN  = 8100
PORT_MAX  = 8200
IMAGE     = os.environ.get("CHALLENGE_IMAGE", "urgence-au-bloc-challenge:latest")
TTL       = int(os.environ.get("CHALLENGE_TTL", 10800))

try:
    docker_client = docker.from_env()
except Exception as ex:
    print(f"Warning: Could not connect to Docker daemon: {ex}")
    docker_client = None


def next_port():
    used = {s["port"] for s in sessions.values()}
    if docker_client:
        try:
            for c in docker_client.containers.list(all=True):
                if c.name.startswith("challenge_"):
                    for container_port, host_bindings in c.ports.items():
                        if host_bindings:
                            for binding in host_bindings:
                                used.add(int(binding["HostPort"]))
        except Exception as ex:
            print(f"Warning: Could not list container ports: {ex}")
    for p in range(PORT_MIN, PORT_MAX + 1):
        if p not in used:
            return p
    return None


def kill(sid):
    s = sessions.pop(sid, None)
    if s and docker_client:
        try:
            container = docker_client.containers.get(s["container_id"])
            container.remove(force=True)
            print(f"[+] Container {s['container_id'][:12]} for session {sid} killed.")
        except Exception as e:
            print(f"[-] Error removing container {s['container_id']}: {e}")


def cleanup():
    while True:
        time.sleep(30)
        now = time.time()
        for sid, s in list(sessions.items()):
            if now - s["started_at"] > TTL:
                print(f"[*] Session {sid} expired. Cleaning up...")
                kill(sid)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/play")
def play():
    if not docker_client:
        abort(500, "Le démon Docker n'est pas disponible sur le serveur.")
    port = next_port()
    if not port:
        abort(503, "Serveur plein, réessayez dans quelques minutes.")
    sid = str(uuid.uuid4())
    container_name = f"challenge_{sid[:8]}"
    try:
        container = docker_client.containers.run(
            IMAGE,
            name=container_name,
            detach=True,
            ports={'80/tcp': port},
            restart_policy={"Name": "unless-stopped"}
        )
        container_id = container.id
        print(f"[+] Started container {container_name} on port {port} (ID: {container_id[:12]})")
    except Exception as e:
        print(f"[-] Docker run error: {e}")
        abort(500, f"Erreur de démarrage Docker : {e}")
    sessions[sid] = {"container_id": container_id, "port": port, "started_at": time.time()}
    return redirect(f"/game/{sid}")


@app.route("/game/<sid>")
def game(sid):
    if sid not in sessions:
        abort(404, "Session introuvable ou expirée.")
    return render_template("game.html", sid=sid)


@app.route("/proxy/<sid>/", defaults={"path": ""})
@app.route("/proxy/<sid>/<path:path>")
def proxy(sid, path):
    if sid not in sessions:
        abort(404)
    port = sessions[sid]["port"]
    url = f"http://127.0.0.1:{port}/{path}"
    if request.query_string:
        url += "?" + request.query_string.decode()
    try:
        resp = req.request(
            method=request.method,
            url=url,
            headers={k: v for k, v in request.headers if k.lower() != "host"},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False,
            stream=True,
            timeout=10
        )
        headers = [(k, v) for k, v in resp.headers.items()
                   if k.lower() not in ("transfer-encoding", "content-encoding", "content-length")]
        return Response(stream_with_context(resp.iter_content(chunk_size=4096)),
                        status=resp.status_code,
                        headers=headers)
    except Exception as e:
        abort(502, f"Proxy error: {e}")


@app.route("/api/status/<sid>")
def status(sid):
    if sid not in sessions:
        return jsonify({"error": "session introuvable"}), 404
    s = sessions[sid]
    elapsed = int(time.time() - s["started_at"])
    return jsonify({
        "session_id": sid,
        "port": s["port"],
        "elapsed": elapsed,
        "remaining": max(0, TTL - elapsed)
    })


@app.route("/api/stop/<sid>", methods=["POST"])
def stop(sid):
    if sid not in sessions:
        return jsonify({"error": "session introuvable"}), 404
    kill(sid)
    return jsonify({"ok": True})


@app.route("/api/sessions")
def list_sessions():
    now = time.time()
    return jsonify([
        {"sid": sid, "port": s["port"], "remaining": max(0, TTL - int(now - s["started_at"]))}
        for sid, s in sessions.items()
    ])


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "sessions": len(sessions)})


if __name__ == "__main__":
    if docker_client:
        try:
            print("[*] Cleaning up leftover containers on startup...")
            for c in docker_client.containers.list(all=True):
                if c.name.startswith("challenge_"):
                    print(f"[*] Removing leftover container {c.name}")
                    c.remove(force=True)
        except Exception as e:
            print(f"Error cleaning up old containers: {e}")
    threading.Thread(target=cleanup, daemon=True).start()
    app.run(host="0.0.0.0", port=5000, debug=False)