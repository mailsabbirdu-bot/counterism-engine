from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class GeometryPath(BaseModel):
    type: str = "curved" # straight, curved, vertical_depth
    control_points: List[Dict[str, float]] = []

class VisualRelationship(BaseModel):
    source_id: str
    target_id: str
    type: str # reveal, construction_flow, containment, energy_transfer, aggregation
    renderer: str # particle_stream, pulse_line, mask_reveal
    grammar: str = "default" # electric, flow, breaking, bridge, ribbon, unstable, beam, command, discharge
    path: GeometryPath
    direction: str = "source_to_target"
    speed: float = 1.0
    strength: float = 1.0
    arrival_animation: str = "draw"
    departure_animation: str = "fade"
    revealFrameStart: Optional[int] = None
    revealDuration: Optional[int] = None

class MotionLanguage(BaseModel):
    meaning: str # hidden_danger, accumulation, progressive_intensity
    grammar: List[str] # slow_reveal, depth_movement, focus_shift
    parameters: Dict[str, Any] = {}

class VisualObject(BaseModel):
    id: str
    label: str
    style_preset: Optional[str] = "glass_disc"
    semantic_type: str = "concept" # city, country, building, human, computer, technology, star, weapon, machine, event, idea
    lifecycle_state: str = "active" # hidden, scanning, building, active, focused, warning, critical, destroyed
    type: str # danger_core, abstract_core, map_marker, terrain, particles, structures
    style: str # warning, standard, highlight
    x: str = "center" # left, right, center
    y: str = "center" # top, bottom, center, lower_third
    depth: float = 0 # 2.5D depth
    layer: str = "surface_layer" # foreground, surface, subsurface, background
    scale: float = 1.0
    pulse: bool = False
    importance: float = 1.0
    visual_weight: float = 1.0
    visual_priority: int = 50 # 0-100
    emotion: str = "calm"
    motion_grammar: Optional[MotionLanguage] = None

class TransitionPlan(BaseModel):
    type: str # zoom_into_city, layer_shift, dissolve_to_detail
    from_node: str
    to_node: str
    meaning: str

class Composition(BaseModel):
    hero_object: Optional[str] = "SCENE_TITLE"
    support_objects: List[str] = []
    attention_curve: List[float] = [0.2, 0.5, 1.0]
    layers: List[str] = ["background", "surface", "foreground"]

class CameraInstruction(BaseModel):
    movement: str # push_in, pull_out, pan_left, pan_right, orbit, depth_transition, focus_shift, descend
    focus: Optional[str] = None
    zoom: float = 1.0
    duration: int = 120

class ScenePlan(BaseModel):
    scene_id: str
    duration: int
    theme: str
    layout_type: str = "force" # force, radial, tree, timeline, flowchart, cycle, constellation, geographic, layered, semantic_zones, hub_spoke, cluster, matrix, sankey, bubble, metro, dna, neural, story_journey
    visual_metaphor: str = "force_graph" # galaxy, solar_system, neural_net, command_map, subway, blueprint, radar, circuit
    cinematic_mood: str = "minimal" # minimal, military, scientific, cyberpunk, luxury_hud, organic, documentary, laboratory, danger, dream
    lighting_style: str = "ambient" # ambient, directional, spotlight, scanning, warning, volumetric
    background_fx: str = "none" # grid, stars, fog, blueprint, radar, topography, noise, reflections
    visual_theme: str = "glassmorphism" # hud, blueprint, cyber_grid, minimal, glassmorphism, particle, floating_3d, wireframe, circuit, satellite, medical, space, investigation, sketch, chalkboard, neon, documentary, dashboard, ai_neural, isometric
    composition: Composition
    visual_objects: List[VisualObject] = []
    relationships: List[VisualRelationship] = []
    transition: Optional[TransitionPlan] = None
    camera: CameraInstruction

class VisualizationPlan(BaseModel):
    project_id: str
    scenes: List[ScenePlan]
    global_theme: str
