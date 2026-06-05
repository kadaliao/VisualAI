from __future__ import annotations

import argparse
import json
import os
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the Visual Prompt Cookbook dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--skill-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--language", default=os.environ.get("VISUAL_PROMPT_DASHBOARD_LANGUAGE", "auto"))
    args = parser.parse_args()

    paths = dashboard_paths(args.skill_root.resolve())
    language = normalize_dashboard_language(args.language)
    handler = type(
        "ConfiguredDashboardHandler",
        (DashboardHandler,),
        {
            "dashboard_root": paths["dashboard_root"],
            "cookbook_root": paths["cookbook_root"],
            "state_dir": paths["state_dir"],
            "language": language,
        },
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{server.server_port}"
    print(url, flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
