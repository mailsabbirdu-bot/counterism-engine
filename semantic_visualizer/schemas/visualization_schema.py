from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class VisualObject(BaseModel):
    id: str
    label: str
    type: str # danger_core, abstract_core, map_marker, terrain, particles, structures
    style: str # warning, standard, highlight
    position: str # center, top, bottom, left, right, bottom_layer
    scale: float = 1.0
    pulse: bool = False
    importance: float = 1.0
    visual_weight: float = 1.0
    emotion: str = "calm"

class VisualRelationship(BaseModel):
    source_id: str
    target_id: str
    type: str # reveal, construction_flow, containment, energy_transfer, aggregation
    visual: str
    strength: float = 1.0

class Animation(BaseModel):
    target_id: str
    enter: str # scale_in, fade, reveal
    motion: str # pulse, float, jitter
    exit: str # fade, slide_out

class CameraInstruction(BaseModel):
    movement: str # push_in, pull_out, pan_left, pan_right, orbit, depth_transition, focus_shift
    focus: Optional[str] = None
    zoom: float = 1.0
    duration: int = 120

class ScenePlan(BaseModel):
    scene_id: str
    duration: int
    theme: str
    visual_objects: List[VisualObject] = []
    relationships: List[VisualRelationship] = []
    animations: List[Animation] = []
    camera: CameraInstruction

class VisualizationPlan(BaseModel):
    project_id: str
    scenes: List[ScenePlan]
    global_theme: str
