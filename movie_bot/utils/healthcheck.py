"""
Простейший HTTP-сервер для health-check на Render.
"""

import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK")


def run_server():
    """Запускает HTTP-сервер на порту из переменной PORT."""
    port = int(os.getenv("PORT", 8000))
    server_address = ("", port)
    httpd = HTTPServer(server_address, HealthCheckHandler)
    print(f"🌍 Health-check сервер запущен на порту {port}")
    httpd.serve_forever()