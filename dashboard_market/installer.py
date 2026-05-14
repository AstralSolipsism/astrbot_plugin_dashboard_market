from __future__ import annotations

import hashlib
import json
import posixpath
import re
import shutil
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class InstallError(Exception):
    """Raised when a dashboard artifact cannot be installed safely."""


class DashboardInstaller:
    def __init__(
        self,
        *,
        data_dir: Path | str,
        plugin_data_dir: Path | str,
        current_version: str,
        max_backups: int,
        max_artifact_bytes: int,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.plugin_data_dir = Path(plugin_data_dir)
        self.current_version = current_version
        self.max_backups = max(1, int(max_backups))
        self.max_artifact_bytes = max(1, int(max_artifact_bytes))
        self.dist_dir = self.data_dir / "dist"
        self.backups_dir = self.plugin_data_dir / "backups"
        self.work_dir = self.plugin_data_dir / "work"
        self.install_state_path = self.plugin_data_dir / "install_state.json"

    def status(self, runtime_dashboard_path: str | None = None) -> dict[str, Any]:
        dist_path = self.dist_dir.resolve(strict=False)
        runtime_path = Path(runtime_dashboard_path).resolve(strict=False) if runtime_dashboard_path else None
        return {
            "astrbotVersion": self.current_version,
            "dist": {
                "path": str(dist_path),
                "exists": self.dist_dir.exists(),
                "version": self._read_dist_version(self.dist_dir),
            },
            "runtime": {
                "dashboardPath": str(runtime_path) if runtime_path else None,
                "usesDataDist": bool(runtime_path and runtime_path == dist_path),
                "requiresRestart": bool(runtime_path and runtime_path != dist_path),
            },
            "installed": self._read_install_state(),
            "backups": self.list_backups(),
        }

    def install_from_artifact(
        self,
        artifact_path: Path | str,
        *,
        dashboard_id: str,
        version: str,
        artifact_url: str,
        sha256: str,
    ) -> dict[str, Any]:
        artifact = Path(artifact_path)
        if not artifact.is_file():
            raise InstallError("artifact_not_found")
        if artifact.stat().st_size > self.max_artifact_bytes:
            raise InstallError("artifact_too_large")
        actual_sha256 = self._sha256_file(artifact)
        if actual_sha256.lower() != sha256.lower():
            raise InstallError("artifact_sha256_mismatch")

        self._ensure_dirs()
        operation_dir = self.work_dir / f"install-{self._safe_timestamp()}-{uuid.uuid4().hex[:8]}"
        extract_dir = operation_dir / "extract"
        staging_dir = operation_dir / "staging"
        previous_dir = operation_dir / "previous-dist"
        backup_meta: dict[str, Any] | None = None
        try:
            extract_dir.mkdir(parents=True)
            self._extract_zip_safely(artifact, extract_dir)
            content_root = self._find_dashboard_root(extract_dir)
            shutil.copytree(content_root, staging_dir)
            if self.dist_dir.exists():
                backup_meta = self._create_backup()
            self._replace_dist(staging_dir, previous_dir)
            state = {
                "dashboard": {"id": dashboard_id, "version": version},
                "artifact": {"url": artifact_url, "sha256": actual_sha256},
                "installedAt": self._now_iso(),
                "astrbotVersion": self.current_version,
                "backup": backup_meta,
            }
            self._write_json(self.install_state_path, state)
            self._prune_backups()
            return {"dashboard": state["dashboard"], "backup": backup_meta}
        except Exception as exc:
            self._rollback_previous(previous_dir)
            if isinstance(exc, InstallError):
                raise
            raise InstallError(str(exc)) from exc
        finally:
            shutil.rmtree(operation_dir, ignore_errors=True)

    def restore_backup(self, backup_id: str) -> dict[str, Any]:
        backup = self._get_backup(backup_id)
        operation_dir = self.work_dir / f"restore-{self._safe_timestamp()}-{uuid.uuid4().hex[:8]}"
        extract_dir = operation_dir / "extract"
        staging_dir = operation_dir / "staging"
        previous_dir = operation_dir / "previous-dist"
        try:
            extract_dir.mkdir(parents=True)
            self._extract_zip_safely(Path(backup["path"]), extract_dir)
            content_root = self._find_dashboard_root(extract_dir)
            shutil.copytree(content_root, staging_dir)
            self._replace_dist(staging_dir, previous_dir)
            state = {
                "restoredBackup": {
                    "id": backup["id"],
                    "sourceVersion": backup.get("sourceVersion"),
                },
                "restoredAt": self._now_iso(),
                "astrbotVersion": self.current_version,
            }
            self._write_json(self.install_state_path, state)
            return state
        except Exception as exc:
            self._rollback_previous(previous_dir)
            if isinstance(exc, InstallError):
                raise
            raise InstallError(str(exc)) from exc
        finally:
            shutil.rmtree(operation_dir, ignore_errors=True)

    def list_backups(self) -> list[dict[str, Any]]:
        if not self.backups_dir.exists():
            return []
        backups: list[dict[str, Any]] = []
        for meta_path in self.backups_dir.glob("*.json"):
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            archive_path = self.backups_dir / f"{meta.get('id', '')}.zip"
            if archive_path.is_file():
                meta["path"] = str(archive_path)
                backups.append(meta)
        return sorted(backups, key=lambda item: item.get("createdAt", ""), reverse=True)

    def _ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.plugin_data_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def _create_backup(self) -> dict[str, Any]:
        backup_id = f"{self._safe_timestamp()}-{uuid.uuid4().hex[:8]}"
        archive_path = self.backups_dir / f"{backup_id}.zip"
        meta_path = self.backups_dir / f"{backup_id}.json"
        source_version = self._read_dist_version(self.dist_dir)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in self.dist_dir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(self.dist_dir).as_posix())
        meta = {
            "id": backup_id,
            "createdAt": self._now_iso(),
            "sourceVersion": source_version,
            "path": str(archive_path),
            "size": archive_path.stat().st_size,
        }
        self._write_json(meta_path, meta)
        return meta

    def _get_backup(self, backup_id: str) -> dict[str, Any]:
        if not re.fullmatch(r"[0-9TZ-]+-[0-9a-f]{8}", backup_id):
            raise InstallError("invalid_backup_id")
        meta_path = self.backups_dir / f"{backup_id}.json"
        archive_path = self.backups_dir / f"{backup_id}.zip"
        if not meta_path.is_file() or not archive_path.is_file():
            raise InstallError("backup_not_found")
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise InstallError("backup_metadata_invalid") from exc
        meta["path"] = str(archive_path)
        return meta

    def _prune_backups(self) -> None:
        for backup in self.list_backups()[self.max_backups :]:
            backup_id = backup.get("id")
            if not backup_id:
                continue
            for suffix in (".zip", ".json"):
                try:
                    (self.backups_dir / f"{backup_id}{suffix}").unlink()
                except FileNotFoundError:
                    pass

    def _replace_dist(self, staging_dir: Path, previous_dir: Path) -> None:
        if previous_dir.exists():
            shutil.rmtree(previous_dir)
        if self.dist_dir.exists():
            self.dist_dir.rename(previous_dir)
        try:
            staging_dir.rename(self.dist_dir)
        except Exception:
            self._rollback_previous(previous_dir)
            raise
        shutil.rmtree(previous_dir, ignore_errors=True)

    def _rollback_previous(self, previous_dir: Path) -> None:
        if not previous_dir.exists():
            return
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir, ignore_errors=True)
        previous_dir.rename(self.dist_dir)

    def _extract_zip_safely(self, archive_path: Path, target_dir: Path) -> None:
        try:
            with zipfile.ZipFile(archive_path) as zf:
                members = zf.infolist()
                if not members:
                    raise InstallError("artifact_zip_empty")
                for member in members:
                    relative_path = self._safe_zip_member_name(member.filename)
                    destination = target_dir / relative_path
                    if member.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, destination.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
        except zipfile.BadZipFile as exc:
            raise InstallError("artifact_zip_invalid") from exc

    @staticmethod
    def _safe_zip_member_name(name: str) -> Path:
        normalized_name = name.replace("\\", "/").strip()
        if not normalized_name:
            raise InstallError("artifact_zip_invalid_path")
        if normalized_name.startswith("/"):
            raise InstallError("artifact_zip_absolute_path")
        parts = [part for part in normalized_name.split("/") if part not in {"", "."}]
        if not parts:
            raise InstallError("artifact_zip_invalid_path")
        if any(":" in part for part in parts):
            raise InstallError("artifact_zip_windows_drive_path")
        normalized = posixpath.normpath("/".join(parts))
        if normalized == ".." or normalized.startswith("../"):
            raise InstallError("artifact_zip_path_traversal")
        return Path(*normalized.split("/"))

    @staticmethod
    def _find_dashboard_root(extract_dir: Path) -> Path:
        if (extract_dir / "index.html").is_file():
            return extract_dir
        child_dirs = [item for item in extract_dir.iterdir() if item.is_dir()]
        child_files = [item for item in extract_dir.iterdir() if item.is_file()]
        if not child_files and len(child_dirs) == 1 and (child_dirs[0] / "index.html").is_file():
            return child_dirs[0]
        raise InstallError("artifact_missing_index_html")

    def _read_install_state(self) -> dict[str, Any] | None:
        if not self.install_state_path.is_file():
            return None
        try:
            return json.loads(self.install_state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    @staticmethod
    def _read_dist_version(dist_dir: Path) -> str | None:
        version_file = dist_dir / "assets" / "version"
        if not version_file.is_file():
            return None
        return version_file.read_text(encoding="utf-8").strip() or None

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def _sha256_file(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _safe_timestamp() -> str:
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
