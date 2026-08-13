"""Smoke: public health must stay lean and secret-free."""

from django.test import Client


def test_health_ok_no_secrets():
    client = Client()
    resp = client.get("/health/")
    assert resp.status_code == 200
    data = resp.json()
    assert data == {"status": "ok"}
    raw = resp.content.decode("utf-8").lower()
    for leak in (
        "secret",
        "password",
        "postgres",
        "traceback",
        "exception",
        "redis://",
        "sk-",
    ):
        assert leak not in raw
