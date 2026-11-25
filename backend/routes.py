from datetime import date

from flask import Blueprint, current_app, g, jsonify, request, send_from_directory

from auth import create_token, token_required
from models import TASK_STATUSES, Task, TaskPhoto, User, db
from storage import delete_photo_file, save_photo

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
manager_bp = Blueprint("manager", __name__, url_prefix="/api/manager")
employee_bp = Blueprint("employee", __name__, url_prefix="/api/employee")
uploads_bp = Blueprint("uploads", __name__, url_prefix="/api/uploads")

MIN_PASSWORD_LENGTH = 8


# ---------- Helpers ----------
def parse_date(value):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def validate_assignee(assigned_to_id):
    """Return (id_or_None, error_message_or_None)."""
    if not assigned_to_id:
        return None, None
    assignee = db.session.get(User, int(assigned_to_id))
    if assignee is None or assignee.role != "employee":
        return None, "Assigned user must be an employee"
    if not assignee.is_active:
        return None, "Cannot assign tasks to a deactivated employee"
    return assignee.id, None


# ---------- Auth ----------
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role")  # which portal the user is logging into

    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401
    if not user.is_active:
        return jsonify({"error": "This account has been deactivated. Please contact your manager."}), 403
    if role and user.role != role:
        return jsonify({"error": f"This account is not a {role} account"}), 403

    return jsonify({"token": create_token(user), "user": user.to_dict()})


@auth_bp.get("/me")
@token_required()
def me():
    return jsonify(g.current_user.to_dict())


@auth_bp.post("/change-password")
@token_required()
def change_password():
    data = request.get_json() or {}
    current = data.get("current_password") or ""
    new = data.get("new_password") or ""

    if not g.current_user.check_password(current):
        return jsonify({"error": "Current password is incorrect"}), 400
    if len(new) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"New password must be at least {MIN_PASSWORD_LENGTH} characters"}), 400
    if new == current:
        return jsonify({"error": "New password must be different from the current one"}), 400

    g.current_user.set_password(new)
    db.session.commit()
    return jsonify({"message": "Password updated"})


# ---------- Manager ----------
@manager_bp.get("/dashboard")
@token_required("manager")
def manager_dashboard():
    employees = User.query.filter_by(role="employee").order_by(User.first_name).all()
    tasks = Task.query.order_by(Task.scheduled_date).all()
    return jsonify(
        {
            "employees": [e.to_dict() for e in employees],
            "tasks": [t.to_dict() for t in tasks],
            "stats": {
                status: Task.query.filter_by(status=status).count()
                for status in TASK_STATUSES
            },
        }
    )


