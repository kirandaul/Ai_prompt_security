"""
ocr.py — extract text from images so the same detectors can scan screenshots.

Uses rapidocr-onnxruntime (pip-only, no system binary, runs offline). The model
is loaded lazily on first use and reused (a few hundred ms to load, then ~1-2s
per image). If the engine is not installed, OCR degrades gracefully.
"""
from __future__ import annotations

import io
import threading
from typing import Optional

_engine = None
_lock = threading.Lock()
_available: Optional[bool] = None


def available() -> bool:
    global _available
    if _available is None:
        try:
            import rapidocr_onnxruntime  # noqa: F401
            import PIL  # noqa: F401
            import numpy  # noqa: F401
            _available = True
        except Exception:
            _available = False
    return _available


def _get_engine():
    global _engine
    if _engine is None:
        with _lock:
            if _engine is None:
                from rapidocr_onnxruntime import RapidOCR
                _engine = RapidOCR()
    return _engine


def extract_text(image_bytes: bytes) -> str:
    """Return all text found in the image, or '' if none / on failure."""
    if not image_bytes or not available():
        return ""
    try:
        import numpy as np
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        arr = np.array(img)
        result, _elapse = _get_engine()(arr)
        if not result:
            return ""
        return " ".join(line[1] for line in result).strip()
    except Exception:
        return ""
