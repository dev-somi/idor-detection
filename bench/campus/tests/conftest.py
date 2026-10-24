import pathlib
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import database, seed  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test_campus.db"
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    # Patch both the database module and seed's already-imported references
    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(seed, "engine", test_engine)
    monkeypatch.setattr(seed, "SessionLocal", TestSessionLocal)

    seed.init_db()

    with TestClient(app) as test_client:
        yield test_client


def auth_headers(user_id: str) -> dict:
    return {"Authorization": f"Bearer {user_id}"}
