from typing import Dict, Any

from .visualization_schema import GeometryPath

class RelationshipEngine:
    def __init__(self):
        self.rules = {
            "is_a": {"type": "containment", "renderer": "bound_box", "path": "straight"},
            "builds": {"type": "construction_flow", "renderer": "particle_stream", "path": "curved"},
            "hidden_under": {"type": "reveal", "renderer": "mask_reveal", "path": "vertical_depth"},
            "produces": {"type": "energy_transfer", "renderer": "pulse_line", "path": "curved"},
            "forms": {"type": "aggregation", "renderer": "merge_effect", "path": "straight"},
            "located_in": {"type": "containment", "renderer": "map_overlay", "path": "straight"}
        }

    def map_relation(self, relationship: str) -> Dict[str, Any]:
        mapping = self.rules.get(relationship, {"type": "connector", "renderer": "particle_stream", "path": "curved"})

        # Add visual diversity to renderers
        renderer = mapping["renderer"]
        if renderer == "particle_stream" and hash(relationship) % 2 == 0:
            renderer = "liquid_flow"

        return {
            "type": mapping["type"],
            "renderer": renderer,
            "path": GeometryPath(type=mapping["path"], control_points=[]),
            "speed": 0.8 if mapping["type"] == "construction_flow" else 1.0
        }

class VisualMapper:
    def __init__(self):
        self.type_map = {
            "location": {"type": "map_marker", "style": "terrain"},
            "material": {"type": "particles", "style": "structures"},
            "concept": {"type": "abstract_core", "style": "standard"},
            "urban_concept": {"type": "structures", "style": "high_tech"},
            "organization": {"type": "structures", "style": "block"},
            "metaphor": {"type": "transformation_object", "style": "abstract"}
        }

    def map_entity(self, entity_type: str, emotion: str) -> Dict[str, str]:
        base = self.type_map.get(entity_type, {"type": "abstract_core", "style": "standard"})
        style = base["style"]
        if emotion == "intense":
            base["type"] = "danger_core"
            style = "warning"

        return {
            "type": base["type"],
            "style": style
        }
