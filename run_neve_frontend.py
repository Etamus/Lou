"""Launcher that starts the Neve web backend and opens the UI in a desktop window."""

from __future__ import annotations

import contextlib
import importlib.util
import threading
import time
from pathlib import Path
import sys
import types

from PySide6.QtCore import QUrl, Qt, QSize
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication


def _load_backend_module():
    backend_root = Path(__file__).resolve().parent / "neve-frontend" / "backend"
    module_path = backend_root / "server.py"

    package_name = "backend"
    if package_name not in sys.modules:
        package = types.ModuleType(package_name)
        package.__path__ = [str(backend_root)]
        sys.modules[package_name] = package

    spec = importlib.util.spec_from_file_location(f"{package_name}.server", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Nao foi possivel carregar o backend do Neve")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


backend_module = _load_backend_module()
DEFAULT_HOST = backend_module.DEFAULT_HOST
DEFAULT_PORT = backend_module.DEFAULT_PORT
create_server = backend_module.create_server


def start_backend() -> tuple[threading.Thread, object]:
    server = create_server(DEFAULT_HOST, DEFAULT_PORT)
    thread = threading.Thread(target=server.serve_forever, name="neve-backend", daemon=True)
    thread.start()
    time.sleep(0.15)
    return thread, server


def stop_backend(thread: threading.Thread, server: object) -> None:
    with contextlib.suppress(Exception):
        server.shutdown()
        server.server_close()
    thread.join(timeout=1)


def create_window() -> QWebEngineView:
    view = QWebEngineView()
    view.setWindowTitle("Neve Frontend")
    fixed_size = QSize(1280, 760)
    view.setMinimumSize(fixed_size)
    view.setMaximumSize(fixed_size)
    view.setStyleSheet("background: #0f1115;")
    view.setUrl(QUrl(f"http://{DEFAULT_HOST}:{DEFAULT_PORT}"))
    return view


def main() -> int:
    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
    app = QApplication(sys.argv)
    backend_thread, backend = start_backend()
    window = create_window()
    window.show()

    exit_code = app.exec()
    stop_backend(backend_thread, backend)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
