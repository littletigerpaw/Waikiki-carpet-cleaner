import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEV_SECRET = "dev-secret-change-me"


def _database_url():
    url = os.getenv("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "app.db"))
    # Some hosts hand out "postgres://", but SQLAlchemy needs "postgresql://"
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # "production" turns on safety checks (see create_app).
    # Vercel sets VERCEL_ENV automatically, so deployments count as production.
    APP_ENV = os.getenv("APP_ENV") or ("production" if os.getenv("VERCEL_ENV") else "development")

    SECRET_KEY = os.getenv("SECRET_KEY", DEV_SECRET)
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}  # survive dropped DB connections
    TOKEN_EXPIRES_HOURS = 8

    # Only needed if the frontend is served from a different domain than the API.
    # On Vercel both share one domain, so this is just for local development.
    FRONTEND_ORIGINS = [
        o.strip()
        for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
        if o.strip()
    ]

    # Photos: Firebase Storage when FIREBASE_STORAGE_BUCKET is set, else local disk
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET")  # e.g. my-app.firebasestorage.app
    FIREBASE_SERVICE_ACCOUNT = os.getenv("FIREBASE_SERVICE_ACCOUNT")  # service-account JSON
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    # Vercel rejects request bodies over 4.5 MB; the browser shrinks photos first
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic"}


class TestConfig(Config):
    TESTING = True
    APP_ENV = "test"
    SECRET_KEY = "test-secret-key-that-is-long-enough-for-hs256"
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory
    SQLALCHEMY_ENGINE_OPTIONS = {}
    FIREBASE_STORAGE_BUCKET = None
    FIREBASE_SERVICE_ACCOUNT = None
