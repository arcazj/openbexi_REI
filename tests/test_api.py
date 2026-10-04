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
