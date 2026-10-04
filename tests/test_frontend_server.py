"""Browser-only serving must keep files outside its public allowlist private."""

import http.client
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import serve_frontend


class QuietHandler(serve_frontend.FrontendHandler):
    def log_message(self, *args):
        pass


class BrowserOnlyServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        root = Path(cls.directory.name)
        (root / "index.html").write_text("<html>research workspace</html>", encoding="utf-8")
        for document in serve_frontend.DOCUMENTS:
            (root / document).write_text("public documentation", encoding="utf-8")
        (root / "licenses").mkdir()
        (root / "licenses" / "dependency.txt").write_text("dependency license", encoding="utf-8")
        (root / ".env").write_text("OPENAI_API_KEY=secret-static-test", encoding="utf-8")
        (root / "backend").mkdir()
        (root / "backend" / "app.py").write_text("private server implementation", encoding="utf-8")
        cls.root_patch = patch.object(serve_frontend, "ROOT", root)
        cls.root_patch.start()
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=3)
        cls.root_patch.stop()
        cls.directory.cleanup()

    def request(self, path, method="GET"):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            connection.request(method, path)
            response = connection.getresponse()
            return response.status, response.getheaders(), response.read()
        finally:
            connection.close()

    def test_frontend_documentation_and_dependency_licenses_are_reachable(self):
        paths = ["/", "/index.html", "/README.md", "/api/docs/HELP.md", "/licenses/dependency.txt"]
        for path in paths:
            with self.subTest(path=path):
                status, headers, body = self.request(path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
                self.assertEqual(dict(headers)["X-Content-Type-Options"], "nosniff")
                self.assertNotIn(b"secret-static-test", body)

    def test_secret_and_server_paths_are_denied_including_encoded_traversal(self):
        paths = [
            "/.env", "/backend/app.py", "/../.env", "/%2e%2e/.env",
            "/api/docs/../.env", "/api/docs/%2e%2e%2f.env",
            "/licenses/../.env", "/licenses/%2e%2e%2f.env",
            "/licenses/../backend/app.py", "/licenses/nested/dependency.txt",
        ]
        for path in paths:
            with self.subTest(path=path):
                status, _, body = self.request(path)
                self.assertEqual(status, 404)
                self.assertNotIn(b"secret-static-test", body)
                self.assertNotIn(b"private server implementation", body)

    def test_head_returns_headers_without_document_body(self):
        status, headers, body = self.request("/index.html", "HEAD")
        self.assertEqual(status, 200)
        self.assertGreater(int(dict(headers)["Content-Length"]), 0)
        self.assertEqual(body, b"")


if __name__ == "__main__":
    unittest.main()
