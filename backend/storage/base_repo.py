from __future__ import annotations

from sqlalchemy.orm import Session


class BaseRepo:
    """Base repository that supports both a plain Session and a scoped_session factory.

    When a ``scoped_session`` (callable) is passed, each property access returns
    the thread-local session — making the repository safe to use from multiple
    threads.  When a plain ``Session`` is passed (e.g. in tests), it is used
    directly.
    """

    def __init__(self, session) -> None:
        self._session_or_factory = session

    @property
    def _session(self) -> Session:
        if callable(self._session_or_factory) and not isinstance(self._session_or_factory, Session):
            return self._session_or_factory()
        return self._session_or_factory
