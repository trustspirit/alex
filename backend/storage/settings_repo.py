from __future__ import annotations

import keyring
from sqlalchemy.orm import Session

from backend.storage.models import Setting

KEYRING_SERVICE = "rag-knowledge-app"
_SECRET_MARKER = "__secret__"


class SettingsRepo:
    def __init__(self, session: Session) -> None:
        self._session = session

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
        return keyring.get_password(KEYRING_SERVICE, key)

    def set_secret(self, key: str, value: str) -> None:
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
