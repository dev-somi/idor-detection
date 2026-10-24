"""vampi_vuln 빌드(스위치=1)의 실제 동작이 ground_truth/endpoints.json 라벨과 맞는지 확인한다."""

import json

from conftest import add_book, login


def test_e01_book_secret_readable_by_other_user(client):
    # vampi_vuln:e01 vulnerable — 제목만으로 조회해 다른 사용자의 secret을 돌려준다
    add_book(client, login(client, "name1", "pass1"), "t-name1")
    r = client.get("/books/v1/t-name1", headers=login(client, "name2", "pass2"))
    assert r.status_code == 200
    assert r.get_json()["secret"] == "secret-of-t-name1"


def test_e02_password_changeable_for_other_user(client):
    # vampi_vuln:e02 vulnerable — 경로의 username 사용자의 비밀번호를 바꾼다
    r = client.put("/users/v1/name1/password", json={"password": "changed"}, headers=login(client, "name2", "pass2"))
    assert r.status_code == 204
    assert "auth_token" in client.post("/users/v1/login", json={"username": "name1", "password": "changed"}).get_json()


def test_e03_email_update_applies_to_requester(client):
    # vampi_vuln:e03 not_vulnerable — 경로의 username을 쓰지 않고 토큰 주체의 이메일을 바꾼다
    r = client.put("/users/v1/name1/email", json={"email": "new@mail.com"}, headers=login(client, "name2", "pass2"))
    assert r.status_code == 204
    assert json.loads(client.get("/users/v1/name1").data)["email"] == "mail1@mail.com"
    assert json.loads(client.get("/users/v1/name2").data)["email"] == "new@mail.com"


def test_e04_delete_requires_admin(client):
    # vampi_vuln:e04 not_vulnerable — admin이 아니면 거부한다
    assert client.delete("/users/v1/name1", headers=login(client, "name2", "pass2")).status_code == 401
    assert client.delete("/users/v1/name1", headers=login(client, "admin", "pass1")).status_code == 200


def test_e05_new_book_owned_by_requester(client):
    # vampi_vuln:e05 not_vulnerable — 새 책의 소유자는 토큰 주체다
    headers = login(client, "name1", "pass1")
    add_book(client, headers, "t-own")
    assert client.get("/books/v1/t-own", headers=headers).get_json()["owner"] == "name1"


def test_e06_user_lookup_returns_basic_fields(client):
    # vampi_vuln:e06 boundary — 인증 없이 username·email만 돌려준다
    assert set(json.loads(client.get("/users/v1/name1").data)) == {"username", "email"}


def test_e07_debug_discloses_passwords(client):
    # vampi_vuln:e07 boundary — 모든 사용자의 비밀번호를 돌려준다
    users = client.get("/users/v1/_debug").get_json()["users"]
    assert any(u["password"] == "pass1" for u in users)
