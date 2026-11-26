import pytest

from app import create_app
from config import Config, TestConfig, _database_url


def test_postgres_url_is_normalized(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
    assert _database_url() == "postgresql://u:p@host:5432/db"


def test_production_requires_secret_key():
    class Prod(Config):
        APP_ENV = "production"
        SECRET_KEY = "dev-secret-change-me"

    with pytest.raises(RuntimeError):
        create_app(Prod)


def test_production_starts_with_secret_key():
    class Prod(TestConfig):
        APP_ENV = "production"

    assert create_app(Prod).config["APP_ENV"] == "production"


def test_health(client):
    assert client.get("/api/health").json == {"status": "ok"}


def test_vercel_deployments_count_as_production(monkeypatch):
    import importlib

    import config

    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("VERCEL_ENV", "production")
    assert importlib.reload(config).Config.APP_ENV == "production"
    monkeypatch.delenv("VERCEL_ENV")
    assert importlib.reload(config).Config.APP_ENV == "development"
