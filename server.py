#!/usr/bin/env python3
"""Serveur local — sert le rapport HTML et permet le rafraîchissement des données."""

import json
import subprocess
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

DIR = Path(__file__).parent
REPORT_PATH = DIR / "report.html"
PORT = 8080

_refreshing = False
_refresh_lock = threading.Lock()


def _run_refresh():
    global _refreshing
    try:
        subprocess.run([sys.executable, str(DIR / "generate_report.py")], cwd=str(DIR))
    finally:
        _refreshing = False


SPINNER_PAGE = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Rafraîchissement…</title>
  <style>
    body { margin:0; background:#040d18; color:#dde8f2;
           font-family:-apple-system,sans-serif;
           display:flex; flex-direction:column; align-items:center;
           justify-content:center; height:100vh; gap:24px; }
    .spinner { width:56px; height:56px; border:4px solid rgba(255,255,255,0.1);
               border-top-color:#facc15; border-radius:50%;
               animation:spin 0.9s linear infinite; }
    @keyframes spin { to { transform:rotate(360deg); } }
    p { font-size:16px; color:rgba(255,255,255,0.5); }
  </style>
</head>
<body>
  <div class="spinner"></div>
  <p>Rafraîchissement en cours…</p>
  <script>
    var mtime = MTIME_PLACEHOLDER;
    setInterval(function() {
      fetch('/status').then(function(r){ return r.json(); }).then(function(d){
        if (!d.refreshing && d.mtime > mtime) {
          window.location.href = '/';
        }
      }).catch(function(){});
    }, 1500);
  </script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _refreshing

        if self.path.startswith("/refresh"):
            with _refresh_lock:
                if not _refreshing:
                    _refreshing = True
                    threading.Thread(target=_run_refresh, daemon=True).start()
            mtime = REPORT_PATH.stat().st_mtime if REPORT_PATH.exists() else 0
            page = SPINNER_PAGE.replace("MTIME_PLACEHOLDER", str(mtime))
            body = page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        elif self.path.startswith("/status"):
            mtime = REPORT_PATH.stat().st_mtime if REPORT_PATH.exists() else 0
            data = json.dumps({"refreshing": _refreshing, "mtime": mtime}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        else:
            try:
                content = REPORT_PATH.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Rapport introuvable. Lancez generate_report.py d'abord.")

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    import socket
    local_ip = socket.gethostbyname(socket.gethostname())
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Serveur démarré → http://localhost:{PORT}")
    print(f"Réseau local     → http://{local_ip}:{PORT}")
    print("Ctrl+C pour arrêter")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServeur arrêté.")
