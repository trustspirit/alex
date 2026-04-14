from __future__ import annotations

import pytest

from backend.storage.chat_repo import ChatRepo


def test_create_session(tmp_db):
    repo = ChatRepo(tmp_db)
    session = repo.create_session(title="My Chat")
    assert session.id is not None
    assert session.title == "My Chat"
    assert session.created_at is not None


def test_create_session_default_title(tmp_db):
    repo = ChatRepo(tmp_db)
    session = repo.create_session()
    assert session.title == "New Chat"


def test_add_message_and_get_messages(tmp_db):
    repo = ChatRepo(tmp_db)
    session = repo.create_session(title="Test Chat")

    msg1 = repo.add_message(session.id, role="user", content="Hello!")
    msg2 = repo.add_message(
        session.id,
        role="assistant",
        content="Hi there!",
        source_references='[{"doc": "paper.pdf"}]',
    )

    messages = repo.get_messages(session.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "Hello!"
    assert messages[1].role == "assistant"
    assert messages[1].source_references == '[{"doc": "paper.pdf"}]'


def test_list_sessions(tmp_db):
    repo = ChatRepo(tmp_db)
    repo.create_session(title="Session A")
    repo.create_session(title="Session B")
    repo.create_session(title="Session C")

    sessions = repo.list_sessions()
    assert len(sessions) == 3
    # Most recent first
    assert sessions[0].title == "Session C"
    assert sessions[2].title == "Session A"


def test_delete_session_with_cascade(tmp_db):
    repo = ChatRepo(tmp_db)
    session = repo.create_session(title="To Delete")
    repo.add_message(session.id, role="user", content="Message 1")
    repo.add_message(session.id, role="assistant", content="Message 2")

    session_id = session.id
    repo.delete_session(session_id)

    assert repo.get_session(session_id) is None
    # Messages should also be deleted
    messages = repo.get_messages(session_id)
    assert len(messages) == 0


def test_get_session_nonexistent(tmp_db):
    repo = ChatRepo(tmp_db)
    result = repo.get_session(9999)
    assert result is None
