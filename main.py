from __future__ import annotations

import traceback
from pathlib import Path
from typing import Any

from quart import current_app, jsonify, request

from astrbot.api import AstrBotConfig, logger
from astrbot.api.star import Context, Star
from astrbot.core.config.default import VERSION
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .dashboard_market.installer import InstallError
from .dashboard_market.market import DashboardNotInstallableError, MarketError
from .dashboard_market.service import DEFAULT_MARKET_BASE_URL, DashboardMarketService


PLUGIN_NAME = "astrbot_plugin_dashboard_market"


class DashboardMarketPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig | None = None):
        super().__init__(context)
        self.config = config or {}
        data_dir = Path(get_astrbot_data_path())
        self.service = DashboardMarketService(
            data_dir=data_dir,
            plugin_data_dir=data_dir / "plugin_data" / PLUGIN_NAME,
            current_version=VERSION,
            market_base_url=str(self.config.get("market_base_url") or DEFAULT_MARKET_BASE_URL),
            request_timeout_sec=self._int_config("request_timeout_sec", 30),
            max_backups=self._int_config("max_backups", 5),
            max_artifact_mb=self._int_config("max_artifact_mb", 256),
        )
        context.register_web_api(f"/{PLUGIN_NAME}/market", self.api_market, ["GET"], "List installable dashboards")
        context.register_web_api(f"/{PLUGIN_NAME}/status", self.api_status, ["GET"], "Dashboard market install status")
        context.register_web_api(f"/{PLUGIN_NAME}/install", self.api_install, ["POST"], "Install dashboard from market")
        context.register_web_api(f"/{PLUGIN_NAME}/restore", self.api_restore, ["POST"], "Restore dashboard backup")

    async def api_market(self):
        try:
            return jsonify({"ok": True, "data": await self.service.market()})
        except Exception as exc:
            self._log_exception("Dashboard market fetch failed", exc, stage="market")
            return self._json_error("market_unavailable", str(exc), 502)

    async def api_status(self):
        runtime_path = getattr(current_app, "static_folder", None)
        return jsonify({"ok": True, "data": self.service.status(runtime_path)})

    async def api_install(self):
        stage = "parse_request"
        dashboard_id = ""
        version = ""
        try:
            payload = await self._json_payload()
            dashboard_id = str(payload.get("id") or "").strip()
            version = str(payload.get("version") or "").strip()
            if not dashboard_id or not version:
                return self._json_error("id_and_version_required", "Both id and version are required.", 400)
            stage = "install"
            result = await self.service.install(dashboard_id, version)
            return jsonify({"ok": True, "data": self._with_status(result, "install", dashboard_id, version)})
        except DashboardNotInstallableError as exc:
            self._log_exception(
                "Dashboard install rejected",
                exc,
                stage=stage,
                dashboard_id=dashboard_id,
                version=version,
            )
            return self._json_error("dashboard_not_installable", str(exc), 400)
        except (InstallError, MarketError) as exc:
            self._log_exception(
                "Dashboard install failed",
                exc,
                stage=stage,
                dashboard_id=dashboard_id,
                version=version,
            )
            return self._json_error("install_failed", str(exc), 400)
        except Exception as exc:
            self._log_exception(
                "Unexpected dashboard install failure",
                exc,
                stage=stage,
                dashboard_id=dashboard_id,
                version=version,
            )
            return self._json_error("install_failed", self._exception_message(exc), 500)

    async def api_restore(self):
        stage = "parse_request"
        backup_id = ""
        try:
            payload = await self._json_payload()
            backup_id = str(payload.get("backupId") or "").strip()
            if not backup_id:
                return self._json_error("backup_id_required", "backupId is required.", 400)
            stage = "restore"
            result = self.service.restore(backup_id)
            return jsonify({"ok": True, "data": self._with_status(result, "restore", backup_id=backup_id)})
        except InstallError as exc:
            self._log_exception("Dashboard restore failed", exc, stage=stage, backup_id=backup_id)
            return self._json_error("restore_failed", str(exc), 400)
        except Exception as exc:
            self._log_exception("Unexpected dashboard restore failure", exc, stage=stage, backup_id=backup_id)
            return self._json_error("restore_failed", self._exception_message(exc), 500)

    async def terminate(self):
        pass

    def _int_config(self, key: str, default: int) -> int:
        try:
            value = int(self.config.get(key, default))
        except (TypeError, ValueError):
            return default
        return value if value > 0 else default

    @staticmethod
    async def _json_payload() -> dict[str, Any]:
        payload = await request.get_json(silent=True)
        return payload if isinstance(payload, dict) else {}

    def _with_status(
        self,
        result: dict[str, Any],
        operation: str,
        dashboard_id: str = "",
        version: str = "",
        backup_id: str = "",
    ) -> dict[str, Any]:
        data = dict(result)
        try:
            runtime_path = getattr(current_app, "static_folder", None)
            data["status"] = self.service.status(runtime_path)
        except Exception as exc:
            self._log_exception(
                "Dashboard status collection failed",
                exc,
                stage=f"{operation}_status",
                dashboard_id=dashboard_id,
                version=version,
                backup_id=backup_id,
            )
            data["statusError"] = {
                "error": "status_unavailable",
                "message": self._exception_message(exc),
            }
        return data

    @staticmethod
    def _exception_message(exc: Exception) -> str:
        return str(exc) or repr(exc)

    @classmethod
    def _log_exception(cls, message: str, exc: Exception, *, stage: str, **context: str) -> None:
        context_text = " ".join(f"{key}={value}" for key, value in context.items() if value)
        detail = (
            f"{message}: stage={stage}"
            f"{(' ' + context_text) if context_text else ''}"
            f" exception_type={type(exc).__name__}"
            f" exception_repr={exc!r}"
            f" message={cls._exception_message(exc)}"
        )
        logger.error(detail)
        traceback_text = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)).rstrip()
        if traceback_text:
            for line in traceback_text.splitlines():
                logger.error(f"{message} traceback | {line}")

    @staticmethod
    def _json_error(code: str, message: str, status_code: int):
        response = jsonify(
            {
                "ok": False,
                "status": "error",
                "error": code,
                "message": message or code,
                "httpStatus": status_code,
            }
        )
        response.status_code = 200
        return response
