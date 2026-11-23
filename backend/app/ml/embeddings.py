import os
from pathlib import Path

import numpy as np

from ..config import PRODUCTION

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "ml_training/artifacts/minilm"

class MiniLM:
    """CPU inference for the quantized Sentence Transformers ONNX export."""

    def __init__(self, path):
        import onnxruntime as ort
        ort.disable_telemetry_events()
        from tokenizers import Tokenizer

        path = Path(path)
        options = ort.SessionOptions()
        options.intra_op_num_threads = int(os.getenv("ML_CPU_THREADS", "2"))
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(
            str(path / "onnx/model_quint8_avx2.onnx"), options, providers=["CPUExecutionProvider"]
        )
        self.tokenizer = Tokenizer.from_file(str(path / "tokenizer.json"))
        self.tokenizer.enable_truncation(max_length=128)
        self.tokenizer.enable_padding(pad_id=self.tokenizer.token_to_id("<pad>"), pad_token="<pad>")
        self.inputs = {item.name for item in self.session.get_inputs()}

    def encode(self, texts, normalize_embeddings=True):
        batches = []
        for start in range(0, len(texts), 16):
            batch = self.tokenizer.encode_batch(list(texts[start:start + 16]))
            mask = np.asarray([entry.attention_mask for entry in batch], dtype=np.int64)
            data = {"input_ids": np.asarray([entry.ids for entry in batch], dtype=np.int64),
                    "attention_mask": mask, "token_type_ids": np.zeros_like(mask)}
            hidden = self.session.run(None, {k: v for k, v in data.items() if k in self.inputs})[0]
            pooled = (hidden * mask[..., None]).sum(axis=1) / np.maximum(mask.sum(axis=1, keepdims=True), 1)
            if normalize_embeddings:
                pooled /= np.maximum(np.linalg.norm(pooled, axis=1, keepdims=True), 1e-12)
            batches.append(pooled.astype(np.float32))
        return np.concatenate(batches) if batches else np.empty((0, 384), dtype=np.float32)

def load_encoder():
    configured = os.getenv("EMBEDDING_MODEL_PATH")
    if PRODUCTION and configured:
        raise RuntimeError("Production embeddings must use the verified release directory.")
    artifacts = os.getenv("CIVICAI_ARTIFACTS")
    path = Path(configured) if configured else Path(artifacts)/"minilm" if artifacts else DEFAULT_PATH
    if not path.exists() and not configured:
        return None
    if (path / "onnx/model_quint8_avx2.onnx").is_file():
        return MiniLM(path)
    if configured:
        from sentence_transformers import SentenceTransformer
        return SentenceTransformer(str(path), device="cpu", local_files_only=True)
    return None
