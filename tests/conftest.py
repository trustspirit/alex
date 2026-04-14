import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.storage.database import Base


@pytest.fixture
def tmp_db(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def tmp_data_dir(tmp_path):
    chroma_dir = tmp_path / "chroma"
    chroma_dir.mkdir()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return tmp_path
