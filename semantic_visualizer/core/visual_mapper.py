from typing import Dict, Any

class RelationshipEngine:
    def __init__(self):
        self.rules = {
            "is_a": {"type": "containment", "visual": "bound_box"},
            "builds": {"type": "construction_flow", "visual": "particle_stream"},
            "hidden_under": {"type": "reveal", "visual": "mask_reveal"},
            "produces": {"type": "energy_transfer", "visual": "pulse_line"},
            "forms": {"type": "aggregation", "visual": "merge_effect"},
            "located_in": {"type": "containment", "visual": "map_overlay"}
        }

    def map_relation(self, relationship: str) -> Dict[str, str]:
        return self.rules.get(relationship, {"type": "connector", "visual": "basic_line"})

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
