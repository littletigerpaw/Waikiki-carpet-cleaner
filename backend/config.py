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
    # "production" turns on safety checks (see create_app)
    APP_ENV = os.getenv("APP_ENV", "development")

    SECRET_KEY = os.getenv("SECRET_KEY", DEV_SECRET)
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}  # survive dropped DB connections
    TOKEN_EXPIRES_HOURS = 8

    # Comma-separated list, e.g. "https://myapp.netlify.app,http://localhost:5173"
    FRONTEND_ORIGINS = [
        o.strip()
        for o in os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
        if o.strip()
    ]

    # Photos: Cloudinary when CLOUDINARY_URL is set (production), else local disk
    CLOUDINARY_URL = os.getenv("CLOUDINARY_URL")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB per request
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "heic"}


class TestConfig(Config):
    TESTING = True
    APP_ENV = "test"
    SECRET_KEY = "test-secret-key-that-is-long-enough-for-hs256"
    SQLALCHEMY_DATABASE_URI = "sqlite://"  # in-memory
    SQLALCHEMY_ENGINE_OPTIONS = {}
    CLOUDINARY_URL = None
