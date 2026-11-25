"""Shared test setup: a fresh in-memory database for every test."""
import io
from datetime import date

import pytest

from app import create_app
from config import TestConfig
from models import Task, User, db

PASSWORD = "password123"


@pytest.fixture
def app(tmp_path):
    class Config(TestConfig):
        UPLOAD_FOLDER = str(tmp_path / "uploads")

    app = create_app(Config)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(email, role="employee", first_name="Test", is_active=True):
    user = User(first_name=first_name, last_name="User", email=email, role=role, is_active=is_active)
    user.set_password(PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


def make_task(assignee=None, status="pending", unit_name="Unit 1"):
    task = Task(
        unit_name=unit_name,
        address="123 Beach Rd",
        scheduled_date=date(2026, 12, 1),
        status=status,
        assignee=assignee,
    )
    db.session.add(task)
    db.session.commit()
    return task


def login(client, email, role=None):
    body = {"email": email, "password": PASSWORD}
    if role:
        body["role"] = role
    res = client.post("/api/auth/login", json=body)
    assert res.status_code == 200, res.json
    return {"Authorization": f"Bearer {res.json['token']}"}


def fake_png(name="photo.png"):
    return (io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 32), name)


@pytest.fixture
def manager(app):
    return make_user("boss@test.com", role="manager", first_name="Boss")


@pytest.fixture
def employee(app):
    return make_user("emp@test.com", first_name="Emp")


@pytest.fixture
def other_employee(app):
    return make_user("other@test.com", first_name="Other")


@pytest.fixture
def manager_headers(client, manager):
    return login(client, manager.email, "manager")


@pytest.fixture
def employee_headers(client, employee):
    return login(client, employee.email, "employee")
