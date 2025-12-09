from __future__ import annotations

import json
import logging
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from passlib.context import CryptContext

try:
    import bcrypt as bcrypt_module
except ImportError:  # pragma: no cover - bcrypt installed via requirements
    bcrypt_module = None

BACKEND_DIR = Path(__file__).resolve().parent
DATA_DIR = BACKEND_DIR / "data"
USERS_FILE = DATA_DIR / "users.json"
REGISTRATIONS_FILE = DATA_DIR / "registrations.json"

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _patch_bcrypt_backend() -> None:
    """Force bcrypt>=5 to mimic legacy behavior expected by passlib."""
    if not bcrypt_module:
        return
    if getattr(bcrypt_module, "_passlib_patch_applied", False):
        return

    about_version = getattr(bcrypt_module, "__version__", "unknown")

    class _About:
        __version__ = about_version

    if not hasattr(bcrypt_module, "__about__"):
        bcrypt_module.__about__ = _About()  # type: ignore[attr-defined]

    original_hashpw = bcrypt_module.hashpw

    def _safe_hashpw(password: bytes, salt: bytes) -> bytes:
        try:
            return original_hashpw(password, salt)
        except ValueError as exc:
            message = str(exc)
            if "password cannot be longer than 72 bytes" in message:
                logger.warning(
                    "bcrypt backend rejected >72 byte secret; truncating to keep compatibility (consider pinning bcrypt<5)."
                )
                return original_hashpw(password[:72], salt)
            raise

    bcrypt_module.hashpw = _safe_hashpw  # type: ignore[assignment]
    bcrypt_module._passlib_patch_applied = True  # type: ignore[attr-defined]


