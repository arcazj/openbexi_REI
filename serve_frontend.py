"""Serve the standalone frontend and explicit documentation without exposing .env."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent
DOCUMENTS = {
    "README.md", "HELP.md", "COMMERCIAL_LICENSING.md",
    "THIRD_PARTY_NOTICES.md", "REI_RESEARCH_EXPLORER_PROMPT.md",
}


class FrontendHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._serve(send_body=True)

    def do_HEAD(self):
        self._serve(send_body=False)

    def _serve(self, send_body):
        route = unquote(urlsplit(self.path).path)
        file_path = None
        media_type = "text/plain; charset=utf-8"
        if route in {"/", "/index.html"}:
            file_path = ROOT / "index.html"
            media_type = "text/html; charset=utf-8"
        elif route.lstrip("/") in DOCUMENTS and route.count("/") == 1:
            file_path = ROOT / route[1:]
        elif route.startswith("/api/docs/") and route[10:] in DOCUMENTS:
            file_path = ROOT / route[10:]
        elif route.startswith("/licenses/"):
            name = route[10:]
            license_root = (ROOT / "licenses").resolve()
            candidate = (license_root / name).resolve()
            if candidate.parent == license_root and candidate.suffix == ".txt" and candidate.is_file():
                file_path = candidate
        if file_path is None or not file_path.is_file():
            self.send_error(404, "Resource not available")
            return
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", media_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if send_body:
            self.wfile.write(content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("port must be between 1 and 65535")
    server = ThreadingHTTPServer(("127.0.0.1", args.port), FrontendHandler)
    print("Frontend: http://127.0.0.1:" + str(args.port), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
