"""Where task photos live.

- Production (CLOUDINARY_URL set): Cloudinary. Hosts like Render wipe the local
  disk on every deploy/restart, so photos must live somewhere else.
- Development / tests: the local `uploads/` folder, served by /api/uploads/<name>.
"""
import os
import uuid

import cloudinary
import cloudinary.uploader
from flask import current_app

CLOUDINARY_FOLDER = "waikiki-task-photos"


def using_cloudinary():
    return bool(current_app.config.get("CLOUDINARY_URL"))


def save_photo(file_storage, ext):
    """Store an uploaded file. Returns (storage_key, public_url_or_None)."""
    if using_cloudinary():
        cloudinary.config(cloudinary_url=current_app.config["CLOUDINARY_URL"])
        result = cloudinary.uploader.upload(
            file_storage, folder=CLOUDINARY_FOLDER, resource_type="image"
        )
        # f_auto/q_auto: Cloudinary converts formats like iPhone HEIC to
        # something every browser can show, and compresses large photos.
        url = result["secure_url"].replace("/upload/", "/upload/f_auto,q_auto/", 1)
        return result["public_id"], url

    # Random name: never trust the uploaded filename, and avoid collisions
    filename = f"{uuid.uuid4().hex}.{ext}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    file_storage.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
    return filename, None


def delete_photo_file(photo):
    if photo.url:  # stored on Cloudinary
        if using_cloudinary():
            cloudinary.config(cloudinary_url=current_app.config["CLOUDINARY_URL"])
            cloudinary.uploader.destroy(photo.filename)
        return

    path = os.path.join(current_app.config["UPLOAD_FOLDER"], photo.filename)
    if os.path.exists(path):
        os.remove(path)
