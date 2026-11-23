"""Check model bytes before deserializing release artifacts."""
import hashlib
import hmac
import json
import os
from pathlib import Path

from ..config import PRODUCTION

def verify_artifacts(root):
    manifest = root / "sha256.json"
    expected = os.getenv("CIVICAI_MODEL_MANIFEST_SHA256", "")
    if not manifest.is_file():
        if expected or (PRODUCTION and any(path.is_file() for path in root.rglob("*"))):
            raise RuntimeError("A model integrity manifest is required.")
        return
    raw = manifest.read_bytes()
    if PRODUCTION and not expected:
        raise RuntimeError("Set the model manifest digest from your trusted release.")
    if expected and not hmac.compare_digest(expected,hashlib.sha256(raw).hexdigest()):
        raise RuntimeError("The model integrity manifest failed verification.")
    entries = json.loads(raw)
    for name, digest in entries.items():
        path = root / name
        if Path(name).is_absolute() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
            raise RuntimeError("A model asset is missing or outside the release directory.")
        with path.open("rb") as handle:
            if not hmac.compare_digest(digest,hashlib.file_digest(handle,"sha256").hexdigest()):
                raise RuntimeError("A model asset failed integrity verification.")
    for file in ("text.joblib","forecast.joblib", "whisper/model.bin", "whisper/tokenizer.json",
                 "whisper/config.json","whisper/vocabulary.txt","road/road.onnx",
                 "minilm/tokenizer.json","minilm/onnx/model_quint8_avx2.onnx"):
        if (root/file).is_file() and file not in entries:
            raise RuntimeError("An unverified model asset was found.")
