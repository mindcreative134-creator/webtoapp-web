import os
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server import main


class HealthEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(main.app)

    def test_healthz(self):
        resp = self.client.get("/healthz")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json().get("ok"))

    def test_readyz(self):
        resp = self.client.get("/readyz")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("apps_writable"))

    def assert_metrics_body(self, resp):
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertIn("distill", body)
        self.assertIn("caches", body)
        self.assertIn("features", body)
        self.assertIn("analyze", body)
        self.assertIn("history", body)
        self.assertIn("android_builds", body)
        self.assertIn("keystores", body)

    def test_metrics_forbidden_for_public_callers_without_token(self):
        # TestClient's source host is "testclient" — i.e. not loopback — so
        # with no METRICS_TOKEN configured the endpoint must refuse.
        with mock.patch.dict(os.environ, {"METRICS_TOKEN": ""}):
            resp = self.client.get("/api/metrics")
        self.assertEqual(resp.status_code, 403)

    def test_metrics_allowed_for_loopback_without_token(self):
        with mock.patch.dict(os.environ, {"METRICS_TOKEN": ""}), \
                mock.patch.object(main, "_client_ip", return_value="127.0.0.1"):
            self.assert_metrics_body(self.client.get("/api/metrics"))

    def test_metrics_accepts_bearer_and_header_token(self):
        with mock.patch.dict(os.environ, {"METRICS_TOKEN": "s3cret"}):
            self.assert_metrics_body(
                self.client.get("/api/metrics", headers={"Authorization": "Bearer s3cret"})
            )
            self.assert_metrics_body(
                self.client.get("/api/metrics", headers={"X-Metrics-Token": "s3cret"})
            )

    def test_metrics_rejects_wrong_token(self):
        with mock.patch.dict(os.environ, {"METRICS_TOKEN": "s3cret"}):
            resp = self.client.get("/api/metrics", headers={"Authorization": "Bearer nope"})
            self.assertEqual(resp.status_code, 403)
            resp = self.client.get("/api/metrics")
            self.assertEqual(resp.status_code, 403)


if __name__ == "__main__":
    unittest.main()
