"""VAmPI 벤치 실행 테스트 공통 설정: 앱 생성, DB 초기화, 로그인 헬퍼.

벤치 디렉터리(bench/vampi_*)를 sys.path에 넣고 Flask 테스트 클라이언트로 요청한다.
시드 책 제목은 난수라 충돌할 수 있으므로 randrange를 순서대로 다른 값을 주도록 바꾼다.
"""

import itertools
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import api_app  # noqa: E402
import models.user_model as user_model  # noqa: E402


@pytest.fixture()
def client(monkeypatch):
    """DB를 다시 만든 테스트 클라이언트를 돌려준다."""
    counter = itertools.count()
    monkeypatch.setattr(user_model, "randrange", lambda n: next(counter))
    c = api_app.app.test_client()
    assert c.get("/createdb").status_code == 200
    return c


def login(client, username, password):
    """로그인해서 Authorization 헤더를 돌려준다."""
    r = client.post("/users/v1/login", json={"username": username, "password": password})
    return {"Authorization": "Bearer " + r.get_json()["auth_token"]}


def add_book(client, headers, title):
    """요청자 소유로 책을 하나 추가한다."""
    r = client.post("/books/v1", json={"book_title": title, "secret": f"secret-of-{title}"}, headers=headers)
    assert r.status_code == 200
