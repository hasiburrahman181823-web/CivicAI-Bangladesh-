"""
CivicAI Bangladesh - Secure File & Evidence Upload Route
Supports both Cloudinary Cloud Storage and local persistent fallback.
"""

import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/api/upload", tags=["Uploads"])

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Cloudinary configuration check
CLOUDINARY_CONFIGURED = False
try:
    import cloudinary
    import cloudinary.uploader
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    cloudinary_url = os.getenv("CLOUDINARY_URL")

    if cloudinary_url or (cloud_name and api_key and api_secret):
        if not cloudinary_url:
            cloudinary.config(
                cloud_name=cloud_name,
                api_key=api_key,
                api_secret=api_secret,
                secure=True
            )
        CLOUDINARY_CONFIGURED = True
except Exception:
    CLOUDINARY_CONFIGURED = False

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

    # Upload to Cloudinary if configured in environment
    if CLOUDINARY_CONFIGURED:
        try:
            upload_result = cloudinary.uploader.upload(
                contents,
                folder="civicai_bangladesh",
                resource_type="auto"
            )
            return {
                "success": True,
                "filename": upload_result.get("public_id"),
                "url": upload_result.get("secure_url"),
                "storage": "cloudinary",
                "size_bytes": len(contents)
            }
        except Exception as e:
            # Fall back to local disk storage if Cloudinary upload fails
            pass

    # Local disk fallback
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
        "storage": "local",
        "size_bytes": len(contents)
    }
