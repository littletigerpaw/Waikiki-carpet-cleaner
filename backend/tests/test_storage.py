"""Firebase Storage path, tested with a fake bucket (no real Firebase needed)."""
import base64
import json
from urllib.parse import parse_qs, urlparse

import pytest

import storage
from models import TaskPhoto
from tests.conftest import fake_png, make_task


class FakeBlob:
    def __init__(self, bucket, path):
        self.bucket, self.path, self.metadata = bucket, path, None

    def upload_from_file(self, stream, content_type=None):
        self.bucket.files[self.path] = {"data": stream.read(), "metadata": self.metadata, "type": content_type}

    def exists(self):
        return self.path in self.bucket.files

    def delete(self):
        del self.bucket.files[self.path]


class FakeBucket:
    name = "waikiki-test.firebasestorage.app"

    def __init__(self):
        self.files = {}

    def blob(self, path):
        return FakeBlob(self, path)


@pytest.fixture
def bucket(app, monkeypatch):
    fake = FakeBucket()
    app.config["FIREBASE_STORAGE_BUCKET"] = fake.name
    monkeypatch.setattr(storage, "get_bucket", lambda: fake)
    return fake


def upload(client, task_id, headers):
    return client.post(f"/api/employee/tasks/{task_id}/photos", headers=headers,
                       data={"photos": [fake_png()]}, content_type="multipart/form-data")


def test_upload_goes_to_firebase(app, client, bucket, employee, employee_headers):
    task = make_task(employee)
    res = upload(client, task.id, employee_headers)
    assert res.status_code == 201

    [(path, stored)] = bucket.files.items()
    assert path.startswith("task-photos/") and path.endswith(".png")
    assert stored["type"] == "image/png"
    token = stored["metadata"]["firebaseStorageDownloadTokens"]

    url = res.json["photos"][0]["url"]
    parsed = urlparse(url)
    assert parsed.netloc == "firebasestorage.googleapis.com"
    assert parsed.path == f"/v0/b/{bucket.name}/o/task-photos%2F{path.split('/')[1]}"
    assert parse_qs(parsed.query) == {"alt": ["media"], "token": [token]}


def test_delete_photo_removes_from_firebase(client, bucket, employee, employee_headers):
    task = make_task(employee)
    photo_id = upload(client, task.id, employee_headers).json["photos"][0]["id"]
    res = client.delete(f"/api/employee/tasks/{task.id}/photos/{photo_id}", headers=employee_headers)
    assert res.status_code == 200
    assert bucket.files == {}


def test_delete_task_removes_firebase_photos(client, bucket, employee, employee_headers, manager_headers):
    task = make_task(employee)
    upload(client, task.id, employee_headers)
    upload(client, task.id, employee_headers)
    assert len(bucket.files) == 2
    client.delete(f"/api/manager/tasks/{task.id}", headers=manager_headers)
    assert bucket.files == {}
    assert TaskPhoto.query.count() == 0


def test_service_account_accepts_json_or_base64(app):
    info = {"type": "service_account", "project_id": "demo"}
    app.config["FIREBASE_SERVICE_ACCOUNT"] = json.dumps(info)
    assert storage._load_service_account() == info
    app.config["FIREBASE_SERVICE_ACCOUNT"] = base64.b64encode(json.dumps(info).encode()).decode()
    assert storage._load_service_account() == info


def test_missing_service_account_is_a_clear_error(app):
    app.config["FIREBASE_SERVICE_ACCOUNT"] = None
    with pytest.raises(RuntimeError, match="FIREBASE_SERVICE_ACCOUNT"):
        storage._load_service_account()
