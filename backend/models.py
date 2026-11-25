from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import true
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

ROLES = ("manager", "employee")
TASK_STATUSES = ("pending", "in_progress", "completed")


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")
    # Deactivated users can't log in, but their history (completed tasks, photos) is kept
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=true())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship("Task", back_populates="assignee", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
        }


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    unit_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    scheduled_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assignee = db.relationship("User", back_populates="tasks")
    photos = db.relationship(
        "TaskPhoto",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskPhoto.created_at",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "unit_name": self.unit_name,
            "address": self.address,
            "description": self.description,
            "scheduled_date": self.scheduled_date.isoformat(),
            "status": self.status,
            "assigned_to": self.assignee.to_dict() if self.assignee else None,
            "photos": [p.to_dict() for p in self.photos],
        }


class TaskPhoto(db.Model):
    """A photo an employee uploads to show a finished unit."""

    __tablename__ = "task_photos"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    task = db.relationship("Task", back_populates="photos")
    uploaded_by = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "url": f"/api/uploads/{self.filename}",
            "uploaded_by": self.uploaded_by.first_name if self.uploaded_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
