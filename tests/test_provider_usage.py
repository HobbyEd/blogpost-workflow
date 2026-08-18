"""Tests voor Claude-limieten en Grok-saldo in de verbruiksbalk."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts.orchestrator import provider_usage as usage


def _get(payloads):
    def inner(url, headers):
        for prefix, status, body in payloads:
            if prefix in url:
                return status, body, ""
        return 404, None, "missing"
    return inner


class TestClaudeUsage(unittest.TestCase):
    def test_beschikbaar_is_honderd_minus_gebruikt(self) -> None:
        creds = {
            "claudeAiOauth": {
                "accessToken": "tok",
                "expiresAt": 9_999_999_999_000,
                "subscriptionType": "max",
            }
        }
        http = _get([
            (
                "oauth/usage",
                200,
                {
                    "five_hour": {
                        "utilization": 84.0,
                        "resets_at": "2026-08-18T16:09:59+00:00",
                    },
                    "seven_day": {
                        "utilization": 63.0,
                        "resets_at": "2026-08-20T23:59:59+00:00",
                    },
                },
            )
        ])
        res = usage.fetch_claude_usage(http_get=http, creds=creds)
        self.assertTrue(res["ok"])
        self.assertEqual(res["session"]["available_pct"], 16.0)
        self.assertEqual(res["week"]["available_pct"], 37.0)
        self.assertTrue(res["session"]["resets_at_local"])

    def test_zonder_login_faalt_zacht(self) -> None:
        res = usage.fetch_claude_usage(creds={"claudeAiOauth": {}})
        self.assertFalse(res["ok"])
        self.assertIn("access-token", res["error"])


class TestGrokCredits(unittest.TestCase):
    def test_zonder_management_key_legt_uit(self) -> None:
        http = _get([
            ("/v1/api-key", 200, {"team_id": "team-1"}),
        ])
        res = usage.fetch_grok_credits(
            env={"GROK_API_KEY": "xai-test"},
            http_get=http,
        )
        self.assertFalse(res["ok"])
        self.assertEqual(res["team_id"], "team-1")
        self.assertIn("management", res["error"].lower())

    def test_met_management_key_leest_saldo(self) -> None:
        http = _get([
            ("/v1/api-key", 200, {"team_id": "team-1"}),
            ("prepaid/balance", 200, {"total": {"val": "-4500"}}),
        ])
        res = usage.fetch_grok_credits(
            env={"GROK_API_KEY": "xai-test", "XAI_MANAGEMENT_KEY": "mgmt"},
            http_get=http,
        )
        self.assertTrue(res["ok"], res)
        self.assertEqual(res["remaining_usd"], 45.0)


class TestCollectUsage(unittest.TestCase):
    def test_bundelt_beide(self) -> None:
        creds = {
            "claudeAiOauth": {
                "accessToken": "tok",
                "expiresAt": 9_999_999_999_000,
            }
        }
        http = _get([
            (
                "oauth/usage",
                200,
                {"five_hour": {"utilization": 10.0, "resets_at": None}},
            ),
            ("/v1/api-key", 200, {"team_id": "t"}),
        ])
        res = usage.collect_usage(
            use_cache=False,
            http_get=http,
            claude_creds=creds,
            env={"GROK_API_KEY": "x"},
        )
        self.assertTrue(res["claude"]["ok"])
        self.assertFalse(res["grok"]["ok"])


class TestUsageApi(unittest.TestCase):
    def test_endpoint_geeft_bundel(self) -> None:
        from fastapi.testclient import TestClient
        from server import app

        fake = {
            "ok": True,
            "fetched_at": "2026-08-18T12:00:00+00:00",
            "claude": {"ok": True, "session": {"available_pct": 16}},
            "grok": {"ok": False, "error": "geen key"},
        }
        with patch("scripts.orchestrator.provider_usage.collect_usage", return_value=fake):
            client = TestClient(app)
            res = client.get("/api/usage")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["claude"]["session"]["available_pct"], 16)


if __name__ == "__main__":
    unittest.main()
