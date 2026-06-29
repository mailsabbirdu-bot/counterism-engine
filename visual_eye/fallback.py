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

class SceneAnalysis(BaseModel):
    version: str = "1.0"
    status: str
    scene_type: Optional[str] = "unknown"
    objects: List[DetectedObject] = []
    safe_text_regions: List[SafeTextRegion] = []

def get_empty_analysis() -> SceneAnalysis:
    return SceneAnalysis(status="failed")
