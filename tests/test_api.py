"""Validate API boundaries without depending on public services or an API key."""

import os
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app import app


class APIBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.environment = patch.dict(os.environ, {"OPENAI_API_KEY": ""})
        self.environment.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)
        self.environment.stop()

    def test_health_is_available_without_openai_credentials(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)

    def test_standalone_local_origins_support_health_preflight_and_ai_check(self):
        origins = [
            "http://127.0.0.1:8765", "http://localhost:8775", "http://127.0.0.1:63514",
            "http://localhost:1", "http://127.0.0.1:65535", "http://localhost", "http://127.0.0.1",
            "http://127.0.0.1:8000", "http://localhost:8080",
        ]
        for origin in origins:
            with self.subTest(origin=origin):
                response = self.client.get("/api/health", headers={"Origin": origin})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
                response = self.client.options("/api/ai/check", headers={
                    "Origin": origin, "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                })
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
                with patch("backend.app.ai.check_connection", new=AsyncMock(return_value={"ok": True})) as check:
                    response = self.client.post("/api/ai/check", json={}, headers={"Origin": origin})
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.headers.get("access-control-allow-origin"), origin)
                check.assert_awaited_once()

    def test_untrusted_and_file_origins_cannot_access_ai(self):
        origins = [
            "null", "https://localhost:8765", "https://127.0.0.1:8765", "https://example.com",
            "http://example.com", "http://192.168.1.2:8765", "http://localhost.evil.example:8765",
            "http://127.0.0.1.evil.example:8765", "http://localhost@evil.example:8765",
            "http://user@localhost:8765", "http://localhost:0", "http://localhost:65536",
            "http://127.0.0.1:100000", "http://localhost:8765/", "http://localhost:8765?query",
            "http://localhost:8765#fragment", "http://localhost:", "http://localhost:08765", "",
        ]
        for origin in origins:
            with self.subTest(origin=origin):
                response = self.client.get("/api/health", headers={"Origin": origin})
                self.assertNotIn("access-control-allow-origin", response.headers)
                response = self.client.options("/api/ai/check", headers={
                    "Origin": origin, "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                })
                self.assertEqual(response.status_code, 400, response.text)
                self.assertNotIn("access-control-allow-origin", response.headers)
                with patch("backend.app.ai.check_connection", new=AsyncMock()) as check:
                    response = self.client.post("/api/ai/check", json={}, headers={"Origin": origin})
                self.assertEqual(response.status_code, 403, response.text)
                self.assertIn("serve_frontend.py", response.json()["detail"])
                check.assert_not_awaited()

    def test_ai_check_without_origin_remains_available_to_local_clients(self):
        with patch("backend.app.ai.check_connection", new=AsyncMock(return_value={"ok": True})) as check:
            response = self.client.post("/api/ai/check", json={})
        self.assertEqual(response.status_code, 200, response.text)
        check.assert_awaited_once()

    def test_invalid_search_never_reaches_a_public_source(self):
        invalid_requests = [
            {"query": "", "mode": "topic", "sources": ["pubmed"]},
            {"query": "a" * 5001, "mode": "topic", "sources": ["pubmed"]},
            {"query": "ovarian aging", "mode": "unsupported", "sources": ["pubmed"]},
            {"query": "ovarian aging", "mode": "topic", "sources": ["arbitrary-source"]},
            {"query": "ovarian aging", "mode": "topic", "sources": ["pubmed"], "limit": -1},
        ]
        for payload in invalid_requests:
            with self.subTest(payload=payload):
                response = self.client.post("/api/search", json=payload)
                self.assertEqual(response.status_code, 422, response.text)

    def test_static_routes_do_not_expose_server_or_environment_files(self):
        paths = [
            "/.env", "/.git/config", "/backend/app.py", "/backend/ai.py",
            "/help/../.env", "/help/%2e%2e/.env", "/help/%2e%2e%2f.env",
        ]
        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 404, response.text)

    def test_health_never_returns_a_configured_key(self):
        fake_secret = "sk-contract-test-must-not-leak"
        with patch.dict(os.environ, {"OPENAI_API_KEY": fake_secret}):
            response = self.client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(fake_secret, response.text)

    def test_missing_ai_key_returns_actionable_error_without_network(self):
        response = self.client.post("/api/ai", json={
            "action": "explain", "query": "ovarian aging", "records": [{
                "id": "pubmed:123456", "source": "pubmed", "type": "publication",
                "title": "Fixture publication", "url": "https://pubmed.ncbi.nlm.nih.gov/123456/",
            }],
        })
        self.assertEqual(response.status_code, 503, response.text)
        self.assertIn("OPENAI_API_KEY", response.json()["detail"])

    def test_one_failed_source_keeps_successful_evidence_and_failure_coverage(self):
        async def retrieve(source, interpretation, limit):
            if source == "pubmed":
                return {"records": [{"id": "pubmed:123456", "title": "Retrieved publication"}],
                        "coverage": {"source": source, "status": "ok", "total": 1, "retrieved": 1}}
            return {"records": [], "coverage": {"source": source, "status": "error", "total": None, "retrieved": 0, "error": "Fixture timeout"}}
        with patch.object(app.state.sources, "search", new=AsyncMock(side_effect=retrieve)):
            response = self.client.post("/api/search", json={"query": "ovarian aging", "mode": "topic", "sources": ["pubmed", "gwas"]})
        self.assertEqual(response.status_code, 200, response.text)
        result = response.json()
        self.assertEqual([record["id"] for record in result["records"]], ["pubmed:123456"])
        self.assertEqual([coverage["status"] for coverage in result["coverage"]], ["ok", "error"])
        self.assertFalse(result["demo"])

    def test_validation_does_not_echo_accidentally_pasted_key(self):
        secret = "sk-accidentally-pasted-credential"
        response = self.client.post("/api/search", json={"query": "topic", "sources": [secret]})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(secret, response.text)


if __name__ == "__main__":
    unittest.main()
