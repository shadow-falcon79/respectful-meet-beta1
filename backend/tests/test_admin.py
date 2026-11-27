import io

import pytest
from fastapi.testclient import TestClient

from tests.test_social import client, _register_user, _login  # noqa: F401


ADMIN_EMAIL = "admin@example.com"


def _admin_login(client: TestClient, monkeypatch) -> None:
    import app.core.config as config_module

    monkeypatch.setattr(config_module.settings, "admin_allowed_emails", ADMIN_EMAIL)

    client.post("/api/v1/admin/auth/request-code", json={"email": ADMIN_EMAIL})
    code = client.sent_codes[ADMIN_EMAIL]  # type: ignore[attr-defined]
    resp = client.post("/api/v1/admin/auth/verify-code", json={"email": ADMIN_EMAIL, "code": code})
    assert resp.status_code == 200


def _tiny_jpeg_bytes() -> bytes:
    return b"\xff\xd8\xff\xe0" + b"\x00" * 100


def test_non_allowlisted_email_gets_no_otp_and_is_denied(client: TestClient, monkeypatch) -> None:
    import app.core.config as config_module

    monkeypatch.setattr(config_module.settings, "admin_allowed_emails", "realadmin@example.com")

    r1 = client.post("/api/v1/admin/auth/request-code", json={"email": "notadmin@example.com"})
    assert r1.status_code == 200  # generic response, never reveals anything
    assert "notadmin@example.com" not in client.sent_codes  # type: ignore[attr-defined] — no OTP actually sent

    r2 = client.post("/api/v1/admin/auth/verify-code", json={"email": "notadmin@example.com", "code": "123456"})
    assert r2.status_code == 403


def test_allowlisted_email_becomes_admin_after_otp(client: TestClient, monkeypatch) -> None:
    _admin_login(client, monkeypatch)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 200


def test_regular_user_cannot_access_admin_routes(client: TestClient) -> None:
    _register_user(client, "plain@example.com", "Plain")
    _login(client, "plain@example.com")
    resp = client.get("/api/v1/admin/users")
    assert resp.status_code == 403


def test_admin_can_list_users(client: TestClient, monkeypatch) -> None:
    _register_user(client, "watched@example.com", "Watched")
    _admin_login(client, monkeypatch)
    resp = client.get("/api/v1/admin/users")
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "watched@example.com" in emails


def test_admin_can_suspend_and_user_is_locked_out(client: TestClient, monkeypatch) -> None:
    _register_user(client, "naughty@example.com", "Naughty")
    _login(client, "naughty@example.com")
    my_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _admin_login(client, monkeypatch)
    resp = client.post(f"/api/v1/admin/users/{my_id}/suspend")
    assert resp.status_code == 204

    _login(client, "naughty@example.com")
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 403


def test_create_vip_profile_appears_indistinguishable_in_feed(client: TestClient, monkeypatch) -> None:
    _admin_login(client, monkeypatch)
    resp = client.post(
        "/api/v1/admin/vip",
        params={
            "first_name": "Sophia",
            "last_name": "V",
            "date_of_birth": "1996-05-01",
            "gender": "woman",
            "country": "France",
            "city": "Paris",
            "bio": "A lovely person.",
        },
        files={"file": ("vip.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    assert resp.status_code == 201
    vip_id = resp.json()["user_id"]

    # A regular user's Feed must show this VIP with zero visible difference —
    # same shape as any normal profile (no extra "isVip" field returned).
    _register_user(client, "seeker@example.com", "Seeker")
    _login(client, "seeker@example.com")
    feed = client.get("/api/v1/feed").json()
    assert any(p["user_id"] == vip_id for p in feed)
    vip_entry = next(p for p in feed if p["user_id"] == vip_id)
    assert "is_vip" not in vip_entry
    assert "vip" not in vip_entry.get("bio", "").lower()


def test_vip_capacity_enforced(client: TestClient, monkeypatch) -> None:
    import app.core.plans as plans_module

    monkeypatch.setattr(plans_module, "VIP_CAPACITY", 2)
    monkeypatch.setattr("app.api.v1.admin.VIP_CAPACITY", 2)

    _admin_login(client, monkeypatch)

    for i in range(2):
        resp = client.post(
            "/api/v1/admin/vip",
            params={
                "first_name": f"Vip{i}",
                "last_name": "Test",
                "date_of_birth": "1996-05-01",
                "gender": "woman",
                "country": "France",
                "city": "Paris",
            },
            files={"file": ("vip.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
        )
        assert resp.status_code == 201

    resp3 = client.post(
        "/api/v1/admin/vip",
        params={
            "first_name": "Overflow",
            "last_name": "Test",
            "date_of_birth": "1996-05-01",
            "gender": "woman",
            "country": "France",
            "city": "Paris",
        },
        files={"file": ("vip.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    assert resp3.status_code == 400


def test_delete_vip_profile(client: TestClient, monkeypatch) -> None:
    _admin_login(client, monkeypatch)
    create_resp = client.post(
        "/api/v1/admin/vip",
        params={
            "first_name": "Temp",
            "last_name": "Vip",
            "date_of_birth": "1996-05-01",
            "gender": "woman",
            "country": "France",
            "city": "Paris",
        },
        files={"file": ("vip.jpg", io.BytesIO(_tiny_jpeg_bytes()), "image/jpeg")},
    )
    vip_id = create_resp.json()["user_id"]

    delete_resp = client.delete(f"/api/v1/admin/vip/{vip_id}")
    assert delete_resp.status_code == 204

    listing = client.get("/api/v1/admin/vip").json()
    assert not any(v["user_id"] == vip_id for v in listing)


def test_admin_can_resolve_report(client: TestClient, monkeypatch) -> None:
    _register_user(client, "reporter@example.com", "Reporter")
    _register_user(client, "reported@example.com", "Reported")
    _login(client, "reported@example.com")
    reported_id = client.get("/api/v1/profiles/me").json()["user_id"]

    _login(client, "reporter@example.com")
    report_resp = client.post("/api/v1/reports", json={"reported_user_id": reported_id, "reason": "spam"})
    report_id = report_resp.json()["id"]

    _admin_login(client, monkeypatch)
    resolve_resp = client.post(f"/api/v1/admin/reports/{report_id}/resolve")
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"
