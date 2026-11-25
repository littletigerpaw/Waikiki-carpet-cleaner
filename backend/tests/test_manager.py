import os

import pytest

from models import Task, TaskPhoto, User, db
from tests.conftest import fake_png, login, make_task, make_user


# ---------- Access control ----------
@pytest.mark.parametrize(
    "method,url",
    [
        ("get", "/api/manager/dashboard"),
        ("post", "/api/manager/tasks"),
        ("post", "/api/manager/employees"),
        ("patch", "/api/manager/tasks/1"),
        ("delete", "/api/manager/tasks/1"),
        ("patch", "/api/manager/employees/1"),
    ],
)
def test_manager_routes_reject_employees_and_anonymous(client, employee_headers, method, url):
    call = getattr(client, method)
    assert call(url, json={}).status_code == 401
    assert call(url, json={}, headers=employee_headers).status_code == 403


# ---------- Dashboard ----------
def test_dashboard(client, manager_headers, employee):
    make_task(employee, status="completed")
    make_task(None)
    res = client.get("/api/manager/dashboard", headers=manager_headers)
    assert res.status_code == 200
    assert res.json["stats"] == {"pending": 1, "in_progress": 0, "completed": 1}
    assert [e["email"] for e in res.json["employees"]] == ["emp@test.com"]
    assert len(res.json["tasks"]) == 2


# ---------- Create task ----------
def test_create_task(client, manager_headers, employee):
    res = client.post("/api/manager/tasks", headers=manager_headers, json={
        "unit_name": "Ocean Suite", "address": "1 Kalakaua", "scheduled_date": "2026-12-24",
        "assigned_to_id": employee.id,
    })
    assert res.status_code == 201
    assert res.json["assigned_to"]["id"] == employee.id
    assert res.json["status"] == "pending"


def test_create_task_validation(client, manager_headers, manager):
    base = {"unit_name": "U", "address": "A", "scheduled_date": "2026-12-24"}
    assert client.post("/api/manager/tasks", headers=manager_headers, json={}).status_code == 400
    bad_date = {**base, "scheduled_date": "12/24/2026"}
    assert client.post("/api/manager/tasks", headers=manager_headers, json=bad_date).status_code == 400
    # can't assign to a manager
    to_manager = {**base, "assigned_to_id": manager.id}
    assert client.post("/api/manager/tasks", headers=manager_headers, json=to_manager).status_code == 400


def test_cannot_assign_to_deactivated_employee(client, manager_headers):
    gone = make_user("gone@test.com", is_active=False)
    res = client.post("/api/manager/tasks", headers=manager_headers, json={
        "unit_name": "U", "address": "A", "scheduled_date": "2026-12-24", "assigned_to_id": gone.id,
    })
    assert res.status_code == 400


# ---------- Edit / reassign ----------
def test_edit_and_reassign_task(client, manager_headers, employee, other_employee):
    task = make_task(employee)
    res = client.patch(f"/api/manager/tasks/{task.id}", headers=manager_headers, json={
        "unit_name": "Renamed", "status": "in_progress", "assigned_to_id": other_employee.id,
        "scheduled_date": "2027-01-02",
    })
    assert res.status_code == 200
    assert res.json["unit_name"] == "Renamed"
    assert res.json["status"] == "in_progress"
    assert res.json["assigned_to"]["id"] == other_employee.id
    assert res.json["scheduled_date"] == "2027-01-02"


def test_unassign_task(client, manager_headers, employee):
    task = make_task(employee)
    res = client.patch(f"/api/manager/tasks/{task.id}", headers=manager_headers, json={"assigned_to_id": None})
    assert res.json["assigned_to"] is None


def test_edit_validation(client, manager_headers, employee):
    task = make_task(employee)
    url = f"/api/manager/tasks/{task.id}"
    assert client.patch(url, headers=manager_headers, json={"unit_name": "  "}).status_code == 400
    assert client.patch(url, headers=manager_headers, json={"status": "done"}).status_code == 400
    assert client.patch(url, headers=manager_headers, json={"scheduled_date": "nope"}).status_code == 400
    assert client.patch("/api/manager/tasks/999", headers=manager_headers, json={}).status_code == 404


def test_editing_completed_task_keeps_deactivated_assignee(client, manager_headers):
    gone = make_user("gone@test.com", is_active=False)
    task = make_task(gone, status="completed")
    res = client.patch(f"/api/manager/tasks/{task.id}", headers=manager_headers,
                       json={"unit_name": "Edited", "assigned_to_id": gone.id})
    assert res.status_code == 200


# ---------- Delete ----------
def test_delete_task_removes_photos(app, client, manager_headers, employee):
    task = make_task(employee)
    emp_headers = login(client, employee.email)
    client.post(f"/api/employee/tasks/{task.id}/photos", headers=emp_headers,
                data={"photos": [fake_png()]}, content_type="multipart/form-data")
    assert len(os.listdir(app.config["UPLOAD_FOLDER"])) == 1

    res = client.delete(f"/api/manager/tasks/{task.id}", headers=manager_headers)
    assert res.status_code == 200
    assert db.session.get(Task, task.id) is None
    assert TaskPhoto.query.count() == 0
    assert os.listdir(app.config["UPLOAD_FOLDER"]) == []


def test_delete_missing_task(client, manager_headers):
    assert client.delete("/api/manager/tasks/999", headers=manager_headers).status_code == 404


# ---------- Employees ----------
def test_create_employee(client, manager_headers):
    res = client.post("/api/manager/employees", headers=manager_headers, json={
        "first_name": "New", "last_name": "Hire", "email": "New@Test.com", "password": "temp12345",
    })
    assert res.status_code == 201
    assert res.json["role"] == "employee"
    assert res.json["email"] == "new@test.com"
    # the new employee can log in
    assert client.post("/api/auth/login", json={"email": "new@test.com", "password": "temp12345"}).status_code == 200


def test_create_employee_duplicate_email(client, manager_headers, employee):
    res = client.post("/api/manager/employees", headers=manager_headers, json={
        "first_name": "X", "last_name": "Y", "email": employee.email, "password": "temp12345",
    })
    assert res.status_code == 409


def test_deactivate_employee_unassigns_open_tasks(client, manager_headers, employee):
    open_task = make_task(employee, status="in_progress")
    done_task = make_task(employee, status="completed")

    res = client.patch(f"/api/manager/employees/{employee.id}", headers=manager_headers, json={"is_active": False})
    assert res.status_code == 200
    assert res.json["unassigned_tasks"] == 1
    assert db.session.get(Task, open_task.id).assigned_to_id is None
    assert db.session.get(Task, done_task.id).assigned_to_id == employee.id  # history kept
    assert db.session.get(User, employee.id).is_active is False


def test_reactivate_employee(client, manager_headers):
    gone = make_user("gone@test.com", is_active=False)
    res = client.patch(f"/api/manager/employees/{gone.id}", headers=manager_headers, json={"is_active": True})
    assert res.status_code == 200
    assert res.json["employee"]["is_active"] is True


def test_set_active_validation(client, manager_headers, manager, employee):
    url = f"/api/manager/employees/{employee.id}"
    assert client.patch(url, headers=manager_headers, json={"is_active": "no"}).status_code == 400
    # managers can't be deactivated through this route
    res = client.patch(f"/api/manager/employees/{manager.id}", headers=manager_headers, json={"is_active": False})
    assert res.status_code == 404