_patch_bcrypt_backend()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AuthManager:
    """File-based user & registration store with bcrypt hashing."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._users: Dict[str, Dict[str, Any]] = {}
        self._registrations: Dict[str, Dict[str, Any]] = {}
        self._load_state()
        self._ensure_root_user()

    # ------------------------
    # Persistence helpers
    # ------------------------
    def _load_state(self) -> None:
        self._users = self._load_records(USERS_FILE, key="user_id")
        self._registrations = self._load_records(REGISTRATIONS_FILE, key="request_id")

    def _load_records(self, path: Path, key: str) -> Dict[str, Dict[str, Any]]:
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as fp:
                payload = json.load(fp)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load %s: %s", path.name, exc)
            return {}

        records: Dict[str, Dict[str, Any]] = {}
        if isinstance(payload, list):
            source_iterable = payload
        elif isinstance(payload, dict):
            source_iterable = payload.values()
        else:
            return {}

        for item in source_iterable:
            if not isinstance(item, dict):
                continue
            record_key = item.get(key)
            if isinstance(record_key, str) and record_key:
                records[record_key] = item
        return records

    def _persist_users(self) -> None:
        self._persist_records(USERS_FILE, self._users.values())

    def _persist_registrations(self) -> None:
        self._persist_records(REGISTRATIONS_FILE, self._registrations.values())

    def _persist_records(self, path: Path, values) -> None:  # type: ignore[no-untyped-def]
        tmp_path = path.with_suffix(".tmp")
        try:
            with tmp_path.open("w", encoding="utf-8") as fp:
                json.dump(list(values), fp, ensure_ascii=False, indent=2)
            tmp_path.replace(path)
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to persist %s: %s", path.name, exc)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    # ------------------------
    # User operations
    # ------------------------
    def _ensure_root_user(self) -> None:
        root_user_id = os.getenv("ROOT_USER_ID", "root")
        default_password = os.getenv("ROOT_USER_PASSWORD") or os.getenv("ROOT_DEFAULT_PASSWORD") or "test0000"
        with self._lock:
            if root_user_id in self._users:
                return
            password_hash = pwd_context.hash(default_password)
            self._users[root_user_id] = {
                "user_id": root_user_id,
                "password_hash": password_hash,
                "role": "admin",
                "status": "active",
                "created_at": _utc_now_iso(),
            }
            self._persist_users()
        logger.warning(
            "Root user '%s' created with default password. Please update ROOT_USER_PASSWORD to override the default.",
            root_user_id,
        )

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        user = self._users.get(user_id)
        if not user:
            return None
        return {k: v for k, v in user.items() if k != "password_hash"}

    def authenticate(self, user_id: str, password: str) -> Optional[Dict[str, Any]]:
        if not user_id:
            return None
        with self._lock:
            user = self._users.get(user_id)
            if not user or user.get("status") != "active":
                return None
            if not pwd_context.verify(password, user.get("password_hash", "")):
                return None
            return {k: v for k, v in user.items() if k != "password_hash"}

    def create_user(self, user_id: str, password_hash: str, role: str = "normal") -> Dict[str, Any]:
        with self._lock:
            if user_id in self._users:
                raise ValueError("用户已存在")
            record = {
                "user_id": user_id,
                "password_hash": password_hash,
                "role": role,
                "status": "active",
                "created_at": _utc_now_iso(),
            }
            self._users[user_id] = record
            self._persist_users()
            return {k: v for k, v in record.items() if k != "password_hash"}

    # ------------------------
    # Registration workflow
    # ------------------------
    def submit_registration(self, user_id: str, password: str) -> Dict[str, Any]:
        normalized_id = user_id.strip()
        if not normalized_id:
            raise ValueError("用户ID不能为空")
        with self._lock:
            if normalized_id in self._users:
                raise ValueError("用户已存在")
            if any(
                req for req in self._registrations.values()
                if req.get("user_id") == normalized_id and req.get("status") == "pending"
            ):
                raise ValueError("已有待审核的申请")
            request_id = uuid.uuid4().hex
            record = {
                "request_id": request_id,
                "user_id": normalized_id,
                "password_hash": pwd_context.hash(password),
                "status": "pending",
                "submitted_at": _utc_now_iso(),
                "reviewer": None,
                "reviewed_at": None,
                "decision_reason": None,
            }
            self._registrations[request_id] = record
            self._persist_registrations()
            return self._sanitize_registration(record)

    def list_pending_registrations(self) -> List[Dict[str, Any]]:
        with self._lock:
            pending = [
                self._sanitize_registration(record)
                for record in self._registrations.values()
                if record.get("status") == "pending"
            ]
        pending.sort(key=lambda item: item.get("submitted_at") or "", reverse=True)
        return pending

    def approve_registration(self, request_id: str, reviewer: str) -> Dict[str, Any]:
        with self._lock:
            record = self._registrations.get(request_id)
            if not record:
                raise ValueError("申请不存在")
            if record.get("status") != "pending":
                raise ValueError("申请已处理")
            user_id = record["user_id"]
            if user_id in self._users:
                raise ValueError("用户已存在")
            password_hash = record["password_hash"]
            self._users[user_id] = {
                "user_id": user_id,
                "password_hash": password_hash,
                "role": "normal",
                "status": "active",
                "created_at": _utc_now_iso(),
            }
            record.update({
                "status": "approved",
                "reviewer": reviewer,
                "reviewed_at": _utc_now_iso(),
            })
            self._persist_users()
            self._persist_registrations()
            return {
                "user_id": user_id,
                "role": "normal",
                "status": "active",
                "created_at": self._users[user_id]["created_at"],
            }

    def reject_registration(self, request_id: str, reviewer: str, reason: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            record = self._registrations.get(request_id)
            if not record:
                raise ValueError("申请不存在")
            if record.get("status") != "pending":
                raise ValueError("申请已处理")
            record.update({
                "status": "rejected",
                "reviewer": reviewer,
                "reviewed_at": _utc_now_iso(),
                "decision_reason": reason,
            })
            self._persist_registrations()
            return self._sanitize_registration(record)

    def _sanitize_registration(self, record: Dict[str, Any]) -> Dict[str, Any]:
        sanitized = {
            key: record.get(key)
            for key in [
                "request_id",
                "user_id",
                "status",
                "submitted_at",
                "reviewer",
                "reviewed_at",
                "decision_reason",
            ]
        }
        return sanitized


__all__ = ["AuthManager"]
