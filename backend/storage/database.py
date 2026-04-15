from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, scoped_session, sessionmaker


class Base(DeclarativeBase):
    pass


DEFAULT_DATA_DIR = Path.home() / ".alex"


def get_engine(data_dir: Path = DEFAULT_DATA_DIR):
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "app.db"
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session_factory(engine=None):
    if engine is None:
        engine = get_engine()
    return sessionmaker(bind=engine)


def get_scoped_session_factory(engine=None):
    if engine is None:
        engine = get_engine()
    return scoped_session(sessionmaker(bind=engine))


def _add_missing_columns(engine):
    """Add columns present in the ORM models but missing from the database.

    SQLAlchemy's ``create_all`` only creates new *tables*; it never alters
    existing ones.  This helper bridges the gap for SQLite (which supports
    ``ALTER TABLE ADD COLUMN``) so that model changes are picked up without
    requiring a full migration framework.
    """
    inspector = inspect(engine)
    with engine.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if table.name not in inspector.get_table_names():
                continue  # brand-new table — create_all handles it
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for col in table.columns:
                if col.name not in existing:
                    col_type = col.type.compile(dialect=engine.dialect)
                    conn.execute(
                        text(
                            f"ALTER TABLE {table.name} "
                            f"ADD COLUMN {col.name} {col_type}"
                        )
                    )


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)
    _add_missing_columns(engine)
    return engine
