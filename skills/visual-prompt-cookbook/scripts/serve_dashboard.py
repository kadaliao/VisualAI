from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from cookbook_core import (
    dashboard_paths,
    localize_dashboard_index,
    localize_dashboard_style,
    normalize_dashboard_language,
    read_dashboard_locale,
    record_dashboard_selection,
)


class DashboardHandler(SimpleHTTPRequestHandler):
    dashboard_root: Path
    cookbook_root: Path
    state_dir: Path
    language: str

    def translate_path(self, path: str) -> str:
        clean = unquote(urlparse(path).path)
        if clean in ("", "/"):
            return str(self.dashboard_root / "index.html")
        if clean.startswith("/cookbook/"):
            return str(self.cookbook_root / clean.removeprefix("/cookbook/"))
        return str(self.dashboard_root / clean.lstrip("/"))

    def do_GET(self) -> None:
        route = urlparse(self.path)
        path = route.path
        language = self._request_language(route.query)
        if path == "/api/config":
            self._send_json({"language": self.language})
            return
        if path == "/api/index":
            index = json.loads((self.cookbook_root / "styles-index.json").read_text(encoding="utf-8"))
            self._send_json(localize_dashboard_index(index, language, read_dashboard_locale(language, self.skill_root())))
            return
        if path.startswith("/api/style/"):
            slug = unquote(path.removeprefix("/api/style/"))
            style = json.loads((self.cookbook_root / "styles" / slug / "style.json").read_text(encoding="utf-8"))
            self._send_json(localize_dashboard_style(style, language, read_dashboard_locale(language, self.skill_root())))
            return
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/select":
            self.send_error(404)
            return
        length = int(self.headers.get("content-length", "0"))
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        event = record_dashboard_selection(self.state_dir, payload)
        self._send_json(event)
        self._request_shutdown()

    def _send_json(self, payload: object) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _request_language(self, query: str) -> str:
        values = parse_qs(query).get("language")
        if values:
            return normalize_dashboard_language(values[0])
        return self.language

    def skill_root(self) -> Path:
        return self.dashboard_root.parents[1]

    def _request_shutdown(self) -> None:
        if getattr(self.server, "shutdown_requested", False):
            return
        self.server.shutdown_requested = True
        threading.Thread(target=self.server.shutdown, daemon=True).start()


def build_handler(skill_root: Path, language: str) -> type[DashboardHandler]:
    paths = dashboard_paths(skill_root.resolve())
    return type(
        "ConfiguredDashboardHandler",
        (DashboardHandler,),
        {
            "dashboard_root": paths["dashboard_root"],
            "cookbook_root": paths["cookbook_root"],
            "state_dir": paths["state_dir"],
            "language": language,
        },
    )


def find_available_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/api/config", timeout=0.5) as response:
                return response.status == 200
        except OSError:
            time.sleep(0.1)
    return False


def run_foreground_server(host: str, port: int, skill_root: Path, language: str) -> str:
    handler = build_handler(skill_root, language)
    server = ThreadingHTTPServer((host, port), handler)
    url = f"http://{host}:{server.server_port}"
    print(url, flush=True)
    server.serve_forever()
    return url


def start_background_server(
    *,
    host: str,
    port: int,
    skill_root: Path,
    language: str,
    open_browser: bool,
) -> str:
    selected_port = port or find_available_port(host)
    url = f"http://{host}:{selected_port}"
    state_dir = dashboard_paths(skill_root.resolve())["state_dir"]
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "server.log"
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--host",
        host,
        "--port",
        str(selected_port),
        "--skill-root",
        str(skill_root.resolve()),
        "--language",
        language,
        "--foreground",
        "--no-open",
    ]
    with log_path.open("a", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    (state_dir / "server.pid").write_text(f"{process.pid}\n", encoding="utf-8")
    if not wait_for_server(url):
        exit_status = process.poll()
        detail = f" exited with status {exit_status}" if exit_status is not None else ""
        raise RuntimeError(f"Dashboard server failed to start{detail}; see {log_path}")
    if open_browser:
        webbrowser.open(url)
    print(url, flush=True)
    return url


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Visual Prompt Cookbook dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--language", default=os.environ.get("VISUAL_PROMPT_DASHBOARD_LANGUAGE", "auto"))
    parser.add_argument("--foreground", action="store_true", help="Run the HTTP server in this process.")
    parser.add_argument("--no-open", action="store_true", help="Do not open the dashboard in the default browser.")
    args = parser.parse_args()

    language = normalize_dashboard_language(args.language)
    if args.foreground:
        run_foreground_server(args.host, args.port, args.skill_root.resolve(), language)
        return
    start_background_server(
        host=args.host,
        port=args.port,
        skill_root=args.skill_root.resolve(),
        language=language,
        open_browser=not args.no_open,
    )


if __name__ == "__main__":
    main()
