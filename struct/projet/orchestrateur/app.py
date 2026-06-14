import uuid
import os
import threading
import time
import docker
import requests as req
from flask import Flask, jsonify, request, redirect, abort, render_template, Response, stream_with_context, make_response

app = Flask(__name__, static_folder=None)

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

# Detect network if running inside a Docker container
orchestrator_network = None
if docker_client:
    try:
        import socket
        container_id = socket.gethostname()
        self_container = docker_client.containers.get(container_id)
        networks = self_container.attrs.get('NetworkSettings', {}).get('Networks', {})
        if networks:
            orchestrator_network = list(networks.keys())[0]
            print(f"[+] Orchestrator is running inside a container. Network: {orchestrator_network}")
    except Exception as e:
        print(f"[*] Orchestrator is running on host (not in a container): {e}")


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
        run_kwargs = {
            "name": container_name,
            "detach": True,
            "restart_policy": {"Name": "unless-stopped"}
        }
        # If we are in a docker network, run on the same network
        if orchestrator_network:
            run_kwargs["network"] = orchestrator_network
        else:
            # Otherwise map port to host
            run_kwargs["ports"] = {'80/tcp': port}

        container = docker_client.containers.run(IMAGE, **run_kwargs)
        container_id = container.id
        print(f"[+] Started container {container_name} (ID: {container_id[:12]})")

        # Get container IP address if running on network
        container.reload()
        ip_address = None
        if orchestrator_network:
            for _ in range(5):
                networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                if orchestrator_network in networks:
                    ip_address = networks[orchestrator_network].get('IPAddress')
                    if ip_address:
                        break
                time.sleep(0.1)
                container.reload()
            print(f"[+] Container {container_name} IP: {ip_address}")

    except Exception as e:
        print(f"[-] Docker run error: {e}")
        abort(500, f"Erreur de démarrage Docker : {e}")
    sessions[sid] = {
        "container_id": container_id,
        "port": port,
        "ip": ip_address,
        "started_at": time.time()
    }
    return redirect(f"/game/{sid}")


@app.route("/game/<sid>")
def game(sid):
    if sid not in sessions:
        abort(404, "Session introuvable ou expirée.")
    resp = make_response(render_template("game.html", sid=sid))
    resp.set_cookie("current_sid", sid, path="/")
    return resp


@app.route("/proxy/<sid>/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/proxy/<sid>/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def proxy(sid, path):
    if sid not in sessions:
        abort(404)
    port = sessions[sid]["port"]
    ip = sessions[sid].get("ip")
    if ip:
        url = f"http://{ip}/{path}"
    else:
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
        
        # Build headers and rewrite Location for redirects
        headers = []
        for k, v in resp.headers.items():
            k_low = k.lower()
            if k_low in ("transfer-encoding", "content-encoding", "content-length"):
                continue
            if k_low == "location":
                if v.startswith("/"):
                    v = f"/proxy/{sid}{v}"
                elif v.startswith(f"http://127.0.0.1:{port}/"):
                    v = v.replace(f"http://127.0.0.1:{port}/", f"/proxy/{sid}/")
                elif ip and v.startswith(f"http://{ip}/"):
                    v = v.replace(f"http://{ip}/", f"/proxy/{sid}/")
            headers.append((k, v))
            
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            # Read full content to perform HTML substitutions
            content = resp.content.decode("utf-8", errors="ignore")
            content = content.replace('"/static/', f'"/proxy/{sid}/static/')
            content = content.replace("'/static/", f"'/proxy/{sid}/static/")
            content = content.replace('action="/', f'action="/proxy/{sid}/')
            content = content.replace("action='/", f"action='/proxy/{sid}/")
            
            flask_resp = Response(content, status=resp.status_code, headers=headers)
            flask_resp.set_cookie("current_sid", sid, path="/")
            return flask_resp
            
        flask_resp = Response(stream_with_context(resp.iter_content(chunk_size=4096)),
                              status=resp.status_code,
                              headers=headers)
        flask_resp.set_cookie("current_sid", sid, path="/")
        return flask_resp
    except Exception as e:
        abort(502, f"Proxy error: {e}")


@app.route("/static/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def static_proxy(path):
    return catch_all(f"static/{path}")


@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def catch_all(path):
    sid = request.cookies.get("current_sid")
    if not sid or sid not in sessions:
        abort(404)
    port = sessions[sid]["port"]
    ip = sessions[sid].get("ip")
    if ip:
        url = f"http://{ip}/{path}"
    else:
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
        
        headers = []
        for k, v in resp.headers.items():
            k_low = k.lower()
            if k_low in ("transfer-encoding", "content-encoding", "content-length"):
                continue
            if k_low == "location":
                if v.startswith("/"):
                    v = f"/proxy/{sid}{v}"
                elif v.startswith(f"http://127.0.0.1:{port}/"):
                    v = v.replace(f"http://127.0.0.1:{port}/", f"/proxy/{sid}/")
                elif ip and v.startswith(f"http://{ip}/"):
                    v = v.replace(f"http://{ip}/", f"/proxy/{sid}/")
            headers.append((k, v))
            
        content_type = resp.headers.get("Content-Type", "")
        if "text/html" in content_type:
            content = resp.content.decode("utf-8", errors="ignore")
            content = content.replace('"/static/', f'"/proxy/{sid}/static/')
            content = content.replace("'/static/", f"'/proxy/{sid}/static/")
            content = content.replace('action="/', f'action="/proxy/{sid}/')
            content = content.replace("action='/", f"action='/proxy/{sid}/")
            return Response(content, status=resp.status_code, headers=headers)
            
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