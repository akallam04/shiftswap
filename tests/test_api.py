import pytest
from fastapi.testclient import TestClient

from app.main import app, reset

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean():
    reset()


def make(venue="gammage", start="2026-10-24T17:00", end="2026-10-24T22:00", who="arun"):
    return client.post(
        "/shifts",
        json={"venue": venue, "role": "concessions", "start": start, "end": end, "posted_by": who},
    )


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_version_defaults_to_dev():
    assert client.get("/version").json()["commit"] == "dev"


def test_post_and_list():
    assert make().status_code == 201
    assert len(client.get("/shifts").json()) == 1


def test_end_before_start_rejected():
    assert make(start="2026-10-24T22:00", end="2026-10-24T17:00").status_code == 422


def test_overlapping_post_rejected():
    make()
    assert make(start="2026-10-24T20:00", end="2026-10-24T23:00").status_code == 409


def test_filter_by_venue():
    make()
    make(venue="athletics", start="2026-10-25T10:00", end="2026-10-25T14:00")
    rows = client.get("/shifts", params={"venue": "athletics"}).json()
    assert [r["venue"] for r in rows] == ["athletics"]


def test_claim_flow():
    sid = make().json()["id"]
    r = client.post(f"/shifts/{sid}/claim", json={"name": "yajaira"})
    assert r.status_code == 200 and r.json()["claimed_by"] == "yajaira"
    assert client.get("/shifts").json() == []
    assert client.post(f"/shifts/{sid}/claim", json={"name": "sara"}).status_code == 409


def test_cannot_claim_own_shift():
    sid = make().json()["id"]
    assert client.post(f"/shifts/{sid}/claim", json={"name": "arun"}).status_code == 400


def test_cannot_claim_overlapping_shifts():
    a = make(who="arun").json()["id"]
    b = make(who="sara", venue="athletics").json()["id"]
    client.post(f"/shifts/{a}/claim", json={"name": "brayan"})
    assert client.post(f"/shifts/{b}/claim", json={"name": "brayan"}).status_code == 409


def test_claim_missing_shift():
    assert client.post("/shifts/99/claim", json={"name": "arun"}).status_code == 404
