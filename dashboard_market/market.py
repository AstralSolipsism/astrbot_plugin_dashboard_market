from __future__ import annotations

import asyncio
import json
import ssl
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import aiohttp
import certifi
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version


class DashboardNotInstallableError(Exception):
    """Raised when a market dashboard cannot be installed under strict policy."""


class MarketError(Exception):
    """Raised when the remote dashboard market cannot be reached or parsed."""


def select_installable_dashboard(
    dashboards: list[dict[str, Any]],
    dashboard_id: str,
    version: str,
    current_astrbot_version: str,
) -> dict[str, Any]:
    dashboard = next(
        (
            item
            for item in dashboards
            if str(item.get("id")) == dashboard_id and str(item.get("version")) == version
        ),
        None,
    )
    if not dashboard:
        raise DashboardNotInstallableError("dashboard_not_found")
    if dashboard.get("verification", {}).get("status") != "passed":
        raise DashboardNotInstallableError("dashboard_not_verified")
    compatibility = dashboard.get("compatibility", {})
    if not _is_version_compatible(compatibility.get("astrbot"), current_astrbot_version):
        raise DashboardNotInstallableError("dashboard_not_compatible")
    artifact = dashboard.get("artifact", {})
    if not _artifact_url(dashboard):
        raise DashboardNotInstallableError("dashboard_artifact_url_missing")
    sha256 = artifact.get("sha256")
    if not isinstance(sha256, str) or len(sha256) != 64:
        raise DashboardNotInstallableError("dashboard_artifact_sha256_missing")
    return dashboard


def installable_dashboards(
    dashboards: list[dict[str, Any]],
    current_astrbot_version: str,
) -> list[dict[str, Any]]:
    installable: list[dict[str, Any]] = []
    for dashboard in dashboards:
        try:
            selected = select_installable_dashboard(
                [dashboard],
                str(dashboard.get("id", "")),
                str(dashboard.get("version", "")),
                current_astrbot_version,
            )
        except DashboardNotInstallableError:
            continue
        installable.append(selected)
    return _current_dashboard_versions(installable)


def artifact_url(dashboard: dict[str, Any]) -> str:
    url = _artifact_url(dashboard)
    if not url:
        raise DashboardNotInstallableError("dashboard_artifact_url_missing")
    return url


def _artifact_url(dashboard: dict[str, Any]) -> str | None:
    artifact = dashboard.get("artifact", {})
    for candidate in (artifact.get("preferredUrl"), artifact.get("url")):
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def _is_version_compatible(specifier: Any, current_version: str) -> bool:
    if not isinstance(specifier, str) or not specifier.strip():
        return False
    try:
        spec = SpecifierSet(_normalize_specifier_set(specifier))
        version = Version(current_version.strip().lstrip("vV"))
    except (InvalidSpecifier, InvalidVersion):
        return False
    return spec.contains(version, prereleases=True)


def _current_dashboard_versions(dashboards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for dashboard in dashboards:
        dashboard_id = str(dashboard.get("id", ""))
        if not dashboard_id:
            continue
        current = selected.get(dashboard_id)
        if current is None or _dashboard_sort_key(dashboard) > _dashboard_sort_key(current):
            selected[dashboard_id] = dashboard
    return list(selected.values())


def _dashboard_sort_key(dashboard: dict[str, Any]) -> tuple[float, Version]:
    return (
        _verified_at_timestamp(dashboard.get("verification", {}).get("verifiedAt")),
        _version_key(str(dashboard.get("version", ""))),
    )


def _verified_at_timestamp(value: Any) -> float:
    if not isinstance(value, str) or not value.strip():
        return float("-inf")
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).timestamp()
    except ValueError:
        return float("-inf")


def _version_key(version: str) -> Version:
    try:
        return Version(version.strip().lstrip("vV"))
    except InvalidVersion:
        return Version("0")


def _normalize_specifier_set(specifier: str) -> str:
    raw = specifier.strip()
    if "," in raw:
        return raw
    parts = raw.split()
    if len(parts) <= 1:
        return raw
    return ",".join(parts)


class MarketClient:
    def __init__(self, *, base_url: str, timeout_sec: int) -> None:
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout_sec = max(1, int(timeout_sec))

    async def fetch_installable_dashboards(self) -> dict[str, Any]:
        return await self._get_json(urljoin(self.base_url, "api/dashboards?installable=true"))

    async def download_artifact(self, url: str, target: Path, max_bytes: int) -> None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            raise MarketError("artifact_url_scheme_not_allowed")
        target.parent.mkdir(parents=True, exist_ok=True)
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        timeout = aiohttp.ClientTimeout(total=None, sock_connect=self.timeout_sec, sock_read=self.timeout_sec)
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=timeout,
                trust_env=True,
            ) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise MarketError(f"artifact_download_failed:{response.status}")
                    length = response.headers.get("content-length")
                    if length and int(length) > max_bytes:
                        raise MarketError("artifact_too_large")
                    total = 0
                    with target.open("wb") as handle:
                        async for chunk in response.content.iter_chunked(1024 * 1024):
                            total += len(chunk)
                            if total > max_bytes:
                                raise MarketError("artifact_too_large")
                            handle.write(chunk)
        except asyncio.TimeoutError as exc:
            raise MarketError("artifact_download_timeout") from exc
        except (aiohttp.ClientError, OSError, ValueError) as exc:
            raise MarketError(f"artifact_download_failed:{exc}") from exc

    async def _get_json(self, url: str) -> dict[str, Any]:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        timeout = aiohttp.ClientTimeout(total=self.timeout_sec)
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                timeout=timeout,
                trust_env=True,
            ) as session:
                async with session.get(url, headers={"accept": "application/json"}) as response:
                    if response.status != 200:
                        raise MarketError(f"market_request_failed:{response.status}")
                    text = await response.text()
        except asyncio.TimeoutError as exc:
            raise MarketError("market_request_timeout") from exc
        except aiohttp.ClientError as exc:
            raise MarketError(f"market_request_failed:{exc}") from exc
        try:
            data = json.loads(text.lstrip("\ufeff"))
        except json.JSONDecodeError as exc:
            raise MarketError("market_invalid_json") from exc
        if not isinstance(data, dict):
            raise MarketError("market_invalid_payload")
        return data
