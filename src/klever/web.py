# The clock's local web page. Same URLs as the Arduino firmware v2.x, so the
# existing index.html / app.js / style.css on the SD card work unchanged.
# Copyright (c) 2026 Klever Klox. All rights reserved. See LICENSE.
#
# Everything runs from the main loop via server.poll(): there is no second task,
# so a request can never race the display or the audio player.

import json

from adafruit_httpserver import (GET, POST, FileResponse, JSONResponse, Request,
                                 Response, Server, SSEResponse, Status)

from . import config
from .util import log
from .version import NAME

SETUP_PAGE = """<!DOCTYPE html><html><head><title>Klever Klox WiFi Setup</title>
<meta name="viewport" content="width=device-width, initial-scale=1"><style>
body{font-family:Arial;display:flex;justify-content:center;align-items:center;min-height:100vh;margin:0;background:#1a1a2e;color:#fff}
.c{background:#16213e;padding:32px;border-radius:10px;max-width:400px;width:100%;box-sizing:border-box}
h1{text-align:center;color:#4fc3f7}label{display:block;color:#b0bec5;margin-top:16px}
input{width:100%;padding:10px;border:1px solid #37474f;border-radius:5px;background:#263238;color:#fff;box-sizing:border-box}
button{width:100%;margin-top:24px;padding:12px;background:#4fc3f7;color:#1a1a2e;border:none;border-radius:5px;font-size:16px;font-weight:bold}
p{text-align:center;color:#78909c;font-size:14px}</style></head><body><div class="c"><h1>Klever Klox</h1>
<form action="/save" method="POST"><label for="ssid">WiFi network (SSID)</label>
<input id="ssid" name="ssid" required><label for="password">Password</label>
<input type="password" id="password" name="password"><button type="submit">Connect</button></form>
<p>The clock restarts after saving.</p></div></body></html>"""

MISSING_PAGE = ("<!DOCTYPE html><html><head><title>Klever Klox</title></head><body>"
                "<h1>Klever Klox</h1><p>index.html is missing from the SD card.</p></body></html>")


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


class Web:
    def __init__(self, app, pool, ap_mode):
        self.app = app
        self.ap_mode = ap_mode
        self.sse = []
        self.server = Server(pool, root_path=config.SD_MOUNT if app.sd_ok else None, debug=False)
        if ap_mode:
            self._ap_routes()
        else:
            self._routes()

    def start(self, ip):
        try:
            self.server.start(ip, 80)
            log("[WEB] serving on http://%s" % ip)
        except Exception as e:
            log("[WEB] could not start:", e)

    def poll(self):
        try:
            self.server.poll()
        except Exception as e:                 # a bad request must never stop the clock
            log("[WEB] poll error:", e)

    # ---- server-sent events ----
    def push(self, event, data):
        if not self.sse:
            return
        payload = json.dumps(data)
        alive = []
        for r in self.sse:
            try:
                r.send_event(payload, event=event)
                alive.append(r)
            except Exception:
                try:
                    r.close()
                except Exception:
                    pass
        self.sse = alive

    # ---- normal mode ----
    def _routes(self):
        s, app = self.server, self.app

        def static(request, name, ctype):
            if not app.sd_ok:
                return Response(request, MISSING_PAGE if name == "index.html" else "",
                                content_type=ctype)
            try:
                return FileResponse(request, name, root_path=config.SD_MOUNT, content_type=ctype)
            except Exception:
                return Response(request, MISSING_PAGE, content_type="text/html")

        @s.route("/", GET)
        def index(request: Request):
            return static(request, "index.html", "text/html")

        @s.route("/style.css", GET)
        def css(request: Request):
            return static(request, "style.css", "text/css")

        @s.route("/app.js", GET)
        def js(request: Request):
            return static(request, "app.js", "text/javascript")

        @s.route("/api/settings", GET)
        def get_settings(request: Request):
            return JSONResponse(request, app.public_settings())

        @s.route("/api/settings", POST)
        def post_settings(request: Request):
            try:
                doc = request.json()
            except ValueError:
                doc = None
            if not isinstance(doc, dict):
                return Response(request, "Bad JSON", status=Status(400, "Bad Request"))
            app.apply_web_settings(doc)
            return Response(request, "OK")

        @s.route("/songs", GET)
        def songs(request: Request):
            return JSONResponse(request, [n for n, _ in app.player.songs] if app.player else [])

        @s.route("/api/ota", GET)
        def ota(request: Request):
            return JSONResponse(request, app.ota_status())

        @s.route("/api/ota/check", POST)
        def ota_check(request: Request):
            return Response(request, "Updates are installed over USB in the Python firmware",
                            status=Status(501, "Not Implemented"))

        @s.route("/api/ota/install", POST)
        def ota_install(request: Request):
            return Response(request, "Updates are installed over USB in the Python firmware",
                            status=Status(501, "Not Implemented"))

        @s.route("/events", GET)
        def events(request: Request):
            if len(self.sse) >= 3:             # keep RAM bounded
                old = self.sse.pop(0)
                try:
                    old.close()
                except Exception:
                    pass
            r = SSEResponse(request)
            self.sse.append(r)
            return r

    # ---- first-time setup (access point) ----
    def _ap_routes(self):
        s, app = self.server, self.app

        @s.route("/", GET)
        def setup(request: Request):
            return Response(request, SETUP_PAGE, content_type="text/html")

        @s.route("/generate_204", GET)        # Android captive-portal probe
        def g204(request: Request):
            return Response(request, SETUP_PAGE, content_type="text/html")

        @s.route("/connecttest.txt", GET)     # Windows probe
        def ms_probe(request: Request):
            return Response(request, "Microsoft Connect Test")

        @s.route("/save", POST)
        def save(request: Request):
            ssid = (request.form_data.get("ssid") or "").strip()
            password = request.form_data.get("password") or ""
            if not ssid:
                return Response(request, "<h2>SSID required</h2>", content_type="text/html",
                                status=Status(400, "Bad Request"))
            app.save_wifi(ssid, password)
            host = config.MDNS_HOSTNAME
            body = ("<!DOCTYPE html><html><head><meta charset='UTF-8'>"
                    "<style>body{font-family:Arial;text-align:center;margin-top:50px;"
                    "background:#1a1a2e;color:#fff}</style></head><body>"
                    "<h2>Saved</h2><p>Network: <strong>%s</strong></p>"
                    "<p>The clock is restarting. Then open <a href='http://%s.local'>"
                    "http://%s.local</a></p><p>%s</p></body></html>"
                    % (_esc(ssid), host, host, NAME))
            return Response(request, body, content_type="text/html")
