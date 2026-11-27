"""Manager tools for erasing data: bulk clean-up, deleting employees, deleting photos."""
import os
from datetime import date, timedelta

import pytest

from models import Task, TaskPhoto, User, db
from tests.conftest import PASSWORD, fake_png, login, make_task, make_user


def days_ago(n):
    return date.today() - timedelta(days=n)


def add_photo(client, task, employee):
    headers = login(client, employee.email)
    res = client.post(f"/api/employee/tasks/{task.id}/photos", headers=headers,
                      data={"photos": [fake_png()]}, content_type="multipart/form-data")
    assert res.status_code == 201
    return res.json["photos"][-1]["id"]


def dated_task(employee, status, age_days, name):
    task = make_task(employee, status=status, unit_name=name)
    task.scheduled_date = days_ago(age_days)
    db.session.commit()
    return task


# ---------- Bulk clean-up ----------
@pytest.fixture
def old_and_new(employee):
    return {
        "old_done": dated_task(employee, "completed", 100, "Old done"),
        "old_pending": dated_task(employee, "pending", 100, "Old pending"),  # never deleted: not completed
        "recent_done": dated_task(employee, "completed", 5, "Recent done"),
    }


def test_preview_counts_without_deleting(client, manager_headers, employee, old_and_new):
    add_photo(client, old_and_new["old_done"], employee)
    res = client.get("/api/manager/cleanup?days=30", headers=manager_headers)
    assert res.status_code == 200
    assert res.json["tasks"] == 1
    assert res.json["photos"] == 1
    assert res.json["cutoff"] == days_ago(30).isoformat()
    assert Task.query.count() == 3  # nothing deleted


def test_cleanup_deletes_only_old_completed_tasks_and_their_photos(app, client, manager_headers, employee, old_and_new):
    add_photo(client, old_and_new["old_done"], employee)
    add_photo(client, old_and_new["recent_done"], employee)
    assert len(os.listdir(app.config["UPLOAD_FOLDER"])) == 2

    res = client.post("/api/manager/cleanup", json={"days": 30}, headers=manager_headers)
    assert res.status_code == 200
    assert res.json["tasks"] == 1 and res.json["photos"] == 1

    remaining = {t.unit_name for t in Task.query.all()}
    assert remaining == {"Old pending", "Recent done"}
    assert TaskPhoto.query.count() == 1
    assert len(os.listdir(app.config["UPLOAD_FOLDER"])) == 1  # the recent photo's file is kept


def test_cleanup_with_nothing_to_delete(client, manager_headers, old_and_new):
    res = client.post("/api/manager/cleanup", json={"days": 365}, headers=manager_headers)
    assert res.json["tasks"] == 0
    assert Task.query.count() == 3


@pytest.mark.parametrize("days", [None, "abc", 0, -5, 99999])
def test_cleanup_rejects_bad_days(client, manager_headers, days):
    assert client.post("/api/manager/cleanup", json={"days": days}, headers=manager_headers).status_code == 400
    assert client.get(f"/api/manager/cleanup?days={days}", headers=manager_headers).status_code == 400


def test_cleanup_is_manager_only(client, employee_headers):
    assert client.post("/api/manager/cleanup", json={"days": 30}, headers=employee_headers).status_code == 403
    assert client.get("/api/manager/cleanup?days=30", headers=employee_headers).status_code == 403
    assert client.post("/api/manager/cleanup", json={"days": 30}).status_code == 401


# ---------- Permanently delete an employee ----------
def test_cannot_delete_active_employee(client, manager_headers, employee):
    res = client.delete(f"/api/manager/employees/{employee.id}", headers=manager_headers)
    assert res.status_code == 409
    assert db.session.get(User, employee.id) is not None


def test_delete_deactivated_employee(client, manager_headers, employee):
    done = make_task(employee, status="completed", unit_name="Done")
    photo_id = add_photo(client, done, employee)
    client.patch(f"/api/manager/employees/{employee.id}", json={"is_active": False}, headers=manager_headers)
    # simulate an open task assigned after deactivation (e.g. data from before this rule)
    open_task = make_task(employee, status="pending", unit_name="Open")

    res = client.delete(f"/api/manager/employees/{employee.id}", headers=manager_headers)
    assert res.status_code == 200
    assert db.session.get(User, employee.id) is None

    done, open_task = db.session.get(Task, done.id), db.session.get(Task, open_task.id)
    assert done.assigned_to_id is None and done.assignee_deleted is True
    assert open_task.assigned_to_id is None and open_task.assignee_deleted is False
    assert db.session.get(TaskPhoto, photo_id).uploaded_by_id is None  # photo kept with the task

    # they can't log in any more
    assert client.post("/api/auth/login", json={"email": "emp@test.com", "password": PASSWORD}).status_code == 401


def test_deleted_employee_shows_as_former_on_dashboard(client, manager_headers, employee):
    make_task(employee, status="completed")
    client.patch(f"/api/manager/employees/{employee.id}", json={"is_active": False}, headers=manager_headers)
    client.delete(f"/api/manager/employees/{employee.id}", headers=manager_headers)
    [task] = client.get("/api/manager/dashboard", headers=manager_headers).json["tasks"]
    assert task["assigned_to"] is None and task["assignee_deleted"] is True


def test_reassigning_former_employee_task_clears_flag(client, manager_headers, employee, other_employee):
    task = make_task(employee, status="completed")
    client.patch(f"/api/manager/employees/{employee.id}", json={"is_active": False}, headers=manager_headers)
    client.delete(f"/api/manager/employees/{employee.id}", headers=manager_headers)
    res = client.patch(f"/api/manager/tasks/{task.id}", json={"assigned_to_id": other_employee.id}, headers=manager_headers)
    assert res.json["assignee_deleted"] is False


def test_cannot_delete_managers_or_missing(client, manager_headers, manager):
    assert client.delete(f"/api/manager/employees/{manager.id}", headers=manager_headers).status_code == 404
    assert client.delete("/api/manager/employees/999", headers=manager_headers).status_code == 404


def test_delete_employee_is_manager_only(client, employee_headers, other_employee):
    other_employee.is_active = False
    db.session.commit()
    res = client.delete(f"/api/manager/employees/{other_employee.id}", headers=employee_headers)
    assert res.status_code == 403


# ---------- Manager deletes a photo ----------
def test_manager_deletes_any_photo(app, client, manager_headers, employee):
    task = make_task(employee)
    photo_id = add_photo(client, task, employee)
    res = client.delete(f"/api/manager/tasks/{task.id}/photos/{photo_id}", headers=manager_headers)
    assert res.status_code == 200
    assert res.json["photos"] == []
    assert os.listdir(app.config["UPLOAD_FOLDER"]) == []


def test_manager_delete_photo_wrong_task(client, manager_headers, employee):
    task_a, task_b = make_task(employee, unit_name="A"), make_task(employee, unit_name="B")
    photo_id = add_photo(client, task_a, employee)
    assert client.delete(f"/api/manager/tasks/{task_b.id}/photos/{photo_id}", headers=manager_headers).status_code == 404
    assert client.delete(f"/api/manager/tasks/{task_a.id}/photos/999", headers=manager_headers).status_code == 404
    assert TaskPhoto.query.count() == 1


def test_employee_cannot_use_manager_photo_delete(client, employee, employee_headers):
    task = make_task(employee)
    photo_id = add_photo(client, task, employee)
    res = client.delete(f"/api/manager/tasks/{task.id}/photos/{photo_id}", headers=employee_headers)
    assert res.status_code == 403


def test_make_user_helper_still_works(app):
    assert make_user("x@test.com").id
