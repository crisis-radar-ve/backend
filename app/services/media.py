import hashlib
import os
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image

from app.config import settings

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_upload(file: UploadFile) -> dict:
    """Save an uploaded image/video and generate a thumbnail for images."""
    contents = await file.read()
    ext = Path(file.filename or "unknown").suffix.lower()
    if ext not in (".jpg", ".jpeg", ".png", ".webp", ".mp4", ".mov"):
        ext = ".jpg"

    file_id = hashlib.sha256(contents).hexdigest()[:16]
    original_name = f"{file_id}{ext}"
    original_path = UPLOAD_DIR / original_name

    with open(original_path, "wb") as f:
        f.write(contents)

    result = {
        "file_path": str(original_path),
        "original_url": f"/uploads/{original_name}",
        "thumbnail_url": f"/uploads/{original_name}",
        "mime_type": file.content_type or "application/octet-stream",
        "size_bytes": len(contents),
        "width": None,
        "height": None,
    }

    if ext in (".jpg", ".jpeg", ".png", ".webp"):
        try:
            with Image.open(original_path) as img:
                result["width"], result["height"] = img.size
                thumb = img.copy()
                thumb.thumbnail((300, 300))
                thumb_name = f"{file_id}_thumb{ext}"
                thumb_path = UPLOAD_DIR / thumb_name
                thumb.save(thumb_path, optimize=True, quality=75)
                result["thumbnail_url"] = f"/uploads/{thumb_name}"
        except Exception:
            pass

    return result
