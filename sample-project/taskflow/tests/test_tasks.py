import pytest


def test_create_task(client, auth_headers):
    resp = client.post("/tasks/", json={
        "title": "Write unit tests",
        "description": "Cover the happy path first",
        "priority": "high",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Write unit tests"
    assert data["priority"] == "high"
    assert data["completed"] is False


def test_list_tasks_empty(client, auth_headers):
    resp = client.get("/tasks/", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_get_task(client, auth_headers):
    create = client.post("/tasks/", json={"title": "Read docs"}, headers=auth_headers)
    task_id = create.json()["id"]

    resp = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


def test_get_task_not_found(client, auth_headers):
    resp = client.get("/tasks/99999", headers=auth_headers)
    assert resp.status_code == 404


def test_update_task(client, auth_headers):
    create = client.post("/tasks/", json={"title": "Draft PR"}, headers=auth_headers)
    task_id = create.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"completed": True}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["completed"] is True


def test_delete_task(client, auth_headers):
    create = client.post("/tasks/", json={"title": "Temp task"}, headers=auth_headers)
    task_id = create.json()["id"]

    resp = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 204

    resp = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_filter_by_priority(client, auth_headers):
    client.post("/tasks/", json={"title": "Low task", "priority": "low"}, headers=auth_headers)
    client.post("/tasks/", json={"title": "High task", "priority": "high"}, headers=auth_headers)

    resp = client.get("/tasks/?priority=low", headers=auth_headers)
    assert resp.status_code == 200
    assert all(t["priority"] == "low" for t in resp.json())


def test_unauthenticated_request(client):
    resp = client.get("/tasks/")
    assert resp.status_code == 401
