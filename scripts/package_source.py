"""Build the release ZIP without dependencies, databases or the source datasets."""
import hashlib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

root = Path(__file__).resolve().parents[1]
destination = root.parent / "CivicAI_Bangladesh_Hardened.zip"
excluded = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", ".openai", "raw"}
included_artifacts = {
    "text.joblib", "forecast.joblib", "text_metrics.json", "forecast_metrics.json",
    "duplicate_proxy_metrics.json", "voice_metrics.json", "road_metrics.json",
    "natural_english_metrics.json", "sha256.json",
    "minilm/tokenizer.json", "minilm/onnx/model_quint8_avx2.onnx",
    "whisper/config.json", "whisper/model.bin", "whisper/tokenizer.json", "whisper/vocabulary.txt",
    "road/road.onnx", "road/model.safetensors", "road/README.md",
    "licenses/Apache-2.0.txt", "licenses/AGPL-3.0.txt", "licenses/Whisper-MIT.txt",
}
artifact_dir = root / "backend/ml_training/artifacts"
ROOT_FILES = {".dockerignore", ".env.example", ".gitignore", "Dockerfile", "LICENSE",
              "README.md", "docker-compose.yml", "render.yaml", "index.html", "package-lock.json",
              "package.json", "vite.config.js"}
ROOT_DIRS = {"backend", "frontend", "public", "scripts", "dist", "docs", ".github"}
SOURCE_SUFFIXES = {".py",".jsx",".js",".css",".json",".html",".md",".txt",".yml",".yaml",".svg"}
with ZipFile(destination, "w", ZIP_DEFLATED, compresslevel=4) as archive:
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file() or path.is_symlink() or any(part in excluded for part in relative.parts):
            continue
        if path.is_relative_to(artifact_dir):
            include = path.relative_to(artifact_dir).as_posix() in included_artifacts
        elif len(relative.parts)==1:
            include = relative.name in ROOT_FILES
        elif "data" in relative.parts:
            include = relative.as_posix() in {
                "backend/ml_training/data/reviewed_pairs_template.csv",
                "backend/ml_training/data/expert_priority_template.csv",
                "backend/ml_training/data/natural_complaints_template.csv",
            }
        else:
            include = relative.parts[0] in ROOT_DIRS and path.suffix in SOURCE_SUFFIXES
        if include:
            archive.write(path, Path("bd-complaint-ai") / relative)
with destination.open("rb") as content:
    print(destination, destination.stat().st_size, hashlib.file_digest(content,"sha256").hexdigest())
