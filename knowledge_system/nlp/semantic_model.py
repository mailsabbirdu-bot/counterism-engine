from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Entity(BaseModel):
    id: str
    label: str
    type: str = "concept" # hero, concept, organization, location, etc.
    importance: float = 1.0
    emotion: Optional[str] = None
    scale: float = 1.0
    time: Optional[str] = None
    attributes: Dict[str, Any] = {}

class Action(BaseModel):
    id: str
    label: str
    subject_id: Optional[str] = None
    object_id: Optional[str] = None
    importance: float = 1.0

class Quantity(BaseModel):
    value: float
    unit: Optional[str] = None
    label: str
    entity_id: Optional[str] = None

class TemporalExpression(BaseModel):
    label: str
    value: Optional[str] = None
    type: str = "point" # point, duration, range

class Relation(BaseModel):
    id: str
    source_id: str
    target_id: str
    relationship: str
    importance: float = 1.0
    strength: float = 1.0

class SemanticSceneModel(BaseModel):
    scene_id: str
    narration: str
    entities: List[Entity] = []
    actions: List[Action] = []
    quantities: List[Quantity] = []
    temporal_expressions: List[TemporalExpression] = []
    relations: List[Relation] = []
    scene_type: str = "trend" # trend, conflict, comparison, historical
    emotional_tone: str = "calm"
    importance_score: float = 1.0
    metadata: Dict[str, Any] = {}
