from typing import Dict, Any

from .visualization_schema import GeometryPath

class RelationshipEngine:
    def __init__(self):
        self.rules = {
            "is_a": {"type": "containment", "renderer": "bound_box", "path": "straight", "grammar": "bridge"},
            "builds": {"type": "construction_flow", "renderer": "particle_stream", "path": "curved", "grammar": "flow"},
            "hidden_under": {"type": "reveal", "renderer": "mask_reveal", "path": "vertical_depth", "grammar": "hides"},
            "produces": {"type": "energy_transfer", "renderer": "pulse_line", "path": "curved", "grammar": "ribbon"},
            "forms": {"type": "aggregation", "renderer": "merge_effect", "path": "straight", "grammar": "flow"},
            "located_in": {"type": "containment", "renderer": "map_overlay", "path": "straight", "grammar": "bridge"},
            "causes": {"type": "energy_transfer", "renderer": "electric_arc", "path": "curved", "grammar": "discharge"},
            "destroys": {"type": "destruction", "renderer": "pulse_line", "path": "straight", "grammar": "breaking"},
            "threatens": {"type": "danger", "renderer": "laser_sweep", "path": "curved", "grammar": "unstable"}
        }

    def map_relation(self, relationship: str) -> Dict[str, Any]:
        mapping = self.rules.get(relationship, {"type": "connector", "renderer": "particle_stream", "path": "curved", "grammar": "default"})

        # Add visual diversity to renderers
        renderer = mapping["renderer"]
        rel_hash = abs(hash(relationship))

        if renderer == "particle_stream":
            options = ["particle_stream", "liquid_flow", "laser_sweep", "electric_arc", "dna_helix", "circuit_board", "neural_synapse"]
            renderer = options[rel_hash % len(options)]

        if "sankey" in relationship.lower():
            renderer = "sankey_link"

        return {
            "type": mapping["type"],
            "renderer": renderer,
            "grammar": mapping["grammar"],
            "path": GeometryPath(type=mapping["path"], control_points=[]),
            "speed": 0.8 if mapping["type"] == "construction_flow" else 1.0
        }

class VisualMapper:
    def __init__(self):
        self.type_map = {
            "location": {"type": "map_marker", "style": "terrain", "semantic_type": "city"},
            "material": {"type": "particles", "style": "structures", "semantic_type": "machine"},
            "concept": {"type": "abstract_core", "style": "standard", "semantic_type": "idea"},
            "urban_concept": {"type": "structures", "style": "high_tech", "semantic_type": "building"},
            "organization": {"type": "structures", "style": "block", "semantic_type": "organization"},
            "metaphor": {"type": "transformation_object", "style": "abstract", "semantic_type": "concept"}
        }

    def map_entity(self, entity_type: str, emotion: str) -> Dict[str, str]:
        base = self.type_map.get(entity_type, {"type": "abstract_core", "style": "standard", "semantic_type": "concept"})
        style = base["style"]
        if emotion == "intense":
            base["type"] = "danger_core"
            style = "warning"

        return {
            "type": base["type"],
            "style": style
        }
