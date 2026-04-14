from __future__ import annotations

try:
    import keyring
except ImportError:
    keyring = None  # type: ignore[assignment]

from backend.storage.base_repo import BaseRepo
from backend.storage.models import Setting

KEYRING_SERVICE = "alex"
_SECRET_MARKER = "__secret__"


class SettingsRepo(BaseRepo):
    def get(self, key: str) -> str | None:
        setting = self._session.query(Setting).filter_by(key=key).first()
        if setting is None:
            return None
        return setting.value

    def set(self, key: str, value: str) -> Setting:
        setting = self._session.query(Setting).filter_by(key=key).first()
        if setting is None:
            setting = Setting(key=key, value=value)
            self._session.add(setting)
        else:
            setting.value = value
            setting.encrypted = False
        self._session.commit()
        self._session.refresh(setting)
        return setting

    def get_secret(self, key: str) -> str | None:
        if keyring is None:
            return None
        return keyring.get_password(KEYRING_SERVICE, key)

    def set_secret(self, key: str, value: str) -> None:
        if keyring is None:
            raise RuntimeError("keyring package is not installed")
        keyring.set_password(KEYRING_SERVICE, key, value)
        # Store a marker in SQLite so we know a secret exists for this key
        setting = self._session.query(Setting).filter_by(key=key).first()
        if setting is None:
            setting = Setting(key=key, value=_SECRET_MARKER, encrypted=True)
            self._session.add(setting)
        else:
            setting.value = _SECRET_MARKER
            setting.encrypted = True
        self._session.commit()

    def list_all(self) -> list[Setting]:
        return self._session.query(Setting).all()
