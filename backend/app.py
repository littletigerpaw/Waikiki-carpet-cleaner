from flask import Flask, jsonify
from flask_cors import CORS
from sqlalchemy import inspect, text

from config import Config
from models import db
from routes import auth_bp, employee_bp, manager_bp, uploads_bp


def add_missing_columns():
    """Tiny migration: db.create_all() makes new tables but won't add new
    columns to existing ones, so add them here without wiping your data."""
    user_cols = {c["name"] for c in inspect(db.engine).get_columns("users")}
    if "is_active" not in user_cols:
        db.session.execute(
            text("ALTER TABLE users ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1")
        )
        db.session.commit()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app, origins=[app.config["FRONTEND_ORIGIN"]])

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(uploads_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()
        add_missing_columns()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
