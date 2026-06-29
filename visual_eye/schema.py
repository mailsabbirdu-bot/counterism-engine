from typing import List, Optional
from pydantic import BaseModel

class BBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class DetectedObject(BaseModel):
    id: str
    type: str
    confidence: float
    bbox: BBox

class SafeTextRegion(BaseModel):
    x: float
    y: float
    width: float
    height: float
    confidence: float

class AnalysisFrame(BaseModel):
    frame_index: int
    objects: List[DetectedObject] = []
    safe_text_regions: List[SafeTextRegion] = []

class SceneAnalysis(BaseModel):
    version: str = "1.5"
    status: str
    scene_type: Optional[str] = "unknown"
    # Root level fields for backward compatibility (mapped to first sampled frame)
    objects: List[DetectedObject] = []
    safe_text_regions: List[SafeTextRegion] = []
    # Phase 1.5 Multi-frame support
    frames: List[AnalysisFrame] = []
    total_frames: Optional[int] = 0
    sampled_frames: Optional[int] = 0
