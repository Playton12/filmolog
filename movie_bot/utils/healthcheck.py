"""
Простейший HTTP-сервер для health-check на Render.
Запускается в отдельном потоке, отвечает на /health с кодом 200.
"""

import os
import logging
import signal
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Optional


# Настройка логирования
logger = logging.getLogger("healthcheck")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """
    Обработчик HTTP-запросов для health-check.
    Отвечает только на GET /health.
    """

    def do_GET(self):
        if self.path != "/health":
            self.send_error(404, "Not Found")
            return

        logger.info(f"Health-check запрос от {self.client_address[0]}")
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        """Подавляем стандартный лог `http.server`"""
        pass  # Используем наш логгер


class HealthCheckServer:
    """
    Управляемый HTTP-сервер для health-check.
    Запускается в отдельном потоке.
    """

    def __init__(self, port: int = 8000):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
        self.running = False

    def start(self):
        """Запускает сервер в фоновом потоке."""
        if self.running:
            logger.warning("Health-check сервер уже запущен.")
            return

        self.running = True
        server_address = ("", self.port)
        self.server = HTTPServer(server_address, HealthCheckHandler)

        def run():
            logger.info(f"✅ Health-check сервер запущен на порту {self.port}, путь: /health")
            try:
                self.server.serve_forever()
            except Exception as e:
                if self.running:
                    logger.error(f"❌ Ошибка сервера health-check: {e}")

        self.thread = Thread(target=run, daemon=True)
        self.thread.start()

    def stop(self):
        """Останавливает сервер (graceful shutdown)."""
        if self.running and self.server:
            logger.info("🛑 Останавливаю health-check сервер...")
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            logger.info("ℹ️ Health-check сервер остановлен.")


# Глобальный экземпляр
_health_server: Optional[HealthCheckServer] = None


def run_health_server():
    """Запускает health-check сервер. Можно вызывать из main.py."""
    global _health_server
    if _health_server is None:
        port = int(os.getenv("PORT", 8000))
        _health_server = HealthCheckServer(port=port)
        _health_server.start()
    return _health_server


def stop_health_server():
    """Останавливает health-check сервер. Полезно при graceful shutdown бота."""
    global _health_server
    if _health_server:
        _health_server.stop()
        _health_server = None