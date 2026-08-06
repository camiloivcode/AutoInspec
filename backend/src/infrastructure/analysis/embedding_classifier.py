"""CLIP-embedding-based position classifier.

Unlike photo_classifier.py's hand-tuned absolute thresholds (b > 130,
symmetry > 0.8, ...), which were fit by eye against the 81 tuning photos and
measured at 4.94% accuracy on a session-held-out split (see
backend/eval/results/), this scores each photo against a small logistic
regression head trained on CLIP ViT-B/32 image embeddings. The embedding
model has never seen this dataset, so it generalizes on visual concepts
("front of a car", "a document", "a wheel") rather than this dataset's
specific lighting/camera quirks.

The vision encoder (~85MB ONNX, downloaded at Docker build time -- see
Dockerfile) does the heavy lifting; the classification head trained on top
of it is a plain 11x512 weight matrix + bias, small enough to commit as JSON
(position_head.json) and infer with numpy alone.
"""
import os
import json
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

CLIP_INPUT_SIZE = 224
CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

DEFAULT_MODEL_PATH = os.environ.get(
    "CLIP_MODEL_PATH",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "models", "vision_model_quantized.onnx"),
)
DEFAULT_HEAD_PATH = os.path.join(os.path.dirname(__file__), "position_head.json")


def preprocess_clip_array(img_rgb: np.ndarray) -> np.ndarray:
    """Resize-shortest-edge to 224, center crop, CLIP normalize, NCHW float32.
    Takes an already-loaded RGB array so eval/train_head.py can run the same
    normalization on augmented (rotated/jittered/cropped) variants without
    round-tripping through disk."""
    h, w = img_rgb.shape[:2]
    scale = CLIP_INPUT_SIZE / min(h, w)
    nh, nw = max(CLIP_INPUT_SIZE, round(h * scale)), max(CLIP_INPUT_SIZE, round(w * scale))
    img = cv2.resize(img_rgb, (nw, nh), interpolation=cv2.INTER_CUBIC)
    top = (nh - CLIP_INPUT_SIZE) // 2
    left = (nw - CLIP_INPUT_SIZE) // 2
    img = img[top:top + CLIP_INPUT_SIZE, left:left + CLIP_INPUT_SIZE]
    img = img.astype(np.float32) / 255.0
    img = (img - CLIP_MEAN) / CLIP_STD
    return img.transpose(2, 0, 1)[None].astype(np.float32)


def preprocess_clip(image_path: str) -> Optional[np.ndarray]:
    img = cv2.imread(image_path)
    if img is None:
        return None
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return preprocess_clip_array(img)


class ClipEmbedder:
    """Thin wrapper around the ONNX vision encoder. One session per process
    (onnxruntime sessions are thread-safe for inference)."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH):
        self._model_path = model_path
        self._session = None

    def _get_session(self):
        if self._session is None:
            import onnxruntime as ort
            if not os.path.exists(self._model_path):
                raise FileNotFoundError(
                    f"CLIP ONNX model not found at {self._model_path}. "
                    "It's downloaded at Docker build time, not committed to the repo."
                )
            self._session = ort.InferenceSession(self._model_path, providers=["CPUExecutionProvider"])
        return self._session

    def embed(self, image_path: str) -> Optional[np.ndarray]:
        pixel_values = preprocess_clip(image_path)
        if pixel_values is None:
            return None
        return self.embed_array(pixel_values)

    def embed_array(self, pixel_values: np.ndarray) -> np.ndarray:
        """pixel_values: NCHW float32, already preprocessed (see
        preprocess_clip_array). Used directly by eval/train_head.py for
        augmented in-memory variants."""
        session = self._get_session()
        out = session.run(None, {"pixel_values": pixel_values})[0][0]
        norm = np.linalg.norm(out)
        if norm > 1e-6:
            out = out / norm
        return out.astype(np.float32)


class EmbeddingPositionClassifier:
    """Loads the trained 11x512 logistic regression head (position_head.json,
    see eval/train_head.py) and scores a photo's CLIP embedding against it."""

    def __init__(self, model_path: str = DEFAULT_MODEL_PATH, head_path: str = DEFAULT_HEAD_PATH):
        self._embedder = ClipEmbedder(model_path)
        self._head_path = head_path
        self._weights: Optional[np.ndarray] = None  # (n_positions, 512)
        self._bias: Optional[np.ndarray] = None      # (n_positions,)
        self._position_ids: Optional[list[int]] = None

    def _load_head(self):
        if self._weights is not None:
            return
        with open(self._head_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self._position_ids = [int(p) for p in data["positions"]]
        self._weights = np.array(data["weights"], dtype=np.float32)
        self._bias = np.array(data["bias"], dtype=np.float32)

    def predict_proba(self, image_path: str) -> Optional[dict[int, float]]:
        embedding = self._embedder.embed(image_path)
        if embedding is None:
            return None
        self._load_head()
        logits = self._weights @ embedding + self._bias
        logits -= logits.max()
        exp = np.exp(logits)
        probs = exp / exp.sum()
        return {pos: float(p) for pos, p in zip(self._position_ids, probs)}

    def classify(self, image_path: str) -> tuple[Optional[int], dict]:
        probs = self.predict_proba(image_path)
        if not probs:
            return None, {"method": "embedding_unreadable", "confidence": "low"}
        best_pos = max(probs, key=probs.get)
        best_prob = probs[best_pos]
        return best_pos, {
            "method": "clip_embedding",
            "confidence": "high" if best_prob >= 0.5 else "medium" if best_prob >= 0.3 else "low",
            "margin": round(best_prob, 4),
            "probs": {str(k): round(v, 4) for k, v in probs.items()},
        }
