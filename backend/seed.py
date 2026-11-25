"""Reset the database and load demo users + tasks. FOR DEVELOPMENT ONLY.

Run:  flask db upgrade   (first time, creates the tables)
      python seed.py
"""
import os
import shutil
from datetime import date, timedelta

from app import app
from models import Task, TaskPhoto, User, db

USERS = [
    ("Kai", "Manager", "manager@waikiki.com", "manager123", "manager"),
    ("Leilani", "Kahale", "leilani@waikiki.com", "employee123", "employee"),
    ("Noah", "Akana", "noah@waikiki.com", "employee123", "employee"),
]

if app.config["APP_ENV"] == "production":
    raise SystemExit("Refusing to wipe a production database. Use `flask ensure-manager` instead.")

with app.app_context():
    # Clear old uploaded photos too
    shutil.rmtree(app.config["UPLOAD_FOLDER"], ignore_errors=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Empty the tables (children first). Tables themselves come from migrations.
    TaskPhoto.query.delete()
    Task.query.delete()
    User.query.delete()
    db.session.commit()

    users = {}
    for first, last, email, pw, role in USERS:
        u = User(first_name=first, last_name=last, email=email, role=role)
        u.set_password(pw)
        db.session.add(u)
        users[email] = u
    db.session.flush()

    today = date.today()
    leilani = users["leilani@waikiki.com"]
    noah = users["noah@waikiki.com"]
    db.session.add_all(
        [
            Task(unit_name="Ocean View Studio 1204", address="2410 Koa Ave, Honolulu",
                 description="Turnover clean + carpet shampoo", scheduled_date=today,
                 assignee=leilani, status="in_progress"),
            Task(unit_name="Diamond Head Suite 8B", address="3009 Kalakaua Ave, Honolulu",
                 description="Full clean, restock linens", scheduled_date=today + timedelta(days=1),
                 assignee=leilani),
            Task(unit_name="Lanai Loft 302", address="155 Paoakalani Ave, Honolulu",
                 description="Spot clean living room carpet", scheduled_date=today,
                 assignee=noah, status="completed"),
            Task(unit_name="Palm Grove Condo 17", address="444 Niu St, Honolulu",
                 description="Deep clean after 2-week stay", scheduled_date=today + timedelta(days=2)),
        ]
    )
    db.session.commit()
    print("Seeded:", ", ".join(f"{e} / {p} ({r})" for _, _, e, p, r in USERS))
