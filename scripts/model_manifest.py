"""Generate checksums of model assets after a trusted build."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "backend/ml_training/artifacts"
files = ("text.joblib", "forecast.joblib", "minilm/tokenizer.json",
         "minilm/onnx/model_quint8_avx2.onnx", "whisper/model.bin",
         "whisper/tokenizer.json", "whisper/config.json", "whisper/vocabulary.txt",
         "road/road.onnx","road/model.safetensors")
entries={}
for name in files:
    with (root/name).open("rb") as f:
        entries[name]=hashlib.file_digest(f,"sha256").hexdigest()
raw=(json.dumps(entries,sort_keys=True,indent=2)+"\n").encode()
(root/"sha256.json").write_bytes(raw)
print(hashlib.sha256(raw).hexdigest())
