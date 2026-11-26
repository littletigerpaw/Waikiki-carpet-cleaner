"""Where task photos live.

- Production (FIREBASE_STORAGE_BUCKET set): Firebase Storage. Vercel's servers have
  no permanent disk, so photos must live somewhere else.
- Development / tests: the local `uploads/` folder, served by /api/uploads/<name>.

Firebase Storage buckets are Google Cloud Storage buckets, so we use the small
`google-cloud-storage` library instead of the whole Firebase Admin SDK.
"""
import base64
import json
import os
import uuid
from urllib.parse import quote

from flask import current_app

FIREBASE_FOLDER = "task-photos"

_bucket = None  # cached between requests on the same server instance


def using_firebase():
    return bool(current_app.config.get("FIREBASE_STORAGE_BUCKET"))


def _load_service_account():
    """FIREBASE_SERVICE_ACCOUNT holds the service-account JSON, pasted as-is or base64-encoded."""
    raw = (current_app.config.get("FIREBASE_SERVICE_ACCOUNT") or "").strip()
    if not raw:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT is not set")
    if not raw.startswith("{"):
        raw = base64.b64decode(raw).decode()
    return json.loads(raw)


def get_bucket():
    global _bucket
    if _bucket is None:
        from google.cloud import storage  # imported lazily: not needed in dev/tests

        client = storage.Client.from_service_account_info(_load_service_account())
        _bucket = client.bucket(current_app.config["FIREBASE_STORAGE_BUCKET"])
    return _bucket


def firebase_download_url(bucket_name, path, token):
    """The same kind of link Firebase's getDownloadURL() returns: works without
    logging in to Firebase, but only for someone who has the random token."""
    return (
        f"https://firebasestorage.googleapis.com/v0/b/{bucket_name}/o/"
        f"{quote(path, safe='')}?alt=media&token={token}"
    )


def save_photo(file_storage, ext):
    """Store an uploaded file. Returns (storage_key, public_url_or_None)."""
    # Random name: never trust the uploaded filename, and avoid collisions
    filename = f"{uuid.uuid4().hex}.{ext}"

    if using_firebase():
        bucket = get_bucket()
        path = f"{FIREBASE_FOLDER}/{filename}"
        token = uuid.uuid4().hex
        blob = bucket.blob(path)
        blob.metadata = {"firebaseStorageDownloadTokens": token}
        blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype or None)
        return path, firebase_download_url(bucket.name, path, token)

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename, None


def delete_photo_file(photo):
    if photo.url:  # stored in Firebase
        if using_firebase():
            blob = get_bucket().blob(photo.filename)
            if blob.exists():
                blob.delete()
        return

    path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.filename)
    if os.path.exists(path):
        os.remove(path)
