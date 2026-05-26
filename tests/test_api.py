"""End-to-end API tests via TestClient. Verifies thin-route, thick-service split."""


def test_healthz(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_patient_lifecycle(client):
    r = client.post("/v1/patients", json={"full_name": "Asha"})
    assert r.status_code == 201
    pid = r.json()["id"]

    r = client.get(f"/v1/patients/{pid}")
    assert r.status_code == 200
    assert r.json()["full_name"] == "Asha"

    r = client.patch(f"/v1/patients/{pid}", json={"notes": "Diabetes"})
    assert r.status_code == 200
    assert r.json()["notes"] == "Diabetes"

    r = client.delete(f"/v1/patients/{pid}")
    assert r.status_code == 204

    r = client.get(f"/v1/patients/{pid}")
    assert r.status_code == 404


def test_medication_scheduling_writes_timeline_event(client):
    pid = client.post("/v1/patients", json={"full_name": "P"}).json()["id"]
    r = client.post(
        f"/v1/patients/{pid}/medications",
        json={"medication_name": "Metformin", "dosage": "500mg", "times_of_day": ["08:00"]},
    )
    assert r.status_code == 201

    page = client.get(f"/v1/patients/{pid}/timeline").json()
    types = {e["event_type"] for e in page["items"]}
    assert "medication_scheduled" in types


def test_alert_resolution_endpoint(client):
    pid = client.post("/v1/patients", json={"full_name": "P"}).json()["id"]
    alert = client.post(
        f"/v1/patients/{pid}/alerts",
        json={"title": "Test", "urgency": "medium"},
    ).json()
    r = client.post(f"/v1/alerts/{alert['id']}/resolve", json={})
    assert r.status_code == 200
    assert r.json()["status"] == "resolved"


def test_handoff_summary_endpoint(client):
    pid = client.post("/v1/patients", json={"full_name": "P"}).json()["id"]
    # Drop a few events into the window.
    for et, urgency in [
        ("medication_taken", "low"),
        ("medication_missed", "medium"),
        ("medication_taken", "low"),
    ]:
        client.post(
            f"/v1/patients/{pid}/timeline",
            json={"event_type": et, "urgency": urgency},
        )
    r = client.get(f"/v1/patients/{pid}/handoff?hours=24")
    assert r.status_code == 200
    body = r.json()
    assert "events" in body and body["events"]["medication_taken"] == 2
    assert "Patient" in body["body"] or "medication" in body["body"].lower()