@manager_bp.post("/employees")
@token_required("manager")
def create_employee():
    data = request.get_json() or {}
    required = ("first_name", "last_name", "email", "password")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    email = data["email"].strip().lower()
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already in use"}), 409

    user = User(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=email,
        phone=data.get("phone"),
        role="employee",
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201


@manager_bp.patch("/employees/<int:employee_id>")
@token_required("manager")
def set_employee_active(employee_id):
    """Deactivate or reactivate an employee.

    Deactivating unassigns their unfinished tasks so they can be reassigned.
    Completed tasks keep the employee's name for history.
    """
    employee = db.session.get(User, employee_id)
    if employee is None or employee.role != "employee":
        return jsonify({"error": "Employee not found"}), 404

    is_active = (request.get_json() or {}).get("is_active")
    if not isinstance(is_active, bool):
        return jsonify({"error": "is_active must be true or false"}), 400

    unassigned = 0
    if not is_active:
        open_tasks = Task.query.filter(
            Task.assigned_to_id == employee.id, Task.status != "completed"
        ).all()
        for task in open_tasks:
            task.assigned_to_id = None
        unassigned = len(open_tasks)

    employee.is_active = is_active
    db.session.commit()
    return jsonify({"employee": employee.to_dict(), "unassigned_tasks": unassigned})


@manager_bp.post("/tasks")
@token_required("manager")
def create_task():
    data = request.get_json() or {}
    required = ("unit_name", "address", "scheduled_date")
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    scheduled = parse_date(data["scheduled_date"])
    if scheduled is None:
        return jsonify({"error": "scheduled_date must be YYYY-MM-DD"}), 400

    assigned_to_id, err = validate_assignee(data.get("assigned_to_id"))
    if err:
        return jsonify({"error": err}), 400

    task = Task(
        unit_name=data["unit_name"],
        address=data["address"],
        description=data.get("description"),
        scheduled_date=scheduled,
        assigned_to_id=assigned_to_id,
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@manager_bp.patch("/tasks/<int:task_id>")
@token_required("manager")
def update_task(task_id):
    """Edit any task field, including reassigning it to another employee."""
    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    data = request.get_json() or {}

    for field in ("unit_name", "address"):
        if field in data:
            if not (data[field] or "").strip():
                return jsonify({"error": f"{field} cannot be empty"}), 400
            setattr(task, field, data[field].strip())

    if "description" in data:
        task.description = data["description"]

    if "scheduled_date" in data:
        scheduled = parse_date(data["scheduled_date"])
        if scheduled is None:
            return jsonify({"error": "scheduled_date must be YYYY-MM-DD"}), 400
        task.scheduled_date = scheduled

    if "status" in data:
        if data["status"] not in TASK_STATUSES:
            return jsonify({"error": f"Status must be one of {TASK_STATUSES}"}), 400
        task.status = data["status"]

    new_assignee = int(data["assigned_to_id"]) if data.get("assigned_to_id") else None
    if "assigned_to_id" in data and new_assignee != task.assigned_to_id:
        assigned_to_id, err = validate_assignee(data["assigned_to_id"])
        if err:
            return jsonify({"error": err}), 400
        task.assigned_to_id = assigned_to_id

    db.session.commit()
    return jsonify(task.to_dict())


@manager_bp.delete("/tasks/<int:task_id>")
@token_required("manager")
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    for photo in task.photos:
        delete_photo_file(photo)
    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted"})


# ---------- Employee ----------
def get_own_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None or task.assigned_to_id != g.current_user.id:
        return None
    return task


@employee_bp.get("/tasks")
@token_required("employee")
def my_tasks():
    tasks = (
        Task.query.filter_by(assigned_to_id=g.current_user.id)
        .order_by(Task.scheduled_date)
        .all()
    )
    return jsonify([t.to_dict() for t in tasks])


@employee_bp.patch("/tasks/<int:task_id>")
@token_required("employee")
def update_task_status(task_id):
    task = get_own_task(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    status = (request.get_json() or {}).get("status")
    if status not in TASK_STATUSES:
        return jsonify({"error": f"Status must be one of {TASK_STATUSES}"}), 400

    task.status = status
    db.session.commit()
    return jsonify(task.to_dict())


@employee_bp.post("/tasks/<int:task_id>/photos")
@token_required("employee")
def upload_photos(task_id):
    task = get_own_task(task_id)
    if task is None:
        return jsonify({"error": "Task not found"}), 404

    files = request.files.getlist("photos")
    if not files or all(f.filename == "" for f in files):
        return jsonify({"error": "No photos selected"}), 400

    allowed = current_app.config["ALLOWED_IMAGE_EXTENSIONS"]
    for f in files:
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in allowed:
            return jsonify({"error": f"'{f.filename}' is not an allowed image type"}), 400

    for f in files:
        ext = f.filename.rsplit(".", 1)[-1].lower()
        key, url = save_photo(f, ext)
        db.session.add(
            TaskPhoto(task=task, filename=key, url=url, uploaded_by_id=g.current_user.id)
        )

    db.session.commit()
    return jsonify(task.to_dict()), 201


@employee_bp.delete("/tasks/<int:task_id>/photos/<int:photo_id>")
@token_required("employee")
def delete_photo(task_id, photo_id):
    task = get_own_task(task_id)
    photo = db.session.get(TaskPhoto, photo_id)
    if task is None or photo is None or photo.task_id != task.id:
        return jsonify({"error": "Photo not found"}), 404

    delete_photo_file(photo)
    db.session.delete(photo)
    db.session.commit()
    return jsonify(task.to_dict())


# ---------- Uploaded files ----------
@uploads_bp.get("/<path:filename>")
def serve_upload(filename):
    # Filenames are random UUIDs, so they can't be guessed.
    # (<img> tags can't send our Bearer token, so this route is not token-protected.)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
