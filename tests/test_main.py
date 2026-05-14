import asyncio
import importlib
import sys
import types
import unittest
from pathlib import Path


def _install_import_stubs():
    if "quart" not in sys.modules:
        quart = types.ModuleType("quart")
        quart.current_app = types.SimpleNamespace(static_folder="runtime-dist")
        quart.request = types.SimpleNamespace(get_json=lambda silent=True: {})

        def jsonify(payload):
            return _FakeJsonResponse(payload)

        quart.jsonify = jsonify
        sys.modules["quart"] = quart

    if "astrbot" not in sys.modules:
        astrbot = types.ModuleType("astrbot")
        sys.modules["astrbot"] = astrbot

    api = types.ModuleType("astrbot.api")
    api.AstrBotConfig = dict
    api.logger = _FakeLogger()
    sys.modules["astrbot.api"] = api

    star = types.ModuleType("astrbot.api.star")

    class Star:
        def __init__(self, context):
            self.context = context

    star.Context = object
    star.Star = Star
    sys.modules["astrbot.api.star"] = star

    default = types.ModuleType("astrbot.core.config.default")
    default.VERSION = "4.24.2"
    sys.modules["astrbot.core.config.default"] = default

    path_module = types.ModuleType("astrbot.core.utils.astrbot_path")
    path_module.get_astrbot_data_path = lambda: str(Path.cwd())
    sys.modules["astrbot.core.utils.astrbot_path"] = path_module

    for name in [
        "astrbot.core",
        "astrbot.core.config",
        "astrbot.core.utils",
    ]:
        sys.modules.setdefault(name, types.ModuleType(name))


class _FakeJsonResponse(dict):
    status_code = 200


class _FakeLogger:
    def __init__(self):
        self.messages = []

    def error(self, message, *args, **kwargs):
        self.messages.append(str(message))


_install_import_stubs()
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
market_module = importlib.import_module("astrbot_plugin_dashboard_market.dashboard_market.market")
plugin_main = importlib.import_module("astrbot_plugin_dashboard_market.main")


class DashboardMarketPluginHandlerTests(unittest.TestCase):
    def test_install_status_failure_returns_install_result_without_http_500(self):
        plugin = plugin_main.DashboardMarketPlugin.__new__(plugin_main.DashboardMarketPlugin)
        plugin.service = _StatusFailingInstallService()
        plugin._json_payload = _async_payload({"id": "demo", "version": "1.0.0"})

        response = asyncio.run(plugin.api_install())

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["ok"])
        self.assertEqual(response["data"]["dashboard"], {"id": "demo", "version": "1.0.0"})
        self.assertEqual(response["data"]["statusError"]["error"], "status_unavailable")
        self.assertIn("status failed", response["data"]["statusError"]["message"])

    def test_install_unexpected_exception_returns_bridge_error_without_http_500(self):
        plugin = plugin_main.DashboardMarketPlugin.__new__(plugin_main.DashboardMarketPlugin)
        plugin.service = _UnexpectedInstallFailureService()
        plugin._json_payload = _async_payload({"id": "demo", "version": "1.0.0"})

        response = asyncio.run(plugin.api_install())

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response["ok"])
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error"], "install_failed")
        self.assertEqual(response["httpStatus"], 500)
        self.assertIn("install exploded", response["message"])


class DashboardMarketSelectionTests(unittest.TestCase):
    def test_installable_dashboards_keeps_latest_published_version_per_id(self):
        dashboards = [
            _dashboard("demo", "0.1.0", "2026-05-13T12:42:50.430Z"),
            _dashboard("demo", "0.1.1", "2026-05-14T09:08:17.381Z"),
            _dashboard("other", "1.0.0", "2026-05-12T00:00:00.000Z"),
        ]

        result = market_module.installable_dashboards(dashboards, "4.24.2")

        self.assertEqual(
            [(dashboard["id"], dashboard["version"]) for dashboard in result],
            [("demo", "0.1.1"), ("other", "1.0.0")],
        )

    def test_select_installable_dashboard_stays_exact_by_id_and_version(self):
        dashboards = [
            _dashboard("demo", "0.1.0", "2026-05-13T12:42:50.430Z"),
            _dashboard("demo", "0.1.1", "2026-05-14T09:08:17.381Z"),
        ]

        selected = market_module.select_installable_dashboard(dashboards, "demo", "0.1.0", "4.24.2")

        self.assertEqual(selected["version"], "0.1.0")


def _async_payload(payload):
    async def inner():
        return payload

    return inner


class _StatusFailingInstallService:
    async def install(self, dashboard_id, version):
        return {"dashboard": {"id": dashboard_id, "version": version}}

    def status(self, runtime_dashboard_path=None):
        raise RuntimeError("status failed")


class _UnexpectedInstallFailureService:
    async def install(self, dashboard_id, version):
        raise RuntimeError("install exploded")


def _dashboard(dashboard_id, version, verified_at):
    return {
        "id": dashboard_id,
        "version": version,
        "verification": {
            "status": "passed",
            "verifiedAt": verified_at,
        },
        "compatibility": {
            "astrbot": ">=4.24.2 <4.25.0",
        },
        "artifact": {
            "url": f"https://example.com/{dashboard_id}-{version}.zip",
            "sha256": "a" * 64,
        },
    }


if __name__ == "__main__":
    unittest.main()
