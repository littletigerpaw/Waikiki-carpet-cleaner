import os

import click
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate

from config import DEV_SECRET, Config
from models import User, db
from routes import auth_bp, employee_bp, manager_bp, uploads_bp

migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config["APP_ENV"] == "production":
        if app.config["SECRET_KEY"] == DEV_SECRET:
            raise RuntimeError("Set the SECRET_KEY environment variable in production")
        if not app.config["CLOUDINARY_URL"]:
            app.logger.warning(
                "CLOUDINARY_URL is not set: photos will be saved to local disk "
                "and lost when the server restarts."
            )

    db.init_app(app)
    # render_as_batch lets migrations alter columns on SQLite too
    migrate.init_app(app, db, render_as_batch=True)
    CORS(app, origins=app.config["FRONTEND_ORIGINS"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(manager_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(uploads_bp)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    register_cli(app)
    return app


def register_cli(app):
    @app.cli.command("create-manager")
    @click.option("--first-name", prompt=True)
    @click.option("--last-name", prompt=True)
    @click.option("--email", prompt=True)
    @click.password_option()
    def create_manager(first_name, last_name, email, password):
        """Create a manager account (interactive)."""
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise click.ClickException(f"{email} already exists")
        user = User(first_name=first_name, last_name=last_name, email=email, role="manager")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Manager {email} created.")

    @app.cli.command("ensure-manager")
    def ensure_manager():
        """Create the first manager from env vars if no manager exists yet.

        Used on hosts without shell access (e.g. Render free plan). Set
        INITIAL_MANAGER_EMAIL and INITIAL_MANAGER_PASSWORD, deploy once, log in,
        change the password on the My Account page, then remove the env vars.
        """
        email = (os.getenv("INITIAL_MANAGER_EMAIL") or "").strip().lower()
        password = os.getenv("INITIAL_MANAGER_PASSWORD")
        if User.query.filter_by(role="manager").first():
            click.echo("A manager already exists; nothing to do.")
            return
        if not email or not password:
            click.echo("No manager yet. Set INITIAL_MANAGER_EMAIL and INITIAL_MANAGER_PASSWORD to create one.")
            return
        user = User(first_name="Admin", last_name="Manager", email=email, role="manager")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Created initial manager {email}.")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
