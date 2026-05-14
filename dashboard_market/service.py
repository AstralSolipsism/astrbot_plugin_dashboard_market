from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .installer import DashboardInstaller
from .market import MarketClient, artifact_url, installable_dashboards, select_installable_dashboard


DEFAULT_MARKET_BASE_URL = "https://market.outlune.com"


class DashboardMarketService:
    def __init__(
        self,
        *,
        data_dir: Path | str,
        plugin_data_dir: Path | str,
        current_version: str,
        market_base_url: str = DEFAULT_MARKET_BASE_URL,
        request_timeout_sec: int = 30,
        max_backups: int = 5,
        max_artifact_mb: int = 256,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.plugin_data_dir = Path(plugin_data_dir)
        self.current_version = current_version
        self.market_base_url = market_base_url.rstrip("/")
        self.request_timeout_sec = int(request_timeout_sec)
        self.max_artifact_bytes = int(max_artifact_mb) * 1024 * 1024
        self.cache_path = self.plugin_data_dir / "registry_cache.json"
        self.client = MarketClient(base_url=self.market_base_url, timeout_sec=self.request_timeout_sec)
        self.installer = DashboardInstaller(
            data_dir=self.data_dir,
            plugin_data_dir=self.plugin_data_dir,
            current_version=current_version,
            max_backups=max_backups,
            max_artifact_bytes=self.max_artifact_bytes,
        )

    async def market(self) -> dict[str, Any]:
        payload, cached, error = await self._fetch_market_with_cache()
        dashboards = payload.get("dashboards", [])
        if not isinstance(dashboards, list):
            dashboards = []
        filtered = installable_dashboards(dashboards, self.current_version)
        return {
            "dashboards": filtered,
            "sync": payload.get("sync"),
            "cached": cached,
            "error": error,
            "marketBaseUrl": self.market_base_url,
        }

    async def install(self, dashboard_id: str, version: str) -> dict[str, Any]:
        payload, _, _ = await self._fetch_market_with_cache()
        dashboards = payload.get("dashboards", [])
        if not isinstance(dashboards, list):
            dashboards = []
        dashboard = select_installable_dashboard(
            dashboards,
            dashboard_id,
            version,
            self.current_version,
        )
        url = artifact_url(dashboard)
        artifact = dashboard.get("artifact", {})
        artifact_path = self.installer.work_dir / f"artifact-{uuid.uuid4().hex}.zip"
        try:
            await self.client.download_artifact(url, artifact_path, self.max_artifact_bytes)
            result = self.installer.install_from_artifact(
                artifact_path,
                dashboard_id=dashboard_id,
                version=version,
                artifact_url=url,
                sha256=str(artifact["sha256"]),
            )
        finally:
            try:
                artifact_path.unlink()
            except FileNotFoundError:
                pass
        return {
            **result,
            "activation": {
                "message": "Dashboard installed. Hard-refresh the browser; restart AstrBot if it was started with a custom --webui-dir.",
            },
        }

    def status(self, runtime_dashboard_path: str | None = None) -> dict[str, Any]:
        return self.installer.status(runtime_dashboard_path)

    def restore(self, backup_id: str) -> dict[str, Any]:
        return self.installer.restore_backup(backup_id)

    async def _fetch_and_cache_market(self) -> dict[str, Any]:
        payload = await self.client.fetch_installable_dashboards()
        self._write_json(self.cache_path, payload)
        return payload

    async def _fetch_market_with_cache(self) -> tuple[dict[str, Any], bool, str | None]:
        try:
            return await self._fetch_and_cache_market(), False, None
        except Exception as exc:
            payload = self._read_cache()
            if payload is None:
                raise
            return payload, True, str(exc)

    def _read_cache(self) -> dict[str, Any] | None:
        if not self.cache_path.is_file():
            return None
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return payload if isinstance(payload, dict) else None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
