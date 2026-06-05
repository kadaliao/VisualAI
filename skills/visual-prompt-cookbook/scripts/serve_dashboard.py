from __future__ import annotations

import argparse
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from cookbook_core import dashboard_paths, record_dashboard_selection


class DashboardHandler(SimpleHTTPRequestHandler):
    dashboard_root: Path
    cookbook_root: Path
    state_dir: Path

    def translate_path(self, path: str) -> str:
        clean = unquote(path.split("?", 1)[0].split("#", 1)[0])
        if clean in ("", "/"):
            return str(self.dashboard_root / "index.html")
        if clean.startswith("/cookbook/"):
            return str(self.cookbook_root / clean.removeprefix("/cookbook/"))
        return str(self.dashboard_root / clean.lstrip("/"))

    def do_GET(self) -> None:
        if self.path == "/api/index":
            self._send_json(json.loads((self.cookbook_root / "styles-index.json").read_text(encoding="utf-8")))
            return
        if self.path.startswith("/api/style/"):
            slug = unquote(self.path.removeprefix("/api/style/"))
            self._send_json(json.loads((self.cookbook_root / "styles" / slug / "style.json").read_text(encoding="utf-8")))
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

    def _send_json(self, payload: object) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Visual Prompt Cookbook dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    paths = dashboard_paths(args.skill_root.resolve())
    handler = type(
        "ConfiguredDashboardHandler",
        (DashboardHandler,),
        {
            "dashboard_root": paths["dashboard_root"],
            "cookbook_root": paths["cookbook_root"],
            "state_dir": paths["state_dir"],
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{server.server_port}"
    print(url, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
