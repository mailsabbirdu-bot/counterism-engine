from typing import List, Dict, Any
from ..schemas.visualization_schema import Composition, VisualObject

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
            return Composition(hero_object="none")

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

        x = "center"
        y = "center"

        if layer == "background": y = "top"
        if layer == "subsurface": y = "lower_third"
        if not is_hero:
             x = "left" if hash(node["id"]) % 2 == 0 else "right"

        return {
            "x": x,
            "y": y,
            "depth": depth,
            "layer": layer,
            "visual_priority": 90 if is_hero else 50
        }
