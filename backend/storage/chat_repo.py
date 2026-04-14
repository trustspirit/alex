from __future__ import annotations

from backend.storage.base_repo import BaseRepo
from backend.storage.models import ChatMessage, ChatSession


class ChatRepo(BaseRepo):

    def create_session(self, title: str = "New Chat") -> ChatSession:
        chat_session = ChatSession(title=title)
        self._session.add(chat_session)
        self._session.commit()
        self._session.refresh(chat_session)
        return chat_session

    def get_session(self, session_id: int) -> ChatSession | None:
        return self._session.query(ChatSession).filter_by(id=session_id).first()

    def list_sessions(self) -> list[ChatSession]:
        return (
            self._session.query(ChatSession)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    def add_message(
        self,
        session_id: int,
        role: str,
        content: str,
        source_references: str | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            source_references=source_references,
        )
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
        return message

    def get_messages(self, session_id: int) -> list[ChatMessage]:
        return (
            self._session.query(ChatMessage)
            .filter_by(session_id=session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

    def delete_session(self, session_id: int) -> None:
        # Delete messages first (cascade)
        self._session.query(ChatMessage).filter_by(session_id=session_id).delete()
        chat_session = self.get_session(session_id)
        if chat_session is not None:
            self._session.delete(chat_session)
        self._session.commit()
