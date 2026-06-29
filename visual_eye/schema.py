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

class TrackedObject(BaseModel):
    track_id: str
    type: str
    first_frame: int
    last_frame: int
    frames_visible: int
    average_confidence: float
    average_bbox: BBox
    movement_distance: float

class SubjectRank(BaseModel):
    track_id: str
    type: str
    visual_importance: float = 0.0
    narrative_importance: float = 0.0
    final_importance: float = 0.0

class CameraMotion(BaseModel):
    type: str = "unknown"
    confidence: float = 0.0

class ShotAnalysis(BaseModel):
    shot_type: str = "unknown"
    camera_height: str = "unknown"
    environment: str = "unknown"
    complexity: str = "unknown"

class CompositionAnalysis(BaseModel):
    visual_balance: str = "unknown"
    negative_space: str = "unknown"
    horizon: str = "unknown"
    busy_score: float = 0.0
    clean_score: float = 0.0

class RecommendedTextRegion(SafeTextRegion):
    stability: float = 0.0

class ColorAnalysis(BaseModel):
    dominant_colors: List[str] = []
    brightness: float = 0.0
    contrast: float = 0.0

class MotionAnalysis(BaseModel):
    intensity: str = "unknown"
    score: float = 0.0

class SceneSummary(BaseModel):
    main_subject: Optional[str] = "unknown"
    selection_reason: Optional[str] = ""
    camera_motion: Optional[str] = "unknown"
    best_overlay_side: Optional[str] = "center"
    recommended_animation: Optional[str] = "fade_in"

class SceneAnalysis(BaseModel):
    version: str = "2.0"
    status: str
    scene_type: Optional[str] = "unknown"
    # Root level fields for backward compatibility (mapped to first sampled frame)
    objects: List[DetectedObject] = []
    safe_text_regions: List[SafeTextRegion] = []
    # Phase 1.5 Multi-frame support
    frames: List[AnalysisFrame] = []
    total_frames: Optional[int] = 0
    sampled_frames: Optional[int] = 0

    # Phase 2 Advanced Scene Understanding
    tracked_objects: List[TrackedObject] = []
    visual_subjects: List[SubjectRank] = []
    narrative_subjects: List[SubjectRank] = []
    main_subjects: List[SubjectRank] = []
    camera_motion: CameraMotion = CameraMotion()
    shot_analysis: ShotAnalysis = ShotAnalysis()
    composition: CompositionAnalysis = CompositionAnalysis()
    recommended_text_region: RecommendedTextRegion = RecommendedTextRegion(x=0, y=0, width=0, height=0, confidence=0)
    visual_style: ColorAnalysis = ColorAnalysis()
    motion: MotionAnalysis = MotionAnalysis()
    scene_summary: SceneSummary = SceneSummary()
