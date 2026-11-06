#!/usr/bin/env python3
"""
Eisenhower Daily - local launcher.

Start it with:  python run_planner.py   (or double-click the Start file for your system)
It opens the planner at http://localhost:8765 in your browser.

- Your tasks are saved to planner-data.json in this folder.
- Jira site, email and API token (entered in the planner's settings) are saved
  to jira-config.json in this folder. Nothing is sent anywhere except to your Jira site.
- Only programs on this computer can reach it (it listens on 127.0.0.1).
Needs Python 3.8 or newer. No extra packages.
"""
import base64
import json
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "eisenhower-daily.html")
DATA = os.path.join(HERE, "planner-data.json")
CONFIG = os.path.join(HERE, "jira-config.json")
PORT = int(os.environ.get("PLANNER_PORT", "8765"))
FIELDS = "summary,status,priority,duedate,issuetype,project"
HEAD = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
        '</head><body>')
LOCK = threading.Lock()


def read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def site_url(site):
    site = (site or "").strip().rstrip("/")
    if not site:
        return ""
    if not site.startswith("http"):
        site = "https://" + site
    return site


def jira_search(jql):
    cfg = read_json(CONFIG, {})
    base, email, token = site_url(cfg.get("site")), cfg.get("email"), cfg.get("token")
    if not (base and email and token):
        return 400, {"code": "no_config",
                     "error": "Add your Jira site, email and API token in Rules & settings > Jira."}
    auth = base64.b64encode(f"{email}:{token}".encode()).decode()
    issues, page_token, complete = [], None, False
    for _ in range(5):  # up to 500 tickets
        q = {"jql": jql, "fields": FIELDS, "maxResults": "100"}
        if page_token:
            q["nextPageToken"] = page_token
        req = urllib.request.Request(
            base + "/rest/api/3/search/jql?" + urllib.parse.urlencode(q),
            headers={"Authorization": "Basic " + auth, "Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.load(r)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:300]
            if e.code == 401:
                return 502, {"code": "auth", "error": "Jira rejected the email or API token."}
            if e.code == 400:
                return 502, {"code": "jql", "error": "Jira didn't accept the search (JQL): " + detail}
            return 502, {"code": "jira_error", "error": f"Jira returned {e.code}: {detail}"}
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            return 502, {"code": "network",
                         "error": f"The launcher couldn't reach {base}. Check your internet or VPN. ({e})"}
        issues += body.get("issues", [])
        page_token = body.get("nextPageToken")
        if body.get("isLast", True) or not page_token:
            complete = True
            break
    return 200, {"issues": issues, "complete": complete, "siteUrl": base}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _allowed(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0]
        origin = self.headers.get("Origin")
        ok_host = host in ("localhost", "127.0.0.1")
        ok_origin = origin is None or origin in (f"http://localhost:{PORT}", f"http://127.0.0.1:{PORT}")
        return ok_host and ok_origin

    def _send(self, status, body, ctype="application/json"):
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _json_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0 or n > 20_000_000:
            return None
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except ValueError:
            return None

    def do_GET(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        u = urllib.parse.urlparse(self.path)
        if u.path in ("/", "/index.html"):
            with open(PAGE, encoding="utf-8") as f:
                html = HEAD + f.read() + "</body></html>"
            return self._send(200, html.encode("utf-8"), "text/html")
        if u.path == "/api/state":
            return self._send(200, read_json(DATA, {}))
        if u.path == "/api/jira/config":
            c = read_json(CONFIG, {})
            return self._send(200, {"site": c.get("site", ""), "email": c.get("email", ""),
                                    "hasToken": bool(c.get("token"))})
        if u.path == "/api/jira/search":
            jql = urllib.parse.parse_qs(u.query).get("jql", [""])[0]
            status, body = jira_search(jql)
            return self._send(status, body)
        return self._send(404, {"error": "not found"})

    def do_PUT(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        if urllib.parse.urlparse(self.path).path != "/api/state":
            return self._send(404, {"error": "not found"})
        body = self._json_body()
        if not isinstance(body, dict):
            return self._send(400, {"error": "bad data"})
        with LOCK:
            write_json(DATA, body)
        return self._send(200, {"ok": True})

    def do_POST(self):
        if not self._allowed():
            return self._send(403, {"error": "forbidden"})
        if urllib.parse.urlparse(self.path).path != "/api/jira/config":
            return self._send(404, {"error": "not found"})
        body = self._json_body() or {}
        with LOCK:
            c = read_json(CONFIG, {})
            for k in ("site", "email"):
                if isinstance(body.get(k), str):
                    c[k] = body[k].strip()
            if isinstance(body.get("token"), str) and body["token"].strip():
                c["token"] = body["token"].strip()
            write_json(CONFIG, c)
        return self._send(200, {"site": c.get("site", ""), "email": c.get("email", ""),
                                "hasToken": bool(c.get("token"))})


def main():
    if not os.path.exists(PAGE):
        sys.exit("eisenhower-daily.html must be in the same folder as this launcher.")
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError:
        url = f"http://localhost:{PORT}"
        print(f"The planner already seems to be running. Opening {url}")
        webbrowser.open(url)
        return
    url = f"http://localhost:{PORT}"
    print(f"Eisenhower Daily is running at {url}")
    print("Keep this window open while you use the planner. Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
