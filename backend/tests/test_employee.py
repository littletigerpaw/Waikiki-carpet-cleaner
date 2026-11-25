import io
import os

import pytest

from models import TaskPhoto
from tests.conftest import fake_png, login, make_task


def upload(client, task_id, headers, files):
    return client.post(f"/api/employee/tasks/{task_id}/photos", headers=headers,
                       data={"photos": files}, content_type="multipart/form-data")


@pytest.mark.parametrize("method,url", [("get", "/api/employee/tasks"), ("patch", "/api/employee/tasks/1")])
def test_employee_routes_reject_managers(client, manager_headers, method, url):
    assert getattr(client, method)(url, json={}, headers=manager_headers).status_code == 403


def test_my_tasks_only_returns_own(client, employee, other_employee, employee_headers):
    mine = make_task(employee, unit_name="Mine")
    make_task(other_employee, unit_name="Theirs")
    make_task(None, unit_name="Nobody's")
    res = client.get("/api/employee/tasks", headers=employee_headers)
    assert [t["id"] for t in res.json] == [mine.id]


def test_update_own_task_status(client, employee, employee_headers):
    task = make_task(employee)
    res = client.patch(f"/api/employee/tasks/{task.id}", headers=employee_headers, json={"status": "completed"})
    assert res.status_code == 200
    assert res.json["status"] == "completed"


def test_cannot_update_someone_elses_task(client, other_employee, employee_headers):
    task = make_task(other_employee)
    res = client.patch(f"/api/employee/tasks/{task.id}", headers=employee_headers, json={"status": "completed"})
    assert res.status_code == 404


def test_invalid_status(client, employee, employee_headers):
    task = make_task(employee)
    res = client.patch(f"/api/employee/tasks/{task.id}", headers=employee_headers, json={"status": "finished"})
    assert res.status_code == 400


# ---------- Photos ----------
def test_upload_multiple_photos(app, client, employee, employee_headers):
    task = make_task(employee)
    res = upload(client, task.id, employee_headers, [fake_png("a.png"), fake_png("b.JPG")])
    assert res.status_code == 201
    assert len(res.json["photos"]) == 2
    assert len(os.listdir(app.config["UPLOAD_FOLDER"])) == 2

    # served back with a random name, not the original
    url = res.json["photos"][0]["url"]
    assert url.startswith("/api/uploads/") and "a.png" not in url
    assert client.get(url).status_code == 200


def test_upload_rejects_non_images(client, employee, employee_headers):
    task = make_task(employee)
    res = upload(client, task.id, employee_headers, [(io.BytesIO(b"MZ"), "virus.exe")])
    assert res.status_code == 400
    assert TaskPhoto.query.count() == 0


def test_upload_requires_files(client, employee, employee_headers):
    task = make_task(employee)
    assert upload(client, task.id, employee_headers, []).status_code == 400


def test_cannot_upload_to_someone_elses_task(client, other_employee, employee_headers):
    task = make_task(other_employee)
    assert upload(client, task.id, employee_headers, [fake_png()]).status_code == 404


def test_delete_own_photo(app, client, employee, employee_headers):
    task = make_task(employee)
    photo_id = upload(client, task.id, employee_headers, [fake_png()]).json["photos"][0]["id"]
    res = client.delete(f"/api/employee/tasks/{task.id}/photos/{photo_id}", headers=employee_headers)
    assert res.status_code == 200
    assert res.json["photos"] == []
    assert os.listdir(app.config["UPLOAD_FOLDER"]) == []


def test_cannot_delete_someone_elses_photo(client, employee, other_employee):
    task = make_task(other_employee)
    other_headers = login(client, other_employee.email)
    photo_id = upload(client, task.id, other_headers, [fake_png()]).json["photos"][0]["id"]

    my_headers = login(client, employee.email)
    res = client.delete(f"/api/employee/tasks/{task.id}/photos/{photo_id}", headers=my_headers)
    assert res.status_code == 404
    assert TaskPhoto.query.count() == 1


def test_uploads_route_blocks_path_traversal(client):
    assert client.get("/api/uploads/../app.py").status_code == 404
