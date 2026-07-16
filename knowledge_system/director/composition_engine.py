from typing import List, Dict, Any
from .visualization_schema import Composition, VisualObject

class CompositionEngine:
    def __init__(self):
        self.layer_depths = {
            "foreground": 200,
            "surface": 0,
            "subsurface": -200,
            "background": -500
        }

    def plan_composition(self, scene_nodes: List[Dict[str, Any]], global_hero: str) -> Composition:
        if not scene_nodes:
            return Composition(hero_object="SCENE_TITLE")

        # Determine local hero based on importance and centrality
        local_hero = max(scene_nodes, key=lambda x: x.get("importance", 1.0))["id"]
        support = [n["id"] for n in scene_nodes if n["id"] != local_hero]

        # Determine layers present
        layers = set()
        for node in scene_nodes:
            layers.add(self._assign_layer(node))

        return Composition(
            hero_object=local_hero,
            support_objects=support,
            attention_curve=[0.2, 0.6, 1.0],
            layers=sorted(list(layers))
        )

    def _assign_layer(self, node: Dict[str, Any]) -> str:
        if node.get("type") == "location": return "background"
        if node.get("emotion") == "intense": return "subsurface"
        if node.get("importance", 1.0) > 2.0: return "foreground"
        return "surface"

    def get_layout(self, node: Dict[str, Any], is_hero: bool) -> Dict[str, Any]:
        layer = self._assign_layer(node)
        depth = self.layer_depths.get(layer, 0)

        # Composition logic to avoid center-stacking
        x = "center"
        y = "center"

        # Use a more diverse hash for randomization
        node_hash = hash(node["id"] + node.get("label", ""))

        if layer == "background":
            y = "top"
            x = "right" if node_hash % 2 == 0 else "left"
        elif layer == "subsurface":
            y = "lower_third"
            x = "center" if is_hero else ("left" if node_hash % 2 == 0 else "right")
        elif not is_hero:
             x = "left" if node_hash % 2 == 0 else "right"
             y = "top" if node_hash % 3 == 0 else "bottom"

        # Randomize preset for visual diversity
        presets = [
            'glass_disc', 'neon_hexagon', 'circuit_chip', 'tactical_triangle',
            'orbital_rings', 'core_pulse', 'dna_helix', 'neural_synapse',
            'holographic_sphere', 'glass_pyramid', 'cyber_eye'
        ]

        # Semantic mapping for presets
        entity_type = node.get("type", "")
        if "dna" in entity_type or "genetic" in entity_type: preset = "dna_helix"
        elif "neural" in entity_type or "brain" in entity_type or "ai" in entity_type: preset = "neural_synapse"
        elif "eye" in entity_type or "surveillance" in entity_type: preset = "cyber_eye"
        else:
            preset = presets[node_hash % len(presets)]

        return {
            "x": x,
            "y": y,
            "depth": depth,
            "layer": layer,
            "visual_priority": 90 if is_hero else 50,
            "style_preset": preset
        }
