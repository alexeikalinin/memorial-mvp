"""Публичный waitlist без авторизации."""
import pytest


def test_waitlist_signup_creates_row(client):
    r = client.post(
        "/api/v1/waitlist/",
        json={"email": "waiter@example.com", "source": "landing"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["already_registered"] is False
    assert "thank" in data["message"].lower()


def test_waitlist_duplicate_same_success(client):
    body = {"email": "dup@example.com"}
    r1 = client.post("/api/v1/waitlist/", json=body)
    r2 = client.post("/api/v1/waitlist/", json=body)
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r2.json()["already_registered"] is True


def test_waitlist_invalid_email(client):
    r = client.post("/api/v1/waitlist/", json={"email": "not-an-email"})
    assert r.status_code == 422
