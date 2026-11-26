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
        if not app.config["FIREBASE_STORAGE_BUCKET"]:
            app.logger.warning(
                "FIREBASE_STORAGE_BUCKET is not set: photo uploads will not work "
                "on hosts without a permanent disk (like Vercel)."
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
        """Create a manager account (interactive).

        To create one in production, point DATABASE_URL at the Neon database:
            DATABASE_URL="postgresql://..." flask create-manager
        """
        email = email.strip().lower()
        if User.query.filter_by(email=email).first():
            raise click.ClickException(f"{email} already exists")
        user = User(first_name=first_name, last_name=last_name, email=email, role="manager")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"Manager {email} created.")


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5001)
