from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DEFAULT_DATA_DIR = Path.home() / ".rag-knowledge-app"


def get_engine(data_dir: Path = DEFAULT_DATA_DIR):
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "app.db"
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session_factory(engine=None):
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine)


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    return engine
