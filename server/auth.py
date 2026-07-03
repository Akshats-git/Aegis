"""Email + password accounts for the web app.

Users register with an email + password; the password is stored only as a salted
PBKDF2-HMAC-SHA256 hash (stdlib, no extra dependency). Each account gets a stable id
that the web app sends on every request as X-User-Id, so its clinical data lives in an
isolated PatientStore keyed by that id (see server/store.py).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import uuid

from server.store import DATA_DIR

USERS_PATH = DATA_DIR / "_users.json"
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PBKDF2_ROUNDS = 200_000


class AuthError(Exception):
    """Registration/login failure carrying a user-safe message."""


def _hash_password(password: str, salt_hex: str) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), _PBKDF2_ROUNDS)
    return dk.hex()


class UserStore:
    def __init__(self) -> None:
        self.users: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not USERS_PATH.exists():
            return
        try:
            self.users = json.loads(USERS_PATH.read_text())
        except Exception:
            self.users = {}

    def _save(self) -> None:
        USERS_PATH.write_text(json.dumps(self.users, indent=2))

    def register(self, email: str, password: str, name: str | None) -> dict:
        email = (email or "").strip().lower()
        if not _EMAIL_RE.match(email):
            raise AuthError("Enter a valid email address.")
        if len(password or "") < 8:
            raise AuthError("Password must be at least 8 characters.")
        if email in self.users:
            raise AuthError("An account with this email already exists.")
        salt = secrets.token_hex(16)
        self.users[email] = {
            "id": f"user-{uuid.uuid4().hex[:12]}",
            "email": email,
            "name": (name or "").strip() or email.split("@")[0],
            "salt": salt,
            "password_hash": _hash_password(password, salt),
        }
        self._save()
        return self._public(email)

    def authenticate(self, email: str, password: str) -> dict:
        email = (email or "").strip().lower()
        u = self.users.get(email)
        # Compare in constant time; still hash even when the user is unknown to avoid leaking
        # which emails exist via timing.
        salt = u["salt"] if u else "00" * 16
        expected = u["password_hash"] if u else "0" * 64
        if not hmac.compare_digest(expected, _hash_password(password or "", salt)) or not u:
            raise AuthError("Incorrect email or password.")
        return self._public(email)

    def _public(self, email: str) -> dict:
        u = self.users[email]
        return {"id": u["id"], "email": u["email"], "name": u["name"]}


_store: UserStore | None = None


def get_user_store() -> UserStore:
    global _store
    if _store is None:
        _store = UserStore()
    return _store
