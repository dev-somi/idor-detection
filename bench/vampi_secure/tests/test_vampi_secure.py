"""vampi_secure 빌드(스위치=0)의 실제 동작이 ground_truth/endpoints.json 라벨과 맞는지 확인한다."""

import json

from conftest import add_book, login


def test_e01_book_secret_blocked_for_other_user(client):
    # vampi_secure:e01 not_vulnerable — 토큰 주체의 책 중에서만 찾는다
    headers1 = login(client, "name1", "pass1")
    add_book(client, headers1, "t-name1")
    assert client.get("/books/v1/t-name1", headers=login(client, "name2", "pass2")).status_code == 404
    assert client.get("/books/v1/t-name1", headers=headers1).status_code == 200


def test_e02_password_change_applies_to_requester(client):
    # vampi_secure:e02 not_vulnerable — 경로의 username이 아니라 토큰 주체의 비밀번호를 바꾼다
    r = client.put("/users/v1/name1/password", json={"password": "changed"}, headers=login(client, "name2", "pass2"))
    assert r.status_code == 204
    assert "auth_token" in client.post("/users/v1/login", json={"username": "name1", "password": "pass1"}).get_json()
    assert "auth_token" in client.post("/users/v1/login", json={"username": "name2", "password": "changed"}).get_json()


def test_e03_email_update_applies_to_requester(client):
    # vampi_secure:e03 not_vulnerable
    r = client.put("/users/v1/name1/email", json={"email": "new@mail.com"}, headers=login(client, "name2", "pass2"))
    assert r.status_code == 204
    assert json.loads(client.get("/users/v1/name1").data)["email"] == "mail1@mail.com"


def test_e04_delete_requires_admin(client):
    # vampi_secure:e04 not_vulnerable
    assert client.delete("/users/v1/name1", headers=login(client, "name2", "pass2")).status_code == 401
    assert client.delete("/users/v1/name1", headers=login(client, "admin", "pass1")).status_code == 200


def test_e05_new_book_owned_by_requester(client):
    # vampi_secure:e05 not_vulnerable
    headers = login(client, "name1", "pass1")
    add_book(client, headers, "t-own")
    assert client.get("/books/v1/t-own", headers=headers).get_json()["owner"] == "name1"


def test_e06_user_lookup_returns_basic_fields(client):
    # vampi_secure:e06 boundary
    assert set(json.loads(client.get("/users/v1/name1").data)) == {"username", "email"}


def test_e07_debug_discloses_passwords(client):
    # vampi_secure:e07 boundary — 스위치와 무관하게 노출된다
    users = client.get("/users/v1/_debug").get_json()["users"]
    assert any(u["password"] == "pass1" for u in users)
