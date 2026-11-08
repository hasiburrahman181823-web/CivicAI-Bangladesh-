"""
CivicAI Bangladesh - Secure File & Evidence Upload Route
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status

router = APIRouter(prefix="/api/upload", tags=["Uploads"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

@router.post("")
async def upload_file(file: UploadFile = File(...)):
    """Upload photo/video evidence or document with size and extension validation."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '.{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read content to verify size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum permissible size of 10 MB"
        )

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    uploads_dir = os.path.join(base_dir, "uploads")
    os.makedirs(uploads_dir, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}.{ext}"
    dest_path = os.path.join(uploads_dir, safe_filename)

    with open(dest_path, "wb") as f:
        f.write(contents)

    return {
        "success": True,
        "filename": safe_filename,
        "url": f"/uploads/{safe_filename}",
        "size_bytes": len(contents)
    }
