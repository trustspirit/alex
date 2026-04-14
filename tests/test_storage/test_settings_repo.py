from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.storage.settings_repo import SettingsRepo


def test_set_and_get_plain(tmp_db):
    repo = SettingsRepo(tmp_db)
    repo.set("theme", "dark")

    result = repo.get("theme")
    assert result == "dark"


def test_update_existing(tmp_db):
    repo = SettingsRepo(tmp_db)
    repo.set("theme", "dark")
    repo.set("theme", "light")  # upsert

    result = repo.get("theme")
    assert result == "light"


def test_get_nonexistent_returns_none(tmp_db):
    repo = SettingsRepo(tmp_db)
    result = repo.get("nonexistent_key")
    assert result is None


def test_set_and_get_secret(tmp_db):
    repo = SettingsRepo(tmp_db)

    with patch("backend.storage.settings_repo.keyring") as mock_keyring:
        mock_keyring.set_password = MagicMock()
        mock_keyring.get_password = MagicMock(return_value="super_secret_value")

        repo.set_secret("api_key", "super_secret_value")

        # Should store a marker in the DB
        marker = repo.get("api_key")
        assert marker == "__secret__"

        # Should store actual value in keyring
        mock_keyring.set_password.assert_called_once_with(
            "alex", "api_key", "super_secret_value"
        )

        # Retrieving the secret should use keyring
        value = repo.get_secret("api_key")
        assert value == "super_secret_value"
        mock_keyring.get_password.assert_called_once_with(
            "alex", "api_key"
        )


def test_list_all(tmp_db):
    repo = SettingsRepo(tmp_db)
    repo.set("key1", "value1")
    repo.set("key2", "value2")
    repo.set("key3", "value3")

    settings = repo.list_all()
    assert len(settings) == 3
    keys = {s.key for s in settings}
    assert keys == {"key1", "key2", "key3"}
