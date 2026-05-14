import hashlib
import asyncio
import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from dashboard_market.installer import DashboardInstaller, InstallError
from dashboard_market.market import DashboardNotInstallableError, MarketError, select_installable_dashboard
from dashboard_market.service import DashboardMarketService


class DashboardInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data_dir = self.root / "data"
        self.data_dir.mkdir()
        self.plugin_data_dir = self.root / "plugin_data" / "astrbot_plugin_dashboard_market"
        self.dist_dir = self.data_dir / "dist"
        (self.dist_dir / "assets").mkdir(parents=True)
        (self.dist_dir / "index.html").write_text("old dashboard", encoding="utf-8")
        (self.dist_dir / "assets" / "version").write_text("old@1.0.0", encoding="utf-8")
        self.installer = DashboardInstaller(
            data_dir=self.data_dir,
            plugin_data_dir=self.plugin_data_dir,
            current_version="4.24.2",
            max_backups=2,
            max_artifact_bytes=10 * 1024 * 1024,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_zip_path_traversal(self):
        archive = self._zip({"../escape.txt": "bad", "index.html": "ok"})

        with self.assertRaises(InstallError):
            self.installer.install_from_artifact(
                archive,
                dashboard_id="demo",
                version="1.0.0",
                artifact_url="https://market.example/demo.zip",
                sha256=self._sha256(archive),
            )

        self.assertEqual((self.dist_dir / "index.html").read_text(encoding="utf-8"), "old dashboard")
        self.assertFalse((self.root / "escape.txt").exists())

    def test_rejects_absolute_and_windows_drive_paths(self):
        for name in ["/absolute.txt", "C:/absolute.txt", "nested/C:/bad.txt"]:
            with self.subTest(name=name):
                archive = self._zip({name: "bad", "index.html": "ok"})
                with self.assertRaises(InstallError):
                    self.installer.install_from_artifact(
                        archive,
                        dashboard_id="demo",
                        version="1.0.0",
                        artifact_url="https://market.example/demo.zip",
                        sha256=self._sha256(archive),
                    )

        self.assertEqual((self.dist_dir / "assets" / "version").read_text(encoding="utf-8"), "old@1.0.0")

    def test_sha256_mismatch_does_not_replace_dist(self):
        archive = self._zip({"index.html": "new dashboard", "assets/version": "demo@1.0.0"})

        with self.assertRaises(InstallError):
            self.installer.install_from_artifact(
                archive,
                dashboard_id="demo",
                version="1.0.0",
                artifact_url="https://market.example/demo.zip",
                sha256="0" * 64,
            )

        self.assertEqual((self.dist_dir / "index.html").read_text(encoding="utf-8"), "old dashboard")
        self.assertFalse((self.plugin_data_dir / "install_state.json").exists())

    def test_installs_root_zip_with_backup_and_state(self):
        archive = self._zip({"index.html": "new dashboard", "assets/version": "demo@1.0.0"})

        result = self.installer.install_from_artifact(
            archive,
            dashboard_id="demo",
            version="1.0.0",
            artifact_url="https://market.example/demo.zip",
            sha256=self._sha256(archive),
        )

        self.assertEqual(result["dashboard"]["id"], "demo")
        self.assertEqual((self.dist_dir / "index.html").read_text(encoding="utf-8"), "new dashboard")
        self.assertEqual((self.dist_dir / "assets" / "version").read_text(encoding="utf-8"), "demo@1.0.0")
        backups = self.installer.list_backups()
        self.assertEqual(len(backups), 1)
        self.assertEqual(backups[0]["sourceVersion"], "old@1.0.0")
        state = json.loads((self.plugin_data_dir / "install_state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["dashboard"]["id"], "demo")
        self.assertEqual(state["artifact"]["sha256"], self._sha256(archive))

    def test_installs_single_top_level_directory_zip(self):
        archive = self._zip({"dist/index.html": "wrapped dashboard", "dist/assets/version": "demo@1.0.0"})

        self.installer.install_from_artifact(
            archive,
            dashboard_id="demo",
            version="1.0.0",
            artifact_url="https://market.example/demo.zip",
            sha256=self._sha256(archive),
        )

        self.assertEqual((self.dist_dir / "index.html").read_text(encoding="utf-8"), "wrapped dashboard")
        self.assertFalse((self.dist_dir / "dist").exists())

    def test_missing_index_rolls_back_current_dashboard(self):
        archive = self._zip({"assets/version": "broken@1.0.0"})

        with self.assertRaises(InstallError):
            self.installer.install_from_artifact(
                archive,
                dashboard_id="broken",
                version="1.0.0",
                artifact_url="https://market.example/broken.zip",
                sha256=self._sha256(archive),
            )

        self.assertEqual((self.dist_dir / "index.html").read_text(encoding="utf-8"), "old dashboard")
        self.assertEqual((self.dist_dir / "assets" / "version").read_text(encoding="utf-8"), "old@1.0.0")

    def test_restore_backup_replaces_current_dist(self):
        archive = self._zip({"index.html": "new dashboard", "assets/version": "demo@1.0.0"})
        self.installer.install_from_artifact(
            archive,
            dashboard_id="demo",
            version="1.0.0",
            artifact_url="https://market.example/demo.zip",
            sha256=self._sha256(archive),
        )
        backup_id = self.installer.list_backups()[0]["id"]

        result = self.installer.restore_backup(backup_id)

        self.assertEqual(result["restoredBackup"]["id"], backup_id)
        self.assertEqual((self.dist_dir / "index.html").read_text(encoding="utf-8"), "old dashboard")
        self.assertEqual((self.dist_dir / "assets" / "version").read_text(encoding="utf-8"), "old@1.0.0")

    def _zip(self, files):
        archive = self.root / f"artifact-{len(list(self.root.glob('artifact-*.zip')))}.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return archive

    @staticmethod
    def _sha256(path):
        h = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()


class MarketSelectionTests(unittest.TestCase):
    def test_selects_passed_compatible_dashboard(self):
        dashboard = _dashboard("demo", "1.0.0", "passed", ">=4.24.2 <4.25.0")

        selected = select_installable_dashboard([dashboard], "demo", "1.0.0", "4.24.2")

        self.assertEqual(selected["id"], "demo")

    def test_rejects_failed_dashboard(self):
        with self.assertRaises(DashboardNotInstallableError):
            select_installable_dashboard(
                [_dashboard("demo", "1.0.0", "failed", ">=4.24.2 <4.25.0")],
                "demo",
                "1.0.0",
                "4.24.2",
            )

    def test_rejects_incompatible_dashboard(self):
        with self.assertRaises(DashboardNotInstallableError):
            select_installable_dashboard(
                [_dashboard("demo", "1.0.0", "passed", ">=4.25.0 <4.26.0")],
                "demo",
                "1.0.0",
                "4.24.2",
            )

    def test_rejects_dashboard_without_artifact_url(self):
        dashboard = _dashboard("demo", "1.0.0", "passed", ">=4.24.2 <4.25.0")
        dashboard["artifact"].pop("url")

        with self.assertRaises(DashboardNotInstallableError):
            select_installable_dashboard([dashboard], "demo", "1.0.0", "4.24.2")


class DashboardMarketServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.data_dir = self.root / "data"
        self.plugin_data_dir = self.root / "plugin_data" / "astrbot_plugin_dashboard_market"
        self.artifact = self._zip({"index.html": "new dashboard", "assets/version": "demo@1.0.0"})
        self.sha256 = DashboardInstallerTests._sha256(self.artifact)
        self.service = DashboardMarketService(
            data_dir=self.data_dir,
            plugin_data_dir=self.plugin_data_dir,
            current_version="4.24.2",
            market_base_url="https://market.example",
            max_backups=2,
            max_artifact_mb=10,
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_install_uses_cached_registry_when_live_fetch_fails(self):
        self.service._write_json(
            self.service.cache_path,
            {"dashboards": [_dashboard("demo", "1.0.0", "passed", ">=4.24.2 <4.25.0", sha256=self.sha256)]},
        )
        self.service.client = _FailingDownloadCapableMarketClient(self.artifact)

        result = asyncio.run(self.service.install("demo", "1.0.0"))

        self.assertEqual(result["dashboard"], {"id": "demo", "version": "1.0.0"})
        self.assertEqual((self.data_dir / "dist" / "index.html").read_text(encoding="utf-8"), "new dashboard")

    def test_install_live_fetch_failure_without_cache_stays_market_error(self):
        self.service.client = _FailingDownloadCapableMarketClient(self.artifact)

        with self.assertRaises(MarketError) as caught:
            asyncio.run(self.service.install("demo", "1.0.0"))

        self.assertIn("market_request_failed:test", str(caught.exception))

    def _zip(self, files):
        archive = self.root / "service-artifact.zip"
        with zipfile.ZipFile(archive, "w") as zf:
            for name, content in files.items():
                zf.writestr(name, content)
        return archive


class _FailingDownloadCapableMarketClient:
    def __init__(self, artifact: Path):
        self.artifact = artifact

    async def fetch_installable_dashboards(self):
        raise MarketError("market_request_failed:test")

    async def download_artifact(self, url, target, max_bytes):
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.artifact, target)


def _dashboard(dashboard_id, version, status, astrbot_range, sha256="a" * 64):
    return {
        "id": dashboard_id,
        "version": version,
        "project": {
            "name": "Demo Dashboard",
            "description": "Demo",
            "authors": [{"name": "Tester"}],
            "tags": ["demo"],
        },
        "artifact": {
            "url": "https://market.example/demo.zip",
            "sha256": sha256,
        },
        "compatibility": {
            "astrbot": astrbot_range,
            "contract": "astrbot-dashboard-contract@v4.24.2",
        },
        "verification": {"status": status},
        "media": {"effectiveScreenshots": [], "screenshots": []},
    }
