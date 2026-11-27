import pytest
from tests.test_social import _register_user, _login
from tests.test_admin import _admin_login

def test_admin_like_match_and_analytics(client, monkeypatch):
    _register_user(client, "a@example.com", "A")
    _register_user(client, "b@example.com", "B")
    _login(client, "a@example.com"); aid=client.get("/api/v1/profiles/me").json()["user_id"]
    _login(client, "b@example.com"); bid=client.get("/api/v1/profiles/me").json()["user_id"]
    _login(client, "a@example.com"); assert client.post("/api/v1/likes", json={"to_user_id":bid}).status_code == 201
    _login(client, "b@example.com"); assert client.post("/api/v1/likes", json={"to_user_id":aid}).status_code == 201
    _admin_login(client, monkeypatch)
    r=client.get("/api/v1/admin/likes"); assert r.status_code==200 and r.json()["total_matches"]==1
    r=client.get("/api/v1/admin/analytics"); assert r.status_code==200 and r.json()["users_total"]>=2

def test_admin_message_metadata_never_exposes_e2ee_fields(client, monkeypatch):
    _register_user(client, "c@example.com", "C"); _register_user(client, "d@example.com", "D")
    _admin_login(client, monkeypatch)
    stats=client.get("/api/v1/admin/messages"); assert stats.status_code==200
    rows=client.get("/api/v1/admin/messages/metadata").json()
    assert isinstance(rows,list)
    for row in rows:
        assert "ciphertext" not in row and "text" not in row and "nonce" not in row

def test_admin_subscriptions_and_settings(client, monkeypatch):
    _admin_login(client, monkeypatch)
    assert client.get("/api/v1/admin/subscriptions").status_code==200
    settings=client.get("/api/v1/admin/settings")
    assert settings.status_code==200
    assert any(x["key"]=="vapid_configured" for x in settings.json())

def test_user_settings_are_persistent_and_validated(client):
    _register_user(client, "settings@example.com", "Settings")
    _login(client, "settings@example.com")
    r=client.get("/api/v1/settings/me"); assert r.status_code==200
    assert r.json()["min_age"]==18
    r=client.patch("/api/v1/settings/me", json={"show_online_status":False,"min_age":25,"max_age":45,"discovery_radius_km":250,"language":"FR"})
    assert r.status_code==200 and r.json()["show_online_status"] is False
    r=client.get("/api/v1/settings/me"); assert r.json()["language"]=="FR"
    assert client.patch("/api/v1/settings/me", json={"min_age":60,"max_age":20}).status_code==400
