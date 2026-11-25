from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request

from models import User, db


def create_token(user):
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=current_app.config["TOKEN_EXPIRES_HOURS"]),
    }
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def token_required(*roles):
    """Require a valid Bearer token. Optionally restrict to specific roles.

    Usage:
        @token_required()                 -> any logged-in user
        @token_required("manager")        -> managers only
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return jsonify({"error": "Missing token"}), 401
            try:
                payload = jwt.decode(
                    header.split(" ", 1)[1],
                    current_app.config["SECRET_KEY"],
                    algorithms=["HS256"],
                )
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Session expired, please log in again"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            user = db.session.get(User, int(payload["sub"]))
            if user is None:
                return jsonify({"error": "User not found"}), 401
            if not user.is_active:
                return jsonify({"error": "This account has been deactivated"}), 401
            if roles and user.role not in roles:
                return jsonify({"error": "You do not have access to this resource"}), 403

            g.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator
