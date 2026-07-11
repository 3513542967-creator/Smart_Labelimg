from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def read_image_bgr(path: Path) -> np.ndarray | None:
    """Read an image from a Windows Unicode path without cv2.imread limitations."""
    try:
        encoded = np.fromfile(path, dtype=np.uint8)
    except (OSError, ValueError):
        return None
    if encoded.size == 0:
        return None
    return cv2.imdecode(encoded, cv2.IMREAD_COLOR)
