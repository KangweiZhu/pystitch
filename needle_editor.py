import os, json, socket, subprocess, time, threading, uuid, flask
from flask import Flask, render_template, jsonify, request
from flask_sock import Sock
from urllib.parse import parse_qs

app = Flask(__name__)
sock = Sock(app)

BASE = os.path.dirname(os.path.abspath(__file__))
STATIC = os.path.join(BASE, "static")
NEEDLES = os.path.join(BASE, "needles")
os.makedirs(NEEDLES, exist_ok=True)


def get_qemu_sessions():
    out = subprocess.run(["pgrep", "-a", "qemu-system"], capture_output=True, text=True).stdout
    sessions = []
    for line in out.strip().splitlines():
        if "-qmp" not in line:
            continue
        pid, cmd = line.split(" ", 1)
        for part in cmd.split():
            if part.startswith("unix:") and ".sock" in part:
                sock_path = part.split("unix:")[1].split(",")[0]
                sessions.append({"pid": pid, "qmp": sock_path, "cmd": cmd})
    return sessions


@app.route("/")
def index():
    return render_template("index.html", sessions=get_qemu_sessions())


@app.route("/session/<pid>")
def editor(pid):
    return render_template("editor.html", pid=pid)


@app.route("/api/sessions")
def api_sessions():
    return jsonify(get_qemu_sessions())


@app.route("/save", methods=["POST"])
def save_needle():
    print('hit save needle endpoint')
    try:
        meta_file = request.files["meta"]
        image_file = request.files["image"]

        meta = json.loads(meta_file.read().decode("utf-8"))
        name = meta["name"]
        tags = meta["tags"]
        areas = meta["areas"]

        # Save JSON
        with open(os.path.join(NEEDLES, f"{name}.json"), "w") as f:
            json.dump({
                "area": areas,
                "properties": [],
                "tags": tags
            }, f, indent=2)

        # Save Image
        image_path = os.path.join(NEEDLES, f"{name}.png")
        image_file.save(image_path)

        return jsonify({"status": "ok", "saved": name})

    except Exception as e:
        print("❌ Save failed:", e)
        return jsonify({"status": "error", "message": str(e)}), 500



@sock.route("/ws")
def screenshot_socket(ws):
    query_string = ws.environ.get("QUERY_STRING", "")
    query = parse_qs(query_string)
    pid = query.get("pid", [None])[0]

    sessions = get_qemu_sessions()
    if not pid or not sessions:
        ws.close()
        return

    session = next((s for s in sessions if s["pid"] == pid), None)
    if not session:
        ws.close()
        return

    qmp_path = session["qmp"]

    unique = uuid.uuid4().hex
    bmp = os.path.join(STATIC, f"screenshot_{unique}.bmp")
    png = os.path.join(STATIC, f"screenshot_{unique}.png")

    stop_event = threading.Event()

    def send_loop():
        while not stop_event.is_set():
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                    s.connect(qmp_path)
                    sf = s.makefile("rw")
                    json.loads(sf.readline())
                    sf.write(json.dumps({"execute": "qmp_capabilities"}) + "\n")
                    sf.flush()
                    sf.readline()
                    sf.write(json.dumps({
                        "execute": "screendump",
                        "arguments": {"filename": bmp}
                    }) + "\n")
                    sf.flush()
                    sf.readline()

                subprocess.run(["./magick", bmp, png], check=True)
                with open(png, "rb") as f:
                    ws.send(f.read())

            except Exception as e:
                print("screendump/send error:", e)
                break

            time.sleep(1)

        # Cleanup temp files, will be triggered when the qemu session is closed. So remember terminating qemu before terminating this server.
        # Otherwise the bmp & png files will stack inside needle_editor/static directory.
        for p in (bmp, png):
            try:
                os.remove(p)
            except OSError:
                pass

    thread = threading.Thread(target=send_loop, daemon=True)
    thread.start()

    try:
        while True:
            msg = ws.receive(timeout=5)
            if msg is None:
                print("WebSocket closed by client")
                break
            if msg == "__close__":
                print("Received __close__ from client")
                stop_event.set()
                break
    except Exception as e:
        print("WebSocket receive error:", e)
    finally:
        stop_event.set()
        thread.join()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
