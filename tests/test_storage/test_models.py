from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.storage.database import Base
from backend.storage.models import (
    Collection,
    Document,
    Tag,
    ChatSession,
    ChatMessage,
    Setting,
)


def test_create_collection(tmp_db):
    coll = Collection(name="Economics", description="Economics papers")
    tmp_db.add(coll)
    tmp_db.commit()

    result = tmp_db.query(Collection).first()
    assert result.name == "Economics"
    assert result.description == "Economics papers"
    assert result.created_at is not None


def test_create_document_with_collection(tmp_db):
    coll = Collection(name="ML")
    tmp_db.add(coll)
    tmp_db.commit()

    doc = Document(
        title="Attention Is All You Need",
        source_type="pdf",
        source_path="/path/to/paper.pdf",
        collection_id=coll.id,
        status="completed",
        token_count=5000,
    )
    tmp_db.add(doc)
    tmp_db.commit()

    result = tmp_db.query(Document).first()
    assert result.title == "Attention Is All You Need"
    assert result.collection.name == "ML"
    assert result.token_count == 5000
    assert result.fallback_used is False


def test_document_tags(tmp_db):
    doc = Document(title="Test", source_type="md", source_path="/test.md", status="pending")
    tag1 = Tag(name="AI")
    tag2 = Tag(name="NLP")
    doc.tags.append(tag1)
    doc.tags.append(tag2)
    tmp_db.add(doc)
    tmp_db.commit()

    result = tmp_db.query(Document).first()
    tag_names = [t.name for t in result.tags]
    assert "AI" in tag_names
    assert "NLP" in tag_names


def test_chat_session_and_messages(tmp_db):
    session = ChatSession(title="First chat")
    tmp_db.add(session)
    tmp_db.commit()

    msg1 = ChatMessage(
        session_id=session.id,
        role="user",
        content="What is attention mechanism?",
    )
    msg2 = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="Attention is...",
        source_references='[{"doc": "paper.pdf", "page": 3, "score": 0.92}]',
    )
    tmp_db.add_all([msg1, msg2])
    tmp_db.commit()

    messages = tmp_db.query(ChatMessage).filter_by(session_id=session.id).all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[1].source_references is not None


def test_setting(tmp_db):
    setting = Setting(key="default_llm", value="claude-sonnet-4-6", encrypted=False)
    tmp_db.add(setting)
    tmp_db.commit()

    result = tmp_db.query(Setting).filter_by(key="default_llm").first()
    assert result.value == "claude-sonnet-4-6"
