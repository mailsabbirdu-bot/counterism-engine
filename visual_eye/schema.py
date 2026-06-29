from typing import List, Optional, Dict, Any
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
    avoid_subject: bool = True

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
    confidence: float = 0.0
    visual_importance: float = 0.0
    narrative_importance: float = 0.0
    tracking_stability: float = 0.0
    screen_position_score: float = 0.0
    duration_visibility: float = 0.0
    cinematic_score: float = 0.0
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

class CinematicDecision(BaseModel):
    decision: str
    confidence: float
    fallback_used: bool = False

class SceneSummary(BaseModel):
    hero_subject: Optional[Dict[str, Any]] = None
    secondary_subjects: List[Dict[str, Any]] = []
    text_position: Optional[CinematicDecision] = None
    camera_behavior: Optional[CinematicDecision] = None
    animation_style: Optional[CinematicDecision] = None
    overlay_strategy: Optional[str] = ""
    main_subject: Optional[str] = "unknown"
    selection_reason: Optional[str] = ""
    camera_motion: Optional[str] = "unknown"
    best_overlay_side: Optional[str] = "center"
    recommended_animation: Optional[str] = "fade_in"

# --- AI COMPACT SUMMARY SCHEMA (PHASE 3.1) ---

class AIHeroSubject(BaseModel):
    type: str
    position: str
    size_ratio: float
    importance: float
    confidence: float
    role: str = "primary subject"

class AIShotSummary(BaseModel):
    type: str
    camera_height: str
    camera_motion: str

class AICompositionSummary(BaseModel):
    balance: str
    negative_space: str
    horizon: str
    busy_score: float

class AISemanticContext(BaseModel):
    crowd_density: float = 0.0
    traffic_density: float = 0.0
    greenery_level: float = 0.0
    urban_density: float = 0.0
    water_presence: bool = False
    skyline_visibility: float = 0.0
    pedestrian_flow: str = "static"
    movement_intensity: str = "low"
    construction_level: float = 0.0
    weather: str = "clear"
    time_of_day: str = "unknown"

class AISummary(BaseModel):
    scene_id: str
    scene_type: str
    environment: str
    shot: AIShotSummary
    composition: AICompositionSummary
    hero_subject: Optional[AIHeroSubject] = None
    secondary_subjects: List[str] = []
    semantic_context: AISemanticContext = AISemanticContext()
    camera_recommendation: Dict[str, str] = {}
    text_region: Dict[str, str] = {}
    visual_style: ColorAnalysis
    semantic_description: str

# --- END AI SCHEMA ---

class SceneAnalysis(BaseModel):
    version: str = "3.1"
    status: str
    scene_type: Optional[str] = "unknown"
    objects: List[DetectedObject] = []
    safe_text_regions: List[SafeTextRegion] = []
    frames: List[AnalysisFrame] = []
    total_frames: Optional[int] = 0
    sampled_frames: Optional[int] = 0
    main_subject: Optional[Dict[str, Any]] = None
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
    ai_summary: Optional[AISummary] = None
