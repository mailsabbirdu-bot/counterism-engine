import cv2
import numpy as np
from typing import List
from .schema import DetectedObject, BBox

def detect_objects(frame: np.ndarray) -> List[DetectedObject]:
    """
    Object detection abstraction. Initially supports a mock implementation
    or a simple OpenCV-based detection if models are not available.
    """
    try:
        # Phase 1: Placeholder for actual model
        return [
            DetectedObject(
                id="obj_001",
                type="building",
                confidence=0.95,
                bbox=BBox(x=800, y=200, width=400, height=600)
            )
        ]
    except Exception:
        return []

def classify_scene(frame: np.ndarray) -> str:
    """
    Simple scene classification.
    """
    try:
        return "urban_city"
    except Exception:
        return "unknown"
