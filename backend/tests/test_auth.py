from models import User, db
from tests.conftest import PASSWORD, login, make_user


def test_login_success_returns_token_and_user(client, employee):
    res = client.post("/api/auth/login", json={"email": "EMP@test.com ", "password": PASSWORD, "role": "employee"})
    assert res.status_code == 200
    assert res.json["token"]
    assert res.json["user"]["email"] == "emp@test.com"
    assert "password_hash" not in res.json["user"]


def test_login_wrong_password(client, employee):
    res = client.post("/api/auth/login", json={"email": employee.email, "password": "nope"})
    assert res.status_code == 401


def test_login_unknown_email(client):
    res = client.post("/api/auth/login", json={"email": "ghost@test.com", "password": PASSWORD})
    assert res.status_code == 401


def test_employee_cannot_use_manager_portal(client, employee):
    res = client.post("/api/auth/login", json={"email": employee.email, "password": PASSWORD, "role": "manager"})
    assert res.status_code == 403


def test_deactivated_user_cannot_log_in(client, app):
    make_user("gone@test.com", is_active=False)
    res = client.post("/api/auth/login", json={"email": "gone@test.com", "password": PASSWORD})
    assert res.status_code == 403
    assert "deactivated" in res.json["error"]


def test_passwords_are_hashed(employee):
    assert employee.password_hash != PASSWORD
    assert employee.check_password(PASSWORD)


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_me_rejects_bad_token(client):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


def test_me_returns_current_user(client, employee_headers):
    res = client.get("/api/auth/me", headers=employee_headers)
    assert res.status_code == 200
    assert res.json["email"] == "emp@test.com"


def test_token_stops_working_after_deactivation(client, employee, employee_headers):
    employee.is_active = False
    db.session.commit()
    assert client.get("/api/auth/me", headers=employee_headers).status_code == 401


class TestChangePassword:
    url = "/api/auth/change-password"

    def test_success(self, client, employee, employee_headers):
        res = client.post(self.url, json={"current_password": PASSWORD, "new_password": "brandnew123"},
                          headers=employee_headers)
        assert res.status_code == 200
        assert db.session.get(User, employee.id).check_password("brandnew123")

    def test_wrong_current_password(self, client, employee_headers):
        res = client.post(self.url, json={"current_password": "wrong", "new_password": "brandnew123"},
                          headers=employee_headers)
        assert res.status_code == 400

    def test_too_short(self, client, employee_headers):
        res = client.post(self.url, json={"current_password": PASSWORD, "new_password": "short"},
                          headers=employee_headers)
        assert res.status_code == 400

    def test_same_as_current(self, client, employee_headers):
        res = client.post(self.url, json={"current_password": PASSWORD, "new_password": PASSWORD},
                          headers=employee_headers)
        assert res.status_code == 400

    def test_requires_login(self, client):
        assert client.post(self.url, json={}).status_code == 401


def test_login_helper_roles(client, manager):
    # sanity check for the shared helper
    assert login(client, manager.email, "manager")["Authorization"].startswith("Bearer ")
